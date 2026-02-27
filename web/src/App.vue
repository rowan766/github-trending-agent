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
        <a href="https://github.com/rowan766/github-trending-agent" target="_blank" class="github-link" title="查看项目源码 GitHub">
          <svg height="20" width="20" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        </a>
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
      <div v-if="!collapsed && isMobile" class="sidebar-backdrop" @click="collapsed = true"></div>
      <el-aside :width="collapsed ? '64px' : '220px'" class="app-aside" :class="{ 'aside-open': !collapsed }">
        <el-menu :default-active="route.path" router :collapse="collapsed" class="aside-menu" @select="onMenuSelect">
          <el-menu-item index="/">
            <el-icon><DataBoard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>技术栈配置</template>
          </el-menu-item>
          <el-menu-item index="/feedback">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>联系开发者</template>
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/users">
            <el-icon><UserFilled /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <el-menu-item v-if="userStore.isAdmin" index="/admin/feedback">
            <el-icon><Comment /></el-icon>
            <template #title>意见管理</template>
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
  <el-dialog v-model="showProfile" title="个人中心" width="500px" class="profile-dialog" destroy-on-close>
    <el-form :model="profileForm" label-width="90px">
      <el-form-item label="用户名">
        <el-input :value="userStore.user?.username" disabled />
      </el-form-item>
      <el-form-item label="角色">
        <el-tag :type="userStore.isAdmin ? 'danger' : 'info'">
          {{ userStore.isAdmin ? '管理员' : '普通用户' }}
        </el-tag>
      </el-form-item>

      <!-- Email fields with verification -->
      <template v-for="(_, idx) in profileForm.emails" :key="idx">
        <el-form-item :label="idx === 0 ? '主邮箱' : `备用邮箱 ${idx}`" :required="idx === 0">
          <div class="email-field-wrap">
            <el-input
              v-model="profileForm.emails[idx]"
              :placeholder="idx === 0 ? '填写主邮箱以接收日报推送' : '可选'"
              clearable
              @input="onEmailInput(idx)"
            />
            <template v-if="profileForm.emails[idx]">
              <el-tag v-if="verifiedEmails[idx]" type="success" effect="dark" size="small" class="verified-tag">✅ 已验证</el-tag>
              <el-button
                v-else
                size="small"
                :loading="sendingIdx === idx"
                @click="handleSendCode(idx)"
                class="send-code-btn"
              >发送验证码</el-button>
            </template>
          </div>
          <!-- Code input row (shown after code sent) -->
          <div v-if="codeInputVisible[idx] && !verifiedEmails[idx]" class="code-input-row">
            <el-input
              v-model="emailCodes[idx]"
              placeholder="请输入6位验证码"
              maxlength="6"
              style="flex:1"
              size="small"
            />
            <el-button type="primary" size="small" :loading="verifyingIdx === idx" @click="handleVerifyCode(idx)">验证</el-button>
            <el-text type="info" size="small" class="code-tip">{{ codeCountdown[idx] > 0 ? `${codeCountdown[idx]}s 后可重发` : '' }}</el-text>
          </div>
        </el-form-item>
      </template>

      <el-form-item label="邮件推送">
        <div style="display:flex;align-items:center;gap:12px">
          <el-switch v-model="profileForm.receive_email" active-text="开启" inactive-text="关闭" />
          <el-text type="info" size="small">开启后每日日报发送到以上邮箱</el-text>
        </div>
      </el-form-item>
      <el-form-item label="修改密码">
        <el-input v-model="profileForm.password" type="password" placeholder="留空不修改" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeProfileDialog">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSaveProfile">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { ElMessageBox, ElMessage } from 'element-plus'
import { ChatDotRound, Comment } from '@element-plus/icons-vue'
import { sendEmailCode, verifyEmailCode } from './api/index.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(window.innerWidth <= 768)
const isMobile = ref(window.innerWidth <= 768)
const showProfile = ref(false)
const saving = ref(false)
const profileForm = reactive({ emails: ['', '', ''], receive_email: true, password: '' })

// Email verification state
const verifiedEmails = reactive([false, false, false])   // verified flag per email slot
const verifiedAddrs = reactive(['', '', ''])              // which address was verified per slot
const codeInputVisible = reactive([false, false, false])  // show code input row
const emailCodes = reactive(['', '', ''])                 // entered codes
const sendingIdx = ref(-1)                                // which slot is sending
const verifyingIdx = ref(-1)                              // which slot is verifying
const codeCountdown = reactive([0, 0, 0])                 // countdown timer per slot
let countdownTimers = [null, null, null]

function startCountdown(idx) {
  codeCountdown[idx] = 60
  if (countdownTimers[idx]) clearInterval(countdownTimers[idx])
  countdownTimers[idx] = setInterval(() => {
    codeCountdown[idx]--
    if (codeCountdown[idx] <= 0) {
      clearInterval(countdownTimers[idx])
      countdownTimers[idx] = null
    }
  }, 1000)
}

function resetEmailVerification(idx) {
  verifiedEmails[idx] = false
  verifiedAddrs[idx] = ''
  codeInputVisible[idx] = false
  emailCodes[idx] = ''
  codeCountdown[idx] = 0
  if (countdownTimers[idx]) { clearInterval(countdownTimers[idx]); countdownTimers[idx] = null }
}

function onEmailInput(idx) {
  // If user changes the email, reset verification status
  if (profileForm.emails[idx] !== verifiedAddrs[idx]) {
    resetEmailVerification(idx)
  }
}

async function handleSendCode(idx) {
  const email = profileForm.emails[idx]?.trim()
  if (!email) return ElMessage.warning('请先输入邮箱地址')
  if (codeCountdown[idx] > 0) return ElMessage.warning(`请等待 ${codeCountdown[idx]}s 后再重新发送`)
  sendingIdx.value = idx
  try {
    await sendEmailCode(email)
    ElMessage.success('验证码已发送，请查收邮件（有效期10分钟）')
    codeInputVisible[idx] = true
    startCountdown(idx)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '发送失败，请检查邮箱地址')
  } finally { sendingIdx.value = -1 }
}

async function handleVerifyCode(idx) {
  const email = profileForm.emails[idx]?.trim()
  const code = emailCodes[idx]?.trim()
  if (!code) return ElMessage.warning('请输入验证码')
  verifyingIdx.value = idx
  try {
    await verifyEmailCode(email, code)
    verifiedEmails[idx] = true
    verifiedAddrs[idx] = email
    codeInputVisible[idx] = false
    ElMessage.success('邮箱验证成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '验证码错误或已过期')
  } finally { verifyingIdx.value = -1 }
}

function parseEmails(emailStr) {
  const parts = (emailStr || '').split(',').map(e => e.trim())
  return [parts[0] || '', parts[1] || '', parts[2] || '']
}

function openProfileDialog() {
  const emails = parseEmails(userStore.user?.email)
  profileForm.emails = [...emails]
  profileForm.receive_email = userStore.user?.receive_email !== false && userStore.user?.receive_email !== 0
  profileForm.password = ''
  // Reset all verification state
  for (let i = 0; i < 3; i++) resetEmailVerification(i)
  showProfile.value = true
}

function handleCmd(cmd) {
  if (cmd === 'profile') openProfileDialog()
  else if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}

function onMenuSelect() {
  if (isMobile.value) collapsed.value = true
}

function onOpenProfile() { openProfileDialog() }

function onResize() { isMobile.value = window.innerWidth <= 768 }

function closeProfileDialog() {
  showProfile.value = false
  countdownTimers.forEach((t, i) => { if (t) { clearInterval(t); countdownTimers[i] = null } })
}

onMounted(() => {
  window.addEventListener('open-profile', onOpenProfile)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('open-profile', onOpenProfile)
  window.removeEventListener('resize', onResize)
  countdownTimers.forEach(t => { if (t) clearInterval(t) })
})

async function handleSaveProfile() {
  const savedEmails = parseEmails(userStore.user?.email)
  const validEmails = profileForm.emails.map(e => e.trim())

  // Check that every non-empty email that changed from saved value has been verified
  for (let i = 0; i < 3; i++) {
    const addr = validEmails[i]
    if (!addr) continue
    const isNew = addr !== savedEmails[i]
    if (isNew && !verifiedEmails[i]) {
      return ElMessage.warning(`"${addr}" 是新邮箱，请先发送验证码并完成验证`)
    }
  }

  const filtered = validEmails.filter(e => e)
  if (profileForm.receive_email && filtered.length === 0) {
    return ElMessage.warning('开启邮件推送需要至少填写一个邮箱')
  }
  saving.value = true
  try {
    const emailStr = filtered.join(',')
    const data = { email: emailStr, receive_email: profileForm.receive_email }
    if (profileForm.password) data.password = profileForm.password
    await userStore.updateProfile(data)
    ElMessage.success('保存成功')
    showProfile.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally { saving.value = false }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }
.app-layout { height: 100vh; flex-direction: column; }
.app-header {
  background: #fff; border-bottom: 1px solid #e8e8e8;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 56px; z-index: 10;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-menu-btn { cursor: pointer; }
.header-title { font-size: 17px; font-weight: 600; color: #333; }
.header-right { display: flex; align-items: center; gap: 12px; }
.github-link {
  display: flex; align-items: center; color: #555;
  transition: color 0.2s; text-decoration: none;
}
.github-link:hover { color: #f0883e; }
.user-dropdown { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; color: #333; }
.app-aside {
  background: #1d1e2c; overflow-y: auto; overflow-x: hidden; transition: width 0.3s;
}
.aside-menu { border-right: none; background: transparent; height: 100%; }
.aside-menu:not(.el-menu--collapse) { width: 220px; }
.aside-menu .el-menu-item { color: rgba(255,255,255,0.7); }
.aside-menu .el-menu-item:hover,
.aside-menu .el-menu-item.is-active { color: #fff; background: rgba(240,136,62,0.15); }
.app-main { background: #f5f7fa; overflow-y: auto; padding: 24px; }
.main-content { max-width: 1100px; margin: 0 auto; height: 100%; }
.sidebar-backdrop {
  display: none;
}
.email-field-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.email-field-wrap .el-input { flex: 1; min-width: 0; }
.verified-tag { flex-shrink: 0; }
.send-code-btn { flex-shrink: 0; white-space: nowrap; }
.code-input-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  width: 100%;
}
.code-tip { flex-shrink: 0; font-size: 12px; }

@media (max-width: 768px) {
  .sidebar-backdrop {
    display: block; position: fixed; top: 56px; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.3); z-index: 19;
  }
  .app-aside {
    position: fixed; z-index: 20; height: calc(100vh - 56px); top: 56px;
    transform: translateX(-100%); transition: transform 0.3s, width 0.3s;
  }
  .app-aside.aside-open { transform: translateX(0); }
  .app-main { padding: 12px; }
  .main-content { max-width: 100%; }
  .username { display: none; }
  .header-title { font-size: 15px; }
  .header-right .el-tag { display: none; }
  .app-header { padding: 0 12px; }
  .profile-dialog { --el-dialog-width: 92vw !important; }
  .profile-dialog .el-form-item__label { width: 80px !important; }
  .send-code-btn { font-size: 12px; padding: 4px 8px; }
}
</style>
