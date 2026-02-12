<template>
  <div class="project-list">
    <el-empty v-if="!projects.length" description="暂无数据" />

    <!-- Highlights: relevance >= 7 -->
    <template v-if="highlights.length">
      <div class="section-title">🎯 与你技术栈相关 ({{ highlights.length }})</div>
      <div v-for="p in highlights" :key="p.name" class="project-card highlight">
        <div class="project-name-row">
          <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
          <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制链接" />
        </div>
        <div class="project-meta">
          <el-tag size="small" type="primary">{{ p.category }}</el-tag>
          <el-tag size="small" type="warning">⭐ {{ fmt(p.stars) }}<template v-if="showStarsToday"> (+{{ p.stars_today }})</template></el-tag>
          <el-tag v-if="p.forks" size="small">🍴 {{ fmt(p.forks) }}</el-tag>
          <el-tag size="small" type="success">相关度 {{ p.relevance_score }}/10</el-tag>
          <el-tag v-if="p.language" size="small" effect="plain">{{ p.language }}</el-tag>
        </div>
        <p class="project-summary">📝 {{ p.summary_zh }}</p>
        <p class="project-reason">💡 <strong>关联：</strong>{{ p.relevance_reason }}</p>
        <p v-if="p.description" class="project-desc">💬 {{ p.description }}</p>
        <div v-if="p.readme_snippet" class="project-readme">
          <p class="readme-label">📖 README 摘录</p>
          <div class="readme-content">{{ p.readme_snippet }}</div>
        </div>
        <div v-if="p.topics?.length" class="project-topics">
          <el-tag v-for="t in p.topics.slice(0, 10)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
        </div>
      </div>
    </template>

    <!-- Others -->
    <template v-if="others.length">
      <div class="section-title">📈 {{ periodLabel ? periodLabel + '热门' : '全部项目' }} ({{ others.length }})</div>
      <!-- Mobile -->
      <div class="mobile-list">
        <div v-for="p in others" :key="p.name" class="project-card other-card">
          <div class="project-name-row">
            <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
            <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" />
          </div>
          <div class="project-meta">
            <el-tag size="small">{{ p.category }}</el-tag>
            <el-tag size="small" type="warning">⭐ {{ fmt(p.stars) }}<template v-if="showStarsToday"> (+{{ p.stars_today }})</template></el-tag>
            <el-tag v-if="p.language" size="small" effect="plain">{{ p.language }}</el-tag>
          </div>
          <p class="project-summary">📝 {{ p.summary_zh }}</p>
          <p v-if="p.relevance_reason" class="project-reason">💡 {{ p.relevance_reason }}</p>
          <div v-if="p.topics?.length" class="project-topics">
            <el-tag v-for="t in p.topics.slice(0, 6)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
          </div>
        </div>
      </div>
      <!-- Desktop -->
      <el-table :data="others" stripe class="desktop-table">
        <el-table-column label="项目" min-width="180">
          <template #default="{ row }">
            <a :href="row.url" target="_blank" class="project-link">{{ row.name }}</a>
            <div class="cell-desc">{{ row.summary_zh }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" align="center">
          <template #default="{ row }"><el-tag size="small">{{ row.category }}</el-tag></template>
        </el-table-column>
        <el-table-column label="语言" width="90" align="center">
          <template #default="{ row }">{{ row.language || '-' }}</template>
        </el-table-column>
        <el-table-column label="⭐ 总星" width="80" align="center">
          <template #default="{ row }"><span style="font-weight:600">{{ fmt(row.stars) }}</span></template>
        </el-table-column>
        <el-table-column v-if="showStarsToday" :label="`⭐ ${periodLabel || '今日'}`" width="85" align="center">
          <template #default="{ row }">
            <span style="color:#e3b341;font-weight:600">+{{ row.stars_today }}</span>
          </template>
        </el-table-column>
        <el-table-column label="相关度" width="85" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.relevance_score*10" :stroke-width="8" :show-text="false"
              :color="row.relevance_score>=7?'#f0883e':'#909399'" style="width:50px;display:inline-block" />
            <span style="margin-left:4px;font-size:12px">{{ row.relevance_score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="关联说明" min-width="140" show-overflow-tooltip>
          <template #default="{ row }"><span class="cell-reason">{{ row.relevance_reason }}</span></template>
        </el-table-column>
        <el-table-column label="" width="50" align="center">
          <template #default="{ row }">
            <el-button :icon="CopyDocument" link @click="copyUrl(row.url)" />
          </template>
        </el-table-column>
      </el-table>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  projects: { type: Array, default: () => [] },
  periodLabel: { type: String, default: '' },
  showStarsToday: { type: Boolean, default: true },
})

const highlights = computed(() => props.projects.filter(p => p.relevance_score >= 7))
const others = computed(() => props.projects.filter(p => p.relevance_score < 7))

function fmt(n) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n }
function copyUrl(url) {
  navigator.clipboard.writeText(url).then(
    () => ElMessage.success('链接已复制'),
    () => ElMessage.error('复制失败')
  )
}
</script>

<style scoped>
.section-title { font-size: 16px; font-weight: 600; margin: 16px 0 12px; color: #333; }
.section-title:first-child { margin-top: 0; }

.project-card { padding: 14px; border-radius: 8px; margin-bottom: 10px; }
.project-card.highlight {
  background: linear-gradient(135deg, #fff8f0 0%, #fff3e6 100%);
  border-left: 4px solid #f0883e;
}
.project-card.other-card { background: #fafbfc; border: 1px solid #eee; }
.project-name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.project-name { font-size: 16px; font-weight: 600; color: #0969da; text-decoration: none; }
.project-name:hover { text-decoration: underline; }
.project-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.project-summary { font-size: 14px; color: #333; margin: 4px 0; line-height: 1.6; }
.project-reason { font-size: 13px; color: #666; margin: 4px 0; line-height: 1.5; }
.project-desc { font-size: 13px; color: #888; margin: 4px 0; }
.project-readme { margin: 8px 0; padding: 10px 12px; background: #f6f8fa; border-radius: 6px; border: 1px solid #e8e8e8; }
.readme-label { font-size: 12px; color: #666; margin: 0 0 4px; }
.readme-content { font-size: 13px; color: #444; line-height: 1.6; white-space: pre-wrap; word-break: break-word; max-height: 120px; overflow-y: auto; }
.project-topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }

.project-link { color: #0969da; text-decoration: none; font-weight: 500; }
.project-link:hover { text-decoration: underline; }
.cell-desc { font-size: 12px; color: #888; margin-top: 2px; line-height: 1.4; }
.cell-reason { font-size: 12px; color: #666; }

.mobile-list { display: none; }
@media (max-width: 768px) {
  .mobile-list { display: block; }
  .desktop-table { display: none; }
  .project-name { font-size: 15px; }
}
</style>
