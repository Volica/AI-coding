from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
RANDOM_STATE = 42


def read_data(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("请确认 data/train.csv 和 data/test.csv 已存在。")
    return pd.read_csv(train_path), pd.read_csv(test_path)


def normalize_title(title: str) -> str:
    title_map = {
        "Mlle": "Miss",
        "Ms": "Miss",
        "Mme": "Mrs",
        "Lady": "Royalty",
        "Countess": "Royalty",
        "Sir": "Royalty",
        "Don": "Royalty",
        "Dona": "Royalty",
        "Jonkheer": "Royalty",
        "Capt": "Officer",
        "Col": "Officer",
        "Major": "Officer",
        "Dr": "Officer",
        "Rev": "Officer",
    }
    return title_map.get(title, title)


def extract_title(name: str) -> str:
    match = re.search(r",\s*([^.]*)\.", name)
    if not match:
        return "Unknown"
    return normalize_title(match.group(1).strip())


def extract_ticket_prefix(ticket: str) -> str:
    cleaned = re.sub(r"[./]", "", str(ticket)).strip()
    prefix = re.sub(r"\d+", "", cleaned).strip().upper()
    return prefix if prefix else "NONE"


def fill_age_with_group_median(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    group_medians = df.groupby(["Sex", "Pclass", "Title"], observed=False)["Age"].transform("median")
    df["Age"] = df["Age"].fillna(group_medians)
    df["Age"] = df["Age"].fillna(df["Age"].median())
    return df


def engineer_features(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = train.copy()
    test = test.copy()
    train["IsTrain"] = 1
    test["IsTrain"] = 0
    test["Survived"] = pd.NA
    combined = pd.concat([train, test], ignore_index=True, sort=False)

    combined["Title"] = combined["Name"].map(extract_title)
    combined["Deck"] = combined["Cabin"].fillna("M").astype(str).str[0]
    combined["Embarked"] = combined["Embarked"].fillna(combined["Embarked"].mode()[0])
    combined["Fare"] = combined["Fare"].fillna(combined.groupby("Pclass")["Fare"].transform("median"))
    combined["Fare"] = combined["Fare"].fillna(combined["Fare"].median())
    combined = fill_age_with_group_median(combined)

    combined["FamilySize"] = combined["SibSp"] + combined["Parch"] + 1
    combined["IsAlone"] = (combined["FamilySize"] == 1).astype(int)
    combined["FamilyGroup"] = pd.cut(
        combined["FamilySize"],
        bins=[0, 1, 4, 7, 20],
        labels=["Alone", "Small", "Medium", "Large"],
        include_lowest=True,
    ).astype(str)
    combined["FarePerPerson"] = combined["Fare"] / combined["FamilySize"].clip(lower=1)
    combined["NameLength"] = combined["Name"].astype(str).str.len()
    combined["CabinCount"] = combined["Cabin"].fillna("").map(lambda value: len(str(value).split()) if value else 0)
    combined["TicketPrefix"] = combined["Ticket"].map(extract_ticket_prefix)
    combined["TicketGroupSize"] = combined.groupby("Ticket")["Ticket"].transform("size")
    combined["AgeBin"] = pd.cut(
        combined["Age"],
        bins=[0, 12, 18, 35, 50, 65, 100],
        labels=["Child", "Teen", "YoungAdult", "Adult", "Senior", "Elder"],
        include_lowest=True,
    ).astype(str)
    combined["FareBin"] = pd.qcut(
        combined["Fare"],
        q=4,
        labels=["LowFare", "MidFare", "HighFare", "TopFare"],
        duplicates="drop",
    ).astype(str)
    combined["Pclass"] = combined["Pclass"].astype(str)

    train_features = combined[combined["IsTrain"] == 1].drop(columns=["IsTrain"])
    test_features = combined[combined["IsTrain"] == 0].drop(columns=["IsTrain", "Survived"])
    train_features["Survived"] = train_features["Survived"].astype(int)
    return train_features, test_features


def build_preprocessor() -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric_features = [
        "Age",
        "SibSp",
        "Parch",
        "Fare",
        "FamilySize",
        "IsAlone",
        "FarePerPerson",
        "NameLength",
        "CabinCount",
        "TicketGroupSize",
    ]
    categorical_features = [
        "Pclass",
        "Sex",
        "Embarked",
        "Title",
        "Deck",
        "TicketPrefix",
        "FamilyGroup",
        "AgeBin",
        "FareBin",
    ]
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )
    return preprocessor, numeric_features, categorical_features


def candidate_models(preprocessor: ColumnTransformer) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                ("model", LogisticRegression(max_iter=2000, C=0.7, random_state=RANDOM_STATE)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=500,
                        max_depth=6,
                        min_samples_split=6,
                        min_samples_leaf=2,
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("preprocessor", clone(preprocessor)),
                (
                    "model",
                    GradientBoostingClassifier(
                        n_estimators=180,
                        learning_rate=0.035,
                        max_depth=3,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def evaluate_models(models: dict[str, Pipeline], x: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rows = []
    for name, model in models.items():
        scores = cross_val_score(model, x, y, cv=cv, scoring="accuracy", n_jobs=-1)
        rows.append(
            {
                "model": name,
                "cv_accuracy_mean": scores.mean(),
                "cv_accuracy_std": scores.std(),
                "fold_scores": ", ".join(f"{score:.4f}" for score in scores),
            }
        )
    return pd.DataFrame(rows).sort_values("cv_accuracy_mean", ascending=False).reset_index(drop=True)


def get_feature_names(model: Pipeline) -> list[str]:
    preprocessor = model.named_steps["preprocessor"]
    return list(preprocessor.get_feature_names_out())


def feature_importance(model: Pipeline, output_dir: Path) -> pd.DataFrame:
    model_step = model.named_steps["model"]
    names = get_feature_names(model)
    if hasattr(model_step, "feature_importances_"):
        values = model_step.feature_importances_
    elif hasattr(model_step, "coef_"):
        values = abs(model_step.coef_[0])
    else:
        return pd.DataFrame()

    importance = (
        pd.DataFrame({"feature": names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    importance.to_csv(output_dir / "feature_importance.csv", index=False)
    top = importance.head(15).sort_values("importance")
    plt.figure(figsize=(8, 6))
    sns.barplot(data=top, x="importance", y="feature", color="#4C78A8")
    plt.title("Top 15 Feature Importances")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=160)
    plt.close()
    return importance


def create_visualizations(train: pd.DataFrame, output_dir: Path) -> None:
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(6, 4))
    sns.countplot(data=train, x="Survived", hue="Survived", palette=["#E45756", "#54A24B"], legend=False)
    plt.xticks([0, 1], ["Not survived", "Survived"])
    plt.title("Survival Count")
    plt.tight_layout()
    plt.savefig(output_dir / "survival_count.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    sns.barplot(data=train, x="Sex", y="Survived", hue="Sex", palette=["#4C78A8", "#F58518"], legend=False)
    plt.title("Survival Rate by Sex")
    plt.ylabel("Survival Rate")
    plt.tight_layout()
    plt.savefig(output_dir / "survival_by_sex.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    sns.barplot(data=train, x="Pclass", y="Survived", hue="Pclass", palette="viridis", legend=False)
    plt.title("Survival Rate by Passenger Class")
    plt.ylabel("Survival Rate")
    plt.tight_layout()
    plt.savefig(output_dir / "survival_by_pclass.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4))
    sns.histplot(data=train, x="Age", hue="Survived", bins=24, kde=True, palette=["#E45756", "#54A24B"])
    plt.title("Age Distribution by Survival")
    plt.tight_layout()
    plt.savefig(output_dir / "age_distribution.png", dpi=160)
    plt.close()


def write_summary(
    cv_results: pd.DataFrame,
    holdout_accuracy: float,
    report: str,
    confusion: list[list[int]],
    output_dir: Path,
) -> None:
    best = cv_results.iloc[0]
    summary = {
        "best_model": best["model"],
        "best_cv_accuracy_mean": round(float(best["cv_accuracy_mean"]), 5),
        "best_cv_accuracy_std": round(float(best["cv_accuracy_std"]), 5),
        "holdout_accuracy": round(float(holdout_accuracy), 5),
        "confusion_matrix": confusion,
        "classification_report": report,
    }
    (output_dir / "metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Titanic Survival Prediction Summary",
        "",
        f"Best model: `{best['model']}`",
        f"5-fold CV accuracy: `{best['cv_accuracy_mean']:.4f} +/- {best['cv_accuracy_std']:.4f}`",
        f"Holdout accuracy: `{holdout_accuracy:.4f}`",
        "",
        "## Model comparison",
        "",
        cv_results.to_markdown(index=False),
        "",
        "## Confusion matrix",
        "",
        f"`{confusion}`",
        "",
        "## Interpretation",
        "",
        "- Sex, passenger class, title, fare, cabin/deck, family size and age-related features are the most informative signals.",
        "- Women, children, passengers in higher classes and passengers with higher fare/cabin information generally show higher survival probability.",
        "- The final Kaggle file is `submission.csv` and contains `PassengerId,Survived`.",
        "",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_pipeline() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    train_raw, test_raw = read_data()
    train, test = engineer_features(train_raw, test_raw)
    create_visualizations(train, OUTPUT_DIR)

    target = train["Survived"]
    drop_columns = ["Survived", "PassengerId", "Name", "Ticket", "Cabin"]
    x = train.drop(columns=drop_columns)
    x_test = test.drop(columns=["PassengerId", "Name", "Ticket", "Cabin"])

    preprocessor, _, _ = build_preprocessor()
    models = candidate_models(preprocessor)
    cv_results = evaluate_models(models, x, target)
    cv_results.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)

    best_name = cv_results.iloc[0]["model"]
    best_model = models[best_name]
    x_train, x_valid, y_train, y_valid = train_test_split(
        x,
        target,
        test_size=0.2,
        stratify=target,
        random_state=RANDOM_STATE,
    )
    holdout_model = clone(best_model)
    holdout_model.fit(x_train, y_train)
    valid_predictions = holdout_model.predict(x_valid)
    holdout_accuracy = accuracy_score(y_valid, valid_predictions)
    report = classification_report(y_valid, valid_predictions)
    confusion = confusion_matrix(y_valid, valid_predictions).tolist()

    best_model.fit(x, target)
    predictions = best_model.predict(x_test).astype(int)
    submission = pd.DataFrame(
        {
            "PassengerId": test["PassengerId"].astype(int),
            "Survived": predictions,
        }
    )
    submission.to_csv(OUTPUT_DIR / "submission.csv", index=False)
    feature_importance(best_model, OUTPUT_DIR)
    write_summary(cv_results, holdout_accuracy, report, confusion, OUTPUT_DIR)

    print("Model comparison:")
    print(cv_results.to_string(index=False))
    print(f"\nBest model: {best_name}")
    print(f"Holdout accuracy: {holdout_accuracy:.4f}")
    print(f"Saved Kaggle submission to: {OUTPUT_DIR / 'submission.csv'}")
    print(f"Saved summary to: {OUTPUT_DIR / 'summary.md'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Titanic survival prediction pipeline")
    parser.add_argument("--run", action="store_true", help="Run training, evaluation and submission generation.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.run:
        run_pipeline()
    else:
        print("Run `python titanic_model.py --run` to train models and create outputs.")
