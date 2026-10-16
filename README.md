# ScscriptriPt Blog

个人博客，基于 [Hugo](https://gohugo.io/) + [Hugo Bootstrap Theme (HBS)](https://github.com/razonyang/hugo-theme-bootstrap) 搭建，
通过 GitHub Actions 自动发布到 GitHub Pages。

- 线上地址：https://scscriptript.github.io/
- 内容语言：只有中文（简体）

---

## 一、怎么发一篇新文章

在 `content/blog/` 下建一个文件夹，里面放 `index.md`：

```
content/blog/my-first-post/index.md
```

`index.md` 开头是文章属性，照着下面写：

```toml
+++
title = "文章标题"
date = 2026-10-16T03:00:00+08:00
draft = false
tags = []
categories = []
series = []
+++

这里写摘要，列表页会显示这一段。

<!--more-->

这里开始是正文，点"阅读更多"之后才会看到。
```

### 三个最容易踩的坑

**1. 日期绝对不能写成未来时间**

Hugo 默认**不发布日期在未来的文章**——不报错，就是直接跳过，文件都不生成。

```
你写文章的时间：  2026-10-16 04:26
文章里的 date：   2026-10-16 08:00    ← 比现在晚，这篇就消失了
```

- 想正常显示：`date` 填一个**已经过去的时间**
- 不想改日期：本地预览时加 `hugo server --buildFuture`
- **注意 GitHub 上自动发布没有这个开关**，所以日期还在未来的话，线上也不会出现

**2. 网址由 `title` 决定，不是文件夹名**

网址规则在 `config/_default/config.yaml` 里：

```yaml
blog: /blog/:year/:month/:slug/
```

`:slug` 取的是 `title`。所以标题「停止所谓的"为了你好"」生成的网址是：

```
/blog/2026/10/停止所谓的为了你好/     ← 标题里的引号会被去掉
```

这意味着**改标题 = 改网址**，别人收藏的旧链接会失效。真要改的话，加一行兜底：

```toml
aliases = ["/旧的网址/"]
```

文件夹名**不影响网址**，只在一个地方有用：给文章配图。

**3. `draft = true` 的文章不会发布**

`hugo server` 本地能看到（草稿默认也会显示），但线上不会出现。写完记得改 `false`。

### 标签、分类、系列怎么填

| 字段 | 能不能随便写 | 说明 |
|---|---|---|
| `tags` | 能，随便写多少都行 | 写「网络安全」，就自动多出 `/tags/网络安全/` 页面 |
| `categories` | 能，随便写 | 同上 |
| `series` | **不能随便写** | 见下面「三、开一个系列」 |

不想要某一项，把那行删掉，或者写成 `[]`，效果一样。

细节：

- **名字里别带标点**。中文逗号、引号都会被算进名字里，变成 `标签一，标签二` 这种怪名字
- **大小写不同算两个**。`Docker` 和 `docker` 是两个标签
- **系列名改一个字就是新系列**，所以要从第一篇复制过去，别手打

### 给文章配图

把图片和 `index.md` 放在**同一个文件夹**里：

```
content/blog/my-first-post/
  index.md
  配图.png
```

正文里直接写文件名就行：

```markdown
![](配图.png)
```

---

## 二、开一个新板块（比如「笔记」）

`blog` 不是唯一能放文章的地方。想分板块，比如技术笔记单独一块，跟 `blog` 平级：

### 第一步：建文件夹 + 一个 `_index.md`

```
content/notes/_index.md
```

内容写：

```yaml
---
title: 笔记
menu:
  main:
    weight: 20
    params:
      icon: '<i class="fas fa-fw fa-book"></i>'
---
```

就完事了：

- 网址是 `/notes/`
- 顶部导航栏自动多出一个「笔记」选项卡
- `weight` 是排序，越小越靠左

`_index.md` **只管这个板块叫什么、排第几，它不是文章**。文章照常往这个文件夹里放：

```
content/notes/某篇笔记/index.md
```

### 第二步（可选）：让网址带上年月

不加也能用，但加了网址风格跟 `blog` 一致。改 `config/_default/config.yaml`：

```yaml
permalinks:
  news: /news/:year/:month/:slug/
  blog: /blog/:year/:month/:slug/
  notes: /notes/:year/:month/:slug/     ← 加这一行
```

不加这行的话，网址就是 `/notes/文件夹名/`，没有年月。

### 要不要分板块

东西多了就分，但**别一开局就开五六个**。板块多了，每写一篇都要纠结"这该放哪"，反而是负担。

建议按这个思路分：

- 长文、有想法的 → `blog`
- 技术笔记、踩坑记录（短、多、频繁）→ `notes` 之类

### 图标能用哪些

图标是**编译时按需打进去的**，不是整套都有。当前能用的约 100 个，常见的：

```
fa-book  fa-blog  fa-file  fa-newspaper  fa-shield  fa-code  fa-database
fa-link  fa-globe  fa-home  fa-folder  fa-tags  fa-columns  fa-user
fa-list  fa-cog  fa-star  fa-comments  fa-envelope  fa-rss  fa-github
fa-search  fa-history  fa-rocket  fa-map-marker-alt  fa-language ...
```

**写了个不在清单里的图标，那一栏就没有图标**（不报错，也不显示）。

要加新图标，改 `assets/icons/custom.js`：

```js
import { faShield } from '@fortawesome/free-solid-svg-icons';

const icons = [
    faBook, faBlog, faFile, faNewspaper,
    faShield,     // ← 加进数组才生效
];
```

图标名字去 https://fontawesome.com/v5/search 查，**注意是 v5**，主题用的是 5.x，v6 的名字不一样。

---

## 三、开一个系列

系列是"把几篇文章串成一套、有先后顺序"，跟标签不是一回事。

**做法只有一件事：给同一组的每篇文章写一样的 `series` 名字。**

```toml
+++
# 第一篇
title = "XSS 入门（一）：反射型"
date = 2026-10-01T10:00:00+08:00
series = ["XSS 入门"]
+++
```

```toml
+++
# 第二篇
title = "XSS 入门（二）：存储型"
date = 2026-10-02T10:00:00+08:00
series = ["XSS 入门"]
+++
```

写完就完事，网站自己生成这些页面：

```
/series/                          所有系列的列表（导航栏那个「系列」）
/series/xss-入门/                  这个系列的文章列表
```

### 四个注意点

1. **名字要从第一篇复制过去**，别手打。少个空格、多个标点、大小写不同，都会变成两个系列
2. **系列名里别用标点**（引号、括号、逗号），会被去掉或转义
3. **排序看日期，不是看序号**。想让读者按第一章→第二章读，**第一章的日期要设得最早**
4. **日期别写未来**，否则那篇不会出现在系列页里，看着像漏了一篇

### 系列和标签的区别

| | 标签 | 系列 |
|---|---|---|
| 干什么用 | 贴关键词，"这篇讲了啥" | "这几篇是一套，要连着看" |
| 一篇能有几个 | 想打几个打几个 | 一般只归一个 |
| 名字能不能随便写 | 能 | 同一组的几个必须完全一致 |

两个可以同时用：一篇笔记可以既属于 `notes` 板块，又归到某个系列里。

### 给系列加一段介绍（可选）

不建也能用。想加就建：

```
content/series/xss-入门/_index.md
```

```yaml
---
title: XSS 入门
---
这里写这个系列讲什么、适合谁看、建议怎么读。
```

### 系列的文章发到哪

**放 `content/blog/`（或你新建的板块里），跟普通文章一模一样。**

`/series/` 不是文件夹，**你不需要往里面放东西**，它是网站自动生成的列表页。

一个系列的几篇建议放同一个板块，别一篇放 `blog`、一篇放 `notes`，那样网址风格会不一致。

---

## 四、本地预览（在自己电脑上看效果）

在仓库目录下打开终端（PowerShell 或 CMD），敲：

```
hugo server
```

然后浏览器打开 http://localhost:1313

- 改任何文件（文章、配置、样式）都会**自动刷新**页面，不用重启
- 想停止：在终端里按 **Ctrl + C**
- 这个终端窗口要一直开着，关掉网站就访问不了了

### 常用命令

| 想做什么 | 命令 |
|---|---|
| 本地预览（最常用） | `hugo server` |
| 预览时连日期在未来的文章也显示 | `hugo server --buildFuture` |
| 构建到 `public\`，和线上发布效果一致 | `hugo --minify --gc --enableGitInfo` |
| 查看 Hugo 版本 | `hugo version` |

**文章在本地看不到？** 八成是日期写成了未来时间，试试 `hugo server --buildFuture`。

### 环境说明（已经配好了，这里只是记录）

这台机器上装过两个 Hugo 版本，**新版 0.168 会让这个主题直接报错**（`can't evaluate field Author`，因为 Hugo 在 0.164 删掉了 `site.Author`）。所以已经做了如下设置：

- Hugo **0.148.0** 装在 `%LOCALAPPDATA%\hugo-blog-0.148.0\`，和 GitHub 自动发布用的版本一致
- 该目录已加到**用户 PATH 的最前面**，所以 `hugo` 命令会解析到 0.148.0，压过 winget 装的 0.168
- Go 已在系统 PATH 里，Hugo 用它下载主题模块
- 原 PATH 备份在 `%LOCALAPPDATA%\hugo-blog-0.148.0\PATH-backup.txt`

> PATH 改完之后，**已经开着的终端窗口要关掉重开**才会生效。

如果哪天 `hugo version` 又显示 0.168，说明 PATH 被别的软件改了，把 `%LOCALAPPDATA%\hugo-blog-0.148.0` 重新挪到用户 PATH 最前面即可。

### 第一次运行很慢？

第一次要先下载主题模块，需要联网，可能要等一两分钟。之后就有缓存了。

如果下载失败（网络问题），设置一下国内代理再重试：

```powershell
$env:HUGO_MODULE_PROXY = "https://goproxy.cn"
hugo server
```

---

## 五、发布

```shell
git add -A
git commit -m "写一篇文章"
git push
```

推送到 `main` 分支后，GitHub Actions（`.github/workflows/gh-pages.yml`）会自动构建，
并把结果发布到 `gh-pages` 分支，也就是线上站点。大约 1~2 分钟后生效。

可以在仓库的 **Actions** 标签页看构建进度。

> **推送前先看一眼文章日期。** 日期在未来，推上去线上也不会出现，要等到那个时间点才自动冒出来。

---

## 六、我要改东西，该去哪个文件

| 想改什么 | 改哪个文件 |
|---|---|
| 站名、域名、版权、站点语言、网址规则 | `config/_default/config.yaml` |
| 中文站名（会覆盖上面那个） | `config/_default/config.zh-hans.yaml` |
| 站点简介、主题色、侧边栏个人资料、社交图标 | `config/_default/params.yaml` |
| 顶部导航栏自己加的栏目（比如「关于」） | `config/_default/menu.zh-hans.yaml` |
| 「博客 / 归档 / 系列 / 分类 / 标签」这几个导航的名字 | `content/` 下对应的 `_index.md` |
| **新开一个板块** | 见上面「二、开一个新板块」 |
| 关于我页面 | `content/about/index.md` |
| 页面头像 | `static/images/profile.webp` |
| 页头 logo | `static/images/logo.webp`（开关在 `params.yaml` 的 `logo:`） |
| 作者页头像 | `content/authors/ScscriptriPt/avatar.jpg` |
| 浏览器标签页图标 | `assets/favicon.webp` |
| 主题色、字号 | `assets/main/scss/_variables.scss` |
| 自己额外加的样式 | `assets/main/scss/_custom.scss` |
| 自己额外加的脚本 | `assets/main/js/custom.ts` |
| 新文章的模板 | `archetypes/default.md` |

### 导航栏结构说明

顶部有几个板块，它们**分成两处配置**，这是最容易搞混的地方：

**（1）板块级的选项卡**，写在各板块自己的 `_index.md` 里：

- `content/blog/_index.md` → 博客（下面带下拉）
- `content/news/_index.md` → News
- `content/archives/_index.md` → 归档（在「博客」下拉里）
- `content/series/_index.md` → 系列（在「博客」下拉里）
- `content/categories/_index.md` → 分类（在「博客」下拉里）
- `content/tags/_index.md` → 标签（在「博客」下拉里）

想改名就改那里的 `title`，想调顺序就改 `weight`。

**（2）手动加的链接**，写在 `config/_default/menu.zh-hans.yaml` 里：

```yaml
main:
  - name: 关于
    url: /about/
    weight: 10
    params:
      icon: '<i class="fas fa-fw fa-user"></i>'
```

两种写法都能加选项卡，区别是：

| | 写在 `_index.md` | 写在菜单配置文件 |
|---|---|---|
| 适合 | 一个真实存在的内容板块 | 单页、外部链接 |
| 页面不存在时 | 不会出问题 | 点了会 404 |
| 集中管理 | 分散 | 一个文件看全 |

**做下拉菜单**：父项要有 `identifier`，子项写 `parent: 那个identifier`。「博客」下拉就是这么来的。

---

## 七、升级主题

主题以 Hugo Module 的形式引入，版本记录在 `go.mod`。

```shell
hugo mod get github.com/razonyang/hugo-theme-bootstrap@master
hugo mod npm pack
npm update
git add go.mod go.sum package.json package-lock.json
git commit -m "升级主题"
```

> 国内网络如果下载模块失败，把 `config/_default/config.yaml` 里
> `# proxy: https://goproxy.cn` 这行的注释去掉。

**升级前先提交一次**，升级后本地跑 `hugo server` 确认没问题再推送。主题版本跳太多可能会报错。

---

## 八、目前还没配的东西

这些位置目前是空的或者是关掉的，需要的时候再开：

- **评论区**：原来是主题作者的 giscus 配置，已删除。要用去 https://giscus.app 申请自己的，填进 `config/_default/params.yaml`
- **打赏**：`params.yaml` 里的 `reward` 是注释状态（原配置引用的图片文件仓库里并不存在）
- **联系表单**：`params.yaml` 里的 `contact.endpoint` 是注释状态，没有后端就提交不了
- **网站统计**：`params.yaml` 里的 `analytics` 是空的
- **搜索引擎收录验证**：`params.yaml` 里的 `siteVerification` 是空的

---

## 九、目录结构

```
content/          文章和页面内容
  about/          关于我
  blog/           博客文章
  news/           动态
  archives/       归档页
  categories/     分类页
  series/         系列页
  tags/           标签页
  search/         搜索页
  offline/        离线页（PWA 用的，别删）
  authors/        作者资料
config/_default/  站点配置
archetypes/       新文章模板
assets/           需要编译的样式、脚本、图标
static/           直接复制的文件（图片等）
.github/workflows/ 自动发布配置
```

`public/`、`resources/`、`node_modules/`、`hugo_stats.json`、`.hugo_build.lock`
都是构建生成或依赖目录，已被 `.gitignore` 排除，不用管。

`content/` 下的 `archives`、`categories`、`series`、`tags`、`search`、`offline`
**是网站的固定功能页，别删**。`blog`、`news` 是内容板块，可以增删。

### 已经删掉的东西（从这里知道原来有什么）

从模板里清掉了这些用不上的文件，如果你想改用别的平台部署，需要自己重新加：

| 已删除 | 原来是干什么的 |
|---|---|
| `.gitlab-ci.yml` | GitLab CI 自动部署 |
| `netlify.toml` | Netlify 部署（里面锁的 Hugo 0.146.5 已经比本项目旧） |
| `Dockerfile` / `docker-compose.yaml` / `.dockerignore` | Docker 里跑 Hugo |
| `package.hugo.json` | Hugo module 的旧存根文件，无人引用 |
| `content/docs/` | 主题自带的安装文档（讲怎么装这个主题的，不是你的内容） |
| `content/contact/` | 联系表单页，没有后端，表单提交不了 |
| `layouts/partials/hooks/docs/` | 主题给的示例 hook，docs 删了就没用了 |
| 各页面的 `*.zh-hans.md` | 模板自带的英文版重复文件，本站只做中文，已全部删除 |

### 页头图片（logo）的开关

`static/images/logo.webp` 是页头左上角那张图。开关在 `config/_default/params.yaml`：

```yaml
logo: images/logo.webp    # 显示这张图
# logo: false             # 关掉，只显示文字
```

留空不写的话，主题会默认去加载 `images/logo.webp`。


