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
      <div v-if="showProgress" class="progress-section">
        <div class="progress-header">
          <span class="progress-step">
            <el-icon :class="{ 'is-loading': isRunning }" style="vertical-align:-2px">
              <Loading v-if="isRunning" /><SuccessFilled v-else />
            </el-icon>
            {{ progress.message }}
          </span>
          <span class="progress-pct">{{ progress.percentage }}%</span>
        </div>
        <el-progress :percentage="progress.percentage" :stroke-width="12" :show-text="false" :color="isRunning ? '#f0883e' : '#67c23a'" />
        <div class="progress-steps">
          <span v-for="s in stepList" :key="s.key"
            :class="['step-dot', { active: s.key === progress.step, done: s.pct < progress.percentage }]">
            {{ s.label }}
          </span>
        </div>
      </div>
    </el-card>

    <div class="stats-row">
      <div class="stat-card stat-reports">
        <div class="stat-icon-wrap"><el-icon :size="26"><Document /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ reportStore.list.length }}</span>
          <span class="stat-label">总报告数</span>
        </div>
      </div>
      <div class="stat-card stat-projects">
        <div class="stat-icon-wrap"><el-icon :size="26"><TrendCharts /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ latestCount }}</span>
          <span class="stat-label">最近推送项目数</span>
        </div>
      </div>
      <div class="stat-card stat-lastrun">
        <div class="stat-icon-wrap"><el-icon :size="26"><Clock /></el-icon></div>
        <div class="stat-info">
          <span class="stat-value">{{ lastRunText }}</span>
          <span class="stat-label">上次运行</span>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>📋 推送记录</span>
          <el-button text :icon="Refresh" @click="reportStore.fetchList()">刷新</el-button>
        </div>
      </template>
      <el-table :data="pagedList" stripe v-loading="reportStore.loading" @row-click="goDetail" class="desktop-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="report_date" label="日期" width="130" />
        <el-table-column prop="project_count" label="项目数" width="90" align="center">
          <template #default="{ row }"><el-tag size="small">{{ row.project_count }} 个</el-tag></template>
        </el-table-column>
        <el-table-column label="当日推送" width="110" align="center">
          <template #default="{ row }">
            <el-tooltip :content="emailTooltip(row)" placement="top" :show-after="300">
              <el-tag :type="emailTagType(row)" size="small" effect="light">
                {{ emailTagText(row) }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="goDetail(row)">详情</el-button>
            <el-popconfirm title="确定删除该报告？仅从你的列表中移除" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="mobile-list">
        <div v-for="item in pagedList" :key="item.id" class="mobile-report-card" @click="goDetail(item)">
          <div class="mobile-report-top">
            <span class="mobile-report-date">{{ item.report_date }}</span>
            <div style="display:flex;gap:6px;align-items:center">
              <el-tag :type="emailTagType(item)" size="small">
                {{ emailTagText(item) }}
              </el-tag>
              <el-tag size="small">{{ item.project_count }} 个</el-tag>
            </div>
          </div>
          <div class="mobile-report-bottom">
            <el-text type="info" size="small">{{ formatTime(item.created_at) }}</el-text>
            <el-button type="danger" link size="small" @click.stop="confirmMobileDelete(item)">删除</el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="!reportStore.loading && reportStore.list.length === 0" description="暂无报告，点击上方手动触发" />
      <div v-if="reportStore.list.length > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="reportStore.list.length"
          layout="prev, pager, next"
          small
          background
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '../stores/report'
import { useUserStore } from '../stores/user'
import { Refresh, Document, TrendCharts, Clock, Loading, Promotion, SuccessFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatTime } from '../utils/format'

const router = useRouter()
const reportStore = useReportStore()
const userStore = useUserStore()
const triggering = ref(false)
const currentPage = ref(1)
const pageSize = 10
const showProgress = ref(false)
let pollTimer = null
let hideProgressTimer = null

const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return reportStore.list.slice(start, start + pageSize)
})

async function handleDelete(id) {
  try {
    await reportStore.removeReport(id)
    ElMessage.success('已从你的列表中移除')
  } catch { ElMessage.error('删除失败') }
}

async function confirmMobileDelete(item) {
  try {
    await ElMessageBox.confirm(`确定移除报告「${item.report_date}」？`, '确认', { type: 'warning' })
    await handleDelete(item.id)
  } catch { /* cancelled */ }
}

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
    else if (result.status === 'limit_reached') ElMessage.warning(result.message || '今日触发次数已达上限')
    else { ElMessage.success('已触发，请稍候...'); startPoll() }
  } catch { ElMessage.error('触发失败') }
  finally { triggering.value = false }
}

function startPoll() {
  if (pollTimer) return
  showProgress.value = true
  if (hideProgressTimer) { clearTimeout(hideProgressTimer); hideProgressTimer = null }
  pollTimer = setInterval(async () => {
    await reportStore.fetchStatus()
    if (!reportStore.pipelineStatus.running) {
      clearInterval(pollTimer); pollTimer = null
      await reportStore.fetchList()
      ElMessage.success('任务完成!')
      // 完成后保留进度条 5 秒再隐藏
      hideProgressTimer = setTimeout(() => { showProgress.value = false }, 5000)
    }
  }, 2000)
}

function goDetail(row) { router.push(`/report/${row.id}`) }

// 当日推送状态：区分"注册前"/"已推送"/"未推送"
// email_sent 是系统级全局标志（当天是否向订阅用户发了邮件），与具体用户无关
// 若报告日期早于当前用户注册日期，显示"—"
function userRegDate() {
  const ca = userStore.user?.created_at
  return ca ? ca.slice(0, 10) : null
}
function emailTagType(row) {
  const reg = userRegDate()
  if (reg && row.report_date < reg) return 'info'
  return row.email_sent ? 'success' : 'warning'
}
function emailTagText(row) {
  const reg = userRegDate()
  if (reg && row.report_date < reg) return '— 注册前'
  return row.email_sent ? '✅ 已推送' : '⏳ 未推送'
}
function emailTooltip(row) {
  const reg = userRegDate()
  if (reg && row.report_date < reg) return '该报告生成于你注册之前，未向你推送'
  return row.email_sent ? '当日已向所有订阅用户发送邮件' : '当日未发送邮件推送'
}

onMounted(async () => {
  reportStore.fetchList()
  await reportStore.fetchStatus()
  userStore.fetchMe()
  if (reportStore.pipelineStatus.running) startPoll()
})
onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (hideProgressTimer) { clearTimeout(hideProgressTimer); hideProgressTimer = null }
})
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
.stats-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px;
}
.stat-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px; border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.stat-icon-wrap {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-info { display: flex; flex-direction: column; min-width: 0; }
.stat-value { font-size: 24px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }

/* --- color themes --- */
.stat-reports { background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); }
.stat-reports .stat-icon-wrap { background: #818cf8; color: #fff; }
.stat-reports .stat-value { color: #4338ca; }

.stat-projects { background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%); }
.stat-projects .stat-icon-wrap { background: #f97316; color: #fff; }
.stat-projects .stat-value { color: #c2410c; }

.stat-lastrun { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); }
.stat-lastrun .stat-icon-wrap { background: #34d399; color: #fff; }
.stat-lastrun .stat-value { color: #047857; }
.list-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.el-table { cursor: pointer; }
.mobile-list { display: none; }
.mobile-report-card { padding: 14px 0; border-bottom: 1px solid #eee; cursor: pointer; }
.mobile-report-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.mobile-report-bottom { display: flex; justify-content: space-between; align-items: center; }
.mobile-report-date { font-weight: 600; font-size: 15px; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 16px; }
@media (max-width: 768px) {
  .mobile-list { display: block; }
  .desktop-table { display: none; }
  .action-bar { flex-direction: column; align-items: flex-start; }
  .action-btns { align-self: flex-end; }
  .trigger-btn { min-width: 110px; height: 36px; font-size: 14px; }
  .progress-steps { flex-wrap: wrap; }
  .step-dot { font-size: 11px; min-width: 40px; }
  .stats-row { grid-template-columns: 1fr; gap: 10px; }
  .stat-card { padding: 14px; gap: 12px; }
  .stat-icon-wrap { width: 42px; height: 42px; border-radius: 10px; }
  .stat-icon-wrap .el-icon { font-size: 20px !important; }
  .stat-value { font-size: 20px; }
  .stat-label { font-size: 12px; }
}
</style>
