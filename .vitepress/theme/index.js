import { h } from 'vue'
import DefaultTheme from 'vitepress/theme' 
import mediumZoom from 'medium-zoom'
import { onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'
import './style.css' 
import escookTheme from '@escook/vitepress-theme'
import '@escook/vitepress-theme/style.css' 
import MyLayout from './MyLayout.vue' 
import NCard from './NCard.vue' 

/** @type {import('vitepress').Theme} */
export default {
  extends: escookTheme,
  Layout: MyLayout, 
  setup() {
    const route = useRoute()
    const initZoom = () => {
      mediumZoom(".main img", { background: "var(--vp-c-bg)" })
    }

    onMounted(() => {
      initZoom()
    })

    watch(
      () => route.path,
      () => nextTick(() => initZoom())
    )
  },

  // 应用增强配置
  enhanceApp({ app, router, siteData }) {
    // --- 注册全局组件 ---
    app.component('NCard', NCard) // 注册 NCard 组件

    // --- 保持百度统计逻辑 ---
    if (import.meta.env.PROD) {
      router.onBeforeRouteChange = (to) => {
        if (typeof _hmt !== 'undefined' && !!to) {
          try {
            _hmt.push(['_trackPageview', to])
          } catch (e) {
            console.error('Baidu Analytics Error:', e)
          }
        }
      }
    }
  }
}