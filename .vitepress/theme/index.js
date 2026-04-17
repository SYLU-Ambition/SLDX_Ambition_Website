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
  InjectionKey,
} from '@nolebase/vitepress-plugin-enhanced-readabilities/client'
import '@nolebase/vitepress-plugin-enhanced-readabilities/client/style.css'

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
    
    // 提供中文配置
    app.provide(InjectionKey, {
      locale: 'zh-CN',
    })
  }
}
