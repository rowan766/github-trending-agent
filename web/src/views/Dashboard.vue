<template>
  <div class="dashboard">
    <el-card shadow="never" class="action-card">
      <div class="action-bar">
        <div>
          <h2>📊 仪表盘</h2>
          <el-text type="info">管理和查看每日 GitHub Trending 推送</el-text>
        </div>
        <div class="action-btns">
          <el-button type="primary" size="large" :loading="triggering" :disabled="isRunning" @click="handleTrigger" class="trigger-btn">
            <template v-if="!triggering" #icon><el-icon><Promotion /></el-icon></template>
            {{ isRunning ? '运行中...' : '手动触发' }}
          </el-button>
        </div>
      </div>

      <!-- Progress bar -->
      <div v-if="isRunning" class="progress-section">
        <div class="progress-header">
          <span class="progress-step">
            <el-icon class="is-loading" style="vertical-align:-2px"><Loading /></el-icon>
            {{ progress.message }}
          </span>
          <span class="progress-pct">{{ progress.percentage }}%</span>
        </div>
        <el-progress :percentage="progress.percentage" :stroke-width="12" :show-text="false" color="#f0883e" />
        <div class="progress-steps">
          <span v-for="s in stepList" :key="s.key"
            :class="['step-dot', { active: s.key === progress.step, done: s.pct < progress.percentage }]">
            {{ s.label }}
          </span>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="总报告数" :value="reportStore.list.length">
            <template #prefix><el-icon><Document /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="最近推送项目数" :value="latestCount">
            <template #prefix><el-icon><TrendCharts /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="上次运行" :value="lastRunText">
            <template #prefix><el-icon><Clock /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>📋 推送记录</span>
          <el-button text :icon="Refresh" @click="reportStore.fetchList()">刷新</el-button>
        </div>
      </template>
      <el-table :data="reportStore.list" stripe v-loading="reportStore.loading" @row-click="goDetail" class="desktop-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="report_date" label="日期" width="140" />
        <el-table-column prop="project_count" label="项目数" width="100" align="center">
          <template #default="{ row }"><el-tag size="small">{{ row.project_count }} 个</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="goDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mobile-list">
        <div v-for="item in reportStore.list" :key="item.id" class="mobile-report-card" @click="goDetail(item)">
          <div class="mobile-report-top">
            <span class="mobile-report-date">{{ item.report_date }}</span>
            <el-tag size="small">{{ item.project_count }} 个项目</el-tag>
          </div>
          <el-text type="info" size="small">{{ item.created_at }}</el-text>
        </div>
      </div>
      <el-empty v-if="!reportStore.loading && reportStore.list.length === 0" description="暂无报告，点击上方手动触发" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '../stores/report'
import { useUserStore } from '../stores/user'
import { Refresh, Document, TrendCharts, Clock, Loading, Promotion } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const reportStore = useReportStore()
const userStore = useUserStore()
const triggering = ref(false)
let pollTimer = null

const isRunning = computed(() => reportStore.pipelineStatus.running)
const progress = computed(() => reportStore.pipelineStatus.progress || { percentage: 0, step: 'idle', message: '等待中' })
const todayPushed = computed(() => reportStore.pipelineStatus.today_pushed)

const stepList = [
  { key: 'scraping', label: '抓取', pct: 10 },
  { key: 'dedup', label: '去重', pct: 20 },
  { key: 'enriching', label: '详情', pct: 45 },
  { key: 'analyzing', label: 'AI分析', pct: 70 },
  { key: 'report', label: '报告', pct: 88 },
  { key: 'email', label: '邮件', pct: 95 },
]

const latestCount = computed(() => reportStore.list[0]?.project_count || 0)
const lastRunText = computed(() => {
  const r = reportStore.pipelineStatus.last_result
  return r?.status === 'success' ? `推送 ${r.pushed} 个` : '暂无'
})

function hasEmail() {
  const email = userStore.user?.email || ''
  return email.split(',').some(e => e.trim())
}

async function handleTrigger() {
  // 校验邮箱
  if (!hasEmail()) {
    try {
      await ElMessageBox.confirm(
        '你还未配置接收邮箱，无法接收日报推送。\n是否前往个人中心配置邮箱？',
        '提示',
        { confirmButtonText: '去配置', cancelButtonText: '继续触发', type: 'warning', distinguishCancelAndClose: true }
      )
      window.dispatchEvent(new CustomEvent('open-profile'))
      return
    } catch (action) {
      if (action === 'close') return
    }
  }

  // 校验今日是否已推送
  if (todayPushed.value) {
    try {
      await ElMessageBox.confirm(
        '今日已经推送过了，再次触发会覆盖今日报告并重新调用 AI 接口。\n确定要重新触发吗？',
        '今日已推送',
        { confirmButtonText: '重新触发', cancelButtonText: '取消', type: 'warning' }
      )
    } catch {
      return
    }
  }

  triggering.value = true
  try {
    const result = await reportStore.trigger()
    if (result.status === 'already_running') ElMessage.warning('任务正在运行中')
    else { ElMessage.success('已触发，请稍候...'); startPoll() }
  } catch { ElMessage.error('触发失败') }
  finally { triggering.value = false }
}

function startPoll() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    await reportStore.fetchStatus()
    if (!reportStore.pipelineStatus.running) {
      clearInterval(pollTimer); pollTimer = null
      await reportStore.fetchList()
      ElMessage.success('任务完成!')
    }
  }, 2000)
}

function goDetail(row) { router.push(`/report/${row.id}`) }

onMounted(() => {
  reportStore.fetchList()
  reportStore.fetchStatus()
  userStore.fetchMe()
  if (reportStore.pipelineStatus.running) startPoll()
})
onUnmounted(() => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } })
</script>

<style scoped>
.action-card { margin-bottom: 16px; }
.action-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.action-bar h2 { margin-bottom: 4px; }
.action-btns { flex-shrink: 0; }
.trigger-btn { min-width: 130px; height: 40px; font-size: 15px; }
.progress-section { margin-top: 18px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.progress-step { font-size: 14px; color: #333; font-weight: 500; }
.progress-pct { font-size: 14px; color: #f0883e; font-weight: 600; }
.progress-steps { display: flex; justify-content: space-between; margin-top: 10px; gap: 4px; }
.step-dot { font-size: 12px; color: #ccc; position: relative; padding-top: 10px; text-align: center; flex: 1; }
.step-dot::before { content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 8px; height: 8px; border-radius: 50%; background: #e0e0e0; }
.step-dot.done { color: #999; }
.step-dot.done::before { background: #f0883e; }
.step-dot.active { color: #f0883e; font-weight: 600; }
.step-dot.active::before { background: #f0883e; box-shadow: 0 0 0 3px rgba(240,136,62,0.2); width: 10px; height: 10px; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; margin-bottom: 12px; }
.list-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.el-table { cursor: pointer; }
.mobile-list { display: none; }
.mobile-report-card { padding: 14px 0; border-bottom: 1px solid #eee; cursor: pointer; }
.mobile-report-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.mobile-report-date { font-weight: 600; font-size: 15px; }
@media (max-width: 768px) {
  .mobile-list { display: block; }
  .desktop-table { display: none; }
  .action-bar { flex-direction: column; align-items: flex-start; }
  .action-btns { align-self: flex-end; }
  .trigger-btn { min-width: 110px; height: 36px; font-size: 14px; }
  .progress-steps { flex-wrap: wrap; }
  .step-dot { font-size: 11px; min-width: 40px; }
  .stat-card { margin-bottom: 8px; }
  .stat-card :deep(.el-statistic__number) { font-size: 20px; }
}
</style>
