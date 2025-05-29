import { h } from 'vue'
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
      // 确保只在浏览器环境执行
      if (typeof window !== 'undefined') {
        mediumZoom(".main img", { background: "var(--vp-c-bg)" })
      }
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
  }
}