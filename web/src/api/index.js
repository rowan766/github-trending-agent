import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(r => r, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.hash = '#/login'
  }
  return Promise.reject(error)
})

// Auth
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')
export const updateProfile = (data) => api.put('/auth/profile', data)

// Pipeline
export const getHealth = () => api.get('/health')
export const getStatus = () => api.get('/status')
export const triggerPipeline = () => api.post('/trigger')

// Tech Stack
export const getTechStack = () => api.get('/config/tech-stack')
export const updateTechStack = (items) => api.put('/config/tech-stack', items)
export const getPresetTypes = () => api.get('/config/preset-types')

// Reports
export const getReports = (limit = 50) => api.get('/reports', { params: { limit } })
export const getReportDetail = (id) => api.get(`/reports/${id}`)
export const deleteReport = (id) => api.delete(`/reports/${id}`)

// Admin
export const getUsers = () => api.get('/admin/users')
export const createUser = (data) => api.post('/admin/users', data)
export const updateUser = (id, data) => api.put(`/admin/users/${id}`, data)
export const deleteUser = (id) => api.delete(`/admin/users/${id}`)
export const getAdminPresetTypes = () => api.get('/admin/preset-types')
export const updatePresetTypes = (types) => api.put('/admin/preset-types', types)

// Feedback
export const submitFeedback = (data) => api.post('/feedback', data)
export const getMyFeedback = () => api.get('/feedback')
export const getAdminFeedback = () => api.get('/admin/feedback')
export const replyFeedback = (id, reply) => api.put(`/admin/feedback/${id}/reply`, { reply })
