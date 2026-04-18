<template>
  <a
    v-if="show"
    :href="editLink"
    target="_blank"
    rel="noopener noreferrer"
    class="edit-on-github"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
    <span>{{ text }}</span>
  </a>
</template>

<script setup>
import { computed } from 'vue'
import { useData, useRoute } from 'vitepress'

const { page } = useData()
const route = useRoute()

const repo = 'SYLU-Ambition/SLDX_Ambition_Website'
const docsDir = 'doc'

const show = computed(() => {
  const path = route.path
  return !path.includes('/404.html') && !path.includes('/contents')
})

// 将路由路径转换为 GitHub 上的文件路径
const editLink = computed(() => {
  const path = route.path.replace(/\/$/, '')
  // 将 /xxx/yyy/ 转换为 xxx/yyy.md
  const filePath = path.replace(/^\//, '').replace(/\.html$/, '') + '.md'
  return `https://github.com/${repo}/edit/main/${docsDir}/${filePath}`
})

const text = computed(() => {
  return '在 GitHub 上编辑此页'
})
</script>

<style scoped>
.edit-on-github {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  margin-top: 24px;
  font-size: 14px;
  font-weight: 500;
  color: var(--vp-c-brand-1);
  background-color: var(--vp-c-bg-soft);
  border-radius: 6px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.edit-on-github:hover {
  color: var(--vp-c-brand-2);
  background-color: var(--vp-c-bg-soft-up);
  text-decoration: none;
}

@media (max-width: 768px) {
  .edit-on-github {
    width: 100%;
    justify-content: center;
  }
}
</style>
