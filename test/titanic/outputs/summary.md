# Titanic Survival Prediction Summary

Best model: `gradient_boosting`
5-fold CV accuracy: `0.8406 +/- 0.0150`
Holdout accuracy: `0.7933`

## Model comparison

| model               |   cv_accuracy_mean |   cv_accuracy_std | fold_scores                            |
|:--------------------|-------------------:|------------------:|:---------------------------------------|
| gradient_boosting   |           0.840619 |        0.0149992  | 0.8492, 0.8483, 0.8202, 0.8258, 0.8596 |
| random_forest       |           0.83163  |        0.00970569 | 0.8492, 0.8315, 0.8202, 0.8315, 0.8258 |
| logistic_regression |           0.829389 |        0.0162767  | 0.8436, 0.8371, 0.7978, 0.8371, 0.8315 |

## Confusion matrix

`[[94, 16], [21, 48]]`

## Interpretation

- Sex, passenger class, title, fare, cabin/deck, family size and age-related features are the most informative signals.
- Women, children, passengers in higher classes and passengers with higher fare/cabin information generally show higher survival probability.
- The final Kaggle file is `submission.csv` and contains `PassengerId,Survived`.
