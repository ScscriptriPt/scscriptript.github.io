# CTF

**目录**

- [pwnable.kr](https://pwnable.kr/)
- [ROP Emporium](#rop-emporium)：ROP 练习
- [CryptoHack](#cryptohack)：密码学挑战
- [Sekai CTF](https://2026.ctf.sekai.team/)
- [SECCON](https://ctf.seccon.jp/)
- [Lakera Agent Breaker](https://play.lakera.ai/agent-breaker)：Agent / 提示词注入
- [HackAPrompt](https://www.hackaprompt.com/)：Agent / 提示词注入

## ROP Emporium {#rop-emporium}

网址：[ropemporium.com](https://ropemporium.com/)

### 技术背景

现代程序启用栈保护之后，无法像早期漏洞利用那样在栈上写入 shellcode 并跳转执行。攻击者由此转向另一种思路：程序自身包含大量现成的代码片段（gadget），每段仅一至两条指令并以 `ret` 结尾。将这些片段拼接起来，即可让程序按攻击者的意图逐段执行。这种方法称为面向返回的编程（Return-Oriented Programming，ROP）。

ROP Emporium 是专门训练该技术的题目集。

### 内容结构

平台共提供八道题目，难度依次递增：

| 序号 | 题目 | 考察点 |
|---|---|---|
| 1 | ret2win | 程序中存在直接输出 flag 的函数，改写返回地址即可 |
| 2 | split | 组合前面学到的技术 |
| 3 | callme | 连续调用三个函数并正确传参，同时对比 32 位与 64 位的传参差异 |
| 4 | write4 | 寻找写入类 gadget，构造任意写原语 |
| 5 | badchars | 部分字符无法进入内存（如换行、空字节），需要绕过 |
| 6 | fluff | 可用 gadget 不明显，需要筛选 |
| 7 | pivot | 栈空间不足，需要将栈迁移至其他位置 |
| 8 | ret2csu | gadget 稀疏的环境下，利用程序初始化代码构造参数 |

每道题提供四个架构的二进制文件：x86_64、x86、ARMv5、MIPS，合计 32 个可执行文件。不包含 ARM64 版本。

### 设计取向

平台刻意剥离了逆向与漏洞挖掘环节。八道题的漏洞均为同一个未做边界检查的栈溢出，学习者不需要寻找漏洞，只需专注于构造 ROP 链。这是它的优点，将一个技术点训练到熟练；也是它的局限，完成之后仍然不具备漏洞挖掘能力。

平台不设账号、判题与进度记录。学习者下载二进制文件后在本地运行，目标是读取程序目录下的 flag.txt。首页提供一份初学者指南，说明了栈对齐、读写长度等常见问题。

### 维护状态

平台基本停止更新。截至 2026 年仍可正常访问，但题目数量仍为八道，二进制文件仍基于 libc 2.24。首页同时推广作者的付费课程 HeapLAB（讲解堆利用），构成其商业入口。

### 适用阶段

位于 pwn.college 黄带前后。用一周时间完成八道题，即可建立 ROP 的基本手感。

## CryptoHack {#cryptohack}

网址：[cryptohack.org](https://cryptohack.org/)

### 平台形态

密码学学习中存在一个常见断层：教材上的数学推导可以理解，面对实际题目却不知从何入手。CryptoHack 的定位正是填补这一断层。

平台由两位英国从业者于 2020 年建立，目前包含 316 道题目，分为课程与题库两种形态。

### 课程

Courses 共 5 门、64 节，采用「先读讲义、再做题目」的线性结构：Introduction to CryptoHack、Modular Arithmetic、Symmetric Cryptography、Public-Key Cryptography、Elliptic Curves。适合从零开始的学习者。

### 题库

Challenges 按主题分类，可按需选做。这是平台的主要价值所在：

| 分类 | 内容 |
|---|---|
| Introduction | 编码与异或等基础内容 |
| Symmetric Ciphers | 对称加密，AES 各种工作模式的失效方式 |
| RSA | 教科书式 RSA 的经典缺陷（小指数、共模、Wiener 攻击等） |
| Diffie-Hellman | 密钥交换协议的常见问题 |
| Elliptic Curves | 椭圆曲线，包含 pairing 与异常曲线 |
| Hash Functions | 哈希函数与长度扩展攻击 |
| Crypto on the Web | 真实协议中的密码学错误 |
| Lattices | 格密码，后量子方向的主要内容 |
| Isogenies | 同源密码，同属后量子方向 |
| ZKPs | 零知识证明 |
| CTF Archive | 真实赛题归档，难度最高 |

### 技术要求

几乎每道题都需要编写脚本，官方推荐使用 Python 3，配合 PyCryptodome 与 gmpy2，进阶题目还需要 SageMath。平台提供 Docker 镜像，可以省去环境配置。

难度曲线较陡。前半部分较为平缓，自格密码开始需要线性代数与抽象代数的基础。这并非平台设计的问题，而是学科本身的要求。

平台完全免费，依靠 Patreon 捐赠与赞助商维持，页面同时展示 Zellic、Include Security 等公司的招聘信息。注册时需要先完成一道凯撒密码题。

### 适用阶段

适用于计划从事密码学方向、或希望理解 TLS、RSA、数字签名等日常技术失效原因的学习者。完成全部内容约需 200 小时以上。
