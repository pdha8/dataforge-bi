<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  Plus, Search, Star, Share2, Pencil, Copy, Trash2,
  X, ChevronDown, LayoutDashboard, Globe, FileEdit,
  Clock, Tag, Grid3x3, List, BarChart2, Download,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
type ViewMode = 'grid' | 'list'

interface WidgetRect { x: number; y: number; w: number; h: number; color: string }
interface Dashboard {
  id: string | number
  name: string
  description?: string
  status: string
  starred: boolean
  widget_count: number
  tags: string[]
  updated_at: string
  created_by: string
  layout: WidgetRect[]
}

// ── Layout preview helpers ─────────────────────────────────
// 12-col × 7-row grid, SVG viewBox "0 0 120 70", each unit = 10px
const COLORS = [
  'oklch(76% 0.14 62 / 0.55)',    // amber
  'oklch(65% 0.13 148 / 0.50)',   // teal
  'oklch(60% 0.12 258 / 0.45)',   // blue-violet
  'oklch(68% 0.12 290 / 0.45)',   // violet
  'oklch(70% 0.14 80  / 0.45)',   // warning amber
  'oklch(64% 0.19 24  / 0.40)',   // rose/red
]

const GAP = 1.5

function rects(layout: Array<[number,number,number,number]>): WidgetRect[] {
  return layout.map(([x, y, w, h], i) => ({
    x: x * 10 + GAP,
    y: y * 10 + GAP,
    w: w * 10 - GAP * 2,
    h: h * 10 - GAP * 2,
    color: COLORS[i % COLORS.length],
  }))
}

// Preset layouts (x, y, w, h in grid units, grid=12×7)
const L = {
  hero3:     rects([[0,0,7,4],[7,0,5,4],[0,4,4,3],[4,4,4,3],[8,4,4,3]]),
  twoRow:    rects([[0,0,6,4],[6,0,6,4],[0,4,6,3],[6,4,6,3]]),
  bigLeft:   rects([[0,0,8,7],[8,0,4,4],[8,4,4,3]]),
  triple:    rects([[0,0,4,7],[4,0,4,7],[8,0,4,7]]),
  magazine:  rects([[0,0,12,3],[0,3,4,4],[4,3,4,4],[8,3,4,4]]),
  kpiRow:    rects([[0,0,3,2],[3,0,3,2],[6,0,3,2],[9,0,3,2],[0,2,6,5],[6,2,6,5]]),
  classic:   rects([[0,0,8,5],[8,0,4,5],[0,5,12,2]]),
  minimal:   rects([[0,0,12,4],[0,4,6,3],[6,4,6,3]]),
}

const LAYOUT_LIST = [L.hero3, L.twoRow, L.kpiRow, L.bigLeft, L.triple, L.classic, L.magazine, L.minimal]
let _layoutIdx = 0
function nextLayout(): WidgetRect[] {
  return LAYOUT_LIST[_layoutIdx++ % LAYOUT_LIST.length]
}

function mapDashboard(d: any): Dashboard {
  const rawTags = d.tags
  const tags: string[] = Array.isArray(rawTags)
    ? rawTags.filter((t: any) => typeof t === 'string')
    : typeof rawTags === 'object' && rawTags !== null
      ? Object.keys(rawTags)
      : []
  return {
    id:           d.id,
    name:         d.name || '',
    description:  d.description || undefined,
    status:       d.status || 'draft',
    starred:      false,
    widget_count: d.widget_count ?? 0,
    tags,
    updated_at:   d.updated_at || new Date().toISOString(),
    created_by:   d.owner_name || '',
    layout:       nextLayout(),
  }
}

// Layout templates for "create" drawer
const LAYOUT_TEMPLATES: Array<{ id: string; label: string; layout: WidgetRect[]; desc: string }> = [
  { id: 'hero3',   label: 'Héro + 3',      layout: L.hero3,   desc: '1 grand + 4 widgets' },
  { id: 'twoRow',  label: '2 × 2',          layout: L.twoRow,  desc: '4 widgets équilibrés' },
  { id: 'kpiRow',  label: 'KPIs + 2',       layout: L.kpiRow,  desc: '4 KPIs + 2 graphiques' },
  { id: 'bigLeft', label: 'Grand gauche',   layout: L.bigLeft, desc: 'Principale + 2 droite' },
  { id: 'triple',  label: '3 colonnes',     layout: L.triple,  desc: '3 colonnes égales' },
  { id: 'classic', label: 'Classique',      layout: L.classic, desc: 'Large + latéral + bande' },
  { id: 'magazine',label: 'Magazine',       layout: L.magazine,'desc': 'Bannière + 3 colonnes' },
  { id: 'minimal', label: 'Minimaliste',    layout: L.minimal, desc: '1 grand + 2 petits' },
]

// ── State ──────────────────────────────────────────────────
const dashboards     = ref<Dashboard[]>([])
const loading        = ref(true)
const listVisible    = ref(false)
const searchQuery    = ref('')
const filterStatus   = ref('all')
const filterTag      = ref('all')
const viewMode       = ref<ViewMode>('grid')
const drawerOpen     = ref(false)
const deleteConfirm  = ref<string | number | null>(null)
const submitting     = ref(false)
const editDash       = ref<Dashboard | null>(null)
const previewDash    = ref<Dashboard | null>(null)
const shareDash      = ref<Dashboard | null>(null)
const shareCopied    = ref(false)
const shareBaseUrl   = window.location.origin

const form = ref({
  name: '',
  description: '',
  status: 'draft',
  templateId: 'hero3',
})

// ── Publish / Export state ─────────────────────────────────
const publishingId   = ref<string | number | null>(null)
const exportingId    = ref<string | number | null>(null)
const exportFeedback = ref<string | number | null>(null)

// ── Computed ───────────────────────────────────────────────
const allTags = computed(() => {
  const tags = new Set<string>()
  dashboards.value.forEach(d => d.tags.forEach(t => tags.add(t)))
  return Array.from(tags).sort()
})

const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return dashboards.value.filter(d => {
    const matchSearch = !q || d.name.toLowerCase().includes(q) || d.description?.toLowerCase().includes(q) || d.tags.some(t => t.includes(q))
    const matchStatus = filterStatus.value === 'all' || d.status === filterStatus.value
    const matchTag    = filterTag.value === 'all' || d.tags.includes(filterTag.value)
    return matchSearch && matchStatus && matchTag
  })
})

const stats = computed(() => ({
  total:     dashboards.value.length,
  published: dashboards.value.filter(d => d.status === 'published').length,
  draft:     dashboards.value.filter(d => d.status === 'draft').length,
  starred:   dashboards.value.filter(d => d.starred).length,
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

async function toggleStar(d: Dashboard) {
  const wasStar = d.starred
  d.starred = !d.starred
  try {
    if (!wasStar) {
      await api.post('/api/visualizations/favorites/add/', { dashboard: d.id })
    } else {
      await api.post('/api/visualizations/favorites/remove/', { dashboard: d.id })
    }
  } catch {
    d.starred = wasStar
  }
}

async function duplicateDash(d: Dashboard) {
  try {
    const { data } = await api.post(`/api/visualizations/dashboards/${d.id}/duplicate/`, {})
    const clone = mapDashboard(data)
    const idx = dashboards.value.findIndex(x => x.id === d.id)
    dashboards.value.splice(idx + 1, 0, clone)
  } catch {
    /* ignore */
  }
}

async function publishDash(d: Dashboard) {
  publishingId.value = d.id
  try {
    const { data } = await api.post(`/api/visualizations/dashboards/${d.id}/publish/`)
    const updated = mapDashboard(data)
    const idx = dashboards.value.findIndex(x => x.id === d.id)
    if (idx !== -1) dashboards.value[idx] = { ...dashboards.value[idx], ...updated }
  } catch {
    /* ignore */
  } finally {
    publishingId.value = null
  }
}

async function exportDash(d: Dashboard) {
  exportingId.value = d.id
  exportFeedback.value = d.id
  try {
    await api.post(`/api/visualizations/dashboards/${d.id}/export/`, { format: 'pdf' })
  } catch {
    /* ignore */
  } finally {
    exportingId.value = null
    setTimeout(() => {
      if (exportFeedback.value === d.id) exportFeedback.value = null
    }, 3000)
  }
}

async function deleteDash(id: string | number) {
  try {
    await api.delete(`/api/visualizations/dashboards/${id}/`)
    dashboards.value = dashboards.value.filter(d => d.id !== id)
  } catch {
    /* ignore */
  }
  deleteConfirm.value = null
}

function openDrawer() {
  editDash.value = null
  form.value = { name: '', description: '', status: 'draft', templateId: 'hero3' }
  drawerOpen.value = true
}

function openEdit(d: Dashboard) {
  editDash.value = d
  form.value = { name: d.name, description: d.description || '', status: d.status, templateId: 'hero3' }
  drawerOpen.value = true
}

function openPreview(d: Dashboard) {
  previewDash.value = d
}

function openShare(d: Dashboard) {
  shareDash.value = d
  shareCopied.value = false
}

function copyShareLink() {
  const url = `${shareBaseUrl}/dashboards/${shareDash.value?.id}`
  navigator.clipboard.writeText(url).then(() => {
    shareCopied.value = true
    setTimeout(() => { shareCopied.value = false }, 2000)
  })
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  try {
    const payload = {
      name:        form.value.name.trim(),
      description: form.value.description || '',
      status:      form.value.status,
    }
    if (editDash.value) {
      const { data } = await api.patch(`/api/visualizations/dashboards/${editDash.value.id}/`, payload)
      const idx = dashboards.value.findIndex(d => d.id === editDash.value!.id)
      if (idx !== -1) dashboards.value[idx] = { ...dashboards.value[idx], ...mapDashboard(data) }
      editDash.value = null
    } else {
      const { data } = await api.post('/api/visualizations/dashboards/', payload)
      dashboards.value = [mapDashboard(data), ...dashboards.value]
    }
    drawerOpen.value = false
  } catch {
    /* ignore */
  } finally {
    submitting.value = false
  }
}

// ── API ────────────────────────────────────────────────────
async function fetchDashboards() {
  loading.value = true
  listVisible.value = false
  _layoutIdx = 0
  try {
    const { data } = await api.get('/api/visualizations/dashboards/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    dashboards.value = rows.map(mapDashboard)
  } catch {
    dashboards.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

onMounted(fetchDashboards)
</script>

<template>
  <div class="db-page">

    <!-- ── Page header ─────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Tableaux de bord</h2>
        <p class="page-meta">
          {{ stats.total }} tableau{{ stats.total !== 1 ? 'x' : '' }} · {{ stats.published }} publié{{ stats.published !== 1 ? 's' : '' }}
        </p>
      </div>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="15" />
        <span>Nouveau tableau</span>
      </button>
    </header>

    <!-- ── Stats strip ─────────────────────────────────────── -->
    <section class="stats-strip" aria-label="Statistiques">
      <div class="stat-item">
        <LayoutDashboard :size="15" class="stat-icon" />
        <span class="stat-val">{{ stats.total }}</span>
        <span class="stat-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <Globe :size="15" class="stat-icon stat-icon--pub" />
        <span class="stat-val stat-val--pub">{{ stats.published }}</span>
        <span class="stat-lbl">Publiés</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <FileEdit :size="15" class="stat-icon stat-icon--draft" />
        <span class="stat-val stat-val--draft">{{ stats.draft }}</span>
        <span class="stat-lbl">Brouillons</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <Star :size="15" class="stat-icon stat-icon--star" />
        <span class="stat-val stat-val--star">{{ stats.starred }}</span>
        <span class="stat-lbl">Favoris</span>
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
          placeholder="Rechercher un tableau de bord…"
        />
      </div>

      <div class="select-wrap">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="published">Publiés</option>
          <option value="draft">Brouillons</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="select-wrap">
        <select v-model="filterTag" class="filter-select">
          <option value="all">Tous les tags</option>
          <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>

      <div class="view-toggle" role="group" aria-label="Mode d'affichage">
        <button class="view-btn" :class="{ 'view-btn--active': viewMode === 'grid' }" @click="viewMode = 'grid'" title="Grille">
          <Grid3x3 :size="14" />
        </button>
        <button class="view-btn" :class="{ 'view-btn--active': viewMode === 'list' }" @click="viewMode = 'list'" title="Liste">
          <List :size="14" />
        </button>
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <div v-if="loading" class="db-grid">
      <div v-for="i in 6" :key="i" class="card-skel"></div>
    </div>

    <!-- ── Empty ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <LayoutDashboard :size="40" class="empty-icon" />
      <p class="empty-title">Aucun tableau de bord trouvé</p>
      <p class="empty-sub">Modifiez vos filtres ou créez votre premier tableau de bord.</p>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="14" />
        <span>Nouveau tableau</span>
      </button>
    </div>

    <!-- ── Grid view ───────────────────────────────────────── -->
    <div
      v-else-if="viewMode === 'grid'"
      class="db-grid"
      :class="{ 'db-grid--visible': listVisible }"
    >
      <article
        v-for="(dash, i) in filtered"
        :key="dash.id"
        class="dash-card"
        :class="{ 'dash-card--draft': dash.status === 'draft' }"
        :style="{ '--ci': i }"
      >
        <!-- Layout preview -->
        <div class="card-preview">
          <svg
            class="layout-svg"
            viewBox="0 0 120 70"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <rect x="0" y="0" width="120" height="70" fill="none" />
            <rect
              v-for="(r, ri) in dash.layout"
              :key="ri"
              :x="r.x" :y="r.y" :width="r.w" :height="r.h"
              :fill="r.color"
              rx="1.5"
            />
          </svg>
          <!-- Hover overlay -->
          <div class="preview-overlay">
            <button class="overlay-btn" @click.stop="openPreview(dash)">
              <BarChart2 :size="15" />
              <span>Ouvrir</span>
            </button>
          </div>
        </div>

        <!-- Card body -->
        <div class="card-body">
          <!-- Top row: status + star -->
          <div class="card-top">
            <span class="status-badge" :class="`status--${dash.status}`">
              <component :is="dash.status === 'published' ? Globe : FileEdit" :size="10" />
              {{ dash.status === 'published' ? 'Publié' : 'Brouillon' }}
            </span>
            <button
              class="star-btn"
              :class="{ 'star-btn--active': dash.starred }"
              :title="dash.starred ? 'Retirer des favoris' : 'Ajouter aux favoris'"
              @click="toggleStar(dash)"
            >
              <Star :size="14" :fill="dash.starred ? 'currentColor' : 'none'" />
            </button>
          </div>

          <h3 class="card-title" :title="dash.name">{{ dash.name }}</h3>
          <p v-if="dash.description" class="card-desc">{{ dash.description }}</p>

          <!-- Tags -->
          <div v-if="dash.tags.length" class="card-tags">
            <span v-for="tag in dash.tags.slice(0, 3)" :key="tag" class="tag-chip">
              <Tag :size="9" />{{ tag }}
            </span>
            <span v-if="dash.tags.length > 3" class="tag-chip tag-chip--more">
              +{{ dash.tags.length - 3 }}
            </span>
          </div>

          <!-- Footer: meta + actions -->
          <div class="card-footer">
            <div class="card-meta">
              <span class="meta-widgets">
                <BarChart2 :size="11" />
                {{ dash.widget_count }} widget{{ dash.widget_count !== 1 ? 's' : '' }}
              </span>
              <span class="meta-time">
                <Clock :size="11" />
                {{ timeAgo(dash.updated_at) }}
              </span>
            </div>

            <div class="card-actions">
              <button
                class="act-btn act-btn--publish"
                :class="{ 'act-btn--unpublish': dash.status === 'published' }"
                :title="dash.status === 'draft' ? 'Publier' : 'Dépublier'"
                :disabled="publishingId === dash.id"
                @click="publishDash(dash)"
              >
                <span v-if="publishingId === dash.id" class="act-spinner"></span>
                <Globe v-else :size="13" />
              </button>
              <button
                class="act-btn act-btn--export"
                :title="exportFeedback === dash.id ? 'Export en cours…' : 'Exporter (PDF)'"
                :disabled="exportingId === dash.id"
                @click="exportDash(dash)"
              >
                <span v-if="exportingId === dash.id" class="act-spinner"></span>
                <Download v-else :size="13" />
              </button>
              <button class="act-btn" title="Partager" @click="openShare(dash)"><Share2 :size="13" /></button>
              <button class="act-btn" title="Modifier" @click="openEdit(dash)"><Pencil :size="13" /></button>
              <button class="act-btn" title="Dupliquer" @click="duplicateDash(dash)"><Copy :size="13" /></button>
              <template v-if="deleteConfirm === dash.id">
                <button class="act-btn act-btn--yes" @click="deleteDash(dash.id)">Oui</button>
                <button class="act-btn" @click="deleteConfirm = null">Non</button>
              </template>
              <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = dash.id">
                <Trash2 :size="13" />
              </button>
            </div>
          </div>
        </div>
      </article>
    </div>

    <!-- ── List view ────────────────────────────────────────── -->
    <div
      v-else
      class="db-list"
      :class="{ 'db-list--visible': listVisible }"
    >
      <!-- List header -->
      <div class="list-head">
        <span>Nom</span>
        <span>Statut</span>
        <span>Tags</span>
        <span>Widgets</span>
        <span>Modifié</span>
        <span>Auteur</span>
        <span></span>
      </div>

      <div
        v-for="(dash, i) in filtered"
        :key="dash.id"
        class="list-row"
        :class="{ 'list-row--draft': dash.status === 'draft' }"
        :style="{ '--ri': i }"
      >
        <!-- Name + star -->
        <div class="list-name-cell">
          <button
            class="star-btn star-btn--sm"
            :class="{ 'star-btn--active': dash.starred }"
            @click="toggleStar(dash)"
          >
            <Star :size="12" :fill="dash.starred ? 'currentColor' : 'none'" />
          </button>
          <div class="list-name-block">
            <span class="list-name">{{ dash.name }}</span>
            <span v-if="dash.description" class="list-desc">{{ dash.description }}</span>
          </div>
        </div>

        <!-- Status -->
        <span class="status-badge" :class="`status--${dash.status}`">
          <component :is="dash.status === 'published' ? Globe : FileEdit" :size="10" />
          {{ dash.status === 'published' ? 'Publié' : 'Brouillon' }}
        </span>

        <!-- Tags -->
        <div class="list-tags">
          <span v-for="tag in dash.tags.slice(0, 2)" :key="tag" class="tag-chip">{{ tag }}</span>
          <span v-if="dash.tags.length > 2" class="tag-chip tag-chip--more">+{{ dash.tags.length - 2 }}</span>
        </div>

        <!-- Widgets -->
        <span class="list-widgets">{{ dash.widget_count }}</span>

        <!-- Time -->
        <span class="list-time">{{ timeAgo(dash.updated_at) }}</span>

        <!-- Author -->
        <span class="list-author">{{ dash.created_by }}</span>

        <!-- Actions -->
        <div class="list-actions">
          <button
            class="act-btn act-btn--publish"
            :class="{ 'act-btn--unpublish': dash.status === 'published' }"
            :title="dash.status === 'draft' ? 'Publier' : 'Dépublier'"
            :disabled="publishingId === dash.id"
            @click="publishDash(dash)"
          >
            <span v-if="publishingId === dash.id" class="act-spinner"></span>
            <Globe v-else :size="13" />
          </button>
          <button
            class="act-btn act-btn--export"
            :title="exportFeedback === dash.id ? 'Export en cours…' : 'Exporter (PDF)'"
            :disabled="exportingId === dash.id"
            @click="exportDash(dash)"
          >
            <span v-if="exportingId === dash.id" class="act-spinner"></span>
            <Download v-else :size="13" />
          </button>
          <button class="act-btn" title="Partager" @click="openShare(dash)"><Share2 :size="13" /></button>
          <button class="act-btn" title="Modifier" @click="openEdit(dash)"><Pencil :size="13" /></button>
          <button class="act-btn" title="Dupliquer" @click="duplicateDash(dash)"><Copy :size="13" /></button>
          <template v-if="deleteConfirm === dash.id">
            <button class="act-btn act-btn--yes" @click="deleteDash(dash.id)">Oui</button>
            <button class="act-btn" @click="deleteConfirm = null">Non</button>
          </template>
          <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = dash.id">
            <Trash2 :size="13" />
          </button>
        </div>
      </div>
    </div>

    <!-- ── Preview modal ─────────────────────────────────────── -->
    <Transition name="modal-fade">
      <div v-if="previewDash" class="preview-modal-overlay" @click.self="previewDash = null">
        <div class="preview-modal">
          <div class="pm-hd">
            <div>
              <h3 class="pm-title">{{ previewDash.name }}</h3>
              <p v-if="previewDash.description" class="pm-desc">{{ previewDash.description }}</p>
            </div>
            <button class="drawer-close" @click="previewDash = null" aria-label="Fermer"><X :size="18" /></button>
          </div>
          <div class="pm-body">
            <svg class="pm-svg" viewBox="0 0 120 70" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect
                v-for="(r, ri) in previewDash.layout"
                :key="ri"
                :x="r.x" :y="r.y" :width="r.w" :height="r.h"
                :fill="r.color"
                rx="1.5"
              />
            </svg>
          </div>
          <div class="pm-footer">
            <span class="pm-meta">{{ previewDash.widget_count }} widget{{ previewDash.widget_count !== 1 ? 's' : '' }} · par {{ previewDash.created_by }}</span>
            <button class="btn-ghost" @click="previewDash = null">Fermer</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── Share modal ────────────────────────────────────────── -->
    <Transition name="modal-fade">
      <div v-if="shareDash" class="preview-modal-overlay" @click.self="shareDash = null">
        <div class="preview-modal preview-modal--sm">
          <div class="pm-hd">
            <h3 class="pm-title">Partager « {{ shareDash.name }} »</h3>
            <button class="drawer-close" @click="shareDash = null" aria-label="Fermer"><X :size="18" /></button>
          </div>
          <div class="share-body">
            <p class="share-label">Lien de partage</p>
            <div class="share-input-row">
              <input
                class="share-input"
                type="text"
                readonly
                :value="`${shareBaseUrl}/dashboards/${shareDash.id}`"
              />
              <button
                class="btn-primary"
                :class="{ 'share-copied': shareCopied }"
                @click="copyShareLink"
              >
                {{ shareCopied ? 'Copié !' : 'Copier' }}
              </button>
            </div>
            <p class="share-hint">Seules les personnes ayant accès à la plateforme peuvent voir ce tableau de bord.</p>
          </div>
          <div class="pm-footer">
            <span></span>
            <button class="btn-ghost" @click="shareDash = null">Fermer</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ── Create drawer ────────────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Nouveau tableau de bord">

          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editDash ? 'Modifier le tableau de bord' : 'Nouveau tableau de bord' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false; editDash = null" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

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
                placeholder="Ex : KPIs Direction Q3"
                required
              />
            </div>

            <!-- Description -->
            <div class="form-field">
              <label class="form-label" for="f-desc">
                Description <span class="opt">optionnel</span>
              </label>
              <textarea
                id="f-desc"
                v-model="form.description"
                class="form-input form-textarea"
                placeholder="Brève description du tableau de bord…"
                rows="2"
              ></textarea>
            </div>

            <!-- Status -->
            <div class="form-field">
              <label class="form-label">Statut initial</label>
              <div class="status-toggle">
                <button
                  type="button"
                  class="status-opt"
                  :class="{ 'status-opt--active': form.status === 'draft' }"
                  @click="form.status = 'draft'"
                >
                  <FileEdit :size="14" />
                  Brouillon
                </button>
                <button
                  type="button"
                  class="status-opt"
                  :class="{ 'status-opt--active': form.status === 'published' }"
                  @click="form.status = 'published'"
                >
                  <Globe :size="14" />
                  Publié
                </button>
              </div>
            </div>

            <!-- Layout template -->
            <div class="form-field">
              <label class="form-label">Modèle de disposition</label>
              <div class="tpl-grid">
                <button
                  v-for="tpl in LAYOUT_TEMPLATES"
                  :key="tpl.id"
                  type="button"
                  class="tpl-opt"
                  :class="{ 'tpl-opt--active': form.templateId === tpl.id }"
                  :title="tpl.label"
                  @click="form.templateId = tpl.id"
                >
                  <svg viewBox="0 0 120 70" class="tpl-svg" aria-hidden="true">
                    <rect
                      v-for="(r, ri) in tpl.layout"
                      :key="ri"
                      :x="r.x" :y="r.y" :width="r.w" :height="r.h"
                      fill="currentColor"
                      rx="1.5"
                    />
                  </svg>
                  <span class="tpl-label">{{ tpl.label }}</span>
                  <span class="tpl-desc">{{ tpl.desc }}</span>
                </button>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false; editDash = null">Annuler</button>
              <button
                type="submit"
                class="btn-primary"
                :class="{ 'btn-primary--loading': submitting }"
                :disabled="submitting"
              >
                <span v-if="!submitting">{{ editDash ? 'Enregistrer' : 'Créer' }}</span>
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
.db-page {
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

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent);
  color: var(--text-on-accent);
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
.btn-primary--loading { min-width: 90px; justify-content: center; }

.btn-ghost {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm);
  font-weight: 500; color: var(--text-secondary);
  min-height: 38px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover { border-color: var(--border-strong); color: var(--text-primary); }

/* ── Stats strip ─────────────────────────────────────────── */
.stats-strip {
  display: flex; align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stat-item {
  flex: 1; display: flex; align-items: center;
  gap: var(--sp-2); padding: var(--sp-4) var(--sp-6);
}

.stat-sep { width: 1px; height: 32px; background: var(--border-subtle); flex-shrink: 0; }

.stat-icon           { color: var(--text-muted); flex-shrink: 0; }
.stat-icon--pub      { color: oklch(65% 0.13 148); }
.stat-icon--draft    { color: var(--warning); }
.stat-icon--star     { color: var(--accent-dim); }

.stat-val            { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.stat-val--pub       { color: oklch(65% 0.13 148); }
.stat-val--draft     { color: var(--warning); }
.stat-val--star      { color: var(--accent-dim); }

.stat-lbl { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); }

.search-wrap { position: relative; flex: 1; max-width: 360px; }

.search-icon {
  position: absolute; left: 11px; top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted); pointer-events: none;
}

.search-input {
  width: 100%; height: 38px;
  padding: 0 var(--sp-4) 0 34px;
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary); font-family: var(--font-ui);
  font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }
.filter-select {
  appearance: none; height: 38px;
  padding: 0 30px 0 var(--sp-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary); font-family: var(--font-ui);
  font-size: var(--text-sm); outline: none; cursor: pointer;
  transition: border-color 150ms;
}
.filter-select:focus { border-color: var(--accent-dim); }
.filter-select option { background: var(--surface-raised); }
.select-arrow {
  position: absolute; right: 9px; top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted); pointer-events: none;
}

.view-toggle {
  display: flex; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); overflow: hidden;
}
.view-btn {
  display: flex; align-items: center; justify-content: center;
  width: 36px; height: 36px;
  background: none; border: none;
  color: var(--text-muted); cursor: pointer;
  transition: background 100ms, color 100ms;
}
.view-btn:hover { color: var(--text-primary); background: var(--surface-overlay); }
.view-btn--active { color: var(--accent); background: var(--accent-surface); }
.view-btn + .view-btn { border-left: 1px solid var(--border-default); }

/* ── Grid ────────────────────────────────────────────────── */
.db-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-5);
  opacity: 0; transition: opacity 300ms;
}
.db-grid--visible { opacity: 1; }

/* ── Card ────────────────────────────────────────────────── */
.dash-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: border-color 200ms, box-shadow 200ms;

  opacity: 0; transform: translateY(8px);
  animation: card-in 320ms var(--ease-out-expo) forwards;
  animation-delay: calc(var(--ci, 0) * 35ms);
}

@keyframes card-in { to { opacity: 1; transform: translateY(0); } }

.dash-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 8px 32px oklch(5% 0.01 258 / 0.4);
}

.dash-card--draft { border-style: dashed; }

/* Preview */
.card-preview {
  position: relative;
  height: 130px;
  background: var(--surface-base);
  padding: var(--sp-3);
  overflow: hidden;
}

.layout-svg {
  width: 100%; height: 100%;
  display: block;
}

.preview-overlay {
  position: absolute; inset: 0;
  background: oklch(8% 0.01 258 / 0.75);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 200ms;
}
.dash-card:hover .preview-overlay { opacity: 1; }

.overlay-btn {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent); color: var(--text-on-accent);
  border: none; border-radius: var(--radius-md);
  font-family: var(--font-ui); font-size: var(--text-sm);
  font-weight: 600; cursor: pointer;
  transition: background 150ms;
}
.overlay-btn:hover { background: oklch(80% 0.14 62); }

/* Card body */
.card-body {
  padding: var(--sp-4);
  display: flex; flex-direction: column;
  gap: var(--sp-2); flex: 1;
}

.card-top {
  display: flex; align-items: center;
  justify-content: space-between;
}

/* Status badge */
.status-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase;
}

.status--published {
  background: oklch(15% 0.05 148);
  color: oklch(65% 0.13 148);
}

.status--draft {
  background: oklch(18% 0.05 80);
  color: var(--warning);
}

/* Star */
.star-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border-radius: var(--radius-sm);
  border: none; background: none;
  color: var(--text-muted); cursor: pointer;
  transition: color 150ms, background 150ms;
}
.star-btn:hover { color: var(--accent-dim); background: var(--accent-surface); }
.star-btn--active { color: var(--accent); }
.star-btn--sm { width: 24px; height: 24px; flex-shrink: 0; }

.card-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1.3;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.card-desc {
  font-size: var(--text-xs); color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Tags */
.card-tags, .list-tags {
  display: flex; flex-wrap: wrap; gap: var(--sp-1);
  margin-top: auto;
}

.tag-chip {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 7px;
  background: var(--surface-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 600;
  color: var(--text-muted); white-space: nowrap;
}

.tag-chip--more { color: var(--accent-dim); border-color: var(--accent-deep); background: var(--accent-surface); }

/* Card footer */
.card-footer {
  display: flex; align-items: center;
  justify-content: space-between;
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border-subtle);
  margin-top: var(--sp-1);
  gap: var(--sp-2);
}

.card-meta {
  display: flex; align-items: center;
  gap: var(--sp-3); flex-wrap: wrap;
}

.meta-widgets, .meta-time {
  display: flex; align-items: center; gap: 4px;
  font-size: var(--text-xs); color: var(--text-muted);
}

.meta-widgets svg, .meta-time svg { flex-shrink: 0; }

.card-actions {
  display: flex; align-items: center; gap: var(--sp-1);
}

/* ── Action buttons ──────────────────────────────────────── */
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none;
  color: var(--text-muted); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) {
  background: var(--surface-overlay);
  border-color: var(--border-default);
  color: var(--text-secondary);
}
.act-btn--del:hover:not(:disabled) {
  background: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}
.act-btn--yes {
  background: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
  width: auto; padding: 0 var(--sp-2);
}
.act-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.act-btn--publish:hover:not(:disabled) {
  background: oklch(15% 0.05 148); border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148);
}
.act-btn--unpublish:hover:not(:disabled) {
  background: oklch(18% 0.05 80); border-color: var(--warning); color: var(--warning);
}
.act-btn--export:hover:not(:disabled) {
  background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent);
}

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
  height: 260px; border-radius: var(--radius-lg);
  background: linear-gradient(
    90deg,
    var(--surface-raised)  25%,
    var(--surface-overlay) 50%,
    var(--surface-raised)  75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
.card-skel:nth-child(2) { animation-delay: 0.08s; }
.card-skel:nth-child(3) { animation-delay: 0.16s; }
.card-skel:nth-child(4) { animation-delay: 0.24s; }
.card-skel:nth-child(5) { animation-delay: 0.32s; }

/* ── List view ───────────────────────────────────────────── */
.db-list {
  display: flex; flex-direction: column;
  gap: 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  opacity: 0; transition: opacity 300ms;
}
.db-list--visible { opacity: 1; }

.list-head {
  display: grid;
  grid-template-columns: 1fr 110px 160px 80px 100px 110px 160px;
  padding: var(--sp-2) var(--sp-5);
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-display);
  font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase;
  color: var(--text-muted);
}

.list-row {
  display: grid;
  grid-template-columns: 1fr 110px 160px 80px 100px 110px 160px;
  align-items: center;
  gap: var(--sp-3);
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
.list-row--draft { background: oklch(12% 0.02 80 / 0.4); }
.list-row--draft:hover { background: oklch(13% 0.03 80 / 0.5); }

.list-name-cell {
  display: flex; align-items: flex-start; gap: var(--sp-2); min-width: 0;
}
.list-name-block { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.list-name { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.list-desc { font-size: var(--text-xs); color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.list-widgets { font-size: var(--text-sm); color: var(--text-secondary); font-weight: 500; }
.list-time    { font-size: var(--text-xs); color: var(--text-muted); }
.list-author  { font-size: var(--text-xs); color: var(--text-muted); }

.list-actions {
  display: flex; align-items: center; gap: var(--sp-1);
  justify-content: flex-end;
}

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
  z-index: var(--z-modal);
  display: flex; justify-content: flex-end;
}

.drawer {
  width: 500px; max-width: 100vw;
  height: 100dvh;
  background: var(--surface-raised);
  border-left: 1px solid var(--border-default);
  display: flex; flex-direction: column;
  overflow-y: auto;
}

.drawer-hd {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0; position: sticky; top: 0;
  background: var(--surface-raised); z-index: 1;
}

.drawer-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); }

.drawer-close {
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px;
  border-radius: var(--radius-sm); border: 1px solid var(--border-default);
  background: none; color: var(--text-secondary); cursor: pointer;
  transition: all 150ms;
}
.drawer-close:hover { border-color: var(--border-strong); color: var(--text-primary); }

.drawer-form {
  display: flex; flex-direction: column;
  gap: var(--sp-5); padding: var(--sp-6); flex: 1;
}

.form-field { display: flex; flex-direction: column; gap: var(--sp-2); }
.form-label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.req { color: var(--accent-dim); }
.opt { font-size: var(--text-xs); font-weight: 400; color: var(--text-muted); margin-left: 4px; }

.form-input {
  height: 40px; padding: 0 var(--sp-4);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary); font-family: var(--font-ui);
  font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.form-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }
.form-input::placeholder { color: var(--text-muted); }

.form-textarea { height: auto; padding: var(--sp-3) var(--sp-4); resize: none; line-height: 1.55; }

/* Status toggle */
.status-toggle {
  display: flex; gap: var(--sp-2);
}

.status-opt {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: var(--sp-2); padding: var(--sp-2) var(--sp-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none; cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-muted);
  transition: all 150ms;
}
.status-opt:hover { border-color: var(--border-strong); color: var(--text-secondary); }
.status-opt--active {
  border-color: var(--accent-dim);
  background: var(--accent-surface);
  color: var(--accent);
}

/* Template grid */
.tpl-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.tpl-opt {
  display: flex; flex-direction: column;
  align-items: center; gap: var(--sp-1);
  padding: var(--sp-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none; cursor: pointer;
  transition: all 150ms;
  color: var(--border-strong);
}
.tpl-opt:hover { border-color: var(--border-strong); color: var(--text-muted); background: var(--surface-overlay); }
.tpl-opt--active { border-color: var(--accent-dim); background: var(--accent-surface); color: var(--accent-dim); }

.tpl-svg { width: 100%; height: auto; display: block; }

.tpl-label { font-size: 0.65rem; font-weight: 600; color: inherit; white-space: nowrap; }
.tpl-opt--active .tpl-label { color: var(--accent-dim); }

.tpl-desc { font-size: 0.58rem; color: var(--text-muted); text-align: center; line-height: 1.3; }

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

.preview-modal--sm { max-width: 480px; }

.pm-hd {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  gap: var(--sp-4);
}

.pm-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); }
.pm-desc  { font-size: var(--text-sm); color: var(--text-muted); margin-top: var(--sp-1); }

.pm-body {
  flex: 1;
  padding: var(--sp-6);
  position: relative;
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pm-svg { width: 100%; height: auto; max-height: 400px; display: block; }

.pm-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--border-subtle);
}

.pm-meta { font-size: 0.7rem; color: var(--text-muted); }

/* Share modal */
.share-body { padding: var(--sp-5) var(--sp-6); display: flex; flex-direction: column; gap: var(--sp-3); }
.share-label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.share-input-row { display: flex; gap: var(--sp-2); }
.share-input {
  flex: 1;
  height: 40px;
  padding: 0 var(--sp-3);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  outline: none;
  cursor: default;
}
.share-hint { font-size: var(--text-xs); color: var(--text-muted); line-height: 1.5; }
.share-copied { background: oklch(45% 0.13 148) !important; }

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
  .db-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 1100px) {
  .list-head, .list-row { grid-template-columns: 1fr 100px 130px 60px 90px 160px; }
  .list-head span:nth-child(6),
  .list-row .list-author { display: none; }
}

@media (max-width: 900px) {
  .db-page { padding: var(--sp-6); gap: var(--sp-4); }
  .db-grid { grid-template-columns: 1fr; }
  .toolbar { flex-wrap: wrap; }
  .search-wrap { max-width: 100%; }
  .tpl-grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 680px) {
  .db-page { padding: var(--sp-4); }
  .stats-strip { flex-wrap: wrap; }
  .stat-sep { display: none; }
  .stat-item { min-width: 45%; }
  .tpl-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .dash-card, .list-row { animation: none; opacity: 1; transform: none; }
  .card-skel { animation: none; }
}
</style>
