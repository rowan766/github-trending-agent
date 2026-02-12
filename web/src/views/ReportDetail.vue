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
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="推送项目" :value="report.project_count" />
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="高相关项目" :value="highlights.length" />
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="stat-card">
              <el-statistic title="报告日期" :value="report.report_date" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Highlights -->
        <el-card v-if="highlights.length" shadow="never" class="section-card">
          <template #header><span>🎯 与你技术栈相关</span></template>
          <div v-for="p in highlights" :key="p.name" class="project-card highlight">
            <div class="project-header">
              <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
              <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制链接" />
            </div>
            <div class="project-tags">
              <el-tag size="small" type="primary">{{ p.category }}</el-tag>
              <el-tag size="small" type="warning">⭐ {{ formatNum(p.stars) }} (+{{ p.stars_today }})</el-tag>
              <el-tag size="small" type="success">相关度 {{ p.relevance_score }}/10</el-tag>
              <el-tag v-if="p.language" size="small">{{ p.language }}</el-tag>
            </div>
            <p class="project-summary">{{ p.summary_zh }}</p>
            <p class="project-reason">💡 {{ p.relevance_reason }}</p>
            <div v-if="p.topics?.length" class="project-topics">
              <el-tag v-for="t in p.topics.slice(0, 8)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
            </div>
          </div>
        </el-card>

        <!-- Others -->
        <el-card shadow="never" class="section-card">
          <template #header><span>📈 今日热门</span></template>
          <!-- Mobile: card list -->
          <div class="mobile-list">
            <div v-for="p in others" :key="p.name" class="mobile-project-card">
              <div class="mobile-card-top">
                <a :href="p.url" target="_blank" class="project-link">{{ p.name }}</a>
                <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制链接" />
              </div>
              <div class="mobile-card-tags">
                <el-tag size="small">{{ p.category }}</el-tag>
                <span class="star-text">⭐ +{{ p.stars_today }}</span>
              </div>
              <p class="mobile-summary">{{ p.summary_zh }}</p>
            </div>
          </div>
          <!-- Desktop: table -->
          <el-table :data="others" stripe class="desktop-table">
            <el-table-column label="项目" min-width="180">
              <template #default="{ row }">
                <a :href="row.url" target="_blank" class="project-link">{{ row.name }}</a>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" align="center">
              <template #default="{ row }"><el-tag size="small">{{ row.category }}</el-tag></template>
            </el-table-column>
            <el-table-column label="⭐ 今日" width="90" align="center">
              <template #default="{ row }">
                <span style="color: #e3b341; font-weight: 600;">+{{ row.stars_today }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="summary_zh" label="摘要" min-width="200" show-overflow-tooltip />
            <el-table-column label="分享" width="70" align="center">
              <template #default="{ row }">
                <el-button :icon="CopyDocument" link @click="copyUrl(row.url)" />
              </template>
            </el-table-column>
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
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const store = useReportStore()

const report = computed(() => store.currentReport)
const projects = computed(() => report.value?.projects || [])
const highlights = computed(() => projects.value.filter(p => p.relevance_score >= 7))
const others = computed(() => projects.value.filter(p => p.relevance_score < 7))

function formatNum(n) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n }

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(
    () => ElMessage.success('链接已复制'),
    () => ElMessage.error('复制失败')
  )
}

onMounted(() => store.fetchDetail(route.params.id))
</script>

<style scoped>
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; margin-bottom: 12px; }
.section-card { margin-bottom: 16px; }
.project-card { padding: 16px; border-radius: 8px; margin-bottom: 12px; }
.project-card.highlight { background: #fff8f0; border-left: 4px solid #f0883e; }
.project-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.project-name { font-size: 16px; font-weight: 600; color: #0969da; text-decoration: none; }
.project-name:hover { text-decoration: underline; }
.project-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 4px; }
.project-summary { margin: 8px 0 4px; font-size: 14px; color: #333; }
.project-reason { font-size: 13px; color: #888; margin: 0; }
.project-topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.project-link { color: #0969da; text-decoration: none; font-weight: 500; }
.project-link:hover { text-decoration: underline; }

/* Mobile/Desktop toggle */
.mobile-list { display: none; }
.mobile-project-card { padding: 12px; border-bottom: 1px solid #eee; }
.mobile-card-top { display: flex; justify-content: space-between; align-items: center; }
.mobile-card-tags { display: flex; gap: 8px; align-items: center; margin-top: 6px; }
.star-text { color: #e3b341; font-weight: 600; font-size: 13px; }
.mobile-summary { font-size: 13px; color: #666; margin-top: 6px; }

@media (max-width: 768px) {
  .mobile-list { display: block; }
  .desktop-table { display: none; }
}
</style>
