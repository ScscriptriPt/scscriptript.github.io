# 车联网学习记录

从零开始的车联网学习，记录了我从2026年11月份开始的车联网学习方便自己复盘，诸如：

- 采购花销
- 材料来源
- 留存的笔记
- 学习路线推进

## 内容

- [python-can 库说明](python-can库说明.md)：python-can 文档速览、虚拟接口、命令行工具与上层库

## Month 1

这段任务的开始时间为 11月7日，是我第一次开始阅读 CSS 电子介绍手册的日子，目前尚未完成所有任务。

1. 阅读 [CSS Electronics](https://www.csselectronics.com/pages/can-bus-intros-tutorials) 的车联网入门介绍文档，访问官方，上方标签页的 “Guide” 下有很多入门介绍：

    - CAN Bus Explained：了解汽车总线是什么，CAN Frame 结构、仲裁、错误处理、DBC 解码等概念
    - UDS Explained：了解 UDS（统一诊断服务），其中 SID/NRC、ISO-TP，DID

2. 通读 [The Car Hacker's Handbook](https://opengarages.org/handbook/)，这本书英文版免费，中文版收费。我选择 Agent 下载英文版后，用 Zcode 的免费鸡蛋翻译成中文，在 Obsidian 内，右侧接 Copilot 插件阅读。也可以让他把电子书直接做成自己喜欢的电子书风格 HTML，直接在浏览器内阅读。

    - 入门较晦涩：概念不清楚会读的很懵，当第一次写下这段内容时为11月16日，我目前看到第八章
    - 实验实操困难：书中很多內容需要用到真实硬件，例如

        1. 汽车 ECU：这东西在咸鱼上也不好找并且昂贵。咸鱼上大多数是摩托 ECU，摩托存量低、用户少、车联网也远远不如汽车发达，ECU 破解难度低得多，研究的价值相较于汽车 ECU 极低
        2. 二进制流量包：在示例介绍中，作者不知道从哪里就瞬间掏出来一个奇怪的实验材料，并且也不告诉你这个流量包的来源，几乎不可能跟随做实验
        3. 硬件配置不提前说：例如电源、台架、逻辑分析仪、CANable，总是等你阅读到了相关章节才告诉你需要这个做实验，于是又要等上两天等硬件到。

3. 看一遍 [python-can 官方文档](https://python-can.readthedocs.io/en/stable/)。在实际编程测试中，其实很少用到。而真正用的一般是更上层的库。python-can 类似于 socket 库，而我们实际用的是 request 库，request 基于 socket 库实现

4. Linux 环境安装 [can-utils](https://github.com/linux-can/can-utils) 并创建 vcan 虚拟总线：can-utils 是一个Linux与CAN交互的命令行工具集。但是只对一个CAN Frame操作，后续会使用如 ISO-TP 等工具，can-utils 用的会少一些

5. 实操 [ICSim](https://github.com/zombieCraig/ICSim)：ICSim 是一个新手入门的，类似于闯关游戏的学习项目。`./icsim vcan0` 会配置一个图形化仪表盘， `./controls vcan0` 会发送数据包然后操作仪表盘上的数据，就像一台真车在面前一样。用户的任务是破解众多 CAN 数据包中，哪个数据包，以及这个数据包中的哪个字节真的起到了某个作用，例如关上车门，改变速度等。难度分为tier0-tier3，默认为 tier1。做这个实验之前，可以准备一个便宜的游戏手柄，你读了《The Car Hacker's Handbook》会懂我是什么意思

6. [CaringCaribou 的免硬件演练链](https://github.com/CaringCaribou/caringcaribou)：可以理解为 ICSim 的进阶升级版，对 CAN 总线进行安全测试和诊断分析。listener 扫 ID → uds discovery 定位 0x7e0/0x7e8 → 扫服务 → xcp dump 读内存
