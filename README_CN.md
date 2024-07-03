<div align="center" markdown>

# MindDet

[English](README.md) | 中文

</div>

## 简介

MindDet是一个基于[MindSpore](https://www.mindspore.cn/en)的物体检测模型和算法工具箱。它提供多种用于物体检测领域的模型，比如CenterNet、CenterPoint、Pointpillars、BEVFormer等，通过解耦的模块设计，您可以轻松地将MindDet应用到您自己的检测任务中。

### 主要特性
* 高性能 MindDet集成和计划继承多种业界领先SOTA模型，例如CenterPoint、BevFormer等，提供训练权重、训练策略和性能报告，帮助用户快速选型并将其应用于检测模型。
* 灵活高效 MindDet基于高效的深度学习框架MindSpore开发，具有自动并行和自动微分等特性，支持不同硬件平台上（CPU/GPU/Ascend），同时支持效率优化的静态图模式和调试灵活的动态图模式。

## 模型支持列表

* pointpillars - https://arxiv.org/abs/1812.05784
* centernet - https://arxiv.org/abs/1904.07850
* centerpoint - https://arxiv.org/abs/2006.11275

## 即将支持
* Multipath++
* Detr3d
* MatrixVT
* BevDet
* BevFormer
* ...

## 快速入门
MindDet提供了统一的训练和推理入口以及丰富的配置文件，便于用户方便的调用各个模型。此外，用户可以通过阅读各个模型的Readme文档，快速启动训练和推理流程。

| 名称    |                                               使用说明                                               |
| :------: |:------------------------------------------------------------------------------------------------:  |
| pointpillars | [快速开始](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/pointpillars/README.md) |
| centernet  |  [快速开始](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/centernet/README.md)     |
| centerpoint |  [快速开始](https://github.com/jeremyyan09/minddet/blob/master/minddet/models/centerpoint/README.md)  |


## 支持算法
* 优化器
    * Adam
    * AdamW
* 学习率调度器
    * CenterNetPolynomialDecayLR
    * CenterNetMultiEpochsDecayLR
    * OneCycle
* 损失函数
    * Softmax loss
    * Smooth L1 localization loss
    * Sigmoid focal cross entropy loss
    * Focal loss
    * L1 loss

## 贡献方式

欢迎开发者用户提issue或提交代码PR，或贡献更多的算法和模型，一起让MindDet变得更好。

## 许可证

本项目遵循[Apache License 2.0](LICENSE.md)开源协议。
