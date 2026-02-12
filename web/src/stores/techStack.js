import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTechStack, updateTechStack, getPresetTypes } from '../api'

export const useTechStackStore = defineStore('techStack', () => {
  const items = ref([])
  const presetTypes = ref([])
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const [stackRes, typesRes] = await Promise.all([getTechStack(), getPresetTypes()])
      items.value = stackRes.data
      presetTypes.value = typesRes.data
    } finally { loading.value = false }
  }

  async function save() {
    loading.value = true
    try { await updateTechStack(items.value) }
    finally { loading.value = false }
  }

  function addItem(name) {
    if (items.value.some(i => i.name === name)) return false
    items.value.push({ name, weight: 5, enabled: true, preset: false })
    return true
  }

  function removeItem(index) { items.value.splice(index, 1) }

  return { items, presetTypes, loading, fetch, save, addItem, removeItem }
})
