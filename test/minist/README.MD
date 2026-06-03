MNIST手写数字识别（CV基础）

目标：实现手写数字识别

技能重点：CNN架构设计（LeNet→ResNet）、数据增强（旋转/平移）、模型轻量化（知识蒸馏）

高阶玩法：在Kannada MNIST数据集实现迁移学习

数据集来源：
本项目来源于和鲸社区，使用转载需要标注来源
作者: K同学啊
来源: https://www.heywhale.com/mw/project/6496efc3ae1f61137ad53e1a/content
torchvision.datasets是Pytorch自带的一个数据库，我们可以通过代码在线下载数据，这里使用的是torchvision.datasets中的MNIST数据集。
```
torchvision.datasets.MNIST(root, train=True, transform=None, target_transform=None, download=False)
```

项目来源1：和鲸社区手写数字识别（推荐）https://www.heywhale.com/mw/project/6a0e5ccb5ba04f7e48eeda96


项目数据链接2：kaggle
https://www.kaggle.com/datasets/martininf1n1ty/mnist100?resource=download