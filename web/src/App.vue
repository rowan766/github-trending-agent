<template>
  <!-- Login page -->
  <router-view v-if="route.path === '/login'" />

  <!-- Main layout -->
  <el-container v-else class="app-layout">
    <el-header class="app-header">
      <div class="header-left">
        <el-icon :size="22" color="#f0883e" class="header-menu-btn" @click="collapsed = !collapsed">
          <Fold v-if="!collapsed" /><Expand v-else />
        </el-icon>
        <span class="header-title">🔥 GitHub Trending Agent</span>
      </div>
      <div class="header-right">
        <el-dropdown trigger="click" @command="handleCmd">
          <span class="user-dropdown">
            <el-avatar :size="32" style="background:#f0883e">
              {{ userStore.user?.username?.[0]?.toUpperCase() }}
            </el-avatar>
            <span class="username">{{ userStore.user?.username }}</span>
            <el-tag size="small" :type="userStore.isAdmin ? 'danger' : 'info'">
              {{ userStore.isAdmin ? '管理员' : '用户' }}
            </el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人中心
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
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
            <el-icon><UserFilled /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <div class="main-content">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>

  <!-- Profile dialog -->
  <el-dialog v-model="showProfile" title="个人中心" width="500px" destroy-on-close>
    <el-form :model="profileForm" label-width="100px">
      <el-form-item label="用户名">
        <el-input :value="userStore.user?.username" disabled />
      </el-form-item>
      <el-form-item label="角色">
        <el-tag :type="userStore.isAdmin ? 'danger' : 'info'">
          {{ userStore.isAdmin ? '管理员' : '普通用户' }}
        </el-tag>
      </el-form-item>
      <el-form-item label="主邮箱" required>
        <el-input v-model="profileForm.emails[0]" placeholder="填写主邮箱以接收日报推送" />
      </el-form-item>
      <el-form-item label="备用邮箱 1">
        <el-input v-model="profileForm.emails[1]" placeholder="可选，填写第二个接收邮箱" />
      </el-form-item>
      <el-form-item label="备用邮箱 2">
        <el-input v-model="profileForm.emails[2]" placeholder="可选，填写第三个接收邮箱" />
      </el-form-item>
      <el-form-item label="邮件推送">
        <div style="display: flex; align-items: center; gap: 12px;">
          <el-switch v-model="profileForm.receive_email" active-text="开启" inactive-text="关闭" />
          <el-text type="info" size="small">开启后每日日报发送到以上邮箱</el-text>
        </div>
      </el-form-item>
      <el-form-item label="修改密码">
        <el-input v-model="profileForm.password" type="password" placeholder="留空不修改" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showProfile = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSaveProfile">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)
const showProfile = ref(false)
const saving = ref(false)
const profileForm = reactive({ emails: ['', '', ''], receive_email: true, password: '' })

function parseEmails(emailStr) {
  const parts = (emailStr || '').split(',').map(e => e.trim())
  return [parts[0] || '', parts[1] || '', parts[2] || '']
}

function handleCmd(cmd) {
  if (cmd === 'profile') {
    const emails = parseEmails(userStore.user?.email)
    profileForm.emails = emails
    profileForm.receive_email = userStore.user?.receive_email !== false && userStore.user?.receive_email !== 0
    profileForm.password = ''
    showProfile.value = true
  } else if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}

async function handleSaveProfile() {
  const validEmails = profileForm.emails.filter(e => e.trim())
  if (profileForm.receive_email && validEmails.length === 0) {
    return ElMessage.warning('开启邮件推送需要至少填写一个邮箱')
  }
  saving.value = true
  try {
    const emailStr = validEmails.join(',')
    const data = { email: emailStr, receive_email: profileForm.receive_email }
    if (profileForm.password) data.password = profileForm.password
    await userStore.updateProfile(data)
    ElMessage.success('保存成功')
    showProfile.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}

// 全局暴露给子组件调用
const openProfile = () => handleCmd('profile')
defineExpose({ openProfile })
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
.aside-menu { border-right: none; background: transparent; height: 100%; }
.aside-menu:not(.el-menu--collapse) { width: 220px; }
.aside-menu .el-menu-item { color: rgba(255,255,255,0.7); }
.aside-menu .el-menu-item:hover,
.aside-menu .el-menu-item.is-active { color: #fff; background: rgba(240,136,62,0.15); }

.app-main { background: #f5f7fa; overflow-y: auto; padding: 24px; }
.main-content { max-width: 1100px; margin: 0 auto; }

@media (max-width: 768px) {
  .app-aside { position: fixed; z-index: 20; height: calc(100vh - 56px); top: 56px; }
  .app-main { padding: 16px; }
  .main-content { max-width: 100%; }
  .username { display: none; }
  .header-title { font-size: 15px; }
}
</style>
