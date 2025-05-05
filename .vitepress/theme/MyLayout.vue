<script setup>
import DefaultTheme from 'vitepress/theme';
import { watch } from 'vue';
import Giscus from '@giscus/vue';
import { useRoute, useData, inBrowser } from 'vitepress';
// 不再需要导入 Aurora.vue
// import Aurora from './Aurora.vue';

const { page, isDark, frontmatter } = useData();
const { Layout } = DefaultTheme;

watch(isDark, (dark) => {
  if (!inBrowser) return;

  const iframe = document
    .querySelector('giscus-widget')
    ?.shadowRoot?.querySelector('iframe');

  iframe?.contentWindow?.postMessage(
    { giscus: { setConfig: { theme: dark ? 'dark' : 'light' } } },
    'https://giscus.app'
  );
});
// ... (可以保留或删除，根据你的具体需要)
</script>

<template>
  <Layout>
    <!-- 将 Aurora.vue 的 template 内容直接放在这里，并用 v-if 控制 -->
    <div
        v-if="frontmatter.layout === 'home'"
        class="aurora-container absolute flex flex-col z-[40] w-full !max-w-full items-center justify-center bg-transparent transition-bg overflow-hidden h-[60vh] -top-16 pointer-events-none opacity-[.35] dark:opacity-50">
        <div class="jumbo absolute opacity-60 animate"></div>
    </div>

    <!-- 文档内容之后的部分 -->
    <template #doc-after>
      <!-- Giscus 评论区，不在首页显示 -->
      <div v-if="frontmatter.layout !== 'home'" style="margin-top: 24px">
        <Giscus
          :key="page.filePath"
          repo="SYLU-Ambition/Ambition_Website"
          repo-id="R_kgDOOea3Bg"
          category="Genera"
          category-id="DIC_kwDOOea3Bs4CpZV7"
          mapping="title"
          strict="0"
          reactions-enabled="1"
          emit-metadata="0"
          :theme="isDark ? 'dark' : 'light'"
          input-position="top"
          lang="zh-CN"
          crossorigin="anonymous"
        />
      </div>
    </template>

  </Layout>
</template>

<style>
/* 原 MyLayout.vue 的样式 */
iframe{
  width: 100%;
  height: 400px;
  border-top-width: 0px;
  border-bottom-width: 0px;
  border-left-width: 0px;
  border-right-width: 0px;
  margin-top: 40px;
  margin-bottom: 40px;
}

th, td {
    white-space: nowrap !important; /* 不让th，td内容换行显示 */
    width: 1%; /* 强制均匀分配宽度 */
}

.main img{
  display: block;
  margin: 0 auto;
}

/* --- 从 Aurora.vue 移入的样式 --- */
.aurora-container .opacity-\[\.35\] { /* 可以给外层容器加个类名提高特异性，防止冲突 */
    opacity: .35;
}

.aurora-container .bg-transparent {
    background-color: transparent;
}

.aurora-container .overflow-hidden {
    overflow: hidden;
}

.aurora-container .justify-center {
    justify-content: center;
}

.aurora-container .items-center {
    align-items: center;
}

.aurora-container .flex-col {
    flex-direction: column;
}

.aurora-container .\!max-w-full {
    max-width: 100% !important;
}

.aurora-container .w-full {
    width: 100%;
}

.aurora-container .h-\[60vh\] {
    height: 60vh;
}

.aurora-container .flex {
    display: flex;
}

.aurora-container .z-\[40\] {
    z-index: 40;
}

.aurora-container .-top-16 {
    top: -4rem;
}

.aurora-container .absolute {
    position: absolute;
}

.aurora-container .pointer-events-none {
    pointer-events: none;
}

/* 给 .jumbo 相关的样式也加上 .aurora-container 前缀 */
.aurora-container .jumbo {
    --stripes: repeating-linear-gradient(100deg, #fff 0%, #fff 7%, transparent 10%, transparent 12%, #fff 16%);
    --stripesDark: repeating-linear-gradient(100deg, #000 0%, #000 7%, transparent 10%, transparent 12%, #000 16%);
    --rainbow: repeating-linear-gradient(100deg, #60a5fa 10%, #e879f9 16%, #5eead4 22%, #60a5fa 30%);
    contain: strict;
    contain-intrinsic-size: 100vw 40vh; /* 调整为适合布局的大小 */
    width: 100%; /* 确保宽度充满容器 */
    height: 100%; /* 确保高度充满容器 */
    /* background-image: var(--stripes), var(--rainbow); */ /* 在暗黑模式下切换 */
    background-size: 300%, 200%;
    background-position: 50% 50%, 50% 50%;
    /* height: inherit; */ /* 改为具体值或百分比 */
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    -webkit-perspective: 1000;
    perspective: 1000;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    /* filter: invert(100%); */ /* 根据暗黑模式切换 */
    -webkit-mask-image: radial-gradient(ellipse at 100% 0%, black 40%, transparent 70%);
    mask-image: radial-gradient(ellipse at 100% 0%, black 40%, transparent 70%);
    pointer-events: none;
}

/* 暗黑模式下的样式调整 */
:root.dark .aurora-container .jumbo {
  background-image: var(--stripesDark), var(--rainbow);
  filter: none; /* 暗黑模式下通常不需要反相 */
}

:root:not(.dark) .aurora-container .jumbo {
  background-image: var(--stripes), var(--rainbow);
   filter: invert(100%);
}

.aurora-container .opacity-60 {
    opacity: .6;
}

/* .aurora-container .absolute 样式已在上面定义过 */

@keyframes jumbo-animation { /* 重命名动画以避免潜在冲突 */
    0% {
        background-position: 50% 50%, 50% 50%
    }

    to {
        background-position: 350% 50%, 350% 50%
    }
}

.aurora-container .jumbo:after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    /* background-image: var(--stripes), var(--rainbow); */ /* 由父元素控制 */
    background-size: 200%, 100%;
    mix-blend-mode: difference;
    /* 暗黑模式下的处理 */
    background-image: inherit; /* 继承父元素的背景 */
}

.aurora-container .animate.jumbo:after {
    animation: jumbo-animation 90s linear infinite; /* 使用重命名的动画 */
}

/* 添加暗黑模式下的透明度切换 */
:root.dark .aurora-container.dark\:opacity-50 {
    opacity: 0.5;
}
</style>