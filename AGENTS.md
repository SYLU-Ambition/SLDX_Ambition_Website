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

## 已知问题

- `no_desc_title` 类文章（图片分享型）在手机端标题可能不可见，可删目录重下
- VitePress 中 `.md` 文件不要用 `<template>` 标签，用 `<div>` 代替

## 常用命令

```bash
# 开发
pnpm dev                          # VitePress 开发服务器

# 构建部署
python3 scripts/optimize_wechat.py  # 优化图片/CSS
pnpm run build                      # 构建 VitePress
```
