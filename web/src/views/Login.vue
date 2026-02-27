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
            <el-form-item>
              <div class="captcha-row">
                <div class="captcha-question">{{ captchaA }} + {{ captchaB }} = ?</div>
                <el-input v-model="loginCaptcha" placeholder="请输入答案" size="large" class="captcha-input" type="number" />
                <el-button size="large" plain @click="refreshCaptcha" class="captcha-refresh" title="换一题">↻</el-button>
              </div>
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
            <el-form-item>
              <div class="captcha-row">
                <div class="captcha-question">{{ captchaA }} + {{ captchaB }} = ?</div>
                <el-input v-model="loginCaptcha" placeholder="请输入答案" size="large" class="captcha-input" type="number" />
                <el-button size="large" plain @click="refreshCaptcha" class="captcha-refresh" title="换一题">↻</el-button>
              </div>
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

// Simple math captcha
const captchaA = ref(0)
const captchaB = ref(0)
const loginCaptcha = ref('')

function refreshCaptcha() {
  captchaA.value = Math.floor(Math.random() * 10)
  captchaB.value = Math.floor(Math.random() * 10)
  loginCaptcha.value = ''
}

function validateCaptcha() {
  return parseInt(loginCaptcha.value, 10) === captchaA.value + captchaB.value
}

refreshCaptcha()

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) return ElMessage.warning('请填写用户名和密码')
  if (!loginCaptcha.value) return ElMessage.warning('请填写验证码')
  if (!validateCaptcha()) {
    ElMessage.error('验证码答案错误')
    refreshCaptcha()
    return
  }
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
    refreshCaptcha()
  } finally { loading.value = false }
}

async function handleRegister() {
  if (regForm.username.length < 2) return ElMessage.warning('用户名至少2位')
  if (regForm.password.length < 6) return ElMessage.warning('密码至少6位')
  if (!loginCaptcha.value) return ElMessage.warning('请填写验证码')
  if (!validateCaptcha()) {
    ElMessage.error('验证码答案错误')
    refreshCaptcha()
    return
  }
  loading.value = true
  try {
    await userStore.doRegister(regForm.username, regForm.password, regForm.email)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
    refreshCaptcha()
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
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  box-sizing: border-box;
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
  box-sizing: border-box;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  opacity: 0.95;
}
.login-header { text-align: center; margin-bottom: 24px; }
.login-header h1 { font-size: 28px; margin-bottom: 6px; }
.login-header p { color: #888; font-size: 14px; }
.login-form { padding-top: 8px; }
.login-form .el-input { width: 100%; }

/* Captcha */
.captcha-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
}
.captcha-question {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 0 12px;
  height: 40px;
  line-height: 40px;
  white-space: nowrap;
  flex-shrink: 0;
}
.captcha-input { flex: 1; min-width: 0; }
.captcha-refresh { flex-shrink: 0; padding: 0 12px; }

@media (max-width: 480px) {
  .login-page { padding: 12px; align-items: flex-start; padding-top: 60px; }
  .login-card { padding: 24px 16px; }
  .login-header h1 { font-size: 22px; }
  .captcha-question { font-size: 14px; padding: 0 8px; }
}
</style>
