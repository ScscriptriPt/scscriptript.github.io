UDS：统一诊断服务

重点內容：
1. CAN Bus 上的 UDS（UDSonCAN）
2. 基于 CAN 的诊断（DoCAN）
3. ISO-TP 协议
4. UDS、OBD2、WWH-OBD和OBDonUDS之间的区别
5. 示例操作：如何请求、记录、解码 UDS 消息


UDS：用于汽车 ECU 的通信协议，实现诊断、固件更新、例行测试。在应用中：测试工具为 Client，ECU为Server，以CS架构通信


UDS 的 OSI 结构图：

![[Pasted image 20261108182457.png]]


![[Pasted image 20261108182508.png]]

UDS 不存在标准连接器，很多连接器都可以使用 UDS 协议


UDS 请求帧结构：

![[Pasted image 20261108182534.png]]


- UDS 的安全性通过 session 控制（身份验证）来实现。ECU 向测试人员发送一个种子，测试人员生成一个密钥，才能访问关键服务，为了保持权限，测试人员需要定期发送消息，来证明自身在场

- DTC：故障诊断码；数据标识符：DID

- Sub Function Btye：在读取 DTC 时，可以用 Sub Function Byte 来控制报告类型
- 请求数据参数：



# 视频

UDS 负责多种文件