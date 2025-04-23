<script setup>
import { onMounted } from 'vue';
onMounted(() => {
  let script = document.createElement('script');
  script.type = 'text/javascript';
  script.src = `https://volunteer.cdn-go.cn/404/latest/404.js`;
  script.setAttribute("rendertarget","div404")

  document.getElementsByTagName('head')[0].appendChild(script);
});
</script>

<template>
<div id="div404"></div>
</template>

<style lang="scss">
#div404{
  overflow-y: hidden;
}
</style>
