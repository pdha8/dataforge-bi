<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  Bookmark, Search, RefreshCcw, Trash2, ExternalLink,
  BarChart2, LayoutGrid, Target, FileText, X,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
type FavoriteType = 'dashboard' | 'kpi' | 'report' | 'visualization'

interface Favorite {
  id: string
  content_type: string
  object_id: string
  item_name: string
  item_type: FavoriteType
  created_at: string
}

// ── Type metadata ──────────────────────────────────────────
const TYPE_META: Record<string, { label: string; icon: any; color: string; route: string }> = {
  dashboard:     { label: 'Tableau de bord', icon: LayoutGrid, color: 'oklch(62% 0.13 240)', route: '/dashboards' },
  kpi:           { label: 'KPI',             icon: Target,     color: 'oklch(76% 0.14 62)',  route: '/kpis' },
  report:        { label: 'Rapport',         icon: FileText,   color: 'oklch(65% 0.13 148)', route: '/reports' },
  visualization: { label: 'Visualisation',   icon: BarChart2,  color: 'oklch(68% 0.12 290)', route: '/visualizations' },
}

function typeMeta(t: string) {
  return TYPE_META[t] ?? { label: t, icon: Bookmark, color: 'var(--text-muted)', route: '/' }
}

// ── State ──────────────────────────────────────────────────
const favorites    = ref<Favorite[]>([])
const loading      = ref(true)
const refreshing   = ref(false)
const listVisible  = ref(false)
const searchQuery  = ref('')
const filterType   = ref<FavoriteType | 'all'>('all')
const removingId   = ref<string | null>(null)

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return favorites.value.filter(f => {
    const matchSearch = !q || f.item_name.toLowerCase().includes(q)
    const matchType   = filterType.value === 'all' || f.item_type === filterType.value
    return matchSearch && matchType
  })
})

const stats = computed(() => ({
  total:         favorites.value.length,
  dashboards:    favorites.value.filter(f => f.item_type === 'dashboard').length,
  kpis:          favorites.value.filter(f => f.item_type === 'kpi').length,
  reports:       favorites.value.filter(f => f.item_type === 'report').length,
  visualizations:favorites.value.filter(f => f.item_type === 'visualization').length,
}))

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

// ── API ────────────────────────────────────────────────────
async function fetchFavorites() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/visualizations/favorites/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    favorites.value = rows.map((f: any): Favorite => {
      // The API returns separate FK fields (dashboard, kpi, report) and their names
      let item_type: FavoriteType = 'visualization'
      let item_name = f.item_name || f.name || ''
      if (f.dashboard != null) {
        item_type = 'dashboard'
        item_name = item_name || f.dashboard_name || `Tableau de bord #${f.dashboard}`
      } else if (f.kpi != null) {
        item_type = 'kpi'
        item_name = item_name || f.kpi_name || `KPI #${f.kpi}`
      } else if (f.report != null) {
        item_type = 'report'
        item_name = item_name || f.report_name || `Rapport #${f.report}`
      }
      return {
        id:           String(f.id),
        content_type: item_type,
        object_id:    String(f.dashboard ?? f.kpi ?? f.report ?? f.id),
        item_name:    item_name || `Élément #${f.id}`,
        item_type,
        created_at:   f.created_at || new Date().toISOString(),
      }
    })
  } catch {
    favorites.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function removeFavorite(id: string) {
  removingId.value = id
  try {
    await api.delete(`/api/visualizations/favorites/${id}/`)
    favorites.value = favorites.value.filter(f => f.id !== id)
  } catch { /* ignore */ } finally {
    removingId.value = null
  }
}

async function refresh() {
  refreshing.value = true
  await fetchFavorites()
  refreshing.value = false
}

onMounted(fetchFavorites)
</script>

<template>
  <div class="fav-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Favoris</h2>
        <p class="page-meta">{{ stats.total }} élément{{ stats.total !== 1 ? 's' : '' }} en favoris</p>
      </div>
      <button
        class="btn-ghost btn-icon"
        :class="{ 'btn-icon--spin': refreshing }"
        :disabled="refreshing"
        title="Actualiser"
        @click="refresh"
      >
        <RefreshCcw :size="14" />
      </button>
    </header>

    <!-- ── Stats rail ──────────────────────────────────────── -->
    <section class="stats-rail">
      <div class="stat-cell">
        <Bookmark :size="15" class="sc-icon sc-icon--accent" />
        <span class="sc-val">{{ stats.total }}</span>
        <span class="sc-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <LayoutGrid :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.dashboards }}</span>
        <span class="sc-lbl">Tableaux de bord</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Target :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.kpis }}</span>
        <span class="sc-lbl">KPIs</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <FileText :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.reports }}</span>
        <span class="sc-lbl">Rapports</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <BarChart2 :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.visualizations }}</span>
        <span class="sc-lbl">Visualisations</span>
      </div>
    </section>

    <!-- ── Toolbar ─────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          type="search"
          class="search-input"
          placeholder="Rechercher dans les favoris…"
        />
      </div>
      <div class="select-wrap">
        <select v-model="filterType" class="filter-select">
          <option value="all">Tous les types</option>
          <option value="dashboard">Tableaux de bord</option>
          <option value="kpi">KPIs</option>
          <option value="report">Rapports</option>
          <option value="visualization">Visualisations</option>
        </select>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <template v-if="loading">
      <div class="fav-grid">
        <div v-for="i in 6" :key="i" class="fav-skel"></div>
      </div>
    </template>

    <!-- ── Empty ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <Bookmark :size="40" class="empty-icon" />
      <p class="empty-title">{{ favorites.length === 0 ? 'Aucun favori' : 'Aucun résultat' }}</p>
      <p class="empty-sub">
        {{ favorites.length === 0
          ? 'Ajoutez des éléments en favoris pour les retrouver ici.'
          : 'Modifiez vos filtres de recherche.' }}
      </p>
    </div>

    <!-- ── Grid ────────────────────────────────────────────── -->
    <div
      v-else
      class="fav-grid"
      :class="{ 'fav-grid--visible': listVisible }"
    >
      <article
        v-for="(fav, i) in filtered"
        :key="fav.id"
        class="fav-card"
        :style="{ '--ci': i, '--fc': typeMeta(fav.item_type).color }"
      >
        <div class="fav-card-top">
          <span class="fav-type-badge">
            <component :is="typeMeta(fav.item_type).icon" :size="11" />
            {{ typeMeta(fav.item_type).label }}
          </span>
          <button
            class="fav-remove"
            title="Retirer des favoris"
            :disabled="removingId === fav.id"
            @click="removeFavorite(fav.id)"
          >
            <span v-if="removingId === fav.id" class="fav-spinner"></span>
            <X v-else :size="13" />
          </button>
        </div>

        <h3 class="fav-name">{{ fav.item_name }}</h3>

        <div class="fav-footer">
          <span class="fav-time">Ajouté {{ timeAgo(fav.created_at) }}</span>
          <a
            :href="typeMeta(fav.item_type).route"
            class="fav-open"
            title="Ouvrir"
          >
            <ExternalLink :size="12" />
          </a>
        </div>
      </article>
    </div>

  </div>
</template>

<style scoped>
.fav-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  padding: var(--sp-8);
  min-height: 100%;
}

/* Header */
.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
.page-meta  { font-size: var(--text-sm); color: var(--text-muted); margin-top: 2px; }

/* Stats rail */
.stats-rail { display: flex; align-items: center; gap: var(--sp-4); padding: var(--sp-3) var(--sp-5); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); flex-wrap: wrap; }
.stat-sep { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.stat-cell { display: flex; align-items: center; gap: var(--sp-2); }
.sc-icon { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--accent { color: var(--accent); }
.sc-val { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.sc-lbl { font-size: var(--text-xs); color: var(--text-muted); }

/* Toolbar */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 220px; }
.search-icon { position: absolute; left: var(--sp-3); top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input { width: 100%; padding: var(--sp-2) var(--sp-3) var(--sp-2) calc(var(--sp-3) + 22px); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); }
.select-wrap { position: relative; }
.filter-select { padding: var(--sp-2) var(--sp-4) var(--sp-2) var(--sp-3); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); appearance: none; cursor: pointer; }

/* Grid */
.fav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--sp-4);
  opacity: 0; transition: opacity 300ms;
}
.fav-grid--visible { opacity: 1; }

/* Card */
.fav-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--fc, var(--accent));
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  opacity: 0; transform: translateY(4px);
  animation: fav-in 240ms var(--ease-out-quart, ease) forwards;
  animation-delay: calc(var(--ci, 0) * 30ms);
}
@keyframes fav-in { to { opacity: 1; transform: none; } }

.fav-card-top { display: flex; align-items: center; justify-content: space-between; }
.fav-type-badge {
  display: inline-flex; align-items: center; gap: var(--sp-1);
  padding: 2px var(--sp-2);
  border-radius: var(--radius-full);
  background: color-mix(in oklch, var(--fc) 15%, transparent);
  color: var(--fc, var(--accent));
  font-family: var(--font-display); font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}
.fav-remove {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: none; border: none; cursor: pointer;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  transition: color 120ms, background 120ms;
}
.fav-remove:hover { color: oklch(64% 0.19 24); background: oklch(14% 0.05 24 / 0.4); }
.fav-name {
  font-family: var(--font-display); font-size: var(--text-base); font-weight: 700;
  color: var(--text-primary);
  flex: 1;
}
.fav-footer { display: flex; align-items: center; justify-content: space-between; }
.fav-time { font-size: var(--text-xs); color: var(--text-muted); }
.fav-open {
  display: flex; align-items: center;
  color: var(--text-muted); text-decoration: none;
  transition: color 120ms;
}
.fav-open:hover { color: var(--accent); }

/* Skeleton */
.fav-skel {
  height: 110px;
  background: var(--surface-raised);
  border-radius: var(--radius-lg);
  animation: skel-pulse 1.4s ease-in-out infinite alternate;
}
@keyframes skel-pulse { from { opacity: 0.4; } to { opacity: 0.8; } }
.fav-spinner {
  display: inline-block; width: 10px; height: 10px;
  border: 2px solid currentColor; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Empty */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--sp-3); padding: var(--sp-16); text-align: center; }
.empty-icon { color: var(--text-muted); opacity: 0.4; }
.empty-title { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.empty-sub { font-size: var(--text-sm); color: var(--text-muted); }

/* Buttons */
.btn-ghost { display: inline-flex; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-3); background: transparent; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-secondary); font-family: var(--font-ui); font-size: var(--text-sm); cursor: pointer; transition: all 120ms; }
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.btn-icon { padding: var(--sp-2); }
.btn-icon--spin svg { animation: spin 1s linear infinite; }
</style>
