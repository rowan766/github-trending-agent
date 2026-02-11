import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTechStack, updateTechStack } from '../api'

export const useTechStackStore = defineStore('techStack', () => {
  const items = ref([])
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const { data } = await getTechStack()
      items.value = data
    } finally {
      loading.value = false
    }
  }

  async function save() {
    loading.value = true
    try {
      await updateTechStack(items.value)
    } finally {
      loading.value = false
    }
  }

  function addItem(name) {
    if (items.value.some(i => i.name === name)) return false
    items.value.push({ name, weight: 5, enabled: true, preset: false })
    return true
  }

  function removeItem(index) {
    items.value.splice(index, 1)
  }

  function toggleItem(index) {
    items.value[index].enabled = !items.value[index].enabled
  }

  return { items, loading, fetch, save, addItem, removeItem, toggleItem }
})
