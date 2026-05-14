<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  Users, Shield, Settings, ScrollText,
  Plus, Search, ChevronDown, X, Check,
  UserCheck, UserX, Trash2, Pencil, Mail,
  Globe, Database, Bell, Lock,
  CheckCircle2, XCircle, AlertTriangle, Info,
  Key, Plug, Users2,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
type TabId      = 'users' | 'roles' | 'teams' | 'settings' | 'audit'
type UserRole   = 'admin' | 'analyst' | 'contributor' | 'reader'
type UserStatus = 'active' | 'inactive'
interface AppUser {
  id: number
  name: string
  email: string
  role: UserRole
  status: UserStatus
  last_login: string
  initials: string
}

interface UserActivity {
  id: number
  action: string
  action_display: string
  user_name: string
  resource_type: string
  resource_name: string
  description: string
  severity: string
  severity_display: string
  severity_icon: string
  time_ago: string
  created_at: string
  success: boolean
  ip_address: string
}

interface Permission {
  key: string
  label: string
  admin: boolean; analyst: boolean; contributor: boolean; reader: boolean
}

interface Team {
  id: string
  name: string
  description: string
  team_lead: string | null
  team_lead_name: string
  members: any[]
  member_count: number
  created_at: string
}

interface UserStatsAPI {
  total_users: number
  active_users: number
  inactive_users: number
  [key: string]: any
}

// ── Tabs ───────────────────────────────────────────────────
const TABS: Array<{ id: TabId; label: string; icon: any }> = [
  { id: 'users',    label: 'Utilisateurs',        icon: Users      },
  { id: 'roles',    label: 'Rôles',               icon: Shield     },
  { id: 'teams',    label: 'Équipes',             icon: Users2     },
  { id: 'settings', label: 'Paramètres',          icon: Settings   },
  { id: 'audit',    label: "Journal d'audit",     icon: ScrollText },
]

const activeTab = ref<TabId>('users')

// ── Role metadata ──────────────────────────────────────────
const ROLE_META: Record<UserRole, { label: string; color: string; desc: string }> = {
  admin:       { label: 'Administrateur', color: 'oklch(76% 0.14 62)',  desc: 'Accès complet à toutes les fonctionnalités et paramètres' },
  analyst:     { label: 'Analyste',       color: 'oklch(65% 0.13 148)', desc: 'Création et gestion des visualisations, tableaux de bord et KPIs' },
  contributor: { label: 'Contributeur',   color: 'oklch(60% 0.12 258)', desc: 'Création de visualisations et contribution aux tableaux de bord' },
  reader:      { label: 'Lecteur',        color: 'oklch(68% 0.12 290)', desc: 'Consultation en lecture seule des tableaux de bord publiés' },
}

// ── Permissions matrix ─────────────────────────────────────
const PERMISSIONS: Permission[] = [
  { key: 'user_manage',   label: 'Gérer les utilisateurs',      admin: true,  analyst: false, contributor: false, reader: false },
  { key: 'source_write',  label: 'Créer/modifier des sources',  admin: true,  analyst: false, contributor: false, reader: false },
  { key: 'source_read',   label: 'Voir les sources',            admin: true,  analyst: true,  contributor: true,  reader: false },
  { key: 'pipeline_run',  label: 'Exécuter des pipelines',      admin: true,  analyst: true,  contributor: false, reader: false },
  { key: 'pipeline_read', label: 'Voir les pipelines',          admin: true,  analyst: true,  contributor: true,  reader: false },
  { key: 'dw_read',       label: 'Explorer le Data Warehouse',  admin: true,  analyst: true,  contributor: true,  reader: false },
  { key: 'viz_write',     label: 'Créer des visualisations',    admin: true,  analyst: true,  contributor: true,  reader: false },
  { key: 'viz_read',      label: 'Voir les visualisations',     admin: true,  analyst: true,  contributor: true,  reader: true  },
  { key: 'dash_publish',  label: 'Publier des tableaux de bord',admin: true,  analyst: true,  contributor: false, reader: false },
  { key: 'dash_read',     label: 'Voir les tableaux de bord',   admin: true,  analyst: true,  contributor: true,  reader: true  },
  { key: 'kpi_write',     label: 'Gérer les KPIs',              admin: true,  analyst: true,  contributor: false, reader: false },
  { key: 'kpi_read',      label: 'Voir les KPIs',               admin: true,  analyst: true,  contributor: true,  reader: true  },
  { key: 'settings',      label: 'Modifier les paramètres',     admin: true,  analyst: false, contributor: false, reader: false },
]

// ── Settings state ─────────────────────────────────────────
const settings = ref({
  platformName:   'Integrated BI — Sotifibre',
  language:       'fr',
  timezone:       'Africa/Algiers',
  dataRetention:  365,
  maxConnections: 50,
  refreshInterval:15,
  sessionTimeout: 60,
  require2fa:     false,
  passwordStrength:'strong',
  emailAlerts:    true,
  smtpHost:       'smtp.sotifibre.com',
  smtpPort:       '587',
  kpiAlertPct:    15,
})

const settingsSaved    = ref(false)
const settingsSaving   = ref(false)

async function saveSettings() {
  settingsSaving.value = true
  await new Promise(r => setTimeout(r, 700))
  settingsSaving.value = false
  settingsSaved.value  = true
  setTimeout(() => { settingsSaved.value = false }, 2500)
}

// ── Users state ────────────────────────────────────────────
const users          = ref<AppUser[]>([])
const loading        = ref(true)
const searchQuery    = ref('')
const filterRole     = ref<UserRole | 'all'>('all')
const filterStatus   = ref<UserStatus | 'all'>('all')
const drawerOpen     = ref(false)
const deleteConfirm  = ref<number | null>(null)
const submitting     = ref(false)

const form = ref({ name: '', email: '', role: 'reader' as UserRole })

// ── Audit state ────────────────────────────────────────────
const auditLog       = ref<UserActivity[]>([])
const auditLoading   = ref(true)
const auditFilter    = ref('all')

// ── Computed ───────────────────────────────────────────────
const filteredUsers = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return users.value.filter(u => {
    const matchQ      = !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    const matchRole   = filterRole.value   === 'all' || u.role   === filterRole.value
    const matchStatus = filterStatus.value === 'all' || u.status === filterStatus.value
    return matchQ && matchRole && matchStatus
  })
})

const userStats = computed(() => ({
  total:    users.value.length,
  active:   users.value.filter(u => u.status === 'active').length,
  inactive: users.value.filter(u => u.status === 'inactive').length,
  admins:   users.value.filter(u => u.role === 'admin').length,
}))

const roleUserCounts = computed(() => {
  const counts: Record<UserRole, number> = { admin: 0, analyst: 0, contributor: 0, reader: 0 }
  users.value.forEach(u => counts[u.role]++)
  return counts
})

const uniqueActions = computed(() => {
  const seen = new Set<string>()
  return auditLog.value
    .filter(e => { if (seen.has(e.action)) return false; seen.add(e.action); return true })
    .map(e => ({ action: e.action, label: e.action_display }))
})

const filteredAudit = computed(() =>
  auditFilter.value === 'all'
    ? auditLog.value
    : auditLog.value.filter(e => e.action === auditFilter.value)
)

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function toggleStatus(u: AppUser) {
  u.status = u.status === 'active' ? 'inactive' : 'active'
}

function deleteUser(id: number) {
  users.value = users.value.filter(u => u.id !== id)
  deleteConfirm.value = null
}

function severityIcon(sev: string) {
  if (sev === 'error' || sev === 'critical') return XCircle
  if (sev === 'warning') return AlertTriangle
  if (sev === 'success') return CheckCircle2
  return Info
}

function severityIconClass(sev: string): string {
  if (sev === 'error' || sev === 'critical') return 'ai--error'
  if (sev === 'warning') return 'ai--update'
  if (sev === 'success') return 'ai--create'
  return 'ai--login'
}

function auditBadgeClass(entry: UserActivity): string {
  if (entry.severity === 'error' || entry.severity === 'critical') return 'ab--delete'
  if (entry.severity === 'warning') return 'ab--update'
  if (entry.severity === 'success') return 'ab--create'
  return 'ab--login'
}

async function inviteUser() {
  if (!form.value.name.trim() || !form.value.email.trim()) return
  submitting.value = true
  await new Promise(r => setTimeout(r, 600))
  const parts = form.value.name.trim().split(' ')
  const initials = parts.map(p => p[0]).join('').toUpperCase().slice(0, 2)
  users.value = [{
    id: Date.now(), name: form.value.name, email: form.value.email,
    role: form.value.role, status: 'active',
    last_login: new Date().toISOString(), initials,
  }, ...users.value]
  submitting.value = false
  drawerOpen.value = false
  form.value = { name: '', email: '', role: 'reader' }
}

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await api.get('/api/users/users/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    users.value = rows
  } catch {
    users.value = []
  } finally {
    loading.value = false
  }
}

async function fetchActivities() {
  auditLoading.value = true
  try {
    const { data } = await api.get('/api/users/activities/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    auditLog.value = rows
  } catch {
    auditLog.value = []
  } finally {
    auditLoading.value = false
  }
}

// ── User extra actions ─────────────────────────────────────
const resetPwdLoading = ref<number | null>(null)
const resetPwdSuccess = ref<number | null>(null)
const toggleApiLoading = ref<number | null>(null)

async function resetPassword(user: AppUser) {
  resetPwdLoading.value = user.id
  try {
    await api.post(`/api/users/users/${user.id}/reset_password/`)
    resetPwdSuccess.value = user.id
    setTimeout(() => { resetPwdSuccess.value = null }, 2500)
  } catch {
    // silent fail — could show a toast here
  } finally {
    resetPwdLoading.value = null
  }
}

async function toggleApiAccess(user: AppUser & { api_access_enabled?: boolean }) {
  toggleApiLoading.value = user.id
  try {
    const { data } = await api.post(`/api/users/users/${user.id}/toggle_api_access/`)
    user.api_access_enabled = data?.api_access_enabled ?? !user.api_access_enabled
  } catch {
    // silent fail
  } finally {
    toggleApiLoading.value = null
  }
}

// ── User Stats from API ────────────────────────────────────
const apiUserStats = ref<UserStatsAPI | null>(null)

async function fetchUserStats() {
  try {
    const { data } = await api.get('/api/users/users/stats/')
    apiUserStats.value = data
  } catch {
    apiUserStats.value = null
  }
}

// ── Teams state ────────────────────────────────────────────
const teams            = ref<Team[]>([])
const teamsLoading     = ref(false)
const teamSearchQuery  = ref('')
const teamDrawerOpen   = ref(false)
const editTeam         = ref<Team | null>(null)
const teamDeleteConfirm = ref<string | null>(null)
const teamSubmitting   = ref(false)
const teamForm         = ref({ name: '', description: '', team_lead: '' })
const selectedTeam     = ref<Team | null>(null)
const newMemberUUID    = ref('')
const memberActionLoading = ref(false)
const teamToast        = ref('')

const filteredTeams = computed(() => {
  const q = teamSearchQuery.value.toLowerCase()
  if (!q) return teams.value
  return teams.value.filter(t =>
    t.name.toLowerCase().includes(q) ||
    t.description?.toLowerCase().includes(q) ||
    t.team_lead_name?.toLowerCase().includes(q)
  )
})

function openCreateTeam() {
  editTeam.value = null
  teamForm.value = { name: '', description: '', team_lead: '' }
  teamDrawerOpen.value = true
}

function openEditTeam(team: Team) {
  editTeam.value = team
  teamForm.value = { name: team.name, description: team.description, team_lead: team.team_lead ?? '' }
  teamDrawerOpen.value = true
}

function closeTeamDrawer() {
  teamDrawerOpen.value = false
  editTeam.value = null
}

function showTeamToast(msg: string) {
  teamToast.value = msg
  setTimeout(() => { teamToast.value = '' }, 2500)
}

async function fetchTeams() {
  teamsLoading.value = true
  try {
    const { data } = await api.get('/api/users/teams/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    teams.value = rows
  } catch {
    teams.value = []
  } finally {
    teamsLoading.value = false
  }
}

async function saveTeam() {
  if (!teamForm.value.name.trim()) return
  teamSubmitting.value = true
  try {
    const payload = {
      name: teamForm.value.name,
      description: teamForm.value.description,
      team_lead: teamForm.value.team_lead || null,
    }
    if (editTeam.value) {
      const { data } = await api.patch(`/api/users/teams/${editTeam.value.id}/`, payload)
      const idx = teams.value.findIndex(t => t.id === editTeam.value!.id)
      if (idx !== -1) teams.value[idx] = data
    } else {
      const { data } = await api.post('/api/users/teams/', payload)
      teams.value = [data, ...teams.value]
    }
    closeTeamDrawer()
    showTeamToast(editTeam.value ? 'Équipe mise à jour' : 'Équipe créée')
  } catch {
    // silent
  } finally {
    teamSubmitting.value = false
  }
}

async function deleteTeam(id: string) {
  try {
    await api.delete(`/api/users/teams/${id}/`)
    teams.value = teams.value.filter(t => t.id !== id)
    if (selectedTeam.value?.id === id) selectedTeam.value = null
    teamDeleteConfirm.value = null
    showTeamToast('Équipe supprimée')
  } catch {
    // silent
  }
}

async function addMember() {
  if (!selectedTeam.value || !newMemberUUID.value.trim()) return
  memberActionLoading.value = true
  try {
    const { data } = await api.post(`/api/users/teams/${selectedTeam.value.id}/add_member/`, {
      user_id: newMemberUUID.value.trim(),
    })
    // Refresh the team data
    const idx = teams.value.findIndex(t => t.id === selectedTeam.value!.id)
    if (idx !== -1 && data) {
      teams.value[idx] = data
      selectedTeam.value = data
    } else {
      await fetchTeams()
      selectedTeam.value = teams.value.find(t => t.id === selectedTeam.value!.id) ?? null
    }
    newMemberUUID.value = ''
    showTeamToast('Membre ajouté')
  } catch {
    // silent
  } finally {
    memberActionLoading.value = false
  }
}

async function removeMember(userId: any) {
  if (!selectedTeam.value) return
  memberActionLoading.value = true
  try {
    const memberId = typeof userId === 'object' ? (userId.id ?? userId) : userId
    const { data } = await api.post(`/api/users/teams/${selectedTeam.value.id}/remove_member/`, {
      user_id: memberId,
    })
    const idx = teams.value.findIndex(t => t.id === selectedTeam.value!.id)
    if (idx !== -1 && data) {
      teams.value[idx] = data
      selectedTeam.value = data
    } else {
      await fetchTeams()
      selectedTeam.value = teams.value.find(t => t.id === selectedTeam.value!.id) ?? null
    }
    showTeamToast('Membre retiré')
  } catch {
    // silent
  } finally {
    memberActionLoading.value = false
  }
}

onMounted(() => { fetchUsers(); fetchActivities(); fetchTeams(); fetchUserStats() })
</script>

<template>
  <div class="admin-page">

    <!-- ── Page header ─────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Administration</h2>
        <p class="page-meta">Gestion des utilisateurs, rôles, paramètres et journaux</p>
      </div>
    </header>

    <!-- ── Tab nav ──────────────────────────────────────────── -->
    <nav class="tab-nav" role="tablist" aria-label="Sections d'administration">
      <button
        v-for="tab in TABS"
        :key="tab.id"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === tab.id }"
        role="tab"
        :aria-selected="activeTab === tab.id"
        @click="activeTab = tab.id"
      >
        <component :is="tab.icon" :size="15" />
        {{ tab.label }}
        <span v-if="tab.id === 'users'" class="tab-count">{{ userStats.total }}</span>
      </button>
    </nav>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: USERS                                          -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-if="activeTab === 'users'">

      <!-- Stats strip -->
      <section class="stats-strip">
        <div class="stat-cell">
          <Users :size="14" class="sc-icon" />
          <span class="sc-val">{{ userStats.total }}</span>
          <span class="sc-lbl">Total</span>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-cell">
          <UserCheck :size="14" class="sc-icon sc-icon--ok" />
          <span class="sc-val sc-val--ok">{{ userStats.active }}</span>
          <span class="sc-lbl">Actifs</span>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-cell">
          <UserX :size="14" class="sc-icon sc-icon--off" />
          <span class="sc-val sc-val--off">{{ userStats.inactive }}</span>
          <span class="sc-lbl">Inactifs</span>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-cell">
          <Shield :size="14" class="sc-icon sc-icon--adm" />
          <span class="sc-val sc-val--adm">{{ userStats.admins }}</span>
          <span class="sc-lbl">Admins</span>
        </div>
      </section>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input v-model="searchQuery" type="search" class="search-input" placeholder="Rechercher un utilisateur…" />
        </div>
        <div class="select-wrap">
          <select v-model="filterRole" class="filter-select">
            <option value="all">Tous les rôles</option>
            <option v-for="(m, k) in ROLE_META" :key="k" :value="k">{{ m.label }}</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
        <div class="select-wrap">
          <select v-model="filterStatus" class="filter-select">
            <option value="all">Tous les statuts</option>
            <option value="active">Actif</option>
            <option value="inactive">Inactif</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
        <button class="btn-primary" @click="drawerOpen = true">
          <Plus :size="14" /><span>Inviter</span>
        </button>
      </div>

      <!-- Users table -->
      <div class="panel" v-if="!loading">
        <table class="user-table">
          <thead>
            <tr>
              <th class="uth">Utilisateur</th>
              <th class="uth">Rôle</th>
              <th class="uth uth--center">Statut</th>
              <th class="uth">Dernière connexion</th>
              <th class="uth uth--right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(user, i) in filteredUsers"
              :key="user.id"
              class="user-row"
              :class="{ 'user-row--inactive': user.status === 'inactive' }"
              :style="{ '--ri': i }"
            >
              <!-- Avatar + name + email -->
              <td class="utd">
                <div class="user-ident">
                  <div
                    class="avatar"
                    :style="{ '--ac': ROLE_META[user.role].color }"
                  >{{ user.initials }}</div>
                  <div class="user-info">
                    <span class="user-name">{{ user.name }}</span>
                    <span class="user-email">{{ user.email }}</span>
                  </div>
                </div>
              </td>

              <!-- Role -->
              <td class="utd">
                <span class="role-badge" :style="{ '--rc': ROLE_META[user.role].color }">
                  {{ ROLE_META[user.role].label }}
                </span>
              </td>

              <!-- Status -->
              <td class="utd utd--center">
                <span class="status-dot-wrap" :class="user.status === 'active' ? 'sdw--active' : 'sdw--off'">
                  <span class="status-dot"></span>
                  {{ user.status === 'active' ? 'Actif' : 'Inactif' }}
                </span>
              </td>

              <!-- Last login -->
              <td class="utd">
                <span class="last-login">{{ timeAgo(user.last_login) }}</span>
              </td>

              <!-- Actions -->
              <td class="utd utd--right">
                <div class="row-actions">
                  <button class="act-btn" title="Modifier"><Pencil :size="13" /></button>
                  <button
                    class="act-btn"
                    :title="user.status === 'active' ? 'Désactiver' : 'Activer'"
                    @click="toggleStatus(user)"
                  >
                    <component :is="user.status === 'active' ? UserX : UserCheck" :size="13" />
                  </button>
                  <!-- Reset password -->
                  <button
                    class="act-btn"
                    :class="{ 'act-btn--success': resetPwdSuccess === user.id }"
                    :title="resetPwdSuccess === user.id ? 'Email envoyé !' : 'Réinitialiser MDP'"
                    :disabled="resetPwdLoading === user.id"
                    @click="resetPassword(user)"
                  >
                    <span v-if="resetPwdLoading === user.id" class="spinner spinner--sm" aria-label="…"></span>
                    <CheckCircle2 v-else-if="resetPwdSuccess === user.id" :size="13" />
                    <Key v-else :size="13" />
                  </button>
                  <!-- Toggle API access -->
                  <button
                    class="act-btn"
                    :class="{ 'act-btn--api-on': (user as any).api_access_enabled }"
                    :title="(user as any).api_access_enabled ? 'Désactiver accès API' : 'Activer accès API'"
                    :disabled="toggleApiLoading === user.id"
                    @click="toggleApiAccess(user as any)"
                  >
                    <span v-if="toggleApiLoading === user.id" class="spinner spinner--sm" aria-label="…"></span>
                    <Plug v-else :size="13" />
                  </button>
                  <template v-if="deleteConfirm === user.id">
                    <span class="del-label">Supprimer ?</span>
                    <button class="act-btn act-btn--yes" @click="deleteUser(user.id)">Oui</button>
                    <button class="act-btn" @click="deleteConfirm = null">Non</button>
                  </template>
                  <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = user.id">
                    <Trash2 :size="13" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="5" class="empty-row">Aucun utilisateur trouvé.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div v-else class="panel">
        <div v-for="i in 5" :key="i" class="user-skel"></div>
      </div>

    </template>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: ROLES                                          -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-else-if="activeTab === 'roles'">

      <!-- Role cards -->
      <div class="roles-grid">
        <div
          v-for="(meta, key) in ROLE_META"
          :key="key"
          class="role-card"
          :style="{ '--rc': meta.color }"
        >
          <div class="role-card-hd">
            <div class="role-icon-wrap">
              <Shield :size="20" />
            </div>
            <div>
              <h3 class="role-name">{{ meta.label }}</h3>
              <span class="role-users">{{ roleUserCounts[key as UserRole] }} utilisateur{{ roleUserCounts[key as UserRole] !== 1 ? 's' : '' }}</span>
            </div>
          </div>
          <p class="role-desc">{{ meta.desc }}</p>
        </div>
      </div>

      <!-- Permissions matrix -->
      <div class="panel">
        <div class="panel-hd">
          <span class="panel-title">Matrice des permissions</span>
        </div>
        <div class="perm-table-wrap">
          <table class="perm-table">
            <thead>
              <tr>
                <th class="pth pth--perm">Permission</th>
                <th
                  v-for="(m, k) in ROLE_META"
                  :key="k"
                  class="pth pth--role"
                  :style="{ '--rc': m.color }"
                >
                  {{ m.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="perm in PERMISSIONS" :key="perm.key" class="perm-row">
                <td class="ptd ptd--perm">{{ perm.label }}</td>
                <td v-for="role in (['admin','analyst','contributor','reader'] as UserRole[])" :key="role" class="ptd ptd--check">
                  <Check v-if="perm[role]" :size="14" class="perm-yes" />
                  <span v-else class="perm-no">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: TEAMS                                          -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-else-if="activeTab === 'teams'">

      <!-- Toast -->
      <Transition name="fade">
        <div v-if="teamToast" class="team-toast">
          <CheckCircle2 :size="14" />
          {{ teamToast }}
        </div>
      </Transition>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input v-model="teamSearchQuery" type="search" class="search-input" placeholder="Rechercher une équipe…" />
        </div>
        <button class="btn-primary" @click="openCreateTeam">
          <Plus :size="14" /><span>Nouvelle équipe</span>
        </button>
      </div>

      <!-- Teams table -->
      <div class="panel" v-if="!teamsLoading">
        <table class="user-table">
          <thead>
            <tr>
              <th class="uth">Nom</th>
              <th class="uth">Description</th>
              <th class="uth">Chef d'équipe</th>
              <th class="uth uth--center">Membres</th>
              <th class="uth uth--right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(team, i) in filteredTeams"
              :key="team.id"
              class="user-row"
              :class="{ 'team-row--selected': selectedTeam?.id === team.id }"
              :style="{ '--ri': i }"
              @click="selectedTeam = selectedTeam?.id === team.id ? null : team"
            >
              <td class="utd">
                <div class="team-name-cell">
                  <div class="team-avatar">
                    <Users2 :size="14" />
                  </div>
                  <span class="user-name">{{ team.name }}</span>
                </div>
              </td>
              <td class="utd">
                <span class="team-desc-text">{{ team.description || '—' }}</span>
              </td>
              <td class="utd">
                <span class="user-email">{{ team.team_lead_name || (team.team_lead ? team.team_lead : '—') }}</span>
              </td>
              <td class="utd utd--center">
                <span class="member-count-badge">{{ team.member_count ?? team.members?.length ?? 0 }}</span>
              </td>
              <td class="utd utd--right" @click.stop>
                <div class="row-actions">
                  <button class="act-btn" title="Modifier" @click="openEditTeam(team)">
                    <Pencil :size="13" />
                  </button>
                  <template v-if="teamDeleteConfirm === team.id">
                    <span class="del-label">Supprimer ?</span>
                    <button class="act-btn act-btn--yes" @click="deleteTeam(team.id)">Oui</button>
                    <button class="act-btn" @click="teamDeleteConfirm = null">Non</button>
                  </template>
                  <button v-else class="act-btn act-btn--del" title="Supprimer" @click="teamDeleteConfirm = team.id">
                    <Trash2 :size="13" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredTeams.length === 0">
              <td colspan="5" class="empty-row">Aucune équipe trouvée.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading skeleton -->
      <div v-else class="panel">
        <div v-for="i in 4" :key="i" class="user-skel"></div>
      </div>

      <!-- Member management sub-panel -->
      <Transition name="fade">
        <div v-if="selectedTeam" class="team-members-panel">
          <div class="panel-hd team-members-hd">
            <div class="team-members-title-row">
              <Users2 :size="15" class="sp-icon" />
              <span class="panel-title">Membres de « {{ selectedTeam.name }} »</span>
            </div>
            <button class="drawer-close" @click="selectedTeam = null" aria-label="Fermer">
              <X :size="16" />
            </button>
          </div>

          <div class="team-members-body">
            <!-- Current members list -->
            <div v-if="selectedTeam.members && selectedTeam.members.length > 0" class="members-list">
              <div
                v-for="member in selectedTeam.members"
                :key="typeof member === 'object' ? member.id : member"
                class="member-row"
              >
                <div class="member-avatar">
                  {{ typeof member === 'object' ? (member.initials || (member.name || member.email || '?')[0].toUpperCase()) : '?' }}
                </div>
                <div class="member-info">
                  <span class="member-name">{{ typeof member === 'object' ? (member.name || member.username || 'Utilisateur') : member }}</span>
                  <span class="member-email">{{ typeof member === 'object' ? member.email || '' : '' }}</span>
                </div>
                <button
                  class="act-btn act-btn--del"
                  title="Retirer du groupe"
                  :disabled="memberActionLoading"
                  @click="removeMember(member)"
                >
                  <X :size="13" />
                </button>
              </div>
            </div>
            <div v-else class="members-empty">
              <Users :size="20" />
              <span>Aucun membre dans cette équipe.</span>
            </div>

            <!-- Add member -->
            <div class="add-member-row">
              <input
                v-model="newMemberUUID"
                class="form-input add-member-input"
                type="text"
                placeholder="UUID de l'utilisateur à ajouter…"
                @keydown.enter.prevent="addMember"
              />
              <button
                class="btn-primary"
                :disabled="memberActionLoading || !newMemberUUID.trim()"
                @click="addMember"
              >
                <span v-if="memberActionLoading" class="spinner" aria-label="…"></span>
                <template v-else><Plus :size="14" /><span>Ajouter membre</span></template>
              </button>
            </div>
          </div>
        </div>
      </Transition>

    </template>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: SETTINGS                                       -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-else-if="activeTab === 'settings'">

      <div class="settings-grid">

        <!-- General -->
        <section class="settings-panel">
          <div class="sp-hd">
            <Globe :size="16" class="sp-icon" />
            <span class="sp-title">Général</span>
          </div>
          <div class="sp-body">
            <div class="sf">
              <label class="sf-label">Nom de la plateforme</label>
              <input v-model="settings.platformName" class="sf-input" type="text" />
            </div>
            <div class="sf-row">
              <div class="sf">
                <label class="sf-label">Langue</label>
                <div class="select-wrap">
                  <select v-model="settings.language" class="sf-select">
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                    <option value="ar">العربية</option>
                  </select>
                  <ChevronDown :size="12" class="select-arrow" />
                </div>
              </div>
              <div class="sf">
                <label class="sf-label">Fuseau horaire</label>
                <div class="select-wrap">
                  <select v-model="settings.timezone" class="sf-select">
                    <option value="Africa/Algiers">Africa/Algiers (UTC+1)</option>
                    <option value="Europe/Paris">Europe/Paris (UTC+2)</option>
                    <option value="UTC">UTC</option>
                  </select>
                  <ChevronDown :size="12" class="select-arrow" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Data -->
        <section class="settings-panel">
          <div class="sp-hd">
            <Database :size="16" class="sp-icon" />
            <span class="sp-title">Données</span>
          </div>
          <div class="sp-body">
            <div class="sf-row">
              <div class="sf">
                <label class="sf-label">Rétention des données (jours)</label>
                <input v-model.number="settings.dataRetention" class="sf-input" type="number" min="30" max="3650" />
              </div>
              <div class="sf">
                <label class="sf-label">Connexions simultanées max</label>
                <input v-model.number="settings.maxConnections" class="sf-input" type="number" min="1" max="500" />
              </div>
            </div>
            <div class="sf">
              <label class="sf-label">Intervalle de rafraîchissement (min)</label>
              <input v-model.number="settings.refreshInterval" class="sf-input" type="number" min="1" max="1440" />
              <span class="sf-hint">Fréquence de mise à jour automatique des tableaux de bord</span>
            </div>
          </div>
        </section>

        <!-- Security -->
        <section class="settings-panel">
          <div class="sp-hd">
            <Lock :size="16" class="sp-icon" />
            <span class="sp-title">Sécurité</span>
          </div>
          <div class="sp-body">
            <div class="sf">
              <label class="sf-label">Timeout de session (minutes)</label>
              <input v-model.number="settings.sessionTimeout" class="sf-input" type="number" min="5" max="480" />
            </div>
            <div class="sf">
              <label class="sf-label">Complexité du mot de passe</label>
              <div class="select-wrap">
                <select v-model="settings.passwordStrength" class="sf-select">
                  <option value="basic">Basique (8+ caractères)</option>
                  <option value="medium">Moyen (8+ car. + chiffre)</option>
                  <option value="strong">Fort (12+ car. + spec. + chiffre)</option>
                </select>
                <ChevronDown :size="12" class="select-arrow" />
              </div>
            </div>
            <div class="sf-toggle">
              <div class="sf-toggle-info">
                <span class="sf-label">Authentification à deux facteurs</span>
                <span class="sf-hint">Rendre le 2FA obligatoire pour tous les utilisateurs</span>
              </div>
              <button
                class="toggle-btn"
                :class="{ 'toggle-btn--on': settings.require2fa }"
                role="switch"
                :aria-checked="settings.require2fa"
                @click="settings.require2fa = !settings.require2fa"
              >
                <span class="toggle-thumb"></span>
              </button>
            </div>
          </div>
        </section>

        <!-- Notifications -->
        <section class="settings-panel">
          <div class="sp-hd">
            <Bell :size="16" class="sp-icon" />
            <span class="sp-title">Notifications</span>
          </div>
          <div class="sp-body">
            <div class="sf-toggle">
              <div class="sf-toggle-info">
                <span class="sf-label">Alertes par email</span>
                <span class="sf-hint">Envoyer des notifications par email</span>
              </div>
              <button
                class="toggle-btn"
                :class="{ 'toggle-btn--on': settings.emailAlerts }"
                role="switch"
                :aria-checked="settings.emailAlerts"
                @click="settings.emailAlerts = !settings.emailAlerts"
              >
                <span class="toggle-thumb"></span>
              </button>
            </div>
            <div v-if="settings.emailAlerts" class="sf-row">
              <div class="sf">
                <label class="sf-label">Serveur SMTP</label>
                <input v-model="settings.smtpHost" class="sf-input" type="text" />
              </div>
              <div class="sf sf--sm">
                <label class="sf-label">Port</label>
                <input v-model="settings.smtpPort" class="sf-input" type="text" />
              </div>
            </div>
            <div class="sf">
              <label class="sf-label">Seuil d'alerte KPI (%)</label>
              <input v-model.number="settings.kpiAlertPct" class="sf-input" type="number" min="1" max="100" />
              <span class="sf-hint">Alerte quand un KPI s'écarte de l'objectif de plus de ce pourcentage</span>
            </div>
          </div>
        </section>

      </div>

      <!-- Save bar -->
      <div class="save-bar">
        <Transition name="fade">
          <div v-if="settingsSaved" class="save-confirm">
            <CheckCircle2 :size="15" />
            Paramètres enregistrés
          </div>
        </Transition>
        <button
          class="btn-primary"
          :disabled="settingsSaving"
          @click="saveSettings"
        >
          <span v-if="settingsSaving" class="spinner" aria-label="Enregistrement…"></span>
          <span v-else>Enregistrer</span>
        </button>
      </div>

    </template>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: AUDIT LOG                                      -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-else-if="activeTab === 'audit'">

      <div class="toolbar">
        <div class="select-wrap">
          <select v-model="auditFilter" class="filter-select">
            <option value="all">Toutes les actions</option>
            <option v-for="a in uniqueActions" :key="a.action" :value="a.action">{{ a.label }}</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
        <span class="audit-count">{{ filteredAudit.length }} entrée{{ filteredAudit.length !== 1 ? 's' : '' }}</span>
      </div>

      <div v-if="auditLoading" class="audit-timeline">
        <div v-for="i in 6" :key="i" class="user-skel"></div>
      </div>

      <div v-else class="audit-timeline">
        <div
          v-for="(entry, i) in filteredAudit"
          :key="entry.id"
          class="audit-entry"
          :style="{ '--ai': i }"
        >
          <div class="audit-icon-col">
            <div class="audit-icon" :class="severityIconClass(entry.severity)">
              <component :is="severityIcon(entry.severity)" :size="13" />
            </div>
            <div v-if="i < filteredAudit.length - 1" class="audit-line"></div>
          </div>
          <div class="audit-body">
            <div class="audit-top">
              <span class="audit-user">{{ entry.user_name }}</span>
              <span class="audit-action-badge" :class="auditBadgeClass(entry)">{{ entry.action_display }}</span>
              <span v-if="entry.resource_type" class="audit-entity-type">{{ entry.resource_type }}</span>
              <span v-if="entry.resource_name" class="audit-entity">« {{ entry.resource_name }} »</span>
            </div>
            <p class="audit-details">{{ entry.description }}</p>
            <span class="audit-time">{{ entry.time_ago }}</span>
          </div>
        </div>
        <div v-if="filteredAudit.length === 0" class="audit-empty">
          <Info :size="24" />
          <span>Aucune entrée pour ce filtre.</span>
        </div>
      </div>

    </template>

    <!-- ── Team create/edit drawer ──────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="teamDrawerOpen" class="drawer-overlay" @click.self="closeTeamDrawer">
        <aside class="drawer" role="dialog" aria-modal="true" :aria-label="editTeam ? 'Modifier l\'équipe' : 'Nouvelle équipe'">

          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editTeam ? 'Modifier l\'équipe' : 'Nouvelle équipe' }}</h3>
            <button class="drawer-close" @click="closeTeamDrawer" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="saveTeam">

            <div class="form-field">
              <label class="form-label" for="tf-name">Nom <span class="req">*</span></label>
              <input id="tf-name" v-model="teamForm.name" class="form-input" type="text" placeholder="Nom de l'équipe" required />
            </div>

            <div class="form-field">
              <label class="form-label" for="tf-desc">Description</label>
              <textarea
                id="tf-desc"
                v-model="teamForm.description"
                class="form-input form-textarea"
                placeholder="Description de l'équipe…"
                rows="3"
              ></textarea>
            </div>

            <div class="form-field">
              <label class="form-label" for="tf-lead">UUID Chef d'équipe</label>
              <input id="tf-lead" v-model="teamForm.team_lead" class="form-input" type="text" placeholder="UUID de l'utilisateur chef d'équipe" />
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="closeTeamDrawer">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="teamSubmitting" :class="{ 'btn-primary--loading': teamSubmitting }">
                <span v-if="!teamSubmitting">{{ editTeam ? 'Enregistrer' : 'Créer l\'équipe' }}</span>
                <span v-else class="spinner" aria-label="Enregistrement…"></span>
              </button>
            </div>

          </form>
        </aside>
      </div>
    </Transition>

    <!-- ── Invite user drawer ────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Inviter un utilisateur">

          <div class="drawer-hd">
            <h3 class="drawer-title">Inviter un utilisateur</h3>
            <button class="drawer-close" @click="drawerOpen = false" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="inviteUser">

            <div class="form-field">
              <label class="form-label" for="f-name">Nom complet <span class="req">*</span></label>
              <input id="f-name" v-model="form.name" class="form-input" type="text" placeholder="Prénom Nom" required />
            </div>

            <div class="form-field">
              <label class="form-label" for="f-email">
                <Mail :size="13" class="lbl-icon" />
                Adresse email <span class="req">*</span>
              </label>
              <input id="f-email" v-model="form.email" class="form-input" type="email" placeholder="prenom.nom@sotifibre.com" required />
            </div>

            <div class="form-field">
              <label class="form-label">Rôle</label>
              <div class="role-grid">
                <button
                  v-for="(meta, key) in ROLE_META"
                  :key="key"
                  type="button"
                  class="role-opt"
                  :class="{ 'role-opt--active': form.role === key }"
                  :style="{ '--rc': meta.color }"
                  @click="form.role = key as UserRole"
                >
                  <Shield :size="14" class="role-opt-icon" />
                  <span class="role-opt-name">{{ meta.label }}</span>
                  <span class="role-opt-desc">{{ meta.desc }}</span>
                </button>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting" :class="{ 'btn-primary--loading': submitting }">
                <span v-if="!submitting">Envoyer l'invitation</span>
                <span v-else class="spinner" aria-label="Envoi…"></span>
              </button>
            </div>

          </form>
        </aside>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* ── Page ────────────────────────────────────────────────── */
.admin-page {
  padding: var(--sp-8);
  display: flex; flex-direction: column;
  gap: var(--sp-6); min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd { flex-shrink: 0; }

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl); font-weight: 700;
  letter-spacing: -0.01em; color: var(--text-primary); line-height: 1.2;
}

.page-meta { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }

/* ── Tab nav ─────────────────────────────────────────────── */
.tab-nav {
  display: flex; gap: 2px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0;
  flex-shrink: 0;
}

.tab-btn {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: none; border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  color: var(--text-muted);
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  cursor: pointer; white-space: nowrap;
  transition: color 150ms, border-color 150ms;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}
.tab-btn:hover { color: var(--text-secondary); background: var(--surface-overlay); }
.tab-btn--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: none;
}

.tab-count {
  font-size: 0.65rem; font-weight: 700;
  padding: 1px 6px;
  background: var(--surface-muted);
  border-radius: var(--radius-full);
  color: var(--text-muted);
}
.tab-btn--active .tab-count { background: var(--accent-surface); color: var(--accent-dim); }

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent); color: var(--text-on-accent);
  border: none; border-radius: var(--radius-md);
  cursor: pointer; font-family: var(--font-ui);
  font-size: var(--text-sm); font-weight: 600;
  min-height: 38px; white-space: nowrap;
  transition: background 150ms, box-shadow 150ms;
}
.btn-primary:hover:not(:disabled) {
  background: oklch(80% 0.14 62);
  box-shadow: 0 4px 16px oklch(76% 0.14 62 / 0.28);
}
.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }
.btn-primary--loading { min-width: 120px; justify-content: center; }

.btn-ghost {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-secondary); min-height: 38px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover { border-color: var(--border-strong); color: var(--text-primary); }

/* ── Panel ───────────────────────────────────────────────── */
.panel {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.panel-hd {
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase;
  color: var(--text-muted);
}

/* ── Stats strip ─────────────────────────────────────────── */
.stats-strip {
  display: flex; align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); overflow: hidden;
}
.stat-cell { flex: 1; display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-4) var(--sp-6); }
.stat-sep  { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.sc-icon     { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--ok { color: oklch(65% 0.13 148); }
.sc-icon--off{ color: var(--text-muted); }
.sc-icon--adm{ color: var(--accent-dim); }
.sc-val     { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.sc-val--ok { color: oklch(65% 0.13 148); }
.sc-val--off{ color: var(--text-muted); }
.sc-val--adm{ color: var(--accent-dim); }
.sc-lbl     { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; max-width: 360px; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input {
  width: 100%; height: 38px; padding: 0 var(--sp-4) 0 34px;
  background: var(--surface-raised); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }
.filter-select {
  appearance: none; height: 38px; padding: 0 30px 0 var(--sp-3);
  background: var(--surface-raised); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-secondary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none; cursor: pointer;
  transition: border-color 150ms;
}
.filter-select:focus { border-color: var(--accent-dim); }
.filter-select option { background: var(--surface-raised); }
.select-arrow { position: absolute; right: 9px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }

/* ── User table ──────────────────────────────────────────── */
.user-table {
  width: 100%; border-collapse: collapse; font-size: var(--text-sm);
}

.uth {
  padding: var(--sp-2) var(--sp-5);
  font-family: var(--font-display);
  font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase;
  color: var(--text-muted); text-align: left;
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
  position: sticky; top: 0; z-index: 1;
}
.uth--center { text-align: center; }
.uth--right  { text-align: right; }

.user-row {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;

  opacity: 0; transform: translateY(4px);
  animation: row-in 260ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--ri, 0) * 30ms);
}
@keyframes row-in { to { opacity: 1; transform: translateY(0); } }
.user-row:last-child { border-bottom: none; }
.user-row:hover { background: var(--surface-overlay); }
.user-row--inactive { opacity: 0.6; }

.utd { padding: var(--sp-3) var(--sp-5); vertical-align: middle; }
.utd--center { text-align: center; }
.utd--right  { text-align: right; }

/* Avatar */
.user-ident { display: flex; align-items: center; gap: var(--sp-3); }
.avatar {
  width: 36px; height: 36px; border-radius: var(--radius-md); flex-shrink: 0;
  background: color-mix(in oklch, var(--ac) 18%, oklch(10% 0.013 258));
  color: var(--ac);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 0.78rem; font-weight: 800;
}
.user-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.user-name  { font-weight: 600; color: var(--text-primary); white-space: nowrap; }
.user-email { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Role badge */
.role-badge {
  display: inline-flex; align-items: center;
  padding: 3px 9px;
  background: color-mix(in oklch, var(--rc) 13%, oklch(10% 0.013 258));
  color: var(--rc);
  border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em;
  text-transform: uppercase; white-space: nowrap;
}

/* Status dot */
.status-dot-wrap {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: var(--text-xs); font-weight: 600;
}
.status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.sdw--active .status-dot { background: oklch(65% 0.13 148); }
.sdw--active { color: oklch(65% 0.13 148); }
.sdw--off .status-dot    { background: var(--text-muted); }
.sdw--off    { color: var(--text-muted); }

.last-login { font-size: var(--text-xs); color: var(--text-muted); }

/* Row actions */
.row-actions { display: flex; align-items: center; gap: var(--sp-1); justify-content: flex-end; }
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none; color: var(--text-muted);
  cursor: pointer; font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) { background: var(--surface-overlay); border-color: var(--border-default); color: var(--text-secondary); }
.act-btn--del:hover:not(:disabled) { background: var(--error-surface); border-color: var(--error); color: var(--error); }
.act-btn--yes { background: var(--error-surface); border-color: var(--error); color: var(--error); width: auto; padding: 0 var(--sp-2); }
.del-label { font-size: var(--text-xs); color: var(--error); white-space: nowrap; }

/* Skeleton */
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.user-skel {
  height: 60px; margin: var(--sp-1) var(--sp-5);
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%; animation: shimmer 1.4s infinite;
}

.empty-row { text-align: center; padding: var(--sp-12); color: var(--text-muted); font-size: var(--text-sm); }

/* ── Roles tab ───────────────────────────────────────────── */
.roles-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--sp-4);
}

.role-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-top: 3px solid var(--rc);
  border-radius: var(--radius-lg);
  padding: var(--sp-5);
  display: flex; flex-direction: column; gap: var(--sp-3);
  transition: box-shadow 200ms;
}
.role-card:hover { box-shadow: 0 6px 20px oklch(5% 0.01 258 / 0.3); }

.role-card-hd { display: flex; align-items: flex-start; gap: var(--sp-3); }
.role-icon-wrap {
  width: 38px; height: 38px; border-radius: var(--radius-md); flex-shrink: 0;
  background: color-mix(in oklch, var(--rc) 14%, oklch(10% 0.013 258));
  color: var(--rc);
  display: flex; align-items: center; justify-content: center;
}
.role-name  { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-primary); }
.role-users { font-size: var(--text-xs); color: var(--text-muted); }
.role-desc  { font-size: var(--text-xs); color: var(--text-secondary); line-height: 1.55; }

/* Permissions matrix */
.perm-table-wrap { overflow-x: auto; }
.perm-table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }

.pth {
  padding: var(--sp-2) var(--sp-4);
  font-family: var(--font-display); font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase;
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}
.pth--perm { text-align: left; color: var(--text-muted); }
.pth--role { text-align: center; color: var(--rc); }

.perm-row { border-bottom: 1px solid var(--border-subtle); transition: background 100ms; }
.perm-row:last-child { border-bottom: none; }
.perm-row:hover { background: var(--surface-overlay); }

.ptd { padding: var(--sp-2) var(--sp-4); }
.ptd--perm { color: var(--text-secondary); }
.ptd--check { text-align: center; }

.perm-yes { color: oklch(65% 0.13 148); display: inline-block; }
.perm-no  { color: var(--border-strong); }

/* ── Settings tab ────────────────────────────────────────── */
.settings-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--sp-5);
}

.settings-panel {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.sp-hd {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-overlay);
}
.sp-icon  { color: var(--accent-dim); flex-shrink: 0; }
.sp-title { font-family: var(--font-display); font-size: var(--text-sm); font-weight: 700; letter-spacing: 0.03em; color: var(--text-primary); }

.sp-body { padding: var(--sp-5); display: flex; flex-direction: column; gap: var(--sp-4); }

.sf { display: flex; flex-direction: column; gap: var(--sp-1); }
.sf-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); align-items: end; }
.sf--sm { flex: 0 0 80px; }

.sf-label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.sf-hint  { font-size: var(--text-xs); color: var(--text-muted); line-height: 1.4; }

.sf-input {
  height: 38px; padding: 0 var(--sp-3);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default); border-radius: var(--radius-md);
  color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.sf-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }

.sf-select {
  appearance: none; width: 100%; height: 38px; padding: 0 30px 0 var(--sp-3);
  background: var(--surface-overlay); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none; cursor: pointer;
  transition: border-color 150ms;
}
.sf-select:focus { border-color: var(--accent-dim); }
.sf-select option { background: var(--surface-raised); }

.sf-toggle { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
.sf-toggle-info { display: flex; flex-direction: column; gap: 2px; }

/* Toggle switch */
.toggle-btn {
  width: 42px; height: 24px; border-radius: 12px; flex-shrink: 0;
  background: var(--border-strong); border: none; cursor: pointer;
  position: relative; transition: background 200ms;
}
.toggle-btn--on { background: var(--accent); }
.toggle-thumb {
  position: absolute; top: 3px; left: 3px;
  width: 18px; height: 18px; border-radius: 50%;
  background: white;
  transition: transform 200ms var(--ease-out-expo);
  box-shadow: 0 1px 3px oklch(0% 0 0 / 0.3);
}
.toggle-btn--on .toggle-thumb { transform: translateX(18px); }

/* Save bar */
.save-bar {
  display: flex; align-items: center; justify-content: flex-end;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.save-confirm {
  display: flex; align-items: center; gap: var(--sp-2);
  font-size: var(--text-sm); font-weight: 600;
  color: oklch(65% 0.13 148);
}

/* ── Audit timeline ──────────────────────────────────────── */
.audit-count { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

.audit-timeline {
  display: flex; flex-direction: column;
  gap: 0;
}

.audit-entry {
  display: flex; gap: var(--sp-4);
  opacity: 0; transform: translateX(-6px);
  animation: audit-in 260ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--ai, 0) * 35ms);
}

@keyframes audit-in { to { opacity: 1; transform: translateX(0); } }

.audit-icon-col {
  display: flex; flex-direction: column; align-items: center;
  flex-shrink: 0; width: 28px;
}

.audit-icon {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  z-index: 1;
}
.ai--create  { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.ai--update  { background: var(--accent-surface); color: var(--accent-dim); }
.ai--delete  { background: var(--error-surface); color: var(--error); }
.ai--error   { background: var(--error-surface); color: var(--error); }
.ai--login   { background: oklch(14% 0.04 258); color: oklch(62% 0.12 258); }
.ai--publish { background: oklch(15% 0.05 148); color: oklch(65% 0.13 148); }

.audit-line {
  width: 1px; flex: 1; background: var(--border-subtle);
  margin: var(--sp-1) 0;
}

.audit-body {
  padding-bottom: var(--sp-5);
  flex: 1; min-width: 0;
}

.audit-top {
  display: flex; align-items: center; gap: var(--sp-2);
  flex-wrap: wrap; margin-bottom: 4px;
}

.audit-user { font-weight: 600; color: var(--text-primary); font-size: var(--text-sm); }

.audit-action-badge {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  padding: 1px 6px; border-radius: var(--radius-full);
}
.ab--create  { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.ab--update  { background: var(--accent-surface); color: var(--accent-dim); }
.ab--delete  { background: var(--error-surface); color: var(--error); }
.ab--error   { background: var(--error-surface); color: var(--error); }
.ab--login   { background: oklch(14% 0.04 258); color: oklch(62% 0.12 258); }
.ab--publish { background: oklch(15% 0.05 148); color: oklch(65% 0.13 148); }

.audit-entity-type { font-size: var(--text-xs); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.audit-entity { font-size: var(--text-sm); color: var(--text-secondary); font-style: italic; }

.audit-details { font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 4px; }
.audit-time    { font-size: var(--text-xs); color: var(--text-muted); }

.audit-empty {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-12); color: var(--text-muted);
  font-size: var(--text-sm); justify-content: center;
}

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed; inset: 0;
  background: oklch(5% 0.01 258 / 0.72);
  z-index: var(--z-modal); display: flex; justify-content: flex-end;
}
.drawer {
  width: 460px; max-width: 100vw; height: 100dvh;
  background: var(--surface-raised);
  border-left: 1px solid var(--border-default);
  display: flex; flex-direction: column; overflow-y: auto;
}
.drawer-hd {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--sp-6); border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0; position: sticky; top: 0;
  background: var(--surface-raised); z-index: 1;
}
.drawer-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); }
.drawer-close {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-default); background: none;
  color: var(--text-secondary); cursor: pointer; transition: all 150ms;
}
.drawer-close:hover { border-color: var(--border-strong); color: var(--text-primary); }

.drawer-form { display: flex; flex-direction: column; gap: var(--sp-5); padding: var(--sp-6); flex: 1; }
.form-field  { display: flex; flex-direction: column; gap: var(--sp-2); }
.form-label  { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); display: flex; align-items: center; gap: 5px; }
.lbl-icon    { color: var(--text-muted); flex-shrink: 0; }
.req { color: var(--accent-dim); margin-left: 2px; }

.form-input {
  height: 40px; padding: 0 var(--sp-4);
  background: var(--surface-overlay); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.form-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }
.form-input::placeholder { color: var(--text-muted); }

/* Role picker in drawer */
.role-grid { display: flex; flex-direction: column; gap: var(--sp-2); }
.role-opt {
  display: flex; align-items: flex-start; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border: 1px solid var(--border-default); border-radius: var(--radius-md);
  background: none; cursor: pointer; text-align: left;
  transition: all 150ms;
}
.role-opt:hover { border-color: var(--border-strong); background: var(--surface-overlay); }
.role-opt--active {
  border-color: var(--rc);
  background: color-mix(in oklch, var(--rc) 10%, oklch(10% 0.013 258));
}
.role-opt-icon { color: var(--rc); flex-shrink: 0; margin-top: 2px; }
.role-opt-name { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); display: block; }
.role-opt--active .role-opt-name { color: var(--rc); }
.role-opt-desc { font-size: var(--text-xs); color: var(--text-muted); line-height: 1.4; display: block; margin-top: 2px; }

.drawer-footer {
  display: flex; gap: var(--sp-3); justify-content: flex-end;
  padding-top: var(--sp-4); margin-top: auto;
  border-top: 1px solid var(--border-subtle); flex-shrink: 0;
}

@keyframes spin-sm { to { transform: rotate(360deg); } }
.spinner {
  display: block; width: 16px; height: 16px;
  border: 2px solid oklch(14% 0.013 258 / 0.3);
  border-top-color: var(--text-on-accent);
  border-radius: 50%; animation: spin-sm 0.7s linear infinite;
}

/* Drawer transition */
.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from, .drawer-anim-leave-to { opacity: 0; }
.drawer-anim-enter-active .drawer { transition: transform 380ms var(--ease-out-expo); }
.drawer-anim-leave-active .drawer { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer, .drawer-anim-leave-to .drawer { transform: translateX(100%); }

/* Fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 250ms ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── User extra action states ────────────────────────────── */
.act-btn--success { color: oklch(65% 0.13 148) !important; border-color: oklch(65% 0.13 148) !important; }
.act-btn--api-on  { color: var(--accent-dim) !important; border-color: var(--accent-dim) !important; }
.act-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.spinner--sm {
  display: inline-block; width: 11px; height: 11px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--text-secondary);
  border-radius: 50%; animation: spin-sm 0.7s linear infinite;
}

/* ── Teams tab ───────────────────────────────────────────── */
.team-toast {
  display: inline-flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: oklch(14% 0.04 148);
  color: oklch(65% 0.13 148);
  border: 1px solid oklch(65% 0.13 148 / 0.3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm); font-weight: 600;
  align-self: flex-start;
}

.team-name-cell {
  display: flex; align-items: center; gap: var(--sp-3);
}

.team-avatar {
  width: 32px; height: 32px; border-radius: var(--radius-md); flex-shrink: 0;
  background: var(--accent-surface);
  color: var(--accent-dim);
  display: flex; align-items: center; justify-content: center;
}

.team-desc-text {
  font-size: var(--text-xs); color: var(--text-muted);
  max-width: 240px; display: block;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.member-count-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 24px; height: 20px; padding: 0 6px;
  background: var(--surface-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 700; color: var(--text-muted);
}

.team-row--selected { background: var(--accent-surface) !important; }

.team-members-panel {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.team-members-hd {
  display: flex; align-items: center; justify-content: space-between;
  gap: var(--sp-3);
}

.team-members-title-row {
  display: flex; align-items: center; gap: var(--sp-2);
}

.team-members-body {
  padding: var(--sp-5);
  display: flex; flex-direction: column; gap: var(--sp-4);
}

.members-list {
  display: flex; flex-direction: column; gap: var(--sp-2);
}

.member-row {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-overlay);
  transition: background 100ms;
}
.member-row:hover { background: var(--surface-raised); }

.member-avatar {
  width: 30px; height: 30px; border-radius: var(--radius-sm); flex-shrink: 0;
  background: var(--accent-surface); color: var(--accent-dim);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 0.72rem; font-weight: 800;
}

.member-info { flex: 1; display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.member-name { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); white-space: nowrap; }
.member-email { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.members-empty {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-6); color: var(--text-muted);
  font-size: var(--text-sm); justify-content: center;
}

.add-member-row {
  display: flex; gap: var(--sp-3); align-items: center;
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border-subtle);
}

.add-member-input { flex: 1; }

.form-textarea {
  height: auto !important; padding: var(--sp-3) var(--sp-4) !important;
  resize: vertical;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1200px) {
  .roles-grid { grid-template-columns: repeat(2, 1fr); }
  .settings-grid { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  .admin-page { padding: var(--sp-6); gap: var(--sp-4); }
  .tab-nav { overflow-x: auto; }
  .stats-strip { flex-wrap: wrap; }
  .stat-sep { display: none; }
  .stat-cell { min-width: 40%; }
}

@media (max-width: 680px) {
  .admin-page { padding: var(--sp-4); }
  .roles-grid { grid-template-columns: 1fr; }
  .uth:nth-child(4), .utd:nth-child(4) { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .user-row, .audit-entry { animation: none; opacity: 1; transform: none; }
}
</style>
