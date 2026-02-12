import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { noAuth: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },
  { path: '/report/:id', name: 'ReportDetail', component: () => import('../views/ReportDetail.vue') },
  { path: '/users', name: 'Users', component: () => import('../views/UserManagement.vue'), meta: { admin: true } },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.noAuth && !token) return '/login'
})

export default router
