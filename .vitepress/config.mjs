import { defineConfig } from 'vitepress';
import { withResponsiveImages } from 'vitepress-plugin-responsive-images';
import nav from './nav.mjs';
import sidebar from './sidebar.mjs';
import socialLinks from './socialLinks.mjs';

const SITE_URL = 'https://www.sldx-ambition.top';
const SITE_TITLE = '沈理电协 Ambition 战队';
const SITE_DESC = '沈阳理工大学电子技术与应用协会 Ambition 战队官方网站 - 梦以为剑，创征四方！';
const OG_IMAGE = '/home/Ambition_LOGO_LIGHT.png';

// https://vitepress.dev/reference/site-config
export default withResponsiveImages(defineConfig({
  lang: 'zh-CN',
  head: [
    ["link", { rel: "icon", href: "/home/Ambition_LOGO_LIGHT.png" }],
    ["meta", { name: "description", content: SITE_DESC }],
    ["meta", { name: "baidu-site-verification", content: "codeva-pJXIGYLWho" }],
    // OpenGraph / 社交分享卡片
    ["meta", { property: "og:site_name", content: SITE_TITLE }],
    ["meta", { property: "og:title", content: SITE_TITLE }],
    ["meta", { property: "og:description", content: SITE_DESC }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:url", content: SITE_URL }],
    ["meta", { property: "og:image", content: OG_IMAGE }],
    ["meta", { property: "og:locale", content: "zh_CN" }],
    ["meta", { name: "twitter:card", content: "summary_large_image" }],
    ["meta", { name: "twitter:title", content: SITE_TITLE }],
    ["meta", { name: "twitter:description", content: SITE_DESC }],
    ["meta", { name: "twitter:image", content: OG_IMAGE }]
  ],
  title: "沈理电协Ambition战队",//网页大标题
  description: SITE_DESC,
  sitemap: { hostname: SITE_URL },
  cleanUrls: true,//清除URL中的.html后缀
  themeConfig: {
    outlineTitle: '目录',
    outline: [2, 6],
    logo: {
      light: '/home/SLDX_LOGO_LIGHT.png',
      dark: '/home/SLDX_LOGO_DARK.png'
    },

    nav: nav,//页眉按钮

    sidebar: sidebar,//左侧边栏

    socialLinks: socialLinks,//跳转
footer: {//页脚
// 在这里添加友链
message: `<span class="footer-slogan">梦以为剑，创征四方！</span>`,
      copyright:
        `<div class="footer-links">
          <a href="https://www.sylu.edu.cn/" target="_blank" rel="noopener noreferrer" class="footer-link">沈阳理工大学 官网</a>
          <a href="https://www.robomaster.com/zh-CN" target="_blank" rel="noopener noreferrer" class="footer-link">RoboMaster 官网</a>
          <a href="https://bbs.robomaster.com/" target="_blank" rel="noopener noreferrer" class="footer-link">RoboMaster 论坛</a>
        </div>
        <div class="footer-copyright">${new Date().getFullYear()} © 沈理电协 Ambition 战队 · 运营组 Zhan_Kong</div>`,
    },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },
    lastUpdated: {//更新时间设置
      text: '更新时间',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'medium'
      }
    },
    docFooter: {//页面底部跳转
      prev: '上一篇',
      next: '下一篇'
    },
    returnToTopLabel: '返回顶部',
    lightModeSwitchTitle: '浅色模式',
    darkModeSwitchTitle: '深色模式',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '切换主题',
  },
    vite: {
        ssr: {
            noExternal: ['@escook/vitepress-theme', 'vitepress', '@nolebase/vitepress-plugin-enhanced-readabilities', '@nolebase/ui'],
        },
    },
  srcDir: './doc',//MD页面根目录
  lastUpdated: true,//更新时间开关
  markdown: {
    lineNumbers: true,//代码块行数
  },
  base: '/',
}), {
  // 图片响应式多尺寸 + WebP 压缩（含 loading="lazy" 懒加载）
  // 只用 webp：编码快、文件仍明显变小，兼顾构建速度与收益
  widths: [480, 720, 960, 1440],
  formats: ['webp'],
})