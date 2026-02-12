<template>
  <div class="dashboard">
    <el-card shadow="never" class="action-card">
      <div class="action-bar">
        <div>
          <h2>📊 仪表盘</h2>
          <el-text type="info">管理和查看每日 GitHub Trending 推送</el-text>
        </div>
        <div class="action-btns">
          <el-tag v-if="store.pipelineStatus.running" type="warning" effect="dark">
            <el-icon class="is-loading"><Loading /></el-icon> 正在运行
          </el-tag>
          <el-button type="primary" :icon="Refresh" :loading="triggering" @click="handleTrigger">手动触发</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card">
          <el-statistic title="总报告数" :value="store.list.length">
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
          <el-button text :icon="Refresh" @click="store.fetchList()">刷新</el-button>
        </div>
      </template>
      <el-table :data="store.list" stripe v-loading="store.loading" @row-click="goDetail" class="desktop-table">
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
      <!-- Mobile list -->
      <div class="mobile-list">
        <div v-for="item in store.list" :key="item.id" class="mobile-report-card" @click="goDetail(item)">
          <div class="mobile-report-top">
            <span class="mobile-report-date">{{ item.report_date }}</span>
            <el-tag size="small">{{ item.project_count }} 个项目</el-tag>
          </div>
          <el-text type="info" size="small">{{ item.created_at }}</el-text>
        </div>
      </div>
      <el-empty v-if="!store.loading && store.list.length === 0" description="暂无报告，点击上方手动触发" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReportStore } from '../stores/report'
import { Refresh, Document, TrendCharts, Clock, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useReportStore()
const triggering = ref(false)
let pollTimer = null

const latestCount = computed(() => store.list[0]?.project_count || 0)
const lastRunText = computed(() => {
  const r = store.pipelineStatus.last_result
  return r?.status === 'success' ? `推送 ${r.pushed} 个` : '暂无'
})

async function handleTrigger() {
  triggering.value = true
  try {
    const result = await store.trigger()
    if (result.status === 'already_running') ElMessage.warning('任务正在运行中')
    else { ElMessage.success('已触发'); startPoll() }
  } catch { ElMessage.error('触发失败') }
  finally { triggering.value = false }
}

function startPoll() {
  pollTimer = setInterval(async () => {
    await store.fetchStatus()
    if (!store.pipelineStatus.running) {
      clearInterval(pollTimer); pollTimer = null
      await store.fetchList()
      ElMessage.success('任务完成!')
    }
  }, 3000)
}

function goDetail(row) { router.push(`/report/${row.id}`) }

onMounted(() => { store.fetchList(); store.fetchStatus() })
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.action-card { margin-bottom: 16px; }
.action-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.action-bar h2 { margin-bottom: 4px; }
.action-btns { display: flex; align-items: center; gap: 12px; }
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
}
</style>
