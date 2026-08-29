<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { inBrowser } from 'vitepress'

// 顶部滚动进度条：细条随页面滚动变宽，纯原生 + rAF 节流，性能开销极小
const progress = ref(0)
let rafId = null

function update() {
  const doc = document.documentElement
  const scrollTop = window.scrollY || doc.scrollTop
  const scrollHeight = Math.max(
    doc.scrollHeight,
    document.body.scrollHeight
  ) - window.innerHeight
  const value = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0
  progress.value = Math.min(100, Math.max(0, value))
}

function onScroll() {
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    update()
    rafId = null
  })
}

// 页面路由变化（VitePress SPA 渲染 / 高度变化）后重新计算
let observer = null

onMounted(() => {
  if (!inBrowser) return
  update()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onScroll)
  observer = new MutationObserver(() => update())
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style'] })
})

onBeforeUnmount(() => {
  if (!inBrowser) return
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  if (rafId) cancelAnimationFrame(rafId)
  observer?.disconnect()
})
</script>

<template>
  <div class="scroll-progress" aria-hidden="true" :style="{ transform: `scaleX(${progress / 100})` }"></div>
</template>

<style scoped>
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  transform-origin: 0 0;
  background: linear-gradient(90deg, var(--amb-amber), var(--amb-blue-3));
  pointer-events: none;
  transition: transform 0.1s linear;
}
</style>
