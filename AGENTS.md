# 项目注意事项

## 架构

- VitePress 静态站点，`doc/` 为源目录
- 公众号文章存档流程：文章 HTML 存于 `doc/public/wechat/articles/` → `scripts/optimize_wechat.py` 优化 → VitePress 构建
- 文章目录页：`doc/wechat.md`（VitePress Vue SFC）
- 文章数据流：`wechat.data.js` 数据加载器 → `wechat.md` Vue 组件渲染

## 公众号文章优化

- 文章 HTML 由外部归档工具生成，存放在 `doc/public/wechat/articles/`（`_shared/` 为共享 CSS，`wechat-metadata.json` 为元数据）
- 下载后必须运行 `scripts/optimize_wechat.py` 优化（图片压缩、CSS 去重、HTML 压缩、元数据生成）

## 文章目录过滤

- 排除列表在 `doc/wechat.data.js` 和 `scripts/optimize_wechat.py` 的 SKIP 数组中
- 还自动排除标题以「转载」开头的文章
- 修改排除列表后需重新运行 `optimize_wechat.py` + `pnpm run build`

## 文件名与路径大小写敏感（重要）

本项目的**构建产物、GitHub Actions 和线上服务器全部是 Linux，文件名严格区分大小写**；
Windows / macOS（默认）不区分。所以本地预览完全正常、线上却裂图，最常见的原因就是**大小写写错**。

- **Markdown 里引用的图片路径，扩展名和文件名必须与实际文件 100% 一致**。
  - 实际文件是 `26LMS2.JPG` → 只能写 `/Ambition_Introduction/team_photos/26LMS2.JPG`
  - 写成 `26LMS2.jpg` / `26LMS2.Jpg` 在 Windows 上照样能显示，但**构建直接失败**
- **这不只是「裂图」那么简单**：`vitepress-plugin-responsive-images` 在**构建期**解析图片路径，
  大小写不匹配会让 `pnpm run build` / CI 直接报错退出：

  ```
  [vite]: Rollup failed to resolve import "/Ambition_Introduction/team_photos/26LMS2.jpg"
  ```

  改 `ignoreDeadLinks` 之类的配置**没用**，必须把路径改对。
- 目录名同样区分大小写：`team_photos` ≠ `Team_Photos`。
- **改完图片相关路径，务必跑一次 `pnpm run build`**（不是只看 `pnpm dev`），
  `dev` 模式是宽松的，`build` 才会暴露大小写问题。
- 批量重命名 / 压缩图片后尤其注意：`foo.JPG` 压成 `foo.jpg`、`x.PNG` 转成 `x.png`
  这类扩展名变化，必须同步改所有引用它的 `.md`。
- 定位问题可以用：

  ```bash
  # 找出所有 Markdown 里引用的图片，逐个核对真实文件名（大小写敏感）
  grep -rn '!\[.*\](/' doc --include='*.md'
  ```

### 已知踩坑记录

- `doc/Ambition_Introduction/team_photos.md` 曾把 `26LMS2.JPG` 误写成 `26LMS2.jpg`，
  图片文件内容毫无变化，仅扩展名大小写不同，就导致整站构建失败。

## 图片格式选择（重要）

图片由 `vitepress-plugin-responsive-images` 自动生成多尺寸变体，插件会把**源图格式**带进
变体文件名和 `<img src>`：

| 源文件格式 | 生成的回退变体 | 变体文件名后缀 |
|-----------|---------------|---------------|
| `.jpg` / `.jpeg` | `.jpg-q70.jpg` | `-q70.jpg` |
| `.png` | `.png-default.png` | `-default.png` |
| `.webp` | `.png-default.png` | `-default.png` |

**结论：源图优先用 `.jpg`，其次 `.png`，不要用 `.webp`。**

- 浏览器走 `<picture>` 会优先选 `webp-q70.webp`，所以三者差异通常看不出来；
  但**不支持 WebP 的旧浏览器/爬虫/邮件客户端会回退到 `src` 里的那个变体**，
  这时只有 jpg 源能保证拿到的是 JPEG；
- 用 `.webp` 当源，回退变体是 PNG，体积是 JPEG 的 3~5 倍（实测 720px 的图
  PNG 回退约 100KB vs JPEG 约 10~20KB）；
- `.webp` 源另外还有一层历史坑：早期版本插件对它生成过内容损坏的回退变体
  （每个文件只有几百字节的错误页），表现为**线上图片空白**。已实测当前版本不再复现，
  但仍不建议用 webp 当源。
- **不要为了「体积小」把源图转成 `.webp`**。省的是源图本身几十 KB，
  换来的是回退变体大几倍，得不偿失。

改完图片引用/替换图片格式后，务必 `pnpm run build` 并确认：

```bash
# 看变体是否按预期格式生成（不该出现 *.png-default.png 之外的异常）
ls .vitepress/dist/_responsive-images/ | grep <图片名小写>
```

## 已知问题

- `no_desc_title` 类文章（图片分享型）在手机端标题可能不可见，可删目录重下
- VitePress 中 `.md` 文件不要用 `<template>` 标签，用 `<div>` 代替
- **VitePress 社区主题组件（如 `VPTeamMembersItem`）的样式在 bundle 里排在
  `style.css` 之后**，且特异性相同。想覆盖它们必须提高特异性或加 `!important`；
  但更好的做法是**从结构上让数据一致**（例如团队卡片成员要么都有 `desc`、要么都没有），
  而不是靠 `padding` 硬凑。
- 团队成员卡片里 `desc` 存在与否会带来约 42px 高度差（`.desc` 自带 `padding-top:16px`
  + 一行行高），导致社交图标行错位。**保持卡片数据结构一致**即可，不要用 padding 补。

## 常用命令

```bash
# 开发
pnpm dev                          # VitePress 开发服务器

# 构建部署
python3 scripts/optimize_wechat.py  # 优化图片/CSS
pnpm run build                      # 构建 VitePress
```

## 提交规范（重要）

- **不要用 `git add .` / `git commit -a` 一把梭**。工作区常伴有大量「图片重压缩漂移」改动，务必只 `git add` 本次真正要改的文件，避免把噪音一起提交。
- **`scripts/optimize_wechat.py` 是幂等压缩**（`JPEG_QUALITY`、`optimize=True`），对已压缩图片重复运行会产生**字节级漂移**：表现为 `git status` 里大量 `.jpg` 的 `M`（内容修改），`git diff --stat` 却是 **0 insertions / 0 deletions**。
  - 这类改动**没有净收益、无需提交**。主分支上的图片往往已优化过，直接 `git restore doc/public/wechat/` 丢弃即可。
  - 仅当确有**新文章 / 新图片**需要优化时才运行并提交。
- **本地备份目录绝不可提交**：`doc/public原图备份/`、`doc/wechat-backups/`（均已被 gitignore）。曾因误提交原图备份导致仓库膨胀到 GB 级而被 GitHub 拒收，务必保持不入库。
- 提交信息遵循中文描述，如 `ci: ...`、`feat: ...` 前缀惯例（见历史提交）。
