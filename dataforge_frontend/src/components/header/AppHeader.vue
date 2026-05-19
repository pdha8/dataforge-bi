<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import { Menu, Bell, ChevronDown, LogOut, User, AlertTriangle, Info, GitBranch, TrendingUp, Activity, FileText } from 'lucide-vue-next'
import api from '@/api/axios'

const { toggle } = useSidebar()
const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const showUserMenu  = ref(false)
const showNotifMenu = ref(false)
const userMenuRef   = ref<HTMLElement | null>(null)
const notifRef      = ref<HTMLElement | null>(null)
onClickOutside(userMenuRef, () => { showUserMenu.value = false })
onClickOutside(notifRef,    () => { showNotifMenu.value = false })

interface NotifItem {
  id: string
  title: string
  notification_type: string
  time_ago: string
  status: string
  read_at: string | null
}

const notifs     = ref<NotifItem[]>([])
const unreadCount = ref(0)

function isRead(n: NotifItem) { return n.status === 'read' || n.read_at !== null }

function notifIcon(type: string) {
  if (type?.includes('pipeline')) return GitBranch
  if (type?.includes('kpi'))      return TrendingUp
  if (type?.includes('report'))   return FileText
  if (type?.includes('anomaly'))  return Activity
  if (type === 'system_alert' || type === 'maintenance') return AlertTriangle
  return Info
}

function notifCls(type: string) {
  if (type === 'pipeline_failed' || type === 'system_alert' || type === 'anomaly_detected') return 'ni--err'
  if (type === 'kpi_alert' || type === 'maintenance') return 'ni--warn'
  if (type === 'pipeline_complete' || type === 'kpi_target_reached' || type === 'report_ready') return 'ni--ok'
  return 'ni--info'
}

async function fetchNotifPreview() {
  try {
    const [listRes, countRes] = await Promise.all([
      api.get('/api/notifications/notifications/?page_size=5'),
      api.get('/api/notifications/notifications/unread_count/'),
    ])
    const rows = Array.isArray(listRes.data?.results) ? listRes.data.results : Array.isArray(listRes.data) ? listRes.data : []
    notifs.value = rows
    unreadCount.value = countRes.data?.data?.count ?? countRes.data?.count ?? countRes.data?.unread_count ?? 0
  } catch {
    notifs.value = []
    unreadCount.value = 0
  }
}

async function markAllRead() {
  try {
    await api.post('/api/notifications/notifications/mark_all_read/', {})
    notifs.value.forEach((n: any) => { n.status = 'read' })
    unreadCount.value = 0
  } catch { /* ignore */ }
}

function openNotifications() {
  showNotifMenu.value = false
  router.push('/notifications')
}

onMounted(fetchNotifPreview)

function goToProfile() {
  showUserMenu.value = false
  router.push('/profile')
}

function handleLogout() {
  showUserMenu.value = false
  auth.logout()
  router.replace('/login')
}

const routeLabels: Record<string, string> = {
  '/dashboard':      'Dashboard',
  '/visualizations': 'Visualisations',
  '/dashboards':     'Tableaux de bord',
  '/kpis':           'KPIs',
  '/reports':        'Rapports',
  '/sources':        'Sources de données',
  '/pipelines':      'Pipelines ETL',
  '/warehouse':      'Data Warehouse',
  '/notifications':  'Notifications',
  '/admin':          'Administration',
}

const pageTitle = computed(() => {
  for (const [path, label] of Object.entries(routeLabels)) {
    if (route.path.startsWith(path)) return label
  }
  return 'DataForge BI'
})

const userInitials = computed(() => {
  const u = auth.user
  if (!u) return 'U'
  const parts = [u.first_name, u.last_name].filter(Boolean)
  return parts.length
    ? parts.map((p) => p[0].toUpperCase()).join('')
    : u.username[0].toUpperCase()
})

const userName = computed(() => {
  const u = auth.user
  if (!u) return 'Utilisateur'
  return [u.first_name, u.last_name].filter(Boolean).join(' ') || u.username
})

</script>

<template>
  <header class="app-header" @click.self="showUserMenu = false">

    <!-- Left: mobile toggle + breadcrumb -->
    <div class="header-left">
      <button class="menu-btn" @click="toggle" aria-label="Basculer la navigation">
        <Menu :size="20" />
      </button>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <!-- Right: notifications + user -->
    <div class="header-right">

      <!-- Notifications -->
      <div class="notif-wrap" ref="notifRef">
        <button
          class="icon-btn"
          aria-label="Notifications"
          title="Notifications"
          @click="showNotifMenu = !showNotifMenu"
        >
          <Bell :size="18" />
          <span v-if="unreadCount > 0" class="notif-badge" :aria-label="`${unreadCount} notifications`">
            {{ unreadCount > 9 ? '9+' : unreadCount }}
          </span>
        </button>
        <Transition name="dropdown">
          <div v-if="showNotifMenu" class="notif-dropdown" role="menu">
            <div class="notif-hd">
              <span class="notif-hd-title">Notifications</span>
              <span v-if="unreadCount > 0" class="notif-hd-count">{{ unreadCount }} nouvelle{{ unreadCount > 1 ? 's' : '' }}</span>
            </div>
            <div class="notif-divider"></div>
            <template v-if="notifs.length === 0">
              <div class="notif-empty">Aucune notification récente</div>
            </template>
            <div
              v-for="n in notifs"
              :key="n.id"
              class="notif-item"
              :class="{ 'notif-item--unread': !isRead(n) }"
              role="menuitem"
            >
              <span class="ni-icon" :class="notifCls(n.notification_type)">
                <component :is="notifIcon(n.notification_type)" :size="14" />
              </span>
              <div class="ni-body">
                <span class="ni-title">{{ n.title }}</span>
                <span class="ni-time">{{ n.time_ago }}</span>
              </div>
              <span v-if="!isRead(n)" class="ni-dot"></span>
            </div>
            <div class="notif-divider"></div>
            <div class="notif-footer">
              <button class="notif-footer-btn" @click="markAllRead">Tout marquer comme lu</button>
              <button class="notif-footer-btn notif-footer-btn--primary" @click="openNotifications">Voir tout</button>
            </div>
          </div>
        </Transition>
      </div>

      <!-- User menu -->
      <div class="user-menu-wrap" ref="userMenuRef">
        <button
          class="user-trigger"
          @click="showUserMenu = !showUserMenu"
          :aria-expanded="showUserMenu"
          aria-haspopup="true"
        >
          <span class="user-avatar">{{ userInitials }}</span>
          <span class="user-trigger-name">{{ userName }}</span>
          <ChevronDown
            :size="14"
            class="chevron"
            :class="{ 'chevron--up': showUserMenu }"
          />
        </button>

        <Transition name="dropdown">
          <div v-if="showUserMenu" class="user-dropdown" role="menu">
            <div class="dropdown-header">
              <span class="dropdown-name">{{ userName }}</span>
              <span class="dropdown-role">{{ auth.user?.role ?? 'Analyste BI' }}</span>
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" role="menuitem" @click="goToProfile">
              <User :size="15" />
              <span>Mon profil</span>
            </button>
            <button
              class="dropdown-item dropdown-item--danger"
              role="menuitem"
              @click="handleLogout"
            >
              <LogOut :size="15" />
              <span>Déconnexion</span>
            </button>
          </div>
        </Transition>
      </div>

    </div>
  </header>
</template>

<style scoped>
/* ── Header shell ────────────────────────────────────────── */
.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--sp-6);
  background-color: var(--surface-raised);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  gap: var(--sp-4);
}

/* ── Left ────────────────────────────────────────────────── */
.header-left {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  min-width: 0;
}

.menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: background-color 150ms ease, color 150ms ease;
}

.menu-btn:hover {
  background-color: var(--surface-overlay);
  color: var(--text-primary);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Right ───────────────────────────────────────────────── */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-shrink: 0;
}

.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 150ms ease, color 150ms ease;
}

.icon-btn:hover {
  background-color: var(--surface-overlay);
  color: var(--text-primary);
}

.notif-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 14px;
  height: 14px;
  border-radius: var(--radius-full);
  background-color: var(--accent);
  color: var(--text-on-accent);
  font-size: 9px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  line-height: 1;
}

/* ── Notif wrap ──────────────────────────────────────────── */
.notif-wrap { position: relative; }

.notif-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 300px;
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 8px 32px oklch(0% 0 0 / 0.4);
  z-index: var(--z-dropdown);
}

.notif-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
}

.notif-hd-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.notif-hd-count {
  font-size: var(--text-xs);
  color: var(--accent-dim);
  font-weight: 600;
}

.notif-divider { height: 1px; background: var(--border-subtle); }

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  cursor: pointer;
  transition: background 120ms;
}
.notif-item:hover { background: var(--surface-muted); }

.ni-icon {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ni-icon.ni--warn  { background: oklch(18% 0.05 80);  color: var(--warning); }
.ni-icon.ni--ok    { background: oklch(15% 0.05 148); color: oklch(65% 0.13 148); }
.ni-icon.ni--info  { background: oklch(15% 0.05 258); color: oklch(60% 0.12 258); }
.ni-icon.ni--err   { background: var(--error-surface); color: var(--error); }

.ni-body { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.ni-title { font-size: var(--text-xs); color: var(--text-secondary); font-weight: 500; line-height: 1.4; }
.ni-time  { font-size: 0.68rem; color: var(--text-muted); }

.notif-item--unread .ni-title { color: var(--text-primary); font-weight: 600; }
.ni-dot {
  width: 7px; height: 7px; border-radius: var(--radius-full);
  background: var(--accent); flex-shrink: 0; margin-top: 2px;
}

.notif-empty {
  padding: var(--sp-4);
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.notif-footer {
  display: flex;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-3);
  gap: var(--sp-2);
}
.notif-footer-btn {
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  font-weight: 500;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: var(--sp-1) var(--sp-2);
  border-radius: var(--radius-sm);
  transition: color 150ms ease, background 150ms ease;
}
.notif-footer-btn:hover { color: var(--text-primary); background: var(--surface-muted); }
.notif-footer-btn--primary { color: var(--accent); }
.notif-footer-btn--primary:hover { color: var(--accent); background: var(--accent-surface); }

/* ── User trigger ────────────────────────────────────────── */
.user-menu-wrap { position: relative; }

.user-trigger {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: var(--sp-1) var(--sp-3) var(--sp-1) var(--sp-1);
  cursor: pointer;
  color: var(--text-secondary);
  transition: border-color 150ms ease, background-color 150ms ease;
}

.user-trigger:hover {
  border-color: var(--border-default);
  background-color: var(--surface-overlay);
  color: var(--text-primary);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background-color: var(--accent-surface);
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-trigger-name {
  font-size: var(--text-sm);
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  flex-shrink: 0;
  transition: transform 200ms var(--ease-out-quart);
}

.chevron--up { transform: rotate(-180deg); }

/* ── Dropdown ────────────────────────────────────────────── */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 200px;
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 8px 32px oklch(0% 0 0 / 0.4);
  z-index: var(--z-dropdown);
}

.dropdown-header {
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.dropdown-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.dropdown-role {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.dropdown-divider {
  height: 1px;
  background-color: var(--border-subtle);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  width: 100%;
  padding: var(--sp-3) var(--sp-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  transition: background-color 150ms ease, color 150ms ease;
}

.dropdown-item:hover {
  background-color: var(--surface-muted);
  color: var(--text-primary);
}

.dropdown-item--danger:hover {
  background-color: var(--error-surface);
  color: var(--error);
}

/* ── Dropdown transition ─────────────────────────────────── */
.dropdown-enter-active {
  transition: all 200ms var(--ease-out-expo);
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.97);
}
.dropdown-leave-active {
  transition: all 150ms ease;
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 480px) {
  .user-trigger-name { display: none; }
}
</style>
