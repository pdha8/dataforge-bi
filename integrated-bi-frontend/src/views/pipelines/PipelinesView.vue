<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import {
  Plus, Search, Play, Square, RotateCcw, Pause,
  Trash2, Pencil, X, ChevronDown, Timer, CalendarClock,
  ArrowRight, ChevronUp, ToggleLeft, Code2,
  Mail, MessageSquare, Webhook, Hash, Bell, Zap,
  Loader2,
} from 'lucide-vue-next'

const auth = useAuthStore()

// ── Types ──────────────────────────────────────────────────
type PipelineStatus = 'draft' | 'active' | 'paused' | 'error' | 'archived' | 'deprecated' | 'running' | 'success' | 'failed' | 'scheduled'
type DetailTab = 'executions' | 'transformations' | 'dependencies' | 'schemas' | 'etl-notifications' | 'source_schema' | 'target_schema' | 'notifications_pl'

interface DataSourceOption {
  id: string
  name: string
  source_type: string
}

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

interface PipelineNotification {
  id:               string
  pipeline:         string
  pipeline_name:    string
  channel:          'email' | 'sms' | 'webhook' | 'slack'
  recipient:        string
  send_on_start:    boolean
  send_on_success:  boolean
  send_on_failure:  boolean
  is_enabled:       boolean
}

interface SourceSchema {
  id:                 string
  pipeline:           string
  query:              string
  table_name:         string
  filters:            Record<string, any> | null
  selected_columns:   string[] | null
  incremental_column: string
  last_value:         string
}

interface TargetSchemaColumn {
  name:     string
  type?:    string
  nullable?: boolean
}

interface TargetSchema {
  id:               string
  pipeline:         string
  table_name:       string
  schema_name:      string
  columns:          TargetSchemaColumn[] | null
  insert_strategy:  'append' | 'upsert' | 'merge' | 'replace' | 'truncate_insert'
  upsert_keys:      string[] | null
  is_partitioned:   boolean
  partition_column: string
  partition_type:   'range' | 'list' | 'hash' | ''
}

interface PipelineNotificationPl {
  id:               string
  pipeline:         string
  channel:          'email' | 'slack' | 'webhook' | 'teams' | 'sms'
  recipient:        string
  send_on_start:    boolean
  send_on_success:  boolean
  send_on_failure:  boolean
  is_enabled:       boolean
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
const runningAnim   = ref<string[]>([])
const submitting    = ref(false)
const formError     = ref<string | null>(null)
const editPipeline  = ref<Pipeline | null>(null)
const toggleLoading = ref<string | null>(null)

// ── Health & Stats state ───────────────────────────────────
const pipelineHealth = ref<{ healthy: number; warning: number; critical: number; total: number } | null>(null)
const pipelineStats  = ref<{ total: number; active: number; error: number; avg_success_rate: number; total_executions: number } | null>(null)

// ── ETL Notifications state ────────────────────────────────
const etlNotifications  = ref<PipelineNotification[]>([])
const etlNotifsLoading  = ref(false)
const notifDrawerOpen   = ref(false)
const editingNotif      = ref<PipelineNotification | null>(null)
const testingNotifId    = ref<string | null>(null)
const notifForm = ref({
  channel:         'email' as PipelineNotification['channel'],
  recipient:       '',
  send_on_start:   false,
  send_on_success: true,
  send_on_failure: true,
  is_enabled:      true,
})

// ── Data sources for pickers ───────────────────────────────
const dataSources = ref<DataSourceOption[]>([])

async function fetchDataSources() {
  try {
    const { data } = await api.get('/api/data-sources/sources/', { params: { per_page: 500 } })
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    dataSources.value = rows.map((s: any) => ({ id: s.id, name: s.name, source_type: s.source_type || '' }))
  } catch { dataSources.value = [] }
}

// ── Transformation add/delete state ────────────────────────
const transfDrawerOpen = ref(false)
const transfForm = ref({
  name: '',
  transformation_type: 'filter',
  description: '',
  order: 1,
  is_enabled: true,
})
const transfSubmitting = ref(false)
const transfDeleteId = ref<string | null>(null)

const TRANSF_TYPES = [
  { value: 'filter',        label: 'Filtre'           },
  { value: 'map',           label: 'Mapping'          },
  { value: 'aggregate',     label: 'Agrégation'       },
  { value: 'join',          label: 'Jointure'         },
  { value: 'sort',          label: 'Tri'              },
  { value: 'deduplicate',   label: 'Déduplication'    },
  { value: 'validate',      label: 'Validation'       },
  { value: 'enrich',        label: 'Enrichissement'   },
  { value: 'transform',     label: 'Transformation'   },
  { value: 'custom',        label: 'Personnalisé'      },
]

async function openTransfDrawer() {
  transfForm.value = {
    name: '',
    transformation_type: 'filter',
    description: '',
    order: (pipelineTransformations.value.length + 1),
    is_enabled: true,
  }
  transfDrawerOpen.value = true
}

async function submitTransformation() {
  if (!selectedPipeline.value || !transfForm.value.name.trim()) return
  transfSubmitting.value = true
  try {
    await api.post('/api/etl/transformations/', {
      pipeline: selectedPipeline.value.id,
      name: transfForm.value.name,
      transformation_type: transfForm.value.transformation_type,
      description: transfForm.value.description,
      order: transfForm.value.order,
      is_enabled: transfForm.value.is_enabled,
    })
    transfDrawerOpen.value = false
    await fetchPipelineTab()
  } catch { /* ignore */ } finally {
    transfSubmitting.value = false
  }
}

async function deleteTransformation(id: string) {
  try {
    await api.delete(`/api/etl/transformations/${id}/`)
    pipelineTransformations.value = pipelineTransformations.value.filter(t => t.id !== id)
  } catch { /* ignore */ } finally {
    transfDeleteId.value = null
  }
}

// ── Dependencies state ─────────────────────────────────────
const pipelineDependencies = ref<Pipeline[]>([])
const addingDepId = ref<string | null>(null)
const removingDepId = ref<string | null>(null)

async function fetchDependencies() {
  if (!selectedPipeline.value) return
  try {
    const { data } = await api.get(`/api/etl/pipelines/${selectedPipeline.value.id}/dependencies/`)
    const rows = data?.data ?? data?.results ?? data
    pipelineDependencies.value = Array.isArray(rows) ? rows : []
  } catch { pipelineDependencies.value = [] }
}

async function addDependency(depId: string) {
  if (!selectedPipeline.value) return
  addingDepId.value = depId
  try {
    await api.post(`/api/etl/pipelines/${selectedPipeline.value.id}/add_dependency/`, { dependency_id: depId })
    await fetchDependencies()
  } catch { /* ignore */ } finally {
    addingDepId.value = null
  }
}

async function removeDependency(depId: string) {
  if (!selectedPipeline.value) return
  removingDepId.value = depId
  try {
    await api.post(`/api/etl/pipelines/${selectedPipeline.value.id}/remove_dependency/`, { dependency_id: depId })
    await fetchDependencies()
  } catch { /* ignore */ } finally {
    removingDepId.value = null
  }
}

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

// ── Source Schema tab state ────────────────────────────────
const sourceSchema            = ref<SourceSchema | null>(null)
const sourceSchemaLoading     = ref(false)
const sourceSchemaDrawerOpen  = ref(false)
const sourceSchemaSubmitting  = ref(false)
const sourceSchemaForm = ref({
  query:              '',
  table_name:         '',
  filters:            '',
  selected_columns:   '',
  incremental_column: '',
  last_value:         '',
})

// ── Target Schema tab state ────────────────────────────────
const targetSchema            = ref<TargetSchema | null>(null)
const targetSchemaLoading     = ref(false)
const targetSchemaDrawerOpen  = ref(false)
const targetSchemaSubmitting  = ref(false)
const targetSchemaDdlContent  = ref('')
const targetSchemaDdlLoading  = ref(false)
const targetSchemaForm = ref({
  table_name:       '',
  schema_name:      '',
  columns:          '',
  insert_strategy:  'append' as TargetSchema['insert_strategy'],
  upsert_keys:      '',
  is_partitioned:   false,
  partition_column: '',
  partition_type:   '' as TargetSchema['partition_type'],
})

// ── Notifications Pipeline tab state ──────────────────────
const notifPlList         = ref<PipelineNotificationPl[]>([])
const notifPlLoading      = ref(false)
const notifPlDrawerOpen   = ref(false)
const notifPlSubmitting   = ref(false)
const notifPlEditItem     = ref<PipelineNotificationPl | null>(null)
const notifPlTestingId    = ref<string | null>(null)
const notifPlTestResult   = ref<Record<string, 'ok' | 'error'>>({})
const notifPlDeleteId     = ref<string | null>(null)
const notifPlForm = ref({
  channel:         'email' as PipelineNotificationPl['channel'],
  recipient:       '',
  send_on_start:   false,
  send_on_success: true,
  send_on_failure: true,
  is_enabled:      true,
})

const form = ref({
  name: '', source: '', destination: '',
  schedule_label: 'Quotidien', cron: '0 2 * * *', description: '',
  pipeline_type: 'full_load', processing_mode: 'sequential', error_strategy: 'fail_fast',
  batch_size: '', timeout_seconds: '', max_errors: '',
  priority: 5, category: '', tags: '',
  notifications_enabled: false,
  // Politique de réessai
  retry_max_attempts: '3',
  retry_backoff_factor: '2.0',
  retry_delay_seconds: '5',
  // Notifications détaillées
  notify_on_success: false,
  notify_on_start: false,
  notify_on_failure: true,
})

// Drapeau : le nom a été édité manuellement par l'utilisateur
// → on cesse l'auto-génération à partir de Source → Destination
const nameTouched = ref(false)

function onPipelineNameInput() {
  nameTouched.value = true
}

/**
 * Construit "Source → Destination" à partir des selects.
 * Appelé automatiquement quand source ou destination changent,
 * tant que l'utilisateur n'a pas saisi un nom manuel.
 */
function autoBuildPipelineName() {
  if (nameTouched.value) return
  const srcName = dataSources.value.find(s => s.id === form.value.source)?.name
  const dstName = dataSources.value.find(s => s.id === form.value.destination)?.name
  if (srcName && dstName) {
    form.value.name = `${srcName} → ${dstName}`
  } else if (srcName) {
    form.value.name = `${srcName} → …`
  } else if (dstName) {
    form.value.name = `… → ${dstName}`
  }
}

watch(() => [form.value.source, form.value.destination], autoBuildPipelineName)

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
    running:    pipelines.value.filter(p => runningAnim.value.includes(p.id)).length,
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
  if (runningAnim.value.includes(id)) return
  runningAnim.value.push(id)
  try {
    await api.post(`/api/etl/pipelines/${id}/execute/`, {})
  } catch { /* ignore */ }
  runningAnim.value = runningAnim.value.filter(x => x !== id)
  await fetchPipelines()
}

async function toggleStatus(p: Pipeline) {
  if (toggleLoading.value === p.id) return
  toggleLoading.value = p.id
  const newStatus = p.status === 'active' ? 'paused' : 'active'
  try {
    const { data } = await api.post(`/api/etl/pipelines/${p.id}/toggle_status/`, { status: newStatus })
    const payload = data?.data ?? data
    if (payload?.status)         p.status         = payload.status
    if (payload?.status_display) p.status_display = payload.status_display
  } catch { /* ignore */ } finally {
    toggleLoading.value = null
  }
}

/** Alias for stop button on running rows */
async function togglePause(p: Pipeline) {
  await toggleStatus(p)
}

// ── Health & Stats API ─────────────────────────────────────
async function fetchHealth() {
  try {
    const { data } = await api.get('/api/etl/pipelines/health/')
    pipelineHealth.value = data?.data ?? null
  } catch { /* ignore */ }
}

async function fetchStats() {
  try {
    const { data } = await api.get('/api/etl/pipelines/stats/')
    pipelineStats.value = data?.data ?? null
  } catch { /* ignore */ }
}

async function deletePipeline(id: string) {
  try {
    await api.delete(`/api/etl/pipelines/${id}/`)
  } catch { /* ignore */ }
  pipelines.value = pipelines.value.filter(p => p.id !== id)
  deleteConfirm.value = null
}

function openDrawer() {
  editPipeline.value = null
  formError.value = null
  nameTouched.value = false   // reset auto-generation flag pour un nouveau pipeline
  form.value = {
    name: '', source: '', destination: '',
    schedule_label: 'Quotidien', cron: '0 2 * * *', description: '',
    pipeline_type: 'etl', processing_mode: 'batch', error_strategy: 'fail',
    batch_size: '', timeout_seconds: '', max_errors: '',
    priority: 5 as number, category: '', tags: '',
    notifications_enabled: false,
    retry_max_attempts: '3', retry_backoff_factor: '2.0', retry_delay_seconds: '5',
    notify_on_success: false, notify_on_start: false, notify_on_failure: true,
  }
  drawerOpen.value = true
}

function openEditDrawer(p: Pipeline) {
  editPipeline.value = p
  formError.value = null
  nameTouched.value = true   // un pipeline existant a déjà un nom — on ne le réécrit pas
  form.value = {
    name: p.name, source: p.source_name || '', destination: p.target_name || '',
    schedule_label: p.schedule_frequency_display || 'Manuel',
    cron: p.schedule_cron || '', description: p.description || '',
    pipeline_type: 'etl', processing_mode: 'batch', error_strategy: 'fail',
    batch_size: '', timeout_seconds: '', max_errors: '',
    priority: 5 as number, category: '', tags: '',
    notifications_enabled: false,
    retry_max_attempts: '3', retry_backoff_factor: '2.0', retry_delay_seconds: '5',
    notify_on_success: false, notify_on_start: false, notify_on_failure: true,
  }
  drawerOpen.value = true
}

function selectPreset(p: typeof SCHEDULE_PRESETS[number]) {
  form.value.schedule_label = p.label
  form.value.cron = p.cron
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  const payload: Record<string, any> = {
    name:                  form.value.name,
    description:           form.value.description,
    schedule_enabled:      !!form.value.cron,
    schedule_cron:         form.value.cron || '',
    pipeline_type:         form.value.pipeline_type,
    processing_mode:       form.value.processing_mode,
    error_strategy:        form.value.error_strategy,
    priority:              Number(form.value.priority) || 5,
    category:              form.value.category,
    tags:                  form.value.tags ? form.value.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
    notifications_enabled: form.value.notifications_enabled,
  }
  if (form.value.batch_size)         payload.batch_size          = parseInt(form.value.batch_size)
  if (form.value.timeout_seconds)    payload.timeout_seconds     = parseInt(form.value.timeout_seconds)
  if (form.value.max_errors)         payload.max_errors          = parseInt(form.value.max_errors)
  if (form.value.retry_max_attempts) payload.retry_max_attempts  = parseInt(form.value.retry_max_attempts)
  if (form.value.retry_backoff_factor) payload.retry_backoff_factor = parseFloat(form.value.retry_backoff_factor)
  if (form.value.retry_delay_seconds)  payload.retry_delay_seconds  = parseInt(form.value.retry_delay_seconds)
  if (form.value.notifications_enabled) {
    payload.notify_on_success = form.value.notify_on_success
    payload.notify_on_start   = form.value.notify_on_start
    payload.notify_on_failure = form.value.notify_on_failure
  }

  // Backend ETLPipeline attend `source` et `target` (FK), pas `destination`
  if (form.value.source)      payload.source = form.value.source
  if (form.value.destination) payload.target = form.value.destination

  try {
    if (editPipeline.value) {
      await api.patch(`/api/etl/pipelines/${editPipeline.value.id}/`, payload)
    } else {
      payload.source_endpoint_type = 'database'
      payload.target_endpoint_type = 'database'
      await api.post('/api/etl/pipelines/', payload)
    }
    drawerOpen.value = false
    editPipeline.value = null
    await fetchPipelines()
  } catch (err: any) {
    const msg = err?.response?.data?.message ?? err?.response?.data?.detail ?? 'Erreur lors de la sauvegarde. Vérifiez les champs.'
    formError.value = msg
  } finally {
    submitting.value = false
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
      const rows = data?.data ?? data?.results ?? data
      pipelineExecutions.value = Array.isArray(rows) ? rows : []
    } else if (pipelineTab.value === 'transformations') {
      const { data } = await api.get(`/api/etl/pipelines/${id}/transformations/`)
      const rows = data?.data ?? data?.results ?? data
      pipelineTransformations.value = Array.isArray(rows) ? rows : []
    } else if (pipelineTab.value === 'dependencies') {
      await fetchDependencies()
    } else if (pipelineTab.value === 'schemas') {
      const [src, tgt] = await Promise.all([
        api.get(`/api/etl/pipelines/${id}/source_schema/`).catch(() => ({ data: null })),
        api.get(`/api/etl/pipelines/${id}/target_schema/`).catch(() => ({ data: null })),
      ])
      pipelineSourceSchema.value = src.data?.data ?? null
      pipelineTargetSchema.value = tgt.data?.data ?? null
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
    ddlContent.value = typeof data === 'string' ? data : (data?.ddl ?? data?.data ?? JSON.stringify(data, null, 2))
  } catch {
    ddlContent.value = 'Erreur lors de la génération du DDL.'
  } finally {
    ddlLoading.value = false
  }
}

// ── ETL Notifications API ──────────────────────────────────
async function fetchEtlNotifs(pipelineId: string) {
  etlNotifsLoading.value = true
  try {
    const { data } = await api.get('/api/etl/notifications/', { params: { pipeline: pipelineId } })
    etlNotifications.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    etlNotifications.value = []
  } finally {
    etlNotifsLoading.value = false
  }
}

function openNotifDrawer(notif?: PipelineNotification) {
  editingNotif.value = notif ?? null
  if (notif) {
    notifForm.value = {
      channel:         notif.channel,
      recipient:       notif.recipient,
      send_on_start:   notif.send_on_start,
      send_on_success: notif.send_on_success,
      send_on_failure: notif.send_on_failure,
      is_enabled:      notif.is_enabled,
    }
  } else {
    notifForm.value = {
      channel: 'email', recipient: '',
      send_on_start: false, send_on_success: true, send_on_failure: true, is_enabled: true,
    }
  }
  notifDrawerOpen.value = true
}

async function saveEtlNotif() {
  if (!selectedPipeline.value) return
  etlNotifsLoading.value = true
  const payload = { ...notifForm.value, pipeline: selectedPipeline.value.id }
  try {
    if (editingNotif.value) {
      await api.patch(`/api/etl/notifications/${editingNotif.value.id}/`, payload)
    } else {
      await api.post('/api/etl/notifications/', payload)
    }
    notifDrawerOpen.value = false
    editingNotif.value = null
    await fetchEtlNotifs(selectedPipeline.value.id)
  } catch { /* ignore */ } finally {
    etlNotifsLoading.value = false
  }
}

async function deleteEtlNotif(id: string) {
  try {
    await api.delete(`/api/etl/notifications/${id}/`)
    etlNotifications.value = etlNotifications.value.filter(n => n.id !== id)
  } catch { /* ignore */ }
}

async function testEtlNotif(id: string) {
  testingNotifId.value = id
  try {
    await api.post(`/api/etl/notifications/${id}/test/`, {})
  } catch { /* ignore */ } finally {
    testingNotifId.value = null
  }
}

watch(pipelineTab, (tab) => {
  fetchPipelineTab()
  if (tab === 'etl-notifications' && selectedPipeline.value) {
    fetchEtlNotifs(selectedPipeline.value.id)
  }
})

onMounted(() => {
  fetchPipelines()
  fetchHealth()
  fetchStats()
  fetchDataSources()
})
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
      <button
        v-if="auth.canManageETL"
        class="btn-primary"
        @click="openDrawer"
      >
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

    <!-- ── Health strip ──────────────────────────────────── -->
    <div v-if="pipelineStats" class="health-strip">
      <div class="health-cell">
        <span class="health-n">{{ pipelineStats.total }}</span>
        <span class="health-l">Total</span>
      </div>
      <div class="stat-div"></div>
      <div class="health-cell">
        <span class="health-n health-n--ok">{{ pipelineStats.active }}</span>
        <span class="health-l">Actifs</span>
      </div>
      <div class="stat-div"></div>
      <div class="health-cell">
        <span class="health-n health-n--err">{{ pipelineStats.error }}</span>
        <span class="health-l">Erreurs</span>
      </div>
      <div class="stat-div"></div>
      <div class="health-cell">
        <span class="health-n health-n--rate">{{ pipelineStats.avg_success_rate != null ? pipelineStats.avg_success_rate.toFixed(1) + ' %' : '—' }}</span>
        <span class="health-l">Taux de succès</span>
      </div>
      <div class="stat-div"></div>
      <div class="health-cell">
        <span class="health-n">{{ pipelineStats.total_executions?.toLocaleString('fr-FR') ?? '—' }}</span>
        <span class="health-l">Exécutions</span>
      </div>
      <!-- Health indicator from /health/ -->
      <template v-if="pipelineHealth">
        <div class="stat-div"></div>
        <div class="health-cell health-cell--indicator">
          <span
            class="health-dot"
            :class="{
              'health-dot--ok':   pipelineHealth.critical === 0 && pipelineHealth.warning === 0,
              'health-dot--warn': pipelineHealth.critical === 0 && pipelineHealth.warning > 0,
              'health-dot--crit': pipelineHealth.critical > 0,
            }"
          ></span>
          <span class="health-l">
            {{ pipelineHealth.critical > 0 ? 'Critique' : pipelineHealth.warning > 0 ? 'Avertissement' : 'Sain' }}
          </span>
        </div>
      </template>
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
          'pipeline-row--running':   runningAnim.includes(pl.id),
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
              v-if="!runningAnim.includes(pl.id)"
              class="action-btn action-btn--run"
              :disabled="runningAnim.includes(pl.id) || pl.status !== 'active'"
              :title="pl.status !== 'active' ? 'Activez le pipeline pour l\'exécuter' : 'Exécuter maintenant'"
              @click.stop="runPipeline(pl.id)"
            >
              <Play :size="13" />
            </button>
            <button
              v-if="runningAnim.includes(pl.id)"
              class="action-btn action-btn--stop"
              title="Arrêter"
              @click.stop="togglePause(pl)"
            >
              <Square :size="13" />
            </button>
            <!-- Toggle Status (Activer / Mettre en pause) -->
            <button
              class="action-btn action-btn--toggle"
              :title="pl.status === 'active' ? 'Mettre en pause' : 'Activer'"
              :disabled="toggleLoading === pl.id"
              @click.stop="toggleStatus(pl)"
            >
              <span v-if="toggleLoading === pl.id" class="spinner spinner--dark" aria-label="Chargement…"></span>
              <Pause v-else-if="pl.status === 'active'" :size="13" />
              <Play  v-else                             :size="13" />
            </button>
            <!-- Pause / Resume (legacy RotateCcw kept for running rows) -->
            <button
              v-if="pl.status === 'paused' || pl.status === 'draft'"
              class="action-btn"
              :title="pl.status === 'paused' ? 'Reprendre la planification' : 'Mettre en pause'"
              @click.stop="togglePause(pl)"
            >
              <RotateCcw :size="13" />
            </button>
            <!-- Edit -->
            <button
              class="action-btn"
              title="Modifier"
              @click.stop="openEditDrawer(pl)"
            >
              <Pencil :size="13" />
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
        <div v-if="runningAnim.includes(pl.id)" class="run-sweep" aria-hidden="true"></div>

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
            <h3 class="drawer-title">{{ editPipeline ? 'Modifier le pipeline' : 'Nouveau pipeline' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false; editPipeline = null" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- Source -->
            <div class="form-field">
              <label class="form-label" for="pl-source">Source de données <span class="req">*</span></label>
              <div class="select-wrap">
                <select id="pl-source" v-model="form.source" class="form-input" required>
                  <option value="">— Sélectionner une source —</option>
                  <option v-for="src in dataSources" :key="src.id" :value="src.id">
                    {{ src.name }} <template v-if="src.source_type">({{ src.source_type }})</template>
                  </option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>

            <!-- Destination -->
            <div class="form-field">
              <label class="form-label" for="pl-dest">Destination (source cible) <span class="req">*</span></label>
              <div class="select-wrap">
                <select id="pl-dest" v-model="form.destination" class="form-input" required>
                  <option value="">— Sélectionner une destination —</option>
                  <option v-for="src in dataSources" :key="src.id" :value="src.id">
                    {{ src.name }} <template v-if="src.source_type">({{ src.source_type }})</template>
                  </option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>

            <!-- Name : auto-généré à partir des sélecteurs Source → Destination -->
            <div class="form-field">
              <label class="form-label" for="pl-name">
                Nom du pipeline <span class="req">*</span>
                <span v-if="!nameTouched && (form.source || form.destination)" class="opt">(auto-généré)</span>
              </label>
              <input
                id="pl-name"
                v-model="form.name"
                class="form-input"
                type="text"
                placeholder="Sélectionnez Source et Destination pour générer le nom"
                required
                @input="onPipelineNameInput"
              />
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
                    <p class="etl-prev-sub">{{ dataSources.find(s => s.id === form.source)?.name || form.source || 'Source non définie' }}</p>
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
                    <p class="etl-prev-sub">{{ dataSources.find(s => s.id === form.destination)?.name || form.destination || 'Destination non définie' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Advanced options -->
            <details class="adv-section">
              <summary class="adv-summary">Options avancées</summary>
              <div class="adv-body">

                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label">Type de pipeline</label>
                    <div class="select-wrap w100">
                      <select v-model="form.pipeline_type" class="form-select w100">
                        <option value="etl">ETL (Extract-Transform-Load)</option>
                        <option value="elt">ELT (Extract-Load-Transform)</option>
                        <option value="extract">Extract Only</option>
                        <option value="load">Load Only</option>
                        <option value="replication">Réplication</option>
                        <option value="migration">Migration</option>
                        <option value="aggregation">Agrégation</option>
                        <option value="cleaning">Nettoyage</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label">Priorité (1 = haute, 10 = basse)</label>
                    <div class="select-wrap w100">
                      <select v-model.number="form.priority" class="form-select w100">
                        <option :value="1">1 — Critique</option>
                        <option :value="3">3 — Haute</option>
                        <option :value="5">5 — Normale</option>
                        <option :value="7">7 — Faible</option>
                        <option :value="10">10 — Différable</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                </div>

                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label">Mode de traitement</label>
                    <div class="select-wrap w100">
                      <select v-model="form.processing_mode" class="form-select w100">
                        <option value="batch">Batch</option>
                        <option value="streaming">Streaming</option>
                        <option value="incremental">Incrémental</option>
                        <option value="full">Full Refresh</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label">Stratégie d'erreur</label>
                    <div class="select-wrap w100">
                      <select v-model="form.error_strategy" class="form-select w100">
                        <option value="fail">Échec pipeline</option>
                        <option value="skip">Ignorer la ligne</option>
                        <option value="default">Valeur par défaut</option>
                        <option value="retry">Réessayer</option>
                        <option value="notify">Notifier uniquement</option>
                        <option value="continue">Continuer</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                </div>

                <div class="form-row-3">
                  <div class="form-field">
                    <label class="form-label">Taille lot</label>
                    <input v-model="form.batch_size" class="form-input" type="number" min="1" placeholder="1000" />
                  </div>
                  <div class="form-field">
                    <label class="form-label">Timeout (s)</label>
                    <input v-model="form.timeout_seconds" class="form-input" type="number" min="0" placeholder="3600" />
                  </div>
                  <div class="form-field">
                    <label class="form-label">Max erreurs</label>
                    <input v-model="form.max_errors" class="form-input" type="number" min="0" placeholder="0" />
                  </div>
                </div>

                <div class="form-field">
                  <label class="form-label">Catégorie</label>
                  <input v-model="form.category" class="form-input" type="text" placeholder="Ex : Finances, Ventes…" />
                </div>

                <div class="form-field">
                  <label class="form-label">Tags <span class="opt">séparés par virgule</span></label>
                  <input v-model="form.tags" class="form-input" type="text" placeholder="etl, production, mensuel" />
                </div>

                <label class="toggle-label">
                  <input v-model="form.notifications_enabled" type="checkbox" class="form-checkbox" />
                  <span>Activer les notifications</span>
                </label>

                <!-- Notifications détaillées (si activé) -->
                <template v-if="form.notifications_enabled">
                  <div class="form-field" style="margin-top: var(--sp-3); padding-left: var(--sp-4); border-left: 2px solid var(--border-subtle);">
                    <label class="toggle-label">
                      <input v-model="form.notify_on_start" type="checkbox" class="form-checkbox" />
                      <span>Notifier au démarrage</span>
                    </label>
                    <label class="toggle-label" style="margin-top: var(--sp-2);">
                      <input v-model="form.notify_on_success" type="checkbox" class="form-checkbox" />
                      <span>Notifier en cas de succès</span>
                    </label>
                    <label class="toggle-label" style="margin-top: var(--sp-2);">
                      <input v-model="form.notify_on_failure" type="checkbox" class="form-checkbox" />
                      <span>Notifier en cas d'échec</span>
                    </label>
                  </div>
                </template>

              </div>
            </details>

            <!-- ── Advanced: Politique de réessai ────────── -->
            <details class="adv-section">
              <summary class="adv-summary">Politique de réessai</summary>
              <div class="adv-body">
                <div class="form-row-3">
                  <div class="form-field">
                    <label class="form-label">Tentatives max</label>
                    <input v-model="form.retry_max_attempts" class="form-input" type="number" min="0" max="10" placeholder="3" />
                  </div>
                  <div class="form-field">
                    <label class="form-label">Facteur de backoff</label>
                    <input v-model="form.retry_backoff_factor" class="form-input" type="number" min="0" step="0.1" placeholder="2.0" />
                  </div>
                  <div class="form-field">
                    <label class="form-label">Délai initial (s)</label>
                    <input v-model="form.retry_delay_seconds" class="form-input" type="number" min="0" placeholder="5" />
                  </div>
                </div>
              </div>
            </details>

            <p v-if="formError" style="color:var(--color-danger,#ef4444);font-size:0.8rem;margin:0 0 var(--sp-3);">{{ formError }}</p>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false; editPipeline = null; formError = null">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="!submitting">{{ editPipeline ? 'Enregistrer' : 'Créer le pipeline' }}</span>
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
          :class="{ 'detail-tab--active': pipelineTab === 'dependencies' }"
          @click="pipelineTab = 'dependencies'"
        >Dépendances</button>
        <button
          class="detail-tab"
          :class="{ 'detail-tab--active': pipelineTab === 'schemas' }"
          @click="pipelineTab = 'schemas'"
        >Schémas</button>
        <button
          class="detail-tab"
          :class="{ 'detail-tab--active': pipelineTab === 'etl-notifications' }"
          @click="pipelineTab = 'etl-notifications'"
        >Notifications</button>
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
          <div class="transf-tab-hd">
            <span class="transf-tab-count">{{ pipelineTransformations.length }} transformation{{ pipelineTransformations.length !== 1 ? 's' : '' }}</span>
            <button class="btn-primary btn-sm" @click="openTransfDrawer">
              <Plus :size="12" />
              <span>Ajouter</span>
            </button>
          </div>
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
                <template v-if="transfDeleteId === tr.id">
                  <button class="action-btn action-btn--yes" @click="deleteTransformation(tr.id)">Oui</button>
                  <button class="action-btn" @click="transfDeleteId = null">Non</button>
                </template>
                <button v-else class="action-btn action-btn--del" title="Supprimer" @click="transfDeleteId = tr.id">
                  <Trash2 :size="12" />
                </button>
              </div>
            </li>
          </ul>

          <!-- Add Transformation drawer -->
          <Transition name="drawer-anim">
            <div v-if="transfDrawerOpen" class="drawer-overlay" @click.self="transfDrawerOpen = false">
              <aside class="drawer" role="dialog" aria-modal="true" aria-label="Nouvelle transformation">
                <div class="drawer-hd">
                  <h3 class="drawer-title">Ajouter une transformation</h3>
                  <button class="drawer-close" @click="transfDrawerOpen = false"><X :size="18" /></button>
                </div>
                <form class="drawer-form" @submit.prevent="submitTransformation">
                  <div class="form-field">
                    <label class="form-label">Nom <span class="req">*</span></label>
                    <input v-model="transfForm.name" class="form-input" type="text" placeholder="Nom de la transformation" required />
                  </div>
                  <div class="form-field">
                    <label class="form-label">Type</label>
                    <div class="select-wrap">
                      <select v-model="transfForm.transformation_type" class="form-input">
                        <option v-for="t in TRANSF_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow" />
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label">Description</label>
                    <textarea v-model="transfForm.description" class="form-input form-textarea" rows="2" placeholder="Description optionnelle"></textarea>
                  </div>
                  <div class="form-field">
                    <label class="form-label">Ordre</label>
                    <input v-model.number="transfForm.order" class="form-input" type="number" min="1" />
                  </div>
                  <div class="form-field form-field--checkbox">
                    <label class="form-label">
                      <input v-model="transfForm.is_enabled" type="checkbox" class="form-checkbox" />
                      Activée
                    </label>
                  </div>
                  <div class="drawer-foot">
                    <button type="button" class="btn-ghost" @click="transfDrawerOpen = false">Annuler</button>
                    <button type="submit" class="btn-primary" :disabled="transfSubmitting">
                      {{ transfSubmitting ? 'Enregistrement…' : 'Ajouter' }}
                    </button>
                  </div>
                </form>
              </aside>
            </div>
          </Transition>
        </template>

        <!-- Tab: Dependencies -->
        <template v-else-if="pipelineTab === 'dependencies'">
          <div class="transf-tab-hd">
            <span class="transf-tab-count">{{ pipelineDependencies.length }} dépendance{{ pipelineDependencies.length !== 1 ? 's' : '' }}</span>
          </div>
          <div v-if="pipelineDependencies.length === 0" class="detail-empty">Aucune dépendance configurée.</div>
          <ul v-else class="transf-list">
            <li v-for="dep in pipelineDependencies" :key="dep.id" class="transf-item">
              <div class="transf-info">
                <p class="transf-name">{{ dep.name }}</p>
                <p class="transf-type">{{ dep.status_display || dep.status }}</p>
              </div>
              <div class="transf-actions">
                <button
                  class="action-btn action-btn--del"
                  title="Retirer cette dépendance"
                  :disabled="removingDepId === dep.id"
                  @click="removeDependency(dep.id)"
                >
                  <Trash2 :size="12" />
                </button>
              </div>
            </li>
          </ul>
          <!-- Add dependency: pick from other pipelines -->
          <div class="dep-add-row">
            <p class="dep-add-label">Ajouter un pipeline prérequis :</p>
            <div class="dep-picker">
              <div class="select-wrap">
                <select class="form-input form-input--sm" @change="e => { const v = (e.target as HTMLSelectElement).value; if(v) addDependency(v) }">
                  <option value="">— Choisir un pipeline —</option>
                  <option
                    v-for="p in pipelines.filter(p => p.id !== selectedPipeline?.id && !pipelineDependencies.find(d => d.id === p.id))"
                    :key="p.id"
                    :value="p.id"
                  >{{ p.name }}</option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>
          </div>
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

        <!-- Tab: ETL Notifications -->
        <template v-else-if="pipelineTab === 'etl-notifications'">

          <!-- Loading -->
          <div v-if="etlNotifsLoading && etlNotifications.length === 0" class="detail-loading">
            <span class="spinner detail-spinner"></span>
          </div>

          <template v-else>
            <!-- Header row -->
            <div class="notif-tab-hd">
              <span class="notif-tab-title">Canaux de notification</span>
              <button class="btn-ddl" @click="openNotifDrawer()">
                <Plus :size="12" />
                <span>Ajouter</span>
              </button>
            </div>

            <!-- Empty state -->
            <div v-if="etlNotifications.length === 0" class="detail-empty">
              Aucune notification configurée.
            </div>

            <!-- Notifications table -->
            <table v-else class="exec-table notif-table">
              <thead>
                <tr>
                  <th>Canal</th>
                  <th>Destinataire</th>
                  <th>Conditions</th>
                  <th>Actif</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="notif in etlNotifications" :key="notif.id">
                  <!-- Canal icon + label -->
                  <td>
                    <div class="notif-channel">
                      <Mail    v-if="notif.channel === 'email'"   :size="13" class="notif-icon notif-icon--email" />
                      <MessageSquare v-else-if="notif.channel === 'sms'" :size="13" class="notif-icon notif-icon--sms" />
                      <Hash    v-else-if="notif.channel === 'slack'"   :size="13" class="notif-icon notif-icon--slack" />
                      <Webhook v-else                             :size="13" class="notif-icon notif-icon--webhook" />
                      <span class="notif-channel-label">{{ notif.channel }}</span>
                    </div>
                  </td>
                  <!-- Destinataire -->
                  <td class="exec-cell--muted notif-recipient">{{ notif.recipient || '—' }}</td>
                  <!-- Conditions -->
                  <td>
                    <div class="notif-conditions">
                      <span v-if="notif.send_on_start"   class="notif-cond notif-cond--start">Début</span>
                      <span v-if="notif.send_on_success" class="notif-cond notif-cond--ok">Succès</span>
                      <span v-if="notif.send_on_failure" class="notif-cond notif-cond--err">Échec</span>
                    </div>
                  </td>
                  <!-- Activé -->
                  <td>
                    <span
                      class="status-badge"
                      :class="notif.is_enabled ? 'status--success' : 'status--paused'"
                    >
                      <span class="status-dot"></span>
                      <span>{{ notif.is_enabled ? 'Oui' : 'Non' }}</span>
                    </span>
                  </td>
                  <!-- Actions -->
                  <td>
                    <div class="transf-actions">
                      <!-- Tester -->
                      <button
                        class="action-btn"
                        title="Tester le canal"
                        :disabled="testingNotifId === notif.id"
                        @click="testEtlNotif(notif.id)"
                      >
                        <span v-if="testingNotifId === notif.id" class="spinner spinner--dark"></span>
                        <Zap v-else :size="12" />
                      </button>
                      <!-- Modifier -->
                      <button class="action-btn" title="Modifier" @click="openNotifDrawer(notif)">
                        <Pencil :size="12" />
                      </button>
                      <!-- Supprimer -->
                      <button class="action-btn action-btn--delete" title="Supprimer" @click="deleteEtlNotif(notif.id)">
                        <Trash2 :size="12" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </template>

          <!-- Drawer création/modification notification -->
          <Teleport to="body">
            <Transition name="drawer-anim">
              <div v-if="notifDrawerOpen" class="drawer-overlay" @click.self="notifDrawerOpen = false">
                <aside class="drawer" role="dialog" aria-modal="true">
                  <div class="drawer-hd">
                    <h3 class="drawer-title">{{ editingNotif ? 'Modifier notification' : 'Nouvelle notification' }}</h3>
                    <button class="drawer-close" @click="notifDrawerOpen = false" aria-label="Fermer">
                      <X :size="18" />
                    </button>
                  </div>

                  <div class="drawer-form">
                    <!-- Canal -->
                    <div class="form-field">
                      <label class="form-label">Canal <span class="req">*</span></label>
                      <div class="select-wrap w100">
                        <select v-model="notifForm.channel" class="form-select w100">
                          <option value="email">Email</option>
                          <option value="sms">SMS</option>
                          <option value="webhook">Webhook</option>
                          <option value="slack">Slack</option>
                        </select>
                        <ChevronDown :size="13" class="select-arrow" />
                      </div>
                    </div>

                    <!-- Destinataire -->
                    <div class="form-field">
                      <label class="form-label">Destinataire</label>
                      <input
                        v-model="notifForm.recipient"
                        class="form-input"
                        type="text"
                        :placeholder="notifForm.channel === 'email' ? 'email@exemple.com'
                          : notifForm.channel === 'sms' ? '+33600000000'
                          : notifForm.channel === 'slack' ? '#canal-slack'
                          : 'https://hooks.exemple.com/...'"
                      />
                    </div>

                    <!-- Conditions -->
                    <div class="form-field">
                      <label class="form-label">Envoyer lors de</label>
                      <div class="notif-checks">
                        <label class="toggle-label">
                          <input v-model="notifForm.send_on_start"   type="checkbox" class="form-checkbox" />
                          <span>Démarrage</span>
                        </label>
                        <label class="toggle-label">
                          <input v-model="notifForm.send_on_success" type="checkbox" class="form-checkbox" />
                          <span>Succès</span>
                        </label>
                        <label class="toggle-label">
                          <input v-model="notifForm.send_on_failure" type="checkbox" class="form-checkbox" />
                          <span>Échec</span>
                        </label>
                      </div>
                    </div>

                    <!-- Activer -->
                    <div class="form-field">
                      <label class="toggle-label">
                        <input v-model="notifForm.is_enabled" type="checkbox" class="form-checkbox" />
                        <span>Notification activée</span>
                      </label>
                    </div>

                    <div class="drawer-footer">
                      <button type="button" class="btn-ghost" @click="notifDrawerOpen = false">Annuler</button>
                      <button
                        type="button"
                        class="btn-primary"
                        :disabled="etlNotifsLoading"
                        @click="saveEtlNotif"
                      >
                        <span v-if="!etlNotifsLoading">{{ editingNotif ? 'Enregistrer' : 'Créer' }}</span>
                        <span v-else class="spinner" aria-label="Enregistrement…"></span>
                      </button>
                    </div>
                  </div>
                </aside>
              </div>
            </Transition>
          </Teleport>

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

/* ── Advanced section ────────────────────────────────────── */
.adv-section { border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; }
.adv-summary {
  padding: var(--sp-3) var(--sp-4);
  font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary);
  cursor: pointer; list-style: none; display: flex; align-items: center;
  justify-content: space-between;
  background: var(--surface-overlay);
}
.adv-summary::-webkit-details-marker { display: none; }
.adv-summary::after { content: '›'; font-size: 1.1rem; color: var(--text-muted); transition: transform 200ms; }
details[open] .adv-summary::after { transform: rotate(90deg); }
.adv-body { padding: var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-4); }

.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--sp-3); }
.form-select {
  appearance: none; height: 40px; padding: 0 30px 0 var(--sp-3);
  background: var(--surface-overlay); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none; cursor: pointer;
  transition: border-color 150ms;
}
.form-select:focus { border-color: var(--accent-dim); }
.form-select option { background: var(--surface-raised); }
.w100 { width: 100%; }

.form-checkbox { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
.toggle-label {
  display: flex; align-items: center; gap: var(--sp-2);
  font-size: var(--text-sm); color: var(--text-secondary); cursor: pointer;
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
.action-btn--yes { color: oklch(65% 0.13 148); }
.action-btn--del { color: oklch(64% 0.19 24); }

.transf-tab-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-2) var(--sp-4);
  border-bottom: 1px solid var(--border-subtle);
}
.transf-tab-count { font-size: var(--text-xs); color: var(--text-muted); }
.btn-sm { padding: var(--sp-1) var(--sp-2); font-size: var(--text-xs); }

.dep-add-row {
  padding: var(--sp-3) var(--sp-4);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}
.dep-add-label { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap; }
.dep-picker { flex: 1; min-width: 200px; }
.form-input--sm { font-size: var(--text-xs); padding: var(--sp-1) var(--sp-2); }

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

/* ── Health strip ────────────────────────────────────────── */
.health-strip {
  display: flex;
  align-items: stretch;
  background: linear-gradient(135deg, var(--surface-raised) 0%, var(--surface-overlay) 100%);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-wrap: wrap;
}

.health-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-3) var(--sp-5);
  min-width: 80px;
}

.health-cell--indicator {
  flex-direction: row;
  align-items: center;
  gap: var(--sp-2);
}

.health-n {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1;
}

.health-n--ok   { color: oklch(70% 0.15 148); }
.health-n--err  { color: var(--error); }
.health-n--rate { color: var(--accent); }

.health-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.health-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-dot--ok   { background-color: oklch(70% 0.15 148); box-shadow: 0 0 6px oklch(70% 0.15 148 / 0.5); }
.health-dot--warn { background-color: oklch(75% 0.14 85);  box-shadow: 0 0 6px oklch(75% 0.14 85 / 0.5);  }
.health-dot--crit { background-color: var(--error);        box-shadow: 0 0 6px var(--error-surface);       animation: pulse 1.4s infinite; }

/* ── Toggle button ───────────────────────────────────────── */
.action-btn--toggle:hover:not(:disabled) {
  background-color: var(--accent-surface);
  border-color: var(--accent-dim);
  color: var(--accent);
}

/* ── Spinner dark variant (used inside light buttons) ────── */
.spinner--dark {
  border-color: var(--border-strong);
  border-top-color: var(--text-secondary);
}

/* ── ETL Notifications tab ───────────────────────────────── */
.notif-tab-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

.notif-tab-title {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.notif-table { font-size: var(--text-xs); }

.notif-channel {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
}

.notif-channel-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: capitalize;
}

.notif-icon { flex-shrink: 0; }
.notif-icon--email   { color: oklch(68% 0.12 230); }
.notif-icon--sms     { color: oklch(70% 0.15 148); }
.notif-icon--slack   { color: oklch(70% 0.18 290); }
.notif-icon--webhook { color: var(--accent-dim); }

.notif-recipient {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notif-conditions {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}

.notif-cond {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 1px 5px;
  border-radius: 3px;
  text-transform: uppercase;
}

.notif-cond--start { background-color: oklch(16% 0.04 230); color: oklch(68% 0.12 230); }
.notif-cond--ok    { background-color: oklch(14% 0.05 148); color: oklch(70% 0.15 148); }
.notif-cond--err   { background-color: var(--error-surface); color: var(--error); }

.notif-checks {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
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
