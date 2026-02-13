<template>
  <div class="report-detail">
    <el-page-header @back="router.push('/')" style="margin-bottom: 16px">
      <template #content>
        <span>📄 报告详情 — {{ report?.report_date || '' }}</span>
      </template>
    </el-page-header>

    <div v-loading="store.loading">
      <template v-if="report">
        <el-row :gutter="16" class="stats-row">
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="总项目" :value="report.project_count" />
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="今日最热" :value="dailyProjects.length" />
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="本周飙升" :value="weeklyProjects.length" />
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="本月飙升" :value="monthlyProjects.length" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Tabs -->
        <el-card shadow="never">
          <el-tabs v-model="activeTab" class="report-tabs">
            <el-tab-pane name="hot">
              <template #label>
                <span>🔥 最热 <el-tag size="small" round>{{ allByStars.length }}</el-tag></span>
              </template>
              <project-list :projects="allByStars" :show-stars-today="false" />
            </el-tab-pane>
            <el-tab-pane name="daily">
              <template #label>
                <span>⚡ 今日最热 <el-tag size="small" round>{{ dailyProjects.length }}</el-tag></span>
              </template>
              <project-list :projects="dailyProjects" period-label="今日" />
            </el-tab-pane>
            <el-tab-pane name="weekly">
              <template #label>
                <span>📈 本周飙升 <el-tag size="small" round>{{ weeklyProjects.length }}</el-tag></span>
              </template>
              <project-list :projects="weeklyProjects" period-label="本周" />
            </el-tab-pane>
            <el-tab-pane name="monthly">
              <template #label>
                <span>📅 本月飙升 <el-tag size="small" round>{{ monthlyProjects.length }}</el-tag></span>
              </template>
              <project-list :projects="monthlyProjects" period-label="本月" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReportStore } from '../stores/report'
import ProjectList from '../components/ProjectList.vue'

const route = useRoute()
const router = useRouter()
const store = useReportStore()
const activeTab = ref('hot')

const report = computed(() => store.currentReport)

// 兼容新格式(dict) 和 旧格式(array)
const projectsData = computed(() => {
  const p = report.value?.projects
  if (!p) return { daily: [], weekly: [], monthly: [] }
  if (Array.isArray(p)) return { daily: p, weekly: [], monthly: [] }
  return { daily: p.daily || [], weekly: p.weekly || [], monthly: p.monthly || [] }
})

const dailyProjects = computed(() => projectsData.value.daily)
const weeklyProjects = computed(() => projectsData.value.weekly)
const monthlyProjects = computed(() => projectsData.value.monthly)

// “最热” = 所有项目按总星数排序
const allByStars = computed(() => {
  const all = [...dailyProjects.value, ...weeklyProjects.value, ...monthlyProjects.value]
  const unique = Object.values(Object.fromEntries(all.map(p => [p.name, p])))
  return unique.sort((a, b) => b.stars - a.stars)
})

onMounted(() => store.fetchDetail(route.params.id))
</script>

<style scoped>
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; margin-bottom: 12px; }
.report-tabs :deep(.el-tabs__item) { font-size: 15px; }
@media (max-width: 768px) {
  .report-tabs :deep(.el-tabs__nav) { flex-wrap: nowrap; }
  .report-tabs :deep(.el-tabs__item) { font-size: 12px; padding: 0 8px; }
  .report-tabs :deep(.el-tabs__item .el-tag) { display: none; }
  .stats-row .el-col { margin-bottom: 0; }
  .stat-card { margin-bottom: 8px; }
  .stat-card :deep(.el-statistic__number) { font-size: 20px; }
}
</style>
