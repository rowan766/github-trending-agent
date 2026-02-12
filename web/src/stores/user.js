import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getMe, updateProfile as updateProfileApi } from '../api'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const { data } = await loginApi({ username, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function doRegister(username, password, email) {
    const { data } = await registerApi({ username, password, email })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    try {
      const { data } = await getMe()
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
    } catch { logout() }
  }

  async function updateProfile(profileData) {
    const { data } = await updateProfileApi(profileData)
    user.value = { ...user.value, ...data }
    localStorage.setItem('user', JSON.stringify(user.value))
    return data
  }

  return { user, token, isLoggedIn, isAdmin, login, doRegister, logout, fetchMe, updateProfile }
})
