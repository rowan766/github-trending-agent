<template>
  <div class="settings">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <h2>⚙️ 技术方向配置</h2>
            <el-text type="info">选择你关注的技术方向，点击卡片可查看和编辑标签详情</el-text>
          </div>
          <el-button type="primary" :loading="store.loading" @click="handleSave">保存配置</el-button>
        </div>
      </template>

      <div class="directions-grid" v-loading="store.loading">
        <div
          v-for="(dir, index) in store.directions"
          :key="dir.name"
          class="direction-card"
          :class="{ active: dir.enabled }"
        >
          <div class="direction-header">
            <span class="direction-name" @click="openDetail(index)">{{ dir.name }}</span>
            <div class="direction-actions">
              <el-switch :model-value="dir.enabled" @change="store.toggleDirection(index)" />
              <el-button type="danger" link size="small" @click="handleRemoveDirection(index)" title="删除方向">✕</el-button>
            </div>
          </div>
          <div class="direction-tags" @click="openDetail(index)">
            <el-tag
              v-for="tag in dir.tags.slice(0, 6)"
              :key="tag"
              size="small"
              :type="dir.enabled ? '' : 'info'"
              effect="plain"
              class="tag-item"
            >{{ tag }}</el-tag>
            <el-tag v-if="dir.tags.length > 6" size="small" type="warning" effect="plain" class="tag-item tag-more">
              +{{ dir.tags.length - 6 }} 点击查看全部
            </el-tag>
            <el-tag v-if="dir.tags.length === 0" size="small" type="info" effect="plain" class="tag-item">
              暂无标签，点击添加
            </el-tag>
          </div>
        </div>

        <!-- Add new direction card -->
        <div class="direction-card add-card" @click="showAddDialog = true">
          <div class="add-card-content">
            <span class="add-icon">＋</span>
            <span>新增方向</span>
          </div>
        </div>
      </div>

      <el-alert type="info" :closable="false" style="margin-top: 20px">
        <template #title><strong>说明</strong></template>
        <div style="line-height: 2">
          这里的标签仅用于对分析结果中匹配的项目做<strong>高亮标记</strong>，不影响数据的排序和抓取结果。
          所有项目始终按星数排序展示，匹配到你关注方向的项目会带有 🎯 相关 标记，方便快速定位。
        </div>
      </el-alert>
    </el-card>

    <!-- Detail dialog -->
    <el-dialog v-model="detailVisible" :title="`编辑方向：${editingDir?.name || ''}`" width="500px" class="setting-dialog" destroy-on-close>
      <div v-if="editingDir" class="detail-content">
        <div class="detail-tags">
          <el-tag
            v-for="(tag, tagIdx) in editingDir.tags"
            :key="tag"
            closable
            :type="editingDir.enabled ? '' : 'info'"
            @close="handleRemoveTag(tagIdx)"
            class="detail-tag"
          >{{ tag }}</el-tag>
        </div>
        <div class="add-tag-row">
          <el-input v-model="newTag" placeholder="输入新标签，回车添加" @keyup.enter="handleAddTag" size="small" class="tag-input" />
          <el-button type="primary" size="small" @click="handleAddTag" :disabled="!newTag.trim()">添加</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Add direction dialog -->
    <el-dialog v-model="showAddDialog" title="新增技术方向" width="400px" class="setting-dialog" destroy-on-close>
      <el-input v-model="newDirName" placeholder="输入方向名称，如：Rust、移动端、数据库" @keyup.enter="handleAddDirection" />
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddDirection" :disabled="!newDirName.trim()">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTechStackStore } from '../stores/techStack'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useTechStackStore()

const detailVisible = ref(false)
const editingIndex = ref(-1)
const editingDir = ref(null)
const newTag = ref('')
const showAddDialog = ref(false)
const newDirName = ref('')

function openDetail(index) {
  editingIndex.value = index
  editingDir.value = store.directions[index]
  detailVisible.value = true
}

function handleAddTag() {
  const tag = newTag.value.trim().toLowerCase()
  if (!tag) return
  if (store.addTag(editingIndex.value, tag)) {
    newTag.value = ''
  } else {
    ElMessage.warning('该标签已存在')
  }
}

function handleRemoveTag(tagIdx) {
  store.removeTag(editingIndex.value, tagIdx)
}

function handleAddDirection() {
  const name = newDirName.value.trim()
  if (!name) return
  if (store.addDirection(name)) {
    newDirName.value = ''
    showAddDialog.value = false
    ElMessage.success(`已添加方向：${name}`)
  } else {
    ElMessage.warning('该方向已存在')
  }
}

async function handleRemoveDirection(index) {
  const dir = store.directions[index]
  try {
    await ElMessageBox.confirm(`确定删除方向「${dir.name}」及其所有标签？`, '确认', { type: 'warning' })
    store.removeDirection(index)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

async function handleSave() {
  try {
    await store.save()
    ElMessage.success('配置已保存')
  } catch { ElMessage.error('保存失败') }
}

onMounted(() => store.fetch())
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; }
.card-header h2 { margin-bottom: 4px; }

.directions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.direction-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.25s;
  background: #fafafa;
}

.direction-card:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.direction-card.active {
  border-color: #f0883e;
  background: #fff8f0;
}

.direction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.direction-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
}

.direction-name:hover { color: #0969da; }

.direction-card.active .direction-name { color: #f0883e; }
.direction-card.active .direction-name:hover { color: #d4700a; }

.direction-actions { display: flex; align-items: center; gap: 8px; }

.direction-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  cursor: pointer;
  min-height: 28px;
}

.tag-item { font-size: 12px; }
.tag-more { cursor: pointer; }

.add-card {
  border: 2px dashed #dcdfe6;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
}

.add-card:hover { border-color: #f0883e; background: #fff8f0; }

.add-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
}

.add-icon { font-size: 28px; color: #c0c4cc; }
.add-card:hover .add-icon { color: #f0883e; }
.add-card:hover .add-card-content { color: #f0883e; }

.detail-content { min-height: 100px; }
.detail-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; min-height: 32px; }
.detail-tag { font-size: 13px; }
.add-tag-row { display: flex; gap: 8px; }
.tag-input { flex: 1; }

@media (max-width: 768px) {
  .directions-grid { grid-template-columns: 1fr; }
  .card-header { flex-direction: column; align-items: flex-start; }
  .card-header .el-button { align-self: flex-end; }
  .direction-card { padding: 12px; }
  .direction-name { font-size: 15px; }
  .tag-item { font-size: 11px; }
  .detail-tag { font-size: 12px; }
  .add-tag-row { flex-direction: column; }
  .add-tag-row .el-button { align-self: flex-end; }
}
:global(.setting-dialog) { --el-dialog-width: 92vw !important; max-width: 500px; }
</style>
