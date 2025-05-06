<script setup>
import DefaultTheme from 'vitepress/theme';
import { watch } from 'vue';
import Giscus from '@giscus/vue';
import { useRoute, useData, inBrowser } from 'vitepress';
const { page, isDark } = useData();
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

</script>


<template>
  <div> 
    <div
        class="absolute flex flex-col z-[40] w-full !max-w-full items-center justify-center bg-transparent transition-bg overflow-hidden h-[60vh] -top-16 pointer-events-none opacity-[.35] dark:opacity-50">
        <div class="jumbo absolute opacity-60 animate"></div>
    </div>

    <Layout>
      <template #doc-after>
        <div style="margin-top: 24px">
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
  </div>
</template>


<style>
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
</style>

<style scoped>
.opacity-\[\.35\] {
  opacity: .35;
}

.bg-transparent {
  background-color: transparent;
}

.overflow-hidden {
  overflow: hidden;
}

.justify-center {
  justify-content: center;
}

.items-center {
  align-items: center;
}

.flex-col {
  flex-direction: column;
}

.\!max-w-full {
  max-width: 100% !important;
}

.w-full {
  width: 100%;
}

.h-\[60vh\] {
  height: 60vh;
}

.flex {
  display: flex;
}

.z-\[40\] {
  z-index: 40;
}

.-top-16 {
  top: -4rem;
}

.absolute {
  position: absolute;
}

.pointer-events-none {
  pointer-events: none;
}

.jumbo {
  --stripes: repeating-linear-gradient(100deg, #fff 0%, #fff 7%, transparent 10%, transparent 12%, #fff 16%);
  --stripesDark: repeating-linear-gradient(100deg, #000 0%, #000 7%, transparent 10%, transparent 12%, #000 16%);
  --rainbow: repeating-linear-gradient(100deg, #60a5fa 10%, #e879f9 16%, #5eead4 22%, #60a5fa 30%);
  contain: strict;
  contain-intrinsic-size: 100vw 40vh;
  background-image: var(--stripes), var(--rainbow);
  background-size: 300%, 200%;
  background-position: 50% 50%, 50% 50%;
  height: inherit;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  -webkit-perspective: 1000;
  perspective: 1000;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  filter: invert(100%);
  -webkit-mask-image: radial-gradient(ellipse at 100% 0%, black 40%, transparent 70%);
  mask-image: radial-gradient(ellipse at 100% 0%, black 40%, transparent 70%);
  pointer-events: none;
}

.opacity-60 {
  opacity: .6;
}

.absolute {
  position: absolute;
}

@keyframes jumbo-5f0d2d0c {
  0% {
      background-position: 50% 50%, 50% 50%
  }

  to {
      background-position: 350% 50%, 350% 50%
  }
}

.jumbo:after {
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-image: var(--stripes), var(--rainbow);
  background-size: 200%, 100%;
  mix-blend-mode: difference
}

.animate.jumbo:after {
  animation: jumbo-5f0d2d0c 90s linear infinite
}
</style>