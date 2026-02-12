<template>
  <!-- Login page: no layout -->
  <router-view v-if="route.path === '/login'" />

  <!-- Main layout -->
  <el-container v-else class="app-layout">
    <!-- Header -->
    <el-header class="app-header">
      <div class="header-left">
        <el-icon :size="22" color="#f0883e" class="header-menu-btn" @click="collapsed = !collapsed"><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        <span class="header-title">🔥 GitHub Trending Agent</span>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click" @command="handleCmd">
          <span class="user-dropdown">
            <el-avatar :size="32" style="background:#f0883e">{{ userStore.user?.username?.[0]?.toUpperCase() }}</el-avatar>
            <span class="username">{{ userStore.user?.username }}</span>
            <el-tag size="small" :type="userStore.isAdmin ? 'danger' : 'info'">{{ userStore.isAdmin ? '管理员' : '用户' }}</el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <!-- Sidebar -->
      <el-aside :width="collapsed ? '64px' : '220px'" class="app-aside">
        <el-menu :default-active="route.path" router :collapse="collapsed" class="aside-menu">
          <el-menu-item index="/">
            <el-icon><DataBoard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>技术栈配置</template>
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- Content -->
      <el-main class="app-main">
        <div class="main-content">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

function handleCmd(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
.app-layout { height: 100vh; flex-direction: column; }
.app-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  z-index: 10;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-menu-btn { cursor: pointer; }
.header-title { font-size: 17px; font-weight: 600; color: #333; }
.header-right { display: flex; align-items: center; }
.user-dropdown { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; color: #333; }

.app-aside {
  background: #1d1e2c;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s;
}
.aside-menu {
  border-right: none;
  background: transparent;
  height: 100%;
}
.aside-menu:not(.el-menu--collapse) { width: 220px; }
.aside-menu .el-menu-item { color: rgba(255,255,255,0.7); }
.aside-menu .el-menu-item:hover,
.aside-menu .el-menu-item.is-active { color: #fff; background: rgba(240,136,62,0.15); }

.app-main { background: #f5f7fa; overflow-y: auto; padding: 24px; }
.main-content { max-width: 1100px; margin: 0 auto; }

/* Mobile */
@media (max-width: 768px) {
  .app-aside { position: fixed; z-index: 20; height: calc(100vh - 56px); top: 56px; }
  .app-main { padding: 16px; }
  .main-content { max-width: 100%; }
  .username { display: none; }
  .header-title { font-size: 15px; }
  .el-table { font-size: 13px; }
}
</style>
