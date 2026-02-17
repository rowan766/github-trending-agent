<template>
  <div class="admin-feedback">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>💬 用户反馈管理</span>
          <div style="display:flex;gap:8px">
            <el-select v-model="filterStatus" size="small" style="width:120px">
              <el-option label="全部" value="" />
              <el-option label="待回复" value="pending" />
              <el-option label="已回复" value="replied" />
            </el-select>
            <el-button text :icon="Refresh" @click="fetchList">刷新</el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <el-empty v-if="!loading && filtered.length === 0" description="暂无反馈" />

        <div v-for="fb in filtered" :key="fb.id" class="fb-item">
          <div class="fb-header">
            <el-avatar :size="28" style="background:#f0883e;font-size:12px">{{ fb.username?.[0]?.toUpperCase() }}</el-avatar>
            <strong>{{ fb.username }}</strong>
            <el-tag size="small" :type="typeTag(fb.type)">{{ typeLabel(fb.type) }}</el-tag>
            <el-tag size="small" :type="fb.status === 'replied' ? 'success' : 'warning'">
              {{ fb.status === 'replied' ? '已回复' : '待回复' }}
            </el-tag>
            <el-text type="info" size="small">{{ formatTime(fb.created_at) }}</el-text>
          </div>
          <p class="fb-content">{{ fb.content }}</p>

          <!-- Reply area -->
          <div v-if="fb.reply" class="fb-reply">
            <strong>管理员回复：</strong>{{ fb.reply }}
          </div>
          <div class="fb-actions">
            <el-button size="small" type="primary" @click="openReply(fb)">
              {{ fb.reply ? '修改回复' : '回复' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Reply dialog -->
    <el-dialog v-model="showReply" title="回复反馈" width="500px" class="reply-dialog">
      <div v-if="currentFb" style="margin-bottom:12px">
        <el-tag size="small">{{ currentFb.username }}</el-tag>
        <el-text type="info" size="small" style="margin-left:8px">{{ formatTime(currentFb.created_at) }}</el-text>
        <p style="margin:8px 0;color:#333">{{ currentFb.content }}</p>
      </div>
      <el-input v-model="replyText" type="textarea" :rows="3" placeholder="输入回复内容..." />
      <template #footer>
        <el-button @click="showReply = false">取消</el-button>
        <el-button type="primary" :loading="replying" @click="handleReply">发送回复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAdminFeedback, replyFeedback } from '../api'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { formatTime } from '../utils/format'

const loading = ref(false)
const feedbackList = ref([])
const filterStatus = ref('')
const showReply = ref(false)
const currentFb = ref(null)
const replyText = ref('')
const replying = ref(false)

const filtered = computed(() => {
  if (!filterStatus.value) return feedbackList.value
  return feedbackList.value.filter(fb => fb.status === filterStatus.value)
})

function typeLabel(t) { return { suggestion: '💡 建议', bug: '🐛 Bug', other: '💬 其他' }[t] || t }
function typeTag(t) { return { suggestion: '', bug: 'danger', other: 'info' }[t] || '' }

function openReply(fb) {
  currentFb.value = fb
  replyText.value = fb.reply || ''
  showReply.value = true
}

async function handleReply() {
  if (!replyText.value.trim()) return ElMessage.warning('请输入回复内容')
  replying.value = true
  try {
    await replyFeedback(currentFb.value.id, replyText.value)
    ElMessage.success('回复成功')
    showReply.value = false
    await fetchList()
  } catch { ElMessage.error('回复失败') }
  finally { replying.value = false }
}

async function fetchList() {
  loading.value = true
  try { feedbackList.value = (await getAdminFeedback()).data }
  finally { loading.value = false }
}

onMounted(fetchList)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.fb-item { padding: 16px 0; border-bottom: 1px solid #f0f0f0; }
.fb-item:last-child { border-bottom: none; }
.fb-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.fb-content { font-size: 14px; color: #333; line-height: 1.6; margin: 0; }
.fb-reply {
  margin-top: 10px; padding: 10px 14px;
  background: #f0f9eb; border-radius: 6px; border-left: 3px solid #67c23a;
  font-size: 13px; color: #333;
}
.fb-actions { margin-top: 10px; }

@media (max-width: 768px) {
  .fb-header { gap: 6px; }
  .fb-header .el-avatar { display: none; }
  .card-header { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>
<style>
.reply-dialog { --el-dialog-width: 92vw !important; max-width: 500px; }
</style>
