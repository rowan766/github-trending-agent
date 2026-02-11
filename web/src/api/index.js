import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getHealth = () => api.get('/health')
export const getStatus = () => api.get('/status')
export const triggerPipeline = () => api.post('/trigger')

export const getTechStack = () => api.get('/config/tech-stack')
export const updateTechStack = (items) => api.put('/config/tech-stack', items)

export const getReports = (limit = 50) => api.get('/reports', { params: { limit } })
export const getReportDetail = (id) => api.get(`/reports/${id}`)
export const getReportHtml = (id) => api.get(`/reports/${id}/html`)
