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
          <el-col :span="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="推送项目" :value="report.project_count" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="高相关项目" :value="highlights.length" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="报告日期" :value="report.report_date" />
            </el-card>
          </el-col>
        </el-row>

        <el-card v-if="highlights.length" shadow="never" class="section-card">
          <template #header><span>🎯 与你技术栈相关</span></template>
          <div v-for="p in highlights" :key="p.name" class="project-card highlight">
            <div class="project-header">
              <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
              <div class="project-tags">
                <el-tag size="small" type="primary">{{ p.category }}</el-tag>
                <el-tag size="small" type="warning">⭐ {{ formatNum(p.stars) }} (+{{ p.stars_today }})</el-tag>
                <el-tag size="small" type="success">相关度 {{ p.relevance_score }}/10</el-tag>
                <el-tag v-if="p.language" size="small">{{ p.language }}</el-tag>
              </div>
            </div>
            <p class="project-summary">{{ p.summary_zh }}</p>
            <p class="project-reason">💡 {{ p.relevance_reason }}</p>
            <div v-if="p.topics?.length" class="project-topics">
              <el-tag v-for="t in p.topics.slice(0, 8)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="section-card">
          <template #header><span>📈 今日热门</span></template>
          <el-table :data="others" stripe>
            <el-table-column label="项目" min-width="180">
              <template #default="{ row }">
                <a :href="row.url" target="_blank" class="project-link">{{ row.name }}</a>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" align="center">
              <template #default="{ row }"><el-tag size="small">{{ row.category }}</el-tag></template>
            </el-table-column>
            <el-table-column label="⭐ 今日" width="100" align="center">
              <template #default="{ row }">
                <span style="color: #e3b341; font-weight: 600;">+{{ row.stars_today }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="relevance_score" label="相关度" width="90" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.relevance_score * 10" :stroke-width="8" :show-text="false"
                  :color="row.relevance_score >= 7 ? '#f0883e' : '#909399'" style="width: 60px; display: inline-block" />
                <span style="margin-left: 4px; font-size: 12px;">{{ row.relevance_score }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary_zh" label="摘要" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReportStore } from '../stores/report'

const route = useRoute()
const router = useRouter()
const store = useReportStore()

const report = computed(() => store.currentReport)
const projects = computed(() => report.value?.projects || [])
const highlights = computed(() => projects.value.filter(p => p.relevance_score >= 7))
const others = computed(() => projects.value.filter(p => p.relevance_score < 7))

function formatNum(n) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n
}

onMounted(() => store.fetchDetail(route.params.id))
</script>

<style scoped>
.report-detail { max-width: 960px; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.section-card { margin-bottom: 16px; }
.project-card { padding: 16px; border-radius: 8px; margin-bottom: 12px; }
.project-card.highlight { background: #fff8f0; border-left: 4px solid #f0883e; }
.project-header { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.project-name { font-size: 16px; font-weight: 600; color: #0969da; text-decoration: none; }
.project-name:hover { text-decoration: underline; }
.project-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.project-summary { margin: 8px 0 4px; font-size: 14px; color: #333; }
.project-reason { font-size: 13px; color: #888; margin: 0; }
.project-topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.project-link { color: #0969da; text-decoration: none; font-weight: 500; }
.project-link:hover { text-decoration: underline; }
</style>
