<template>
  <div class="user-mgmt">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h2>👥 用户管理</h2>
          <el-button type="primary" :icon="Plus" @click="showAdd = true">添加用户</el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" stripe class="desktop-table">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role === 'admin' ? '管理员' : '用户' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-popconfirm v-if="row.role !== 'admin'" title="确定删除该用户？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="mobile-list" v-loading="loading">
        <div v-for="row in users" :key="row.id" class="mobile-user-card">
          <div class="mobile-user-top">
            <div class="mobile-user-info">
              <strong>{{ row.username }}</strong>
              <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role === 'admin' ? '管理员' : '用户' }}</el-tag>
            </div>
            <div class="mobile-user-actions">
              <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
              <el-popconfirm v-if="row.role !== 'admin'" title="确定删除该用户？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
          <el-text v-if="row.email" type="info" size="small" class="mobile-user-email">{{ row.email }}</el-text>
          <el-text type="info" size="small">{{ row.created_at }}</el-text>
        </div>
      </div>
    </el-card>

    <!-- Add dialog -->
    <el-dialog v-model="showAdd" title="添加用户" width="420px" class="user-dialog" destroy-on-close>
      <el-form :model="addForm" label-width="70px">
        <el-form-item label="用户名"><el-input v-model="addForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="addForm.password" type="password" show-password /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="addForm.email" /></el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="addForm.role">
            <el-radio value="user">普通用户</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- Edit dialog -->
    <el-dialog v-model="showEdit" title="编辑用户" width="420px" class="user-dialog" destroy-on-close>
      <el-form :model="editForm" label-width="70px">
        <el-form-item label="用户名"><el-input v-model="editForm.username" /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="editForm.password" type="password" placeholder="留空不修改" show-password /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="editForm.email" /></el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="editForm.role">
            <el-radio value="user">普通用户</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '../api'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const submitting = ref(false)
const showAdd = ref(false)
const showEdit = ref(false)
const addForm = reactive({ username: '', password: '', email: '', role: 'user' })
const editForm = reactive({ id: 0, username: '', password: '', email: '', role: 'user' })

async function fetchUsers() {
  loading.value = true
  try { users.value = (await getUsers()).data }
  finally { loading.value = false }
}

async function handleAdd() {
  if (!addForm.username || !addForm.password) return ElMessage.warning('请填写用户名和密码')
  submitting.value = true
  try {
    await createUser(addForm)
    ElMessage.success('添加成功')
    showAdd.value = false
    Object.assign(addForm, { username: '', password: '', email: '', role: 'user' })
    await fetchUsers()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '添加失败') }
  finally { submitting.value = false }
}

function openEdit(row) {
  Object.assign(editForm, { id: row.id, username: row.username, email: row.email, role: row.role, password: '' })
  showEdit.value = true
}

async function handleEdit() {
  submitting.value = true
  const data = { username: editForm.username, email: editForm.email, role: editForm.role }
  if (editForm.password) data.password = editForm.password
  try {
    await updateUser(editForm.id, data)
    ElMessage.success('修改成功')
    showEdit.value = false
    await fetchUsers()
  } catch (e) { ElMessage.error('修改失败') }
  finally { submitting.value = false }
}

async function handleDelete(id) {
  try {
    await deleteUser(id)
    ElMessage.success('已删除')
    await fetchUsers()
  } catch (e) { ElMessage.error('删除失败') }
}

onMounted(fetchUsers)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.mobile-list { display: none; }
.mobile-user-card { padding: 12px 0; border-bottom: 1px solid #eee; }
.mobile-user-card:last-child { border-bottom: none; }
.mobile-user-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.mobile-user-info { display: flex; align-items: center; gap: 8px; }
.mobile-user-actions { display: flex; gap: 4px; }
.mobile-user-email { display: block; margin-bottom: 2px; word-break: break-all; }

@media (max-width: 768px) {
  .desktop-table { display: none; }
  .mobile-list { display: block; }
}
</style>
<style>
.user-dialog { --el-dialog-width: 92vw !important; max-width: 420px; }
</style>
