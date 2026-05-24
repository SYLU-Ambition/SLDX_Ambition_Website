---
layout: page
title: 公众号文章存档
---

<script setup>
import { data } from './wechat.data.js'
import { ref, computed } from 'vue'
import { useData } from 'vitepress'

const { isDark } = useData()
const PER_PAGE = 50
const currentPage = ref(1)

const totalPages = computed(() => Math.ceil(data.articles.length / PER_PAGE))

const pagedArticles = computed(() => {
  const start = (currentPage.value - 1) * PER_PAGE
  return data.articles.slice(start, start + PER_PAGE)
})

const grouped = computed(() => {
  const map = {}
  for (const a of pagedArticles.value) {
    if (!map[a.year]) map[a.year] = []
    map[a.year].push(a)
  }
  return map
})

const yearKeys = computed(() => Object.keys(grouped.value).sort((a, b) => b - a))

function goPage(p) {
  if (p >= 1 && p <= totalPages.value) {
    currentPage.value = p
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const paginationSlice = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  if (total <= 7) {
    const ret = []
    for (let i = 1; i <= total; i++) ret.push(i)
    return ret
  }
  const ret = [1]
  if (cur > 3) ret.push('...')
  const start = Math.max(2, cur - 1)
  const end = Math.min(total - 1, cur + 1)
  for (let i = start; i <= end; i++) ret.push(i)
  if (cur < total - 2) ret.push('...')
  ret.push(total)
  return ret
})

function formatTitle(t) {
  if (!t) return ''
  return t.length > 60 ? t.slice(0, 60) + '...' : t
}
</script>

<div class="wx-archive">
<div class="wx-header">
<h1>公众号文章存档</h1>
<p class="wx-subtitle">共 {{ data.articles.length }} 篇文章，记录沈理电协的成长历程</p>
</div>

<div v-if="data.articles.length > 0">
<div v-for="year in yearKeys" :key="year" class="wx-year-group">
<h2 class="wx-year-title">{{ year }} 年</h2>
<div class="wx-article-list">
<a v-for="article in grouped[year]" :key="article.dir" :href="`/wechat/articles/${article.dir}/index.html`" target="_blank" class="wx-article-card">
<div v-if="article.hasCover" class="wx-card-cover"><img :src="`/wechat/articles/${article.dir}/cover.${article.coverExt}`" :alt="article.title" loading="lazy"/></div>
<div class="wx-card-info">
<span class="wx-card-title">{{ formatTitle(article.title) }}</span>
<div class="wx-card-meta">
<span class="wx-card-date">{{ article.date }}</span>
<span v-if="article.hasVideo" class="wx-video-badge">视频</span>
</div>
</div>
</a>
</div>
</div>

<div v-if="totalPages > 1" class="wx-pagination">
<button class="wx-page-btn" :disabled="currentPage === 1" @click="goPage(currentPage - 1)">上一页</button>
<span class="wx-page-group" v-for="p in paginationSlice" :key="p">
<span v-if="p === '...'" class="wx-page-ellipsis">...</span>
<button v-else class="wx-page-btn" :class="{ active: p === currentPage }" @click="goPage(p)">{{ p }}</button>
</span>
<button class="wx-page-btn" :disabled="currentPage === totalPages" @click="goPage(currentPage + 1)">下一页</button>
</div>
</div>

<div v-else class="wx-empty">
<p>暂无文章数据，请先运行文章归档工具。</p>
<p style="font-size: 0.85em; margin-top: 8px; opacity: 0.6;">在 wechat-archive-tool 目录中执行 python main.py 开始归档。</p>
</div>
</div>

<style scoped>
.wx-archive { max-width: 880px; margin: 0 auto; }
.wx-header { text-align: center; padding: 20px 0 10px; }
.wx-header h1 {
  font-size: 1.8em; font-weight: 700;
  background: linear-gradient(135deg, var(--vp-c-brand-1), var(--vp-c-brand-2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.wx-subtitle { color: var(--vp-c-text-2); font-size: 0.9em; margin-top: 6px; }
.wx-year-group { margin-bottom: 32px; }
.wx-year-title {
  font-size: 1.2em; font-weight: 600; color: var(--vp-c-brand-1);
  border-bottom: 2px solid var(--vp-c-brand-soft); padding-bottom: 6px; margin-bottom: 14px;
  position: sticky; top: 0; background: var(--vp-c-bg); z-index: 1;
}
.wx-article-list { display: flex; flex-direction: column; gap: 6px; }
.wx-article-card {
  display: flex; align-items: flex-start; gap: 12px; padding: 10px 14px;
  border-radius: 8px; text-decoration: none; color: var(--vp-c-text-1);
  background: var(--vp-c-bg-soft); border: 1px solid transparent; transition: all 0.2s ease;
}
.wx-article-card:hover { background: var(--vp-c-bg-mute); border-color: var(--vp-c-brand-1); transform: translateX(4px); text-decoration: none; }
.wx-card-cover { flex-shrink: 0; width: 90px; height: 63px; border-radius: 4px; overflow: hidden; background: var(--vp-c-bg-mute); }
.wx-card-cover img { width: 100%; height: 100%; object-fit: cover; }
.wx-card-info { flex: 1; min-width: 0; }
.wx-card-title { display: block; font-size: 0.95em; font-weight: 500; line-height: 1.5; color: var(--vp-c-text-1); }
.wx-card-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.wx-card-date { font-size: 0.8em; font-family: 'SF Mono','Fira Code','Fira Mono',Menlo,Consolas,monospace; color: var(--vp-c-text-3); }
.wx-video-badge { font-size: 0.7em; background: var(--vp-c-red-1); color: var(--vp-c-white); padding: 1px 6px; border-radius: 3px; font-weight: 500; }
.wx-pagination { display: flex; justify-content: center; align-items: center; gap: 4px; margin-top: 40px; padding: 20px 0; flex-wrap: wrap; }
.wx-page-group { display: contents; }
.wx-page-btn {
  min-width: 36px; height: 36px; border: 1px solid var(--vp-c-divider); border-radius: 6px;
  background: var(--vp-c-bg-soft); color: var(--vp-c-text-1); font-size: 0.9em; cursor: pointer;
  transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center; padding: 0 10px;
}
.wx-page-btn:hover:not(:disabled) { border-color: var(--vp-c-brand-1); background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.wx-page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.wx-page-btn.active { background: var(--vp-c-brand-1); color: var(--vp-c-white); border-color: var(--vp-c-brand-1); }
.wx-page-ellipsis { min-width: 36px; text-align: center; color: var(--vp-c-text-3); }
.wx-empty { text-align: center; padding: 60px 20px; color: var(--vp-c-text-2); }
@media (max-width: 768px) {
  .wx-header h1 { font-size: 1.4em; }
  .wx-article-card { padding: 8px 10px; gap: 10px; }
  .wx-card-cover { width: 70px; height: 50px; }
  .wx-card-title { font-size: 0.85em; }
  .wx-year-title { font-size: 1.05em; }
}
</style>
