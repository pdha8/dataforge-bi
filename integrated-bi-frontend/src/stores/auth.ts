import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface UserProfile {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role?: string
  department?: string
  job_title?: string
  phone?: string
  employee_id?: string
  timezone?: string
  language?: string
  two_factor_enabled?: boolean
  api_access_enabled?: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<UserProfile | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(email: string, password: string) {
    const { data } = await axios.post(`${BASE_URL}/api/auth/jwt/token/`, { email, password })
    accessToken.value = data.access
    refreshToken.value = data.refresh
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  function setUser(profile: UserProfile) {
    user.value = profile
  }

  return { accessToken, refreshToken, user, isAuthenticated, login, logout, setUser }
})
