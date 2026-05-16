<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  PointElement, LineElement, Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import {
  Plus, Search, TrendingUp, TrendingDown, Minus,
  Target, AlertTriangle, CheckCircle2, XCircle,
  RefreshCcw, Pencil, Trash2, X, ChevronDown,
  Layers, LayoutGrid, List, Calculator, Star,
} from 'lucide-vue-next'

const auth = useAuthStore()

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler)

// ── Types ──────────────────────────────────────────────────
type KpiDomain   = 'ventes' | 'finance' | 'logistique' | 'rh' | 'technique'
type ViewMode    = 'grid' | 'list'
type GroupMode   = 'flat' | 'domain'

interface KpiDef {
  id: string | number
  name: string
  domain: string
  value: number
  target: number
  unit: string
  trend_dir: string
  trend_pct: number
  status: string
  sparkline: number[]
  updated_at: string
  description?: string
  warning_threshold?: number | null
  critical_threshold?: number | null
  format_string?: string | null
  starred?: boolean
}

async function toggleStarKpi(k: KpiDef) {
  const was = !!k.starred
  k.starred = !was
  try {
    if (!was) {
      await api.post('/api/visualizations/favorites/add/',    { item_id: k.id, item_type: 'kpi' })
    } else {
      await api.post('/api/visualizations/favorites/remove/', { item_id: k.id, item_type: 'kpi' })
    }
  } catch {
    k.starred = was
  }
}

// ── Domain metadata ────────────────────────────────────────
const DOMAIN_META: Record<string, { label: string; color: string }> = {
  ventes:     { label: 'Ventes',      color: 'oklch(76% 0.14 62)'  },
  finance:    { label: 'Finance',     color: 'oklch(65% 0.13 148)' },
  logistique: { label: 'Logistique',  color: 'oklch(60% 0.12 258)' },
  rh:         { label: 'RH',          color: 'oklch(68% 0.12 290)' },
  technique:  { label: 'Technique',   color: 'oklch(64% 0.19 24)'  },
  number:     { label: 'Nombre',      color: 'oklch(62% 0.12 258)' },
  percentage: { label: 'Pourcentage', color: 'oklch(76% 0.14 62)'  },
  currency:   { label: 'Devise',      color: 'oklch(65% 0.13 148)' },
  ratio:      { label: 'Ratio',       color: 'oklch(68% 0.12 290)' },
  trend:      { label: 'Tendance',    color: 'oklch(60% 0.16 155)' },
  comparison: { label: 'Comparaison', color: 'oklch(64% 0.19 24)'  },
}

// ── Status metadata ────────────────────────────────────────
const STATUS_META: Record<string, { label: string; icon: any; cls: string }> = {
  achieved: { label: 'Atteint',   icon: CheckCircle2,  cls: 'st--achieved' },
  on_track: { label: 'En cours',  icon: TrendingUp,    cls: 'st--on-track' },
  at_risk:  { label: 'À risque',  icon: AlertTriangle, cls: 'st--at-risk'  },
  critical: { label: 'Critique',  icon: XCircle,       cls: 'st--critical' },
  success:  { label: 'Atteint',   icon: CheckCircle2,  cls: 'st--achieved' },
  warning:  { label: 'À risque',  icon: AlertTriangle, cls: 'st--at-risk'  },
}

// ── Sparkline helpers ──────────────────────────────────────
function sparkData(values: number[], color: string, fill: boolean) {
  return {
    labels: values.map((_, i) => i),
    datasets: [{
      data: values,
      borderColor: color,
      backgroundColor: fill ? color.replace(/oklch\((.+)\)/, 'oklch($1 / 0.12)') : 'transparent',
      borderWidth: 1.5,
      fill,
      tension: 0.4,
      pointRadius: 0,
    }],
  }
}

const sparkOpts = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  elements: { point: { radius: 0 } },
  scales: { x: { display: false }, y: { display: false } },
}

// ── State ──────────────────────────────────────────────────
const kpis          = ref<KpiDef[]>([])
const loading       = ref(true)
const listVisible   = ref(false)
const searchQuery   = ref('')
const filterDomain  = ref('all')
const filterStatus  = ref('all')
const viewMode      = ref<ViewMode>('grid')
const groupMode     = ref<GroupMode>('flat')
const drawerOpen    = ref(false)
const deleteConfirm = ref<string | number | null>(null)
const submitting    = ref(false)
const refreshing    = ref(false)
const lastUpdated   = ref(new Date())
const editKpi       = ref<KpiDef | null>(null)

const form = ref({
  name: '', domain: 'number' as string,
  value: '', target: '', unit: '', description: '',
  warning_threshold: '', critical_threshold: '',
  formula: '', format_string: '', decimal_places: '2',
  track_trend: false, trend_period: 'monthly',
  dimensional_schema: '' as string,
  measure: '' as string,
})

// ── Lookup data for pickers ────────────────────────────────
interface SchemaOption { id: string; name: string }
interface MeasureOption { id: string; name: string; fact_table_name?: string }
const schemaOptions  = ref<SchemaOption[]>([])
const measureOptions = ref<MeasureOption[]>([])

async function fetchPickerData() {
  try {
    const [schRes, msRes] = await Promise.all([
      api.get('/api/star-schema/dimensional-schemas/', { params: { per_page: 200 } }),
      api.get('/api/data-warehouse/measures/', { params: { per_page: 200 } }),
    ])
    const schRows = Array.isArray(schRes.data?.results) ? schRes.data.results : Array.isArray(schRes.data) ? schRes.data : []
    schemaOptions.value = schRows.map((s: any) => ({ id: s.id, name: s.name }))

    const msRows = Array.isArray(msRes.data?.results) ? msRes.data.results : Array.isArray(msRes.data) ? msRes.data : []
    measureOptions.value = msRows.map((m: any) => ({ id: m.id, name: m.name, fact_table_name: m.fact_table_name || undefined }))
  } catch { /* ignore */ }
}

// ── Filter tabs ────────────────────────────────────────────
type ActiveFilter = 'all' | 'critical' | 'warning'
const activeFilter  = ref<ActiveFilter>('all')
const calculatingId = ref<string | number | null>(null)

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return kpis.value.filter(k => {
    const matchSearch = !q || k.name.toLowerCase().includes(q) || k.description?.toLowerCase().includes(q)
    const matchDomain = filterDomain.value === 'all' || k.domain === filterDomain.value
    const matchStatus = filterStatus.value === 'all' || k.status === filterStatus.value
    return matchSearch && matchDomain && matchStatus
  })
})

const grouped = computed(() => {
  if (groupMode.value === 'flat') return [{ domain: null as string | null, items: filtered.value }]
  const map = new Map<string, KpiDef[]>()
  for (const k of filtered.value) {
    if (!map.has(k.domain)) map.set(k.domain, [])
    map.get(k.domain)!.push(k)
  }
  return Array.from(map.entries()).map(([domain, items]) => ({ domain, items }))
})

const stats = computed(() => ({
  total:    kpis.value.length,
  achieved: kpis.value.filter(k => k.status === 'achieved').length,
  on_track: kpis.value.filter(k => k.status === 'on_track').length,
  at_risk:  kpis.value.filter(k => k.status === 'at_risk').length,
  critical: kpis.value.filter(k => k.status === 'critical').length,
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

function fmtVal(k: KpiDef): string {
  const v = k.value
  if (k.unit === 'M€') return `${v.toFixed(2)}M€`
  if (k.unit === '%')  return `${v.toFixed(1)}%`
  if (k.unit === 'x')  return `${v.toFixed(1)}x`
  if (k.unit === 'j')  return `${v.toFixed(1)} j`
  if (k.unit === '€')  return `${v.toLocaleString('fr-FR')} €`
  return `${v}`
}

function fmtTarget(k: KpiDef): string {
  if (k.unit === 'M€') return `${k.target}M€`
  if (k.unit === '%')  return `${k.target}%`
  if (k.unit === 'x')  return `${k.target}x`
  if (k.unit === 'j')  return `${k.target} j`
  if (k.unit === '€')  return `${k.target.toLocaleString('fr-FR')} €`
  return `${k.target}`
}

function progressPct(k: KpiDef): number {
  if (!k.target) return 0
  if (k.trend_dir === 'down' && k.value > k.target) {
    return Math.min((k.target / k.value) * 100, 100)
  }
  return Math.min((k.value / k.target) * 100, 100)
}

function progressColor(k: KpiDef): string {
  const s = k.status
  if (s === 'achieved') return 'oklch(65% 0.13 148)'
  if (s === 'on_track') return 'oklch(76% 0.14 62)'
  if (s === 'at_risk')  return 'oklch(78% 0.14 80)'
  return 'oklch(64% 0.19 24)'
}

function domainColor(d: string): string {
  return (DOMAIN_META[d] ?? DOMAIN_META['number']).color
}

function trendIcon(d: string) {
  if (d === 'up')   return TrendingUp
  if (d === 'down') return TrendingDown
  return Minus
}

function trendClass(k: KpiDef): string {
  if (k.trend_dir === 'stable') return 'trend--stable'
  return k.trend_dir === 'up' ? 'trend--pos' : 'trend--neg'
}

async function deleteKpi(id: string | number) {
  try { await api.delete(`/api/visualizations/kpis/${id}/`) } catch { /* ignore */ }
  kpis.value = kpis.value.filter(k => k.id !== id)
  deleteConfirm.value = null
}

function openDrawer() {
  editKpi.value = null
  form.value = {
    name: '', domain: 'number', value: '', target: '', unit: '', description: '',
    warning_threshold: '', critical_threshold: '',
    formula: '', format_string: '', decimal_places: '2',
    track_trend: false, trend_period: 'monthly',
    dimensional_schema: '', measure: '',
  }
  drawerOpen.value = true
}

function openEdit(kpi: KpiDef) {
  editKpi.value = kpi
  form.value = {
    name: kpi.name,
    domain: kpi.domain,
    value: String(kpi.value),
    target: String(kpi.target),
    unit: kpi.unit,
    description: kpi.description || '',
    warning_threshold: '', critical_threshold: '',
    formula: '', format_string: '', decimal_places: '2',
    track_trend: false, trend_period: 'monthly',
    dimensional_schema: (kpi as any).dimensional_schema || '',
    measure: (kpi as any).measure || '',
  }
  drawerOpen.value = true
}

async function submitForm() {
  if (!form.value.name.trim() || !form.value.target) return
  submitting.value = true
  const t = parseFloat(form.value.target)
  const VALID_KPI_TYPES = ['number', 'percentage', 'currency', 'ratio', 'trend', 'comparison']
  const payload: Record<string, any> = {
    name:              form.value.name,
    kpi_type:          VALID_KPI_TYPES.includes(form.value.domain) ? form.value.domain : 'number',
    target_value:      t,
    unit:              form.value.unit,
    description:       form.value.description,
    formula:           form.value.formula || '',
    format_string:     form.value.format_string || '',
    decimal_places:    form.value.decimal_places ? parseInt(form.value.decimal_places) : 2,
    track_trend:       form.value.track_trend,
    trend_period:      form.value.trend_period,
  }
  if (form.value.warning_threshold)   payload.warning_threshold  = parseFloat(form.value.warning_threshold)
  if (form.value.critical_threshold)  payload.critical_threshold = parseFloat(form.value.critical_threshold)
  if (form.value.dimensional_schema)  payload.dimensional_schema = form.value.dimensional_schema
  if (form.value.measure)             payload.measure            = form.value.measure
  try {
    if (editKpi.value) {
      await api.patch(`/api/visualizations/kpis/${editKpi.value.id}/`, payload)
    } else {
      await api.post('/api/visualizations/kpis/', payload)
    }
    await fetchKpis()
  } catch {
    /* ignore */
  } finally {
    submitting.value = false
    drawerOpen.value = false
    editKpi.value = null
  }
}

function mapKpi(k: any): KpiDef {
  const statusMap: Record<string, string> = { success: 'achieved', warning: 'at_risk', critical: 'critical', unknown: 'on_track' }
  return {
    id:                 k.id,
    name:               k.name,
    domain:             k.kpi_type || 'number',
    value:              k.current_value ?? 0,
    target:             k.target_value ?? 1,
    unit:               k.unit || '',
    trend_dir:          k.trend_direction || 'stable',
    trend_pct:          k.trend_percentage ?? 0,
    status:             statusMap[k.status] ?? (STATUS_META[k.status] ? k.status : 'on_track'),
    sparkline:          [],
    updated_at:         k.updated_at || k.last_calculated || new Date().toISOString(),
    description:        k.description,
    warning_threshold:  k.warning_threshold ?? null,
    critical_threshold: k.critical_threshold ?? null,
    format_string:      k.format_string ?? null,
  }
}

async function fetchKpis() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/visualizations/kpis/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    kpis.value = rows.map(mapKpi)
  } catch {
    kpis.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function refresh() {
  refreshing.value = true
  await fetchKpis()
  lastUpdated.value = new Date()
  refreshing.value = false
}

async function applyFilter(filter: ActiveFilter) {
  activeFilter.value = filter
  loading.value = true
  listVisible.value = false
  try {
    let url = '/api/visualizations/kpis/'
    if (filter === 'critical') url = '/api/visualizations/kpis/critical/'
    if (filter === 'warning')  url = '/api/visualizations/kpis/warning/'
    const { data } = await api.get(url)
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    kpis.value = rows.map(mapKpi)
  } catch {
    kpis.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function calculateKpi(kpi: KpiDef) {
  calculatingId.value = kpi.id
  try {
    await api.post(`/api/visualizations/kpis/${kpi.id}/calculate/`)
    const { data } = await api.get(`/api/visualizations/kpis/${kpi.id}/`)
    const updated = mapKpi(data)
    const idx = kpis.value.findIndex(k => k.id === kpi.id)
    if (idx !== -1) kpis.value[idx] = updated
  } catch {
    /* ignore */
  } finally {
    calculatingId.value = null
  }
}

onMounted(() => { fetchKpis(); fetchPickerData() })
</script>

<template>
  <div class="kpi-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">KPIs</h2>
        <p class="page-meta">
          {{ stats.total }} indicateur{{ stats.total !== 1 ? 's' : '' }} · Mis à jour {{ timeAgo(lastUpdated.toISOString()) }}
        </p>
      </div>
      <div class="hd-actions">
        <button
          class="btn-ghost btn-icon"
          :class="{ 'btn-icon--spin': refreshing }"
          :disabled="refreshing"
          title="Actualiser"
          @click="refresh"
        >
          <RefreshCcw :size="14" />
        </button>
        <button
          v-if="auth.canManageKPIs"
          class="btn-primary"
          @click="openDrawer"
        >
          <Plus :size="15" />
          <span>Nouveau KPI</span>
        </button>
      </div>
    </header>

    <!-- ── Stats rail ──────────────────────────────────────── -->
    <section class="stats-rail" aria-label="Résumé KPIs">
      <div class="stat-cell">
        <Target :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.total }}</span>
        <span class="sc-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <CheckCircle2 :size="15" class="sc-icon sc-icon--ach" />
        <span class="sc-val sc-val--ach">{{ stats.achieved }}</span>
        <span class="sc-lbl">Atteints</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <TrendingUp :size="15" class="sc-icon sc-icon--ok" />
        <span class="sc-val sc-val--ok">{{ stats.on_track }}</span>
        <span class="sc-lbl">En cours</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <AlertTriangle :size="15" class="sc-icon sc-icon--risk" />
        <span class="sc-val sc-val--risk">{{ stats.at_risk }}</span>
        <span class="sc-lbl">À risque</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <XCircle :size="15" class="sc-icon sc-icon--crit" />
        <span class="sc-val sc-val--crit">{{ stats.critical }}</span>
        <span class="sc-lbl">Critiques</span>
      </div>
    </section>

    <!-- ── Filter tabs ───────────────────────────────────────── -->
    <div class="filter-tabs" role="tablist" aria-label="Filtrer par criticité">
      <button
        role="tab"
        class="filter-tab"
        :class="{ 'filter-tab--active': activeFilter === 'all' }"
        :aria-selected="activeFilter === 'all'"
        @click="applyFilter('all')"
      >
        <Layers :size="13" />
        Tous
        <span class="tab-count">{{ stats.total }}</span>
      </button>
      <button
        role="tab"
        class="filter-tab filter-tab--crit"
        :class="{ 'filter-tab--active': activeFilter === 'critical' }"
        :aria-selected="activeFilter === 'critical'"
        @click="applyFilter('critical')"
      >
        <XCircle :size="13" />
        Critiques
        <span class="tab-count tab-count--crit">{{ stats.critical }}</span>
      </button>
      <button
        role="tab"
        class="filter-tab filter-tab--risk"
        :class="{ 'filter-tab--active': activeFilter === 'warning' }"
        :aria-selected="activeFilter === 'warning'"
        @click="applyFilter('warning')"
      >
        <AlertTriangle :size="13" />
        En alerte
        <span class="tab-count tab-count--risk">{{ stats.at_risk }}</span>
      </button>
    </div>

    <!-- ── Toolbar ─────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          type="search"
          class="search-input"
          placeholder="Rechercher un KPI…"
        />
      </div>

      <div class="select-wrap">
        <select v-model="filterDomain" class="filter-select">
          <option value="all">Tous les domaines</option>
          <option v-for="(m, k) in DOMAIN_META" :key="k" :value="k">{{ m.label }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="select-wrap">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option v-for="(m, k) in STATUS_META" :key="k" :value="k">{{ m.label }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="view-toggle">
        <button class="view-btn" :class="{ 'view-btn--on': groupMode === 'flat' }" title="Vue plate" @click="groupMode = 'flat'">
          <LayoutGrid :size="14" />
        </button>
        <button class="view-btn" :class="{ 'view-btn--on': groupMode === 'domain' }" title="Par domaine" @click="groupMode = 'domain'">
          <Layers :size="14" />
        </button>
      </div>

      <div class="view-toggle">
        <button class="view-btn" :class="{ 'view-btn--on': viewMode === 'grid' }" title="Grille" @click="viewMode = 'grid'">
          <LayoutGrid :size="14" />
        </button>
        <button class="view-btn" :class="{ 'view-btn--on': viewMode === 'list' }" title="Liste" @click="viewMode = 'list'">
          <List :size="14" />
        </button>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <template v-if="loading">
      <div class="kpi-grid">
        <div v-for="i in 8" :key="i" class="card-skel"></div>
      </div>
    </template>

    <!-- ── Empty ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <Target :size="40" class="empty-icon" />
      <p class="empty-title">Aucun KPI trouvé</p>
      <p class="empty-sub">Modifiez vos filtres ou créez votre premier indicateur.</p>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="14" />
        <span>Nouveau KPI</span>
      </button>
    </div>

    <!-- ── Content ─────────────────────────────────────────── -->
    <template v-else>
      <div
        v-for="group in grouped"
        :key="group.domain ?? 'all'"
        class="kpi-group"
      >
        <!-- Group header (domain mode) -->
        <div v-if="group.domain" class="group-hd">
          <span class="group-dot" :style="{ background: domainColor(group.domain) }"></span>
          <span class="group-label">{{ DOMAIN_META[group.domain].label }}</span>
          <span class="group-count">{{ group.items.length }}</span>
        </div>

        <!-- ── Grid view ──────────────────────────────────── -->
        <div
          v-if="viewMode === 'grid'"
          class="kpi-grid"
          :class="{ 'kpi-grid--visible': listVisible }"
        >
          <article
            v-for="(kpi, i) in group.items"
            :key="kpi.id"
            class="kpi-card"
            :class="`kpi-card--${kpi.status}`"
            :style="{ '--ci': i }"
          >
            <!-- Card top: domain + status -->
            <div class="card-top">
              <span class="domain-badge" :style="{ '--dc': domainColor(kpi.domain) }">
                {{ DOMAIN_META[kpi.domain].label }}
              </span>
              <span class="status-chip" :class="STATUS_META[kpi.status].cls">
                <component :is="STATUS_META[kpi.status].icon" :size="10" />
                {{ STATUS_META[kpi.status].label }}
              </span>
            </div>

            <!-- KPI name -->
            <h3 class="kpi-name" :title="kpi.name">{{ kpi.name }}</h3>
            <p v-if="kpi.description" class="kpi-desc">{{ kpi.description }}</p>

            <!-- Value + trend -->
            <div class="kpi-value-row">
              <span class="kpi-value">{{ fmtVal(kpi) }}</span>
              <span class="kpi-trend" :class="trendClass(kpi)">
                <component :is="trendIcon(kpi.trend_dir)" :size="13" />
                <span v-if="kpi.trend_pct > 0">{{ kpi.trend_dir !== 'stable' ? (kpi.trend_dir === 'up' ? '+' : '−') : '' }}{{ kpi.trend_pct.toFixed(1) }}%</span>
                <span v-else>stable</span>
              </span>
            </div>

            <!-- Progress bar -->
            <div class="progress-wrap">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{
                    width: `${progressPct(kpi)}%`,
                    background: progressColor(kpi),
                  }"
                ></div>
              </div>
              <div class="progress-labels">
                <span class="prog-cur">{{ fmtVal(kpi) }}</span>
                <span class="prog-target">
                  <Target :size="9" />
                  {{ fmtTarget(kpi) }}
                </span>
              </div>
            </div>

            <!-- Sparkline -->
            <div class="sparkline-wrap">
              <Line
                :data="sparkData(kpi.sparkline, progressColor(kpi), true)"
                :options="sparkOpts"
              />
            </div>

            <!-- Footer -->
            <div class="card-footer">
              <span class="card-time">{{ timeAgo(kpi.updated_at) }}</span>
              <div class="card-actions">
                <button
                  class="act-btn act-btn--calc"
                  title="Calculer"
                  :disabled="calculatingId === kpi.id"
                  @click="calculateKpi(kpi)"
                >
                  <span v-if="calculatingId === kpi.id" class="act-spinner"></span>
                  <Calculator v-else :size="12" />
                </button>
                <button
                  class="act-btn act-btn--star"
                  :class="{ 'act-btn--star-on': kpi.starred }"
                  :title="kpi.starred ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                  @click="toggleStarKpi(kpi)"
                >
                  <Star :size="12" :fill="kpi.starred ? 'currentColor' : 'none'" />
                </button>
                <button class="act-btn" title="Modifier" @click="openEdit(kpi)"><Pencil :size="12" /></button>
                <template v-if="deleteConfirm === kpi.id">
                  <button class="act-btn act-btn--yes" @click="deleteKpi(kpi.id)">Oui</button>
                  <button class="act-btn" @click="deleteConfirm = null">Non</button>
                </template>
                <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = kpi.id">
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>
          </article>
        </div>

        <!-- ── List view ──────────────────────────────────── -->
        <div
          v-else
          class="kpi-list"
          :class="{ 'kpi-list--visible': listVisible }"
        >
          <div class="list-head">
            <span>Indicateur</span>
            <span>Domaine</span>
            <span>Valeur actuelle</span>
            <span>Objectif</span>
            <span>Progression</span>
            <span>Tendance</span>
            <span>Statut</span>
            <span>Alerte</span>
            <span>Critique</span>
            <span>Format</span>
            <span>Mis à jour</span>
            <span></span>
          </div>

          <div
            v-for="(kpi, i) in group.items"
            :key="kpi.id"
            class="list-row"
            :class="`list-row--${kpi.status}`"
            :style="{ '--ri': i }"
          >
            <!-- Name -->
            <div class="list-name-cell">
              <span class="list-name">{{ kpi.name }}</span>
              <span v-if="kpi.description" class="list-desc">{{ kpi.description }}</span>
            </div>

            <!-- Domain -->
            <span class="domain-badge" :style="{ '--dc': domainColor(kpi.domain) }">
              {{ DOMAIN_META[kpi.domain].label }}
            </span>

            <!-- Value -->
            <span class="list-value">{{ fmtVal(kpi) }}</span>

            <!-- Target -->
            <span class="list-target">{{ fmtTarget(kpi) }}</span>

            <!-- Progress -->
            <div class="list-prog">
              <div class="progress-bar progress-bar--sm">
                <div
                  class="progress-fill"
                  :style="{ width: `${progressPct(kpi)}%`, background: progressColor(kpi) }"
                ></div>
              </div>
              <span class="prog-pct">{{ progressPct(kpi).toFixed(0) }}%</span>
            </div>

            <!-- Trend -->
            <span class="list-trend" :class="trendClass(kpi)">
              <component :is="trendIcon(kpi.trend_dir)" :size="13" />
              <span v-if="kpi.trend_pct > 0">{{ kpi.trend_dir === 'up' ? '+' : kpi.trend_dir === 'down' ? '−' : '' }}{{ kpi.trend_pct.toFixed(1) }}%</span>
              <span v-else>—</span>
            </span>

            <!-- Status -->
            <span class="status-chip" :class="STATUS_META[kpi.status].cls">
              <component :is="STATUS_META[kpi.status].icon" :size="10" />
              {{ STATUS_META[kpi.status].label }}
            </span>

            <!-- Warning threshold -->
            <span class="list-threshold list-threshold--warn">
              {{ kpi.warning_threshold != null ? kpi.warning_threshold : '—' }}
            </span>

            <!-- Critical threshold -->
            <span class="list-threshold list-threshold--crit">
              {{ kpi.critical_threshold != null ? kpi.critical_threshold : '—' }}
            </span>

            <!-- Format string -->
            <span class="list-fmt">{{ kpi.format_string || '—' }}</span>

            <!-- Time -->
            <span class="list-time">{{ timeAgo(kpi.updated_at) }}</span>

            <!-- Actions -->
            <div class="list-actions">
              <button
                class="act-btn act-btn--calc"
                title="Calculer"
                :disabled="calculatingId === kpi.id"
                @click="calculateKpi(kpi)"
              >
                <span v-if="calculatingId === kpi.id" class="act-spinner"></span>
                <Calculator v-else :size="12" />
              </button>
              <button class="act-btn" title="Modifier" @click="openEdit(kpi)"><Pencil :size="12" /></button>
              <template v-if="deleteConfirm === kpi.id">
                <button class="act-btn act-btn--yes" @click="deleteKpi(kpi.id)">Oui</button>
                <button class="act-btn" @click="deleteConfirm = null">Non</button>
              </template>
              <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = kpi.id">
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Create drawer ────────────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Nouveau KPI">

          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editKpi ? 'Modifier le KPI' : 'Nouveau KPI' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false; editKpi = null" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- Domain picker -->
            <div class="form-field">
              <label class="form-label">Domaine</label>
              <div class="domain-grid">
                <button
                  v-for="(meta, key) in DOMAIN_META"
                  :key="key"
                  type="button"
                  class="domain-opt"
                  :class="{ 'domain-opt--active': form.domain === key }"
                  :style="{ '--dc': meta.color }"
                  @click="form.domain = key as KpiDomain"
                >
                  {{ meta.label }}
                </button>
              </div>
            </div>

            <!-- Name -->
            <div class="form-field">
              <label class="form-label" for="f-name">
                Nom de l'indicateur <span class="req">*</span>
              </label>
              <input
                id="f-name"
                v-model="form.name"
                class="form-input"
                type="text"
                placeholder="Ex : Taux de satisfaction client"
                required
              />
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
                placeholder="Définition courte de l'indicateur"
              />
            </div>

            <!-- Value + Target -->
            <div class="form-row-3">
              <div class="form-field">
                <label class="form-label" for="f-val">Valeur actuelle</label>
                <input id="f-val" v-model="form.value" class="form-input" type="number" step="any" placeholder="0" />
              </div>
              <div class="form-field">
                <label class="form-label" for="f-tgt">
                  Objectif <span class="req">*</span>
                </label>
                <input id="f-tgt" v-model="form.target" class="form-input" type="number" step="any" placeholder="100" required />
              </div>
              <div class="form-field">
                <label class="form-label" for="f-unit">Unité</label>
                <input id="f-unit" v-model="form.unit" class="form-input" type="text" placeholder="%, €, j…" />
              </div>
            </div>

            <!-- Thresholds -->
            <div class="form-row-3">
              <div class="form-field">
                <label class="form-label">Seuil alerte</label>
                <input v-model="form.warning_threshold" class="form-input" type="number" step="any" placeholder="80" />
              </div>
              <div class="form-field">
                <label class="form-label">Seuil critique</label>
                <input v-model="form.critical_threshold" class="form-input" type="number" step="any" placeholder="60" />
              </div>
              <div class="form-field">
                <label class="form-label">Décimales</label>
                <input v-model="form.decimal_places" class="form-input" type="number" min="0" max="6" placeholder="2" />
              </div>
            </div>

            <!-- Advanced options -->
            <details class="kpi-adv-section">
              <summary class="kpi-adv-summary">Options avancées</summary>
              <div class="kpi-adv-body">

                <div class="form-field">
                  <label class="form-label">Schéma dimensionnel <span class="opt">optionnel</span></label>
                  <div class="select-wrap">
                    <select v-model="form.dimensional_schema" class="filter-select">
                      <option value="">— Aucun —</option>
                      <option v-for="s in schemaOptions" :key="s.id" :value="s.id">{{ s.name }}</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow" />
                  </div>
                </div>

                <div class="form-field">
                  <label class="form-label">Mesure source <span class="opt">optionnel</span></label>
                  <div class="select-wrap">
                    <select v-model="form.measure" class="filter-select">
                      <option value="">— Aucune —</option>
                      <option v-for="m in measureOptions" :key="m.id" :value="m.id">
                        {{ m.fact_table_name ? `${m.fact_table_name} → ` : '' }}{{ m.name }}
                      </option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow" />
                  </div>
                </div>

                <div class="form-field">
                  <label class="form-label">Formule de calcul <span class="opt">optionnel</span></label>
                  <input v-model="form.formula" class="form-input" type="text" placeholder="Ex : sum(valeur_ventes) / count(commandes)" />
                </div>

                <div class="form-field">
                  <label class="form-label">Format d'affichage <span class="opt">optionnel</span></label>
                  <input v-model="form.format_string" class="form-input" type="text" placeholder="Ex : {value:.1f}%" />
                </div>

                <div class="kpi-adv-row">
                  <label class="toggle-label">
                    <input v-model="form.track_trend" type="checkbox" class="form-checkbox" />
                    <span>Suivre la tendance</span>
                  </label>

                  <div v-if="form.track_trend" class="form-field">
                    <label class="form-label">Période de tendance</label>
                    <div class="select-wrap">
                      <select v-model="form.trend_period" class="filter-select">
                        <option value="daily">Quotidien</option>
                        <option value="weekly">Hebdomadaire</option>
                        <option value="monthly">Mensuel</option>
                        <option value="quarterly">Trimestriel</option>
                        <option value="yearly">Annuel</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                </div>

              </div>
            </details>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false; editKpi = null">Annuler</button>
              <button
                type="submit"
                class="btn-primary"
                :class="{ 'btn-primary--loading': submitting }"
                :disabled="submitting"
              >
                <span v-if="!submitting">{{ editKpi ? 'Enregistrer' : 'Créer' }}</span>
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
.kpi-page {
  padding: var(--sp-8);
  display: flex; flex-direction: column;
  gap: var(--sp-6); min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: var(--sp-4);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl); font-weight: 700;
  letter-spacing: -0.01em; color: var(--text-primary); line-height: 1.2;
}

.page-meta { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }

.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

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
.btn-primary--loading { min-width: 80px; justify-content: center; }

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

.btn-icon { padding: var(--sp-2); min-height: unset; width: 38px; height: 38px; justify-content: center; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-icon--spin svg { animation: spin 0.7s linear infinite; }

/* ── Stats rail ──────────────────────────────────────────── */
.stats-rail {
  display: flex; align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); overflow: hidden;
}

.stat-cell {
  flex: 1; display: flex; align-items: center;
  gap: var(--sp-2); padding: var(--sp-4) var(--sp-5);
}

.stat-sep { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }

.sc-icon          { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--ach     { color: oklch(65% 0.13 148); }
.sc-icon--ok      { color: var(--accent-dim); }
.sc-icon--risk    { color: var(--warning); }
.sc-icon--crit    { color: var(--error); }

.sc-val           { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.sc-val--ach      { color: oklch(65% 0.13 148); }
.sc-val--ok       { color: var(--accent-dim); }
.sc-val--risk     { color: var(--warning); }
.sc-val--crit     { color: var(--error); }

.sc-lbl { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Filter tabs ─────────────────────────────────────────── */
.filter-tabs {
  display: flex; align-items: center; gap: var(--sp-2);
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: var(--sp-1);
}

.filter-tab {
  display: inline-flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid transparent; border-radius: var(--radius-md);
  background: none; cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-muted);
  transition: all 150ms;
  white-space: nowrap;
}
.filter-tab:hover { color: var(--text-secondary); background: var(--surface-overlay); }
.filter-tab--active {
  color: var(--text-primary);
  background: var(--surface-overlay);
  border-color: var(--border-default);
}
.filter-tab--crit.filter-tab--active { color: var(--error); border-color: var(--error); background: var(--error-surface); }
.filter-tab--risk.filter-tab--active { color: var(--warning); border-color: oklch(24% 0.06 80); background: oklch(17% 0.05 80); }

.tab-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; padding: 0 5px; height: 18px;
  background: var(--surface-muted); border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 700; color: var(--text-muted);
}
.tab-count--crit { background: var(--error-surface); color: var(--error); }
.tab-count--risk  { background: oklch(17% 0.05 80);  color: var(--warning); }

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }

.search-wrap { position: relative; flex: 1; max-width: 320px; }
.search-icon {
  position: absolute; left: 11px; top: 50%;
  transform: translateY(-50%); color: var(--text-muted); pointer-events: none;
}
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
.select-arrow {
  position: absolute; right: 9px; top: 50%;
  transform: translateY(-50%); color: var(--text-muted); pointer-events: none;
}

.view-toggle {
  display: flex; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); overflow: hidden;
}
.view-btn {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px;
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  transition: background 100ms, color 100ms;
}
.view-btn:hover { color: var(--text-primary); background: var(--surface-overlay); }
.view-btn--on { color: var(--accent); background: var(--accent-surface); }
.view-btn + .view-btn { border-left: 1px solid var(--border-default); }

/* ── Group header ────────────────────────────────────────── */
.kpi-group { display: flex; flex-direction: column; gap: var(--sp-3); }

.group-hd {
  display: flex; align-items: center; gap: var(--sp-2);
  padding-bottom: var(--sp-2);
  border-bottom: 1px solid var(--border-subtle);
}

.group-dot {
  width: 8px; height: 8px;
  border-radius: 50%; flex-shrink: 0;
}

.group-label {
  font-family: var(--font-display);
  font-size: var(--text-sm); font-weight: 700;
  letter-spacing: 0.05em; text-transform: uppercase;
  color: var(--text-secondary);
}

.group-count {
  font-size: var(--text-xs); color: var(--text-muted);
  background: var(--surface-muted);
  padding: 1px 7px; border-radius: var(--radius-full); font-weight: 600;
}

/* ── Grid ────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-4);
  opacity: 0; transition: opacity 300ms;
}
.kpi-grid--visible { opacity: 1; }

/* ── KPI Card ────────────────────────────────────────────── */
.kpi-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-3);
  transition: border-color 200ms, box-shadow 200ms;

  opacity: 0; transform: translateY(8px);
  animation: card-in 300ms var(--ease-out-expo) forwards;
  animation-delay: calc(var(--ci, 0) * 30ms);
}
@keyframes card-in { to { opacity: 1; transform: translateY(0); } }

.kpi-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 6px 24px oklch(5% 0.01 258 / 0.35);
}

.kpi-card--critical { border-color: oklch(22% 0.06 24); background: oklch(12% 0.03 24 / 0.5); }
.kpi-card--at_risk  { border-color: oklch(24% 0.06 80); }

/* Card top */
.card-top { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); }

/* Domain badge */
.domain-badge {
  display: inline-flex; align-items: center;
  padding: 2px 8px;
  background: color-mix(in oklch, var(--dc) 14%, oklch(10% 0.013 258));
  color: var(--dc);
  border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase;
  white-space: nowrap;
}

/* Status chip */
.status-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 7px;
  border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 700;
  letter-spacing: 0.03em; white-space: nowrap;
}

.st--achieved { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.st--on-track { background: var(--accent-surface);  color: var(--accent-dim); }
.st--at-risk  { background: oklch(17% 0.05 80);  color: var(--warning); }
.st--critical { background: var(--error-surface); color: var(--error); }

/* KPI name */
.kpi-name {
  font-family: var(--font-display);
  font-size: var(--text-base); font-weight: 700;
  color: var(--text-primary); letter-spacing: -0.01em; line-height: 1.3;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.kpi-desc {
  font-size: var(--text-xs); color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

/* Value + trend */
.kpi-value-row {
  display: flex; align-items: baseline;
  justify-content: space-between; gap: var(--sp-2);
}

.kpi-value {
  font-family: var(--font-display);
  font-size: 1.9rem; font-weight: 800;
  letter-spacing: -0.03em; color: var(--text-primary);
  line-height: 1;
}

.kpi-trend {
  display: flex; align-items: center; gap: 3px;
  font-size: var(--text-xs); font-weight: 700;
  white-space: nowrap;
}

.trend--pos    { color: oklch(65% 0.13 148); }
.trend--neg    { color: var(--error); }
.trend--stable { color: var(--text-muted); }

/* Progress */
.progress-wrap { display: flex; flex-direction: column; gap: var(--sp-1); }

.progress-bar {
  height: 5px;
  background: var(--surface-muted);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar--sm { height: 4px; flex: 1; }

.progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 600ms var(--ease-out-expo);
}

.progress-labels {
  display: flex; align-items: center;
  justify-content: space-between;
}

.prog-cur {
  font-size: var(--text-xs); color: var(--text-secondary); font-weight: 600;
}

.prog-target {
  display: flex; align-items: center; gap: 3px;
  font-size: var(--text-xs); color: var(--text-muted);
}

/* Sparkline */
.sparkline-wrap {
  height: 44px;
  position: relative;
  margin: 0 calc(-1 * var(--sp-1));
}

/* Card footer */
.card-footer {
  display: flex; align-items: center;
  justify-content: space-between;
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border-subtle);
}

.card-time { font-size: var(--text-xs); color: var(--text-muted); }

.card-actions { display: flex; align-items: center; gap: var(--sp-1); }

/* ── Action btn ──────────────────────────────────────────── */
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none;
  color: var(--text-muted); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) {
  background: var(--surface-overlay); border-color: var(--border-default); color: var(--text-secondary);
}
.act-btn--del:hover:not(:disabled) {
  background: var(--error-surface); border-color: var(--error); color: var(--error);
}
.act-btn--yes {
  background: var(--error-surface); border-color: var(--error); color: var(--error);
  width: auto; padding: 0 var(--sp-2);
}
.act-btn--calc:hover:not(:disabled) {
  background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent);
}
.act-btn:disabled { opacity: 0.55; cursor: not-allowed; }

@keyframes act-spin { to { transform: rotate(360deg); } }
.act-spinner {
  display: block; width: 10px; height: 10px;
  border: 1.5px solid var(--border-default);
  border-top-color: var(--accent-dim);
  border-radius: 50%;
  animation: act-spin 0.7s linear infinite;
}

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.card-skel {
  height: 220px; border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
.card-skel:nth-child(2) { animation-delay: 0.07s; }
.card-skel:nth-child(3) { animation-delay: 0.14s; }
.card-skel:nth-child(4) { animation-delay: 0.21s; }
.card-skel:nth-child(5) { animation-delay: 0.28s; }

/* ── List view ───────────────────────────────────────────── */
.kpi-list {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  opacity: 0; transition: opacity 300ms;
}
.kpi-list--visible { opacity: 1; }

.list-head {
  display: grid;
  grid-template-columns: 1fr 90px 100px 90px 140px 90px 90px 72px 72px 80px 90px 90px;
  padding: var(--sp-2) var(--sp-5);
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-display);
  font-size: 0.67rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase;
  color: var(--text-muted);
}

.list-row {
  display: grid;
  grid-template-columns: 1fr 90px 100px 90px 140px 90px 90px 72px 72px 80px 90px 90px;
  align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;

  opacity: 0; transform: translateY(3px);
  animation: card-in 240ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--ri, 0) * 25ms);
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: var(--surface-overlay); }
.list-row--critical { background: oklch(12% 0.03 24 / 0.4); }
.list-row--at_risk  { background: oklch(12% 0.02 80 / 0.3); }

.list-name-cell { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.list-name { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.list-desc { font-size: var(--text-xs); color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.list-value {
  font-family: var(--font-display);
  font-size: var(--text-base); font-weight: 700;
  color: var(--text-primary); letter-spacing: -0.01em;
}

.list-target { font-size: var(--text-sm); color: var(--text-muted); }

.list-prog { display: flex; align-items: center; gap: var(--sp-2); }
.prog-pct  { font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; white-space: nowrap; }

.list-trend {
  display: flex; align-items: center; gap: 3px;
  font-size: var(--text-xs); font-weight: 700;
}

.list-time    { font-size: var(--text-xs); color: var(--text-muted); }
.list-threshold { font-size: var(--text-xs); font-variant-numeric: tabular-nums; }
.list-threshold--warn { color: oklch(78% 0.14 80); }
.list-threshold--crit { color: oklch(64% 0.19 24); }
.list-fmt { font-size: var(--text-xs); color: var(--text-muted); font-family: var(--font-mono, monospace); }

.list-actions { display: flex; align-items: center; gap: var(--sp-1); justify-content: flex-end; }

/* ── Empty state ─────────────────────────────────────────── */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--sp-4); padding: var(--sp-24) var(--sp-8); text-align: center;
}
.empty-icon { color: var(--text-muted); margin-bottom: var(--sp-2); }
.empty-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.empty-sub { font-size: var(--text-sm); color: var(--text-muted); max-width: 40ch; line-height: 1.6; }

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed; inset: 0;
  background: oklch(5% 0.01 258 / 0.72);
  z-index: var(--z-modal); display: flex; justify-content: flex-end;
}

.drawer {
  width: 440px; max-width: 100vw; height: 100dvh;
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
.form-label  { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.req  { color: var(--accent-dim); }
.opt  { font-size: var(--text-xs); font-weight: 400; color: var(--text-muted); margin-left: 4px; }

.form-input {
  height: 40px; padding: 0 var(--sp-4);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default); border-radius: var(--radius-md);
  color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.form-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }
.form-input::placeholder { color: var(--text-muted); }

.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 80px; gap: var(--sp-3); align-items: end; }

/* Domain picker */
.domain-grid { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.domain-opt {
  padding: 5px 14px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: none; cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  color: var(--text-muted);
  transition: all 150ms;
}
.domain-opt:hover { border-color: var(--border-strong); color: var(--text-secondary); }
.domain-opt--active {
  border-color: var(--dc);
  background: color-mix(in oklch, var(--dc) 12%, oklch(10% 0.013 258));
  color: var(--dc);
}

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

/* ── KPI Advanced section ────────────────────────────────── */
.kpi-adv-section { border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; }
.kpi-adv-summary {
  padding: var(--sp-3) var(--sp-4);
  font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary);
  cursor: pointer; list-style: none; display: flex; align-items: center;
  background: var(--surface-overlay);
}
.kpi-adv-summary::-webkit-details-marker { display: none; }
.kpi-adv-summary::after { content: ' ›'; color: var(--text-muted); transition: transform 200ms; }
details[open] .kpi-adv-summary::after { content: ' ‹'; }
.kpi-adv-body { padding: var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-4); }
.kpi-adv-row { display: flex; flex-direction: column; gap: var(--sp-3); }
.form-checkbox { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
.toggle-label { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--text-sm); color: var(--text-secondary); cursor: pointer; }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1400px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 1100px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .list-head, .list-row { grid-template-columns: 1fr 80px 90px 80px 120px 80px 80px 80px; }
  .list-head span:nth-child(4), .list-row .list-target { display: none; }
  .list-head span:nth-child(8), .list-head span:nth-child(9), .list-head span:nth-child(10),
  .list-row .list-threshold, .list-row .list-fmt { display: none; }
}
@media (max-width: 900px) {
  .kpi-page { padding: var(--sp-6); gap: var(--sp-4); }
  .stats-rail { flex-wrap: wrap; }
  .stat-sep { display: none; }
  .stat-cell { min-width: 33%; }
}
@media (max-width: 680px) {
  .kpi-page { padding: var(--sp-4); }
  .kpi-grid { grid-template-columns: 1fr; }
  .toolbar { gap: var(--sp-2); }
  .search-wrap { max-width: 100%; flex: 1 1 100%; }
}

@media (prefers-reduced-motion: reduce) {
  .kpi-card, .list-row { animation: none; opacity: 1; transform: none; }
  .card-skel { animation: none; }
}
</style>
