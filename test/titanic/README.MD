# 项目名：泰坦尼克生存预测（分类入门）

特点：可视化、分类、经典、难度适中

数据集：12列特征（含年龄/舱位等级等）

技能重点：缺失值填充策略（众数/中位数）、类别特征编码（One-Hot vs Target Encoding）、模型可解释性分析（SHAP值）

挑战目标：在Kaggle Leaderboard冲进前10%（Accuracy>0.81）

### 项目目标

1912年4月15日，在首航期间，被广泛认为“不可沉没”的泰坦尼克号在撞上冰山后沉没。不幸的是，救生艇数量不足以容纳所有人，导致2224名乘客和船员中有1502人遇难。

虽然生存有一定的运气成分，但似乎有些群体比其他群体更有可能存活。

- 在本挑战中，我们要求你构建一个预测模型，回答“哪些类型的人更有可能存活？”这个问题，利用乘客数据（如姓名、年龄、性别、社会经济阶层等）。

- （可选）可视化结果（比如饼状图、柱状图）

- （趣味可选）自己文字总结一下哪些类型的人更有可能存活

### （重要）项目链接：
如果对于项目了解不足，可以通过url访问原项目了解更多
https://www.kaggle.com/code/alexisbcook/titanic-tutorial

### 获取数据的方法
```
import kagglehub

# Download latest version
path = kagglehub.competition_download('titanic')

print("Path to competition files:", path)
```

### 数据介绍

在这场比赛中，你将获得两个类似的数据集，包含乘客信息，如姓名、年龄、性别、社会经济阶层等。一个数据集标题为，另一个数据集标题为 。train.csvtest.csv

Train.csv将包含机上乘客部分细节（确切地为891人），重要的是，将揭示他们是否幸存，也就是所谓的“实地真相”。

数据集包含类似信息，但未披露每位乘客的“真实情况”。预测这些结果是你的责任。test.csv

利用数据中发现的模式，预测机上其他418名乘客（见于）是否幸存。train.csvtest.csv

请查看“数据”标签，进一步探索数据集。一旦你觉得自己已经创建了一个有竞争力的模型，请提交给 Kaggle，看看你的模型在我们的排行榜上与其他 Kaggler 的排名。



### 可视化项目链接（可结合）：
https://www.heywhale.com/mw/project/606d6a50d884b70017a76734/dataset

## 本项目代码

已补充完整代码文件：`titanic_model.py`

运行方式：

```bash
pip install -r requirements.txt
python titanic_model.py --run
```

运行后会在 `outputs/` 目录生成：

- `submission.csv`：可提交到 Kaggle 的预测结果，格式为 `PassengerId,Survived`
- `model_comparison.csv`：Logistic Regression、Random Forest、Gradient Boosting 的 5 折交叉验证结果
- `summary.md` / `metrics.json`：最佳模型、验证集准确率、混淆矩阵和简要结论
- `feature_importance.csv` / `feature_importance.png`：模型可解释性结果
- `survival_count.png`、`survival_by_sex.png`、`survival_by_pclass.png`、`age_distribution.png`：数据可视化图表

当前本地运行结果中，最佳模型为 `gradient_boosting`，5 折交叉验证 Accuracy 约为 `0.8406`。
