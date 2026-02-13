<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>🔥 Trending Agent</h1>
        <p>每日 GitHub 热门项目推送</p>
      </div>

      <el-tabs v-model="tab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="handleLogin" class="login-form">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="loginForm.password" type="password" placeholder="密码" :prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width:100%">登 录</el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form @submit.prevent="handleRegister" class="login-form">
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="用户名（至少2位）" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.email" placeholder="邮箱（可选，用于接收日报推送）" :prefix-icon="Message" size="large" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="regForm.password" type="password" placeholder="密码（至少6位）" :prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="success" size="large" :loading="loading" @click="handleRegister" style="width:100%">注 册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const tab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', email: '' })

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) return ElMessage.warning('请填写用户名和密码')
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally { loading.value = false }
}

async function handleRegister() {
  if (regForm.username.length < 2) return ElMessage.warning('用户名至少2位')
  if (regForm.password.length < 6) return ElMessage.warning('密码至少6位')
  loading.value = true
  try {
    await userStore.doRegister(regForm.username, regForm.password, regForm.email)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally { loading.value = false }
}
</script>

<style scoped>
html, body, #app {
  height: 100%;
  margin: 0;
}
.login-page {
  min-height: 100vh;
  width: 100vw;              /* 关键：铺满宽度 */
  display: flex;
  align-items: center;
  justify-content: center;

  background: url('../../static/images/login-bg.png') center / cover no-repeat;
  overflow: hidden;  
}
.login-card {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-radius: 12px;
  padding: 40px 36px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  opacity: 0.95;
}
.login-header { text-align: center; margin-bottom: 24px; }
.login-header h1 { font-size: 28px; margin-bottom: 6px; }
.login-header p { color: #888; font-size: 14px; }
.login-form { padding-top: 8px; }
.login-hint { text-align: center; color: #bbb; font-size: 12px; margin-top: 16px; }

@media (max-width: 480px) {
  .login-card { padding: 30px 20px; }
}
</style>
