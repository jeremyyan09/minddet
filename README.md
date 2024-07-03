<div align="center" markdown>

# MindDet

English | [中文](README_CN.md)

</div>

## Introduction

MindDet is A toolbox of object detection models and algorithms based on [MindSpore](https://www.mindspore.cn/en). It provides a variety of models for the field of object detection, such as CenterNet/CenterPoint/Pointpillars/BEVFormer. With the decoupled module design, it is easy to apply or adapt MindDet to your own detection tasks.

### Major Features
* State-of-The-Art. MindDet integrates and plans to inherit multiple industry-leading SOTA models, such as CenterPoint and BevFormer, and provides training weights, training policies, and performance reports to help users quickly select and apply them to detection models.
* Flexibility and efficiency. MindDet is built on MindSpore which is an efficient DL framework that can be run on different hardware platforms (GPU/CPU/Ascend). It supports both graph mode for high efficiency and pynative mode for flexibility.

## Model List

* pointpillars - https://arxiv.org/abs/1812.05784
* centernet - https://arxiv.org/abs/1904.07850
* centerpoint - https://arxiv.org/abs/2006.11275

## Support Coming soon
* Multipath++
* Detr3d
* MatrixVT
* BEVDet
* BEVFormer
* ...

## Getting Started
MindDet provides a unified training and inference entry and various configuration files for users to easily invoke models. In addition, you can read the Readme file of each model to quickly start the training and inference process.

|     Name     |                                               Instructions                                              |
|:------------:|:------------------------------------------------------------------------------------------------:|
| pointpillars | [Quick Start](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/pointpillars/README.md) |
|  centernet   |  [Quick Start](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/centernet/README.md)   |
| centerpoint  |  [Quick Start](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/centerpoint/README.md) |

## Supported Algorithms
* Optimizer
    * Adam
    * AdamW
* LR Scheduler
    * CenterNetPolynomialDecayLR
    * CenterNetMultiEpochsDecayLR
    * OneCycle
* Loss
    * Softmax loss
    * Smooth L1 localization loss
    * Sigmoid focal cross entropy loss
    * Focal loss
    * L1 loss

## How to Contribute

We appreciate all kinds of contributions including issues and PRs to make MindDet better.

## License

This project follows the [Apache License 2.0](LICENSE.md) open-source license.
