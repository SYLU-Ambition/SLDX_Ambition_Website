import { h } from 'vue'
import mediumZoom from 'medium-zoom'
import { onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vitepress'
import './style.css'
import escookTheme from '@escook/vitepress-theme'
import '@escook/vitepress-theme/style.css'
import MyLayout from './MyLayout.vue'
import NCard from './NCard.vue'
import {
  NolebaseEnhancedReadabilitiesMenu,
  NolebaseEnhancedReadabilitiesScreenMenu,
} from '@nolebase/vitepress-plugin-enhanced-readabilities/client'
import '@nolebase/vitepress-plugin-enhanced-readabilities/client/style.css'

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
    app.component('NolebaseEnhancedReadabilitiesMenu', NolebaseEnhancedReadabilitiesMenu)
    app.component('NolebaseEnhancedReadabilitiesScreenMenu', NolebaseEnhancedReadabilitiesScreenMenu)

    // 百度统计：VitePress 是 SPA，路由切换不整页刷新，hm.js 只在首次加载执行一次，
    // 因此需要在每次路由切换后补报一次浏览，否则切换到其它页面的访问会被漏掉。
    router.onAfterRouteChange = (to) => {
      if (typeof window !== 'undefined' && window._hmt) {
        const path = to && to.path ? to.path : (window.location.pathname + window.location.search)
        window._hmt.push(['_trackPageview', path])
      }
    }
  }
}
