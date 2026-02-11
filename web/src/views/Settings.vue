<template>
  <div class="settings">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <h2>⚙️ 技术栈配置</h2>
            <el-text type="info">配置你关注的技术方向和权重，AI 会根据此进行个性化推荐排序</el-text>
          </div>
          <el-button type="primary" :loading="store.loading" @click="handleSave">
            保存配置
          </el-button>
        </div>
      </template>

      <div class="add-section">
        <el-input v-model="newName" placeholder="输入技术名称，如 TypeScript" @keyup.enter="handleAdd" style="width: 280px">
          <template #prepend><el-icon><Plus /></el-icon></template>
        </el-input>
        <el-button type="success" @click="handleAdd" :disabled="!newName.trim()">添加</el-button>
      </div>

      <el-table :data="store.items" v-loading="store.loading" style="margin-top: 16px">
        <el-table-column label="启用" width="70" align="center">
          <template #default="{ row, $index }">
            <el-switch v-model="row.enabled" @change="store.toggleItem($index)" />
          </template>
        </el-table-column>
        <el-table-column label="技术栈" width="180">
          <template #default="{ row }">
            <span>{{ row.name }}</span>
            <el-tag v-if="row.preset" size="small" type="info" style="margin-left: 8px">预制</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权重" min-width="300">
          <template #default="{ row }">
            <div class="weight-cell">
              <el-slider v-model="row.weight" :min="1" :max="10" :step="1" show-stops :disabled="!row.enabled" />
              <el-tag :type="row.weight >= 8 ? 'danger' : row.weight >= 5 ? 'warning' : 'info'" size="small" style="margin-left: 12px; min-width: 32px; text-align: center">
                {{ row.weight }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row, $index }">
            <el-button v-if="!row.preset" type="danger" link size="small" @click="handleRemove($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-alert type="info" :closable="false" style="margin-top: 20px">
        <template #title><strong>权重说明</strong></template>
        <div style="line-height: 2">
          权重范围 1-10，影响 AI 对项目的相关度评分。权重越高的技术方向，相关项目在日报中排名越靠前。<br />
          <el-tag type="danger" size="small">8-10</el-tag> 高优先 &nbsp;
          <el-tag type="warning" size="small">5-7</el-tag> 中等关注 &nbsp;
          <el-tag type="info" size="small">1-4</el-tag> 低优先
        </div>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTechStackStore } from '../stores/techStack'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const store = useTechStackStore()
const newName = ref('')

async function handleAdd() {
  const name = newName.value.trim()
  if (!name) return
  if (store.addItem(name)) {
    newName.value = ''
    ElMessage.success(`已添加 ${name}`)
  } else {
    ElMessage.warning(`${name} 已存在`)
  }
}

function handleRemove(index) {
  const name = store.items[index].name
  store.removeItem(index)
  ElMessage.info(`已删除 ${name}`)
}

async function handleSave() {
  try {
    await store.save()
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

onMounted(() => store.fetch())
</script>

<style scoped>
.settings { max-width: 800px; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; }
.card-header h2 { margin-bottom: 4px; }
.add-section { display: flex; gap: 12px; align-items: center; }
.weight-cell { display: flex; align-items: center; }
.weight-cell .el-slider { flex: 1; }
</style>
