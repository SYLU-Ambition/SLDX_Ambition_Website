import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import Layout from './MyLayout.vue' // 保留自定义布局
import './style.css' // 导入色彩配置文件
import confetti from "./confetti.vue";// 导入彩带配置文件

/** @type {import('vitepress').Theme} */
export default {
  extends: DefaultTheme,
  Layout: () => {
    // 同时保留自定义布局和默认主题扩展
    return h(Layout, null, {
      // 可通过插槽添加更多内容
      // 'sidebar-nav-before': () => h('div', '导航栏前内容')
    })
  },
  enhanceApp({ app, router, siteData }) {
    // 注册彩带组件
    app.component("confetti", confetti);

    // 保留原有统计逻辑
    router.onBeforeRouteChange = (to) => {
      if (import.meta.env.MODE === 'production') {
        if (typeof _hmt !== 'undefined' && !!to) {
          _hmt.push(['_trackPageview', to]);
        }
      }
    };
  }
}