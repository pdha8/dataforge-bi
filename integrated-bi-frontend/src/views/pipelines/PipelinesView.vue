<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api/axios'
import {
  Plus, Search, Play, Square, RotateCcw,
  Trash2, X, ChevronDown, Timer, CalendarClock,
  ArrowRight, ChevronUp, ToggleLeft, Code2,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
type PipelineStatus = 'draft' | 'active' | 'paused' | 'error' | 'archived' | 'deprecated' | 'running' | 'success' | 'failed' | 'scheduled'
type DetailTab = 'executions' | 'transformations' | 'schemas'

interface PipelineExecution {
  id:               string
  status:           string
  status_display:   string
  started_at:       string | null
  completed_at:     string | null
  duration_seconds: number | null
  rows_processed:   number
  rows_failed:      number
  error_message:    string
}

interface PipelineTransformation {
  id:                          string
  name:                        string
  transformation_type:         string
  transformation_type_display: string
  order:                       number
  is_enabled:                  boolean
  description:                 string
}

interface SchemaColumn {
  name:     string
  type?:    string
  nullable?: boolean
}

interface PipelineSchema {
  id:          string
  name:        string
  description: string
  columns?:    SchemaColumn[]
}

interface Pipeline {
  id:                       string
  name:                     string
  description:              string
  pipeline_type_display:    string
  status:                   string
  status_display:           string
  source_name:              string
  target_name:              string
  schedule_enabled:         boolean
  schedule_frequency_display: string
  schedule_cron:            string
  last_execution:           string | null
  last_duration_seconds:    number | null
  total_rows_processed:     number
  success_rate:             number
}

// ── Status metadata ────────────────────────────────────────
const STATUS_META: Record<string, { label: string; cls: string }> = {
  active:     { label: 'Actif',      cls: 'status--success'   },
  paused:     { label: 'En pause',   cls: 'status--paused'    },
  error:      { label: 'Erreur',     cls: 'status--failed'    },
  draft:      { label: 'Brouillon',  cls: 'status--scheduled' },
  archived:   { label: 'Archivé',    cls: 'status--paused'    },
  deprecated: { label: 'Obsolète',   cls: 'status--paused'    },
  running:    { label: 'En cours',   cls: 'status--running'   },
  success:    { label: 'Succès',     cls: 'status--success'   },
  failed:     { label: 'Échec',      cls: 'status--failed'    },
  scheduled:  { label: 'Planifié',   cls: 'status--scheduled' },
}

// ── Schedule presets ───────────────────────────────────────
const SCHEDULE_PRESETS = [
  { label: 'Manuel',      cron: '' },
  { label: '15 min',      cron: '*/15 * * * *' },
  { label: 'Horaire',     cron: '0 * * * *'    },
  { label: 'Quotidien',   cron: '0 2 * * *'    },
  { label: 'Hebdomadaire',cron: '0 2 * * 1'    },
  { label: 'Mensuel',     cron: '0 2 1 * *'    },
]

// ── State ──────────────────────────────────────────────────
const pipelines     = ref<Pipeline[]>([])
const loading       = ref(true)
const listVisible   = ref(false)
const searchQuery   = ref('')
const filterStatus  = ref<PipelineStatus | 'all'>('all')
const drawerOpen    = ref(false)
const deleteConfirm = ref<string | null>(null)
const runningAnim   = ref<Set<string>>(new Set())
const submitting    = ref(false)

// ── Detail panel state ─────────────────────────────────────
const selectedPipeline       = ref<Pipeline | null>(null)
const pipelineTab            = ref<DetailTab>('executions')
const pipelineDetailLoading  = ref(false)
const pipelineExecutions     = ref<PipelineExecution[]>([])
const pipelineTransformations = ref<PipelineTransformation[]>([])
const pipelineSourceSchema   = ref<PipelineSchema | null>(null)
const pipelineTargetSchema   = ref<PipelineSchema | null>(null)
const ddlContent             = ref('')
const ddlLoading             = ref(false)

const form = ref({
  name: '', source: '', destination: '',
  schedule_label: 'Quotidien', cron: '0 2 * * *', description: '',
})

// ── Computed ───────────────────────────────────────────────
const filteredPipelines = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return pipelines.value.filter(p => {
    const matchSearch = !q || p.name.toLowerCase().includes(q)
      || (p.source_name || '').toLowerCase().includes(q)
      || (p.target_name || '').toLowerCase().includes(q)
    const matchStatus = filterStatus.value === 'all' || p.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

const stats = computed(() => {
  const now = Date.now()
  const day = 24 * 3600000
  return {
    total:      pipelines.value.length,
    running:    pipelines.value.filter(p => runningAnim.value.has(p.id)).length,
    successDay: pipelines.value.filter(p =>
      p.status === 'active' && p.last_execution && now - new Date(p.last_execution).getTime() < day
    ).length,
    failedDay:  pipelines.value.filter(p =>
      p.status === 'error' && p.last_execution && now - new Date(p.last_execution).getTime() < day
    ).length,
  }
})

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string): string {
  if (!dateStr) return 'Jamais'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs} h`
  return `${Math.floor(hrs / 24)} j`
}

function lineClass(from: string, to: string): string {
  if (from === 'failed') return 'etl-line--failed'
  if (from === 'success' && to !== 'waiting' && to !== 'skipped') return 'etl-line--active'
  if (from === 'success') return 'etl-line--passed'
  return ''
}

function deriveSteps(status: string): { extract: string; transform: string; load: string } {
  if (status === 'active' || status === 'success')
    return { extract: 'success', transform: 'success', load: 'success' }
  if (status === 'error' || status === 'failed')
    return { extract: 'failed', transform: 'skipped', load: 'skipped' }
  if (status === 'paused')
    return { extract: 'success', transform: 'success', load: 'waiting' }
  if (status === 'running')
    return { extract: 'running', transform: 'waiting', load: 'waiting' }
  return { extract: 'waiting', transform: 'waiting', load: 'waiting' }
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '—'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}m ${s.toString().padStart(2, '0')}s`
}

function getStatusMeta(status: string): { label: string; cls: string } {
  return STATUS_META[status] ?? { label: status, cls: 'status--paused' }
}

// ── API ────────────────────────────────────────────────────
async function fetchPipelines() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/etl/pipelines/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    pipelines.value = rows
  } catch {
    pipelines.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function runPipeline(id: string) {
  if (runningAnim.value.has(id)) return
  runningAnim.value.add(id)
  try {
    await api.post(`/api/etl/pipelines/${id}/execute/`, {})
  } catch { /* ignore */ }
  runningAnim.value.delete(id)
  await fetchPipelines()
}

async function togglePause(p: Pipeline) {
  try {
    await api.post(`/api/etl/pipelines/${p.id}/toggle_status/`, {})
  } catch { /* ignore */ }
  await fetchPipelines()
}

async function deletePipeline(id: string) {
  try {
    await api.delete(`/api/etl/pipelines/${id}/`)
  } catch { /* ignore */ }
  pipelines.value = pipelines.value.filter(p => p.id !== id)
  deleteConfirm.value = null
}

function openDrawer() {
  form.value = { name: '', source: '', destination: '', schedule_label: 'Quotidien', cron: '0 2 * * *', description: '' }
  drawerOpen.value = true
}

function selectPreset(p: typeof SCHEDULE_PRESETS[number]) {
  form.value.schedule_label = p.label
  form.value.cron = p.cron
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  try {
    await api.post('/api/etl/pipelines/', {
      name:                form.value.name,
      description:         form.value.description,
      schedule_enabled:    !!form.value.cron,
      schedule_cron:       form.value.cron || '',
      source_endpoint_type: 'database',
      target_endpoint_type: 'database',
    })
    await fetchPipelines()
  } catch {
    /* ignore */
  } finally {
    submitting.value = false
    drawerOpen.value = false
  }
}

// ── Detail panel helpers ───────────────────────────────────
const EXEC_STATUS_META: Record<string, { label: string; cls: string }> = {
  pending: { label: 'En attente', cls: 'status--scheduled' },
  running: { label: 'En cours',   cls: 'status--running'   },
  success: { label: 'Succès',     cls: 'status--success'   },
  failed:  { label: 'Échec',      cls: 'status--failed'    },
  error:   { label: 'Erreur',     cls: 'status--failed'    },
}

function getExecStatusMeta(status: string) {
  return EXEC_STATUS_META[status] ?? { label: status, cls: 'status--paused' }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ── Detail panel API ───────────────────────────────────────
async function fetchPipelineTab() {
  if (!selectedPipeline.value) return
  const id = selectedPipeline.value.id
  pipelineDetailLoading.value = true
  try {
    if (pipelineTab.value === 'executions') {
      const { data } = await api.get(`/api/etl/pipelines/${id}/executions/`)
      pipelineExecutions.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    } else if (pipelineTab.value === 'transformations') {
      const { data } = await api.get(`/api/etl/pipelines/${id}/transformations/`)
      pipelineTransformations.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    } else if (pipelineTab.value === 'schemas') {
      const [src, tgt] = await Promise.all([
        api.get(`/api/etl/pipelines/${id}/source_schema/`).catch(() => ({ data: null })),
        api.get(`/api/etl/pipelines/${id}/target_schema/`).catch(() => ({ data: null })),
      ])
      pipelineSourceSchema.value = src.data
      pipelineTargetSchema.value = tgt.data
      ddlContent.value = ''
    }
  } catch {
    /* ignore */
  } finally {
    pipelineDetailLoading.value = false
  }
}

async function openPipelineDetail(p: Pipeline) {
  selectedPipeline.value = p
  pipelineTab.value = 'executions'
  await fetchPipelineTab()
}

async function moveTransformation(id: string, direction: 'up' | 'down') {
  try {
    await api.post(`/api/etl/transformations/${id}/move_${direction}/`, {})
    await fetchPipelineTab()
  } catch { /* ignore */ }
}

async function toggleTransformation(id: string) {
  try {
    await api.post(`/api/etl/transformations/${id}/toggle_enabled/`, {})
    await fetchPipelineTab()
  } catch { /* ignore */ }
}

async function generateDDL() {
  if (!pipelineTargetSchema.value) return
  ddlLoading.value = true
  ddlContent.value = ''
  try {
    const { data } = await api.get(`/api/etl/target-schemas/${pipelineTargetSchema.value.id}/generate_ddl/`)
    ddlContent.value = typeof data === 'string' ? data : (data?.ddl ?? JSON.stringify(data, null, 2))
  } catch {
    ddlContent.value = 'Erreur lors de la génération du DDL.'
  } finally {
    ddlLoading.value = false
  }
}

watch(pipelineTab, fetchPipelineTab)

onMounted(fetchPipelines)
</script>

<template>
  <div class="pipelines-page" :class="{ 'pipelines-page--split': selectedPipeline }">
  <div class="pipelines-main">

    <!-- ── Header ──────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Pipelines ETL</h2>
        <p class="page-subtitle">
          {{ stats.total }} pipeline{{ stats.total !== 1 ? 's' : '' }} configuré{{ stats.total !== 1 ? 's' : '' }}
        </p>
      </div>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="15" />
        <span>Nouveau pipeline</span>
      </button>
    </header>

    <!-- ── Stats ───────────────────────────────────────── -->
    <div class="stats-strip">
      <div class="stat-cell">
        <span class="stat-n">{{ stats.total }}</span>
        <span class="stat-l">Total</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--running">{{ stats.running }}</span>
        <span class="stat-l">En cours</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--ok">{{ stats.successDay }}</span>
        <span class="stat-l">Succès (24h)</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--err">{{ stats.failedDay }}</span>
        <span class="stat-l">Échecs (24h)</span>
      </div>
    </div>

    <!-- ── Toolbar ─────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          class="search-input"
          type="search"
          placeholder="Rechercher par nom, source…"
        />
      </div>
      <div class="select-wrap">
        <select v-model="filterStatus" class="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="active">Actif</option>
          <option value="error">Erreur</option>
          <option value="paused">En pause</option>
          <option value="draft">Brouillon</option>
          <option value="archived">Archivé</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>
    </div>

    <!-- ── Column headers ──────────────────────────────── -->
    <div v-if="!loading && filteredPipelines.length > 0" class="col-headers">
      <span>Pipeline</span>
      <span class="col-etl">Étapes ETL</span>
      <span class="col-schedule">Planification</span>
      <span class="col-status">Statut</span>
      <span class="col-actions"></span>
    </div>

    <!-- ── Pipeline list ───────────────────────────────── -->
    <section
      v-if="!loading"
      class="pipeline-list"
      :class="{ 'pipeline-list--visible': listVisible }"
    >

      <!-- Empty state -->
      <div v-if="filteredPipelines.length === 0" class="empty-state">
        <ArrowRight :size="36" class="empty-icon" />
        <p class="empty-title">Aucun pipeline trouvé</p>
        <p class="empty-sub">Créez un pipeline pour automatiser le flux de vos données.</p>
        <button class="btn-primary" @click="openDrawer">
          <Plus :size="14" />
          <span>Créer un pipeline</span>
        </button>
      </div>

      <!-- Pipeline rows -->
      <div
        v-for="(pl, i) in filteredPipelines"
        :key="pl.id"
        class="pipeline-row"
        :class="{
          'pipeline-row--running':   runningAnim.has(pl.id),
          'pipeline-row--failed':    pl.status === 'error',
          'pipeline-row--paused':    pl.status === 'paused',
          'pipeline-row--selected':  selectedPipeline?.id === pl.id,
        }"
        :style="{ '--row-i': i }"
        @click="openPipelineDetail(pl)"
      >

        <!-- Info -->
        <div class="pl-info">
          <p class="pl-name">{{ pl.name }}</p>
          <div class="pl-route">
            <span class="pl-src">{{ pl.source_name || '—' }}</span>
            <ArrowRight :size="11" class="pl-arrow" />
            <span class="pl-dst">{{ pl.target_name || '—' }}</span>
          </div>
          <div class="pl-meta">
            <span v-if="pl.last_duration_seconds">
              <Timer :size="10" class="meta-icon" />{{ formatDuration(pl.last_duration_seconds) }}
            </span>
            <span v-if="pl.total_rows_processed">{{ pl.total_rows_processed.toLocaleString('fr-FR') }} enreg.</span>
          </div>
        </div>

        <!-- ETL step flow -->
        <div class="etl-flow" :title="`Extraire → Transformer → Charger`">
          <div class="etl-node">
            <span class="etl-circle" :class="`etl-circle--${deriveSteps(pl.status).extract}`">E</span>
            <span class="etl-step-label">Extraire</span>
          </div>
          <span class="etl-line" :class="lineClass(deriveSteps(pl.status).extract, deriveSteps(pl.status).transform)"></span>
          <div class="etl-node">
            <span class="etl-circle" :class="`etl-circle--${deriveSteps(pl.status).transform}`">T</span>
            <span class="etl-step-label">Transformer</span>
          </div>
          <span class="etl-line" :class="lineClass(deriveSteps(pl.status).transform, deriveSteps(pl.status).load)"></span>
          <div class="etl-node">
            <span class="etl-circle" :class="`etl-circle--${deriveSteps(pl.status).load}`">L</span>
            <span class="etl-step-label">Charger</span>
          </div>
        </div>

        <!-- Schedule -->
        <div class="pl-schedule">
          <CalendarClock :size="12" class="sched-icon" />
          <div>
            <p class="sched-label">{{ pl.schedule_frequency_display || (pl.schedule_cron ? pl.schedule_cron : 'Manuel') }}</p>
            <p class="sched-last">{{ pl.last_execution ? timeAgo(pl.last_execution) : 'Jamais' }}</p>
          </div>
        </div>

        <!-- Status -->
        <div class="status-badge" :class="getStatusMeta(pl.status).cls">
          <span class="status-dot"></span>
          <span>{{ getStatusMeta(pl.status).label }}</span>
        </div>

        <!-- Actions -->
        <div class="pl-actions" @click.stop>
          <template v-if="deleteConfirm === pl.id">
            <span class="del-label">Supprimer ?</span>
            <button class="action-btn action-btn--yes" @click.stop="deletePipeline(pl.id)">Oui</button>
            <button class="action-btn action-btn--no"  @click.stop="deleteConfirm = null">Non</button>
          </template>
          <template v-else>
            <!-- Run / Pause toggle -->
            <button
              v-if="!runningAnim.has(pl.id)"
              class="action-btn action-btn--run"
              :disabled="runningAnim.has(pl.id)"
              title="Exécuter maintenant"
              @click.stop="runPipeline(pl.id)"
            >
              <Play :size="13" />
            </button>
            <button
              v-if="runningAnim.has(pl.id)"
              class="action-btn action-btn--stop"
              title="Arrêter"
              @click.stop="togglePause(pl)"
            >
              <Square :size="13" />
            </button>
            <!-- Pause / Resume -->
            <button
              v-if="pl.status === 'paused' || pl.status === 'draft'"
              class="action-btn"
              :title="pl.status === 'paused' ? 'Reprendre la planification' : 'Mettre en pause'"
              @click.stop="togglePause(pl)"
            >
              <RotateCcw :size="13" />
            </button>
            <!-- Delete -->
            <button
              class="action-btn action-btn--delete"
              title="Supprimer"
              @click.stop="deleteConfirm = pl.id"
            >
              <Trash2 :size="13" />
            </button>
          </template>
        </div>

        <!-- Running sweep bar -->
        <div v-if="runningAnim.has(pl.id)" class="run-sweep" aria-hidden="true"></div>

      </div>
    </section>

    <!-- ── Skeletons ────────────────────────────────────── -->
    <section v-else class="pipeline-list pipeline-list--visible">
      <div v-for="i in 6" :key="i" class="pipeline-skel"></div>
    </section>

    <!-- ── New pipeline drawer ──────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true">

          <div class="drawer-hd">
            <h3 class="drawer-title">Nouveau pipeline</h3>
            <button class="drawer-close" @click="drawerOpen = false" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- Name -->
            <div class="form-field">
              <label class="form-label" for="pl-name">Nom du pipeline <span class="req">*</span></label>
              <input id="pl-name" v-model="form.name" class="form-input" type="text" placeholder="Ex : Ventes → DW Mensuel" required />
            </div>

            <!-- Source -->
            <div class="form-field">
              <label class="form-label">Source</label>
              <input v-model="form.source" class="form-input" type="text" placeholder="Nom de la source" />
            </div>

            <!-- Destination -->
            <div class="form-field">
              <label class="form-label">Destination</label>
              <input v-model="form.destination" class="form-input" type="text" placeholder="Nom de la destination" />
            </div>

            <!-- Schedule -->
            <div class="form-field">
              <label class="form-label">Planification</label>
              <div class="sched-grid">
                <button
                  v-for="preset in SCHEDULE_PRESETS"
                  :key="preset.label"
                  type="button"
                  class="sched-btn"
                  :class="{ 'sched-btn--active': form.schedule_label === preset.label }"
                  @click="selectPreset(preset)"
                >
                  {{ preset.label }}
                </button>
              </div>
              <div v-if="form.cron" class="cron-display">
                <span class="cron-label">Expression cron</span>
                <code class="cron-code">{{ form.cron }}</code>
              </div>
            </div>

            <!-- ETL preview -->
            <div class="form-field">
              <label class="form-label">Aperçu des étapes</label>
              <div class="etl-preview">
                <div class="etl-prev-step">
                  <span class="etl-prev-num">01</span>
                  <div>
                    <p class="etl-prev-title">Extraire</p>
                    <p class="etl-prev-sub">{{ form.source || 'Source non définie' }}</p>
                  </div>
                </div>
                <ArrowRight :size="14" class="etl-prev-arrow" />
                <div class="etl-prev-step">
                  <span class="etl-prev-num">02</span>
                  <div>
                    <p class="etl-prev-title">Transformer</p>
                    <p class="etl-prev-sub">Normalisation, dédupliq.</p>
                  </div>
                </div>
                <ArrowRight :size="14" class="etl-prev-arrow" />
                <div class="etl-prev-step">
                  <span class="etl-prev-num">03</span>
                  <div>
                    <p class="etl-prev-title">Charger</p>
                    <p class="etl-prev-sub">{{ form.destination || 'Destination non définie' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="!submitting">Créer le pipeline</span>
                <span v-else class="spinner" aria-label="Enregistrement…"></span>
              </button>
            </div>

          </form>
        </aside>
      </div>
    </Transition>

  </div><!-- end pipelines-main -->

  <!-- ── Detail panel ──────────────────────────────────── -->
  <Transition name="detail-anim">
    <aside v-if="selectedPipeline" class="detail-panel" aria-label="Détails du pipeline">

      <!-- Panel header -->
      <div class="detail-hd">
        <div class="detail-hd-info">
          <p class="detail-name">{{ selectedPipeline.name }}</p>
          <div class="status-badge" :class="getStatusMeta(selectedPipeline.status).cls">
            <span class="status-dot"></span>
            <span>{{ getStatusMeta(selectedPipeline.status).label }}</span>
          </div>
        </div>
        <button class="drawer-close" @click="selectedPipeline = null" aria-label="Fermer">
          <X :size="18" />
        </button>
      </div>

      <!-- Tabs -->
      <nav class="detail-tabs">
        <button
          class="detail-tab"
          :class="{ 'detail-tab--active': pipelineTab === 'executions' }"
          @click="pipelineTab = 'executions'"
        >Exécutions</button>
        <button
          class="detail-tab"
          :class="{ 'detail-tab--active': pipelineTab === 'transformations' }"
          @click="pipelineTab = 'transformations'"
        >Transformations</button>
        <button
          class="detail-tab"
          :class="{ 'detail-tab--active': pipelineTab === 'schemas' }"
          @click="pipelineTab = 'schemas'"
        >Schémas</button>
      </nav>

      <!-- Tab content -->
      <div class="detail-body">

        <!-- Loading -->
        <div v-if="pipelineDetailLoading" class="detail-loading">
          <span class="spinner detail-spinner"></span>
        </div>

        <!-- Tab: Executions -->
        <template v-else-if="pipelineTab === 'executions'">
          <div v-if="pipelineExecutions.length === 0" class="detail-empty">Aucune exécution enregistrée.</div>
          <table v-else class="exec-table">
            <thead>
              <tr>
                <th>Statut</th>
                <th>Démarré</th>
                <th>Durée</th>
                <th>Lignes</th>
                <th>Erreurs</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ex in pipelineExecutions" :key="ex.id">
                <td>
                  <div class="status-badge" :class="getExecStatusMeta(ex.status).cls">
                    <span class="status-dot"></span>
                    <span>{{ getExecStatusMeta(ex.status).label }}</span>
                  </div>
                </td>
                <td class="exec-cell--muted">{{ formatDate(ex.started_at) }}</td>
                <td class="exec-cell--muted">{{ formatDuration(ex.duration_seconds) }}</td>
                <td class="exec-cell--muted">{{ ex.rows_processed?.toLocaleString('fr-FR') ?? '—' }}</td>
                <td>
                  <span v-if="ex.rows_failed" class="exec-failed">{{ ex.rows_failed }}</span>
                  <span v-else class="exec-cell--muted">0</span>
                </td>
              </tr>
              <!-- Error messages row (collapsed by default, shown inline) -->
              <template v-for="ex in pipelineExecutions" :key="`err-${ex.id}`">
                <tr v-if="ex.error_message" class="exec-error-row">
                  <td colspan="5" class="exec-error-msg">{{ ex.error_message }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </template>

        <!-- Tab: Transformations -->
        <template v-else-if="pipelineTab === 'transformations'">
          <div v-if="pipelineTransformations.length === 0" class="detail-empty">Aucune transformation configurée.</div>
          <ul v-else class="transf-list">
            <li v-for="tr in pipelineTransformations" :key="tr.id" class="transf-item">
              <span class="transf-order">{{ String(tr.order).padStart(2, '0') }}</span>
              <div class="transf-info">
                <p class="transf-name">{{ tr.name }}</p>
                <p class="transf-type">{{ tr.transformation_type_display }}</p>
              </div>
              <div
                class="status-badge transf-status"
                :class="tr.is_enabled ? 'status--success' : 'status--paused'"
              >
                <span class="status-dot"></span>
                <span>{{ tr.is_enabled ? 'Actif' : 'Inactif' }}</span>
              </div>
              <div class="transf-actions">
                <button class="action-btn" title="Monter" @click="moveTransformation(tr.id, 'up')">
                  <ChevronUp :size="13" />
                </button>
                <button class="action-btn" title="Descendre" @click="moveTransformation(tr.id, 'down')">
                  <ChevronDown :size="13" />
                </button>
                <button
                  class="action-btn"
                  :title="tr.is_enabled ? 'Désactiver' : 'Activer'"
                  @click="toggleTransformation(tr.id)"
                >
                  <ToggleLeft :size="13" />
                </button>
              </div>
            </li>
          </ul>
        </template>

        <!-- Tab: Schemas -->
        <template v-else-if="pipelineTab === 'schemas'">
          <div class="schemas-grid">

            <!-- Source schema -->
            <div class="schema-card">
              <p class="schema-card-title">Schéma source</p>
              <div v-if="pipelineSourceSchema">
                <p class="schema-name">{{ pipelineSourceSchema.name }}</p>
                <p v-if="pipelineSourceSchema.description" class="schema-desc">{{ pipelineSourceSchema.description }}</p>
                <ul v-if="pipelineSourceSchema.columns?.length" class="schema-cols">
                  <li v-for="col in pipelineSourceSchema.columns" :key="col.name" class="schema-col">
                    <span class="col-name">{{ col.name }}</span>
                    <span v-if="col.type" class="col-type">{{ col.type }}</span>
                  </li>
                </ul>
                <p v-else class="detail-empty">Aucune colonne définie.</p>
              </div>
              <p v-else class="detail-empty">Non disponible.</p>
            </div>

            <!-- Target schema -->
            <div class="schema-card">
              <div class="schema-card-hd">
                <p class="schema-card-title">Schéma cible</p>
                <button
                  v-if="pipelineTargetSchema"
                  class="btn-ddl"
                  :disabled="ddlLoading"
                  @click="generateDDL"
                >
                  <Code2 :size="12" />
                  <span>{{ ddlLoading ? '…' : 'Générer DDL' }}</span>
                </button>
              </div>
              <div v-if="pipelineTargetSchema">
                <p class="schema-name">{{ pipelineTargetSchema.name }}</p>
                <p v-if="pipelineTargetSchema.description" class="schema-desc">{{ pipelineTargetSchema.description }}</p>
                <ul v-if="pipelineTargetSchema.columns?.length" class="schema-cols">
                  <li v-for="col in pipelineTargetSchema.columns" :key="col.name" class="schema-col">
                    <span class="col-name">{{ col.name }}</span>
                    <span v-if="col.type" class="col-type">{{ col.type }}</span>
                  </li>
                </ul>
                <p v-else class="detail-empty">Aucune colonne définie.</p>
                <pre v-if="ddlContent" class="ddl-block">{{ ddlContent }}</pre>
              </div>
              <p v-else class="detail-empty">Non disponible.</p>
            </div>

          </div>
        </template>

      </div><!-- end detail-body -->
    </aside>
  </Transition>

  </div><!-- end pipelines-page -->
</template>

<style scoped>
/* ── Page ────────────────────────────────────────────────── */
.pipelines-page {
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 100%;
  align-items: flex-start;
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

.page-subtitle {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}

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
  white-space: nowrap;
  min-height: 38px;
  transition: background-color 150ms ease, box-shadow 150ms ease;
}

.btn-primary:hover:not(:disabled) {
  background-color: oklch(80% 0.14 62);
  box-shadow: 0 4px 16px oklch(76% 0.14 62 / 0.28);
}

.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-ghost {
  display: flex;
  align-items: center;
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
  transition: border-color 150ms ease, color 150ms ease;
}

.btn-ghost:hover { border-color: var(--border-strong); color: var(--text-primary); }

/* ── Stats strip ─────────────────────────────────────────── */
.stats-strip {
  display: flex;
  align-items: stretch;
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stat-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-4) var(--sp-6);
}

.stat-div {
  width: 1px;
  background-color: var(--border-subtle);
  flex-shrink: 0;
  margin: var(--sp-3) 0;
}

.stat-n {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1;
}

.stat-n--running { color: var(--accent); }
.stat-n--ok      { color: oklch(70% 0.15 148); }
.stat-n--err     { color: var(--error); }

.stat-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar {
  display: flex;
  gap: var(--sp-3);
  align-items: center;
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 380px;
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
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms ease;
}

.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }
.w100 { width: 100%; }

.filter-select,
.form-select {
  appearance: none;
  height: 38px;
  padding: 0 30px 0 var(--sp-3);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms ease;
}

.filter-select:focus,
.form-select:focus { border-color: var(--accent-dim); }
.filter-select option,
.form-select option { background-color: var(--surface-raised); }

.select-arrow {
  position: absolute;
  right: 9px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

/* ── Column headers ──────────────────────────────────────── */
.col-headers {
  display: grid;
  grid-template-columns: 1fr 200px 160px 120px 120px;
  gap: var(--sp-4);
  padding: 0 var(--sp-5);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.col-etl     { text-align: center; }
.col-schedule,
.col-status  { }
.col-actions { }

/* ── Pipeline list ───────────────────────────────────────── */
.pipeline-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  opacity: 0;
  transition: opacity 300ms ease;
}

.pipeline-list--visible { opacity: 1; }

/* ── Pipeline row ────────────────────────────────────────── */
.pipeline-row {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 200px 160px 120px 120px;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: background-color 150ms ease, border-color 150ms ease;

  opacity: 0;
  transform: translateY(5px);
  animation: row-in 260ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--row-i, 0) * 35ms);
}

@keyframes row-in {
  to { opacity: 1; transform: none; }
}

.pipeline-row:hover {
  background-color: var(--surface-overlay);
  border-color: var(--border-default);
}

.pipeline-row--running {
  background-color: oklch(12.5% 0.03 62);
  border-color: oklch(22% 0.06 62);
}

.pipeline-row--running:hover {
  background-color: oklch(14% 0.035 62);
}

.pipeline-row--failed {
  background-color: oklch(12.5% 0.035 24);
  border-color: oklch(20% 0.05 24);
}

.pipeline-row--paused {
  opacity: 0.72;
}

/* Running sweep animation at bottom of row */
.run-sweep {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--accent) 50%,
    transparent 100%
  );
  animation: sweep 2.2s linear infinite;
}

@keyframes sweep {
  from { transform: translateX(-100%); }
  to   { transform: translateX(100%); }
}

/* ── Pipeline info ───────────────────────────────────────── */
.pl-info { min-width: 0; }

.pl-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.pl-route {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 3px;
  overflow: hidden;
}

.pl-src,
.pl-dst {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.pl-dst { color: var(--accent-dim); }
.pl-arrow { color: var(--text-muted); flex-shrink: 0; }

.pl-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-top: 4px;
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.pl-meta span {
  display: flex;
  align-items: center;
  gap: 3px;
}

.meta-icon { opacity: 0.7; }

/* ── ETL flow ────────────────────────────────────────────── */
.etl-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.etl-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.etl-circle {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  flex-shrink: 0;
  transition: all 200ms ease;
}

.etl-circle--success {
  background-color: oklch(14% 0.05 148);
  color: oklch(70% 0.15 148);
  border: 1.5px solid oklch(70% 0.15 148);
}

.etl-circle--failed {
  background-color: var(--error-surface);
  color: var(--error);
  border: 1.5px solid var(--error);
}

.etl-circle--running {
  background-color: var(--accent-surface);
  color: var(--accent);
  border: 1.5px solid var(--accent);
  animation: circle-pulse 1.4s ease-in-out infinite;
}

@keyframes circle-pulse {
  0%, 100% { box-shadow: 0 0 0 0 oklch(76% 0.14 62 / 0.4); }
  50%       { box-shadow: 0 0 0 5px oklch(76% 0.14 62 / 0); }
}

.etl-circle--waiting {
  background-color: transparent;
  color: var(--text-muted);
  border: 1.5px solid var(--border-default);
}

.etl-circle--skipped {
  background-color: transparent;
  color: var(--text-muted);
  border: 1.5px dashed var(--border-subtle);
  opacity: 0.45;
}

.etl-step-label {
  font-size: 0.6rem;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.etl-line {
  width: 24px;
  height: 1.5px;
  background-color: var(--border-subtle);
  flex-shrink: 0;
  margin-bottom: 13px;
  transition: background-color 300ms ease;
}

.etl-line--active { background-color: oklch(70% 0.15 148); }
.etl-line--passed { background-color: oklch(50% 0.10 148); }
.etl-line--failed { background-color: var(--error); }

/* ── Schedule ────────────────────────────────────────────── */
.pl-schedule {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
}

.sched-icon { color: var(--text-muted); margin-top: 2px; flex-shrink: 0; }

.sched-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
  line-height: 1.3;
}

.sched-last {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
}

/* ── Status badge ────────────────────────────────────────── */
.status-badge {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-badge span:last-child {
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
}

.status--running   .status-dot { background-color: var(--accent); animation: pulse 1.4s infinite; }
.status--success   .status-dot { background-color: oklch(70% 0.15 148); }
.status--failed    .status-dot { background-color: var(--error); }
.status--paused    .status-dot { background-color: var(--text-muted); }
.status--scheduled .status-dot { background-color: oklch(68% 0.12 230); }

.status--running   span:last-child { color: var(--accent); }
.status--success   span:last-child { color: oklch(70% 0.15 148); }
.status--failed    span:last-child { color: var(--error); }
.status--paused    span:last-child { color: var(--text-muted); }
.status--scheduled span:last-child { color: oklch(68% 0.12 230); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.35; }
}

/* ── Actions ─────────────────────────────────────────────── */
.pl-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  justify-content: flex-end;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 150ms ease;
  flex-shrink: 0;
}

.action-btn:hover:not(:disabled) {
  background-color: var(--surface-overlay);
  border-color: var(--border-strong);
  color: var(--text-secondary);
}

.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.action-btn--run:hover:not(:disabled) {
  background-color: oklch(14% 0.05 148);
  border-color: oklch(70% 0.15 148);
  color: oklch(70% 0.15 148);
}

.action-btn--stop:hover {
  background-color: var(--accent-surface);
  border-color: var(--accent);
  color: var(--accent);
}

.action-btn--delete:hover:not(:disabled) {
  background-color: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}

.del-label {
  font-size: var(--text-xs);
  color: var(--error);
  white-space: nowrap;
}

.action-btn--yes,
.action-btn--no {
  width: auto;
  padding: 0 var(--sp-2);
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  font-weight: 600;
}

.action-btn--yes { background-color: var(--error-surface); border-color: var(--error); color: var(--error); }
.action-btn--no  { color: var(--text-secondary); }

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.pipeline-skel {
  height: 72px;
  border-radius: var(--radius-md);
  background: linear-gradient(
    90deg,
    var(--surface-raised)  25%,
    var(--surface-overlay) 50%,
    var(--surface-raised)  75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.pipeline-skel:nth-child(n+2) { animation-delay: calc((n - 1) * 80ms); }

/* ── Empty state ─────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-24) var(--sp-8);
  text-align: center;
}

.empty-icon   { color: var(--text-muted); margin-bottom: var(--sp-2); }
.empty-title  { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.empty-sub    { font-size: var(--text-sm); color: var(--text-muted); max-width: 42ch; line-height: 1.6; }

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background-color: oklch(5% 0.01 258 / 0.72);
  z-index: var(--z-modal);
  display: flex;
  justify-content: flex-end;
}

.drawer {
  width: 480px;
  max-width: 100vw;
  height: 100dvh;
  background-color: var(--surface-raised);
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
  background-color: var(--surface-raised);
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
  transition: all 150ms ease;
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

.form-input {
  height: 40px;
  padding: 0 var(--sp-4);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms ease;
  width: 100%;
}

.form-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }
.form-input::placeholder { color: var(--text-muted); }

/* ── Schedule grid ───────────────────────────────────────── */
.sched-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-2);
}

.sched-btn {
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  text-align: center;
  transition: all 150ms ease;
}

.sched-btn:hover { background-color: var(--surface-overlay); border-color: var(--border-strong); color: var(--text-primary); }

.sched-btn--active {
  background-color: var(--accent-surface);
  border-color: var(--accent-dim);
  color: var(--accent);
  font-weight: 600;
}

.cron-display {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-2) var(--sp-3);
  background-color: var(--surface-overlay);
  border-radius: var(--radius-sm);
  margin-top: var(--sp-1);
}

.cron-label { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

.cron-code {
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  color: var(--accent-dim);
  letter-spacing: 0.04em;
}

/* ── ETL preview ─────────────────────────────────────────── */
.etl-preview {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4);
  background-color: var(--surface-overlay);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  flex-wrap: nowrap;
  overflow: hidden;
}

.etl-prev-step {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  flex: 1;
  min-width: 0;
}

.etl-prev-num {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--accent-dim);
  line-height: 1;
  flex-shrink: 0;
}

.etl-prev-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1.3;
}

.etl-prev-sub {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 90px;
}

.etl-prev-arrow { color: var(--text-muted); flex-shrink: 0; }

/* ── Drawer footer ───────────────────────────────────────── */
.drawer-footer {
  display: flex;
  gap: var(--sp-3);
  justify-content: flex-end;
  padding-top: var(--sp-4);
  margin-top: auto;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
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

/* ── Drawer transition ───────────────────────────────────── */
.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from,
.drawer-anim-leave-to     { opacity: 0; }

.drawer-anim-enter-active .drawer { transition: transform 380ms var(--ease-out-expo); }
.drawer-anim-leave-active .drawer { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer,
.drawer-anim-leave-to .drawer     { transform: translateX(100%); }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1100px) {
  .pipeline-row   { grid-template-columns: 1fr 180px 140px 110px 100px; }
  .col-headers    { grid-template-columns: 1fr 180px 140px 110px 100px; }
}

@media (max-width: 860px) {
  .pipeline-row {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "info    actions"
      "etl     status"
      "sched   status";
    row-gap: var(--sp-2);
  }
  .col-headers { display: none; }
  .pl-info     { grid-area: info; }
  .etl-flow    { grid-area: etl; justify-content: flex-start; }
  .pl-schedule { grid-area: sched; }
  .status-badge{ grid-area: status; align-self: center; }
  .pl-actions  { grid-area: actions; align-self: start; }
}

@media (max-width: 600px) {
  .pipelines-main { padding: var(--sp-4); }
  .pipeline-row {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "info    actions"
      "etl     etl"
      "sched   status";
  }
  .stat-div  { display: none; }
  .stats-strip { flex-wrap: wrap; }
  .stat-cell { min-width: 45%; }
}

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .pipeline-row     { animation: none; opacity: 1; transform: none; }
  .pipeline-skel    { animation: none; }
  .etl-circle--running { animation: none; }
  .status--running .status-dot { animation: none; }
  .run-sweep        { display: none; }
}

/* ── Split layout ────────────────────────────────────────── */
.pipelines-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  padding: var(--sp-8);
  overflow: hidden;
}

/* ── Selected row highlight ──────────────────────────────── */
.pipeline-row {
  cursor: pointer;
}

.pipeline-row--selected {
  border-color: var(--accent-dim) !important;
  background-color: var(--accent-surface) !important;
}

/* ── Detail panel ────────────────────────────────────────── */
.detail-panel {
  width: 420px;
  flex-shrink: 0;
  height: 100dvh;
  position: sticky;
  top: 0;
  background-color: var(--surface-raised);
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-5) var(--sp-5) var(--sp-4);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.detail-hd-info {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  min-width: 0;
}

.detail-name {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Tabs ────────────────────────────────────────────────── */
.detail-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  padding: 0 var(--sp-2);
}

.detail-tab {
  padding: var(--sp-3) var(--sp-4);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: color 150ms ease, border-color 150ms ease;
  white-space: nowrap;
  margin-bottom: -1px;
}

.detail-tab:hover { color: var(--text-secondary); }

.detail-tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

/* ── Detail body ─────────────────────────────────────────── */
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4) var(--sp-5);
}

.detail-loading {
  display: flex;
  justify-content: center;
  padding: var(--sp-10) 0;
}

.detail-spinner {
  width: 22px;
  height: 22px;
  border-width: 2.5px;
}

.detail-empty {
  font-size: var(--text-sm);
  color: var(--text-muted);
  padding: var(--sp-6) 0;
  text-align: center;
}

/* ── Executions table ────────────────────────────────────── */
.exec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
}

.exec-table th {
  text-align: left;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: var(--sp-2) var(--sp-2) var(--sp-3);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}

.exec-table td {
  padding: var(--sp-2);
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
}

.exec-table tbody tr:last-child td { border-bottom: none; }
.exec-table tbody tr:hover td { background-color: var(--surface-overlay); }

.exec-cell--muted { color: var(--text-muted); }

.exec-failed {
  color: var(--error);
  font-weight: 600;
}

.exec-error-row td { background-color: var(--error-surface); border-bottom: none; }
.exec-error-msg {
  color: var(--error);
  font-size: var(--text-xs);
  padding: var(--sp-2) var(--sp-2) var(--sp-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

/* ── Transformations list ────────────────────────────────── */
.transf-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.transf-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-3);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: border-color 150ms ease;
}

.transf-item:hover { border-color: var(--border-default); }

.transf-order {
  font-family: var(--font-display);
  font-size: 0.9rem;
  font-weight: 800;
  color: var(--accent-dim);
  flex-shrink: 0;
  min-width: 22px;
}

.transf-info {
  flex: 1;
  min-width: 0;
}

.transf-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.transf-type {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
}

.transf-status { flex-shrink: 0; }

.transf-actions {
  display: flex;
  gap: var(--sp-1);
  flex-shrink: 0;
}

/* ── Schemas ─────────────────────────────────────────────── */
.schemas-grid {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.schema-card {
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-4);
}

.schema-card-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
}

.schema-card-title {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: var(--sp-2);
}

.schema-card-hd .schema-card-title { margin-bottom: 0; }

.schema-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--sp-1);
}

.schema-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-bottom: var(--sp-3);
  line-height: 1.5;
}

.schema-cols {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-top: var(--sp-3);
}

.schema-col {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: 3px var(--sp-2);
  background-color: var(--surface-raised);
  border-radius: var(--radius-sm);
}

.col-name {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.col-type {
  font-size: 0.65rem;
  color: var(--accent-dim);
  font-family: 'Courier New', monospace;
  letter-spacing: 0.03em;
}

/* ── DDL button ──────────────────────────────────────────── */
.btn-ddl {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 3px var(--sp-2);
  background-color: var(--accent-surface);
  border: 1px solid var(--accent-dim);
  border-radius: var(--radius-sm);
  color: var(--accent);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background-color 150ms ease;
  white-space: nowrap;
}

.btn-ddl:hover:not(:disabled) { background-color: oklch(14% 0.05 62); }
.btn-ddl:disabled { opacity: 0.55; cursor: not-allowed; }

/* ── DDL block ───────────────────────────────────────────── */
.ddl-block {
  margin-top: var(--sp-3);
  padding: var(--sp-3);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  color: var(--accent-dim);
  overflow-x: auto;
  white-space: pre;
  line-height: 1.6;
  max-height: 240px;
  overflow-y: auto;
}

/* ── Detail panel transition ─────────────────────────────── */
.detail-anim-enter-active { transition: transform 320ms var(--ease-out-expo), opacity 220ms ease; }
.detail-anim-leave-active { transition: transform 200ms cubic-bezier(0.4,0,1,1), opacity 160ms ease; }
.detail-anim-enter-from,
.detail-anim-leave-to {
  transform: translateX(40px);
  opacity: 0;
}

/* ── Responsive for split layout ────────────────────────── */
@media (max-width: 1200px) {
  .detail-panel { width: 380px; }
}

@media (max-width: 900px) {
  .pipelines-page--split { flex-direction: column; }
  .detail-panel {
    width: 100%;
    height: auto;
    max-height: 70dvh;
    position: static;
    border-left: none;
    border-top: 1px solid var(--border-default);
  }
}
</style>
