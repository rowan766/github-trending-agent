import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getReports, getReportDetail, getStatus, triggerPipeline } from '../api'

export const useReportStore = defineStore('report', () => {
  const list = ref([])
  const currentReport = ref(null)
  const pipelineStatus = ref({ running: false, last_result: null, progress: { percentage: 0, step: 'idle', message: '等待中' } })
  const loading = ref(false)

  async function fetchList(limit = 50) {
    loading.value = true
    try { list.value = (await getReports(limit)).data }
    finally { loading.value = false }
  }

  async function fetchDetail(id) {
    loading.value = true
    try { currentReport.value = (await getReportDetail(id)).data }
    finally { loading.value = false }
  }

  async function fetchStatus() {
    try { pipelineStatus.value = (await getStatus()).data }
    catch {}
  }

  async function trigger() {
    const { data } = await triggerPipeline()
    if (data.status === 'triggered') pipelineStatus.value.running = true
    return data
  }

  return { list, currentReport, pipelineStatus, loading, fetchList, fetchDetail, fetchStatus, trigger }
})
