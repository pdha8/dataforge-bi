import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore, type UserRole } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    requiresRole?: UserRole[] | UserRole
    requiresPermission?:
      | 'canManageDataSources'
      | 'canManageETL'
      | 'canManageWarehouse'
      | 'canManageDashboards'
      | 'canManageKPIs'
      | 'canManageVisualizations'
      | 'canAccessAdmin'
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresGuest: true },
  },

  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },

      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/dashboard/DashboardView.vue') },
      { path: 'sources', name: 'sources', component: () => import('@/views/sources/SourcesView.vue') },
      { path: 'pipelines', name: 'pipelines', component: () => import('@/views/pipelines/PipelinesView.vue'), meta: { requiresPermission: 'canManageETL' } },
      { path: 'warehouse', name: 'warehouse', component: () => import('@/views/warehouse/WarehouseView.vue') },
      { path: 'visualizations', name: 'visualizations', component: () => import('@/views/visualizations/VisualizationsView.vue') },
      { path: 'dashboards', name: 'dashboards', component: () => import('@/views/dashboards/DashboardsView.vue') },
      { path: 'kpis', name: 'kpis', component: () => import('@/views/kpis/KpisView.vue') },
      { path: 'reports', name: 'reports', component: () => import('@/views/reports/ReportsView.vue') },
      { path: 'notifications', name: 'notifications', component: () => import('@/views/notifications/NotificationsView.vue') },
      { path: 'executions', name: 'executions', component: () => import('@/views/executions/ExecutionsView.vue') },
      { path: 'star-schema', name: 'star-schema', component: () => import('@/views/star-schema/StarSchemaView.vue'), meta: { requiresPermission: 'canManageWarehouse' } },
      { path: 'ml-analytics', name: 'ml-analytics', component: () => import('@/views/ml-analytics/MlAnalyticsView.vue') },
      { path: 'power-queries', name: 'power-queries', component: () => import('@/views/sources/PowerQueriesView.vue') },
      { path: 'queries', name: 'queries', component: () => import('@/views/sources/QueriesView.vue') },
      { path: 'sources/monitoring', name: 'source-monitoring', component: () => import('@/views/sources/SourceMonitoringView.vue') },
      { path: 'sources/files', name: 'source-files', component: () => import('@/views/sources/FilesView.vue') },
      { path: 'sources/connections', name: 'source-connections', component: () => import('@/views/sources/ConnectionsView.vue') },
      { path: 'favorites', name: 'favorites', component: () => import('@/views/favorites/FavoritesView.vue') },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/admin/AdminView.vue'),
        meta: { requiresRole: ['superadmin', 'admin'], requiresPermission: 'canAccessAdmin' },
      },
      { path: 'profile', name: 'profile', component: () => import('@/views/profile/ProfileView.vue') },
    ],
  },

  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  // ⚠️ Mode hash : URLs deviennent /#/dashboard au lieu de /dashboard.
  // Bulletproof contre F5/refresh sur Render (le serveur ne voit plus que /).
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }

  if (to.meta.requiresGuest && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresRole && auth.isAuthenticated) {
    const allowed = Array.isArray(to.meta.requiresRole) ? to.meta.requiresRole : [to.meta.requiresRole]
    if (!allowed.includes(auth.role as UserRole)) {
      return { name: 'dashboard' }
    }
  }

  if (to.meta.requiresPermission && auth.isAuthenticated) {
    const perm = to.meta.requiresPermission
    const allowed = (auth as unknown as Record<string, boolean>)[perm]
    if (allowed === false) {
      return { name: 'dashboard' }
    }
  }
})

export default router
