<template>
  <div class="project-list">
    <el-empty v-if="!projects.length" description="暂无数据" />

    <div v-for="p in projects" :key="p.name" class="project-card" :class="{ highlight: p.highlight }">
      <div class="project-name-row">
        <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
        <el-tag v-if="p.highlight" size="small" type="warning" effect="dark" class="highlight-badge">🎯 相关</el-tag>
        <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制链接" />
      </div>
      <div class="project-meta">
        <el-tag size="small" type="primary">{{ p.category }}</el-tag>
        <el-tag size="small" type="warning">⭐ {{ fmt(p.stars) }}<template v-if="showStarsToday"> (+{{ p.stars_today }})</template></el-tag>
        <el-tag v-if="p.forks" size="small">🍴 {{ fmt(p.forks) }}</el-tag>
        <el-tag v-if="p.language" size="small" effect="plain">{{ p.language }}</el-tag>
      </div>
      <p class="project-summary">📝 {{ p.summary_zh }}</p>
      <p v-if="p.relevance_reason" class="project-reason">💡 <strong>关联：</strong>{{ p.relevance_reason }}</p>
      <p v-if="p.description" class="project-desc">💬 {{ p.description }}</p>
      <div v-if="p.readme_snippet" class="project-readme">
        <p class="readme-label">📖 README 摘录</p>
        <div class="readme-content">{{ p.readme_snippet }}</div>
      </div>
      <div v-if="p.topics?.length" class="project-topics">
        <el-tag v-for="t in p.topics.slice(0, 10)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineProps({
  projects: { type: Array, default: () => [] },
  periodLabel: { type: String, default: '' },
  showStarsToday: { type: Boolean, default: true },
})

function fmt(n) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n }
function copyUrl(url) {
  navigator.clipboard.writeText(url).then(
    () => ElMessage.success('链接已复制'),
    () => ElMessage.error('复制失败')
  )
}
</script>

<style scoped>
.project-card { padding: 14px; border-radius: 8px; margin-bottom: 10px; background: #fafbfc; border: 1px solid #eee; }
.project-card.highlight {
  background: linear-gradient(135deg, #fff8f0 0%, #fff3e6 100%);
  border-left: 4px solid #f0883e;
}
.highlight-badge { margin-left: 8px; }
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

@media (max-width: 768px) {
  .project-name { font-size: 15px; }
}
</style>
