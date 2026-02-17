<template>
  <div class="project-list">
    <el-empty v-if="!projects.length" description="暂无数据" />

    <div v-for="p in projects" :key="p.name" class="project-card" :class="{ highlight: p.highlight }">
      <div class="project-name-row">
        <a :href="p.url" target="_blank" class="project-name">{{ p.name }}</a>
        <el-tag v-if="p.highlight" size="small" type="warning" effect="dark" class="highlight-badge">🎯 相关</el-tag>
        <el-button size="small" :icon="CopyDocument" circle @click="copyUrl(p.url)" title="复制链接" />
        <el-button size="small" type="primary" plain @click="openDetail(p)">详情</el-button>
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
      <div v-if="p.topics?.length" class="project-topics">
        <el-tag v-for="t in p.topics.slice(0, 10)" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
      </div>
    </div>

    <!-- 项目详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="currentProject?.name || '项目详情'"
      width="680px"
      top="5vh"
      destroy-on-close
      class="project-detail-dialog"
    >
      <template v-if="currentProject">
        <div class="detail-section">
          <div class="detail-header">
            <a :href="currentProject.url" target="_blank" class="detail-repo-link">{{ currentProject.name }}</a>
            <el-tag v-if="currentProject.highlight" size="small" type="warning" effect="dark">🎯 与你的技术栈相关</el-tag>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="detail-section">
          <h4 class="detail-label">基本信息</h4>
          <div class="detail-stats">
            <el-tag type="warning">⭐ {{ fmt(currentProject.stars) }} 星标</el-tag>
            <el-tag v-if="currentProject.stars_today">📈 今日 +{{ currentProject.stars_today }}</el-tag>
            <el-tag v-if="currentProject.forks">🍴 {{ fmt(currentProject.forks) }} 分叉</el-tag>
            <el-tag v-if="currentProject.language" effect="plain">{{ currentProject.language }}</el-tag>
            <el-tag type="info">{{ categoryLabel(currentProject.category) }}</el-tag>
            <el-tag v-if="currentProject.trending_type" type="success" effect="plain">{{ trendingLabel(currentProject.trending_type) }}</el-tag>
          </div>
        </div>

        <!-- 项目详细介绍 -->
        <div class="detail-section">
          <h4 class="detail-label">项目详细介绍</h4>
          <div v-if="currentProject.detail_zh" class="detail-content">{{ currentProject.detail_zh }}</div>
          <p v-else class="detail-text">{{ currentProject.summary_zh }}</p>
          <p v-if="currentProject.description" class="detail-text-sub">{{ currentProject.description }}</p>
        </div>

        <!-- 相关性评估 -->
        <div v-if="currentProject.relevance_score" class="detail-section">
          <h4 class="detail-label">与你的技术栈相关性</h4>
          <div class="detail-relevance">
            <el-progress
              :percentage="currentProject.relevance_score * 10"
              :color="relevanceColor(currentProject.relevance_score)"
              :stroke-width="18"
              :text-inside="true"
              :format="() => `${currentProject.relevance_score} / 10`"
            />
            <p v-if="currentProject.relevance_reason" class="detail-text" style="margin-top: 8px;">
              💡 {{ currentProject.relevance_reason }}
            </p>
          </div>
        </div>

        <!-- 技术标签 -->
        <div v-if="currentProject.tech_tags?.length" class="detail-section">
          <h4 class="detail-label">技术标签</h4>
          <div class="detail-tags">
            <el-tag v-for="tag in currentProject.tech_tags" :key="tag" size="default" effect="plain" type="primary">{{ tag }}</el-tag>
          </div>
        </div>

        <!-- GitHub Topics -->
        <div v-if="currentProject.topics?.length" class="detail-section">
          <h4 class="detail-label">GitHub Topics</h4>
          <div class="detail-tags">
            <el-tag v-for="t in currentProject.topics" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
          </div>
        </div>

        <!-- README 摘要 -->
        <div v-if="currentProject.readme_snippet" class="detail-section">
          <h4 class="detail-label">README 预览</h4>
          <div class="detail-readme">{{ currentProject.readme_snippet }}</div>
        </div>
      </template>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="openGithub(currentProject?.url)">在 GitHub 中打开</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineProps({
  projects: { type: Array, default: () => [] },
  periodLabel: { type: String, default: '' },
  showStarsToday: { type: Boolean, default: true },
})

const detailVisible = ref(false)
const currentProject = ref(null)

function openDetail(project) {
  currentProject.value = project
  detailVisible.value = true
}

function fmt(n) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n }
function copyUrl(url) {
  navigator.clipboard.writeText(url).then(
    () => ElMessage.success('链接已复制'),
    () => ElMessage.error('复制失败')
  )
}

function trendingLabel(type) {
  const map = { daily: '今日热门', weekly: '本周热门', monthly: '本月热门' }
  return map[type] || type
}

function categoryLabel(cat) {
  return cat || '未分类'
}

function relevanceColor(score) {
  if (score >= 8) return '#67c23a'
  if (score >= 5) return '#e6a23c'
  return '#909399'
}

function openGithub(url) {
  window.open(url, '_blank')
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
.project-topics { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }

/* 详情弹窗样式 */
.detail-section { margin-bottom: 18px; }
.detail-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.detail-repo-link { font-size: 20px; font-weight: 700; color: #0969da; text-decoration: none; }
.detail-repo-link:hover { text-decoration: underline; }
.detail-label { font-size: 14px; font-weight: 600; color: #24292f; margin: 0 0 8px 0; padding-bottom: 4px; border-bottom: 1px solid #eee; }
.detail-stats { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-text { font-size: 14px; color: #333; line-height: 1.7; margin: 0; }
.detail-text-sub { font-size: 13px; color: #666; line-height: 1.6; margin: 6px 0 0 0; }
.detail-content {
  font-size: 14px; color: #333; line-height: 1.8; margin: 0;
  white-space: pre-wrap; word-break: break-word;
  background: #f9fafb; border-radius: 6px; padding: 12px 14px;
  border-left: 3px solid #409eff;
}
.detail-relevance { margin-top: 4px; }
.detail-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-readme {
  font-size: 13px; color: #555; line-height: 1.7;
  background: #f6f8fa; border-radius: 6px; padding: 12px;
  white-space: pre-wrap; word-break: break-word;
  max-height: 200px; overflow-y: auto;
  border: 1px solid #e1e4e8;
}

@media (max-width: 768px) {
  .project-card { padding: 12px; }
  .project-name-row { flex-wrap: wrap; }
  .project-name { font-size: 14px; word-break: break-all; }
  .project-meta .el-tag { font-size: 11px; }
  .project-summary { font-size: 13px; }
  .project-reason { font-size: 12px; }
  .project-desc { font-size: 12px; }
  .project-topics .el-tag { font-size: 11px; }
}
</style>
