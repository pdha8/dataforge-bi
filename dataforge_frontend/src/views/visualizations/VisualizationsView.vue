<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  PointElement, LineElement, BarElement, ArcElement,
  ScatterController,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line, Bar, Doughnut, Scatter } from 'vue-chartjs'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import {
  Plus, Search, RefreshCcw, BarChart2, LineChart,
  PieChart, ScatterChart, Table2, AreaChart,
  Pencil, Copy, Trash2, X, ChevronDown, Eye,
  TrendingUp, Grid3x3, List, Star,
} from 'lucide-vue-next'

const auth = useAuthStore()

ChartJS.register(
  CategoryScale, LinearScale,
  PointElement, LineElement, BarElement, ArcElement,
  ScatterController,
  Title, Tooltip, Legend, Filler,
)

// ── Types ──────────────────────────────────────────────────
type ChartType = 'line' | 'area' | 'bar' | 'doughnut' | 'scatter' | 'table'
type ViewMode  = 'grid' | 'list'

interface VizPreview {
  data: any
  color: string
}

interface Visualization {
  id: string | number
  name: string
  type: ChartType
  source: string
  description?: string
  updated_at: string
  preview: VizPreview
  starred?: boolean
  dashboard_id?: string | number | null
}

/**
 * Toggle Favori d'une visualisation. Le backend stocke les favoris pour
 * dashboard/kpi/report → on ajoute la viz comme favori du DASHBOARD parent.
 * Si la viz est orpheline (pas de dashboard), on garde l'état localement.
 */
async function toggleStarViz(v: Visualization) {
  const was = !!v.starred
  v.starred = !was
  if (!v.dashboard_id) return  // viz libre → toggle local seulement
  try {
    if (!was) {
      await api.post('/api/visualizations/favorites/add/',    { item_id: v.dashboard_id, item_type: 'dashboard' })
    } else {
      await api.post('/api/visualizations/favorites/remove/', { item_id: v.dashboard_id, item_type: 'dashboard' })
    }
  } catch {
    v.starred = was
  }
}

// ── Chart preview palette ──────────────────────────────────
const C = {
  amber:   '#d4922a',
  amberFg: 'rgba(212,146,42,0.12)',
  teal:    '#2ab4a0',
  tealFg:  'rgba(42,180,160,0.10)',
  violet:  '#9b72d4',
  violetFg:'rgba(155,114,212,0.12)',
  blue:    '#4a8fd4',
  blueFg:  'rgba(74,143,212,0.11)',
  rose:    '#d4607a',
  roseFg:  'rgba(212,96,122,0.11)',
  green:   '#5cb87a',
  greenFg: 'rgba(92,184,122,0.11)',
}

// Mini preview options (no axes, no legend, no tooltips)
function miniOpts(extra: Record<string, any> = {}): any {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    elements: { point: { radius: 0 } },
    scales: {
      x: { display: false },
      y: { display: false },
    },
    ...extra,
  }
}

const miniLineOpts    = miniOpts()
const miniBarOpts     = miniOpts({ scales: { x: { display: false }, y: { display: false, beginAtZero: true } } })
const miniDonutOpts   = { responsive: true, maintainAspectRatio: false, animation: false, cutout: '60%', plugins: { legend: { display: false }, tooltip: { enabled: false } } }
const miniScatterOpts = miniOpts({ elements: { point: { radius: 3 } } })

function makeLine(color: string, fill: boolean, data: number[]): any {
  return {
    labels: data.map((_, i) => i),
    datasets: [{
      data,
      borderColor: color,
      backgroundColor: fill ? color.replace(')', ', 0.12)').replace('rgb', 'rgba') : 'transparent',
      borderWidth: 2,
      fill,
      tension: 0.4,
      pointRadius: 0,
    }],
  }
}

function makeDonut(colors: string[], data: number[]): any {
  return {
    labels: data.map((_, i) => i),
    datasets: [{
      data,
      backgroundColor: colors,
      borderWidth: 0,
      hoverOffset: 0,
    }],
  }
}

// ── Type metadata ──────────────────────────────────────────
const TYPE_META: Record<ChartType, { label: string; color: string; icon: any; abbr: string }> = {
  line:     { label: 'Courbe',            color: C.amber,  icon: LineChart,   abbr: 'LINE' },
  area:     { label: 'Aires',             color: C.blue,   icon: AreaChart,   abbr: 'AREA' },
  bar:      { label: 'Barres',            color: C.teal,   icon: BarChart2,   abbr: 'BAR'  },
  doughnut: { label: 'Circulaire',        color: C.violet, icon: PieChart,    abbr: 'PIE'  },
  scatter:  { label: 'Nuage de points',   color: C.green,  icon: ScatterChart,abbr: 'XY'   },
  table:    { label: 'Tableau',           color: C.rose,   icon: Table2,      abbr: 'TBL'  },
}

// ── State ──────────────────────────────────────────────────
const vizList        = ref<Visualization[]>([])
const loading        = ref(true)
const searchQuery    = ref('')
const filterType     = ref<ChartType | 'all'>('all')
const viewMode       = ref<ViewMode>('grid')
const drawerOpen     = ref(false)
const deleteConfirm  = ref<string | number | null>(null)
const submitting     = ref(false)
const submitError    = ref<string>('')
const listVisible    = ref(false)
const lastUpdated    = ref(new Date())
const refreshing     = ref(false)
const editViz        = ref<Visualization | null>(null)
const previewViz     = ref<Visualization | null>(null)

const form = ref({
  name: '',
  type: 'line' as ChartType,
  source: '',
  description: '',
  dashboard: '' as string,
})

// ── Dashboards lookup (pour le <select> dynamique) ─────────
interface DashboardOption { id: string | number; name: string }
const dashboardOptions = ref<DashboardOption[]>([])

async function fetchDashboardOptions() {
  try {
    const { data } = await api.get('/api/visualizations/dashboards/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    dashboardOptions.value = rows.map((d: any) => ({ id: d.id, name: d.name || d.title || `Dashboard ${d.id}` }))
  } catch {
    dashboardOptions.value = []
  }
}

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return vizList.value.filter(v => {
    const matchSearch = !q || v.name.toLowerCase().includes(q) || v.source.toLowerCase().includes(q)
    const matchType   = filterType.value === 'all' || v.type === filterType.value
    return matchSearch && matchType
  })
})

const stats = computed(() => {
  const total = vizList.value.length
  const byType = Object.fromEntries(
    Object.keys(TYPE_META).map(k => [k, vizList.value.filter(v => v.type === k).length])
  ) as Record<ChartType, number>
  return { total, byType }
})

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

function typeColor(t: ChartType): string {
  return TYPE_META[t].color
}

// ── API ────────────────────────────────────────────────────
const WIDGET_TYPE_MAP: Record<string, ChartType> = {
  chart:   'line',
  metric:  'bar',
  table:   'table',
  text:    'table',
  image:   'table',
  iframe:  'table',
  custom:  'line',
}

const PREVIEW_COLORS = [C.amber, C.teal, C.violet, C.blue, C.rose, C.green]
let _previewIdx = 0

function mapWidget(w: any): Visualization {
  const color = PREVIEW_COLORS[_previewIdx++ % PREVIEW_COLORS.length]
  const chartType = WIDGET_TYPE_MAP[w.widget_type] ?? 'line'
  return {
    id:           w.id,
    name:         w.name,
    type:         chartType,
    source:       w.dimensional_schema_name || w.dashboard_name || '',
    description:  w.description,
    updated_at:   w.updated_at,
    starred:      false,
    dashboard_id: w.dashboard || null,
    preview: {
      color,
      data: chartType === 'table'
        ? makeLine(color, false, Array.from({ length: 12 }, () => Math.round(Math.random() * 1000)))
        : chartType === 'doughnut'
          ? makeDonut([C.amber, C.teal, C.violet, C.blue, C.rose], [38, 27, 19, 10, 6])
          : makeLine(color, chartType === 'area', Array.from({ length: 12 }, () => Math.round(Math.random() * 1000))),
    },
  }
}

async function fetchViz() {
  loading.value = true
  listVisible.value = false
  _previewIdx = 0
  try {
    const { data } = await api.get('/api/visualizations/widgets/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    vizList.value = rows.map(mapWidget)
  } catch {
    vizList.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function refresh() {
  refreshing.value = true
  await fetchViz()
  lastUpdated.value = new Date()
  refreshing.value = false
}

async function deleteViz(id: string | number) {
  try { await api.delete(`/api/visualizations/widgets/${id}/`) } catch { /* ignore */ }
  vizList.value = vizList.value.filter(v => v.id !== id)
  deleteConfirm.value = null
}

function duplicateViz(v: Visualization) {
  const clone: Visualization = {
    ...v,
    id: Date.now(),
    name: `${v.name} (copie)`,
    updated_at: new Date().toISOString(),
  }
  const idx = vizList.value.findIndex(x => x.id === v.id)
  vizList.value.splice(idx + 1, 0, clone)
}

function openDrawer() {
  editViz.value = null
  submitError.value = ''
  form.value = { name: '', type: 'line', source: '', description: '', dashboard: '' }
  drawerOpen.value = true
  if (dashboardOptions.value.length === 0) fetchDashboardOptions()
}

function openEdit(viz: Visualization) {
  editViz.value = viz
  submitError.value = ''
  form.value = { name: viz.name, type: viz.type, source: viz.source, description: viz.description || '', dashboard: '' }
  drawerOpen.value = true
  if (dashboardOptions.value.length === 0) fetchDashboardOptions()
}

function openPreview(viz: Visualization) {
  previewViz.value = viz
}

async function submitForm() {
  if (!form.value.name.trim()) return
  if (!editViz.value && !form.value.dashboard) {
    submitError.value = 'Veuillez choisir un dashboard pour cette visualisation.'
    return
  }
  submitting.value = true
  submitError.value = ''
  try {
    if (editViz.value) {
      await api.patch(`/api/visualizations/widgets/${editViz.value.id}/`, {
        name:        form.value.name,
        description: form.value.description,
      })
    } else {
      await api.post('/api/visualizations/widgets/', {
        name:        form.value.name,
        widget_type: 'chart',
        description: form.value.description,
        dashboard:   form.value.dashboard,
      })
    }
    await fetchViz()
    drawerOpen.value = false
    editViz.value = null
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string; errors?: Record<string, string[] | string> } } }
    const errs = err?.response?.data?.errors
    if (errs && typeof errs === 'object') {
      submitError.value = Object.entries(errs)
        .map(([k, v]) => `${k} : ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' · ')
    } else {
      submitError.value = err?.response?.data?.message || 'Erreur lors de l\'enregistrement.'
    }
  } finally {
    submitting.value = false
  }
}

onMounted(fetchViz)
</script>

<template>
  <div class="viz-page">

    <!-- ── Page header ─────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Visualisations</h2>
        <p class="page-meta">
          {{ stats.total }} graphique{{ stats.total !== 1 ? 's' : '' }} · Mis à jour {{ timeAgo(lastUpdated.toISOString()) }}
        </p>
      </div>
      <div class="hd-actions">
        <button
          class="btn-ghost btn-icon"
          :class="{ 'btn-icon--spinning': refreshing }"
          :disabled="refreshing"
          title="Actualiser"
          @click="refresh"
        >
          <RefreshCcw :size="14" />
        </button>
        <button
          v-if="auth.canManageVisualizations"
          class="btn-primary"
          @click="openDrawer"
        >
          <Plus :size="15" />
          <span>Nouvelle visualisation</span>
        </button>
      </div>
    </header>

    <!-- ── Stats strip ─────────────────────────────────────── -->
    <section class="stats-strip" aria-label="Statistiques">
      <div class="stat-chip">
        <TrendingUp :size="13" class="stat-chip-icon" />
        <span class="stat-n">{{ stats.byType.line + stats.byType.area }}</span>
        <span class="stat-l">Courbes</span>
      </div>
      <div class="stat-chip">
        <BarChart2 :size="13" class="stat-chip-icon stat-chip-icon--bar" />
        <span class="stat-n">{{ stats.byType.bar }}</span>
        <span class="stat-l">Barres</span>
      </div>
      <div class="stat-chip">
        <PieChart :size="13" class="stat-chip-icon stat-chip-icon--pie" />
        <span class="stat-n">{{ stats.byType.doughnut }}</span>
        <span class="stat-l">Circulaires</span>
      </div>
      <div class="stat-chip">
        <ScatterChart :size="13" class="stat-chip-icon stat-chip-icon--scatter" />
        <span class="stat-n">{{ stats.byType.scatter }}</span>
        <span class="stat-l">XY</span>
      </div>
      <div class="stat-chip stat-chip--total">
        <span class="stat-n">{{ stats.total }}</span>
        <span class="stat-l">Total</span>
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
          placeholder="Rechercher une visualisation…"
        />
      </div>

      <div class="select-wrap">
        <select v-model="filterType" class="filter-select">
          <option value="all">Tous les types</option>
          <option v-for="(meta, key) in TYPE_META" :key="key" :value="key">{{ meta.label }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="view-toggle" role="group" aria-label="Mode d'affichage">
        <button
          class="view-btn"
          :class="{ 'view-btn--active': viewMode === 'grid' }"
          title="Vue grille"
          @click="viewMode = 'grid'"
        >
          <Grid3x3 :size="14" />
        </button>
        <button
          class="view-btn"
          :class="{ 'view-btn--active': viewMode === 'list' }"
          title="Vue liste"
          @click="viewMode = 'list'"
        >
          <List :size="14" />
        </button>
      </div>
    </div>

    <!-- ── Loading skeletons ───────────────────────────────── -->
    <div v-if="loading" class="viz-grid">
      <div v-for="i in 6" :key="i" class="card-skel"></div>
    </div>

    <!-- ── Empty state ─────────────────────────────────────── -->
    <div
      v-else-if="filtered.length === 0"
      class="empty-state"
    >
      <BarChart2 :size="40" class="empty-icon" />
      <p class="empty-title">Aucune visualisation trouvée</p>
      <p class="empty-sub">Modifiez vos filtres ou créez votre première visualisation.</p>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="14" />
        <span>Nouvelle visualisation</span>
      </button>
    </div>

    <!-- ── Grid view ───────────────────────────────────────── -->
    <div
      v-else-if="viewMode === 'grid'"
      class="viz-grid"
      :class="{ 'viz-grid--visible': listVisible }"
    >
      <article
        v-for="(viz, i) in filtered"
        :key="viz.id"
        class="viz-card"
        :style="{ '--card-i': i }"
      >
        <!-- Preview area -->
        <div class="card-preview">
          <div class="card-preview-inner">
            <Line
              v-if="viz.type === 'line'"
              :data="viz.preview.data"
              :options="miniLineOpts"
            />
            <Line
              v-else-if="viz.type === 'area'"
              :data="viz.preview.data"
              :options="miniLineOpts"
            />
            <Bar
              v-else-if="viz.type === 'bar'"
              :data="viz.preview.data"
              :options="miniBarOpts"
            />
            <Doughnut
              v-else-if="viz.type === 'doughnut'"
              :data="viz.preview.data"
              :options="miniDonutOpts"
            />
            <Scatter
              v-else-if="viz.type === 'scatter'"
              :data="viz.preview.data"
              :options="miniScatterOpts"
            />
            <div v-else class="preview-table-placeholder">
              <Table2 :size="32" />
              <span>Tableau</span>
            </div>
          </div>
          <!-- Hover overlay -->
          <div class="card-preview-overlay">
            <button class="overlay-btn" title="Aperçu" @click.stop="openPreview(viz)">
              <Eye :size="16" />
              <span>Ouvrir</span>
            </button>
          </div>
        </div>

        <!-- Card footer -->
        <div class="card-body">
          <div class="card-meta-top">
            <span
              class="type-badge"
              :style="{ '--tc': typeColor(viz.type) }"
            >
              <component :is="TYPE_META[viz.type].icon" :size="10" />
              {{ TYPE_META[viz.type].label }}
            </span>
            <span class="card-time">{{ timeAgo(viz.updated_at) }}</span>
          </div>

          <h3 class="card-title" :title="viz.name">{{ viz.name }}</h3>

          <p v-if="viz.description" class="card-desc">{{ viz.description }}</p>

          <p class="card-source">{{ viz.source }}</p>

          <div class="card-actions">
            <button
              class="card-btn card-btn--star"
              :class="{ 'card-btn--star-on': viz.starred }"
              :title="viz.starred ? 'Retirer des favoris' : 'Ajouter aux favoris'"
              @click="toggleStarViz(viz)"
            >
              <Star :size="13" :fill="viz.starred ? 'currentColor' : 'none'" />
            </button>
            <button
              class="card-btn"
              title="Modifier"
              @click="openEdit(viz)"
            >
              <Pencil :size="13" />
            </button>
            <button
              class="card-btn"
              title="Dupliquer"
              @click="duplicateViz(viz)"
            >
              <Copy :size="13" />
            </button>

            <template v-if="deleteConfirm === viz.id">
              <span class="del-label">Supprimer ?</span>
              <button class="card-btn card-btn--confirm-yes" @click="deleteViz(viz.id)">Oui</button>
              <button class="card-btn" @click="deleteConfirm = null">Non</button>
            </template>
            <button
              v-else
              class="card-btn card-btn--delete"
              title="Supprimer"
              @click="deleteConfirm = viz.id"
            >
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
      </article>
    </div>

    <!-- ── List view ────────────────────────────────────────── -->
    <div
      v-else
      class="viz-list"
      :class="{ 'viz-list--visible': listVisible }"
    >
      <div
        v-for="(viz, i) in filtered"
        :key="viz.id"
        class="list-row"
        :style="{ '--row-i': i }"
      >
        <!-- Type icon -->
        <div class="list-type" :style="{ '--tc': typeColor(viz.type) }">
          <component :is="TYPE_META[viz.type].icon" :size="16" />
        </div>

        <!-- Info -->
        <div class="list-info">
          <span class="list-name">{{ viz.name }}</span>
          <span v-if="viz.description" class="list-desc">{{ viz.description }}</span>
        </div>

        <!-- Type badge -->
        <span class="type-badge" :style="{ '--tc': typeColor(viz.type) }">
          {{ TYPE_META[viz.type].label }}
        </span>

        <!-- Source -->
        <span class="list-source">{{ viz.source }}</span>

        <!-- Updated -->
        <span class="list-time">{{ timeAgo(viz.updated_at) }}</span>

        <!-- Actions -->
        <div class="list-actions">
          <button class="card-btn" title="Modifier" @click="openEdit(viz)"><Pencil :size="13" /></button>
          <button class="card-btn" title="Dupliquer" @click="duplicateViz(viz)"><Copy :size="13" /></button>
          <template v-if="deleteConfirm === viz.id">
            <span class="del-label">Supprimer ?</span>
            <button class="card-btn card-btn--confirm-yes" @click="deleteViz(viz.id)">Oui</button>
            <button class="card-btn" @click="deleteConfirm = null">Non</button>
          </template>
          <button v-else class="card-btn card-btn--delete" title="Supprimer" @click="deleteConfirm = viz.id">
            <Trash2 :size="13" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── Preview modal ─────────────────────────────────────── -->
    <Transition name="modal-fade">
      <div v-if="previewViz" class="preview-modal-overlay" @click.self="previewViz = null">
        <div class="preview-modal">
          <div class="pm-hd">
            <div>
              <h3 class="pm-title">{{ previewViz.name }}</h3>
              <p v-if="previewViz.description" class="pm-desc">{{ previewViz.description }}</p>
            </div>
            <button class="drawer-close" @click="previewViz = null" aria-label="Fermer"><X :size="18" /></button>
          </div>
          <div class="pm-body">
            <Line v-if="previewViz.type === 'line'" :data="previewViz.preview.data" :options="miniLineOpts" />
            <Line v-else-if="previewViz.type === 'area'" :data="previewViz.preview.data" :options="miniLineOpts" />
            <Bar v-else-if="previewViz.type === 'bar'" :data="previewViz.preview.data" :options="miniBarOpts" />
            <Doughnut v-else-if="previewViz.type === 'doughnut'" :data="previewViz.preview.data" :options="miniDonutOpts" />
            <Scatter v-else-if="previewViz.type === 'scatter'" :data="previewViz.preview.data" :options="miniScatterOpts" />
            <div v-else class="preview-table-placeholder"><Table2 :size="48" /><span>Tableau de données</span></div>
          </div>
          <div class="pm-footer">
            <span class="pm-meta">Source : {{ previewViz.source }}</span>
            <button class="btn-ghost" @click="previewViz = null">Fermer</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── "Nouvelle visualisation" drawer ─────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Nouvelle visualisation">

          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editViz ? 'Modifier la visualisation' : 'Nouvelle visualisation' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false; editViz = null" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- Type picker -->
            <div class="form-field">
              <label class="form-label">Type de graphique</label>
              <div class="type-grid">
                <button
                  v-for="(meta, key) in TYPE_META"
                  :key="key"
                  type="button"
                  class="type-opt"
                  :class="{ 'type-opt--active': form.type === key }"
                  :style="{ '--tc': meta.color }"
                  @click="form.type = key as ChartType"
                >
                  <component :is="meta.icon" :size="20" class="type-opt-icon" />
                  <span class="type-opt-label">{{ meta.label }}</span>
                </button>
              </div>
            </div>

            <!-- Name -->
            <div class="form-field">
              <label class="form-label" for="f-name">
                Nom <span class="req">*</span>
              </label>
              <input
                id="f-name"
                v-model="form.name"
                class="form-input"
                type="text"
                placeholder="Ex : Évolution CA mensuel"
                required
              />
            </div>

            <!-- Tableau de bord (destination) — <select> dynamique branché sur /api/visualizations/dashboards/ -->
            <div class="form-field">
              <label class="form-label" for="f-dash">
                Tableau de bord <span class="opt">optionnel</span>
              </label>
              <select
                id="f-dash"
                v-model="form.dashboard"
                class="form-input"
                name="dashboard"
              >
                <option value="">— Aucun (widget libre) —</option>
                <option
                  v-for="opt in dashboardOptions"
                  :key="opt.id"
                  :value="opt.id"
                >{{ opt.name }}</option>
              </select>
            </div>

            <!-- Description -->
            <div class="form-field">
              <label class="form-label" for="f-desc">
                Description <span class="opt">optionnel</span>
              </label>
              <input
                id="f-desc"
                v-model="form.description"
                class="form-input"
                type="text"
                placeholder="Brève description…"
              />
            </div>

            <div v-if="submitError" class="viz-form-error" role="alert">
              {{ submitError }}
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false; editViz = null">Annuler</button>
              <button
                type="submit"
                class="btn-primary"
                :class="{ 'btn-primary--loading': submitting }"
                :disabled="submitting"
              >
                <span v-if="!submitting">{{ editViz ? 'Enregistrer' : 'Créer' }}</span>
                <span v-else class="spinner" aria-label="Enregistrement…"></span>
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
.viz-page {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}

.page-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}

.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background-color: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  min-height: 40px;
  white-space: nowrap;
  transition: background-color 150ms, box-shadow 150ms;
}
.btn-primary:hover:not(:disabled) {
  background-color: oklch(80% 0.14 62);
  box-shadow: var(--shadow-accent);
}
.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }
.btn-primary--loading { min-width: 90px; justify-content: center; }

.btn-ghost {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  min-height: 40px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover { border-color: var(--border-strong); color: var(--text-primary); }

.btn-icon { padding: var(--sp-2); min-height: unset; width: 40px; height: 40px; justify-content: center; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-icon--spinning svg { animation: spin 0.7s linear infinite; }

/* ── Stats strip ─────────────────────────────────────────── */
.stats-strip {
  display: flex;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
}

.stat-chip-icon { color: var(--accent-dim); flex-shrink: 0; }
.stat-chip-icon--bar    { color: oklch(65% 0.13 148); }
.stat-chip-icon--pie    { color: oklch(65% 0.12 290); }
.stat-chip-icon--scatter{ color: oklch(65% 0.14 148); }

.stat-chip--total {
  background: var(--accent-surface);
  border-color: var(--accent-deep);
  margin-left: auto;
}

.stat-n {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-chip--total .stat-n { color: var(--accent); }

.stat-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
}

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 360px;
}

.search-icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 var(--sp-4) 0 34px;
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }

.filter-select {
  appearance: none;
  height: 40px;
  padding: 0 30px 0 var(--sp-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms;
}
.filter-select:focus { border-color: var(--accent-dim); }
.filter-select option { background: var(--surface-raised); }

.select-arrow {
  position: absolute;
  right: 9px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.view-toggle {
  display: flex;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.view-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 100ms, color 100ms;
}
.view-btn:hover { color: var(--text-primary); background: var(--surface-overlay); }
.view-btn--active { color: var(--accent); background: var(--accent-surface); }
.view-btn + .view-btn { border-left: 1px solid var(--border-default); }

/* ── Grid ────────────────────────────────────────────────── */
.viz-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-5);
  opacity: 0;
  transition: opacity 300ms ease;
}
.viz-grid--visible { opacity: 1; }

/* ── Card ────────────────────────────────────────────────── */
.viz-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color 200ms, box-shadow 200ms;

  opacity: 0;
  transform: translateY(8px);
  animation: card-in 320ms var(--ease-out-expo) forwards;
  animation-delay: calc(var(--card-i, 0) * 35ms);
}

@keyframes card-in {
  to { opacity: 1; transform: translateY(0); }
}

.viz-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 8px 32px oklch(5% 0.01 258 / 0.4);
}

/* Preview */
.card-preview {
  position: relative;
  height: 140px;
  background: var(--surface-base);
  padding: var(--sp-4);
  overflow: hidden;
}

.card-preview-inner {
  width: 100%;
  height: 100%;
  position: relative;
}

/* Hover overlay */
.card-preview-overlay {
  position: absolute;
  inset: 0;
  background: oklch(8% 0.01 258 / 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 200ms ease;
}

.viz-card:hover .card-preview-overlay { opacity: 1; }

.overlay-btn {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms;
}
.overlay-btn:hover { background: oklch(80% 0.14 62); }

/* Table placeholder */
.preview-table-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  color: var(--text-muted);
  font-size: var(--text-xs);
}

/* Card body */
.card-body {
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  flex: 1;
}

.card-meta-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
}

.card-time {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
}

.card-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-source {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: 'Barlow Condensed', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: auto;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border-subtle);
  margin-top: var(--sp-1);
}

/* ── Shared card action btn ──────────────────────────────── */
.card-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  transition: all 120ms;
}
.card-btn:hover:not(:disabled) {
  background: var(--surface-overlay);
  border-color: var(--border-default);
  color: var(--text-secondary);
}
.card-btn--delete:hover:not(:disabled) {
  background: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}
.card-btn--confirm-yes {
  background: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
  width: auto;
  padding: 0 var(--sp-2);
}
.del-label {
  font-size: var(--text-xs);
  color: var(--error);
  margin-left: auto;
  white-space: nowrap;
}

/* ── Type badge ──────────────────────────────────────────── */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: color-mix(in oklch, var(--tc) 14%, oklch(10% 0.013 258));
  color: var(--tc);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.card-skel {
  height: 240px;
  border-radius: var(--radius-lg);
  background: linear-gradient(
    90deg,
    var(--surface-raised)  25%,
    var(--surface-overlay) 50%,
    var(--surface-raised)  75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* ── List view ───────────────────────────────────────────── */
.viz-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  opacity: 0;
  transition: opacity 300ms;
}
.viz-list--visible { opacity: 1; }

.list-row {
  display: grid;
  grid-template-columns: 36px 1fr auto auto 100px auto;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-5);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: background 120ms, border-color 120ms;

  opacity: 0;
  transform: translateY(4px);
  animation: card-in 260ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--row-i, 0) * 30ms);
}
.list-row:hover {
  background: var(--surface-overlay);
  border-color: var(--border-default);
}

.list-type {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: color-mix(in oklch, var(--tc) 14%, oklch(10% 0.013 258));
  color: var(--tc);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.list-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.list-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-desc {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-source {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: 'Barlow Condensed', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.list-time {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  text-align: right;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

/* ── Empty state ─────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-24) var(--sp-8);
  text-align: center;
}

.empty-icon { color: var(--text-muted); margin-bottom: var(--sp-2); }

.empty-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-secondary);
}

.empty-sub {
  font-size: var(--text-sm);
  color: var(--text-muted);
  max-width: 40ch;
  line-height: 1.6;
}

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0.01 258 / 0.72);
  z-index: var(--z-modal);
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 440px;
  max-width: 100vw;
  height: 100dvh;
  background: var(--surface-raised);
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.drawer-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  background: var(--surface-raised);
  z-index: 1;
}

.drawer-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.drawer-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms;
}
.drawer-close:hover { border-color: var(--border-strong); color: var(--text-primary); }

.drawer-form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  padding: var(--sp-6);
  flex: 1;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
}

.req { color: var(--accent-dim); }
.opt { font-size: var(--text-xs); font-weight: 400; color: var(--text-muted); margin-left: 4px; }

.form-input {
  height: 40px;
  padding: 0 var(--sp-4);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms;
}
.form-input:focus { border-color: var(--accent-dim); box-shadow: var(--shadow-focus); }
.form-input::placeholder { color: var(--text-muted); }

/* Type picker grid */
.type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-2);
}

.type-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none;
  cursor: pointer;
  transition: all 150ms;
}
.type-opt:hover { background: var(--surface-overlay); border-color: var(--border-strong); }
.type-opt--active {
  border-color: var(--tc);
  background: color-mix(in oklch, var(--tc) 11%, oklch(10% 0.013 258));
}

.type-opt-icon { color: var(--tc); }
.type-opt--active .type-opt-icon { color: var(--tc); }

.type-opt-label {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
}
.type-opt--active .type-opt-label { color: color-mix(in oklch, var(--tc) 70%, var(--text-muted)); }

.drawer-footer {
  display: flex;
  gap: var(--sp-3);
  justify-content: flex-end;
  padding-top: var(--sp-4);
  margin-top: auto;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.viz-form-error {
  margin-top: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: color-mix(in oklab, var(--danger, #dc2626) 12%, transparent);
  border: 1px solid color-mix(in oklab, var(--danger, #dc2626) 35%, transparent);
  border-radius: var(--radius-md);
  color: var(--danger, #dc2626);
  font-size: 13px;
  word-break: break-word;
}

@keyframes spin-sm { to { transform: rotate(360deg); } }
.spinner {
  display: block;
  width: 16px;
  height: 16px;
  border: 2px solid oklch(14% 0.013 258 / 0.3);
  border-top-color: var(--text-on-accent);
  border-radius: 50%;
  animation: spin-sm 0.7s linear infinite;
}

/* ── Preview modal ───────────────────────────────────────── */
.preview-modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0.01 258 / 0.80);
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-6);
}

.preview-modal {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pm-hd {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  gap: var(--sp-4);
}

.pm-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.pm-desc {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}

.pm-body {
  flex: 1;
  padding: var(--sp-6);
  position: relative;
  min-height: 320px;
}

.pm-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--border-subtle);
}

.pm-meta {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: 'Barlow Condensed', monospace;
}

.modal-fade-enter-active { transition: all 200ms var(--ease-out-expo); }
.modal-fade-leave-active { transition: all 150ms ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .preview-modal { transform: scale(0.96); }

/* Drawer transition */
.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from,
.drawer-anim-leave-to { opacity: 0; }
.drawer-anim-enter-active .drawer { transition: transform 380ms var(--ease-out-expo); }
.drawer-anim-leave-active .drawer { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer,
.drawer-anim-leave-to .drawer { transform: translateX(100%); }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .viz-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 900px) {
  .viz-page { padding: var(--sp-6); gap: var(--sp-4); }
  .viz-grid { grid-template-columns: 1fr; }
  .toolbar  { flex-wrap: wrap; }
  .search-wrap { max-width: 100%; }
  .stat-chip--total { margin-left: 0; }

  .list-row { grid-template-columns: 36px 1fr auto auto; }
  .list-source { display: none; }
  .list-time { display: none; }
}

@media (max-width: 580px) {
  .viz-page { padding: var(--sp-4); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .viz-card, .list-row { animation: none; opacity: 1; transform: none; }
  .card-skel { animation: none; }
}
</style>
