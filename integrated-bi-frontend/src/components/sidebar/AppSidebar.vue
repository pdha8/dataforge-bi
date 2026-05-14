<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebar } from '@/composables/useSidebar'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard, Database, GitBranch, ServerCog,
  BarChart2, LayoutGrid, TrendingUp, ShieldCheck,
  ChevronLeft, LogOut, Bell, FileText, Activity, Star,
} from 'lucide-vue-next'

const { collapsed, toggle } = useSidebar()
const route = useRoute()
const auth = useAuthStore()

interface NavItem {
  icon: unknown
  label: string
  to: string
}

interface NavGroup {
  heading: string | null
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    heading: null,
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
    ],
  },
  {
    heading: 'Analytique',
    items: [
      { icon: BarChart2,    label: 'Visualisations',   to: '/visualizations' },
      { icon: LayoutGrid,   label: 'Tableaux de bord', to: '/dashboards' },
      { icon: TrendingUp,   label: 'KPIs',             to: '/kpis' },
      { icon: FileText,     label: 'Rapports',         to: '/reports' },
    ],
  },
  {
    heading: 'Données',
    items: [
      { icon: Database,   label: 'Sources',         to: '/sources' },
      { icon: GitBranch,  label: 'Pipelines ETL',   to: '/pipelines' },
      { icon: Activity,   label: 'Exécutions ETL',  to: '/executions' },
      { icon: ServerCog,  label: 'Data Warehouse',  to: '/warehouse' },
      { icon: Star,       label: 'Schémas étoile',  to: '/star-schema' },
    ],
  },
  {
    heading: 'Système',
    items: [
      { icon: Bell,        label: 'Notifications',  to: '/notifications' },
      { icon: ShieldCheck, label: 'Administration', to: '/admin' },
    ],
  },
]

function isActive(to: string): boolean {
  return route.path.startsWith(to)
}

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
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }" role="navigation" aria-label="Navigation principale">

    <!-- ── Logo ─────────────────────────────────────────── -->
    <div class="sidebar-logo">
      <span class="logo-mark">IBI</span>
      <span class="sidebar-label logo-name">Integrated BI</span>
    </div>

    <!-- ── Navigation ────────────────────────────────────── -->
    <nav class="sidebar-nav">
      <template v-for="group in navGroups" :key="group.heading ?? 'main'">

        <!-- Group heading -->
        <div v-if="group.heading" class="nav-group-head">
          <span class="sidebar-label nav-group-text">{{ group.heading }}</span>
          <span class="nav-group-sep"></span>
        </div>

        <!-- Nav items -->
        <RouterLink
          v-for="item in group.items"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ 'nav-item--active': isActive(item.to) }"
          :data-tooltip="item.label"
        >
          <span class="nav-icon">
            <component :is="(item.icon as never)" :size="20" />
          </span>
          <span class="sidebar-label nav-label">{{ item.label }}</span>
        </RouterLink>

      </template>
    </nav>

    <!-- ── Spacer ─────────────────────────────────────────── -->
    <div class="sidebar-spacer"></div>

    <!-- ── User profile ───────────────────────────────────── -->
    <div class="sidebar-user">
      <div class="user-avatar" :title="userName">{{ userInitials }}</div>
      <div class="sidebar-label user-info">
        <span class="user-name">{{ userName }}</span>
        <button class="user-logout" @click="auth.logout()" title="Déconnexion">
          <LogOut :size="14" />
          <span>Déconnexion</span>
        </button>
      </div>
    </div>

    <!-- ── Collapse toggle ────────────────────────────────── -->
    <button
      class="collapse-btn"
      :class="{ 'collapse-btn--flipped': collapsed }"
      @click="toggle"
      :aria-label="collapsed ? 'Ouvrir la sidebar' : 'Fermer la sidebar'"
      :title="collapsed ? 'Développer' : 'Réduire'"
    >
      <ChevronLeft :size="16" />
    </button>

  </aside>
</template>

<style scoped>
/* ── Sidebar shell ───────────────────────────────────────── */
.sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: var(--surface-raised);
  height: 100dvh;
  overflow: hidden;
  /* Sticky so it stays in view while main scrolls */
  position: sticky;
  top: 0;
}

/* Subtle right border */
.sidebar::after {
  content: '';
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 1px;
  background-color: var(--border-subtle);
}

/* ── Shared: sidebar label (fades out on collapse) ───────── */
.sidebar-label {
  overflow: hidden;
  white-space: nowrap;
  opacity: 1;
  max-width: 180px;
  flex-shrink: 0;
  transition:
    max-width 320ms cubic-bezier(0.25, 1, 0.5, 1),
    opacity 200ms ease;
}

.sidebar--collapsed .sidebar-label {
  max-width: 0;
  opacity: 0;
}

/* ── Logo ────────────────────────────────────────────────── */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-6) var(--sp-4);
  height: 56px;
}

.logo-mark {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: -0.01em;
  flex-shrink: 0;
  line-height: 1;
}

.logo-name {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

/* ── Navigation ──────────────────────────────────────────── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-4) var(--sp-2);
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
}

/* Group heading */
.nav-group-head {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-2) var(--sp-2);
}

.nav-group-text {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.nav-group-sep {
  flex: 1;
  height: 1px;
  background-color: var(--border-subtle);
  opacity: 0;
  transition: opacity 200ms ease;
}

.sidebar--collapsed .nav-group-sep {
  opacity: 1;
}

/* Nav items */
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--text-secondary);
  transition:
    background-color 150ms ease,
    color 150ms ease;
  min-height: 40px;
  position: relative;
}

.nav-item:hover {
  background-color: var(--surface-overlay);
  color: var(--text-primary);
}

.nav-item--active {
  background-color: var(--accent-surface);
  color: var(--accent);
}

.nav-item--active .nav-icon {
  color: var(--accent);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 22px;
}

.nav-label {
  font-size: var(--text-sm);
  font-weight: 500;
}

/* Tooltip when collapsed */
.sidebar--collapsed .nav-item[data-tooltip]:hover::before {
  content: attr(data-tooltip);
  position: fixed;
  left: 72px;
  background-color: var(--surface-muted);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 500;
  padding: var(--sp-2) var(--sp-3);
  border-radius: var(--radius-sm);
  white-space: nowrap;
  pointer-events: none;
  z-index: var(--z-tooltip);
  box-shadow: 0 4px 16px oklch(0% 0 0 / 0.4);
}

/* ── Spacer ──────────────────────────────────────────────── */
.sidebar-spacer { flex: 1; }

/* ── User profile ────────────────────────────────────────── */
.sidebar-user {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4);
  overflow: hidden;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background-color: var(--accent-surface);
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: 0.03em;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-logout {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  padding: 0;
  transition: color 150ms ease;
}

.user-logout:hover { color: var(--error); }

/* ── Collapse button ─────────────────────────────────────── */
.collapse-btn {
  position: absolute;
  top: 16px;
  right: -12px;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition:
    transform 320ms cubic-bezier(0.25, 1, 0.5, 1),
    color 150ms ease,
    background-color 150ms ease;
}

.collapse-btn:hover {
  background-color: var(--surface-muted);
  color: var(--accent);
}

.collapse-btn--flipped {
  transform: rotate(180deg);
}

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .sidebar-label,
  .collapse-btn,
  .nav-group-sep { transition-duration: 0.01ms !important; }
}
</style>
