<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
import {
  Plus, Search, RefreshCcw, Database, FileText,
  CheckCircle2, Clock,
  Trash2, X, ChevronDown, UploadCloud,
  Table2, Activity, BarChart2, Star, Play,
  Pencil, Eye, EyeOff, Shield, Settings, Tag,
  Loader2, RotateCcw, Code2,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
interface DataSource {
  id: string
  name: string
  source_type: string
  source_type_display: string
  host: string
  port: number | null
  database_name: string
  status: string
  status_display: string
  last_sync: string | null
  description: string
  is_connected: boolean
  total_queries: number
  data_quality_score: number
  success_rate: number
  health_status: string
  updated_at: string
}

// ── DB types list ──────────────────────────────────────────
const DB_TYPES = new Set([
  'postgresql', 'mysql', 'oracle', 'sqlite', 'sqlserver',
  'db2', 'mongodb', 'elasticsearch', 'cassandra', 'redis', 'dynamodb',
])

function isDbSource(sourceType: string): boolean {
  return DB_TYPES.has(sourceType)
}

// ── Metadata ───────────────────────────────────────────────
const TYPE_META: Record<string, { label: string; color: string; abbr: string }> = {
  postgresql: { label: 'PostgreSQL', color: 'oklch(62% 0.13 240)', abbr: 'PG'  },
  mysql:      { label: 'MySQL',      color: 'oklch(70% 0.13 52)',  abbr: 'MY'  },
  oracle:     { label: 'Oracle',     color: 'oklch(64% 0.15 30)',  abbr: 'OR'  },
  csv:        { label: 'CSV',        color: 'oklch(68% 0.14 148)', abbr: 'CSV' },
  rest_api:   { label: 'API REST',   color: 'oklch(62% 0.12 290)', abbr: 'API' },
  excel:      { label: 'Excel',      color: 'oklch(58% 0.15 148)', abbr: 'XLS' },
  mongodb:    { label: 'MongoDB',    color: 'oklch(60% 0.16 155)', abbr: 'MDB' },
}

const STATUS_META: Record<string, { label: string; cls: string }> = {
  active:      { label: 'Actif',         cls: 'status--active'   },
  error:       { label: 'Erreur',        cls: 'status--error'    },
  inactive:    { label: 'Inactif',       cls: 'status--inactive' },
  testing:     { label: 'En test',       cls: 'status--pending'  },
  configuring: { label: 'Configuration', cls: 'status--pending'  },
  draft:       { label: 'Brouillon',     cls: 'status--inactive' },
  archived:    { label: 'Archivé',       cls: 'status--inactive' },
  deprecated:  { label: 'Obsolète',      cls: 'status--inactive' },
  pending:     { label: 'En attente',    cls: 'status--pending'  },
}

function getTypeMeta(sourceType: string): { label: string; color: string; abbr: string } {
  return TYPE_META[sourceType] ?? { label: sourceType || 'Inconnu', color: 'oklch(65% 0.08 258)', abbr: (sourceType || '?').slice(0, 3).toUpperCase() }
}
function getStatusMeta(status: string): { label: string; cls: string } {
  return STATUS_META[status] ?? { label: status || 'Inconnu', cls: 'status--inactive' }
}

// ── State ──────────────────────────────────────────────────
const sources       = ref<DataSource[]>([])
const loading       = ref(true)
const searchQuery   = ref('')
const filterType    = ref('all')
const filterStatus  = ref('all')
const drawerOpen    = ref(false)
const testingId     = ref<string | null>(null)
const testedOk      = ref<string | null>(null)
const deleteConfirm = ref<string | null>(null)
const submitting    = ref(false)
const listVisible   = ref(false)

const editSource    = ref<DataSource | null>(null)

const form = ref({
  name: '', source_type: 'postgresql' as string,
  host: '', port: '5432', database_name: '',
  username: '', password: '', description: '', url: '',
  // Advanced fields
  schema_name: '',
  auth_type: 'basic' as string,
  api_key: '', api_key_header: 'X-API-Key',
  use_ssl: false, ssl_mode: 'require',
  timeout_seconds: '30', max_retries: '3', retry_delay_seconds: '5',
  batch_size: '1000',
  sync_frequency: 'manual',
  auto_refresh_enabled: false,
  is_public: false,
  tags: '',
  category: '',
  business_domain: '',
  notes: '',
  // OAuth2
  oauth2_client_id: '',
  oauth2_client_secret: '',
  oauth2_token_url: '',
  // Cloud Storage
  cloud_provider: '',
  bucket_name: '',
  object_key: '',
  region: '',
  // Streaming
  streaming_topic: '',
  streaming_broker: '',
  // Sécurité avancée
  ssl_certificate: '',
  use_credential_vault: false,
  // Organisation
  documentation_url: '',
  support_contact: '',
  owner_team: '',
})

// ── API stats ──────────────────────────────────────────────
const sourceStats = ref<any>(null)

// ── Row-level sync ─────────────────────────────────────────
const syncingId = ref<string | null>(null)

// ── Inline SQL editor ──────────────────────────────────────
const querySourceId = ref<string | null>(null)
const queryText     = ref('')
const queryResult   = ref<any>(null)
const queryLoading  = ref(false)
const queryError    = ref('')

// Preview state for tables
const previewTableId     = ref<string | null>(null)
const previewTableData   = ref<any[]>([])
const previewTableCols   = ref<string[]>([])
const previewLoading     = ref(false)

const selectedFile  = ref<File | null>(null)
const dragOver      = ref(false)
const fileInputRef  = ref<HTMLInputElement | null>(null)

// ── Detail panel state ──────────────────────────────────────
const selectedSource = ref<DataSource | null>(null)
const detailTab      = ref<'tables' | 'logs' | 'metrics' | 'queries'>('tables')
const detailLoading  = ref(false)
const detailTables   = ref<any[]>([])
const detailLogs     = ref<any[]>([])
const detailMetrics  = ref<Record<string, any>>({})
const detailQueries  = ref<any[]>([])
const syncing        = ref(false)
const syncMsg        = ref('')
const execResults    = ref<Record<string, string>>({})

// ── Main tab ───────────────────────────────────────────────
const mainTab = ref<'sources' | 'tables'>('sources')

// ── DataTable state ────────────────────────────────────────
interface DataTable {
  id: string
  data_source?: string
  name: string
  schema?: string
  catalog?: string
  description?: string
  row_count?: number | null
  size_bytes?: number | null
  last_analyzed?: string | null
  is_partitioned?: boolean
  partition_column?: string
  partition_count?: number | null
  last_updated?: string | null
}

const dataTables      = ref<DataTable[]>([])
const dataTablesLoading = ref(false)
const dtSearchQuery   = ref('')
const dtDeleteConfirm = ref<string | null>(null)

async function fetchDataTables() {
  if (dataTablesLoading.value) return
  dataTablesLoading.value = true
  try {
    const { data } = await api.get('/api/data-sources/tables/')
    dataTables.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    dataTables.value = []
  } finally {
    dataTablesLoading.value = false
  }
}

async function deleteDataTable(id: string) {
  try {
    await api.delete(`/api/data-sources/tables/${id}/`)
    dataTables.value = dataTables.value.filter(t => t.id !== id)
  } catch { /* ignore */ }
  dtDeleteConfirm.value = null
}

function formatBytes(bytes?: number | null): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

const filteredDataTables = computed(() => {
  const q = dtSearchQuery.value.toLowerCase()
  return q ? dataTables.value.filter(t => t.name.toLowerCase().includes(q) || (t.schema || '').toLowerCase().includes(q)) : dataTables.value
})

// ── Computed ───────────────────────────────────────────────
const filteredSources = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return sources.value.filter(s => {
    const matchSearch = !q || s.name.toLowerCase().includes(q) || (s.host || '').toLowerCase().includes(q)
    const matchType   = filterType.value === 'all' || s.source_type === filterType.value
    const matchStatus = filterStatus.value === 'all' || s.status === filterStatus.value
    return matchSearch && matchType && matchStatus
  })
})

const stats = computed(() => ({
  total:    sources.value.length,
  active:   sources.value.filter(s => s.status === 'active').length,
  error:    sources.value.filter(s => s.status === 'error').length,
  inactive: sources.value.filter(s => s.status === 'inactive').length,
}))

const isDbType   = computed(() => ['postgresql', 'mysql', 'oracle', 'mongodb'].includes(form.value.source_type))
const isFileType = computed(() => ['csv', 'excel'].includes(form.value.source_type))
const isApiType  = computed(() => form.value.source_type === 'rest_api')

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs} h`
  return `${Math.floor(hrs / 24)} j`
}

// ── API ────────────────────────────────────────────────────
async function fetchSources() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/data-sources/sources/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    sources.value = rows
  } catch {
    sources.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function fetchStats() {
  try {
    const { data } = await api.get('/api/data-sources/sources/stats/')
    sourceStats.value = data
  } catch {
    sourceStats.value = null
  }
}

async function syncTablesRow(source: DataSource) {
  if (syncingId.value) return
  syncingId.value = source.id
  try {
    await api.post(`/api/data-sources/sources/${source.id}/sync_tables/`, {})
    await fetchSources()
    await fetchStats()
  } catch {
    // silently ignore — spinner stops regardless
  } finally {
    syncingId.value = null
  }
}

async function openQueryPanel(source: DataSource) {
  querySourceId.value = source.id
  queryText.value = ''
  queryResult.value = null
  queryError.value = ''
}

function closeQueryPanel() {
  querySourceId.value = null
  queryResult.value = null
  queryError.value = ''
}

async function executeQuerySql() {
  if (!querySourceId.value || !queryText.value.trim()) return
  queryLoading.value = true
  queryResult.value = null
  queryError.value = ''
  try {
    const { data } = await api.post(
      `/api/data-sources/sources/${querySourceId.value}/execute_query/`,
      { query: queryText.value }
    )
    queryResult.value = data
  } catch (err: any) {
    queryError.value = err?.response?.data?.detail
      ?? err?.response?.data?.error
      ?? 'Erreur lors de l\'exécution de la requête.'
  } finally {
    queryLoading.value = false
  }
}

async function testConnection(id: string) {
  if (testingId.value) return
  testedOk.value = null
  testingId.value = id
  try {
    await api.post(`/api/data-sources/sources/${id}/test_connection/`, {})
    testedOk.value = id
    setTimeout(() => { if (testedOk.value === id) testedOk.value = null }, 3000)
  } catch {
    // connection failed - testedOk stays null
  } finally {
    testingId.value = null
  }
}

async function deleteSource(id: string) {
  try {
    await api.delete(`/api/data-sources/sources/${id}/`)
  } catch { /* ignore */ }
  sources.value = sources.value.filter(s => s.id !== id)
  deleteConfirm.value = null
}

function openDrawer() {
  editSource.value = null
  form.value = {
    name: '', source_type: 'postgresql', host: '', port: '5432', database_name: '',
    username: '', password: '', description: '', url: '', schema_name: '',
    auth_type: 'basic', api_key: '', api_key_header: 'X-API-Key',
    use_ssl: false, ssl_mode: 'require',
    timeout_seconds: '30', max_retries: '3', retry_delay_seconds: '5',
    batch_size: '1000', sync_frequency: 'manual',
    auto_refresh_enabled: false, is_public: false,
    tags: '', category: '', business_domain: '', notes: '',
    oauth2_client_id: '', oauth2_client_secret: '', oauth2_token_url: '',
    cloud_provider: '', bucket_name: '', object_key: '', region: '',
    streaming_topic: '', streaming_broker: '',
    ssl_certificate: '', use_credential_vault: false,
    documentation_url: '', support_contact: '', owner_team: '',
  }
  selectedFile.value = null
  dragOver.value = false
  drawerOpen.value = true
}

function openEditDrawer(source: DataSource) {
  editSource.value = source
  form.value = {
    name:                 source.name,
    source_type:          source.source_type,
    host:                 source.host || '',
    port:                 source.port ? String(source.port) : '',
    database_name:        source.database_name || '',
    username:             '',
    password:             '',
    description:          source.description || '',
    url:                  source.host || '',
    schema_name:          '',
    auth_type:            'basic',
    api_key:              '',
    api_key_header:       'X-API-Key',
    use_ssl:              false,
    ssl_mode:             'require',
    timeout_seconds:      '30',
    max_retries:          '3',
    retry_delay_seconds:  '5',
    batch_size:           '1000',
    sync_frequency:       'manual',
    auto_refresh_enabled: false,
    is_public:            false,
    tags:                 '',
    category:             '',
    business_domain:      '',
    notes:                '',
    oauth2_client_id:     '',
    oauth2_client_secret: '',
    oauth2_token_url:     '',
    cloud_provider:       '',
    bucket_name:          '',
    object_key:           '',
    region:               '',
    streaming_topic:      '',
    streaming_broker:     '',
    ssl_certificate:      '',
    use_credential_vault: false,
    documentation_url:    '',
    support_contact:      '',
    owner_team:           '',
  }
  selectedFile.value = null
  drawerOpen.value = true
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}

function handleDragLeave() {
  dragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) setFile(file)
}

function handleFileInput(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) setFile(file)
}

function setFile(file: File) {
  selectedFile.value = file
  if (!form.value.name) form.value.name = file.name.replace(/\.[^.]+$/, '')
  form.value.host = file.name
}

function clickZone() {
  fileInputRef.value?.click()
}

function closeDrawer() {
  drawerOpen.value = false
}

function setType(t: string) {
  form.value.source_type = t
  form.value.port = t === 'postgresql' ? '5432' : t === 'mysql' ? '3306' : t === 'oracle' ? '1521' : t === 'mongodb' ? '27017' : ''
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  try {
    if (isFileType.value && selectedFile.value && !editSource.value) {
      const fd = new FormData()
      fd.append('file', selectedFile.value)
      fd.append('name', form.value.name)
      fd.append('source_type', form.value.source_type)
      if (form.value.description) fd.append('description', form.value.description)
      await api.post('/api/data-sources/files/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    } else {
      const payload: Record<string, any> = {
        name:                  form.value.name,
        source_type:           form.value.source_type,
        host:                  isApiType.value ? form.value.url : form.value.host,
        port:                  form.value.port ? parseInt(form.value.port) : null,
        database_name:         form.value.database_name,
        schema_name:           form.value.schema_name || undefined,
        description:           form.value.description,
        notes:                 form.value.notes || undefined,
        category:              form.value.category || undefined,
        business_domain:       form.value.business_domain || undefined,
        is_public:             form.value.is_public,
        auto_refresh_enabled:  form.value.auto_refresh_enabled,
        sync_frequency:        form.value.sync_frequency,
        use_ssl:               form.value.use_ssl,
        ssl_mode:              form.value.use_ssl ? form.value.ssl_mode : undefined,
        timeout_seconds:       form.value.timeout_seconds ? parseInt(form.value.timeout_seconds) : undefined,
        max_retries:           form.value.max_retries ? parseInt(form.value.max_retries) : undefined,
        retry_delay_seconds:   form.value.retry_delay_seconds ? parseInt(form.value.retry_delay_seconds) : undefined,
        batch_size:            form.value.batch_size ? parseInt(form.value.batch_size) : undefined,
        auth_type:             form.value.auth_type || undefined,
      }
      if (form.value.username) payload.username = form.value.username
      if (form.value.password) payload.password = form.value.password
      if (form.value.api_key)  { payload.api_key = form.value.api_key; payload.api_key_header = form.value.api_key_header }
      if (form.value.tags)     payload.tags = form.value.tags.split(',').map((t: string) => t.trim()).filter(Boolean)
      // OAuth2
      if (form.value.auth_type === 'oauth2') {
        if (form.value.oauth2_client_id)     payload.oauth2_client_id     = form.value.oauth2_client_id
        if (form.value.oauth2_client_secret) payload.oauth2_client_secret = form.value.oauth2_client_secret
        if (form.value.oauth2_token_url)     payload.oauth2_token_url     = form.value.oauth2_token_url
      }
      // Cloud Storage
      if (form.value.cloud_provider) payload.cloud_provider = form.value.cloud_provider
      if (form.value.bucket_name)    payload.bucket_name    = form.value.bucket_name
      if (form.value.object_key)     payload.object_key     = form.value.object_key
      if (form.value.region)         payload.region         = form.value.region
      // Streaming
      if (form.value.streaming_topic)  payload.streaming_topic  = form.value.streaming_topic
      if (form.value.streaming_broker) payload.streaming_broker = form.value.streaming_broker
      // Security & Organisation
      if (form.value.ssl_certificate)     payload.ssl_certificate     = form.value.ssl_certificate
      payload.use_credential_vault = form.value.use_credential_vault
      if (form.value.documentation_url) payload.documentation_url = form.value.documentation_url
      if (form.value.support_contact)   payload.support_contact   = form.value.support_contact
      if (form.value.owner_team)        payload.owner_team        = form.value.owner_team

      if (editSource.value) {
        await api.patch(`/api/data-sources/sources/${editSource.value.id}/`, payload)
      } else {
        await api.post('/api/data-sources/sources/', payload)
      }
    }
    await fetchSources()
    closeDrawer()
    editSource.value = null
  } catch {
    closeDrawer()
    editSource.value = null
  } finally {
    submitting.value = false
  }
}

// ── Preview table data ─────────────────────────────────────
async function previewTable(tableId: string) {
  if (previewTableId.value === tableId) {
    previewTableId.value = null
    return
  }
  previewTableId.value = tableId
  previewLoading.value = true
  previewTableData.value = []
  previewTableCols.value = []
  try {
    const { data } = await api.get(`/api/data-sources/tables/${tableId}/preview/`)
    const rows: any[] = Array.isArray(data?.results) ? data.results
                      : Array.isArray(data?.rows)    ? data.rows
                      : Array.isArray(data)          ? data
                      : []
    if (rows.length > 0) {
      previewTableCols.value = Object.keys(rows[0])
      previewTableData.value = rows.slice(0, 20)
    }
  } catch {
    previewTableData.value = []
  } finally {
    previewLoading.value = false
  }
}

// ── Detail panel API ────────────────────────────────────────
async function fetchDetailTab() {
  if (!selectedSource.value) return
  const id = selectedSource.value.id
  detailLoading.value = true
  try {
    if (detailTab.value === 'tables') {
      const { data } = await api.get(`/api/data-sources/sources/${id}/tables/`)
      detailTables.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    } else if (detailTab.value === 'logs') {
      const { data } = await api.get(`/api/data-sources/sources/${id}/logs/`)
      const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
      detailLogs.value = rows.slice(0, 20)
    } else if (detailTab.value === 'metrics') {
      const { data } = await api.get(`/api/data-sources/sources/${id}/metrics/`)
      detailMetrics.value = Array.isArray(data) ? (data[0] ?? {}) : (data ?? {})
    } else if (detailTab.value === 'queries') {
      const { data } = await api.get(`/api/data-sources/sources/${id}/queries/`)
      detailQueries.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    }
  } catch {
    // silently ignore fetch errors
  } finally {
    detailLoading.value = false
  }
}

function openDetail(source: DataSource) {
  selectedSource.value = source
  detailTab.value = 'tables'
  detailTables.value = []
  detailLogs.value = []
  detailMetrics.value = {}
  detailQueries.value = []
  syncMsg.value = ''
  execResults.value = {}
  fetchDetailTab()
}

function closeDetail() {
  selectedSource.value = null
}

async function syncTables() {
  if (!selectedSource.value || syncing.value) return
  syncing.value = true
  syncMsg.value = ''
  try {
    await api.post(`/api/data-sources/sources/${selectedSource.value.id}/sync_tables/`, {})
    syncMsg.value = 'Synchronisation réussie !'
    await fetchDetailTab()
    setTimeout(() => { syncMsg.value = '' }, 3000)
  } catch {
    syncMsg.value = 'Erreur lors de la synchronisation.'
    setTimeout(() => { syncMsg.value = '' }, 3000)
  } finally {
    syncing.value = false
  }
}

async function executeQuery(queryId: string) {
  try {
    const { data } = await api.post(`/api/data-sources/queries/${queryId}/execute/`, {})
    const count = data?.row_count ?? data?.count ?? data?.rows?.length ?? '?'
    execResults.value = { ...execResults.value, [queryId]: `${count} ligne(s)` }
  } catch {
    execResults.value = { ...execResults.value, [queryId]: 'Erreur' }
  }
}

async function toggleFavorite(queryId: string) {
  try {
    await api.post(`/api/data-sources/queries/${queryId}/toggle_favorite/`, {})
    await fetchDetailTab()
  } catch { /* ignore */ }
}

function logLevelClass(level: string): string {
  const l = (level || '').toLowerCase()
  if (l === 'error' || l === 'critical') return 'log-badge--error'
  if (l === 'warning' || l === 'warn')   return 'log-badge--warning'
  return 'log-badge--info'
}

function fmtDate(d: string | null): string {
  if (!d) return '—'
  try {
    return new Date(d).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return d }
}

watch(detailTab, fetchDetailTab)

onMounted(async () => {
  await fetchSources()
  fetchStats()
})
</script>

<template>
  <div class="sources-page">

    <!-- ── Page header ─────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Sources de données</h2>
        <p class="page-subtitle">
          {{ stats.total }} source{{ stats.total !== 1 ? 's' : '' }} configurée{{ stats.total !== 1 ? 's' : '' }}
        </p>
      </div>
      <button
        v-if="auth.canManageDataSources"
        class="btn-primary"
        @click="openDrawer"
      >
        <Plus :size="15" />
        <span>Nouvelle source</span>
      </button>
    </header>

    <!-- ── Stats strip ─────────────────────────────────── -->
    <div class="stats-strip">
      <div class="stat-cell">
        <span class="stat-n">{{ sourceStats ? sourceStats.total : stats.total }}</span>
        <span class="stat-l">Total</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--ok">{{ sourceStats ? sourceStats.active : stats.active }}</span>
        <span class="stat-l">Actives</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--err">{{ sourceStats ? sourceStats.error : stats.error }}</span>
        <span class="stat-l">En erreur</span>
      </div>
      <div class="stat-div"></div>
      <div class="stat-cell">
        <span class="stat-n stat-n--off">{{ stats.inactive }}</span>
        <span class="stat-l">Inactives</span>
      </div>
      <template v-if="sourceStats">
        <div class="stat-div"></div>
        <div class="stat-cell">
          <span class="stat-n stat-n--accent">{{ sourceStats.total_queries != null ? sourceStats.total_queries.toLocaleString('fr-FR') : '—' }}</span>
          <span class="stat-l">Requêtes totales</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat-cell">
          <span class="stat-n stat-n--quality">
            {{ sourceStats.avg_quality_score != null ? Number(sourceStats.avg_quality_score).toFixed(1) + '%' : '—' }}
          </span>
          <span class="stat-l">Score qualité moy.</span>
        </div>
      </template>
    </div>

    <!-- ── Main tab nav ──────────────────────────────────── -->
    <nav class="main-tab-nav">
      <button
        class="main-tab-btn"
        :class="{ 'main-tab-btn--active': mainTab === 'sources' }"
        @click="mainTab = 'sources'"
      >
        <Database :size="14" />
        Sources
      </button>
      <button
        class="main-tab-btn"
        :class="{ 'main-tab-btn--active': mainTab === 'tables' }"
        @click="mainTab = 'tables'; fetchDataTables()"
      >
        <Table2 :size="14" />
        Tables de données
        <span v-if="dataTables.length" class="tab-chip">{{ dataTables.length }}</span>
      </button>
    </nav>

    <template v-if="mainTab === 'sources'">

    <!-- ── Toolbar ─────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input
          v-model="searchQuery"
          class="search-input"
          type="search"
          placeholder="Rechercher par nom ou hôte…"
        />
      </div>
      <div class="filters">
        <div class="select-wrap">
          <select v-model="filterType" class="filter-select">
            <option value="all">Tous les types</option>
            <option v-for="(meta, key) in TYPE_META" :key="key" :value="key">{{ meta.label }}</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
        <div class="select-wrap">
          <select v-model="filterStatus" class="filter-select">
            <option value="all">Tous les statuts</option>
            <option value="active">Actif</option>
            <option value="error">Erreur</option>
            <option value="inactive">Inactif</option>
            <option value="pending">En attente</option>
            <option value="testing">En test</option>
            <option value="configuring">Configuration</option>
            <option value="draft">Brouillon</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
      </div>
    </div>

    <!-- ── Main content area (list + detail panel) ───────── -->
    <div class="content-area">

      <!-- ── Sources list ──────────────────────────────── -->
      <section
        v-if="!loading"
        class="sources-list"
        :class="{ 'sources-list--visible': listVisible }"
        aria-label="Sources de données"
      >

        <!-- Empty state -->
        <div v-if="filteredSources.length === 0" class="empty-state">
          <Database :size="36" class="empty-icon" />
          <p class="empty-title">Aucune source trouvée</p>
          <p class="empty-sub">Modifiez vos filtres ou ajoutez une nouvelle source de données.</p>
          <button class="btn-primary" @click="openDrawer">
            <Plus :size="14" />
            <span>Ajouter une source</span>
          </button>
        </div>

        <!-- Source rows -->
        <div
          v-for="(src, i) in filteredSources"
          :key="src.id"
          class="source-row"
          :class="{
            'source-row--error':    src.status === 'error',
            'source-row--selected': selectedSource?.id === src.id,
          }"
          :style="{ '--row-i': i }"
          @click="openDetail(src)"
        >

          <!-- Type badge -->
          <div
            class="type-badge"
            :style="{ '--tc': getTypeMeta(src.source_type).color }"
            :title="getTypeMeta(src.source_type).label"
          >
            {{ getTypeMeta(src.source_type).abbr }}
          </div>

          <!-- Main info -->
          <div class="src-info">
            <div class="src-name-row">
              <span class="src-name">{{ src.name }}</span>
              <span class="type-pill" :style="{ '--tc': getTypeMeta(src.source_type).color }">
                {{ getTypeMeta(src.source_type).label }}
              </span>
            </div>
            <p v-if="src.description" class="src-desc">{{ src.description }}</p>
            <p class="src-host">
              {{ src.host }}{{ src.database_name ? ` · ${src.database_name}` : '' }}
            </p>
          </div>

          <!-- Records -->
          <div v-if="src.total_queries" class="src-records">
            <span class="src-records-n">{{ src.total_queries.toLocaleString('fr-FR') }}</span>
            <span class="src-records-l">enregistrements</span>
          </div>
          <div v-else class="src-records">
            <span class="src-records-l">—</span>
          </div>

          <!-- Last sync -->
          <div class="src-sync">
            <Clock :size="11" class="sync-icon" />
            <span class="sync-time">{{ src.last_sync ? timeAgo(src.last_sync) : 'Jamais' }}</span>
          </div>

          <!-- Status -->
          <div class="status-badge" :class="getStatusMeta(src.status).cls">
            <span class="status-dot"></span>
            <span>{{ getStatusMeta(src.status).label }}</span>
          </div>

          <!-- Actions -->
          <div class="src-actions" @click.stop>
            <template v-if="deleteConfirm === src.id">
              <span class="del-label">Supprimer ?</span>
              <button class="action-btn action-btn--confirm-yes" @click="deleteSource(src.id)">Oui</button>
              <button class="action-btn action-btn--confirm-no" @click="deleteConfirm = null">Non</button>
            </template>
            <template v-else>
              <!-- Test connection -->
              <button
                class="action-btn"
                :class="{
                  'action-btn--spinning': testingId === src.id,
                  'action-btn--tested-ok': testedOk === src.id,
                }"
                :disabled="testingId !== null"
                title="Tester la connexion"
                @click="testConnection(src.id)"
              >
                <CheckCircle2 v-if="testedOk === src.id" :size="14" />
                <RefreshCcw v-else :size="14" />
              </button>
              <!-- Sync tables (DB only) -->
              <button
                v-if="isDbSource(src.source_type)"
                class="action-btn action-btn--sync"
                :class="{ 'action-btn--spinning': syncingId === src.id }"
                :disabled="syncingId !== null"
                title="Synchroniser les tables"
                @click="syncTablesRow(src)"
              >
                <Loader2 v-if="syncingId === src.id" :size="14" class="spin-icon" />
                <RotateCcw v-else :size="14" />
              </button>
              <!-- SQL editor (DB only) -->
              <button
                v-if="isDbSource(src.source_type)"
                class="action-btn action-btn--sql"
                :class="{ 'action-btn--sql-active': querySourceId === src.id }"
                title="Éditeur SQL"
                @click="openQueryPanel(src)"
              >
                <Code2 :size="14" />
              </button>
              <!-- Edit -->
              <button
                class="action-btn action-btn--edit"
                title="Modifier la source"
                @click="openEditDrawer(src)"
              >
                <Pencil :size="14" />
              </button>
              <!-- Delete -->
              <button
                class="action-btn action-btn--delete"
                title="Supprimer la source"
                @click="deleteConfirm = src.id"
              >
                <Trash2 :size="14" />
              </button>
            </template>
          </div>

        </div>
      </section>

      <!-- ── Loading skeletons ──────────────────────────── -->
      <section v-else class="sources-list sources-list--visible">
        <div v-for="i in 6" :key="i" class="source-skel"></div>
      </section>

      <!-- ── Detail panel ───────────────────────────────── -->
      <Transition name="detail-anim">
        <aside v-if="selectedSource !== null" class="detail-panel" aria-label="Détails de la source">

          <!-- Panel header -->
          <div class="detail-hd">
            <div class="detail-hd-info">
              <div
                class="detail-type-badge"
                :style="{ '--tc': getTypeMeta(selectedSource.source_type).color }"
              >
                {{ getTypeMeta(selectedSource.source_type).abbr }}
              </div>
              <div>
                <p class="detail-title">{{ selectedSource.name }}</p>
                <p class="detail-subtitle">{{ getTypeMeta(selectedSource.source_type).label }}</p>
              </div>
            </div>
            <button class="detail-close" @click="closeDetail" aria-label="Fermer">
              <X :size="16" />
            </button>
          </div>

          <!-- Tab bar -->
          <nav class="detail-tabs">
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTab === 'tables' }"
              @click="detailTab = 'tables'"
            >
              <Table2 :size="13" />
              <span>Tables</span>
            </button>
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTab === 'logs' }"
              @click="detailTab = 'logs'"
            >
              <Activity :size="13" />
              <span>Logs</span>
            </button>
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTab === 'metrics' }"
              @click="detailTab = 'metrics'"
            >
              <BarChart2 :size="13" />
              <span>Métriques</span>
            </button>
            <button
              class="detail-tab"
              :class="{ 'detail-tab--active': detailTab === 'queries' }"
              @click="detailTab = 'queries'"
            >
              <Play :size="13" />
              <span>Requêtes</span>
            </button>
          </nav>

          <!-- Tab content -->
          <div class="detail-body">

            <!-- Loading skeleton -->
            <template v-if="detailLoading">
              <div v-for="k in 5" :key="k" class="detail-skel"></div>
            </template>

            <!-- Tab: Tables -->
            <template v-else-if="detailTab === 'tables'">
              <div class="detail-tab-toolbar">
                <button
                  class="btn-primary btn-primary--sm"
                  :disabled="syncing"
                  @click="syncTables"
                >
                  <span v-if="syncing" class="spinner spinner--sm" aria-label="Synchronisation…"></span>
                  <RefreshCcw v-else :size="13" />
                  <span>{{ syncing ? 'Sync…' : 'Synchroniser' }}</span>
                </button>
                <span v-if="syncMsg" class="sync-feedback" :class="{ 'sync-feedback--ok': syncMsg.includes('réussie') }">
                  {{ syncMsg }}
                </span>
              </div>

              <div v-if="detailTables.length === 0" class="detail-empty">
                <Table2 :size="24" />
                <p>Aucune table trouvée</p>
              </div>

              <div v-else class="detail-table-wrap">
                <table class="detail-table">
                  <thead>
                    <tr>
                      <th>Nom</th>
                      <th>Lignes</th>
                      <th>Dernière MAJ</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="tbl in detailTables" :key="tbl.name ?? tbl.id">
                      <td class="cell-name">{{ tbl.name ?? tbl.table_name ?? '—' }}</td>
                      <td class="cell-num">{{ tbl.row_count != null ? tbl.row_count.toLocaleString('fr-FR') : '—' }}</td>
                      <td class="cell-date">{{ fmtDate(tbl.last_refresh) }}</td>
                      <td class="cell-action">
                        <button
                          v-if="tbl.id"
                          class="preview-btn"
                          :class="{ 'preview-btn--active': previewTableId === tbl.id }"
                          :disabled="previewLoading && previewTableId === tbl.id"
                          title="Aperçu des données"
                          @click="previewTable(tbl.id)"
                        >
                          <Loader2 v-if="previewLoading && previewTableId === tbl.id" :size="12" class="spin-icon" />
                          <Eye v-else-if="previewTableId !== tbl.id" :size="12" />
                          <EyeOff v-else :size="12" />
                        </button>
                      </td>
                    </tr>
                    <!-- Preview inline row -->
                    <tr v-if="previewTableId && previewTableData.length > 0" class="preview-row">
                      <td :colspan="4">
                        <div class="preview-panel">
                          <p class="preview-label">Aperçu — {{ previewTableCols.length }} colonne(s), {{ previewTableData.length }} ligne(s)</p>
                          <div class="preview-scroll">
                            <table class="preview-table">
                              <thead>
                                <tr>
                                  <th v-for="col in previewTableCols" :key="col">{{ col }}</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr v-for="(row, ri) in previewTableData" :key="ri">
                                  <td v-for="col in previewTableCols" :key="col">{{ row[col] ?? '—' }}</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <!-- Tab: Logs -->
            <template v-else-if="detailTab === 'logs'">
              <div v-if="detailLogs.length === 0" class="detail-empty">
                <Activity :size="24" />
                <p>Aucun log disponible</p>
              </div>

              <div v-else class="detail-table-wrap">
                <table class="detail-table">
                  <thead>
                    <tr>
                      <th>Niveau</th>
                      <th>Message</th>
                      <th>Durée</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(log, li) in detailLogs" :key="li">
                      <td>
                        <span class="log-badge" :class="logLevelClass(log.level ?? log.severity)">
                          {{ (log.level ?? log.severity ?? 'info').toUpperCase() }}
                        </span>
                      </td>
                      <td class="cell-msg">{{ log.message ?? '—' }}</td>
                      <td class="cell-num">{{ log.duration_ms != null ? `${log.duration_ms} ms` : '—' }}</td>
                      <td class="cell-date">{{ fmtDate(log.timestamp) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <!-- Tab: Métriques -->
            <template v-else-if="detailTab === 'metrics'">
              <div v-if="Object.keys(detailMetrics).length === 0" class="detail-empty">
                <BarChart2 :size="24" />
                <p>Aucune métrique disponible</p>
              </div>

              <div v-else class="metrics-grid">
                <div class="metric-card">
                  <span class="metric-label">Requêtes totales</span>
                  <span class="metric-value">{{ detailMetrics.total_queries ?? '—' }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">Succès</span>
                  <span class="metric-value metric-value--ok">{{ detailMetrics.success_count ?? '—' }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">Erreurs</span>
                  <span class="metric-value metric-value--err">{{ detailMetrics.error_count ?? '—' }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">Durée moy. (ms)</span>
                  <span class="metric-value">{{ detailMetrics.avg_duration_ms != null ? Math.round(detailMetrics.avg_duration_ms) : '—' }}</span>
                </div>
                <div class="metric-card metric-card--wide">
                  <span class="metric-label">Dernière synchro</span>
                  <span class="metric-value metric-value--sm">{{ fmtDate(detailMetrics.last_sync) }}</span>
                </div>
              </div>
            </template>

            <!-- Tab: Requêtes -->
            <template v-else-if="detailTab === 'queries'">
              <div v-if="detailQueries.length === 0" class="detail-empty">
                <Play :size="24" />
                <p>Aucune requête sauvegardée</p>
              </div>

              <div v-else class="query-list">
                <div
                  v-for="q in detailQueries"
                  :key="q.id"
                  class="query-row"
                >
                  <div class="query-info">
                    <div class="query-name-row">
                      <Star
                        v-if="q.is_favorite"
                        :size="12"
                        class="query-star query-star--on"
                      />
                      <span class="query-name">{{ q.name ?? 'Sans nom' }}</span>
                    </div>
                    <p v-if="q.description" class="query-desc">{{ q.description }}</p>
                    <p v-if="q.sql || q.query" class="query-sql">{{ (q.sql ?? q.query ?? '').slice(0, 80) }}…</p>
                    <span v-if="execResults[q.id]" class="query-result">{{ execResults[q.id] }}</span>
                  </div>
                  <div class="query-actions">
                    <button
                      class="action-btn action-btn--exec"
                      title="Exécuter"
                      @click="executeQuery(q.id)"
                    >
                      <Play :size="12" />
                    </button>
                    <button
                      class="action-btn"
                      :class="{ 'action-btn--fav-on': q.is_favorite }"
                      title="Favori"
                      @click="toggleFavorite(q.id)"
                    >
                      <Star :size="12" />
                    </button>
                  </div>
                </div>
              </div>
            </template>

          </div>
        </aside>
      </Transition>

    </div><!-- end .content-area -->

    <!-- ── SQL Editor panel ───────────────────────────────── -->
    <Transition name="sql-panel-anim">
      <div v-if="querySourceId !== null" class="sql-panel">

        <!-- SQL panel header -->
        <div class="sql-panel-hd">
          <div class="sql-panel-hd-left">
            <Code2 :size="15" class="sql-panel-icon" />
            <span class="sql-panel-title">
              Requête SQL —
              <strong>{{ filteredSources.find(s => s.id === querySourceId)?.name ?? sources.find(s => s.id === querySourceId)?.name ?? querySourceId }}</strong>
            </span>
          </div>
          <button class="sql-panel-close" @click="closeQueryPanel" aria-label="Fermer l'éditeur SQL">
            <X :size="15" />
          </button>
        </div>

        <!-- SQL editor body -->
        <div class="sql-panel-body">
          <!-- Textarea -->
          <textarea
            v-model="queryText"
            class="sql-textarea"
            rows="5"
            placeholder="SELECT * FROM ma_table LIMIT 10;"
            spellcheck="false"
            @keydown.ctrl.enter.prevent="executeQuerySql"
          ></textarea>

          <!-- Toolbar -->
          <div class="sql-toolbar">
            <button
              class="btn-primary btn-primary--sm sql-run-btn"
              :disabled="queryLoading || !queryText.trim()"
              @click="executeQuerySql"
            >
              <span v-if="queryLoading" class="spinner spinner--sm" aria-label="Exécution…"></span>
              <Play v-else :size="13" />
              <span>{{ queryLoading ? 'Exécution…' : 'Exécuter' }}</span>
            </button>
            <span class="sql-hint">Ctrl + Entrée pour exécuter</span>
            <button class="btn-ghost btn-ghost--sm" @click="queryText = ''; queryResult = null; queryError = ''">
              Effacer
            </button>
          </div>

          <!-- Error -->
          <div v-if="queryError" class="sql-error">
            <X :size="13" />
            <span>{{ queryError }}</span>
          </div>

          <!-- Results -->
          <div v-if="queryResult" class="sql-results">
            <div class="sql-results-hd">
              <span class="sql-results-badge">
                {{ queryResult.row_count ?? queryResult.rows?.length ?? 0 }} ligne(s)
                <template v-if="queryResult.execution_time_ms != null">
                  en {{ queryResult.execution_time_ms }} ms
                </template>
              </span>
            </div>
            <div class="sql-results-scroll">
              <table v-if="queryResult.columns?.length" class="sql-results-table">
                <thead>
                  <tr>
                    <th v-for="col in queryResult.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in (queryResult.rows ?? []).slice(0, 50)" :key="ri">
                    <td v-for="col in queryResult.columns" :key="col">
                      {{ row[col] ?? row[queryResult.columns.indexOf(col)] ?? '—' }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="sql-no-cols">Aucune colonne retournée.</div>
            </div>
          </div>
        </div>

      </div>
    </Transition>

    <!-- ── Add source drawer ────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="closeDrawer">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Nouvelle source de données">

          <!-- Drawer header -->
          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editSource ? 'Modifier la source' : 'Nouvelle source' }}</h3>
            <button class="drawer-close" @click="closeDrawer" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <!-- Drawer form -->
          <form class="drawer-form" @submit.prevent="submitForm">

            <!-- Type selector -->
            <div class="form-field">
              <label class="form-label">Type de source</label>
              <div class="type-grid">
                <button
                  v-for="(meta, key) in TYPE_META"
                  :key="key"
                  type="button"
                  class="type-option"
                  :class="{ 'type-option--active': form.source_type === key }"
                  :style="{ '--tc': meta.color }"
                  @click="setType(key)"
                >
                  <span class="type-opt-abbr">{{ meta.abbr }}</span>
                  <span class="type-opt-label">{{ meta.label }}</span>
                </button>
              </div>
            </div>

            <!-- Name -->
            <div class="form-field">
              <label class="form-label" for="f-name">Nom de la source <span class="req">*</span></label>
              <input
                id="f-name"
                v-model="form.name"
                class="form-input"
                type="text"
                placeholder="Ex : PostgreSQL Production"
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
                placeholder="Brève description…"
              />
            </div>

            <!-- DB fields -->
            <template v-if="isDbType">
              <div class="form-row-2">
                <div class="form-field">
                  <label class="form-label" for="f-host">Hôte <span class="req">*</span></label>
                  <input id="f-host" v-model="form.host" class="form-input" type="text" placeholder="localhost" required />
                </div>
                <div class="form-field form-field--port">
                  <label class="form-label" for="f-port">Port</label>
                  <input id="f-port" v-model="form.port" class="form-input" type="text" />
                </div>
              </div>
              <div class="form-field">
                <label class="form-label" for="f-db">Base de données</label>
                <input id="f-db" v-model="form.database_name" class="form-input" type="text" placeholder="nom_de_la_base" />
              </div>
              <div class="form-row-2">
                <div class="form-field">
                  <label class="form-label" for="f-user">Utilisateur</label>
                  <input id="f-user" v-model="form.username" class="form-input" type="text" placeholder="admin" />
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-pass">Mot de passe</label>
                  <input id="f-pass" v-model="form.password" class="form-input" type="password" placeholder="••••••••" autocomplete="new-password" />
                </div>
              </div>
            </template>

            <!-- File fields -->
            <template v-if="isFileType">
              <div class="form-field">
                <label class="form-label">Fichier</label>
                <input
                  ref="fileInputRef"
                  type="file"
                  :accept="form.source_type === 'csv' ? '.csv,.txt' : '.xlsx,.xls'"
                  style="display:none"
                  @change="handleFileInput"
                />
                <div
                  class="file-zone"
                  :class="{ 'file-zone--drag': dragOver, 'file-zone--ok': selectedFile }"
                  @click="clickZone"
                  @dragover="handleDragOver"
                  @dragleave="handleDragLeave"
                  @drop="handleDrop"
                >
                  <component :is="selectedFile ? FileText : UploadCloud" :size="28" class="file-zone-icon" />
                  <p class="file-zone-text">
                    <span v-if="selectedFile" class="file-selected-name">{{ selectedFile.name }}</span>
                    <span v-else>Glissez un fichier ici ou <span class="file-browse">parcourir</span></span>
                  </p>
                  <p class="file-hint">{{ form.source_type === 'csv' ? 'Formats : .csv, .txt' : 'Formats : .xlsx, .xls' }}</p>
                </div>
              </div>
            </template>

            <!-- API fields -->
            <template v-if="isApiType">
              <div class="form-field">
                <label class="form-label" for="f-url">URL de l'API <span class="req">*</span></label>
                <input id="f-url" v-model="form.url" class="form-input" type="url" placeholder="https://api.exemple.com/v1" required />
              </div>
              <div class="form-row-2">
                <div class="form-field">
                  <label class="form-label" for="f-apikey">Clé API</label>
                  <input id="f-apikey" v-model="form.api_key" class="form-input" type="password" placeholder="sk-…" autocomplete="new-password" />
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-apikeyheader">Header</label>
                  <input id="f-apikeyheader" v-model="form.api_key_header" class="form-input" type="text" placeholder="X-API-Key" />
                </div>
              </div>
            </template>

            <!-- ── Advanced: SSL ───────────────────────────── -->
            <details class="adv-section" v-if="isDbType">
              <summary class="adv-summary">
                <Shield :size="14" />
                SSL / Sécurité
              </summary>
              <div class="adv-body">
                <div class="form-field">
                  <label class="form-label toggle-label">
                    <input type="checkbox" v-model="form.use_ssl" class="form-checkbox" />
                    Activer SSL
                  </label>
                </div>
                <div v-if="form.use_ssl" class="form-field">
                  <label class="form-label">Mode SSL</label>
                  <div class="select-wrap-sm">
                    <select v-model="form.ssl_mode" class="form-select">
                      <option value="disable">Désactivé</option>
                      <option value="require">Requis</option>
                      <option value="verify-ca">Vérifier CA</option>
                      <option value="verify-full">Vérification complète</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow-sm" />
                  </div>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Auth ──────────────────────────── -->
            <details class="adv-section">
              <summary class="adv-summary">
                <Shield :size="14" />
                Authentification avancée
              </summary>
              <div class="adv-body">
                <div class="form-field">
                  <label class="form-label">Type d'authentification</label>
                  <div class="select-wrap-sm">
                    <select v-model="form.auth_type" class="form-select">
                      <option value="none">Aucune</option>
                      <option value="basic">Basic (user/password)</option>
                      <option value="api_key">Clé API</option>
                      <option value="oauth2">OAuth2</option>
                      <option value="jwt">JWT Token</option>
                      <option value="certificate">Certificat</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow-sm" />
                  </div>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Performance ───────────────────── -->
            <details class="adv-section">
              <summary class="adv-summary">
                <Settings :size="14" />
                Performance &amp; Synchronisation
              </summary>
              <div class="adv-body">
                <div class="form-row-3">
                  <div class="form-field">
                    <label class="form-label" for="f-timeout">Timeout (s)</label>
                    <input id="f-timeout" v-model="form.timeout_seconds" class="form-input" type="number" min="1" max="3600" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-retries">Nb. tentatives</label>
                    <input id="f-retries" v-model="form.max_retries" class="form-input" type="number" min="0" max="10" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-batch">Taille batch</label>
                    <input id="f-batch" v-model="form.batch_size" class="form-input" type="number" min="1" />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label">Fréquence de sync</label>
                  <div class="select-wrap-sm">
                    <select v-model="form.sync_frequency" class="form-select">
                      <option value="manual">Manuelle</option>
                      <option value="hourly">Toutes les heures</option>
                      <option value="daily">Quotidienne</option>
                      <option value="weekly">Hebdomadaire</option>
                      <option value="monthly">Mensuelle</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow-sm" />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label toggle-label">
                    <input type="checkbox" v-model="form.auto_refresh_enabled" class="form-checkbox" />
                    Rafraîchissement automatique
                  </label>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Metadata ──────────────────────── -->
            <details class="adv-section">
              <summary class="adv-summary">
                <Tag :size="14" />
                Métadonnées &amp; Classification
              </summary>
              <div class="adv-body">
                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label" for="f-category">Catégorie</label>
                    <input id="f-category" v-model="form.category" class="form-input" type="text" placeholder="Ex : ERP, CRM…" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-domain">Domaine métier</label>
                    <input id="f-domain" v-model="form.business_domain" class="form-input" type="text" placeholder="Ex : Finance, Ventes…" />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-tags">Tags <span class="opt">séparés par virgule</span></label>
                  <input id="f-tags" v-model="form.tags" class="form-input" type="text" placeholder="production, critique, finance" />
                </div>
                <div class="form-field">
                  <label class="form-label toggle-label">
                    <input type="checkbox" v-model="form.is_public" class="form-checkbox" />
                    Source publique (accessible à tous les utilisateurs)
                  </label>
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-notes">Notes</label>
                  <textarea id="f-notes" v-model="form.notes" class="form-textarea" rows="2" placeholder="Notes internes…"></textarea>
                </div>
              </div>
            </details>

            <!-- ── Advanced: OAuth2 ───────────────────────── -->
            <details class="adv-section" v-if="form.auth_type === 'oauth2'">
              <summary class="adv-summary">
                <Shield :size="14" />
                OAuth2
              </summary>
              <div class="adv-body">
                <div class="form-field">
                  <label class="form-label" for="f-oauth2-client-id">Client ID OAuth2</label>
                  <input id="f-oauth2-client-id" v-model="form.oauth2_client_id" class="form-input" type="text" placeholder="client_id" />
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-oauth2-secret">Client Secret</label>
                  <input id="f-oauth2-secret" v-model="form.oauth2_client_secret" class="form-input" type="password" placeholder="••••••••" autocomplete="new-password" />
                </div>
                <div class="form-field">
                  <label class="form-label" for="f-oauth2-token-url">URL Token OAuth2</label>
                  <input id="f-oauth2-token-url" v-model="form.oauth2_token_url" class="form-input" type="url" placeholder="https://auth.exemple.com/oauth/token" />
                </div>
              </div>
            </details>

            <!-- ── Advanced: Cloud Storage ────────────────── -->
            <details class="adv-section" v-if="['s3','azure_blob','gcs','google_drive','sharepoint','onedrive'].includes(form.source_type)">
              <summary class="adv-summary">
                <Settings :size="14" />
                Cloud Storage
              </summary>
              <div class="adv-body">
                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label" for="f-cloud-provider">Fournisseur Cloud</label>
                    <div class="select-wrap-sm">
                      <select id="f-cloud-provider" v-model="form.cloud_provider" class="form-select">
                        <option value="">— Choisir —</option>
                        <option value="aws">AWS</option>
                        <option value="azure">Azure</option>
                        <option value="gcp">GCP</option>
                        <option value="google">Google</option>
                      </select>
                      <ChevronDown :size="13" class="select-arrow-sm" />
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-region">Région</label>
                    <input id="f-region" v-model="form.region" class="form-input" type="text" placeholder="eu-west-1" />
                  </div>
                </div>
                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label" for="f-bucket">Nom du Bucket</label>
                    <input id="f-bucket" v-model="form.bucket_name" class="form-input" type="text" placeholder="mon-bucket" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-object-key">Clé de l'objet</label>
                    <input id="f-object-key" v-model="form.object_key" class="form-input" type="text" placeholder="dossier/fichier.csv" />
                  </div>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Streaming ────────────────────── -->
            <details class="adv-section" v-if="['kafka','kinesis'].includes(form.source_type)">
              <summary class="adv-summary">
                <Activity :size="14" />
                Streaming
              </summary>
              <div class="adv-body">
                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label" for="f-streaming-topic">Topic</label>
                    <input id="f-streaming-topic" v-model="form.streaming_topic" class="form-input" type="text" placeholder="mon-topic" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-streaming-broker">Broker</label>
                    <input id="f-streaming-broker" v-model="form.streaming_broker" class="form-input" type="text" placeholder="localhost:9092" />
                  </div>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Sécurité avancée ────────────── -->
            <details class="adv-section">
              <summary class="adv-summary">
                <Shield :size="14" />
                Sécurité avancée
              </summary>
              <div class="adv-body">
                <div class="form-field">
                  <label class="form-label" for="f-ssl-cert">Certificat SSL (PEM)</label>
                  <textarea id="f-ssl-cert" v-model="form.ssl_certificate" class="form-textarea" rows="4" placeholder="-----BEGIN CERTIFICATE-----&#10;…&#10;-----END CERTIFICATE-----"></textarea>
                </div>
                <div class="form-field">
                  <label class="form-label toggle-label">
                    <input type="checkbox" v-model="form.use_credential_vault" class="form-checkbox" />
                    Utiliser le coffre de mots de passe
                  </label>
                </div>
              </div>
            </details>

            <!-- ── Advanced: Organisation ─────────────────── -->
            <details class="adv-section">
              <summary class="adv-summary">
                <Tag :size="14" />
                Organisation
              </summary>
              <div class="adv-body">
                <div class="form-field">
                  <label class="form-label" for="f-doc-url">URL de documentation</label>
                  <input id="f-doc-url" v-model="form.documentation_url" class="form-input" type="url" placeholder="https://docs.exemple.com/source" />
                </div>
                <div class="form-row-2">
                  <div class="form-field">
                    <label class="form-label" for="f-support">Contact support</label>
                    <input id="f-support" v-model="form.support_contact" class="form-input" type="email" placeholder="support@exemple.com" />
                  </div>
                  <div class="form-field">
                    <label class="form-label" for="f-owner-team">Équipe propriétaire</label>
                    <input id="f-owner-team" v-model="form.owner_team" class="form-input" type="text" placeholder="Équipe Data" />
                  </div>
                </div>
              </div>
            </details>

            <!-- Actions -->
            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="closeDrawer; editSource = null">Annuler</button>
              <button type="submit" class="btn-primary" :class="{ 'btn-primary--loading': submitting }" :disabled="submitting">
                <span v-if="!submitting">{{ editSource ? 'Enregistrer' : 'Créer la source' }}</span>
                <span v-else class="spinner" aria-label="Enregistrement…"></span>
              </button>
            </div>

          </form>
        </aside>
      </div>
    </Transition>

    </template>

    <!-- ════════════════════════════════════════════════════ -->
    <!-- TAB: TABLES DE DONNÉES (DataTable)                   -->
    <!-- ════════════════════════════════════════════════════ -->
    <template v-else-if="mainTab === 'tables'">

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input
            v-model="dtSearchQuery"
            class="search-input"
            type="search"
            placeholder="Rechercher par nom ou schéma…"
          />
        </div>
        <button class="btn-secondary" @click="fetchDataTables">
          <RefreshCcw :size="13" />
          Actualiser
        </button>
        <span style="font-size: var(--text-xs); color: var(--text-muted); margin-left: auto;">
          {{ filteredDataTables.length }} table{{ filteredDataTables.length !== 1 ? 's' : '' }}
        </span>
      </div>

      <!-- Loading -->
      <div v-if="dataTablesLoading" class="content-area">
        <div v-for="i in 5" :key="i" class="source-row" style="height:56px;background:var(--surface-raised);border-radius:var(--radius-md);animation:shimmer 1.4s infinite;"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="filteredDataTables.length === 0" class="empty-state">
        <Table2 :size="36" class="empty-icon" />
        <p class="empty-title">Aucune table trouvée</p>
        <p class="empty-sub">Synchronisez d'abord les tables depuis vos sources de données.</p>
      </div>

      <!-- Table list -->
      <div v-else class="dt-page-wrap">
        <table class="dt-page-table">
          <thead>
            <tr>
              <th class="dt-page-th">Nom</th>
              <th class="dt-page-th">Schéma</th>
              <th class="dt-page-th">Lignes</th>
              <th class="dt-page-th">Taille</th>
              <th class="dt-page-th">Partitionné</th>
              <th class="dt-page-th">Dernière MàJ</th>
              <th class="dt-page-th dt-page-th--act"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tbl in filteredDataTables"
              :key="tbl.id"
              class="dt-page-row"
            >
              <td class="dt-page-td dt-page-td--name">
                <Table2 :size="13" style="color:var(--accent);flex-shrink:0" />
                {{ tbl.name }}
              </td>
              <td class="dt-page-td">
                <span v-if="tbl.schema" class="type-pill" style="--tc: oklch(60% 0.12 258)">{{ tbl.schema }}</span>
                <span v-else class="dash">—</span>
              </td>
              <td class="dt-page-td">{{ tbl.row_count != null ? tbl.row_count.toLocaleString('fr-FR') : '—' }}</td>
              <td class="dt-page-td">{{ formatBytes(tbl.size_bytes) }}</td>
              <td class="dt-page-td">
                <span v-if="tbl.is_partitioned" style="color:var(--accent);font-weight:600;font-size:var(--text-xs)">Oui</span>
                <span v-else class="dash">—</span>
              </td>
              <td class="dt-page-td">{{ tbl.last_updated ? timeAgo(tbl.last_updated) : '—' }}</td>
              <td class="dt-page-td dt-page-td--act">
                <template v-if="dtDeleteConfirm === tbl.id">
                  <span class="del-label">Supprimer&nbsp;?</span>
                  <button class="action-btn action-btn--confirm-yes" @click="deleteDataTable(tbl.id)">Oui</button>
                  <button class="action-btn action-btn--confirm-no" @click="dtDeleteConfirm = null">Non</button>
                </template>
                <template v-else>
                  <button class="action-btn action-btn--del" title="Supprimer" @click="dtDeleteConfirm = tbl.id">
                    <Trash2 :size="13" />
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>

  </div>
</template>

<style scoped>
/* ── Page ────────────────────────────────────────────────── */
.sources-page {
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
  min-height: 40px;
  transition: background-color 150ms ease, box-shadow 150ms ease;
}

.btn-primary:hover:not(:disabled) {
  background-color: oklch(80% 0.14 62);
  box-shadow: var(--shadow-accent);
}

.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-primary--loading {
  min-width: 120px;
  justify-content: center;
}

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
  transition: border-color 150ms ease, color 150ms ease;
}

.btn-ghost:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

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

.stat-n--ok  { color: oklch(70% 0.15 148); }
.stat-n--err { color: var(--error); }
.stat-n--off { color: var(--text-muted); }

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
  height: 40px;
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
.search-input::-webkit-search-cancel-button { opacity: 0.5; cursor: pointer; }

.filters { display: flex; gap: var(--sp-2); }

.select-wrap { position: relative; }

.filter-select {
  appearance: none;
  height: 40px;
  padding: 0 30px 0 var(--sp-3);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms ease, color 150ms ease;
}

.filter-select:focus { border-color: var(--accent-dim); }
.filter-select option { background-color: var(--surface-raised); }

.select-arrow {
  position: absolute;
  right: 9px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

/* ── Sources list ────────────────────────────────────────── */
.sources-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  opacity: 0;
  transition: opacity 300ms ease;
}

.sources-list--visible { opacity: 1; }

/* ── Source row ──────────────────────────────────────────── */
.source-row {
  display: grid;
  grid-template-columns: 48px 1fr 130px 80px 110px 150px;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: background-color 150ms ease, border-color 150ms ease;

  opacity: 0;
  transform: translateY(6px);
  animation: row-in 280ms var(--ease-out-quart) forwards;
  animation-delay: calc(var(--row-i, 0) * 40ms);
}

@keyframes row-in {
  to { opacity: 1; transform: translateY(0); }
}

.source-row:hover {
  background-color: var(--surface-overlay);
  border-color: var(--border-default);
}

.source-row--error {
  background-color: oklch(12.5% 0.035 24);
  border-color: oklch(20% 0.05 24);
}

.source-row--error:hover {
  background-color: oklch(14% 0.04 24);
}

/* ── Type badge ──────────────────────────────────────────── */
.type-badge {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background-color: color-mix(in oklch, var(--tc) 14%, oklch(14% 0.013 258));
  color: var(--tc);
  font-family: var(--font-display);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ── Source info ─────────────────────────────────────────── */
.src-info { min-width: 0; }

.src-name-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: nowrap;
  overflow: hidden;
}

.src-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.type-pill {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background-color: color-mix(in oklch, var(--tc) 14%, oklch(10% 0.013 258));
  color: var(--tc);
  flex-shrink: 0;
  white-space: nowrap;
}

.src-desc {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.src-host {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Records ─────────────────────────────────────────────── */
.src-records {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.src-records-n {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1;
}

.src-records-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

/* ── Sync ────────────────────────────────────────────────── */
.src-sync {
  display: flex;
  align-items: center;
  gap: 5px;
}

.sync-icon { color: var(--text-muted); flex-shrink: 0; }

.sync-time {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
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

.status--active   .status-dot   { background-color: oklch(70% 0.15 148); }
.status--error    .status-dot   { background-color: var(--error); }
.status--inactive .status-dot   { background-color: var(--text-muted); }
.status--pending  .status-dot   { background-color: var(--warning); animation: pulse 2s infinite; }

.status--active   span:last-child { color: oklch(70% 0.15 148); }
.status--error    span:last-child { color: var(--error); }
.status--inactive span:last-child { color: var(--text-muted); }
.status--pending  span:last-child { color: var(--warning); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

/* ── Row actions ─────────────────────────────────────────── */
.src-actions {
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

.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.action-btn--delete:hover:not(:disabled) {
  background-color: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}

.action-btn--edit:hover:not(:disabled) {
  background-color: var(--accent-surface);
  border-color: var(--accent-dim);
  color: var(--accent);
}

/* ── Preview button ───────────────────────────────────────── */
.cell-action { width: 36px; }
.preview-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none;
  color: var(--text-muted); cursor: pointer; transition: all 120ms;
}
.preview-btn:hover:not(:disabled) {
  background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent);
}
.preview-btn--active { background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent); }
.preview-btn:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin-icon { animation: spin 0.7s linear infinite; }

.preview-row { background: var(--surface-overlay); }
.preview-panel { padding: var(--sp-3); }
.preview-label { font-size: var(--text-xs); font-weight: 600; color: var(--text-muted); margin-bottom: var(--sp-2); }
.preview-scroll { overflow-x: auto; max-height: 280px; overflow-y: auto; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); }
.preview-table { width: 100%; border-collapse: collapse; font-size: var(--text-xs); }
.preview-table th {
  position: sticky; top: 0;
  background: var(--surface-muted); padding: var(--sp-2) var(--sp-3);
  text-align: left; font-weight: 700; color: var(--text-muted);
  white-space: nowrap; border-bottom: 1px solid var(--border-subtle);
}
.preview-table td { padding: var(--sp-1) var(--sp-3); color: var(--text-secondary); border-bottom: 1px solid var(--border-subtle); white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }

/* ── Advanced sections ───────────────────────────────────── */
.adv-section {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.adv-summary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  cursor: pointer; list-style: none;
  font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary);
  background: var(--surface-overlay);
  transition: color 150ms, background 150ms;
}
.adv-summary:hover { color: var(--text-primary); background: var(--surface-muted); }
.adv-summary::-webkit-details-marker { display: none; }
.adv-body { padding: var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-4); border-top: 1px solid var(--border-subtle); }

/* ── Form elements ───────────────────────────────────────── */
.form-textarea {
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-overlay); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm);
  outline: none; resize: vertical; transition: border-color 150ms;
}
.form-textarea:focus { border-color: var(--accent-dim); }
.form-checkbox { width: 16px; height: 16px; accent-color: var(--accent); cursor: pointer; }
.toggle-label { cursor: pointer; gap: var(--sp-2); }
.select-wrap-sm { position: relative; }
.form-select {
  appearance: none; height: 40px; padding: 0 30px 0 var(--sp-3);
  background: var(--surface-overlay); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  cursor: pointer; width: 100%; transition: border-color 150ms;
}
.form-select:focus { border-color: var(--accent-dim); }
.form-select option { background: var(--surface-raised); }
.select-arrow-sm { position: absolute; right: 9px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--sp-3); }

.action-btn--spinning svg { animation: spin 0.9s linear infinite; }

.action-btn--tested-ok {
  border-color: oklch(70% 0.15 148);
  color: oklch(70% 0.15 148);
  background-color: oklch(14% 0.04 148);
}

.del-label {
  font-size: var(--text-xs);
  color: var(--error);
  white-space: nowrap;
}

.action-btn--confirm-yes,
.action-btn--confirm-no {
  width: auto;
  padding: 0 var(--sp-2);
  font-size: var(--text-xs);
  font-family: var(--font-ui);
  font-weight: 600;
}

.action-btn--confirm-yes {
  background-color: var(--error-surface);
  border-color: var(--error);
  color: var(--error);
}

.action-btn--confirm-no {
  color: var(--text-secondary);
}

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.source-skel {
  height: 74px;
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

.source-skel:nth-child(2) { animation-delay: 0.08s; }
.source-skel:nth-child(3) { animation-delay: 0.16s; }
.source-skel:nth-child(4) { animation-delay: 0.24s; }
.source-skel:nth-child(5) { animation-delay: 0.32s; }
.source-skel:nth-child(6) { animation-delay: 0.40s; }

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
  max-width: 42ch;
  line-height: 1.6;
}

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
  width: 460px;
  max-width: 100vw;
  height: 100dvh;
  background-color: var(--surface-raised);
  border-left: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
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

.drawer-close:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

/* ── Drawer form ─────────────────────────────────────────── */
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
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms ease;
}

.form-input:focus { border-color: var(--accent-dim); box-shadow: var(--shadow-focus); }
.form-input::placeholder { color: var(--text-muted); }

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 88px;
  gap: var(--sp-3);
  align-items: end;
}

/* ── Type grid ───────────────────────────────────────────── */
.type-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-2);
}

.type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: var(--sp-3) var(--sp-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.type-option:hover {
  background-color: var(--surface-overlay);
  border-color: var(--border-strong);
}

.type-option--active {
  border-color: var(--tc);
  background-color: color-mix(in oklch, var(--tc) 11%, oklch(10% 0.013 258));
}

.type-opt-abbr {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--tc);
  line-height: 1;
}

.type-opt-label {
  font-size: 0.62rem;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
}

.type-option--active .type-opt-label { color: color-mix(in oklch, var(--tc) 70%, var(--text-muted)); }

/* ── File zone ───────────────────────────────────────────── */
.file-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-8) var(--sp-6);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: center;
  transition: all 150ms ease;
}

.file-zone:hover {
  border-color: var(--accent-dim);
  background-color: var(--accent-surface);
}

.file-zone--drag {
  border-color: var(--accent-dim);
  background-color: var(--accent-surface);
  transform: scale(1.01);
}

.file-zone--ok {
  border-color: oklch(65% 0.13 148);
  background-color: oklch(15% 0.05 148);
}

.file-zone-icon { color: var(--text-muted); }
.file-zone--ok .file-zone-icon { color: oklch(65% 0.13 148); }
.file-zone-text { font-size: var(--text-sm); color: var(--text-secondary); }
.file-browse { color: var(--accent-dim); font-weight: 600; }
.file-hint { font-size: var(--text-xs); color: var(--text-muted); }
.file-selected-name { color: oklch(65% 0.13 148); font-weight: 600; word-break: break-all; }

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

/* Spinner */
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
.drawer-anim-enter-active {
  transition: opacity 220ms ease;
}
.drawer-anim-leave-active {
  transition: opacity 180ms ease;
}
.drawer-anim-enter-from,
.drawer-anim-leave-to {
  opacity: 0;
}

.drawer-anim-enter-active .drawer {
  transition: transform 380ms var(--ease-out-expo);
}
.drawer-anim-leave-active .drawer {
  transition: transform 220ms cubic-bezier(0.4, 0, 1, 1);
}
.drawer-anim-enter-from .drawer,
.drawer-anim-leave-to .drawer {
  transform: translateX(100%);
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1200px) {
  .source-row {
    grid-template-columns: 48px 1fr 110px 70px 100px auto;
  }
}

@media (max-width: 960px) {
  .source-row {
    grid-template-columns: 48px 1fr 90px auto;
    grid-template-areas:
      "badge info  records actions"
      "badge sync  status  actions";
    row-gap: var(--sp-1);
  }

  .type-badge  { grid-area: badge; grid-row: 1 / 3; }
  .src-info    { grid-area: info; }
  .src-records { grid-area: records; }
  .src-sync    { grid-area: sync; }
  .status-badge{ grid-area: status; }
  .src-actions { grid-area: actions; grid-row: 1 / 3; }
}

@media (max-width: 680px) {
  .sources-page { padding: var(--sp-4); }
  .stats-strip { flex-wrap: wrap; }
  .stat-div { display: none; }
  .stat-cell { min-width: 45%; }
  .toolbar { flex-wrap: wrap; }
  .search-wrap { max-width: 100%; }

  .source-row {
    grid-template-columns: 40px 1fr auto;
    grid-template-areas:
      "badge info    actions"
      "badge details actions";
    padding: var(--sp-3) var(--sp-4);
    row-gap: 4px;
  }

  .type-badge  { width: 40px; height: 40px; grid-area: badge; grid-row: 1 / 3; }
  .src-info    { grid-area: info; }
  .src-records,
  .src-sync    { display: none; }
  .status-badge{ grid-area: details; }
  .src-actions { grid-area: actions; grid-row: 1 / 3; }
}

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .source-row { animation: none; opacity: 1; transform: none; }
  .source-skel { animation: none; }
  .status--pending .status-dot { animation: none; }
}

/* ═══════════════════════════════════════════════════════════
   DETAIL PANEL
   ═══════════════════════════════════════════════════════════ */

/* ── Content area layout ─────────────────────────────────── */
.content-area {
  display: flex;
  gap: var(--sp-4);
  align-items: flex-start;
  min-height: 0;
}

.sources-list {
  flex: 1;
  min-width: 0;
  transition: flex 300ms var(--ease-out-quart), opacity 300ms ease;
}

/* ── Source row: selected state ──────────────────────────── */
.source-row {
  cursor: pointer;
}

.source-row--selected {
  border-color: var(--accent-dim) !important;
  background-color: color-mix(in oklch, var(--accent) 8%, var(--surface-raised)) !important;
}

/* ── Detail panel container ──────────────────────────────── */
.detail-panel {
  width: 420px;
  flex-shrink: 0;
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: calc(100vh - 200px);
  position: sticky;
  top: var(--sp-6);
}

/* ── Detail panel header ─────────────────────────────────── */
.detail-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  background-color: var(--surface-raised);
}

.detail-hd-info {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  min-width: 0;
}

.detail-type-badge {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background-color: color-mix(in oklch, var(--tc) 14%, oklch(14% 0.013 258));
  color: var(--tc);
  font-family: var(--font-display);
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.detail-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.detail-subtitle {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 1px;
}

.detail-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 150ms ease;
}

.detail-close:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

/* ── Tab bar ─────────────────────────────────────────────── */
.detail-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  background-color: var(--surface-raised);
}

.detail-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: var(--sp-3) var(--sp-2);
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--text-muted);
  transition: color 150ms ease, border-color 150ms ease;
  white-space: nowrap;
}

.detail-tab:hover {
  color: var(--text-secondary);
}

.detail-tab--active {
  color: var(--accent-dim);
  border-bottom-color: var(--accent-dim);
  font-weight: 600;
}

/* ── Tab body ────────────────────────────────────────────── */
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

/* ── Detail loading skeletons ────────────────────────────── */
.detail-skel {
  height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--surface-raised)  25%,
    var(--surface-overlay) 50%,
    var(--surface-raised)  75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.detail-skel:nth-child(2) { animation-delay: 0.08s; width: 85%; }
.detail-skel:nth-child(3) { animation-delay: 0.16s; width: 92%; }
.detail-skel:nth-child(4) { animation-delay: 0.24s; width: 78%; }
.detail-skel:nth-child(5) { animation-delay: 0.32s; width: 88%; }

/* ── Empty state inside panel ────────────────────────────── */
.detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-10) var(--sp-4);
  color: var(--text-muted);
  text-align: center;
}

.detail-empty p {
  font-size: var(--text-sm);
  color: var(--text-muted);
}

/* ── Tab toolbar (sync button row) ───────────────────────── */
.detail-tab-toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-shrink: 0;
  margin-bottom: var(--sp-1);
}

.btn-primary--sm {
  min-height: 30px;
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--text-xs);
}

.sync-feedback {
  font-size: var(--text-xs);
  color: var(--error);
  font-weight: 500;
}

.sync-feedback--ok {
  color: oklch(70% 0.15 148);
}

.spinner--sm {
  width: 12px;
  height: 12px;
  border-width: 2px;
}

/* ── Detail table ────────────────────────────────────────── */
.detail-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
  font-family: var(--font-ui);
}

.detail-table thead tr {
  background-color: var(--surface-overlay);
}

.detail-table th {
  padding: var(--sp-2) var(--sp-3);
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.62rem;
  white-space: nowrap;
  border-bottom: 1px solid var(--border-subtle);
}

.detail-table td {
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
}

.detail-table tbody tr:last-child td {
  border-bottom: none;
}

.detail-table tbody tr:hover td {
  background-color: var(--surface-overlay);
}

.cell-name {
  color: var(--text-primary) !important;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.cell-num {
  text-align: right;
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--text-primary) !important;
  white-space: nowrap;
}

.cell-date {
  white-space: nowrap;
  color: var(--text-muted) !important;
}

.cell-msg {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Log level badges ────────────────────────────────────── */
.log-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.log-badge--error {
  background-color: var(--error-surface);
  color: var(--error);
}

.log-badge--warning {
  background-color: oklch(15% 0.06 60);
  color: var(--warning);
}

.log-badge--info {
  background-color: oklch(14% 0.04 240);
  color: oklch(68% 0.13 240);
}

/* ── Metrics grid ────────────────────────────────────────── */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  padding: var(--sp-4);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.metric-card--wide {
  grid-column: 1 / -1;
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.metric-value {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.metric-value--sm {
  font-size: var(--text-lg);
}

.metric-value--ok { color: oklch(70% 0.15 148); }
.metric-value--err { color: var(--error); }

/* ── Query list ──────────────────────────────────────────── */
.query-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.query-row {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  transition: background-color 150ms ease;
}

.query-row:hover {
  background-color: color-mix(in oklch, var(--surface-overlay) 80%, var(--surface-raised));
}

.query-info {
  flex: 1;
  min-width: 0;
}

.query-name-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.query-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.query-star {
  color: var(--text-muted);
  flex-shrink: 0;
}

.query-star--on {
  color: oklch(78% 0.16 65);
}

.query-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.query-sql {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.7;
}

.query-result {
  display: inline-block;
  margin-top: 4px;
  font-size: var(--text-xs);
  color: oklch(70% 0.15 148);
  font-weight: 600;
}

.query-actions {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  flex-shrink: 0;
}

.action-btn--exec:hover:not(:disabled) {
  background-color: color-mix(in oklch, var(--accent) 14%, var(--surface-overlay));
  border-color: var(--accent-dim);
  color: var(--accent-dim);
}

.action-btn--fav-on {
  border-color: oklch(78% 0.16 65);
  color: oklch(78% 0.16 65);
  background-color: oklch(14% 0.05 65);
}

/* ── Detail panel transition ─────────────────────────────── */
.detail-anim-enter-active {
  transition: opacity 200ms ease, transform 300ms var(--ease-out-expo);
}

.detail-anim-leave-active {
  transition: opacity 160ms ease, transform 200ms cubic-bezier(0.4, 0, 1, 1);
}

.detail-anim-enter-from,
.detail-anim-leave-to {
  opacity: 0;
  transform: translateX(24px);
}

/* ── Responsive: hide detail panel on small screens ──────── */
@media (max-width: 960px) {
  .detail-panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    max-width: 420px;
    max-height: 100dvh;
    border-radius: 0;
    border-left: 1px solid var(--border-default);
    z-index: var(--z-modal);
  }
}

/* ── Extra stat colors ───────────────────────────────────── */
.stat-n--accent  { color: var(--accent-dim); }
.stat-n--quality { color: oklch(74% 0.13 290); }

/* ── Row action: sync & sql ──────────────────────────────── */
.action-btn--sync:hover:not(:disabled) {
  background-color: oklch(14% 0.04 240);
  border-color: oklch(60% 0.13 240);
  color: oklch(68% 0.13 240);
}

.action-btn--sql:hover:not(:disabled) {
  background-color: oklch(14% 0.05 290);
  border-color: oklch(60% 0.12 290);
  color: oklch(68% 0.12 290);
}

.action-btn--sql-active {
  background-color: oklch(14% 0.05 290);
  border-color: oklch(60% 0.12 290);
  color: oklch(68% 0.12 290);
}

/* ═══════════════════════════════════════════════════════════
   SQL EDITOR PANEL
   ═══════════════════════════════════════════════════════════ */

.sql-panel {
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sql-panel-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-5);
  background-color: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.sql-panel-hd-left {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  min-width: 0;
}

.sql-panel-icon { color: oklch(68% 0.12 290); flex-shrink: 0; }

.sql-panel-title {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sql-panel-title strong {
  color: var(--text-primary);
  font-weight: 700;
}

.sql-panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 150ms ease;
}

.sql-panel-close:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.sql-panel-body {
  padding: var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.sql-textarea {
  width: 100%;
  padding: var(--sp-3) var(--sp-4);
  background-color: oklch(10% 0.02 258);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: oklch(88% 0.06 258);
  font-family: 'Courier New', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  outline: none;
  resize: vertical;
  min-height: 110px;
  transition: border-color 150ms ease;
  box-sizing: border-box;
}

.sql-textarea:focus {
  border-color: oklch(60% 0.12 290);
  box-shadow: 0 0 0 3px oklch(60% 0.12 290 / 0.12);
}

.sql-textarea::placeholder { color: var(--text-muted); opacity: 0.6; }

.sql-toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.sql-run-btn {
  gap: var(--sp-2);
}

.sql-hint {
  font-size: var(--text-xs);
  color: var(--text-muted);
  flex: 1;
}

.btn-ghost--sm {
  min-height: 30px;
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--text-xs);
}

.sql-error {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background-color: var(--error-surface);
  border: 1px solid oklch(30% 0.08 24);
  border-radius: var(--radius-md);
  color: var(--error);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.5;
}

.sql-error svg { flex-shrink: 0; margin-top: 1px; }

.sql-results {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.sql-results-hd {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.sql-results-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background-color: oklch(14% 0.04 148);
  border: 1px solid oklch(30% 0.08 148);
  border-radius: var(--radius-sm);
  color: oklch(70% 0.15 148);
  font-size: var(--text-xs);
  font-weight: 700;
}

.sql-results-scroll {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 320px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.sql-results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
  font-family: var(--font-ui);
}

.sql-results-table thead tr {
  background-color: var(--surface-overlay);
  position: sticky;
  top: 0;
}

.sql-results-table th {
  padding: var(--sp-2) var(--sp-3);
  text-align: left;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.03em;
  white-space: nowrap;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.62rem;
  text-transform: uppercase;
}

.sql-results-table td {
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sql-results-table tbody tr:last-child td { border-bottom: none; }
.sql-results-table tbody tr:hover td { background-color: var(--surface-overlay); }

.sql-no-cols {
  padding: var(--sp-6);
  text-align: center;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

/* ── SQL panel transition ─────────────────────────────────── */
.sql-panel-anim-enter-active {
  transition: opacity 200ms ease, transform 280ms var(--ease-out-expo);
}
.sql-panel-anim-leave-active {
  transition: opacity 160ms ease, transform 180ms cubic-bezier(0.4, 0, 1, 1);
}
.sql-panel-anim-enter-from,
.sql-panel-anim-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Main tab nav ─────────────────────────────────────────── */
.main-tab-nav {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.main-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: color 150ms, border-color 150ms;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}
.main-tab-btn:hover { color: var(--text-secondary); background: var(--surface-overlay); }
.main-tab-btn--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: none;
}

.tab-chip {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: var(--accent-surface);
  color: var(--accent);
}

/* ── Secondary button ─────────────────────────────────────── */
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  min-height: 40px;
  transition: border-color 150ms ease, color 150ms ease, background 150ms ease;
}
.btn-secondary:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
  background: var(--surface-overlay);
}

/* ── DataTable page ───────────────────────────────────────── */
.dt-page-wrap {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: auto;
  flex: 1;
}

.dt-page-table {
  width: 100%;
  border-collapse: collapse;
}

.dt-page-th {
  padding: var(--sp-2) var(--sp-4);
  font-family: var(--font-display);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-overlay);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}
.dt-page-th--act { width: 80px; }

.dt-page-row {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;
}
.dt-page-row:last-child { border-bottom: none; }
.dt-page-row:hover { background: var(--surface-overlay); }

.dt-page-td {
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  vertical-align: middle;
}

.dt-page-td--name {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-base);
  white-space: nowrap;
}

.dt-page-td--act { white-space: nowrap; }

.dash { color: var(--text-muted); }

.empty-icon { color: var(--border-default); }
</style>
