import { h } from 'vue'
import mediumZoom from 'medium-zoom'
import { onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'
import './style.css'
import escookTheme from '@escook/vitepress-theme'
import '@escook/vitepress-theme/style.css'
import MyLayout from './MyLayout.vue'
import NCard from './NCard.vue'


// 设置中文环境
if (typeof window !== 'undefined') {
  window.NOLEBASE_LOCALE = 'zh-CN'
}

/** @type {import('vitepress').Theme} */
export default {
  extends: escookTheme,
  Layout: MyLayout,
  setup() {
    const route = useRoute()
    const initZoom = () => {
      if (typeof window !== 'undefined') {
        mediumZoom('.main img', { background: 'var(--vp-c-bg)' })
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
  enhanceApp({ app, router, siteData }) {
    app.component('NCard', NCard)
  }
}
