<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Plus, Search, RefreshCcw, FileText, Download, Pencil, Trash2,
  Play, X, ChevronDown, Clock, Calendar, Grid3x3, List,
  CheckCircle2, AlertTriangle, BarChart2, Check, Users, Star,
} from 'lucide-vue-next'
import api from '@/api/axios'

// ── Types ──────────────────────────────────────────────────
type ReportFormat = 'pdf' | 'xlsx' | 'html' | 'csv' | 'json' | 'tsv' | 'yaml'
type ViewMode = 'grid' | 'list'

interface Report {
  id: string
  name: string
  description: string
  dashboard: string
  dashboard_name: string
  format: ReportFormat
  format_display: string
  schedule: string
  recipients: any
  include_metadata: boolean
  include_filters: boolean
  page_size: string
  orientation: string
  last_generated: string | null
  generation_count: number
  last_error: string
  is_active: boolean
  owner_name: string
  next_run: string
  tags: any
  created_at: string
  updated_at: string
  starred?: boolean
}

async function toggleStarReport(r: Report) {
  const was = !!r.starred
  r.starred = !was
  try {
    if (!was) {
      await api.post('/api/visualizations/favorites/add/',    { item_id: r.id, item_type: 'report' })
    } else {
      await api.post('/api/visualizations/favorites/remove/', { item_id: r.id, item_type: 'report' })
    }
  } catch {
    r.starred = was
  }
}

interface ReportStats {
  total: number
  active: number
  pending: number
  generated_today: number
}

// ── State ──────────────────────────────────────────────────
const reports       = ref<Report[]>([])
const stats         = ref<ReportStats>({ total: 0, active: 0, pending: 0, generated_today: 0 })
const loading       = ref(true)
const refreshing    = ref(false)
const listVisible   = ref(false)

const searchQuery   = ref('')
const filterFormat  = ref<ReportFormat | 'all'>('all')
const filterStatus  = ref<'all' | 'active' | 'inactive'>('all')
const viewMode      = ref<ViewMode>('grid')

const drawerOpen    = ref(false)
const editReport    = ref<Report | null>(null)
const submitting    = ref(false)

const deleteTarget  = ref<string | null>(null)
const deleting      = ref(false)

const generatingIds    = ref<Set<string>>(new Set())
const generateFeedback = ref<string | null>(null)

// ── Lookups (dashboard select + recipients tags) ────────────
interface DashboardOption { id: string; name: string }
interface UserOption      { id: string; email: string; display: string }

const dashboards           = ref<DashboardOption[]>([])
const users                = ref<UserOption[]>([])
const selectedRecipients   = ref<string[]>([])
const recipientSearch      = ref('')
const recipientDropdownOpen = ref(false)

const form = ref({
  name: '',
  description: '',
  dashboard: '',
  format: 'pdf' as ReportFormat,
  schedule: '',
  page_size: 'A4',
  orientation: 'portrait',
  include_metadata: false,
  include_filters: false,
  is_active: true,
})

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return reports.value.filter(r => {
    const matchSearch = !q || r.name.toLowerCase().includes(q) || r.dashboard_name?.toLowerCase().includes(q)
    const matchFormat = filterFormat.value === 'all' || r.format === filterFormat.value
    const matchStatus =
      filterStatus.value === 'all' ||
      (filterStatus.value === 'active' && r.is_active) ||
      (filterStatus.value === 'inactive' && !r.is_active)
    return matchSearch && matchFormat && matchStatus
  })
})

const showPageOptions = computed(() =>
  form.value.format === 'pdf' || form.value.format === 'html'
)

const filteredUsers = computed(() => {
  const q = recipientSearch.value.toLowerCase()
  return users.value.filter(u =>
    !q || u.email.toLowerCase().includes(q) || u.display.toLowerCase().includes(q)
  )
})

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Jamais'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  const days = Math.floor(hrs / 24)
  if (days < 7)  return `il y a ${days} j`
  return new Date(dateStr).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

function nextRunLabel(dateStr: string): string {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return '—'
  }
}

function scheduleLabel(schedule: string): string {
  if (!schedule) return 'Manuel'
  return schedule
}

interface FormatMeta { label: string; color: string; bg: string }
const FORMAT_META: Record<ReportFormat, FormatMeta> = {
  pdf:  { label: 'PDF',   color: '#e05252', bg: 'oklch(18% 0.06 15)'   },
  xlsx: { label: 'Excel', color: '#4db37a', bg: 'oklch(16% 0.06 148)'  },
  html: { label: 'HTML',  color: '#4a8fd4', bg: 'oklch(16% 0.05 240)'  },
  csv:  { label: 'CSV',   color: '#d4922a', bg: 'oklch(16% 0.07 62)'   },
  json: { label: 'JSON',  color: '#9b72d4', bg: 'oklch(16% 0.07 295)'  },
  tsv:  { label: 'TSV',   color: '#6ba3a0', bg: 'oklch(16% 0.05 190)'  },
  yaml: { label: 'YAML',  color: '#c47fbd', bg: 'oklch(16% 0.06 320)'  },
}

function formatMeta(format: ReportFormat): FormatMeta {
  return FORMAT_META[format] ?? { label: format.toUpperCase(), color: 'var(--text-muted)', bg: 'var(--surface-overlay)' }
}

// ── Lookup helpers ─────────────────────────────────────────
async function fetchDashboards() {
  try {
    const { data } = await api.get('/api/visualizations/dashboards/?page_size=200&ordering=name')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    dashboards.value = rows.map((d: any) => ({ id: String(d.id), name: d.name ?? d.slug ?? d.id }))
  } catch { dashboards.value = [] }
}

async function fetchUsers() {
  try {
    const { data } = await api.get('/api/users/users/?page_size=200&ordering=email')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    users.value = rows.map((u: any) => ({
      id:      String(u.id),
      email:   u.email,
      display: [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email,
    }))
  } catch { users.value = [] }
}

function toggleRecipient(email: string) {
  if (selectedRecipients.value.includes(email)) {
    selectedRecipients.value = selectedRecipients.value.filter(e => e !== email)
  } else {
    selectedRecipients.value = [...selectedRecipients.value, email]
    recipientSearch.value = ''
  }
}

// ── API ────────────────────────────────────────────────────
async function fetchReports() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/visualizations/reports/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    reports.value = rows
  } catch {
    reports.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function fetchStats() {
  try {
    const [statsRes, pendingRes] = await Promise.all([
      api.get('/api/visualizations/reports/stats/'),
      api.get('/api/visualizations/reports/pending/'),
    ])
    const s = statsRes.data ?? {}
    const pendingCount = Array.isArray(pendingRes.data?.results)
      ? pendingRes.data.results.length
      : Array.isArray(pendingRes.data)
        ? pendingRes.data.length
        : (pendingRes.data?.count ?? 0)
    stats.value = {
      total:           s.total           ?? reports.value.length,
      active:          s.active          ?? reports.value.filter(r => r.is_active).length,
      pending:         s.pending         ?? pendingCount,
      generated_today: s.generated_today ?? 0,
    }
  } catch {
    // leave defaults
  }
}

async function refresh() {
  refreshing.value = true
  await Promise.all([fetchReports(), fetchStats()])
  refreshing.value = false
}

async function generateReport(id: string) {
  generatingIds.value = new Set([...generatingIds.value, id])
  generateFeedback.value = null
  try {
    const response = await api.post(
      `/api/visualizations/reports/${id}/generate/`,
      {},
      { responseType: 'blob' },
    )

    // Extraire le nom de fichier depuis Content-Disposition
    const disposition: string = response.headers['content-disposition'] ?? ''
    const match = disposition.match(/filename[^;=\n]*=["']?([^"';\n]+)["']?/)
    const report = reports.value.find(r => r.id === id)
    const fallbackName = `rapport_${report?.name ?? id}.${report?.format ?? 'bin'}`
    const filename = match?.[1]?.trim() || fallbackName

    // Déclencher le téléchargement dans le navigateur
    const blobUrl = URL.createObjectURL(response.data as Blob)
    const anchor = document.createElement('a')
    anchor.href = blobUrl
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
    URL.revokeObjectURL(blobUrl)

    generateFeedback.value = `Fichier téléchargé : ${filename}`

    // Rafraîchir les métadonnées du rapport (last_generated, generation_count…)
    const { data } = await api.get(`/api/visualizations/reports/${id}/`)
    const idx = reports.value.findIndex(r => r.id === id)
    if (idx !== -1) reports.value[idx] = data

    setTimeout(() => { generateFeedback.value = null }, 4000)
  } catch (err: any) {
    // Lire le message d'erreur depuis le blob si l'API retourne 500
    let msg = 'Erreur de génération'
    try {
      const errBlob: Blob = err?.response?.data
      if (errBlob instanceof Blob) {
        const text = await errBlob.text()
        const parsed = JSON.parse(text)
        msg = parsed?.error ?? parsed?.message ?? msg
      }
    } catch { /* ignore */ }
    generateFeedback.value = msg
    setTimeout(() => { generateFeedback.value = null }, 5000)
  } finally {
    const next = new Set(generatingIds.value)
    next.delete(id)
    generatingIds.value = next
  }
}

async function toggleActive(report: Report) {
  try {
    const { data } = await api.patch(`/api/visualizations/reports/${report.id}/`, {
      is_active: !report.is_active,
    })
    const idx = reports.value.findIndex(r => r.id === report.id)
    if (idx !== -1) reports.value[idx] = data
  } catch {
    // silent
  }
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.delete(`/api/visualizations/reports/${deleteTarget.value}/`)
    reports.value = reports.value.filter(r => r.id !== deleteTarget.value)
    stats.value.total = Math.max(0, stats.value.total - 1)
  } catch {
    // silent
  } finally {
    deleting.value = false
    deleteTarget.value = null
  }
}

function openDrawer(report?: Report) {
  recipientSearch.value = ''
  recipientDropdownOpen.value = false
  if (report) {
    editReport.value = report
    selectedRecipients.value = Array.isArray(report.recipients)
      ? report.recipients
      : typeof report.recipients === 'string'
        ? report.recipients.split('\n').filter(Boolean)
        : []
    form.value = {
      name:             report.name,
      description:      report.description ?? '',
      dashboard:        report.dashboard ?? '',
      format:           report.format as ReportFormat,
      schedule:         report.schedule ?? '',
      page_size:        report.page_size ?? 'A4',
      orientation:      report.orientation ?? 'portrait',
      include_metadata: report.include_metadata,
      include_filters:  report.include_filters,
      is_active:        report.is_active,
    }
  } else {
    editReport.value = null
    selectedRecipients.value = []
    form.value = {
      name: '', description: '', dashboard: '', format: 'pdf',
      schedule: '', page_size: 'A4', orientation: 'portrait',
      include_metadata: false, include_filters: false, is_active: true,
    }
  }
  drawerOpen.value = true
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  const payload = {
    name:             form.value.name.trim(),
    description:      form.value.description.trim(),
    dashboard:        form.value.dashboard || undefined,
    format:           form.value.format,
    schedule:         form.value.schedule.trim(),
    recipients:       selectedRecipients.value,
    page_size:        showPageOptions.value ? form.value.page_size : undefined,
    orientation:      showPageOptions.value ? form.value.orientation : undefined,
    include_metadata: form.value.include_metadata,
    include_filters:  form.value.include_filters,
    is_active:        form.value.is_active,
  }
  try {
    if (editReport.value) {
      const { data } = await api.patch(`/api/visualizations/reports/${editReport.value.id}/`, payload)
      const idx = reports.value.findIndex(r => r.id === editReport.value!.id)
      if (idx !== -1) reports.value[idx] = data
    } else {
      const { data } = await api.post('/api/visualizations/reports/', payload)
      reports.value.unshift(data)
      stats.value.total++
    }
    drawerOpen.value = false
    editReport.value = null
  } catch {
    // silent
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchReports()
  fetchStats()
  fetchDashboards()
  fetchUsers()
})
</script>

<template>
  <div class="rp-page">

    <!-- ── Generate feedback toast ───────────────────────── -->
    <Transition name="toast-anim">
      <div
        v-if="generateFeedback"
        class="toast-success"
        :class="{ 'toast-success--error': generateFeedback.startsWith('Erreur') || generateFeedback.startsWith('La génération') }"
        role="status"
      >
        <CheckCircle2 v-if="!generateFeedback.startsWith('Erreur') && !generateFeedback.startsWith('La génération')" :size="14" />
        <AlertTriangle v-else :size="14" />
        {{ generateFeedback }}
      </div>
    </Transition>

    <!-- ── Page header ─────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Rapports</h2>
        <p class="page-meta">
          {{ stats.total }} rapport{{ stats.total !== 1 ? 's' : '' }} configuré{{ stats.total !== 1 ? 's' : '' }}
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
        <button class="btn-primary" @click="openDrawer()">
          <Plus :size="15" />
          <span>Nouveau rapport</span>
        </button>
      </div>
    </header>

    <!-- ── Stats strip ─────────────────────────────────────── -->
    <section class="stats-strip" aria-label="Statistiques">
      <div class="stat-card">
        <div class="stat-icon stat-icon--total">
          <FileText :size="16" />
        </div>
        <div class="stat-body">
          <span class="stat-n">{{ stats.total }}</span>
          <span class="stat-l">Total rapports</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--active">
          <CheckCircle2 :size="16" />
        </div>
        <div class="stat-body">
          <span class="stat-n">{{ stats.active }}</span>
          <span class="stat-l">Actifs</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--generated">
          <Download :size="16" />
        </div>
        <div class="stat-body">
          <span class="stat-n">{{ stats.generated_today }}</span>
          <span class="stat-l">Génération aujourd'hui</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--pending">
          <Clock :size="16" />
        </div>
        <div class="stat-body">
          <span class="stat-n">{{ stats.pending }}</span>
          <span class="stat-l">En attente</span>
        </div>
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
          placeholder="Rechercher un rapport…"
        />
      </div>

      <div class="select-wrap">
        <select v-model="filterFormat" class="filter-select">
          <option value="all">Tous les formats</option>
          <option value="pdf">PDF</option>
          <option value="xlsx">Excel (XLSX)</option>
          <option value="csv">CSV</option>
          <option value="tsv">TSV</option>
          <option value="yaml">YAML</option>
          <option value="html">HTML</option>
          <option value="json">JSON</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="select-wrap">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="active">Actifs</option>
          <option value="inactive">Inactifs</option>
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
    <div v-if="loading" class="rp-grid">
      <div v-for="i in 4" :key="i" class="card-skel"></div>
    </div>

    <!-- ── Empty state ─────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <BarChart2 :size="40" class="empty-icon" />
      <p class="empty-title">Aucun rapport</p>
      <p class="empty-sub">
        {{ reports.length === 0
          ? 'Créez votre premier rapport planifié.'
          : 'Aucun rapport ne correspond à vos filtres.' }}
      </p>
      <button class="btn-primary" @click="openDrawer()">
        <Plus :size="14" />
        <span>Nouveau rapport</span>
      </button>
    </div>

    <!-- ── Grid view ───────────────────────────────────────── -->
    <div
      v-else-if="viewMode === 'grid'"
      class="rp-grid"
      :class="{ 'rp-grid--visible': listVisible }"
    >
      <article
        v-for="(report, i) in filtered"
        :key="report.id"
        class="rp-card"
        :class="{ 'rp-card--inactive': !report.is_active }"
        :style="{ '--card-i': i }"
      >
        <!-- Format badge top-right -->
        <div
          class="format-badge"
          :style="{
            '--fb-color': formatMeta(report.format).color,
            '--fb-bg':    formatMeta(report.format).bg,
          }"
        >
          {{ formatMeta(report.format).label }}
        </div>

        <!-- Card header -->
        <div class="card-hd">
          <div class="card-icon">
            <FileText :size="18" />
          </div>
          <div class="card-hd-info">
            <h3 class="card-title" :title="report.name">{{ report.name }}</h3>
            <p v-if="report.description" class="card-desc">{{ report.description }}</p>
          </div>
        </div>

        <!-- Error banner -->
        <div v-if="report.last_error" class="error-banner">
          <AlertTriangle :size="12" />
          <span class="error-text">{{ report.last_error }}</span>
        </div>

        <!-- Meta rows -->
        <ul class="card-meta-list">
          <li class="meta-row">
            <BarChart2 :size="12" class="meta-icon" />
            <span class="meta-label">Tableau de bord</span>
            <span class="meta-val">{{ report.dashboard_name || '—' }}</span>
          </li>
          <li class="meta-row">
            <Clock :size="12" class="meta-icon" />
            <span class="meta-label">Planification</span>
            <span class="meta-val meta-mono">{{ scheduleLabel(report.schedule) }}</span>
          </li>
          <li class="meta-row">
            <Calendar :size="12" class="meta-icon" />
            <span class="meta-label">Prochaine exécution</span>
            <span class="meta-val">{{ nextRunLabel(report.next_run) }}</span>
          </li>
          <li class="meta-row">
            <Download :size="12" class="meta-icon" />
            <span class="meta-label">Dernière génération</span>
            <span class="meta-val">{{ timeAgo(report.last_generated) }}</span>
          </li>
          <li class="meta-row">
            <FileText :size="12" class="meta-icon" />
            <span class="meta-label">Générations</span>
            <span class="meta-val">{{ report.generation_count }}</span>
          </li>
        </ul>

        <!-- Footer -->
        <div class="card-footer">
          <!-- Active toggle -->
          <button
            class="status-badge"
            :class="report.is_active ? 'status-badge--active' : 'status-badge--inactive'"
            :title="report.is_active ? 'Désactiver' : 'Activer'"
            @click="toggleActive(report)"
          >
            <CheckCircle2 :size="11" />
            {{ report.is_active ? 'Actif' : 'Inactif' }}
          </button>

          <div class="card-actions">
            <!-- Favori (étoile) -->
            <button
              class="action-btn action-btn--star"
              :class="{ 'action-btn--star-on': report.starred }"
              :title="report.starred ? 'Retirer des favoris' : 'Ajouter aux favoris'"
              @click="toggleStarReport(report)"
            >
              <Star :size="13" :fill="report.starred ? 'currentColor' : 'none'" />
            </button>
            <!-- Generate -->
            <button
              class="action-btn action-btn--generate"
              :class="{ 'action-btn--loading': generatingIds.has(report.id) }"
              :disabled="generatingIds.has(report.id)"
              title="Générer maintenant"
              @click="generateReport(report.id)"
            >
              <span v-if="generatingIds.has(report.id)" class="spin-dot" />
              <Play v-else :size="13" />
            </button>
            <button
              class="action-btn"
              title="Modifier"
              @click="openDrawer(report)"
            >
              <Pencil :size="13" />
            </button>
            <button
              class="action-btn action-btn--delete"
              title="Supprimer"
              @click="deleteTarget = report.id"
            >
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
      </article>
    </div>

    <!-- ── List view ───────────────────────────────────────── -->
    <div
      v-else
      class="rp-list"
      :class="{ 'rp-list--visible': listVisible }"
    >
      <!-- List header -->
      <div class="list-hdr">
        <span>Nom</span>
        <span>Format</span>
        <span>Planification</span>
        <span>Prochaine exécution</span>
        <span>Dernière génération</span>
        <span>Statut</span>
        <span>Actions</span>
      </div>

      <div
        v-for="(report, i) in filtered"
        :key="report.id"
        class="list-row"
        :class="{ 'list-row--inactive': !report.is_active }"
        :style="{ '--row-i': i }"
      >
        <!-- Name + dashboard -->
        <div class="list-name-col">
          <span class="list-name">{{ report.name }}</span>
          <span v-if="report.dashboard_name" class="list-dashboard">
            <BarChart2 :size="10" />
            {{ report.dashboard_name }}
          </span>
          <span v-if="report.last_error" class="list-error">
            <AlertTriangle :size="10" />
            Erreur
          </span>
        </div>

        <!-- Format badge -->
        <div
          class="format-badge format-badge--sm"
          :style="{
            '--fb-color': formatMeta(report.format).color,
            '--fb-bg':    formatMeta(report.format).bg,
          }"
        >
          {{ formatMeta(report.format).label }}
        </div>

        <!-- Schedule -->
        <span class="list-mono">{{ scheduleLabel(report.schedule) }}</span>

        <!-- Next run -->
        <span class="list-cell">{{ nextRunLabel(report.next_run) }}</span>

        <!-- Last generated -->
        <span class="list-cell">{{ timeAgo(report.last_generated) }}</span>

        <!-- Status toggle -->
        <button
          class="status-badge"
          :class="report.is_active ? 'status-badge--active' : 'status-badge--inactive'"
          @click="toggleActive(report)"
        >
          {{ report.is_active ? 'Actif' : 'Inactif' }}
        </button>

        <!-- Actions -->
        <div class="list-actions">
          <button
            class="action-btn action-btn--generate"
            :class="{ 'action-btn--loading': generatingIds.has(report.id) }"
            :disabled="generatingIds.has(report.id)"
            title="Générer"
            @click="generateReport(report.id)"
          >
            <span v-if="generatingIds.has(report.id)" class="spin-dot" />
            <Play v-else :size="12" />
          </button>
          <button class="action-btn" title="Modifier" @click="openDrawer(report)">
            <Pencil :size="12" />
          </button>
          <button class="action-btn action-btn--delete" title="Supprimer" @click="deleteTarget = report.id">
            <Trash2 :size="12" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── Delete confirm modal ────────────────────────────── -->
    <Transition name="modal-fade">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="confirm-modal" role="dialog" aria-modal="true" aria-label="Confirmer la suppression">
          <div class="confirm-icon">
            <Trash2 :size="22" />
          </div>
          <h3 class="confirm-title">Supprimer ce rapport ?</h3>
          <p class="confirm-body">
            Cette action est irréversible. Le rapport et toutes ses configurations seront définitivement supprimés.
          </p>
          <div class="confirm-actions">
            <button class="btn-ghost" :disabled="deleting" @click="deleteTarget = null">Annuler</button>
            <button class="btn-danger" :disabled="deleting" @click="confirmDelete">
              <span v-if="deleting" class="spinner" />
              <span v-else>Supprimer</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── Create / Edit Drawer ────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false; editReport = null">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Rapport">

          <div class="drawer-hd">
            <h3 class="drawer-title">
              {{ editReport ? 'Modifier le rapport' : 'Nouveau rapport' }}
            </h3>
            <button
              class="drawer-close"
              aria-label="Fermer"
              @click="drawerOpen = false; editReport = null"
            >
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- name -->
            <div class="form-field">
              <label class="form-label" for="f-name">Nom <span class="req">*</span></label>
              <input
                id="f-name"
                v-model="form.name"
                class="form-input"
                type="text"
                placeholder="Ex : Rapport hebdomadaire ventes"
                required
              />
            </div>

            <!-- description -->
            <div class="form-field">
              <label class="form-label" for="f-desc">Description <span class="opt">optionnel</span></label>
              <textarea
                id="f-desc"
                v-model="form.description"
                class="form-textarea"
                placeholder="Brève description du rapport…"
                rows="2"
              />
            </div>

            <!-- dashboard -->
            <div class="form-field">
              <label class="form-label" for="f-dash">Tableau de bord <span class="opt">optionnel</span></label>
              <div class="select-wrap select-wrap--full">
                <select id="f-dash" v-model="form.dashboard" class="filter-select filter-select--full">
                  <option value="">— Aucun tableau de bord —</option>
                  <option v-for="dash in dashboards" :key="dash.id" :value="dash.id">
                    {{ dash.name }}
                  </option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
              <p v-if="dashboards.length === 0" class="form-hint">Aucun tableau de bord disponible</p>
            </div>

            <!-- format -->
            <div class="form-field">
              <label class="form-label" for="f-fmt">Format</label>
              <div class="select-wrap select-wrap--full">
                <select id="f-fmt" v-model="form.format" class="filter-select filter-select--full">
                  <option value="pdf">PDF (nécessite configuration)</option>
                  <option value="xlsx">Excel (XLSX)</option>
                  <option value="csv">CSV</option>
                  <option value="tsv">TSV</option>
                  <option value="yaml">YAML</option>
                  <option value="html">HTML</option>
                  <option value="json">JSON</option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>

            <!-- page_size + orientation (only pdf/html) -->
            <Transition name="fade-field">
              <div v-if="showPageOptions" class="form-row">
                <div class="form-field">
                  <label class="form-label" for="f-psize">Format page</label>
                  <div class="select-wrap select-wrap--full">
                    <select id="f-psize" v-model="form.page_size" class="filter-select filter-select--full">
                      <option value="A4">A4</option>
                      <option value="A3">A3</option>
                      <option value="Letter">Letter</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow" />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-orient">Orientation</label>
                  <div class="select-wrap select-wrap--full">
                    <select id="f-orient" v-model="form.orientation" class="filter-select filter-select--full">
                      <option value="portrait">Portrait</option>
                      <option value="landscape">Paysage</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow" />
                  </div>
                </div>
              </div>
            </Transition>

            <!-- schedule -->
            <div class="form-field">
              <label class="form-label" for="f-sched">
                Planification CRON <span class="opt">optionnel</span>
              </label>
              <!-- CRON preset picker -->
              <div class="cron-presets">
                <button
                  v-for="preset in [
                    { label: 'Manuel',      cron: '' },
                    { label: '15 min',      cron: '*/15 * * * *' },
                    { label: 'Horaire',     cron: '0 * * * *' },
                    { label: 'Quotidien',   cron: '0 9 * * *' },
                    { label: 'Lun-Ven 9h', cron: '0 9 * * 1-5' },
                    { label: 'Hebdomad.',   cron: '0 9 * * 1' },
                    { label: 'Mensuel',     cron: '0 9 1 * *' },
                  ]"
                  :key="preset.label"
                  type="button"
                  class="cron-preset-btn"
                  :class="{ 'cron-preset-btn--active': form.schedule === preset.cron }"
                  @click="form.schedule = preset.cron"
                >{{ preset.label }}</button>
              </div>
              <input
                id="f-sched"
                v-model="form.schedule"
                class="form-input form-input--mono"
                type="text"
                placeholder="0 9 * * * (expression CRON personnalisée)"
              />
            </div>

            <!-- recipients — tags selector -->
            <div class="form-field">
              <div class="recip-label-row">
                <label class="form-label">
                  <Users :size="13" style="vertical-align:middle;margin-right:4px" />
                  Destinataires
                </label>
                <span class="recip-count">
                  {{ selectedRecipients.length }} sélectionné{{ selectedRecipients.length !== 1 ? 's' : '' }}
                </span>
              </div>

              <div class="tags-selector" @click.stop>
                <!-- chips des destinataires sélectionnés -->
                <div class="tags-chips">
                  <span
                    v-for="email in selectedRecipients"
                    :key="email"
                    class="tag-chip"
                  >
                    {{ email }}
                    <button
                      type="button"
                      class="tag-chip-remove"
                      :aria-label="`Retirer ${email}`"
                      @click="toggleRecipient(email)"
                    >
                      <X :size="10" />
                    </button>
                  </span>

                  <input
                    id="f-recip"
                    v-model="recipientSearch"
                    class="tag-input"
                    type="text"
                    :placeholder="selectedRecipients.length ? 'Ajouter…' : 'Rechercher un utilisateur…'"
                    autocomplete="off"
                    @focus="recipientDropdownOpen = true"
                    @blur="setTimeout(() => { recipientDropdownOpen = false }, 200)"
                  />
                </div>

                <!-- dropdown liste utilisateurs -->
                <div v-if="recipientDropdownOpen && users.length > 0" class="tags-dropdown">
                  <div
                    v-for="user in filteredUsers"
                    :key="user.email"
                    class="tags-option"
                    :class="{ 'tags-option--active': selectedRecipients.includes(user.email) }"
                    @mousedown.prevent="toggleRecipient(user.email)"
                  >
                    <div class="option-info">
                      <span class="option-display">{{ user.display }}</span>
                      <span class="option-email">{{ user.email }}</span>
                    </div>
                    <Check v-if="selectedRecipients.includes(user.email)" :size="13" class="option-check" />
                  </div>
                  <div v-if="filteredUsers.length === 0" class="tags-empty">
                    Aucun utilisateur trouvé
                  </div>
                </div>
              </div>
            </div>

            <!-- checkboxes row -->
            <div class="form-checks">
              <label class="check-label">
                <input v-model="form.include_metadata" type="checkbox" class="check-input" />
                <span class="check-box" />
                Inclure les métadonnées
              </label>
              <label class="check-label">
                <input v-model="form.include_filters" type="checkbox" class="check-input" />
                <span class="check-box" />
                Inclure les filtres
              </label>
              <label class="check-label">
                <input v-model="form.is_active" type="checkbox" class="check-input" />
                <span class="check-box check-box--active" />
                Rapport actif
              </label>
            </div>

            <div class="drawer-footer">
              <button
                type="button"
                class="btn-ghost"
                @click="drawerOpen = false; editReport = null"
              >
                Annuler
              </button>
              <button
                type="submit"
                class="btn-primary"
                :class="{ 'btn-primary--loading': submitting }"
                :disabled="submitting || !form.name.trim()"
              >
                <span v-if="!submitting">{{ editReport ? 'Enregistrer' : 'Créer' }}</span>
                <span v-else class="spinner" aria-label="Enregistrement…" />
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
.rp-page {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  min-height: 100%;
  position: relative;
}

/* ── Toast ───────────────────────────────────────────────── */
.toast-success {
  position: fixed;
  top: var(--sp-6);
  right: var(--sp-6);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-5);
  background: oklch(16% 0.06 148);
  border: 1px solid oklch(40% 0.14 148);
  border-radius: var(--radius-md);
  color: #4db37a;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  box-shadow: 0 8px 32px oklch(5% 0.01 258 / 0.5);
  max-width: 420px;
}
.toast-success--error {
  background: oklch(16% 0.06 15);
  border-color: oklch(40% 0.14 15);
  color: #e05252;
}

.toast-anim-enter-active,
.toast-anim-leave-active { transition: all 250ms ease; }
.toast-anim-enter-from,
.toast-anim-leave-to { opacity: 0; transform: translateY(-8px); }

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

.hd-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background-color: var(--accent);
  color: var(--text-on-accent, #0d0c0a);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  min-height: 38px;
  white-space: nowrap;
  transition: background-color 150ms, box-shadow 150ms;
}
.btn-primary:hover:not(:disabled) {
  background-color: oklch(80% 0.14 62);
  box-shadow: 0 4px 16px oklch(76% 0.14 62 / 0.28);
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
  min-height: 38px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover:not(:disabled) { border-color: var(--border-strong, var(--border-default)); color: var(--text-primary); }
.btn-ghost:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-danger {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-5);
  background: var(--error);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  min-height: 38px;
  min-width: 100px;
  transition: opacity 150ms;
}
.btn-danger:hover:not(:disabled) { opacity: 0.88; }
.btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-icon {
  padding: var(--sp-2);
  min-height: unset;
  width: 38px;
  height: 38px;
  justify-content: center;
}

@keyframes spin { to { transform: rotate(360deg); } }
.btn-icon--spinning svg { animation: spin 0.7s linear infinite; }

/* ── Stats strip ─────────────────────────────────────────── */
.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-4);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon--total    { background: oklch(15% 0.05 62); color: var(--accent); }
.stat-icon--active   { background: oklch(16% 0.06 148); color: #4db37a; }
.stat-icon--generated{ background: oklch(16% 0.05 240); color: #4a8fd4; }
.stat-icon--pending  { background: oklch(16% 0.05 55); color: #d4922a; }

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stat-n {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
  flex: 1;
  min-width: 200px;
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
  height: 38px;
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
.select-wrap--full { width: 100%; }

.filter-select {
  appearance: none;
  height: 38px;
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
.filter-select--full { width: 100%; }

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
  margin-left: auto;
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
.rp-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-5);
  opacity: 0;
  transition: opacity 300ms ease;
  align-items: start;
}
.rp-grid--visible { opacity: 1; }

/* ── Card ────────────────────────────────────────────────── */
.rp-card {
  position: relative;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  transition: border-color 200ms, box-shadow 200ms, opacity 200ms;

  opacity: 0;
  transform: translateY(8px);
  animation: card-in 320ms var(--ease-out-expo, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
  animation-delay: calc(var(--card-i, 0) * 40ms);
}

@keyframes card-in { to { opacity: 1; transform: translateY(0); } }

.rp-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 8px 32px oklch(5% 0.01 258 / 0.4);
}

.rp-card--inactive { opacity: 0.6; }
.rp-card--inactive:hover { opacity: 0.85; }

/* Format badge */
.format-badge {
  position: absolute;
  top: var(--sp-4);
  right: var(--sp-4);
  padding: 3px 9px;
  border-radius: var(--radius-full);
  background: var(--fb-bg);
  color: var(--fb-color);
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid color-mix(in oklch, var(--fb-color) 30%, transparent);
}

.format-badge--sm {
  position: static;
  font-size: 0.6rem;
}

/* Card header */
.card-hd {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding-right: 56px;
}

.card-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: var(--accent-surface);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-hd-info { min-width: 0; }

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
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Error banner */
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: var(--error-surface);
  border: 1px solid var(--error);
  border-radius: var(--radius-sm);
}

.error-text {
  font-size: var(--text-xs);
  color: var(--error);
  line-height: 1.5;
  word-break: break-all;
}

/* Meta list */
.card-meta-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.meta-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--text-xs);
}

.meta-icon { color: var(--text-muted); flex-shrink: 0; }

.meta-label {
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 130px;
}

.meta-val {
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-mono {
  font-family: var(--font-display);
  letter-spacing: 0.02em;
  color: var(--accent-dim);
}

/* Card footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--sp-3);
  border-top: 1px solid var(--border-subtle);
  gap: var(--sp-2);
}

/* Status badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
  border: 1px solid transparent;
  transition: opacity 150ms;
}
.status-badge:hover { opacity: 0.78; }

.status-badge--active {
  background: oklch(16% 0.06 148);
  color: #4db37a;
  border-color: oklch(35% 0.14 148);
}

.status-badge--inactive {
  background: var(--surface-muted);
  color: var(--text-muted);
  border-color: var(--border-subtle);
}

/* Action buttons */
.card-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 120ms;
}
.action-btn:hover:not(:disabled) {
  background: var(--surface-overlay);
  border-color: var(--border-default);
  color: var(--text-secondary);
}
.action-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.action-btn--generate:hover:not(:disabled) {
  background: oklch(15% 0.05 62);
  border-color: var(--accent-dim);
  color: var(--accent);
}

.action-btn--loading {
  background: oklch(15% 0.05 62);
  border-color: var(--accent-dim);
  color: var(--accent);
}

.action-btn--delete:hover:not(:disabled) {
  background: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}

/* Spin dots for loading */
@keyframes spin-sm { to { transform: rotate(360deg); } }

.spin-dot {
  display: block;
  width: 13px;
  height: 13px;
  border: 2px solid oklch(50% 0.1 62 / 0.3);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin-sm 0.7s linear infinite;
}

.spinner {
  display: block;
  width: 16px;
  height: 16px;
  border: 2px solid oklch(14% 0.013 258 / 0.3);
  border-top-color: var(--text-on-accent, #0d0c0a);
  border-radius: 50%;
  animation: spin-sm 0.7s linear infinite;
}

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.card-skel {
  height: 280px;
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
.rp-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  opacity: 0;
  transition: opacity 300ms;
}
.rp-list--visible { opacity: 1; }

.list-hdr {
  display: grid;
  grid-template-columns: 1fr 70px 140px 140px 140px 80px 100px;
  align-items: center;
  gap: var(--sp-3);
  padding: 0 var(--sp-4) var(--sp-1);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.list-row {
  display: grid;
  grid-template-columns: 1fr 70px 140px 140px 140px 80px 100px;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: background 120ms, border-color 120ms;

  opacity: 0;
  transform: translateY(4px);
  animation: card-in 260ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: calc(var(--row-i, 0) * 30ms);
}
.list-row:hover {
  background: var(--surface-overlay);
  border-color: var(--border-default);
}
.list-row--inactive { opacity: 0.6; }

.list-name-col {
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

.list-dashboard {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-error {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--error);
}

.list-cell {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-mono {
  font-size: var(--text-xs);
  color: var(--accent-dim);
  font-family: var(--font-display);
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  padding: 80px var(--sp-8);
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

/* ── Delete confirm modal ────────────────────────────────── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0.01 258 / 0.78);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-6);
}

.confirm-modal {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--sp-8);
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  text-align: center;
}

.confirm-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-full);
  background: var(--error-surface);
  color: var(--error);
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}

.confirm-body {
  font-size: var(--text-sm);
  color: var(--text-muted);
  line-height: 1.6;
  max-width: 34ch;
}

.confirm-actions {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  width: 100%;
  justify-content: center;
}

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: oklch(5% 0.01 258 / 0.72);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 480px;
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
.drawer-close:hover { border-color: var(--border-strong, var(--border-default)); color: var(--text-primary); }

.drawer-form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  padding: var(--sp-6);
  flex: 1;
}

/* Form fields */
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
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
  transition: border-color 150ms, box-shadow 150ms;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus {
  border-color: var(--accent-dim);
  box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12);
}
.form-input::placeholder { color: var(--text-muted); }

.form-input--mono {
  font-family: var(--font-display);
  letter-spacing: 0.04em;
  font-size: var(--text-sm);
}

.form-textarea {
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  resize: vertical;
  transition: border-color 150ms, box-shadow 150ms;
  width: 100%;
  box-sizing: border-box;
  line-height: 1.5;
}
.form-textarea:focus {
  border-color: var(--accent-dim);
  box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12);
}
.form-textarea::placeholder { color: var(--text-muted); }

.form-textarea--mono {
  font-family: var(--font-display);
  letter-spacing: 0.02em;
}

/* CRON presets */
.cron-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1);
  margin-bottom: var(--sp-2);
}
.cron-preset-btn {
  padding: var(--sp-1) var(--sp-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-overlay);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all 120ms;
}
.cron-preset-btn:hover { border-color: var(--accent); color: var(--accent); }
.cron-preset-btn--active { background: var(--accent-surface); border-color: var(--accent); color: var(--accent); font-weight: 600; }

/* Recipients */
.recip-label-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--sp-1); }
.recip-count { font-size: var(--text-xs); color: var(--accent); font-weight: 600; }
.form-hint { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }

/* CRON hint button */
.hint-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--accent-dim);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  padding: 0;
  text-align: left;
  transition: color 150ms;
}
.hint-btn:hover { color: var(--accent); }
.hint-btn code {
  font-family: var(--font-display);
  background: var(--accent-surface);
  border-radius: var(--radius-sm);
  padding: 1px 5px;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
}

/* Checkboxes */
.form-checks {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.check-label {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  user-select: none;
}

.check-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.check-box {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: var(--surface-base);
  flex-shrink: 0;
  position: relative;
  transition: border-color 150ms, background 150ms;
}

.check-input:checked + .check-box {
  background: var(--accent);
  border-color: var(--accent);
}

.check-input:checked + .check-box::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 9px;
  border: 2px solid oklch(10% 0.01 258);
  border-top: none;
  border-left: none;
  transform: rotate(40deg);
}

.check-box--active {
  border-color: #4db37a;
}

.check-input:checked + .check-box--active {
  background: #4db37a;
  border-color: #4db37a;
}

/* Drawer footer */
.drawer-footer {
  display: flex;
  gap: var(--sp-3);
  justify-content: flex-end;
  padding-top: var(--sp-4);
  margin-top: auto;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

/* ── Transitions ─────────────────────────────────────────── */
.modal-fade-enter-active { transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1); }
.modal-fade-leave-active { transition: all 150ms ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .confirm-modal { transform: scale(0.95); }

.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from,
.drawer-anim-leave-to { opacity: 0; }
.drawer-anim-enter-active .drawer { transition: transform 380ms cubic-bezier(0.16, 1, 0.3, 1); }
.drawer-anim-leave-active .drawer  { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer,
.drawer-anim-leave-to .drawer { transform: translateX(100%); }

.fade-field-enter-active,
.fade-field-leave-active { transition: all 200ms ease; overflow: hidden; }
.fade-field-enter-from,
.fade-field-leave-to { opacity: 0; max-height: 0; margin: 0; }
.fade-field-enter-to,
.fade-field-leave-from { opacity: 1; max-height: 200px; }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .rp-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 1100px) {
  .stats-strip { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 900px) {
  .rp-page { padding: var(--sp-5); gap: var(--sp-4); }
  .rp-grid { grid-template-columns: 1fr; }
  .stats-strip { grid-template-columns: repeat(2, 1fr); }
  .list-hdr,
  .list-row { grid-template-columns: 1fr 70px auto auto; }
  .list-hdr span:nth-child(n+3):not(:nth-child(6)):not(:nth-child(7)),
  .list-row > *:nth-child(n+3):not(:nth-child(6)):not(:nth-child(7)) { display: none; }
}

@media (max-width: 600px) {
  .rp-page { padding: var(--sp-4); }
  .stats-strip { grid-template-columns: 1fr 1fr; }
  .toolbar { flex-wrap: wrap; }
  .search-wrap { max-width: 100%; }
  .view-toggle { margin-left: 0; }
  .form-row { grid-template-columns: 1fr; }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .rp-card, .list-row { animation: none; opacity: 1; transform: none; }
  .card-skel { animation: none; }
}

/* ── Tags selector (Destinataires) ───────────────────────── */
.tags-selector {
  position: relative;
}
.tags-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-1) var(--sp-2);
  align-items: center;
  min-height: 38px;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-overlay);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: text;
  transition: border-color 0.15s;
}
.tags-chips:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px oklch(52% 0.22 258 / 0.18);
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: oklch(20% 0.06 258);
  border: 1px solid oklch(38% 0.1 258);
  border-radius: 99px;
  font-size: var(--text-xs);
  color: oklch(75% 0.12 258);
  white-space: nowrap;
}
.tag-chip-remove {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: oklch(55% 0.1 258);
  line-height: 1;
  transition: color 0.15s;
}
.tag-chip-remove:hover { color: #e05252; }
.tag-input {
  flex: 1;
  min-width: 140px;
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-primary);
  padding: 2px 0;
}
.tag-input::placeholder { color: var(--text-muted); }

.tags-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 200;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: 0 8px 24px oklch(5% 0.01 258 / 0.4);
  max-height: 220px;
  overflow-y: auto;
}
.tags-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  cursor: pointer;
  transition: background 0.1s;
}
.tags-option:hover       { background: var(--surface-overlay); }
.tags-option--active     { background: oklch(18% 0.06 258); }
.option-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.option-display {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.option-email {
  font-size: var(--text-xs);
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.option-check { color: var(--accent); flex-shrink: 0; }
.tags-empty {
  padding: var(--sp-3);
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-muted);
}
</style>
