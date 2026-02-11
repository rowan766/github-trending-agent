import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },
  { path: '/report/:id', name: 'ReportDetail', component: () => import('../views/ReportDetail.vue') },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
