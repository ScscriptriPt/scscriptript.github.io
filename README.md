# ScscriptriPt Blog

个人博客，基于 [Hugo](https://gohugo.io/) + [Hugo Bootstrap Theme (HBS)](https://github.com/razonyang/hugo-theme-bootstrap) 搭建，
通过 GitHub Actions 自动发布到 GitHub Pages。

- 线上地址：https://scscriptript.github.io/
- 内容语言：只有中文（简体）

---

## 一、怎么发一篇新文章

在 `content/blog/` 下建一个文件夹，里面放 `index.md`。文件夹名就是网址里那一段。

```
content/blog/my-first-post/index.md
```

`index.md` 开头是"front matter"（文章属性），照着下面写：

```toml
+++
title = "文章标题"
date = 2026-01-01T12:00:00+08:00
draft = false
tags = ["标签一", "标签二"]
categories = ["分类一"]
series = ["专栏一"]
+++

这里写摘要，列表页会显示这一段。

<!--more-->

这里开始是正文，点"阅读更多"之后才会看到。
```

**注意**：`draft = true` 的文章不会发布。写完记得改成 `false`。

---

## 二、本地预览（在自己电脑上看效果）

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
| 构建到 `public\`，和线上发布效果一致 | `hugo --minify --gc --enableGitInfo` |
| 查看 Hugo 版本 | `hugo version` |

### 环境说明（已经配好了，这里只是记录）

这台机器上装过两个 Hugo 版本，**新版 0.168 会让这个主题直接报错**（`can't evaluate field Author`，因为 Hugo 在 0.164 删掉了 `site.Author`）。所以已经做了如下设置：

- Hugo **0.148.0** 装在 `%LOCALAPPDATA%\hugo-blog-0.148.0\`，和 GitHub 自动发布用的版本一致
- 该目录已加到**用户 PATH 的最前面**，所以 `hugo` 命令会解析到 0.148.0，压过 winget 装的 0.168
- Go 已在系统 PATH 里，Hugo 用它下载主题模块
- 原 PATH 备份在 `%LOCALAPPDATA%\hugo-blog-0.148.0\PATH-backup.txt`

如果哪天 `hugo version` 又显示 0.168，说明 PATH 被别的软件改了，把 `%LOCALAPPDATA%\hugo-blog-0.148.0` 重新挪到用户 PATH 最前面即可。

### 第一次运行很慢？

第一次要先下载主题模块，需要联网，可能要等一两分钟。之后就有缓存了。

如果下载失败（网络问题），设置一下国内代理再重试：

```powershell
$env:HUGO_MODULE_PROXY = "https://goproxy.cn"
hugo server
```

---

## 三、发布

```shell
git add -A
git commit -m "写一篇文章"
git push
```

推送到 `main` 分支后，GitHub Actions（`.github/workflows/gh-pages.yml`）会自动构建，
并把结果发布到 `gh-pages` 分支，也就是线上站点。大约 1~2 分钟后生效。

可以在仓库的 **Actions** 标签页看构建进度。

---

## 四、我要改东西，该去哪个文件

| 想改什么 | 改哪个文件 |
|---|---|
| 站名、域名、版权、站点语言 | `config/_default/config.yaml` |
| 中文站名（会覆盖上面那个） | `config/_default/config.zh-hans.yaml` |
| 站点简介、主题色、侧边栏个人资料、社交图标 | `config/_default/params.yaml` |
| 顶部导航栏自己加的栏目 | `config/_default/menu.zh-hans.yaml` |
| 「博客 / 归档 / 专栏 / 分类 / 标签」这几个导航的名字 | `content/` 下对应的 `_index.md` |
| 关于我页面 | `content/about/index.md` |
| 页面头像 | `static/images/profile.webp` |
| 浏览器标签页图标 | `assets/favicon.webp` |
| 主题色、字号 | `assets/main/scss/_variables.scss` |
| 自己额外加的样式 | `assets/main/scss/_custom.scss` |
| 自己额外加的脚本 | `assets/main/js/custom.ts` |
| 新文章的模板 | `archetypes/default.md` |

### 导航栏结构说明

顶部「博客」是一个带下拉的菜单，它下面的四项**不在** `menu.zh-hans.yaml` 里，
而是写在各自主页的 front matter 里：

- `content/blog/_index.md` → 博客
- `content/archives/_index.md` → 归档（下拉第一项）
- `content/series/_index.md` → 专栏
- `content/categories/_index.md` → 分类
- `content/tags/_index.md` → 标签

`menu.zh-hans.yaml` 里目前只有一项「关于」。想加新栏目就在那个文件里追加。

---

## 五、升级主题

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

---

## 六、目前还没配的东西

这些位置目前是空的或者是关掉的，需要的时候再开：

- **评论区**：原来是主题作者的 giscus 配置，已删除。要用去 https://giscus.app 申请自己的，填进 `config/_default/params.yaml`
- **打赏**：`params.yaml` 里的 `reward` 是注释状态（原配置引用的图片文件仓库里并不存在）
- **联系表单**：`params.yaml` 里的 `contact.endpoint` 是注释状态，没有后端就提交不了
- **网站统计**：`params.yaml` 里的 `analytics` 是空的
- **搜索引擎收录验证**：`params.yaml` 里的 `siteVerification` 是空的

---

## 七、目录结构

```
content/          文章和页面内容
  about/          关于我
  blog/           博客文章
  archives/       归档页
  categories/     分类页
  series/         专栏页
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

### 已经删掉的东西（从这里知道原来有什么）

从模板里清掉了这些用不上的文件，如果你想改用别的平台部署，需要自己重新加：

| 已删除 | 原来是干什么的 |
|---|---|
| `.gitlab-ci.yml` | GitLab CI 自动部署 |
| `netlify.toml` | Netlify 部署（里面锁的 Hugo 0.146.5 已经比本项目旧） |
| `Dockerfile` / `docker-compose.yaml` / `.dockerignore` | Docker 里跑 Hugo |
| `package.hugo.json` | Hugo module 的旧存根文件，无人引用 |
| `content/news/` | 「动态」栏目，一篇文章都没有，纯空壳 |
| `content/docs/` | 主题自带的安装文档（讲怎么装这个主题的，不是你的内容） |
| `content/contact/` | 联系表单页，没有后端，表单提交不了 |
| `layouts/partials/hooks/docs/` | 主题给的示例 hook，docs 删了就没用了 |

另外 `static/images/logo.webp` 这张图**还在**，但它目前是主题作者的标志，
已经在 `params.yaml` 里用 `logo: false` 关掉了，页面不会显示它。
等你做好自己的 logo 覆盖同名文件，再把那行改成 `logo: images/logo.webp` 即可。

