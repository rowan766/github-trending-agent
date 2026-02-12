<template>
  <div class="feedback-page">
    <el-card shadow="never" class="section-card">
      <template #header><span>💬 联系开发者</span></template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
        欢迎提出你的意见和建议，我们会认真阅读每一条反馈并尽快回复。
      </el-alert>

      <el-form :model="form" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio value="suggestion">💡 功能建议</el-radio>
            <el-radio value="bug">🐛 Bug 反馈</el-radio>
            <el-radio value="other">💬 其他</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请描述你的意见或建议..." maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交反馈</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- My feedback history -->
    <el-card shadow="never" class="section-card">
      <template #header><span>📝 我的反馈记录</span></template>
      <div v-loading="loading">
        <el-empty v-if="!loading && feedbackList.length === 0" description="暂无反馈记录" />
        <div v-for="fb in feedbackList" :key="fb.id" class="fb-item">
          <div class="fb-header">
            <el-tag size="small" :type="typeTag(fb.type)">{{ typeLabel(fb.type) }}</el-tag>
            <el-tag size="small" :type="fb.status === 'replied' ? 'success' : 'info'">
              {{ fb.status === 'replied' ? '已回复' : '待回复' }}
            </el-tag>
            <el-text type="info" size="small">{{ fb.created_at }}</el-text>
          </div>
          <p class="fb-content">{{ fb.content }}</p>
          <div v-if="fb.reply" class="fb-reply">
            <el-icon><ChatDotRound /></el-icon>
            <span>开发者回复：{{ fb.reply }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Donation -->
    <el-card shadow="never" class="section-card donate-card">
      <template #header><span>☕ 打赏支持</span></template>
      <p class="donate-desc">如果这个工具对你有帮助，可以请开发者喝杯咖啡 ☕ 感谢你的支持！</p>
      <div class="donate-qr-row">
        <div class="donate-qr-item">
          <div class="qr-placeholder wechat">
            <el-icon :size="40"><Iphone /></el-icon>
            <span>微信支付</span>
          </div>
          <p>微信扫码支付</p>
          <el-text type="info" size="small">请将 wechat-pay.png 放到 app/static/img/ 目录</el-text>
          <img src="/api/static/img/wechat-pay.png" class="qr-img" @error="onImgError" />
        </div>
        <div class="donate-qr-item">
          <div class="qr-placeholder alipay">
            <el-icon :size="40"><Wallet /></el-icon>
            <span>支付宝</span>
          </div>
          <p>支付宝扫码支付</p>
          <el-text type="info" size="small">请将 alipay-pay.png 放到 app/static/img/ 目录</el-text>
          <img src="/api/static/img/alipay-pay.png" class="qr-img" @error="onImgError" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { submitFeedback, getMyFeedback } from '../api'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Iphone, Wallet } from '@element-plus/icons-vue'

const form = reactive({ type: 'suggestion', content: '' })
const submitting = ref(false)
const loading = ref(false)
const feedbackList = ref([])

function typeLabel(t) { return { suggestion: '💡 功能建议', bug: '🐛 Bug', other: '💬 其他' }[t] || t }
function typeTag(t) { return { suggestion: '', bug: 'danger', other: 'info' }[t] || '' }

function onImgError(e) {
  // 图片加载失败时隐藏图片，显示占位图
  e.target.style.display = 'none'
}

async function handleSubmit() {
  if (!form.content.trim()) return ElMessage.warning('请填写反馈内容')
  submitting.value = true
  try {
    await submitFeedback({ type: form.type, content: form.content })
    ElMessage.success('提交成功，感谢你的反馈！')
    form.content = ''
    await fetchList()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally { submitting.value = false }
}

async function fetchList() {
  loading.value = true
  try { feedbackList.value = (await getMyFeedback()).data }
  finally { loading.value = false }
}

onMounted(fetchList)
</script>

<style scoped>
.section-card { margin-bottom: 16px; }

.fb-item { padding: 14px 0; border-bottom: 1px solid #f0f0f0; }
.fb-item:last-child { border-bottom: none; }
.fb-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.fb-content { font-size: 14px; color: #333; line-height: 1.6; margin: 0; }
.fb-reply {
  margin-top: 10px; padding: 10px 14px;
  background: #f0f9eb; border-radius: 6px; border-left: 3px solid #67c23a;
  font-size: 13px; color: #333; display: flex; align-items: flex-start; gap: 6px;
}

.donate-desc { font-size: 14px; color: #666; margin: 0 0 16px; }
.donate-qr-row { display: flex; gap: 40px; flex-wrap: wrap; justify-content: center; }
.donate-qr-item { text-align: center; }
.donate-qr-item p { font-size: 14px; font-weight: 500; margin: 8px 0 2px; }

.qr-placeholder {
  width: 180px; height: 180px; border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; font-size: 14px; font-weight: 500;
}
.qr-placeholder.wechat { background: #f0faf0; color: #07c160; border: 2px dashed #07c160; }
.qr-placeholder.alipay { background: #f0f4ff; color: #1677ff; border: 2px dashed #1677ff; }

.qr-img {
  width: 180px; height: 180px; border-radius: 12px; object-fit: contain;
  margin-top: -180px; position: relative; z-index: 1; background: #fff;
}

@media (max-width: 768px) {
  .donate-qr-row { gap: 20px; }
  .qr-placeholder, .qr-img { width: 150px; height: 150px; }
  .qr-img { margin-top: -150px; }
}
</style>
