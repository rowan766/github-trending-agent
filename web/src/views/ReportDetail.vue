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
            <div class="project-top">
              <div class="project-name-row">
                <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
                <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制 GitHub 链接" />
              </div>
              <div class="project-meta">
                <el-tag size="small" type="primary">{{ p.category }}</el-tag>
                <el-tag size="small" type="warning">⭐ {{ formatNum(p.stars) }} (+{{ p.stars_today }})</el-tag>
                <el-tag v-if="p.forks" size="small">🍴 {{ formatNum(p.forks) }}</el-tag>
                <el-tag size="small" type="success">相关度 {{ p.relevance_score }}/10</el-tag>
                <el-tag v-if="p.language" size="small" effect="plain">{{ p.language }}</el-tag>
              </div>
            </div>
            <div class="project-body">
              <p class="project-summary">📝 {{ p.summary_zh }}</p>
              <p class="project-reason">💡 <strong>与你的关联：</strong>{{ p.relevance_reason }}</p>
              <p v-if="p.description" class="project-desc">💬 <strong>原始描述：</strong>{{ p.description }}</p>
              <div v-if="p.readme_snippet" class="project-readme">
                <p class="readme-label">📖 README 摘录：</p>
                <div class="readme-content">{{ p.readme_snippet }}</div>
              </div>
              <div v-if="p.topics?.length" class="project-topics">
                <el-tag v-for="t in p.topics.slice(0, 10)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
              </div>
              <div class="project-score">
                <span>综合得分：</span>
                <el-progress :percentage="p.final_score * 10" :stroke-width="10" :show-text="false"
                  color="#f0883e" style="width: 120px; display: inline-block; vertical-align: middle;" />
                <span class="score-num">{{ p.final_score }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Others -->
        <el-card shadow="never" class="section-card">
          <template #header><span>📈 今日热门</span></template>
          <!-- Mobile card list -->
          <div class="mobile-list">
            <div v-for="p in others" :key="p.name" class="project-card other-card">
              <div class="project-name-row">
                <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
                <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" />
              </div>
              <div class="project-meta">
                <el-tag size="small">{{ p.category }}</el-tag>
                <el-tag size="small" type="warning">⭐ +{{ p.stars_today }}</el-tag>
                <el-tag v-if="p.language" size="small" effect="plain">{{ p.language }}</el-tag>
              </div>
              <p class="project-summary">📝 {{ p.summary_zh }}</p>
              <p v-if="p.description && p.description !== p.summary_zh" class="project-desc">💬 {{ p.description }}</p>
              <p v-if="p.relevance_reason" class="project-reason">💡 {{ p.relevance_reason }}</p>
              <div v-if="p.topics?.length" class="project-topics">
                <el-tag v-for="t in p.topics.slice(0, 6)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
              </div>
            </div>
          </div>
          <!-- Desktop table -->
          <el-table :data="others" stripe class="desktop-table">
            <el-table-column label="项目" min-width="160">
              <template #default="{ row }">
                <a :href="row.url" target="_blank" class="project-link">{{ row.name }}</a>
                <div class="cell-desc">{{ row.summary_zh }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="110" align="center">
              <template #default="{ row }"><el-tag size="small">{{ row.category }}</el-tag></template>
            </el-table-column>
            <el-table-column label="语言" width="100" align="center">
              <template #default="{ row }"><span>{{ row.language || '-' }}</span></template>
            </el-table-column>
            <el-table-column label="⭐ 今日" width="90" align="center">
              <template #default="{ row }">
                <span style="color: #e3b341; font-weight: 600;">+{{ row.stars_today }}</span>
              </template>
            </el-table-column>
            <el-table-column label="总星" width="80" align="center">
              <template #default="{ row }">{{ formatNum(row.stars) }}</template>
            </el-table-column>
            <el-table-column label="相关度" width="85" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.relevance_score * 10" :stroke-width="8" :show-text="false"
                  :color="row.relevance_score >= 7 ? '#f0883e' : '#909399'" style="width: 50px; display: inline-block;" />
                <span style="margin-left: 4px; font-size: 12px;">{{ row.relevance_score }}</span>
              </template>
            </el-table-column>
            <el-table-column label="关联说明" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="cell-reason">{{ row.relevance_reason }}</span>
              </template>
            </el-table-column>
            <el-table-column label="分享" width="60" align="center">
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

/* Project card common */
.project-card {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}
.project-card.highlight {
  background: linear-gradient(135deg, #fff8f0 0%, #fff3e6 100%);
  border-left: 4px solid #f0883e;
}
.project-card.other-card {
  background: #fafbfc;
  border: 1px solid #eee;
}
.project-top { margin-bottom: 10px; }
.project-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.project-name {
  font-size: 17px;
  font-weight: 600;
  color: #0969da;
  text-decoration: none;
}
.project-name:hover { text-decoration: underline; }
.project-meta { display: flex; gap: 6px; flex-wrap: wrap; }

.project-body { margin-top: 8px; }
.project-summary {
  font-size: 14px;
  color: #333;
  margin: 6px 0;
  line-height: 1.6;
}
.project-reason {
  font-size: 13px;
  color: #666;
  margin: 4px 0;
  line-height: 1.5;
}
.project-desc {
  font-size: 13px;
  color: #888;
  margin: 4px 0;
  line-height: 1.5;
}
.project-readme {
  margin: 8px 0;
  padding: 10px 12px;
  background: #f6f8fa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}
.readme-label {
  font-size: 12px;
  color: #666;
  margin: 0 0 4px;
}
.readme-content {
  font-size: 13px;
  color: #444;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}
.project-topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.project-score {
  margin-top: 10px;
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}
.score-num { font-weight: 600; color: #f0883e; }

/* Table cells */
.project-link { color: #0969da; text-decoration: none; font-weight: 500; }
.project-link:hover { text-decoration: underline; }
.cell-desc { font-size: 12px; color: #888; margin-top: 2px; line-height: 1.4; }
.cell-reason { font-size: 12px; color: #666; }

/* Mobile/Desktop toggle */
.mobile-list { display: none; }

@media (max-width: 768px) {
  .mobile-list { display: block; }
  .desktop-table { display: none; }
  .project-name { font-size: 15px; }
  .project-readme { max-height: 100px; overflow-y: auto; }
}
</style>
