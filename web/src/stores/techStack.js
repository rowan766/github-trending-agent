import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTechStack, updateTechStack } from '../api'

export const useTechStackStore = defineStore('techStack', () => {
  const directions = ref([])
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const res = await getTechStack()
      directions.value = (res.data || []).map(d => ({
        ...d,
        tags: Array.isArray(d.tags) ? d.tags : [],
      }))
    } finally { loading.value = false }
  }

  async function save() {
    loading.value = true
    try { await updateTechStack(directions.value) }
    finally { loading.value = false }
  }

  function toggleDirection(index) {
    directions.value[index].enabled = !directions.value[index].enabled
  }

  function addDirection(name) {
    if (directions.value.some(d => d.name === name)) return false
    directions.value.push({ name, enabled: true, tags: [] })
    return true
  }

  function removeDirection(index) {
    directions.value.splice(index, 1)
  }

  function addTag(dirIndex, tag) {
    const dir = directions.value[dirIndex]
    if (!dir || dir.tags.includes(tag)) return false
    dir.tags.push(tag)
    return true
  }

  function removeTag(dirIndex, tagIndex) {
    directions.value[dirIndex]?.tags.splice(tagIndex, 1)
  }

  return { directions, loading, fetch, save, toggleDirection, addDirection, removeDirection, addTag, removeTag }
})
