<template>
  <el-container class="app-container">
    <el-aside width="220px" class="app-aside">
      <div class="logo">
        <el-icon :size="24"><Promotion /></el-icon>
        <span>Trending Agent</span>
      </div>
      <el-menu :default-active="route.path" router class="aside-menu">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>技术栈配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
.app-container { height: 100vh; }
.app-aside {
  background: #1d1e2c;
  color: #fff;
  overflow-y: auto;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  font-size: 16px;
  font-weight: 600;
  color: #f0883e;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.aside-menu {
  border-right: none;
  background: transparent;
}
.aside-menu .el-menu-item {
  color: rgba(255,255,255,0.7);
}
.aside-menu .el-menu-item:hover,
.aside-menu .el-menu-item.is-active {
  color: #fff;
  background: rgba(240,136,62,0.15);
}
.app-main {
  background: #f5f7fa;
  overflow-y: auto;
  padding: 24px;
}
</style>
