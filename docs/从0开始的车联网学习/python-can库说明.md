# python-can 库说明

本文只介绍Python-can 文档的大致內容，详细內容参考：[python-can 官方文档](https://python-can.readthedocs.io/)

## 00-简单介绍与示例

该库的一些用例：

- 被动记录 CAN 事件，如使用 [OBD-II 端口](https://en.wikipedia.org/wiki/On-board_diagnostics#OBD-II)监控汽车
- 硬件测试，汽车、摩托、船
- 模拟环境，让新硬件或代码在不接真车下，与旧虚拟系统通信、测试
- 虚拟实验，不需要你购买真实硬件就能练习一些功能

简单示例，依然采用 OOP 封装

```python
#! /usr/bin/env python
"""
展示如何发送单条信息
"""
import can 

def send_one():
    """发送单条信息"""
    with can.Bus as bus:
        msg = can.Message=(arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True)
        try: 
            bus.send(msg)
            print(f"Message sent on {bus.channel_info}")
        except can.CanError:
            print("Message NOT send")

if __name__ == "__main__":
    send_one()
```

## 01-安装

```python
 pip install python-can
```

## 02-配置

这里简要说明，配置方法有三种：Python 编写代码配置、编写配置文件配置、环境变量配置。

主要配置三个参量：

- interface
- channel
- bitrate

具体配置方法参考网站文档：[配置 · python-can](https://python-can.readthedocs.io/en/stable/configuration.html)

## 03-库 API

库 API 是写 Python 代码控制 CAN 硬件时需要的核心：

- Bus：总线
- Message：消息对象
- 文件 IO：读取与存储 CAN 数据
- 异步支持：增加高并发
- 广播管理器：定时闹钟管理，不需要循环 While 或 time.sleep() 手动管理
- 错误处理：记录错误状态，不让程序直接崩溃
- 一般设置检测：检测或配置通用设置，方便跨平台或环境时快速切换
- 位时序配置：硬件心跳，**一般不用**。使用场景为极致的性能和特殊需求，老手使用
- 内部 API：开发者使用，**调包侠不需要**

## 04-硬件接口

厂商如  Kvaser、PCAN、CANalyst-II 的硬件驱动程序清单，说明了python-can可以连上哪些东西

## 05-虚拟接口

虚拟接口用于编写与 OS 和驱动无关的测试用例。

多播 IP 接口是 Python-can 提供的一种虚拟接口，普通虚拟接口只在一个 python 进程内传递消息，多播 IP 接口利用网络协议，可以跨越进程甚至主机的边界。所以如果需要跨进程或跨主机边界发送消息，使用组播 IP 接口

时间戳保留机制demo1：

```python
import can 
bus1 = can.interface.Bus('test', interface='virtual')
bus2 = can.interface.Bus('test', interface='virtual')
msg1 = can.Message(arbitration_id=0xabcde, data=[1,2,3])
bus1 = send(msg1)
msg2 = bus2.recv()
# 假设 msg1 == msg2
assert msg1.arbitration_id == msg2.arbitration_id
assert msg1.data == msg2.data
assert msg1.timestamp != msg2.timestamp
# 时间戳会重新生成
```

时间戳保留机制demo2：

```python
import can 
# 开启保留时间戳
bus1 = can.interface.Bus('test', interface='virtual', preserve_timestamp=True)
bus2 = can.interface.Bus('test', interface='virtual')

# 硬编码一个时间戳：1639740470.051948
msg1 = can.Message(timestamp=1639740470.051948, arbitration_id=0xabcde, data=[1,2,3])
bus1 = send(msg1)
msg2 = bus2.recv()

# 断言检查 msg1 == msg2
assert msg1.arbitration_id == msg2.arbitration_id
assert msg1.data == msg2.data
assert msg1.timestamp != msg2.timestamp
# 时间戳会重新生成
```



## 05-插件接口（未填写）



## 06-其他 CAN 工具

为了保证 python-can 库边界清晰可维护，python-can 没有盲目加功能。在库的封装层次上，python-can 与 Python-UDS 等库的关系就像 socket 与 Requeset 的关系。以后想要做工程，一般都调用更高层的库，不会直接深入到 python-can 这种极低封装层。

其他的高级库例如：

1.  CAN 消息协议

- can-j1939
- canopen
- can-isotp
- python-uds
- usdoncan
- pyxcp：测量与标定协议

2. CAN 帧解析与数据处理工具

- cantools：处理 DBC 
- canmatrix：转换各种格式的 CAN 数据库文件
- pretty_j1939：将 j1939 CAN 日志整理为人类可读终端输出、或JSON，方便查看

3. 其他工具

- MicroPython CAN 类：注意这个不是库，是一个类。专门运行在 MCU 上的 MicroPython 固件自带的 can 类，与Python-can 功能类似，但 API 不同
- asammdf：处理汽车测量数据（MDF文件），在一个库之外，作者还附带开发了一个 GUI 软件

## 07-命令行工具

- can.logger：录制实时数据，并保存到文件中
- can.player：回放数据，
- can.viewer：终端 CAN 数据实时监控器，字节出现变化会高亮显示
- can.bridge：总线桥接：实现数据在二者之间的双向转发，设备间通信
- can.logconvert：转换 CAN 日志文件格式，如 blf 转 asc 或 csv

