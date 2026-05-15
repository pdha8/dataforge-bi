<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api/axios'
import {
  Bell, GitBranch, TrendingUp, AlertTriangle, FileText,
  Activity, Search, RefreshCcw, CheckCheck, ChevronLeft,
  ChevronRight, X, Plus, Pencil, Trash2, Play, ToggleLeft,
  ToggleRight, Mail, MessageSquare, Hash, Globe, Check,
} from 'lucide-vue-next'

// ── Types ───────────────────────────────────────────────────
interface Notification {
  id: string
  title: string
  message: string
  notification_type: string
  notification_type_display: string
  status: string
  priority: string
  priority_display: string
  icon: string
  color: string
  time_ago: string
  created_at: string
  read_at: string | null
  sent_at: string | null
  pipeline_name: string
  kpi_name: string
  dashboard_name: string
}

interface AlertRule {
  id: string
  name: string
  description: string
  is_enabled: boolean
  kpi: string
  kpi_name: string
  condition: string
  condition_display: string
  threshold: number | null
  percentage_change: number | null
  check_frequency: string
  check_frequency_display: string
  cooldown_minutes: number
  last_triggered: string | null
  trigger_count: number
  notification_message: string
  created_at: string
}

interface Channel {
  id: string
  name: string
  provider: string
  is_active: boolean
}

interface Stats {
  total?: number
  unread?: number
  critical?: number
  today?: number
  [key: string]: number | undefined
}

interface PaginatedResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}

interface Subscription {
  id: string
  notification_type: string
  notification_type_display: string
  is_enabled: boolean
  preferred_channels: string[]
  filters: Record<string, unknown>
}

// ── Tabs ────────────────────────────────────────────────────
type Tab = 'notifications' | 'alerts' | 'channels' | 'subscriptions'
const activeTab = ref<Tab>('notifications')

// ── Notification state ───────────────────────────────────────
const notifications   = ref<Notification[]>([])
const notifLoading    = ref(true)
const notifTotal      = ref(0)
const notifPage       = ref(1)
const notifPageSize   = 20
const notifNext       = ref<string | null>(null)
const notifPrev       = ref<string | null>(null)
const searchQuery     = ref('')
const filterType      = ref('all')
const filterPriority  = ref('all')
const unreadCount     = ref(0)
const stats           = ref<Stats>({})
const markingAll      = ref(false)

// ── Alert Rules state ────────────────────────────────────────
const alertRules      = ref<AlertRule[]>([])
const alertLoading    = ref(true)
const drawerOpen      = ref(false)
const editingRule     = ref<AlertRule | null>(null)
const submitting      = ref(false)
const testingId       = ref<string | null>(null)
const deleteConfirm   = ref<string | null>(null)

const alertForm = ref({
  name: '',
  description: '',
  kpi: '',
  condition: 'gt',
  threshold: null as number | null,
  percentage_change: null as number | null,
  check_frequency: 'hourly',
  cooldown_minutes: 60,
  notification_message: '',
  is_enabled: true,
})

// ── Channels state ───────────────────────────────────────────
const channels        = ref<Channel[]>([])
const channelsLoading = ref(true)

// ── Subscriptions state ───────────────────────────────────────
const subscriptions   = ref<Subscription[]>([])
const subsLoading     = ref(true)
const subsSubmitting  = ref<string | null>(null)
const editSub         = ref<string | null>(null)

// ── Helpers ──────────────────────────────────────────────────
const isRead = (n: Notification) => n.status === 'read' || n.read_at !== null

function typeIcon(type: string) {
  if (['pipeline_complete', 'pipeline_failed', 'pipeline_started'].includes(type)) return GitBranch
  if (['kpi_alert', 'kpi_target_reached'].includes(type)) return TrendingUp
  if (['system_alert', 'maintenance'].includes(type)) return AlertTriangle
  if (type === 'report_ready') return FileText
  if (type === 'anomaly_detected') return Activity
  return Bell
}

function typeColor(type: string): string {
  if (['pipeline_failed', 'system_alert', 'anomaly_detected'].includes(type)) return 'error'
  if (type === 'kpi_alert') return 'warning'
  if (['kpi_target_reached', 'pipeline_complete', 'report_ready'].includes(type)) return 'success'
  return 'info'
}

function priorityClass(priority: string): string {
  const map: Record<string, string> = {
    critical: 'badge--error',
    high:     'badge--warning',
    medium:   'badge--amber',
    low:      'badge--muted',
  }
  return map[priority] ?? 'badge--muted'
}

function providerIcon(provider: string) {
  const map: Record<string, typeof Bell> = {
    email:   Mail,
    sms:     MessageSquare,
    slack:   Hash,
    webhook: Globe,
  }
  return map[provider] ?? Bell
}

function conditionShowsThreshold(cond: string) {
  return !['change_up', 'change_down', 'anomaly'].includes(cond)
}
function conditionShowsPct(cond: string) {
  return ['change_up', 'change_down'].includes(cond)
}

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ── Type filter options ──────────────────────────────────────
const TYPE_FILTER_OPTIONS = [
  { value: 'all',               label: 'Tous' },
  { value: 'pipeline',          label: 'Pipeline' },
  { value: 'kpi',               label: 'KPI' },
  { value: 'system_alert',      label: 'Système' },
  { value: 'report_ready',      label: 'Rapport' },
]

const PRIORITY_OPTIONS = [
  { value: 'all',      label: 'Toutes priorités' },
  { value: 'critical', label: 'Critique' },
  { value: 'high',     label: 'Haute' },
  { value: 'medium',   label: 'Moyenne' },
  { value: 'low',      label: 'Basse' },
]

const CONDITION_OPTIONS = [
  { value: 'gt',          label: '> Supérieur à' },
  { value: 'lt',          label: '< Inférieur à' },
  { value: 'gte',         label: '≥ Supérieur ou égal' },
  { value: 'lte',         label: '≤ Inférieur ou égal' },
  { value: 'eq',          label: '= Égal à' },
  { value: 'change_up',   label: '↑ Hausse %' },
  { value: 'change_down', label: '↓ Baisse %' },
  { value: 'anomaly',     label: 'Anomalie détectée' },
]

const FREQUENCY_OPTIONS = [
  { value: 'realtime',    label: 'Temps réel' },
  { value: 'every_5min',  label: 'Toutes les 5 min' },
  { value: 'every_15min', label: 'Toutes les 15 min' },
  { value: 'hourly',      label: 'Horaire' },
  { value: 'daily',       label: 'Quotidien' },
]

// ── Computed filtered ────────────────────────────────────────
const filteredNotifications = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return notifications.value.filter(n => {
    const matchSearch = !q
      || n.title.toLowerCase().includes(q)
      || n.message.toLowerCase().includes(q)
    const matchType = filterType.value === 'all'
      || (filterType.value === 'pipeline' && n.notification_type.startsWith('pipeline'))
      || (filterType.value === 'kpi' && n.notification_type.startsWith('kpi'))
      || n.notification_type === filterType.value
    const matchPriority = filterPriority.value === 'all' || n.priority === filterPriority.value
    return matchSearch && matchType && matchPriority
  })
})

const totalPages = computed(() => Math.ceil(notifTotal.value / notifPageSize))

// ── API calls ────────────────────────────────────────────────
async function fetchNotifications(page = 1) {
  notifLoading.value = true
  try {
    const params: Record<string, string | number> = { page }
    const res = await api.get<PaginatedResponse<Notification>>('/api/notifications/notifications/', { params })
    notifications.value = res.data.results ?? []
    notifTotal.value     = res.data.count ?? 0
    notifNext.value      = res.data.next
    notifPrev.value      = res.data.previous
    notifPage.value      = page
  } catch {
    notifications.value = []
  } finally {
    notifLoading.value = false
  }
}

async function fetchUnreadCount() {
  try {
    const res = await api.get<{ count: number }>('/api/notifications/notifications/unread_count/')
    unreadCount.value = res.data.count ?? 0
  } catch {
    unreadCount.value = 0
  }
}

async function fetchStats() {
  try {
    const res = await api.get<Stats>('/api/notifications/notifications/stats/')
    stats.value = res.data ?? {}
  } catch {
    stats.value = {}
  }
}

async function markRead(id: string) {
  try {
    await api.post(`/api/notifications/notifications/${id}/mark_read/`)
    const n = notifications.value.find(x => x.id === id)
    if (n) {
      n.status  = 'read'
      n.read_at = new Date().toISOString()
    }
    if (unreadCount.value > 0) unreadCount.value--
  } catch { /* silent */ }
}

async function markAllRead() {
  markingAll.value = true
  try {
    await api.post('/api/notifications/notifications/mark_all_read/')
    notifications.value.forEach(n => {
      n.status  = 'read'
      n.read_at = n.read_at ?? new Date().toISOString()
    })
    unreadCount.value = 0
  } catch { /* silent */ } finally {
    markingAll.value = false
  }
}

async function handleNotifClick(n: Notification) {
  if (!isRead(n)) await markRead(n.id)
}

// ── Alert rule API ───────────────────────────────────────────
async function fetchAlertRules() {
  alertLoading.value = true
  try {
    const res = await api.get<AlertRule[] | PaginatedResponse<AlertRule>>('/api/notifications/alerts/')
    alertRules.value = Array.isArray(res.data) ? res.data : (res.data.results ?? [])
  } catch {
    alertRules.value = []
  } finally {
    alertLoading.value = false
  }
}

async function toggleRule(rule: AlertRule) {
  try {
    await api.patch(`/api/notifications/alerts/${rule.id}/`, { is_enabled: !rule.is_enabled })
    rule.is_enabled = !rule.is_enabled
  } catch { /* silent */ }
}

async function testRule(id: string) {
  testingId.value = id
  try {
    await api.post(`/api/notifications/alerts/${id}/test/`)
  } catch { /* silent */ } finally {
    testingId.value = null
  }
}

async function deleteRule(id: string) {
  try {
    await api.delete(`/api/notifications/alerts/${id}/`)
    alertRules.value = alertRules.value.filter(r => r.id !== id)
    deleteConfirm.value = null
  } catch { /* silent */ }
}

function openCreateDrawer() {
  editingRule.value = null
  alertForm.value = {
    name: '', description: '', kpi: '', condition: 'gt',
    threshold: null, percentage_change: null,
    check_frequency: 'hourly', cooldown_minutes: 60,
    notification_message: '', is_enabled: true,
  }
  drawerOpen.value = true
}

function openEditDrawer(rule: AlertRule) {
  editingRule.value = rule
  alertForm.value = {
    name:                 rule.name,
    description:          rule.description,
    kpi:                  rule.kpi,
    condition:            rule.condition,
    threshold:            rule.threshold,
    percentage_change:    rule.percentage_change,
    check_frequency:      rule.check_frequency,
    cooldown_minutes:     rule.cooldown_minutes,
    notification_message: rule.notification_message,
    is_enabled:           rule.is_enabled,
  }
  drawerOpen.value = true
}

async function submitAlertForm() {
  submitting.value = true
  try {
    const payload = { ...alertForm.value }
    if (conditionShowsThreshold(payload.condition)) payload.percentage_change = null
    if (conditionShowsPct(payload.condition)) payload.threshold = null
    if (payload.condition === 'anomaly') { payload.threshold = null; payload.percentage_change = null }

    if (editingRule.value) {
      const res = await api.patch<AlertRule>(`/api/notifications/alerts/${editingRule.value.id}/`, payload)
      const idx = alertRules.value.findIndex(r => r.id === editingRule.value!.id)
      if (idx !== -1) alertRules.value[idx] = res.data
    } else {
      const res = await api.post<AlertRule>('/api/notifications/alerts/', payload)
      alertRules.value.unshift(res.data)
    }
    drawerOpen.value = false
  } catch { /* silent */ } finally {
    submitting.value = false
  }
}

// ── Subscriptions constants ───────────────────────────────────
const AVAILABLE_CHANNELS = [
  { key: 'email',   label: 'Email',   icon: Mail },
  { key: 'sms',     label: 'SMS',     icon: MessageSquare },
  { key: 'webhook', label: 'Webhook', icon: Globe },
  { key: 'in_app',  label: 'In-App',  icon: Bell },
] as const

const SUB_TYPE_LABELS: Record<string, string> = {
  kpi_alert:         'Alerte KPI',
  kpi_target_reached:'KPI objectif atteint',
  pipeline_complete: 'Pipeline terminé',
  pipeline_failed:   'Pipeline échoué',
  pipeline_started:  'Pipeline démarré',
  report_ready:      'Rapport prêt',
  dashboard_shared:  'Dashboard partagé',
  anomaly_detected:  'Anomalie détectée',
  system_alert:      'Alerte système',
  user_welcome:      'Bienvenue',
  weekly_digest:     'Résumé hebdomadaire',
}

// ── Subscriptions API ─────────────────────────────────────────
async function fetchSubscriptions() {
  subsLoading.value = true
  try {
    const res = await api.get<Subscription[] | PaginatedResponse<Subscription>>('/api/notifications/subscriptions/')
    subscriptions.value = Array.isArray(res.data) ? res.data : (res.data.results ?? [])
  } catch {
    subscriptions.value = []
  } finally {
    subsLoading.value = false
  }
}

async function toggleSubscription(sub: Subscription) {
  subsSubmitting.value = sub.id
  try {
    await api.patch(`/api/notifications/subscriptions/${sub.id}/`, { is_enabled: !sub.is_enabled })
    sub.is_enabled = !sub.is_enabled
  } catch { /* silent */ } finally {
    subsSubmitting.value = null
  }
}

async function saveSubChannels(sub: Subscription) {
  subsSubmitting.value = sub.id
  try {
    await api.patch(`/api/notifications/subscriptions/${sub.id}/`, { preferred_channels: sub.preferred_channels })
    editSub.value = null
  } catch { /* silent */ } finally {
    subsSubmitting.value = null
  }
}

function toggleChannel(sub: Subscription, key: string) {
  const idx = sub.preferred_channels.indexOf(key)
  if (idx === -1) sub.preferred_channels.push(key)
  else sub.preferred_channels.splice(idx, 1)
}

// ── Channels API ─────────────────────────────────────────────
async function fetchChannels() {
  channelsLoading.value = true
  try {
    const res = await api.get<Channel[] | PaginatedResponse<Channel>>('/api/notifications/channels/')
    channels.value = Array.isArray(res.data) ? res.data : (res.data.results ?? [])
  } catch {
    channels.value = []
  } finally {
    channelsLoading.value = false
  }
}

// ── Tab switch lazy load ─────────────────────────────────────
watch(activeTab, (tab) => {
  if (tab === 'alerts' && alertRules.value.length === 0 && !alertLoading.value) fetchAlertRules()
  if (tab === 'channels' && channels.value.length === 0 && !channelsLoading.value) fetchChannels()
  if (tab === 'subscriptions' && subscriptions.value.length === 0 && !subsLoading.value) fetchSubscriptions()
})

// ── Init ─────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([fetchNotifications(), fetchUnreadCount(), fetchStats(), fetchSubscriptions()])
})
</script>

<template>
  <div class="notif-page">
    <!-- ── Page header ─────────────────────────────────────── -->
    <header class="page-header">
      <div class="page-header__left">
        <h1 class="page-title">Notifications</h1>
        <span v-if="unreadCount > 0" class="unread-pill">{{ unreadCount }}</span>
      </div>
      <div class="page-header__tabs">
        <button
          v-for="tab in (['notifications', 'alerts', 'channels', 'subscriptions'] as Tab[])"
          :key="tab"
          :class="['tab-btn', { 'tab-btn--active': activeTab === tab }]"
          @click="activeTab = tab"
        >
          <Bell          v-if="tab === 'notifications'"  :size="15" />
          <AlertTriangle v-else-if="tab === 'alerts'"   :size="15" />
          <Mail          v-else-if="tab === 'channels'"  :size="15" />
          <Bell          v-else                          :size="15" />
          <span>{{
            tab === 'notifications'  ? 'Notifications'
            : tab === 'alerts'       ? 'Règles d\'alerte'
            : tab === 'channels'     ? 'Canaux'
            : 'Abonnements'
          }}</span>
          <span v-if="tab === 'notifications' && unreadCount > 0" class="tab-badge">{{ unreadCount }}</span>
        </button>
      </div>
    </header>

    <!-- ════════════════════════════════════════════════════════
         TAB 1 — NOTIFICATIONS
    ═════════════════════════════════════════════════════════ -->
    <section v-if="activeTab === 'notifications'" class="tab-section">

      <!-- Stat cards -->
      <div class="stat-grid">
        <div class="stat-card">
          <span class="stat-label">Total</span>
          <span class="stat-value">{{ stats.total ?? notifTotal }}</span>
        </div>
        <div class="stat-card stat-card--accent">
          <span class="stat-label">Non lues</span>
          <span class="stat-value">{{ stats.unread ?? unreadCount }}</span>
        </div>
        <div class="stat-card stat-card--error">
          <span class="stat-label">Critiques</span>
          <span class="stat-value">{{ stats.critical ?? 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Aujourd'hui</span>
          <span class="stat-value">{{ stats.today ?? 0 }}</span>
        </div>
      </div>

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar__search">
          <Search :size="15" class="toolbar__search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher une notification…"
            class="toolbar__input"
          />
        </div>

        <select v-model="filterType" class="toolbar__select">
          <option v-for="opt in TYPE_FILTER_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>

        <select v-model="filterPriority" class="toolbar__select">
          <option v-for="opt in PRIORITY_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>

        <div class="toolbar__actions">
          <button
            class="btn btn--ghost btn--sm"
            :disabled="markingAll || unreadCount === 0"
            @click="markAllRead"
          >
            <CheckCheck :size="14" />
            {{ markingAll ? 'Traitement…' : 'Tout marquer comme lu' }}
          </button>
          <button class="btn btn--ghost btn--icon" @click="fetchNotifications(notifPage)">
            <RefreshCcw :size="15" :class="{ 'spin': notifLoading }" />
          </button>
        </div>
      </div>

      <!-- List -->
      <div class="notif-list">
        <!-- Skeleton -->
        <template v-if="notifLoading">
          <div v-for="i in 5" :key="i" class="notif-skeleton">
            <div class="skel skel--dot" />
            <div class="skel skel--icon" />
            <div class="skel-body">
              <div class="skel skel--title" />
              <div class="skel skel--msg" />
            </div>
          </div>
        </template>

        <!-- Empty -->
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <Bell :size="40" class="empty-state__icon" />
          <p class="empty-state__text">Aucune notification</p>
          <p class="empty-state__sub">Modifiez vos filtres ou revenez plus tard.</p>
        </div>

        <!-- Items -->
        <template v-else>
          <div
            v-for="n in filteredNotifications"
            :key="n.id"
            :class="['notif-item', { 'notif-item--unread': !isRead(n) }]"
            @click="handleNotifClick(n)"
          >
            <!-- Unread dot -->
            <span :class="['notif-dot', { 'notif-dot--active': !isRead(n) }]" />

            <!-- Icon -->
            <div :class="['notif-icon', `notif-icon--${typeColor(n.notification_type)}`]">
              <span v-if="n.icon" class="notif-emoji">{{ n.icon }}</span>
              <component :is="typeIcon(n.notification_type)" v-else :size="16" />
            </div>

            <!-- Body -->
            <div class="notif-body">
              <p :class="['notif-title', { 'notif-title--bold': !isRead(n) }]">{{ n.title }}</p>
              <p class="notif-message">{{ n.message }}</p>
              <span class="notif-time">{{ n.time_ago }}</span>
            </div>

            <!-- Right meta -->
            <div class="notif-meta" @click.stop>
              <span :class="['badge', priorityClass(n.priority)]">{{ n.priority_display || n.priority }}</span>
              <span class="badge badge--type">{{ n.notification_type_display || n.notification_type }}</span>
              <button
                v-if="!isRead(n)"
                class="btn btn--ghost btn--icon btn--xs"
                title="Marquer comme lu"
                @click="markRead(n.id)"
              >
                <Check :size="13" />
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- Pagination -->
      <div v-if="!notifLoading && totalPages > 1" class="pagination">
        <button
          class="btn btn--ghost btn--sm"
          :disabled="!notifPrev"
          @click="fetchNotifications(notifPage - 1)"
        >
          <ChevronLeft :size="15" /> Précédent
        </button>
        <span class="pagination__info">Page {{ notifPage }} / {{ totalPages }}</span>
        <button
          class="btn btn--ghost btn--sm"
          :disabled="!notifNext"
          @click="fetchNotifications(notifPage + 1)"
        >
          Suivant <ChevronRight :size="15" />
        </button>
      </div>
    </section>

    <!-- ════════════════════════════════════════════════════════
         TAB 2 — RÈGLES D'ALERTE
    ═════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'alerts'" class="tab-section">
      <div class="section-header">
        <h2 class="section-title">Règles d'alerte</h2>
        <button class="btn btn--primary btn--sm" @click="openCreateDrawer">
          <Plus :size="15" /> Nouvelle règle
        </button>
      </div>

      <!-- Loading skeleton -->
      <template v-if="alertLoading">
        <div v-for="i in 4" :key="i" class="alert-skeleton">
          <div class="skel skel--alert-name" />
          <div class="skel skel--alert-pill" />
          <div class="skel skel--alert-pill" />
          <div class="skel skel--alert-pill" />
        </div>
      </template>

      <!-- Empty -->
      <div v-else-if="alertRules.length === 0" class="empty-state">
        <AlertTriangle :size="40" class="empty-state__icon" />
        <p class="empty-state__text">Aucune règle d'alerte</p>
        <p class="empty-state__sub">Créez une règle pour être notifié automatiquement.</p>
      </div>

      <!-- Table -->
      <div v-else class="alert-table-wrap">
        <table class="alert-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>KPI lié</th>
              <th>Condition</th>
              <th>Seuil</th>
              <th>Fréquence</th>
              <th>Dernier déclenché</th>
              <th>Déclenchements</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in alertRules" :key="rule.id">
              <td>
                <span class="rule-name">{{ rule.name }}</span>
                <span v-if="rule.description" class="rule-desc">{{ rule.description }}</span>
              </td>
              <td>
                <span class="badge badge--type">{{ rule.kpi_name || '—' }}</span>
              </td>
              <td>
                <span class="badge badge--muted">{{ rule.condition_display || rule.condition }}</span>
              </td>
              <td class="td--mono">
                {{ rule.threshold !== null ? rule.threshold : rule.percentage_change !== null ? rule.percentage_change + '%' : '—' }}
              </td>
              <td>{{ rule.check_frequency_display || rule.check_frequency }}</td>
              <td class="td--muted">{{ fmtDate(rule.last_triggered) }}</td>
              <td class="td--mono td--center">{{ rule.trigger_count }}</td>
              <td>
                <button
                  :class="['toggle-btn', { 'toggle-btn--on': rule.is_enabled }]"
                  :title="rule.is_enabled ? 'Désactiver' : 'Activer'"
                  @click="toggleRule(rule)"
                >
                  <ToggleRight v-if="rule.is_enabled" :size="22" />
                  <ToggleLeft  v-else :size="22" />
                  <span>{{ rule.is_enabled ? 'Activé' : 'Désactivé' }}</span>
                </button>
              </td>
              <td>
                <div class="action-row">
                  <button
                    class="btn btn--ghost btn--icon btn--xs"
                    title="Tester"
                    :disabled="testingId === rule.id"
                    @click="testRule(rule.id)"
                  >
                    <Play :size="13" :class="{ 'spin': testingId === rule.id }" />
                  </button>
                  <button
                    class="btn btn--ghost btn--icon btn--xs"
                    title="Modifier"
                    @click="openEditDrawer(rule)"
                  >
                    <Pencil :size="13" />
                  </button>
                  <button
                    class="btn btn--ghost btn--icon btn--xs btn--danger"
                    title="Supprimer"
                    @click="deleteConfirm = rule.id"
                  >
                    <Trash2 :size="13" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Delete confirm -->
      <div v-if="deleteConfirm" class="modal-overlay" @click.self="deleteConfirm = null">
        <div class="modal">
          <h3 class="modal__title">Supprimer la règle ?</h3>
          <p class="modal__text">Cette action est irréversible.</p>
          <div class="modal__actions">
            <button class="btn btn--ghost btn--sm" @click="deleteConfirm = null">Annuler</button>
            <button class="btn btn--danger btn--sm" @click="deleteRule(deleteConfirm!)">Supprimer</button>
          </div>
        </div>
      </div>

      <!-- Alert Rule Drawer -->
      <Teleport to="body">
        <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
          <div class="drawer">
            <div class="drawer__header">
              <h2 class="drawer__title">{{ editingRule ? 'Modifier la règle' : 'Nouvelle règle d\'alerte' }}</h2>
              <button class="btn btn--ghost btn--icon" @click="drawerOpen = false">
                <X :size="18" />
              </button>
            </div>

            <form class="drawer__form" @submit.prevent="submitAlertForm">
              <!-- Name -->
              <div class="field">
                <label class="field__label">Nom <span class="field__req">*</span></label>
                <input v-model="alertForm.name" type="text" required class="field__input" placeholder="Alerte CA mensuel…" />
              </div>

              <!-- Description -->
              <div class="field">
                <label class="field__label">Description</label>
                <textarea v-model="alertForm.description" class="field__textarea" rows="2" placeholder="Optionnel" />
              </div>

              <!-- KPI -->
              <div class="field">
                <label class="field__label">KPI (UUID)</label>
                <input v-model="alertForm.kpi" type="text" class="field__input" placeholder="UUID du KPI…" />
              </div>

              <!-- Condition -->
              <div class="field">
                <label class="field__label">Condition <span class="field__req">*</span></label>
                <select v-model="alertForm.condition" class="field__select">
                  <option v-for="opt in CONDITION_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <!-- Threshold (conditional) -->
              <div v-if="conditionShowsThreshold(alertForm.condition)" class="field">
                <label class="field__label">Seuil</label>
                <input v-model.number="alertForm.threshold" type="number" step="any" class="field__input" placeholder="Ex: 1000" />
              </div>

              <!-- Percentage change (conditional) -->
              <div v-if="conditionShowsPct(alertForm.condition)" class="field">
                <label class="field__label">Variation % déclenchante</label>
                <input v-model.number="alertForm.percentage_change" type="number" step="any" class="field__input" placeholder="Ex: 10" />
              </div>

              <!-- Frequency -->
              <div class="field">
                <label class="field__label">Fréquence de vérification</label>
                <select v-model="alertForm.check_frequency" class="field__select">
                  <option v-for="opt in FREQUENCY_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <!-- Cooldown -->
              <div class="field">
                <label class="field__label">Délai de répétition (min)</label>
                <input v-model.number="alertForm.cooldown_minutes" type="number" min="0" class="field__input" />
              </div>

              <!-- Message -->
              <div class="field">
                <label class="field__label">Message de notification</label>
                <textarea v-model="alertForm.notification_message" class="field__textarea" rows="3" placeholder="Message personnalisé…" />
              </div>

              <!-- Enabled -->
              <div class="field field--checkbox">
                <input id="is_enabled" v-model="alertForm.is_enabled" type="checkbox" class="field__checkbox" />
                <label for="is_enabled" class="field__label">Activer immédiatement</label>
              </div>

              <div class="drawer__footer">
                <button type="button" class="btn btn--ghost btn--sm" @click="drawerOpen = false">Annuler</button>
                <button type="submit" class="btn btn--primary btn--sm" :disabled="submitting">
                  {{ submitting ? 'Enregistrement…' : editingRule ? 'Enregistrer' : 'Créer la règle' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </Teleport>
    </section>

    <!-- ════════════════════════════════════════════════════════
         TAB 3 — CANAUX
    ═════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'channels'" class="tab-section">
      <div class="section-header">
        <h2 class="section-title">Canaux de notification</h2>
      </div>

      <!-- Loading skeleton -->
      <template v-if="channelsLoading">
        <div v-for="i in 3" :key="i" class="channel-skeleton">
          <div class="skel skel--ch-icon" />
          <div class="skel-body">
            <div class="skel skel--title" />
            <div class="skel skel--msg" style="width:60%" />
          </div>
        </div>
      </template>

      <!-- Empty -->
      <div v-else-if="channels.length === 0" class="empty-state">
        <Mail :size="40" class="empty-state__icon" />
        <p class="empty-state__text">Aucun canal configuré</p>
        <p class="empty-state__sub">Configurez des canaux depuis l'administration.</p>
      </div>

      <!-- Channel cards -->
      <div v-else class="channel-list">
        <div v-for="ch in channels" :key="ch.id" class="channel-card">
          <div :class="['channel-icon', `channel-icon--${ch.provider}`]">
            <component :is="providerIcon(ch.provider)" :size="20" />
          </div>
          <div class="channel-body">
            <p class="channel-name">{{ ch.name }}</p>
            <p class="channel-provider">{{ ch.provider }}</p>
          </div>
          <span :class="['badge', ch.is_active ? 'badge--success' : 'badge--muted']">
            {{ ch.is_active ? 'Actif' : 'Inactif' }}
          </span>
        </div>
      </div>
    </section>

    <!-- ════════════════════════════════════════════════════════
         TAB 4 — ABONNEMENTS
    ═════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'subscriptions'" class="tab-section">
      <div class="section-header">
        <h2 class="section-title">Abonnements aux notifications</h2>
        <button class="btn btn--ghost btn--icon" @click="fetchSubscriptions">
          <RefreshCcw :size="15" :class="{ 'spin': subsLoading }" />
        </button>
      </div>

      <!-- Loading skeleton -->
      <template v-if="subsLoading">
        <div v-for="i in 5" :key="i" class="alert-skeleton">
          <div class="skel skel--icon" />
          <div class="skel skel--alert-name" style="flex:1" />
          <div class="skel skel--alert-pill" />
          <div class="skel skel--alert-pill" />
          <div class="skel skel--alert-pill" />
        </div>
      </template>

      <!-- Empty -->
      <div v-else-if="subscriptions.length === 0" class="empty-state">
        <Bell :size="40" class="empty-state__icon" />
        <p class="empty-state__text">Aucun abonnement configuré</p>
        <p class="empty-state__sub">
          Les abonnements apparaissent automatiquement selon vos types de notifications actifs.
        </p>
        <button class="btn btn--primary btn--sm" @click="activeTab = 'notifications'">
          <Bell :size="14" /> Voir les notifications
        </button>
      </div>

      <!-- Subscriptions table -->
      <div v-else class="alert-table-wrap">
        <table class="alert-table">
          <thead>
            <tr>
              <th>Type de notification</th>
              <th>Activé</th>
              <th>Canaux préférés</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sub in subscriptions" :key="sub.id">
              <!-- Type -->
              <td>
                <div class="sub-type-cell">
                  <div :class="['notif-icon', `notif-icon--${typeColor(sub.notification_type)}`]" style="width:28px;height:28px;flex-shrink:0">
                    <component :is="typeIcon(sub.notification_type)" :size="14" />
                  </div>
                  <span class="rule-name">
                    {{ sub.notification_type_display || SUB_TYPE_LABELS[sub.notification_type] || sub.notification_type }}
                  </span>
                </div>
              </td>

              <!-- Toggle activé -->
              <td>
                <button
                  :class="['toggle-btn', { 'toggle-btn--on': sub.is_enabled }]"
                  :disabled="subsSubmitting === sub.id"
                  :title="sub.is_enabled ? 'Désactiver' : 'Activer'"
                  @click="toggleSubscription(sub)"
                >
                  <ToggleRight v-if="sub.is_enabled" :size="22" />
                  <ToggleLeft  v-else                 :size="22" />
                  <span>{{ sub.is_enabled ? 'Activé' : 'Désactivé' }}</span>
                </button>
              </td>

              <!-- Canaux préférés -->
              <td>
                <div class="sub-channels-cell">
                  <template v-if="editSub === sub.id">
                    <!-- Mode édition : badges cliquables -->
                    <button
                      v-for="ch in AVAILABLE_CHANNELS"
                      :key="ch.key"
                      :class="['sub-channel-btn', { 'sub-channel-btn--active': sub.preferred_channels.includes(ch.key) }]"
                      @click="toggleChannel(sub, ch.key)"
                    >
                      <component :is="ch.icon" :size="12" />
                      {{ ch.label }}
                    </button>
                  </template>
                  <template v-else>
                    <!-- Mode lecture : badges affichage -->
                    <span
                      v-for="key in sub.preferred_channels"
                      :key="key"
                      class="badge badge--amber"
                    >
                      {{ AVAILABLE_CHANNELS.find(c => c.key === key)?.label ?? key }}
                    </span>
                    <span v-if="sub.preferred_channels.length === 0" class="badge badge--muted">
                      Aucun
                    </span>
                  </template>
                </div>
              </td>

              <!-- Actions -->
              <td>
                <div class="action-row">
                  <template v-if="editSub === sub.id">
                    <button
                      class="btn btn--primary btn--xs"
                      :disabled="subsSubmitting === sub.id"
                      @click="saveSubChannels(sub)"
                    >
                      <Check :size="12" />
                      {{ subsSubmitting === sub.id ? '…' : 'Sauver' }}
                    </button>
                    <button
                      class="btn btn--ghost btn--icon btn--xs"
                      @click="editSub = null"
                    >
                      <X :size="12" />
                    </button>
                  </template>
                  <template v-else>
                    <button
                      class="btn btn--ghost btn--icon btn--xs"
                      title="Modifier les canaux"
                      @click="editSub = sub.id"
                    >
                      <Pencil :size="13" />
                    </button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── Base layout ─────────────────────────────────────────── */
.notif-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  padding: var(--sp-6);
  min-height: 100%;
  background: var(--surface-base);
  font-family: var(--font-ui);
}

/* ── Page header ─────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--sp-4);
}

.page-header__left {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin: 0;
}

.unread-pill {
  background: var(--accent);
  color: oklch(15% 0.05 62);
  font-size: var(--text-xs);
  font-weight: 700;
  border-radius: var(--radius-full);
  padding: 2px 8px;
  min-width: 22px;
  text-align: center;
}

/* ── Tabs ────────────────────────────────────────────────── */
.page-header__tabs {
  display: flex;
  gap: var(--sp-1);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 3px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  border-radius: calc(var(--radius-md) - 2px);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  position: relative;
}

.tab-btn:hover {
  background: var(--surface-overlay);
  color: var(--text-primary);
}

.tab-btn--active {
  background: var(--surface-overlay);
  color: var(--accent);
}

.tab-badge {
  background: var(--accent);
  color: oklch(15% 0.05 62);
  font-size: 10px;
  font-weight: 700;
  border-radius: var(--radius-full);
  padding: 1px 6px;
  min-width: 18px;
  text-align: center;
}

/* ── Tab section ─────────────────────────────────────────── */
.tab-section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* ── Stat cards ──────────────────────────────────────────── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-3);
}

.stat-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.stat-card--accent {
  border-color: var(--accent-dim);
  background: var(--accent-surface);
}

.stat-card--error {
  border-color: color-mix(in oklch, var(--error) 30%, transparent);
  background: var(--error-surface);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.toolbar__search {
  position: relative;
  flex: 1;
  min-width: 220px;
}

.toolbar__search-icon {
  position: absolute;
  left: var(--sp-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.toolbar__input {
  width: 100%;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3) var(--sp-2) calc(var(--sp-3) + 22px);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.toolbar__input::placeholder {
  color: var(--text-muted);
}

.toolbar__input:focus {
  border-color: var(--accent-dim);
}

.toolbar__select {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.toolbar__select:focus {
  border-color: var(--accent-dim);
}

.toolbar__actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

/* ── Buttons ─────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s, opacity 0.15s;
  white-space: nowrap;
  outline: none;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn--sm    { padding: var(--sp-2) var(--sp-3); }
.btn--icon  { padding: var(--sp-2); }
.btn--xs    { padding: 4px; border-radius: var(--radius-sm); }

.btn--primary {
  background: var(--accent);
  color: oklch(15% 0.05 62);
  border-color: var(--accent);
}
.btn--primary:hover:not(:disabled) {
  filter: brightness(1.1);
}

.btn--ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-subtle);
}
.btn--ghost:hover:not(:disabled) {
  background: var(--surface-overlay);
  color: var(--text-primary);
}

.btn--danger {
  background: var(--error);
  color: #fff;
  border-color: var(--error);
}
.btn--danger:hover:not(:disabled) {
  filter: brightness(1.1);
}

/* ── Notification list ───────────────────────────────────── */
.notif-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.notif-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.notif-item:hover {
  background: var(--surface-overlay);
  border-color: var(--border-default);
}

.notif-item--unread {
  border-color: color-mix(in oklch, var(--accent) 30%, var(--border-subtle));
  background: color-mix(in oklch, var(--accent-surface) 60%, var(--surface-raised));
}

/* Unread dot */
.notif-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: transparent;
  transition: background 0.2s;
}
.notif-dot--active {
  background: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-surface);
}

/* Icon circle */
.notif-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.notif-emoji {
  font-size: 18px;
  line-height: 1;
}
.notif-icon--error   { background: var(--error-surface);   color: var(--error);   }
.notif-icon--warning { background: var(--warning-surface); color: var(--warning); }
.notif-icon--success { background: oklch(20% 0.06 148);    color: oklch(65% 0.17 148); }
.notif-icon--info    { background: oklch(20% 0.05 258);    color: oklch(65% 0.12 258); }

/* Body */
.notif-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.notif-title {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.notif-title--bold {
  color: var(--text-primary);
  font-weight: 600;
}

.notif-message {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notif-time {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

/* Right meta */
.notif-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-shrink: 0;
}

/* ── Badges ──────────────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
}

.badge--error   { background: var(--error-surface);   color: var(--error);   }
.badge--warning { background: var(--warning-surface); color: var(--warning); }
.badge--amber   { background: var(--accent-surface);  color: var(--accent);  }
.badge--muted   { background: var(--surface-muted);   color: var(--text-muted); }
.badge--success { background: oklch(20% 0.06 148);    color: oklch(65% 0.17 148); }
.badge--type    {
  background: var(--surface-muted);
  color: var(--text-secondary);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Pagination ──────────────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-4);
  padding: var(--sp-3) 0;
}

.pagination__info {
  font-size: var(--text-sm);
  color: var(--text-muted);
}

/* ── Section header ──────────────────────────────────────── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin: 0;
}

/* ── Alert table ─────────────────────────────────────────── */
.alert-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.alert-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.alert-table thead {
  background: var(--surface-raised);
}

.alert-table th {
  text-align: left;
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}

.alert-table td {
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
}

.alert-table tbody tr:last-child td {
  border-bottom: none;
}

.alert-table tbody tr {
  background: var(--surface-base);
  transition: background 0.12s;
}

.alert-table tbody tr:hover {
  background: var(--surface-raised);
}

.rule-name {
  display: block;
  font-weight: 600;
  color: var(--text-primary);
}

.rule-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.td--mono   { font-family: monospace; font-size: var(--text-xs); }
.td--muted  { color: var(--text-muted); font-size: var(--text-xs); white-space: nowrap; }
.td--center { text-align: center; }

/* Toggle button */
.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  color: var(--text-muted);
  padding: 0;
  transition: color 0.15s;
}

.toggle-btn--on {
  color: var(--accent);
}

.action-row {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

/* ── Modal (delete confirm) ──────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0 0 / 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--sp-6);
  min-width: 320px;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.modal__title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  color: var(--text-primary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.modal__text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
}

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0 0 / 0.55);
  display: flex;
  justify-content: flex-end;
  z-index: 300;
  backdrop-filter: blur(3px);
}

.drawer {
  width: 440px;
  max-width: 95vw;
  height: 100%;
  background: var(--surface-overlay);
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
}

.drawer__title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  margin: 0;
}

.drawer__form {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  padding: var(--sp-6);
}

.drawer__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border-subtle);
  margin-top: var(--sp-2);
}

/* ── Form fields ─────────────────────────────────────────── */
.field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.field--checkbox {
  flex-direction: row;
  align-items: center;
  gap: var(--sp-3);
}

.field__label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.field__req {
  color: var(--error);
}

.field__input,
.field__select,
.field__textarea {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.field__input::placeholder,
.field__textarea::placeholder {
  color: var(--text-muted);
}

.field__input:focus,
.field__select:focus,
.field__textarea:focus {
  border-color: var(--accent-dim);
}

.field__textarea {
  resize: vertical;
  min-height: 64px;
}

.field__checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
  flex-shrink: 0;
}

/* ── Channel list ────────────────────────────────────────── */
.channel-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.channel-card {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.channel-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.channel-icon--email   { background: oklch(20% 0.05 258); color: oklch(65% 0.12 258); }
.channel-icon--sms     { background: oklch(20% 0.06 148); color: oklch(65% 0.17 148); }
.channel-icon--slack   { background: var(--accent-surface); color: var(--accent); }
.channel-icon--webhook { background: var(--surface-muted); color: var(--text-muted); }

.channel-body {
  flex: 1;
}

.channel-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.channel-provider {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin: 0;
  text-transform: capitalize;
}

/* ── Skeletons ───────────────────────────────────────────── */
@keyframes shimmer {
  0%   { opacity: 0.4; }
  50%  { opacity: 0.8; }
  100% { opacity: 0.4; }
}

.skel {
  background: var(--surface-muted);
  border-radius: var(--radius-sm);
  animation: shimmer 1.6s ease-in-out infinite;
}

.notif-skeleton {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.skel--dot   { width: 7px;  height: 7px;  border-radius: 50%; flex-shrink: 0; }
.skel--icon  { width: 36px; height: 36px; border-radius: var(--radius-sm); flex-shrink: 0; }
.skel-body   { flex: 1; display: flex; flex-direction: column; gap: var(--sp-2); }
.skel--title { height: 13px; width: 45%; }
.skel--msg   { height: 11px; width: 75%; }

.alert-skeleton {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.skel--alert-name { height: 14px; width: 30%; }
.skel--alert-pill { height: 22px; width: 80px; border-radius: var(--radius-full); }

.channel-skeleton {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.skel--ch-icon { width: 42px; height: 42px; flex-shrink: 0; }

/* ── Empty state ─────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  padding: var(--sp-8) var(--sp-6);
  text-align: center;
}

.empty-state__icon {
  color: var(--text-muted);
  opacity: 0.5;
}

.empty-state__text {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  color: var(--text-secondary);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin: 0;
}

.empty-state__sub {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin: 0;
}

/* ── Subscriptions tab ───────────────────────────────────── */
.sub-type-cell {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.sub-channels-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-2);
}

.sub-channel-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 3px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: var(--surface-muted);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.sub-channel-btn:hover {
  background: var(--surface-overlay);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.sub-channel-btn--active {
  background: var(--accent-surface);
  color: var(--accent);
  border-color: var(--accent-dim);
}

/* ── Spin animation ──────────────────────────────────────── */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.spin {
  animation: spin 0.8s linear infinite;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 900px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .notif-meta {
    flex-direction: column;
    align-items: flex-end;
    gap: var(--sp-1);
  }

  .alert-table th:nth-child(4),
  .alert-table td:nth-child(4),
  .alert-table th:nth-child(6),
  .alert-table td:nth-child(6) {
    display: none;
  }
}

@media (max-width: 640px) {
  .notif-page {
    padding: var(--sp-4);
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header__tabs {
    width: 100%;
    justify-content: stretch;
  }

  .tab-btn {
    flex: 1;
    justify-content: center;
  }

  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar__actions {
    margin-left: 0;
    justify-content: space-between;
  }

  .notif-item {
    flex-wrap: wrap;
  }

  .notif-meta {
    flex-direction: row;
    flex-wrap: wrap;
    width: 100%;
    padding-top: var(--sp-2);
  }
}
</style>
