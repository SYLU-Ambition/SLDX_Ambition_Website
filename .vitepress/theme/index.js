import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import mediumZoom from 'medium-zoom'
import { onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'
import Layout from './MyLayout.vue'
import './style.css'

/** @type {import('vitepress').Theme} */
export default {
  extends: DefaultTheme,
  
  // 布局配置
  Layout: () => {
    return h(Layout, null, {
      // 可在此处添加布局插槽配置
    })
  },

  // 图片缩放功能
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
    // 保持百度统计逻辑
    router.onBeforeRouteChange = (to) => {
      if (import.meta.env.MODE === 'production') {
        if (typeof _hmt !== 'undefined' && !!to) {
          _hmt.push(['_trackPageview', to])
        }
      }
    }
  }
}