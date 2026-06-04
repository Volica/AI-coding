# MNIST 手写数字识别（CV 基础）

本项目实现一个基于 PyTorch + torchvision 的手写数字识别模型。代码使用 `torchvision.datasets.MNIST` 在线下载 MNIST 数据集，训练一个轻量级 CNN，并输出模型、验证结果和测试集准确率。

## 项目目标

- 使用 MNIST 数据集完成 0-9 手写数字分类。
- 掌握 CNN 基础结构：卷积、池化、BatchNorm、Dropout、全连接分类器。
- 使用简单数据增强：随机旋转、平移、缩放，提升模型泛化能力。
- 保存训练后的模型，并支持对单张本地图片进行预测。

## 数据集获取

`torchvision.datasets` 是 PyTorch 自带的数据集工具。本项目使用其中的 MNIST 数据集，运行训练命令时会自动下载到 `data/` 目录：

```python
torchvision.datasets.MNIST(root, train=True, transform=None, target_transform=None, download=False)
```

本项目实际使用方式如下：

```python
datasets.MNIST(
    root="data",
    train=True,
    transform=transform,
    download=True,
)
```

原始项目/资料来源：

- 和鲸社区项目：K 同学啊，https://www.heywhale.com/mw/project/6496efc3ae1f61137ad53e1a/content
- 和鲸社区手写数字识别项目：https://www.heywhale.com/mw/project/6a0e5ccb5ba04f7e48eeda96
- Kaggle 数据集备选链接：https://www.kaggle.com/datasets/martininf1n1ty/mnist100?resource=download

## 项目文件

- `mnist_model.py`：训练、评估、保存模型、单张图片预测的主程序。
- `requirements.txt`：运行依赖。
- `data/`：MNIST 数据下载目录，首次运行后自动生成。
- `models/mnist_cnn.pt`：训练得到的模型权重。
- `outputs/metrics.json`：测试准确率、混淆矩阵等结果。
- `outputs/training_history.csv`：每轮训练和验证指标。

## 运行方式

### 方式一：普通 PowerShell / CMD

```bash
cd "E:\系统默认\桌面\Sec\研一下\SLP\ai coding\test\minist"
pip install -r requirements.txt
python mnist_model.py --run
```

### 方式二：Anaconda PowerShell（可选）

```bash
conda create -n mnist-cnn python=3.11 -y
conda activate mnist-cnn
cd "E:\系统默认\桌面\Sec\研一下\SLP\ai coding\test\minist"
pip install -r requirements.txt
python mnist_model.py --run
```

如果电脑支持 CUDA，可根据自己的显卡和 CUDA 版本到 PyTorch 官网选择对应安装命令；CPU 也可以正常运行，只是速度较慢。

### 快速测试

第一次只想确认代码能跑通，可以减少训练样本和轮数：

```bash
python mnist_model.py --run --epochs 1 --max-train-samples 1000
```

### 预测单张图片

先完成训练，得到 `models/mnist_cnn.pt` 后，再运行：

```bash
python mnist_model.py --predict path\to\digit.png
```

图片会被自动转为灰度并缩放到 28x28。建议使用白底黑字或黑底白字的清晰数字图片，效果更稳定。

## 注意事项

- 首次运行需要联网下载 MNIST 数据集；下载成功后，后续可加 `--no-download` 使用本地缓存。
- Windows 环境下如果 DataLoader 报错，保持默认 `--num-workers 0` 即可。
- 默认训练 5 轮，CPU 上可能需要几分钟；想更快可降低 `--epochs` 或使用 `--max-train-samples`。
- `minist` 是当前文件夹名，标准数据集名称是 `MNIST`。
- 如果 `import torchvision` 报错，请重新运行 `pip install -r requirements.txt`，或确认当前终端已激活正确的 conda 环境。

## 常用参数

```bash
python mnist_model.py --run --epochs 10 --batch-size 128 --lr 0.001
python mnist_model.py --run --no-download
python mnist_model.py --run --max-train-samples 5000
```

训练完成后，终端会显示最佳验证集准确率和测试集准确率，并在 `models/`、`outputs/` 中保存结果。
