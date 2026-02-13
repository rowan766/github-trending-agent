<template>
  <div class="report-detail">
    <el-page-header @back="router.push('/')" style="margin-bottom: 16px">
      <template #content>
        <span>📄 报告详情 — {{ report?.report_date || '' }}</span>
      </template>
    </el-page-header>

    <!-- Tabs -->
    <el-card v-if="report" v-loading="store.loading" shadow="never" class="tabs-card">
      <el-tabs v-model="activeTab" class="report-tabs">
        <el-tab-pane name="hot">
          <template #label>
            <span>🔥 最热 <el-tag size="small" round>{{ allByStars.length }}</el-tag></span>
          </template>
          <div class="tab-scroll-area">
            <project-list :projects="allByStars" :show-stars-today="false" />
          </div>
        </el-tab-pane>
        <el-tab-pane name="daily">
          <template #label>
            <span>⚡ 今日最热 <el-tag size="small" round>{{ dailyProjects.length }}</el-tag></span>
          </template>
          <div class="tab-scroll-area">
            <project-list :projects="dailyProjects" period-label="今日" />
          </div>
        </el-tab-pane>
        <el-tab-pane name="weekly">
          <template #label>
            <span>📈 本周飙升 <el-tag size="small" round>{{ weeklyProjects.length }}</el-tag></span>
          </template>
          <div class="tab-scroll-area">
            <project-list :projects="weeklyProjects" period-label="本周" />
          </div>
        </el-tab-pane>
        <el-tab-pane name="monthly">
          <template #label>
            <span>📅 本月飙升 <el-tag size="small" round>{{ monthlyProjects.length }}</el-tag></span>
          </template>
          <div class="tab-scroll-area">
            <project-list :projects="monthlyProjects" period-label="本月" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <div v-else v-loading="store.loading" style="height: 200px"></div>
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
.report-detail {
  height: calc(100vh - 56px - 48px); /* 56 header + 24*2 main padding */
  display: flex; flex-direction: column; overflow: hidden;
}
.tabs-card { flex: 1; min-height: 0; overflow: hidden; }
.tabs-card :deep(.el-card__body) { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.report-tabs { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.report-tabs :deep(.el-tabs__header) { flex-shrink: 0; }
.report-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow: hidden; }
.report-tabs :deep(.el-tab-pane) { height: 100%; }
.tab-scroll-area { height: 100%; overflow-y: auto; padding-right: 4px; }
.report-tabs :deep(.el-tabs__item) { font-size: 15px; }

@media (max-width: 768px) {
  .report-detail { height: auto; overflow: visible; }
  .tabs-card, .tabs-card :deep(.el-card__body) { overflow: visible; height: auto; }
  .report-tabs, .report-tabs :deep(.el-tabs__content) { overflow: visible; }
  .tab-scroll-area { height: auto; overflow-y: visible; }
  .report-tabs :deep(.el-tabs__nav) { flex-wrap: nowrap; }
  .report-tabs :deep(.el-tabs__item) { font-size: 12px; padding: 0 8px; }
  .report-tabs :deep(.el-tabs__item .el-tag) { display: none; }
}
</style>
