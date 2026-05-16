import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type UserRole =
  | 'superadmin'
  | 'admin'
  | 'bi_developer'
  | 'bi_analyst'
  | 'bi_consumer'
  | 'viewer'

export interface UserProfile {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role?: UserRole | string
  department?: string
  job_title?: string
  phone?: string
  employee_id?: string
  timezone?: string
  language?: string
  two_factor_enabled?: boolean
  api_access_enabled?: boolean
}

const PROFILE_KEY = 'user_profile'

const ROLES_ADMIN: UserRole[] = ['superadmin', 'admin']
const ROLES_MANAGE_DATA: UserRole[] = ['superadmin', 'admin', 'bi_developer']
const ROLES_MANAGE_BI: UserRole[] = ['superadmin', 'admin', 'bi_developer', 'bi_analyst']

function loadStoredProfile(): UserProfile | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    // Garde-fou : ne ré-hydrate que si le profil a un username ou email réel
    // (évite de charger une enveloppe DRF {success, data, message} corrompue)
    if (parsed && typeof parsed === 'object' && (parsed.username || parsed.email)) {
      return parsed as UserProfile
    }
    localStorage.removeItem(PROFILE_KEY)
    return null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<UserProfile | null>(loadStoredProfile())

  const isAuthenticated = computed(() => !!accessToken.value)
  const role = computed<UserRole | string>(() => user.value?.role ?? 'viewer')

  // ── Helpers de rôle ──────────────────────────────────────────────────
  const isSuperAdmin = computed(() => role.value === 'superadmin')
  const isAdmin = computed(() => ROLES_ADMIN.includes(role.value as UserRole))
  const isAnalyst = computed(() => role.value === 'bi_analyst')
  const isDeveloper = computed(() => role.value === 'bi_developer')
  const isConsumer = computed(() => role.value === 'bi_consumer' || role.value === 'viewer')

  function hasRole(...roles: (UserRole | string)[]): boolean {
    return roles.includes(role.value)
  }

  // ── Permissions fonctionnelles (miroir des permissions backend) ──────
  const canManageDataSources = computed(() => ROLES_MANAGE_DATA.includes(role.value as UserRole))
  const canManageETL = computed(() => ROLES_MANAGE_DATA.includes(role.value as UserRole))
  const canManageWarehouse = computed(() => ROLES_MANAGE_DATA.includes(role.value as UserRole))
  const canManageDashboards = computed(() => ROLES_MANAGE_BI.includes(role.value as UserRole))
  const canManageKPIs = computed(() => ROLES_MANAGE_BI.includes(role.value as UserRole))
  const canManageVisualizations = computed(() => ROLES_MANAGE_BI.includes(role.value as UserRole))
  const canExportData = computed(() => ROLES_MANAGE_BI.includes(role.value as UserRole))
  const canAccessAdmin = computed(() => ROLES_ADMIN.includes(role.value as UserRole))

  // ── Actions ──────────────────────────────────────────────────────────
  async function login(email: string, password: string) {
    const { data } = await axios.post(`${BASE_URL}/api/auth/jwt/token/`, { email, password })
    accessToken.value = data.access
    refreshToken.value = data.refresh
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    // Reset stale profile from a previous session
    user.value = null
    localStorage.removeItem(PROFILE_KEY)

    try {
      const profileRes = await axios.get(`${BASE_URL}/api/users/users/me/`, {
        headers: { Authorization: `Bearer ${data.access}` },
      })
      // L'API peut renvoyer soit le profil direct, soit une enveloppe {success, data, message}
      const payload = profileRes.data
      const profile: UserProfile | undefined =
        payload && typeof payload === 'object' && 'data' in payload && payload.data
          ? (payload.data as UserProfile)
          : (payload as UserProfile)
      if (profile && (profile.username || profile.email)) {
        setUser(profile)
      }
    } catch {
      /* profil chargé plus tard si /me/ indisponible */
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem(PROFILE_KEY)
  }

  function setUser(profile: UserProfile) {
    user.value = profile
    try { localStorage.setItem(PROFILE_KEY, JSON.stringify(profile)) } catch { /* quota */ }
  }

  async function fetchProfile() {
    if (!accessToken.value) return
    try {
      const profileRes = await axios.get(`${BASE_URL}/api/users/users/me/`, {
        headers: { Authorization: `Bearer ${accessToken.value}` },
      })
      const payload = profileRes.data
      const profile: UserProfile | undefined =
        payload && typeof payload === 'object' && 'data' in payload && payload.data
          ? (payload.data as UserProfile)
          : (payload as UserProfile)
      if (profile && (profile.username || profile.email)) {
        setUser(profile)
      }
    } catch {
      /* ignore */
    }
  }

  return {
    accessToken, refreshToken, user, role,
    isAuthenticated,
    isSuperAdmin, isAdmin, isAnalyst, isDeveloper, isConsumer,
    canManageDataSources, canManageETL, canManageWarehouse,
    canManageDashboards, canManageKPIs, canManageVisualizations,
    canExportData, canAccessAdmin,
    hasRole, login, logout, setUser, fetchProfile,
  }
})
