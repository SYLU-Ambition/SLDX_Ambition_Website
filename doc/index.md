---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "沈理电协" # 首页一级标题
  text: "Ambition战队" # 首页二级标题
  tagline: 梦以为剑，创征四方！ # 口号
  image:
    alt: Ambition队徽
    src: /home/Ambition_LOGO_LIGHT.png
  actions: # 中间跳转按钮
    - theme: brand
      text: 了解我们
      link: /Ambition_Introduction/team_introduction
    - theme: alt
      text: 我要报名
      link: /Sign_Up/group_introduction

features: # 首页下方介绍
  - icon:
      src: /home/JXZ.png
    title: 机械组
    details: 机械组负责机器人结构的设计与搭建。
  - icon:
      src: /home/DKZ.png
    title: 电控组
    details: 电控组负责机器人控制算法的编写与调试。
  - icon:
      src: /home/YJZ.png
    title: 硬件组
    details: 硬件组负责设计模块、超级电容、无线充电、检查机器人线路及机器人总体布线布局安排。
  - icon:
      src: /home/SJZ.png
    title: 视觉组
    details: 视觉组负责编写视觉算法处理图像，对获取的图像进行处理，完成自瞄、自动机器人及雷达的开发任务。
  - icon:
      src: /home/YYZ.png
    title: 运营组
    details: 运营组负责各平台账号的运营，日常素材的拍摄，海报的制作和视频的剪辑。
---
<script setup>
import Confetti from '../.vitepress/theme/confetti.vue'
</script>
<confetti />