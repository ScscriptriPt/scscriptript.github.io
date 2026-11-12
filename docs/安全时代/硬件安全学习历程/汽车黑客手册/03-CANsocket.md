## 01-socketCAN

SocketCAN = Linux 对 CAN 设备的统一管理和访问接口

socketCAN 是 Linux 提供的一套 CAN 通信框架，核心思想：不同 CAN 硬件设备统一为 Linux 网口，让程序通过 socket 访问 CAN 总线，避开各种奇怪的适配驱动

```tex
应用层：candump、cansend、Kayak、自定义 C 程序
      ↓
CAN 网络层：SocketCAN / Linux 网络协议栈——PF_CAN、CAN_RAW、CAN_BCM
      ↓
驱动层：can_dev、peak_usb、内置 CAN 控制器驱动等
      ↓
硬件层：USB CAN 适配器、PCI CAN 卡、内置 CAN 控制器
      ↓
车辆 CAN 总线，ECU 之间的通信网络
```

### CAN 帧的数据结构

SocketCAN 使用 struct can_frame 表示经典 CAN Frame，主要字段：

- can_id：CAN 标识符与相关标识
- can_dlc：经典 CAN 数据长度字段
- data：CAN 的数据內容，最多 8 字节

### 使用 C 编写程序

使用 SocketCAN 提供的 Socket 接口，像从前 socket 网络编程那样写程序（不过我没有用过C写网络编程啊喂）

一个基础的 SocketCAN 应用程序主要完成：

1. 创建 CAN Socket。
2. 获取 CAN 接口索引。
3. 绑定 CAN 接口。
4. 准备 CAN 帧。
5. 使用 `read()` 或 `write()` 收发数据。

SocketCAN 使用类似于 TCP/IP OSI 模型的方式，使用：

- PF_CAN：CAN协议族
- CAN_RAW：原始 CAN socket
- CAN_BCM：广播管理器协议

```c
socket(PF_CAN, SOCK_RAW, CAN_RAW)
```

### procfs

procfs 关注如何从 Linux 内核提供的API中查看系统运行信息，procfs 是一种虚拟文件系统，一般挂载位置为：

```bash
/proc
```

查看运行状态：

```bash
cat /proc/cpuinfo
cat /proc/meminfo
```



## 02-can-utils

can-utils 是一套操作 CAN 网络的命令行工具集合，属于一套应用程序

```bash
# 安装
## 软件源安装
sudo apt-get install can-utils
## 源码安装
git clone https://github.com/linux-can/can-utils
```

使用示例：假设已经成功连接了CAN设备，网口为can0

```bash
# 监听can0上的CAN数据
candump can0
# 发送一个CAN帧
cansend can0 123#11223344
# 生成CAN消息
cangen can0
# 重放CAN消息
canplayer -I capture.log
```

can-utils 提供很多工具，等到需要再查找着看，现在先跳过

| 工具                         | 作用                                   | 重要程度   |
| :--------------------------- | :------------------------------------- | :--------- |
| `candump`                    | 监听并显示 CAN 数据包                  | 🟢 重点     |
| `cansend`                    | 发送单个 CAN 帧                        | 🟢 重点     |
| `cangen`                     | 生成并发送 CAN 数据包                  | 🟢 重点     |
| `cansniffer`                 | 按 ID 分组观察数据包，突出显示变化字节 | 🟢 重点     |
| `canplayer`                  | 重放之前保存的数据包                   | 🟢 重点     |
| `canbusload`                 | 查看 CAN 总线负载                      | 🔵 辅助     |
| `cangw`                      | 管理不同 CAN 总线之间的网关            | 🔵 辅助     |
| `canlogserver`               | 接收并记录 CAN 数据                    | ⚪ 了解即可 |
| `asc2log` / `log2asc`        | 转换 CAN 日志格式                      | ⚪ 了解即可 |
| `isotpdump` / `isotpsend` 等 | 操作 ISO-TP 数据                       | ⚪ 后续再学 |
| `slcand`                     | 管理串行 CAN 设备                      | 🟢 配置重点 |

## 03-连接CAN硬件

CAN硬件不同，连接Linux的方式不同，现介绍三种环境：

- 内置 CAN 控制器
- USB/串口 CAN 设备
- 虚拟 CAN 网络

如果还没有购买硬件，直接跳转到虚拟机CAN网络的部分

### 3.1-内置CAN控制器

内置CAN控制器 / PCI / PCMCIA 接口卡，如 PCI CAN、嵌入式设备。

CAN 硬件需要相应的 Linux 内核驱动，才能被系统识别和使用，而驱动通常以“内核模块”的方式加载。

```bash
Linux 计算机
    ├── 内置 CAN 控制器 / PCI / PCMCIA CAN 卡
    ↓
CAN 总线接口
    ↓
CAN-H / CAN-L
    ↓
汽车 CAN 总线
```

#### 配置 CAN 连接

1. 如何确认驱动是否加载成功？

```bash
# 方法1：lsmod，查看当前已经加载的Linux内核模块
lsmod
# 方法2：dmesg，查看Linux内核日志，看到类似下面的输出
dmesg
[ 8603.743057] CAN device driver interface
[ 8603.748745] peak_usb 3-2:1.0: PEAK-System PCAN-USB adapter hwrev 28 serial FFFFFFFF (1 channel)
[ 8603.749554] peak_usb 3-2:1.0 can0: attached to PCAN-USB channel 0 (device 255)
[ 8603.749664] usbcore: registered new interface driver peak_usb
```

2. 配置 CAN 接口

```bash
# 设置 CAN 总线波特率
sudo ip link set can0 type can bitrate 500000
# 启用接口
sudo ip link set can0 up
# 查看接口
ip link show can0
```

#### 参考內容

| 常见的驱动 | 內容                         |
| ---------- | ---------------------------- |
| peak_usb   | PEAK-System USB-CAN 设备驱动 |
| sja1000    | SJA1000 CAN 控制器驱动       |
| ems_prmcia | 特定 PCMCIA CAN 驱动         |
| kvaser_pci | kvaser PCI CAN 卡驱动        |
| can_dev    | CAN 网络设备的通用驱动基础   |

### 3.2-USB/串口CAN设备

USB 设备连接计算机， USB 和 CAN 总线之间存在 USB-CAN 适配器，会使用 FTDI 等 USB 转串口芯片。FTDI 负责 USB 与转口之间转换，USB-CAN 适配器内部负责CAN通信，而 LAWICEL/SLCAN 是计算机到适配器之间使用的串口通信协议

```bash
Linux 计算机
    ↓ USB
USB-CAN 适配器
    ↓ CAN-H / CAN-L
汽车 CAN 总线
```

流程：USB 设备先被 Linux 识别为串口设备 `/dev/ttyUSB0`，再通过 `slcand` 转换成 SocketCAN 接口 `slcan0`，最后使用

1. 如何确认Linux识别了设备？

插入 USB 设备后，Linux 可能会创建一个串口设备文件，但还不是可以直接使用的 CAN 网口：

```tex
/dev/ttyUSB0
```

2. 使用 slcand 创建 CAN 网口

```bash
slcand -o -s6 -t hw -S 3000000 /dev/ttyUSB0

# 参数
-o：打开设备
-s6：设置波特率挡位为6，500kbps（适配器与汽车CAN之间），共8挡
-t hw：使用硬件流控制
-S 3000000：串口通信速率 3Mbps（计算机与适配器之间）
/dev/ttyUSB0：指定串口设备
```

3. 启动与查看

```bash
sudo ip link set up slcan0
ip link show slcan0
candump slcan0
```

### 3.3-虚拟CAN网络

Linux 提供了虚拟 CAN，在软件层面创建 CAN 网络接口。如果我们只是想要开发和测试CAN程序，不需要专门连接真实汽车

```bash
Linux 计算机
    ↓
虚拟 CAN 接口
    ↓
vcan0
    ├── candump
    └── cansend
```

操作：

1. 建立 vcan

```bash
# 加载 vcan 内核模块
sudo modprobe vcan 
# 创建虚拟接口
suod ip link add dev vcan0 type vcan
# 检查
ip link show vcan0
```

2. 测试，需要开启两个终端：终端A和终端B

```bash
candump vcan0  # 终端 A

cansend vcan0 123#11223344  # 终端 B

# 终端 A 会看到：
vcan0  123  [4]  11 22 33 44
```





