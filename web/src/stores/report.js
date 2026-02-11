import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getReports, getReportDetail, getStatus, triggerPipeline } from '../api'

export const useReportStore = defineStore('report', () => {
  const list = ref([])
  const currentReport = ref(null)
  const pipelineStatus = ref({ running: false, last_result: null })
  const loading = ref(false)

  async function fetchList() {
    loading.value = true
    try {
      const { data } = await getReports()
      list.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id) {
    loading.value = true
    try {
      const { data } = await getReportDetail(id)
      currentReport.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchStatus() {
    const { data } = await getStatus()
    pipelineStatus.value = data
  }

  async function trigger() {
    const { data } = await triggerPipeline()
    pipelineStatus.value.running = data.status === 'triggered'
    return data
  }

  return { list, currentReport, pipelineStatus, loading, fetchList, fetchDetail, fetchStatus, trigger }
})
