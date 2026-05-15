<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Star, Plus, Search, Edit, Trash2, Play, Code2, CheckCircle,
  X, Layers, Network, Calculator, GitMerge,
  Copy, RefreshCw, Archive,
} from 'lucide-vue-next'
import api from '@/api/axios'

// ── Types ──────────────────────────────────────────────────────────────────

type SchemaType = 'star' | 'snowflake' | 'galaxy' | 'constellation'
type SchemaStatus = 'draft' | 'active' | 'archived' | 'deprecated'
type Grain = 'transaction' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
type ActiveTab = 'schemas' | 'galaxies' | 'calculations' | 'hierarchies' | 'relations'

interface DimensionalSchema {
  id: string
  name: string
  description?: string
  version?: string
  schema_type: SchemaType
  schema_type_display: string
  status: SchemaStatus
  status_display: string
  grain: Grain
  grain_display: string
  default_join_type?: string
  fact_tables: string[]
  dimension_tables: string[]
  measures: string[]
  category?: string
  business_domain?: string
  documentation_url?: string
  owner?: string | null
  owner_name?: string
  team?: string | null
  team_name?: string
  created_by?: string | null
  created_by_name?: string
  query_count: number
  last_queried_at?: string
  tags: string[]
}

interface GalaxySchema {
  id: string
  name: string
  description?: string
  status: string
  status_display: string
  dimensional_schemas: string[]
  dimensional_schema_count: number
  galaxy_relationships?: any
  schema_graph?: any
  owner?: string | null
  owner_name?: string
  tags: string[]
  created_at: string
  updated_at: string
}

interface Calculation {
  id: string
  name: string
  formula?: string
  type?: string
  status?: string
}

interface DimensionHierarchy {
  id: string
  name: string
  dimension_table?: string
  levels?: any[]
}

interface FactRelationship {
  id: string
  name: string
  description?: string
  from_fact?: string
  to_fact?: string
  from_column?: string
  to_column?: string
  relation_type?: string
  join_type?: string
  is_enabled: boolean
  cardinality?: number | null
}

interface FactRelForm {
  name: string
  description: string
  from_fact: string
  to_fact: string
  from_column: string
  to_column: string
  relation_type: string
  join_type: string
  is_enabled: boolean
}

interface GlobalStats {
  total_schemas?: number
  active_schemas?: number
  cached_schemas?: number
  [key: string]: any
}

// ── Schema Form ─────────────────────────────────────────────────────────────

interface SchemaForm {
  name: string
  description: string
  schema_type: SchemaType
  status: SchemaStatus
  grain: Grain
  version: string
  category: string
  business_domain: string
}

interface GalaxyForm {
  name: string
  description: string
  status: string
}

interface CalcForm {
  name: string
  formula: string
  type: string
  status: string
}

interface HierarchyForm {
  name: string
  dimension_table: string
  levels: string
}

// ── State ───────────────────────────────────────────────────────────────────

const activeTab = ref<ActiveTab>('schemas')

// --- Stats ---
const stats = ref<GlobalStats>({})
const statsLoading = ref(false)

// --- Schemas ---
const schemas = ref<DimensionalSchema[]>([])
const schemasLoading = ref(false)
const schemasSearch = ref('')
const schemasTypeFilter = ref('')
const schemasStatusFilter = ref('')
const selectedSchema = ref<DimensionalSchema | null>(null)

// Detail panel tabs
const detailTab = ref<'sql' | 'validate' | 'execute'>('sql')
const detailSql = ref('')
const detailSqlLoading = ref(false)
const detailValidateResult = ref<any>(null)
const detailValidateLoading = ref(false)
const detailExecuteResult = ref<any>(null)
const detailExecuteLoading = ref(false)
const detailCacheLoading = ref(false)
const detailCacheMsg = ref('')
const copiedSql = ref(false)

// Create/Edit modal
const showSchemaModal = ref(false)
const schemaModalMode = ref<'create' | 'edit'>('create')
const schemaModalLoading = ref(false)
const schemaForm = ref<SchemaForm>({
  name: '',
  description: '',
  schema_type: 'star',
  status: 'draft',
  grain: 'daily',
  version: '',
  category: '',
  business_domain: '',
})
const editingSchemaId = ref<string | null>(null)

// Delete confirm
const showDeleteSchemaConfirm = ref(false)
const deletingSchema = ref<DimensionalSchema | null>(null)
const deleteSchemaLoading = ref(false)

// --- Galaxies ---
const galaxies = ref<GalaxySchema[]>([])
const galaxiesLoading = ref(false)
const showGalaxyModal = ref(false)
const galaxyModalMode = ref<'create' | 'edit'>('create')
const galaxyModalLoading = ref(false)
const galaxyForm = ref<GalaxyForm>({ name: '', description: '', status: 'draft' })
const editingGalaxyId = ref<string | null>(null)
const showDeleteGalaxyConfirm = ref(false)
const deletingGalaxy = ref<GalaxySchema | null>(null)
const deleteGalaxyLoading = ref(false)
const galaxySqlMap = ref<Record<string, string>>({})
const galaxySqlLoading = ref<Record<string, boolean>>({})
const galaxyExecLoading = ref<Record<string, boolean>>({})
const galaxyExecResult = ref<Record<string, any>>({})
const showGalaxySqlPanel = ref<string | null>(null)

// --- Calculations ---
const calculations = ref<Calculation[]>([])
const calculationsLoading = ref(false)
const showCalcForm = ref(false)
const calcFormMode = ref<'create' | 'edit'>('create')
const calcFormLoading = ref(false)
const calcForm = ref<CalcForm>({ name: '', formula: '', type: '', status: '' })
const editingCalcId = ref<string | null>(null)
const showDeleteCalcConfirm = ref(false)
const deletingCalc = ref<Calculation | null>(null)
const deleteCalcLoading = ref(false)

// --- Inline per-schema actions ---
const inlineValidating  = ref<Record<string, boolean>>({})
const inlineValidResult = ref<Record<string, { is_valid?: boolean; errors?: any[]; error?: string } | null>>({})
const inlineSqlLoading  = ref<Record<string, boolean>>({})
const inlineSqlResult   = ref<Record<string, string | null>>({})
const inlineSqlOpen     = ref<Record<string, boolean>>({})
const inlineSqlCopied   = ref<Record<string, boolean>>({})
const inlineCacheLoading = ref<Record<string, boolean>>({})
const inlineCacheMsg    = ref<Record<string, string>>({})

// --- Hierarchies ---
const hierarchies = ref<DimensionHierarchy[]>([])
const hierarchiesLoading = ref(false)
const showHierarchyForm = ref(false)
const hierarchyFormMode = ref<'create' | 'edit'>('create')
const hierarchyFormLoading = ref(false)
const hierarchyForm = ref<HierarchyForm>({ name: '', dimension_table: '', levels: '' })
const editingHierarchyId = ref<string | null>(null)
const showDeleteHierarchyConfirm = ref(false)
const deletingHierarchy = ref<DimensionHierarchy | null>(null)
const deleteHierarchyLoading = ref(false)

// --- FactRelationships ---
const factRels = ref<FactRelationship[]>([])
const factRelsLoading = ref(false)
const showFactRelForm = ref(false)
const factRelFormMode = ref<'create' | 'edit'>('create')
const factRelFormLoading = ref(false)
const factRelForm = ref<FactRelForm>({ name: '', description: '', from_fact: '', to_fact: '', from_column: '', to_column: '', relation_type: 'direct', join_type: 'inner', is_enabled: true })
const editingFactRelId = ref<string | null>(null)
const showDeleteFactRelConfirm = ref(false)
const deletingFactRel = ref<FactRelationship | null>(null)
const deleteFactRelLoading = ref(false)

// ── Computed ────────────────────────────────────────────────────────────────

const filteredSchemas = computed(() => {
  let list = schemas.value
  if (schemasSearch.value) {
    const q = schemasSearch.value.toLowerCase()
    list = list.filter(s => s.name.toLowerCase().includes(q) || (s.description ?? '').toLowerCase().includes(q))
  }
  if (schemasTypeFilter.value) {
    list = list.filter(s => s.schema_type === schemasTypeFilter.value)
  }
  if (schemasStatusFilter.value) {
    list = list.filter(s => s.status === schemasStatusFilter.value)
  }
  return list
})

// ── Color helpers ───────────────────────────────────────────────────────────

function schemaTypeColor(type: SchemaType): string {
  switch (type) {
    case 'star':          return 'type--star'
    case 'snowflake':     return 'type--snowflake'
    case 'galaxy':        return 'type--galaxy'
    case 'constellation': return 'type--constellation'
    default:              return ''
  }
}

function statusColor(status: SchemaStatus | string): string {
  switch (status) {
    case 'draft':       return 'status--draft'
    case 'active':      return 'status--active'
    case 'archived':    return 'status--archived'
    case 'deprecated':  return 'status--deprecated'
    default:            return ''
  }
}

// ── Format helpers ──────────────────────────────────────────────────────────

function fmtCount(n: number | undefined): string {
  if (n === undefined || n === null) return '0'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

// ── API: Stats ──────────────────────────────────────────────────────────────

async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await api.get('/api/star-schema/dimensional-schemas/stats/')
    stats.value = res.data ?? {}
  } catch {
    stats.value = {}
  } finally {
    statsLoading.value = false
  }
}

// ── API: Schemas ────────────────────────────────────────────────────────────

async function fetchSchemas() {
  schemasLoading.value = true
  try {
    const res = await api.get('/api/star-schema/dimensional-schemas/')
    const data = res.data
    schemas.value = Array.isArray(data?.results) ? data.results
                  : Array.isArray(data)          ? data
                  : []
  } catch {
    schemas.value = []
  } finally {
    schemasLoading.value = false
  }
}

function openCreateSchema() {
  schemaModalMode.value = 'create'
  editingSchemaId.value = null
  schemaForm.value = {
    name: '', description: '', schema_type: 'star',
    status: 'draft', grain: 'daily', version: '',
    category: '', business_domain: '',
  }
  showSchemaModal.value = true
}

function openEditSchema(s: DimensionalSchema) {
  schemaModalMode.value = 'edit'
  editingSchemaId.value = s.id
  schemaForm.value = {
    name: s.name,
    description: s.description ?? '',
    schema_type: s.schema_type,
    status: s.status,
    grain: s.grain,
    version: s.version ?? '',
    category: s.category ?? '',
    business_domain: s.business_domain ?? '',
  }
  showSchemaModal.value = true
}

async function saveSchema() {
  if (!schemaForm.value.name.trim()) return
  schemaModalLoading.value = true
  try {
    if (schemaModalMode.value === 'create') {
      await api.post('/api/star-schema/dimensional-schemas/', schemaForm.value)
    } else {
      await api.patch(`/api/star-schema/dimensional-schemas/${editingSchemaId.value}/`, schemaForm.value)
    }
    showSchemaModal.value = false
    await fetchSchemas()
    await fetchStats()
  } catch { /* ignore */ } finally {
    schemaModalLoading.value = false
  }
}

function confirmDeleteSchema(s: DimensionalSchema) {
  deletingSchema.value = s
  showDeleteSchemaConfirm.value = true
}

async function doDeleteSchema() {
  if (!deletingSchema.value) return
  deleteSchemaLoading.value = true
  try {
    await api.delete(`/api/star-schema/dimensional-schemas/${deletingSchema.value.id}/`)
    if (selectedSchema.value?.id === deletingSchema.value.id) selectedSchema.value = null
    showDeleteSchemaConfirm.value = false
    deletingSchema.value = null
    await fetchSchemas()
    await fetchStats()
  } catch { /* ignore */ } finally {
    deleteSchemaLoading.value = false
  }
}

function selectSchema(s: DimensionalSchema) {
  selectedSchema.value = s
  detailTab.value = 'sql'
  detailSql.value = ''
  detailValidateResult.value = null
  detailExecuteResult.value = null
  detailCacheMsg.value = ''
}

// Detail panel actions

async function fetchSql() {
  if (!selectedSchema.value) return
  detailSqlLoading.value = true
  detailSql.value = ''
  try {
    const res = await api.get(`/api/star-schema/dimensional-schemas/${selectedSchema.value.id}/sql/`)
    detailSql.value = res.data?.sql ?? res.data?.content ?? JSON.stringify(res.data, null, 2)
  } catch (e: any) {
    detailSql.value = `Erreur: ${e?.response?.data?.detail ?? e.message}`
  } finally {
    detailSqlLoading.value = false
  }
}

async function validateSchema() {
  if (!selectedSchema.value) return
  detailValidateLoading.value = true
  detailValidateResult.value = null
  try {
    const res = await api.post(`/api/star-schema/dimensional-schemas/${selectedSchema.value.id}/validate/`)
    detailValidateResult.value = res.data
  } catch (e: any) {
    detailValidateResult.value = { error: e?.response?.data?.detail ?? e.message }
  } finally {
    detailValidateLoading.value = false
  }
}

async function executeSchema() {
  if (!selectedSchema.value) return
  detailExecuteLoading.value = true
  detailExecuteResult.value = null
  try {
    const res = await api.post(`/api/star-schema/dimensional-schemas/${selectedSchema.value.id}/execute/`)
    detailExecuteResult.value = res.data
  } catch (e: any) {
    detailExecuteResult.value = { error: e?.response?.data?.detail ?? e.message }
  } finally {
    detailExecuteLoading.value = false
  }
}

async function clearCache() {
  if (!selectedSchema.value) return
  detailCacheLoading.value = true
  detailCacheMsg.value = ''
  try {
    await api.post(`/api/star-schema/dimensional-schemas/${selectedSchema.value.id}/clear_cache/`)
    detailCacheMsg.value = 'Cache effacé avec succès.'
    setTimeout(() => { detailCacheMsg.value = '' }, 4000)
  } catch (e: any) {
    detailCacheMsg.value = `Erreur: ${e?.response?.data?.detail ?? e.message}`
    setTimeout(() => { detailCacheMsg.value = '' }, 4000)
  } finally {
    detailCacheLoading.value = false
  }
}

async function copySql() {
  if (!detailSql.value) return
  try {
    await navigator.clipboard.writeText(detailSql.value)
    copiedSql.value = true
    setTimeout(() => { copiedSql.value = false }, 1500)
  } catch { /* ignore */ }
}

// ── API: Inline per-schema actions ─────────────────────────────────────────

async function validateSchemaInline(id: string) {
  inlineValidating.value  = { ...inlineValidating.value,  [id]: true }
  inlineValidResult.value = { ...inlineValidResult.value, [id]: null }
  try {
    const res = await api.post(`/api/star-schema/dimensional-schemas/${id}/validate/`)
    inlineValidResult.value = { ...inlineValidResult.value, [id]: res.data }
  } catch (e: any) {
    inlineValidResult.value = { ...inlineValidResult.value, [id]: { error: e?.response?.data?.detail ?? e.message } }
  } finally {
    inlineValidating.value = { ...inlineValidating.value, [id]: false }
  }
}

async function generateSqlInline(id: string) {
  // Toggle : si panel déjà ouvert et SQL déjà chargé, refermer
  if (inlineSqlOpen.value[id] && inlineSqlResult.value[id]) {
    inlineSqlOpen.value = { ...inlineSqlOpen.value, [id]: false }
    return
  }
  inlineSqlOpen.value   = { ...inlineSqlOpen.value,   [id]: true }
  inlineSqlLoading.value = { ...inlineSqlLoading.value, [id]: true }
  inlineSqlResult.value  = { ...inlineSqlResult.value,  [id]: null }
  try {
    const res = await api.get(`/api/star-schema/dimensional-schemas/${id}/sql/`)
    inlineSqlResult.value = { ...inlineSqlResult.value, [id]: res.data?.sql ?? res.data?.content ?? JSON.stringify(res.data, null, 2) }
  } catch (e: any) {
    inlineSqlResult.value = { ...inlineSqlResult.value, [id]: `Erreur: ${e?.response?.data?.detail ?? e.message}` }
  } finally {
    inlineSqlLoading.value = { ...inlineSqlLoading.value, [id]: false }
  }
}

async function copySqlInline(id: string) {
  const sql = inlineSqlResult.value[id]
  if (!sql) return
  try {
    await navigator.clipboard.writeText(sql)
    inlineSqlCopied.value = { ...inlineSqlCopied.value, [id]: true }
    setTimeout(() => { inlineSqlCopied.value = { ...inlineSqlCopied.value, [id]: false } }, 1500)
  } catch { /* ignore */ }
}

async function clearCacheInline(id: string) {
  inlineCacheLoading.value = { ...inlineCacheLoading.value, [id]: true }
  inlineCacheMsg.value     = { ...inlineCacheMsg.value,     [id]: '' }
  try {
    await api.post(`/api/star-schema/dimensional-schemas/${id}/clear_cache/`)
    inlineCacheMsg.value = { ...inlineCacheMsg.value, [id]: 'Cache effacé.' }
  } catch (e: any) {
    inlineCacheMsg.value = { ...inlineCacheMsg.value, [id]: `Erreur: ${e?.response?.data?.detail ?? e.message}` }
  } finally {
    inlineCacheLoading.value = { ...inlineCacheLoading.value, [id]: false }
    setTimeout(() => { inlineCacheMsg.value = { ...inlineCacheMsg.value, [id]: '' } }, 4000)
  }
}

// ── API: Galaxies ───────────────────────────────────────────────────────────

async function fetchGalaxies() {
  galaxiesLoading.value = true
  try {
    const res = await api.get('/api/star-schema/galaxies/')
    const data = res.data
    galaxies.value = Array.isArray(data?.results) ? data.results
                   : Array.isArray(data)          ? data
                   : []
  } catch {
    galaxies.value = []
  } finally {
    galaxiesLoading.value = false
  }
}

function openCreateGalaxy() {
  galaxyModalMode.value = 'create'
  editingGalaxyId.value = null
  galaxyForm.value = { name: '', description: '', status: 'draft' }
  showGalaxyModal.value = true
}

function openEditGalaxy(g: GalaxySchema) {
  galaxyModalMode.value = 'edit'
  editingGalaxyId.value = g.id
  galaxyForm.value = { name: g.name, description: g.description ?? '', status: g.status }
  showGalaxyModal.value = true
}

async function saveGalaxy() {
  if (!galaxyForm.value.name.trim()) return
  galaxyModalLoading.value = true
  try {
    if (galaxyModalMode.value === 'create') {
      await api.post('/api/star-schema/galaxies/', galaxyForm.value)
    } else {
      await api.patch(`/api/star-schema/galaxies/${editingGalaxyId.value}/`, galaxyForm.value)
    }
    showGalaxyModal.value = false
    await fetchGalaxies()
  } catch { /* ignore */ } finally {
    galaxyModalLoading.value = false
  }
}

function confirmDeleteGalaxy(g: GalaxySchema) {
  deletingGalaxy.value = g
  showDeleteGalaxyConfirm.value = true
}

async function doDeleteGalaxy() {
  if (!deletingGalaxy.value) return
  deleteGalaxyLoading.value = true
  try {
    await api.delete(`/api/star-schema/galaxies/${deletingGalaxy.value.id}/`)
    showDeleteGalaxyConfirm.value = false
    deletingGalaxy.value = null
    await fetchGalaxies()
  } catch { /* ignore */ } finally {
    deleteGalaxyLoading.value = false
  }
}

async function executeGalaxyUnified(g: GalaxySchema) {
  galaxyExecLoading.value = { ...galaxyExecLoading.value, [g.id]: true }
  galaxyExecResult.value = { ...galaxyExecResult.value, [g.id]: null }
  try {
    const res = await api.post(`/api/star-schema/galaxies/${g.id}/execute_unified/`)
    galaxyExecResult.value = { ...galaxyExecResult.value, [g.id]: res.data }
  } catch (e: any) {
    galaxyExecResult.value = { ...galaxyExecResult.value, [g.id]: { error: e?.response?.data?.detail ?? e.message } }
  } finally {
    galaxyExecLoading.value = { ...galaxyExecLoading.value, [g.id]: false }
  }
}

async function fetchGalaxyUnifiedSql(g: GalaxySchema) {
  if (showGalaxySqlPanel.value === g.id) {
    showGalaxySqlPanel.value = null
    return
  }
  showGalaxySqlPanel.value = g.id
  if (galaxySqlMap.value[g.id]) return
  galaxySqlLoading.value = { ...galaxySqlLoading.value, [g.id]: true }
  try {
    const res = await api.get(`/api/star-schema/galaxies/${g.id}/unified_sql/`)
    galaxySqlMap.value = { ...galaxySqlMap.value, [g.id]: res.data?.sql ?? JSON.stringify(res.data, null, 2) }
  } catch (e: any) {
    galaxySqlMap.value = { ...galaxySqlMap.value, [g.id]: `Erreur: ${e?.response?.data?.detail ?? e.message}` }
  } finally {
    galaxySqlLoading.value = { ...galaxySqlLoading.value, [g.id]: false }
  }
}

// ── API: Calculations ───────────────────────────────────────────────────────

async function fetchCalculations() {
  calculationsLoading.value = true
  try {
    const res = await api.get('/api/star-schema/calculations/')
    const data = res.data
    calculations.value = Array.isArray(data?.results) ? data.results
                       : Array.isArray(data)          ? data
                       : []
  } catch {
    calculations.value = []
  } finally {
    calculationsLoading.value = false
  }
}

function openCreateCalc() {
  calcFormMode.value = 'create'
  editingCalcId.value = null
  calcForm.value = { name: '', formula: '', type: '', status: '' }
  showCalcForm.value = true
}

function openEditCalc(c: Calculation) {
  calcFormMode.value = 'edit'
  editingCalcId.value = c.id
  calcForm.value = { name: c.name, formula: c.formula ?? '', type: c.type ?? '', status: c.status ?? '' }
  showCalcForm.value = true
}

async function saveCalc() {
  if (!calcForm.value.name.trim()) return
  calcFormLoading.value = true
  try {
    if (calcFormMode.value === 'create') {
      await api.post('/api/star-schema/calculations/', calcForm.value)
    } else {
      await api.patch(`/api/star-schema/calculations/${editingCalcId.value}/`, calcForm.value)
    }
    showCalcForm.value = false
    await fetchCalculations()
  } catch { /* ignore */ } finally {
    calcFormLoading.value = false
  }
}

function confirmDeleteCalc(c: Calculation) {
  deletingCalc.value = c
  showDeleteCalcConfirm.value = true
}

async function doDeleteCalc() {
  if (!deletingCalc.value) return
  deleteCalcLoading.value = true
  try {
    await api.delete(`/api/star-schema/calculations/${deletingCalc.value.id}/`)
    showDeleteCalcConfirm.value = false
    deletingCalc.value = null
    await fetchCalculations()
  } catch { /* ignore */ } finally {
    deleteCalcLoading.value = false
  }
}

// ── API: Hierarchies ────────────────────────────────────────────────────────

async function fetchHierarchies() {
  hierarchiesLoading.value = true
  try {
    const res = await api.get('/api/star-schema/dimension-hierarchies/')
    const data = res.data
    hierarchies.value = Array.isArray(data?.results) ? data.results
                      : Array.isArray(data)          ? data
                      : []
  } catch {
    hierarchies.value = []
  } finally {
    hierarchiesLoading.value = false
  }
}

function openCreateHierarchy() {
  hierarchyFormMode.value = 'create'
  editingHierarchyId.value = null
  hierarchyForm.value = { name: '', dimension_table: '', levels: '' }
  showHierarchyForm.value = true
}

function openEditHierarchy(h: DimensionHierarchy) {
  hierarchyFormMode.value = 'edit'
  editingHierarchyId.value = h.id
  hierarchyForm.value = {
    name: h.name,
    dimension_table: h.dimension_table ?? '',
    levels: Array.isArray(h.levels) ? h.levels.join(', ') : '',
  }
  showHierarchyForm.value = true
}

async function saveHierarchy() {
  if (!hierarchyForm.value.name.trim()) return
  hierarchyFormLoading.value = true
  const payload = {
    name: hierarchyForm.value.name,
    dimension_table: hierarchyForm.value.dimension_table,
    levels: hierarchyForm.value.levels ? hierarchyForm.value.levels.split(',').map(l => l.trim()).filter(Boolean) : [],
  }
  try {
    if (hierarchyFormMode.value === 'create') {
      await api.post('/api/star-schema/dimension-hierarchies/', payload)
    } else {
      await api.patch(`/api/star-schema/dimension-hierarchies/${editingHierarchyId.value}/`, payload)
    }
    showHierarchyForm.value = false
    await fetchHierarchies()
  } catch { /* ignore */ } finally {
    hierarchyFormLoading.value = false
  }
}

function confirmDeleteHierarchy(h: DimensionHierarchy) {
  deletingHierarchy.value = h
  showDeleteHierarchyConfirm.value = true
}

async function doDeleteHierarchy() {
  if (!deletingHierarchy.value) return
  deleteHierarchyLoading.value = true
  try {
    await api.delete(`/api/star-schema/dimension-hierarchies/${deletingHierarchy.value.id}/`)
    showDeleteHierarchyConfirm.value = false
    deletingHierarchy.value = null
    await fetchHierarchies()
  } catch { /* ignore */ } finally {
    deleteHierarchyLoading.value = false
  }
}

async function fetchFactRels() {
  factRelsLoading.value = true
  try {
    const { data } = await api.get('/api/star-schema/fact-relationships/')
    factRels.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    factRels.value = []
  } finally {
    factRelsLoading.value = false
  }
}

function openEditFactRel(rel: FactRelationship) {
  factRelFormMode.value = 'edit'
  editingFactRelId.value = rel.id
  factRelForm.value = {
    name: rel.name,
    description: rel.description || '',
    from_fact: rel.from_fact || '',
    to_fact: rel.to_fact || '',
    from_column: rel.from_column || '',
    to_column: rel.to_column || '',
    relation_type: rel.relation_type || 'direct',
    join_type: rel.join_type || 'inner',
    is_enabled: rel.is_enabled,
  }
  showFactRelForm.value = true
}

async function saveFactRel() {
  factRelFormLoading.value = true
  try {
    if (editingFactRelId.value) {
      const { data } = await api.patch(`/api/star-schema/fact-relationships/${editingFactRelId.value}/`, factRelForm.value)
      const idx = factRels.value.findIndex(r => r.id === editingFactRelId.value)
      if (idx !== -1) factRels.value[idx] = data
    } else {
      const { data } = await api.post('/api/star-schema/fact-relationships/', factRelForm.value)
      factRels.value.unshift(data)
    }
    showFactRelForm.value = false
    editingFactRelId.value = null
    factRelFormMode.value = 'create'
    factRelForm.value = { name: '', description: '', from_fact: '', to_fact: '', from_column: '', to_column: '', relation_type: 'direct', join_type: 'inner', is_enabled: true }
  } catch { /* ignore */ } finally {
    factRelFormLoading.value = false
  }
}

function confirmDeleteFactRel(rel: FactRelationship) {
  deletingFactRel.value = rel
  showDeleteFactRelConfirm.value = true
}

async function doDeleteFactRel() {
  if (!deletingFactRel.value) return
  deleteFactRelLoading.value = true
  try {
    await api.delete(`/api/star-schema/fact-relationships/${deletingFactRel.value.id}/`)
    showDeleteFactRelConfirm.value = false
    deletingFactRel.value = null
    await fetchFactRels()
  } catch { /* ignore */ } finally {
    deleteFactRelLoading.value = false
  }
}

// ── Lifecycle ───────────────────────────────────────────────────────────────

watch(activeTab, (tab) => {
  if (tab === 'schemas' && schemas.value.length === 0) fetchSchemas()
  if (tab === 'galaxies' && galaxies.value.length === 0) fetchGalaxies()
  if (tab === 'calculations' && calculations.value.length === 0) fetchCalculations()
  if (tab === 'hierarchies' && hierarchies.value.length === 0) fetchHierarchies()
  if (tab === 'relations' && factRels.value.length === 0) fetchFactRels()
})

onMounted(() => {
  fetchStats()
  fetchSchemas()
})
</script>

<template>
  <div class="ss">

    <!-- ── Page Header ────────────────────────────────────────────────────── -->
    <header class="ss-header">
      <div class="ss-title-row">
        <Star :size="22" class="ss-title-icon" />
        <h2 class="ss-title">Schémas en étoile</h2>
      </div>

      <!-- Stats strip -->
      <div class="stats-strip">
        <div class="stat-card">
          <span class="stat-val">{{ fmtCount(stats.total_schemas) }}</span>
          <span class="stat-lbl">Total schémas</span>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-card">
          <span class="stat-val stat-val--green">{{ fmtCount(stats.active_schemas) }}</span>
          <span class="stat-lbl">Actifs</span>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-card">
          <span class="stat-val stat-val--blue">{{ fmtCount(stats.cached_schemas) }}</span>
          <span class="stat-lbl">En cache</span>
        </div>
      </div>
    </header>

    <!-- ── Tab Bar ────────────────────────────────────────────────────────── -->
    <nav class="tab-bar" role="tablist">
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'schemas' }"
        role="tab"
        :aria-selected="activeTab === 'schemas'"
        @click="activeTab = 'schemas'"
      >
        <Layers :size="14" />
        Schémas
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'galaxies' }"
        role="tab"
        :aria-selected="activeTab === 'galaxies'"
        @click="activeTab = 'galaxies'"
      >
        <Network :size="14" />
        Galaxies
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'calculations' }"
        role="tab"
        :aria-selected="activeTab === 'calculations'"
        @click="activeTab = 'calculations'"
      >
        <Calculator :size="14" />
        Calculs
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'hierarchies' }"
        role="tab"
        :aria-selected="activeTab === 'hierarchies'"
        @click="activeTab = 'hierarchies'"
      >
        <GitMerge :size="14" />
        Hiérarchies
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'relations' }"
        role="tab"
        :aria-selected="activeTab === 'relations'"
        @click="activeTab = 'relations'"
      >
        <GitMerge :size="14" />
        Relations
      </button>
    </nav>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 1: SCHEMAS                                                       -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'schemas'" class="tab-body">

      <!-- Toolbar -->
      <div class="toolbar">
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input
            v-model="schemasSearch"
            type="text"
            class="search-input"
            placeholder="Rechercher un schéma…"
            aria-label="Rechercher"
          />
        </div>

        <select v-model="schemasTypeFilter" class="filter-select" aria-label="Filtrer par type">
          <option value="">Tous les types</option>
          <option value="star">Étoile</option>
          <option value="snowflake">Flocon</option>
          <option value="galaxy">Galaxie</option>
          <option value="constellation">Constellation</option>
        </select>

        <select v-model="schemasStatusFilter" class="filter-select" aria-label="Filtrer par statut">
          <option value="">Tous les statuts</option>
          <option value="draft">Brouillon</option>
          <option value="active">Actif</option>
          <option value="archived">Archivé</option>
          <option value="deprecated">Déprécié</option>
        </select>

        <button class="btn-primary" @click="openCreateSchema">
          <Plus :size="14" />
          Nouveau schéma
        </button>
      </div>

      <!-- Content: grid + detail panel -->
      <div class="schemas-layout">

        <!-- Card grid -->
        <div class="card-grid-wrap">
          <!-- Loading skeleton -->
          <div v-if="schemasLoading" class="skel-grid">
            <div v-for="i in 6" :key="i" class="skel-card"></div>
          </div>

          <!-- Empty -->
          <div v-else-if="filteredSchemas.length === 0" class="empty-state">
            <Layers :size="36" class="empty-icon" />
            <p>Aucun schéma trouvé</p>
          </div>

          <!-- Grid -->
          <div v-else class="card-grid">
            <div
              v-for="schema in filteredSchemas"
              :key="schema.id"
              class="schema-card"
              :class="{ 'schema-card--selected': selectedSchema?.id === schema.id }"
              role="button"
              tabindex="0"
              @click="selectSchema(schema)"
              @keydown.enter="selectSchema(schema)"
            >
              <!-- Card header -->
              <div class="card-head">
                <span class="card-name">{{ schema.name }}</span>
                <div class="card-badges">
                  <span class="type-badge" :class="schemaTypeColor(schema.schema_type)">
                    {{ schema.schema_type_display || schema.schema_type }}
                  </span>
                  <span class="status-badge" :class="statusColor(schema.status)">
                    {{ schema.status_display || schema.status }}
                  </span>
                </div>
              </div>

              <!-- Grain & domain -->
              <div class="card-meta-row">
                <span class="meta-chip">
                  <Star :size="10" />
                  {{ schema.grain_display || schema.grain }}
                </span>
                <span v-if="schema.business_domain" class="meta-chip meta-chip--muted">
                  {{ schema.business_domain }}
                </span>
                <span v-if="schema.category" class="meta-chip meta-chip--muted">
                  {{ schema.category }}
                </span>
              </div>

              <!-- Owner + version -->
              <div class="card-owner-row">
                <span v-if="schema.owner_name" class="owner-txt">{{ schema.owner_name }}</span>
                <span v-if="schema.version" class="version-txt">v{{ schema.version }}</span>
                <span class="query-count">
                  <Play :size="10" />
                  {{ fmtCount(schema.query_count) }} requêtes
                </span>
              </div>

              <!-- Actions -->
              <div class="card-actions" @click.stop>
                <!-- Valider inline -->
                <button
                  class="icon-btn icon-btn--validate"
                  :title="inlineValidating[schema.id] ? 'Validation…' : 'Valider'"
                  :disabled="inlineValidating[schema.id]"
                  @click="validateSchemaInline(schema.id)"
                >
                  <RefreshCw v-if="inlineValidating[schema.id]" :size="14" class="spin-icon" />
                  <CheckCircle v-else :size="14" />
                </button>
                <!-- Générer SQL inline -->
                <button
                  class="icon-btn icon-btn--sql"
                  :title="inlineSqlOpen[schema.id] ? 'Masquer SQL' : 'Générer SQL'"
                  :disabled="inlineSqlLoading[schema.id]"
                  @click="generateSqlInline(schema.id)"
                >
                  <RefreshCw v-if="inlineSqlLoading[schema.id]" :size="14" class="spin-icon" />
                  <Code2 v-else :size="14" />
                </button>
                <!-- Vider cache inline -->
                <button
                  class="icon-btn"
                  :title="inlineCacheLoading[schema.id] ? 'Nettoyage…' : 'Vider le cache'"
                  :disabled="inlineCacheLoading[schema.id]"
                  @click.stop="clearCacheInline(schema.id)"
                >
                  <RefreshCw v-if="inlineCacheLoading[schema.id]" :size="14" class="spin-icon" />
                  <Archive v-else :size="14" />
                </button>
                <!-- Exécuter (ouvre panneau) -->
                <button
                  class="icon-btn icon-btn--execute"
                  title="Exécuter"
                  @click="selectSchema(schema); detailTab = 'execute'; executeSchema()"
                >
                  <Play :size="14" />
                </button>
                <button
                  class="icon-btn"
                  title="Modifier"
                  @click="openEditSchema(schema)"
                >
                  <Edit :size="14" />
                </button>
                <button
                  class="icon-btn icon-btn--danger"
                  title="Supprimer"
                  @click="confirmDeleteSchema(schema)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>

              <!-- Résultat validation inline -->
              <div
                v-if="inlineValidResult[schema.id]"
                class="inline-result"
                :class="inlineValidResult[schema.id]?.error || inlineValidResult[schema.id]?.is_valid === false
                  ? 'inline-result--error'
                  : 'inline-result--success'"
                @click.stop
              >
                <span v-if="inlineValidResult[schema.id]?.error" class="inline-result-text">
                  {{ inlineValidResult[schema.id]?.error }}
                </span>
                <template v-else>
                  <span class="inline-result-text">
                    {{ inlineValidResult[schema.id]?.is_valid ? 'Schéma valide' : 'Schéma invalide' }}
                  </span>
                  <ul
                    v-if="Array.isArray(inlineValidResult[schema.id]?.errors) && inlineValidResult[schema.id]!.errors!.length"
                    class="inline-errors"
                  >
                    <li v-for="(err, i) in inlineValidResult[schema.id]!.errors" :key="i">{{ err }}</li>
                  </ul>
                </template>
              </div>

              <!-- Résultat cache inline -->
              <div v-if="inlineCacheMsg[schema.id]" class="inline-cache-msg" @click.stop>
                {{ inlineCacheMsg[schema.id] }}
              </div>

              <!-- SQL inline block -->
              <div v-if="inlineSqlOpen[schema.id]" class="inline-sql-wrap" @click.stop>
                <div v-if="inlineSqlLoading[schema.id]" class="panel-loading">
                  <RefreshCw :size="14" class="spin-icon" />
                  <span>Génération SQL…</span>
                </div>
                <template v-else-if="inlineSqlResult[schema.id]">
                  <div class="inline-sql-toolbar">
                    <span class="inline-sql-label">SQL généré</span>
                    <button class="btn-secondary" style="font-size:0.68rem; padding:3px 10px;" @click="copySqlInline(schema.id)">
                      <Copy :size="11" />
                      {{ inlineSqlCopied[schema.id] ? 'Copié !' : 'Copier' }}
                    </button>
                    <button class="icon-btn" style="width:22px;height:22px;" title="Fermer" @click="inlineSqlOpen[schema.id] = false">
                      <X :size="12" />
                    </button>
                  </div>
                  <pre class="sql-block sql-block--compact">{{ inlineSqlResult[schema.id] }}</pre>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Detail panel -->
        <Transition name="panel">
          <aside v-if="selectedSchema" class="detail-panel">

            <!-- Panel header -->
            <div class="panel-header">
              <div class="panel-title-row">
                <span class="panel-name">{{ selectedSchema.name }}</span>
                <button class="panel-close" @click="selectedSchema = null" aria-label="Fermer">
                  <X :size="16" />
                </button>
              </div>
              <div class="panel-badges">
                <span class="type-badge" :class="schemaTypeColor(selectedSchema.schema_type)">
                  {{ selectedSchema.schema_type_display || selectedSchema.schema_type }}
                </span>
                <span class="status-badge" :class="statusColor(selectedSchema.status)">
                  {{ selectedSchema.status_display || selectedSchema.status }}
                </span>
                <span class="meta-chip">
                  <Star :size="10" />
                  {{ selectedSchema.grain_display || selectedSchema.grain }}
                </span>
              </div>
              <p v-if="selectedSchema.description" class="panel-desc">{{ selectedSchema.description }}</p>
            </div>

            <!-- Panel tabs -->
            <div class="panel-tabs">
              <button
                class="panel-tab"
                :class="{ 'panel-tab--active': detailTab === 'sql' }"
                @click="detailTab = 'sql'"
              >
                <Code2 :size="12" />
                SQL
              </button>
              <button
                class="panel-tab"
                :class="{ 'panel-tab--active': detailTab === 'validate' }"
                @click="detailTab = 'validate'"
              >
                <CheckCircle :size="12" />
                Valider
              </button>
              <button
                class="panel-tab"
                :class="{ 'panel-tab--active': detailTab === 'execute' }"
                @click="detailTab = 'execute'"
              >
                <Play :size="12" />
                Exécuter
              </button>
            </div>

            <!-- SQL tab -->
            <div v-if="detailTab === 'sql'" class="panel-body">
              <div class="panel-action-row">
                <button class="btn-secondary" :disabled="detailSqlLoading" @click="fetchSql">
                  <Code2 :size="13" />
                  {{ detailSqlLoading ? 'Chargement…' : 'Charger le SQL' }}
                </button>
                <button v-if="detailSql" class="btn-secondary" @click="copySql">
                  <Copy :size="13" />
                  {{ copiedSql ? 'Copié !' : 'Copier' }}
                </button>
              </div>
              <div v-if="detailSqlLoading" class="panel-loading">
                <RefreshCw :size="16" class="spin-icon" />
                <span>Génération du SQL…</span>
              </div>
              <pre v-else-if="detailSql" class="sql-block">{{ detailSql }}</pre>
              <p v-else class="panel-hint">Cliquez sur « Charger le SQL » pour générer la requête.</p>
            </div>

            <!-- Validate tab -->
            <div v-if="detailTab === 'validate'" class="panel-body">
              <div class="panel-action-row">
                <button class="btn-secondary" :disabled="detailValidateLoading" @click="validateSchema">
                  <CheckCircle :size="13" />
                  {{ detailValidateLoading ? 'Validation…' : 'Valider le schéma' }}
                </button>
              </div>
              <div v-if="detailValidateLoading" class="panel-loading">
                <RefreshCw :size="16" class="spin-icon" />
                <span>Validation en cours…</span>
              </div>
              <div
                v-else-if="detailValidateResult"
                class="result-block"
                :class="detailValidateResult.error ? 'result-block--error' : 'result-block--success'"
              >
                <pre>{{ JSON.stringify(detailValidateResult, null, 2) }}</pre>
              </div>
              <p v-else class="panel-hint">Cliquez sur « Valider le schéma » pour lancer la validation.</p>
            </div>

            <!-- Execute tab -->
            <div v-if="detailTab === 'execute'" class="panel-body">
              <div class="panel-action-row">
                <button class="btn-secondary" :disabled="detailExecuteLoading" @click="executeSchema">
                  <Play :size="13" />
                  {{ detailExecuteLoading ? 'Exécution…' : 'Exécuter le schéma' }}
                </button>
                <button
                  class="btn-secondary"
                  :disabled="detailCacheLoading"
                  @click="clearCache"
                >
                  <Archive :size="13" />
                  {{ detailCacheLoading ? 'En cours…' : 'Vider le cache' }}
                </button>
              </div>
              <p v-if="detailCacheMsg" class="cache-msg">{{ detailCacheMsg }}</p>
              <div v-if="detailExecuteLoading" class="panel-loading">
                <RefreshCw :size="16" class="spin-icon" />
                <span>Exécution en cours…</span>
              </div>
              <div
                v-else-if="detailExecuteResult"
                class="result-block"
                :class="detailExecuteResult.error ? 'result-block--error' : 'result-block--success'"
              >
                <pre>{{ JSON.stringify(detailExecuteResult, null, 2) }}</pre>
              </div>
              <p v-else class="panel-hint">Cliquez sur « Exécuter le schéma » pour lancer l'exécution.</p>
            </div>

          </aside>
        </Transition>

      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 2: GALAXIES                                                      -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <div v-else-if="activeTab === 'galaxies'" class="tab-body">

      <div class="toolbar">
        <span class="toolbar-spacer"></span>
        <button class="btn-primary" @click="openCreateGalaxy">
          <Plus :size="14" />
          Nouvelle galaxie
        </button>
      </div>

      <div v-if="galaxiesLoading" class="skel-grid">
        <div v-for="i in 4" :key="i" class="skel-card"></div>
      </div>

      <div v-else-if="galaxies.length === 0" class="empty-state">
        <Network :size="36" class="empty-icon" />
        <p>Aucune galaxie trouvée</p>
      </div>

      <div v-else class="card-grid card-grid--wide">
        <div v-for="g in galaxies" :key="g.id" class="schema-card">

          <div class="card-head">
            <span class="card-name">{{ g.name }}</span>
            <span class="status-badge" :class="statusColor(g.status)">
              {{ g.status_display || g.status }}
            </span>
          </div>

          <div class="card-meta-row">
            <span class="meta-chip">
              <Layers :size="10" />
              {{ g.dimensional_schema_count }} schéma(s)
            </span>
            <span v-if="g.owner_name" class="meta-chip meta-chip--muted">{{ g.owner_name }}</span>
          </div>

          <p v-if="g.description" class="card-desc">{{ g.description }}</p>

          <!-- Galaxy SQL panel -->
          <div v-if="showGalaxySqlPanel === g.id" class="galaxy-sql-panel">
            <div v-if="galaxySqlLoading[g.id]" class="panel-loading">
              <RefreshCw :size="14" class="spin-icon" />
              <span>Chargement…</span>
            </div>
            <pre v-else class="sql-block sql-block--compact">{{ galaxySqlMap[g.id] }}</pre>
          </div>

          <!-- Galaxy exec result -->
          <div
            v-if="galaxyExecResult[g.id]"
            class="result-block result-block--compact"
            :class="galaxyExecResult[g.id]?.error ? 'result-block--error' : 'result-block--success'"
          >
            <pre>{{ JSON.stringify(galaxyExecResult[g.id], null, 2) }}</pre>
          </div>

          <div class="card-actions" style="margin-top: auto; padding-top: var(--sp-2);">
            <button
              class="icon-btn icon-btn--execute"
              title="Exécuter (unifié)"
              :disabled="galaxyExecLoading[g.id]"
              @click="executeGalaxyUnified(g)"
            >
              <RefreshCw v-if="galaxyExecLoading[g.id]" :size="14" class="spin-icon" />
              <Play v-else :size="14" />
            </button>
            <button
              class="icon-btn icon-btn--sql"
              title="SQL unifié"
              @click="fetchGalaxyUnifiedSql(g)"
            >
              <Code2 :size="14" />
            </button>
            <button class="icon-btn" title="Modifier" @click="openEditGalaxy(g)">
              <Edit :size="14" />
            </button>
            <button class="icon-btn icon-btn--danger" title="Supprimer" @click="confirmDeleteGalaxy(g)">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 3: CALCULATIONS                                                  -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <div v-else-if="activeTab === 'calculations'" class="tab-body">

      <div class="toolbar">
        <span class="toolbar-spacer"></span>
        <button class="btn-primary" @click="openCreateCalc">
          <Plus :size="14" />
          Nouveau calcul
        </button>
      </div>

      <!-- Inline form -->
      <Transition name="slide-down">
        <div v-if="showCalcForm" class="inline-form">
          <h4 class="inline-form-title">
            {{ calcFormMode === 'create' ? 'Nouveau calcul' : 'Modifier le calcul' }}
          </h4>
          <div class="form-grid">
            <label class="form-field">
              <span class="form-label">Nom <span class="required">*</span></span>
              <input v-model="calcForm.name" type="text" class="form-input" placeholder="Nom du calcul" />
            </label>
            <label class="form-field">
              <span class="form-label">Type</span>
              <input v-model="calcForm.type" type="text" class="form-input" placeholder="ex: kpi, metric…" />
            </label>
            <label class="form-field form-field--full">
              <span class="form-label">Formule</span>
              <input v-model="calcForm.formula" type="text" class="form-input" placeholder="ex: SUM(revenue) / COUNT(*)" />
            </label>
            <label class="form-field">
              <span class="form-label">Statut</span>
              <input v-model="calcForm.status" type="text" class="form-input" placeholder="ex: active" />
            </label>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" @click="showCalcForm = false">Annuler</button>
            <button class="btn-primary" :disabled="calcFormLoading" @click="saveCalc">
              {{ calcFormLoading ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
          </div>
        </div>
      </Transition>

      <div v-if="calculationsLoading" class="table-skel">
        <div v-for="i in 5" :key="i" class="table-skel-row"></div>
      </div>

      <div v-else-if="calculations.length === 0 && !showCalcForm" class="empty-state">
        <Calculator :size="36" class="empty-icon" />
        <p>Aucun calcul défini</p>
      </div>

      <div v-else-if="calculations.length > 0" class="data-table-wrap">
        <table class="data-table" aria-label="Calculs">
          <thead>
            <tr>
              <th class="dt-th">Nom</th>
              <th class="dt-th">Formule</th>
              <th class="dt-th">Type</th>
              <th class="dt-th">Statut</th>
              <th class="dt-th dt-th--actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in calculations" :key="c.id" class="dt-row">
              <td class="dt-td dt-td--name">{{ c.name }}</td>
              <td class="dt-td dt-td--formula">{{ c.formula || '—' }}</td>
              <td class="dt-td">
                <span v-if="c.type" class="meta-chip">{{ c.type }}</span>
                <span v-else class="dash">—</span>
              </td>
              <td class="dt-td">
                <span v-if="c.status" class="status-badge" :class="statusColor(c.status as SchemaStatus)">
                  {{ c.status }}
                </span>
                <span v-else class="dash">—</span>
              </td>
              <td class="dt-td dt-td--actions">
                <button class="icon-btn" title="Modifier" @click="openEditCalc(c)">
                  <Edit :size="13" />
                </button>
                <button class="icon-btn icon-btn--danger" title="Supprimer" @click="confirmDeleteCalc(c)">
                  <Trash2 :size="13" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 4: HIERARCHIES                                                   -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <div v-else-if="activeTab === 'hierarchies'" class="tab-body">

      <div class="toolbar">
        <span class="toolbar-spacer"></span>
        <button class="btn-primary" @click="openCreateHierarchy">
          <Plus :size="14" />
          Nouvelle hiérarchie
        </button>
      </div>

      <!-- Inline form -->
      <Transition name="slide-down">
        <div v-if="showHierarchyForm" class="inline-form">
          <h4 class="inline-form-title">
            {{ hierarchyFormMode === 'create' ? 'Nouvelle hiérarchie' : 'Modifier la hiérarchie' }}
          </h4>
          <div class="form-grid">
            <label class="form-field">
              <span class="form-label">Nom <span class="required">*</span></span>
              <input v-model="hierarchyForm.name" type="text" class="form-input" placeholder="Nom de la hiérarchie" />
            </label>
            <label class="form-field">
              <span class="form-label">Table dimension</span>
              <input v-model="hierarchyForm.dimension_table" type="text" class="form-input" placeholder="UUID de la table dimension" />
            </label>
            <label class="form-field form-field--full">
              <span class="form-label">Niveaux (séparés par virgule)</span>
              <input v-model="hierarchyForm.levels" type="text" class="form-input" placeholder="ex: année, trimestre, mois" />
            </label>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" @click="showHierarchyForm = false">Annuler</button>
            <button class="btn-primary" :disabled="hierarchyFormLoading" @click="saveHierarchy">
              {{ hierarchyFormLoading ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
          </div>
        </div>
      </Transition>

      <div v-if="hierarchiesLoading" class="table-skel">
        <div v-for="i in 5" :key="i" class="table-skel-row"></div>
      </div>

      <div v-else-if="hierarchies.length === 0 && !showHierarchyForm" class="empty-state">
        <GitMerge :size="36" class="empty-icon" />
        <p>Aucune hiérarchie définie</p>
      </div>

      <div v-else-if="hierarchies.length > 0" class="data-table-wrap">
        <table class="data-table" aria-label="Hiérarchies de dimensions">
          <thead>
            <tr>
              <th class="dt-th">Nom</th>
              <th class="dt-th">Table dimension</th>
              <th class="dt-th">Niveaux</th>
              <th class="dt-th dt-th--actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in hierarchies" :key="h.id" class="dt-row">
              <td class="dt-td dt-td--name">{{ h.name }}</td>
              <td class="dt-td dt-td--formula">{{ h.dimension_table || '—' }}</td>
              <td class="dt-td">
                <span v-if="Array.isArray(h.levels) && h.levels.length">
                  <span
                    v-for="(lvl, i) in h.levels"
                    :key="i"
                    class="meta-chip"
                    style="margin-right: 4px;"
                  >{{ lvl }}</span>
                </span>
                <span v-else class="dash">—</span>
              </td>
              <td class="dt-td dt-td--actions">
                <button class="icon-btn" title="Modifier" @click="openEditHierarchy(h)">
                  <Edit :size="13" />
                </button>
                <button class="icon-btn icon-btn--danger" title="Supprimer" @click="confirmDeleteHierarchy(h)">
                  <Trash2 :size="13" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- TAB 5: FACT RELATIONSHIPS                                            -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <div v-else-if="activeTab === 'relations'" class="tab-body">

      <div class="toolbar">
        <button class="btn-primary" @click="() => { factRelFormMode = 'create'; editingFactRelId = null; factRelForm = { name: '', description: '', from_fact: '', to_fact: '', from_column: '', to_column: '', relation_type: 'direct', join_type: 'inner', is_enabled: true }; showFactRelForm = true }">
          <Plus :size="14" />
          Nouvelle relation
        </button>
        <button class="btn-secondary" @click="fetchFactRels">
          <RefreshCw :size="13" />
          Actualiser
        </button>
      </div>

      <!-- Inline form -->
      <Transition name="slide-down">
        <div v-if="showFactRelForm" class="inline-form">
          <h4 class="inline-form-title">{{ factRelFormMode === 'create' ? 'Nouvelle relation fait-fait' : 'Modifier la relation' }}</h4>
          <div class="form-grid">
            <label class="form-field form-field--full">
              <span class="form-label">Nom *</span>
              <input v-model="factRelForm.name" type="text" class="form-input" placeholder="Nom de la relation" />
            </label>
            <label class="form-field form-field--full">
              <span class="form-label">Description</span>
              <input v-model="factRelForm.description" type="text" class="form-input" placeholder="Description optionnelle" />
            </label>
            <label class="form-field">
              <span class="form-label">Table fait source (UUID)</span>
              <input v-model="factRelForm.from_fact" type="text" class="form-input" placeholder="UUID de la table source" />
            </label>
            <label class="form-field">
              <span class="form-label">Table fait cible (UUID)</span>
              <input v-model="factRelForm.to_fact" type="text" class="form-input" placeholder="UUID de la table cible" />
            </label>
            <label class="form-field">
              <span class="form-label">Colonne source</span>
              <input v-model="factRelForm.from_column" type="text" class="form-input" placeholder="colonne_id" />
            </label>
            <label class="form-field">
              <span class="form-label">Colonne cible</span>
              <input v-model="factRelForm.to_column" type="text" class="form-input" placeholder="colonne_id" />
            </label>
            <label class="form-field">
              <span class="form-label">Type de relation</span>
              <select v-model="factRelForm.relation_type" class="form-select">
                <option value="direct">Direct</option>
                <option value="indirect">Indirect</option>
              </select>
            </label>
            <label class="form-field">
              <span class="form-label">Type de jointure</span>
              <select v-model="factRelForm.join_type" class="form-select">
                <option value="inner">INNER JOIN</option>
                <option value="left">LEFT JOIN</option>
                <option value="right">RIGHT JOIN</option>
                <option value="full">FULL JOIN</option>
              </select>
            </label>
            <label class="form-field form-field--full toggle-label">
              <input type="checkbox" v-model="factRelForm.is_enabled" class="form-checkbox" />
              Relation active
            </label>
          </div>
          <div class="form-actions">
            <button class="btn-ghost" @click="showFactRelForm = false">Annuler</button>
            <button class="btn-primary" :disabled="factRelFormLoading" @click="saveFactRel">
              {{ factRelFormLoading ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
          </div>
        </div>
      </Transition>

      <div v-if="factRelsLoading" class="table-skel">
        <div v-for="i in 5" :key="i" class="table-skel-row"></div>
      </div>

      <div v-else-if="factRels.length === 0 && !showFactRelForm" class="empty-state">
        <GitMerge :size="36" class="empty-icon" />
        <p>Aucune relation fait-fait définie</p>
      </div>

      <div v-else-if="factRels.length > 0" class="data-table-wrap">
        <table class="data-table" aria-label="Relations fait-fait">
          <thead>
            <tr>
              <th class="dt-th">Nom</th>
              <th class="dt-th">Type relation</th>
              <th class="dt-th">Jointure</th>
              <th class="dt-th">Colonnes</th>
              <th class="dt-th">Statut</th>
              <th class="dt-th dt-th--actions"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rel in factRels" :key="rel.id" class="dt-row">
              <td class="dt-td dt-td--name">{{ rel.name }}</td>
              <td class="dt-td">
                <span class="meta-chip">{{ rel.relation_type || '—' }}</span>
              </td>
              <td class="dt-td">
                <span class="meta-chip">{{ rel.join_type?.toUpperCase() || '—' }}</span>
              </td>
              <td class="dt-td dt-td--formula">
                {{ rel.from_column || '—' }} → {{ rel.to_column || '—' }}
              </td>
              <td class="dt-td">
                <span :class="rel.is_enabled ? 'status-badge status--active' : 'status-badge status--draft'">
                  <span class="status-dot"></span>
                  {{ rel.is_enabled ? 'Actif' : 'Inactif' }}
                </span>
              </td>
              <td class="dt-td dt-td--actions">
                <button class="icon-btn" title="Modifier" @click="openEditFactRel(rel)">
                  <Edit :size="13" />
                </button>
                <button class="icon-btn icon-btn--danger" title="Supprimer" @click="confirmDeleteFactRel(rel)">
                  <Trash2 :size="13" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- MODAL: Create / Edit Schema                                          -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <Transition name="dialog">
      <div v-if="showSchemaModal" class="dialog-overlay" @click.self="showSchemaModal = false">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="schema-modal-title">

          <div class="dialog-header">
            <h3 id="schema-modal-title" class="dialog-title">
              {{ schemaModalMode === 'create' ? 'Nouveau schéma' : 'Modifier le schéma' }}
            </h3>
            <button class="dialog-close" @click="showSchemaModal = false" aria-label="Fermer">
              <X :size="16" />
            </button>
          </div>

          <div class="dialog-body-form">
            <div class="form-grid">
              <label class="form-field form-field--full">
                <span class="form-label">Nom <span class="required">*</span></span>
                <input v-model="schemaForm.name" type="text" class="form-input" placeholder="Nom du schéma" />
              </label>

              <label class="form-field form-field--full">
                <span class="form-label">Description</span>
                <textarea v-model="schemaForm.description" class="form-textarea" rows="2" placeholder="Description du schéma…"></textarea>
              </label>

              <label class="form-field">
                <span class="form-label">Type</span>
                <select v-model="schemaForm.schema_type" class="form-select">
                  <option value="star">Étoile (star)</option>
                  <option value="snowflake">Flocon (snowflake)</option>
                  <option value="galaxy">Galaxie (galaxy)</option>
                  <option value="constellation">Constellation</option>
                </select>
              </label>

              <label class="form-field">
                <span class="form-label">Statut</span>
                <select v-model="schemaForm.status" class="form-select">
                  <option value="draft">Brouillon</option>
                  <option value="active">Actif</option>
                  <option value="archived">Archivé</option>
                  <option value="deprecated">Déprécié</option>
                </select>
              </label>

              <label class="form-field">
                <span class="form-label">Grain</span>
                <select v-model="schemaForm.grain" class="form-select">
                  <option value="transaction">Transaction</option>
                  <option value="daily">Quotidien</option>
                  <option value="weekly">Hebdomadaire</option>
                  <option value="monthly">Mensuel</option>
                  <option value="quarterly">Trimestriel</option>
                  <option value="yearly">Annuel</option>
                </select>
              </label>

              <label class="form-field">
                <span class="form-label">Version</span>
                <input v-model="schemaForm.version" type="text" class="form-input" placeholder="ex: 1.0.0" />
              </label>

              <label class="form-field">
                <span class="form-label">Catégorie</span>
                <input v-model="schemaForm.category" type="text" class="form-input" placeholder="ex: Finance" />
              </label>

              <label class="form-field">
                <span class="form-label">Domaine métier</span>
                <input v-model="schemaForm.business_domain" type="text" class="form-input" placeholder="ex: Ventes" />
              </label>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-ghost" @click="showSchemaModal = false">Annuler</button>
            <button
              class="btn-primary"
              :disabled="schemaModalLoading || !schemaForm.name.trim()"
              @click="saveSchema"
            >
              {{ schemaModalLoading ? 'Enregistrement…' : (schemaModalMode === 'create' ? 'Créer' : 'Enregistrer') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- MODAL: Create / Edit Galaxy                                          -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <Transition name="dialog">
      <div v-if="showGalaxyModal" class="dialog-overlay" @click.self="showGalaxyModal = false">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="galaxy-modal-title">

          <div class="dialog-header">
            <h3 id="galaxy-modal-title" class="dialog-title">
              {{ galaxyModalMode === 'create' ? 'Nouvelle galaxie' : 'Modifier la galaxie' }}
            </h3>
            <button class="dialog-close" @click="showGalaxyModal = false" aria-label="Fermer">
              <X :size="16" />
            </button>
          </div>

          <div class="dialog-body-form">
            <div class="form-grid">
              <label class="form-field form-field--full">
                <span class="form-label">Nom <span class="required">*</span></span>
                <input v-model="galaxyForm.name" type="text" class="form-input" placeholder="Nom de la galaxie" />
              </label>

              <label class="form-field form-field--full">
                <span class="form-label">Description</span>
                <textarea v-model="galaxyForm.description" class="form-textarea" rows="2" placeholder="Description…"></textarea>
              </label>

              <label class="form-field">
                <span class="form-label">Statut</span>
                <select v-model="galaxyForm.status" class="form-select">
                  <option value="draft">Brouillon</option>
                  <option value="active">Actif</option>
                  <option value="archived">Archivé</option>
                  <option value="deprecated">Déprécié</option>
                </select>
              </label>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-ghost" @click="showGalaxyModal = false">Annuler</button>
            <button
              class="btn-primary"
              :disabled="galaxyModalLoading || !galaxyForm.name.trim()"
              @click="saveGalaxy"
            >
              {{ galaxyModalLoading ? 'Enregistrement…' : (galaxyModalMode === 'create' ? 'Créer' : 'Enregistrer') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- CONFIRM DELETE MODALS                                                -->
    <!-- ════════════════════════════════════════════════════════════════════ -->

    <!-- Delete Schema -->
    <Transition name="dialog">
      <div v-if="showDeleteSchemaConfirm" class="dialog-overlay" @click.self="showDeleteSchemaConfirm = false">
        <div class="dialog dialog--sm" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <h3 class="dialog-title">Supprimer le schéma</h3>
            <button class="dialog-close" @click="showDeleteSchemaConfirm = false"><X :size="16" /></button>
          </div>
          <p class="dialog-confirm-body">
            Êtes-vous sûr de vouloir supprimer <strong>{{ deletingSchema?.name }}</strong>&nbsp;? Cette action est irréversible.
          </p>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showDeleteSchemaConfirm = false">Annuler</button>
            <button class="btn-danger" :disabled="deleteSchemaLoading" @click="doDeleteSchema">
              {{ deleteSchemaLoading ? 'Suppression…' : 'Supprimer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Galaxy -->
    <Transition name="dialog">
      <div v-if="showDeleteGalaxyConfirm" class="dialog-overlay" @click.self="showDeleteGalaxyConfirm = false">
        <div class="dialog dialog--sm" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <h3 class="dialog-title">Supprimer la galaxie</h3>
            <button class="dialog-close" @click="showDeleteGalaxyConfirm = false"><X :size="16" /></button>
          </div>
          <p class="dialog-confirm-body">
            Êtes-vous sûr de vouloir supprimer <strong>{{ deletingGalaxy?.name }}</strong>&nbsp;?
          </p>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showDeleteGalaxyConfirm = false">Annuler</button>
            <button class="btn-danger" :disabled="deleteGalaxyLoading" @click="doDeleteGalaxy">
              {{ deleteGalaxyLoading ? 'Suppression…' : 'Supprimer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Calculation -->
    <Transition name="dialog">
      <div v-if="showDeleteCalcConfirm" class="dialog-overlay" @click.self="showDeleteCalcConfirm = false">
        <div class="dialog dialog--sm" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <h3 class="dialog-title">Supprimer le calcul</h3>
            <button class="dialog-close" @click="showDeleteCalcConfirm = false"><X :size="16" /></button>
          </div>
          <p class="dialog-confirm-body">
            Êtes-vous sûr de vouloir supprimer <strong>{{ deletingCalc?.name }}</strong>&nbsp;?
          </p>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showDeleteCalcConfirm = false">Annuler</button>
            <button class="btn-danger" :disabled="deleteCalcLoading" @click="doDeleteCalc">
              {{ deleteCalcLoading ? 'Suppression…' : 'Supprimer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete Hierarchy -->
    <Transition name="dialog">
      <div v-if="showDeleteHierarchyConfirm" class="dialog-overlay" @click.self="showDeleteHierarchyConfirm = false">
        <div class="dialog dialog--sm" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <h3 class="dialog-title">Supprimer la hiérarchie</h3>
            <button class="dialog-close" @click="showDeleteHierarchyConfirm = false"><X :size="16" /></button>
          </div>
          <p class="dialog-confirm-body">
            Êtes-vous sûr de vouloir supprimer <strong>{{ deletingHierarchy?.name }}</strong>&nbsp;?
          </p>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showDeleteHierarchyConfirm = false">Annuler</button>
            <button class="btn-danger" :disabled="deleteHierarchyLoading" @click="doDeleteHierarchy">
              {{ deleteHierarchyLoading ? 'Suppression…' : 'Supprimer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Delete FactRelationship -->
    <Transition name="dialog">
      <div v-if="showDeleteFactRelConfirm" class="dialog-overlay" @click.self="showDeleteFactRelConfirm = false">
        <div class="dialog dialog--sm" role="dialog" aria-modal="true">
          <div class="dialog-header">
            <h3 class="dialog-title">Supprimer la relation</h3>
            <button class="dialog-close" @click="showDeleteFactRelConfirm = false"><X :size="16" /></button>
          </div>
          <p class="dialog-confirm-body">
            Êtes-vous sûr de vouloir supprimer <strong>{{ deletingFactRel?.name }}</strong>&nbsp;?
          </p>
          <div class="dialog-footer">
            <button class="btn-ghost" @click="showDeleteFactRelConfirm = false">Annuler</button>
            <button class="btn-danger" :disabled="deleteFactRelLoading" @click="doDeleteFactRel">
              {{ deleteFactRelLoading ? 'Suppression…' : 'Supprimer' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* ── Keyframes ─────────────────────────────────────────────────────────────── */
@keyframes spin     { to { transform: rotate(360deg); } }
@keyframes shimmer  {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.spin-icon { animation: spin 0.8s linear infinite; flex-shrink: 0; }

/* ── Root ──────────────────────────────────────────────────────────────────── */
.ss {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  height: 100%;
  min-height: 0;
}

/* ── Page header ───────────────────────────────────────────────────────────── */
.ss-header {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  flex-shrink: 0;
}

.ss-title-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.ss-title-icon { color: var(--accent); flex-shrink: 0; }

.ss-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}

/* ── Stats strip ───────────────────────────────────────────────────────────── */
.stats-strip {
  display: flex;
  align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-6);
  flex: 1;
}

.stat-sep {
  width: 1px;
  height: 32px;
  background: var(--border-subtle);
  flex-shrink: 0;
}

.stat-val {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.stat-val--green { color: var(--success); }
.stat-val--blue  { color: var(--info); }

.stat-lbl {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
}

/* ── Tab bar ───────────────────────────────────────────────────────────────── */
.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  gap: 0;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-5);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
  transition: color 150ms, border-color 150ms, background 150ms;
  white-space: nowrap;
  margin-bottom: -1px;
}
.tab-btn:hover { color: var(--text-primary); background: var(--surface-overlay); }
.tab-btn--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* ── Tab body ──────────────────────────────────────────────────────────────── */
.tab-body {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ── Toolbar ───────────────────────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.toolbar-spacer { flex: 1; }

/* ── Search ────────────────────────────────────────────────────────────────── */
.search-wrap {
  position: relative;
  flex: 1;
  min-width: 180px;
  max-width: 320px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 12px 8px 32px;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-primary);
  outline: none;
  transition: border-color 150ms;
}
.search-input::placeholder { color: var(--text-muted); }
.search-input:focus { border-color: var(--accent); }

/* ── Filter select ─────────────────────────────────────────────────────────── */
.filter-select {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms;
}
.filter-select:focus { border-color: var(--accent); }

/* ── Buttons ───────────────────────────────────────────────────────────────── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 150ms;
}
.btn-primary:hover:not(:disabled) { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 6px 14px;
  background: none;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: background 150ms, border-color 150ms, color 150ms;
}
.btn-secondary:hover:not(:disabled) {
  background: var(--accent-surface);
  border-color: var(--accent);
  color: var(--accent);
}
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 16px;
  background: none;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 150ms, color 150ms;
}
.btn-ghost:hover { background: var(--surface-overlay); color: var(--text-primary); }

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 16px;
  background: oklch(14% 0.05 0);
  border: 1px solid oklch(30% 0.10 0);
  color: var(--error);
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms;
}
.btn-danger:hover:not(:disabled) { background: oklch(18% 0.06 0); }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Icon buttons ──────────────────────────────────────────────────────────── */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 100ms, color 100ms;
}
.icon-btn:hover:not(:disabled) { background: var(--surface-muted); color: var(--text-primary); }
.icon-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.icon-btn--validate:hover:not(:disabled) { color: var(--success); background: oklch(14% 0.04 148); }
.icon-btn--sql:hover:not(:disabled)      { color: var(--info);    background: oklch(14% 0.04 220); }
.icon-btn--execute:hover:not(:disabled)  { color: var(--accent);  background: var(--accent-surface); }
.icon-btn--danger:hover:not(:disabled)   { color: var(--error);   background: oklch(14% 0.05 0); }

/* ── Skeleton ──────────────────────────────────────────────────────────────── */
.skel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sp-4);
}

.skel-card {
  height: 180px;
  border-radius: var(--radius-lg);
  background: linear-gradient(
    90deg,
    var(--surface-overlay) 25%,
    var(--surface-muted)   50%,
    var(--surface-overlay) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* ── Schemas layout ────────────────────────────────────────────────────────── */
.schemas-layout {
  display: flex;
  gap: var(--sp-4);
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.card-grid-wrap {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* ── Card grid ─────────────────────────────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--sp-4);
  align-content: start;
}

.card-grid--wide {
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
}

/* ── Schema card ───────────────────────────────────────────────────────────── */
.schema-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  cursor: pointer;
  transition: border-color 150ms, box-shadow 150ms, background 150ms;
  outline: none;
}
.schema-card:hover {
  border-color: var(--border-default);
  box-shadow: 0 4px 20px oklch(0% 0 0 / 0.15);
}
.schema-card:focus-visible {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-surface);
}
.schema-card--selected {
  border-color: var(--accent);
  background: var(--accent-surface);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-2);
}

.card-name {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-badges {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.card-meta-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.card-owner-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.owner-txt {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
}

.version-txt {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-family: 'Barlow Condensed', monospace;
  background: var(--surface-muted);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}

.query-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-left: auto;
}

.card-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  margin-top: auto;
  padding-top: var(--sp-2);
  border-top: 1px solid var(--border-subtle);
}

/* ── Type badges ───────────────────────────────────────────────────────────── */
.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.type--star         { background: var(--accent-surface);          color: var(--accent);   border: 1px solid var(--accent-deep, var(--accent)); }
.type--snowflake    { background: oklch(14% 0.05 220);             color: var(--info);     border: 1px solid oklch(30% 0.08 220); }
.type--galaxy       { background: oklch(14% 0.06 310);             color: #a855f7;         border: 1px solid oklch(30% 0.10 310); }
.type--constellation{ background: oklch(17% 0.05 80);              color: var(--warning);  border: 1px solid oklch(35% 0.10 80); }

/* ── Status badges ─────────────────────────────────────────────────────────── */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
}

.status--draft      { color: var(--text-muted);      background: var(--surface-muted);         border: 1px solid var(--border-subtle); }
.status--active     { color: var(--success);          background: oklch(14% 0.04 148);          border: 1px solid oklch(28% 0.08 148); }
.status--archived   { color: var(--text-secondary);   background: var(--surface-overlay);       border: 1px solid var(--border-default); }
.status--deprecated { color: var(--warning);          background: oklch(17% 0.05 80);           border: 1px solid oklch(35% 0.10 80); }

/* ── Meta chips ────────────────────────────────────────────────────────────── */
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}
.meta-chip--muted { color: var(--text-muted); }

/* ── Empty state ───────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  padding: var(--sp-16);
  color: var(--text-muted);
  font-size: var(--text-sm);
}
.empty-icon { color: var(--border-default); }

/* ── Detail panel ──────────────────────────────────────────────────────────── */
.detail-panel {
  width: 420px;
  flex-shrink: 0;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  flex-shrink: 0;
}

.panel-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-2);
}

.panel-name {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.panel-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 100ms, color 100ms;
}
.panel-close:hover { background: var(--surface-muted); color: var(--text-primary); }

.panel-badges {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.panel-desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Panel tabs */
.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  padding: 0 var(--sp-4);
}

.panel-tab {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-3);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  transition: color 150ms, border-color 150ms;
  white-space: nowrap;
  margin-bottom: -1px;
}
.panel-tab:hover { color: var(--text-primary); }
.panel-tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* Panel body */
.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.panel-action-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.panel-loading {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  font-size: var(--text-sm);
  color: var(--text-muted);
  padding: var(--sp-4) 0;
}

.panel-hint {
  font-size: var(--text-sm);
  color: var(--text-muted);
  padding: var(--sp-2) 0;
}

.sql-block {
  background: var(--surface-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-4);
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  overflow: auto;
  max-height: 400px;
  flex-shrink: 0;
}

.sql-block--compact {
  max-height: 200px;
  font-size: 0.7rem;
}

.result-block {
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  padding: var(--sp-3) var(--sp-4);
  flex-shrink: 0;
}
.result-block pre {
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-xs);
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
.result-block--success { background: oklch(11% 0.03 148); border-color: oklch(25% 0.07 148); }
.result-block--success pre { color: oklch(65% 0.15 148); }
.result-block--error   { background: oklch(11% 0.04 0);   border-color: oklch(28% 0.08 0); }
.result-block--error pre  { color: var(--error); }
.result-block--compact { max-height: 160px; overflow: auto; }

.cache-msg {
  font-size: var(--text-xs);
  color: var(--success);
  font-weight: 500;
}

/* Panel slide transition */
.panel-enter-active { transition: opacity 200ms, transform 200ms; }
.panel-leave-active { transition: opacity 150ms, transform 150ms; }
.panel-enter-from   { opacity: 0; transform: translateX(20px); }
.panel-leave-to     { opacity: 0; transform: translateX(20px); }

/* ── Galaxy SQL panel ──────────────────────────────────────────────────────── */
.galaxy-sql-panel {
  margin-top: var(--sp-2);
}

/* ── Data table ────────────────────────────────────────────────────────────── */
.data-table-wrap {
  flex: 1;
  overflow: auto;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.dt-th {
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
.dt-th--actions { width: 80px; }

.dt-row {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;
}
.dt-row:last-child { border-bottom: none; }
.dt-row:hover { background: var(--surface-overlay); }

.dt-td {
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  vertical-align: middle;
}

.dt-td--name {
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-base);
  white-space: nowrap;
}

.dt-td--formula {
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-xs);
  color: var(--text-muted);
  max-width: 280px;
}

.dt-td--actions {
  white-space: nowrap;
}
.dt-td--actions .icon-btn { opacity: 0; }
.dt-row:hover .dt-td--actions .icon-btn { opacity: 1; }

.dash { color: var(--border-default); }

/* ── Table skeleton ────────────────────────────────────────────────────────── */
.table-skel {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4);
}

.table-skel-row {
  height: 40px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--surface-overlay) 25%,
    var(--surface-muted)   50%,
    var(--surface-overlay) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* ── Inline form ───────────────────────────────────────────────────────────── */
.inline-form {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  flex-shrink: 0;
}

.inline-form-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
}

/* ── Form grid ─────────────────────────────────────────────────────────────── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.form-field--full { grid-column: 1 / -1; }

.form-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.03em;
}

.required { color: var(--error); }

.form-input,
.form-select,
.form-textarea {
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-primary);
  outline: none;
  transition: border-color 150ms;
  width: 100%;
}
.form-input::placeholder,
.form-textarea::placeholder { color: var(--text-muted); }
.form-input:focus,
.form-select:focus,
.form-textarea:focus { border-color: var(--accent); }

.form-textarea { resize: vertical; min-height: 60px; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

/* ── Dialog ────────────────────────────────────────────────────────────────── */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0% 0 0 / 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
  padding: var(--sp-4);
}

.dialog {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px oklch(0% 0 0 / 0.5);
}

.dialog--sm { max-width: 400px; }

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-5) var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.dialog-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
}

.dialog-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 100ms, color 100ms;
}
.dialog-close:hover { background: var(--surface-muted); color: var(--text-primary); }

.dialog-body-form {
  padding: var(--sp-5) var(--sp-6);
  overflow-y: auto;
  flex: 1;
}

.dialog-confirm-body {
  padding: var(--sp-5) var(--sp-6);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-6);
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

/* Dialog transition */
.dialog-enter-active, .dialog-leave-active { transition: opacity 150ms, transform 150ms; }
.dialog-enter-from, .dialog-leave-to       { opacity: 0; transform: scale(0.96); }

/* Slide-down transition (inline forms) */
.slide-down-enter-active { transition: opacity 200ms, max-height 200ms ease-out; overflow: hidden; }
.slide-down-leave-active { transition: opacity 150ms, max-height 150ms ease-in;  overflow: hidden; }
.slide-down-enter-from   { opacity: 0; max-height: 0; }
.slide-down-enter-to     { opacity: 1; max-height: 600px; }
.slide-down-leave-from   { opacity: 1; max-height: 600px; }
.slide-down-leave-to     { opacity: 0; max-height: 0; }

/* ── Inline action results (per-card) ─────────────────────────────────────── */
.inline-result {
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  padding: var(--sp-2) var(--sp-3);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.5;
}
.inline-result--success {
  background: oklch(11% 0.03 148);
  border-color: oklch(25% 0.07 148);
  color: oklch(65% 0.15 148);
}
.inline-result--error {
  background: oklch(11% 0.04 0);
  border-color: oklch(28% 0.08 0);
  color: var(--error);
}
.inline-result-text { display: block; }
.inline-errors {
  margin: var(--sp-1) 0 0 var(--sp-3);
  padding: 0;
  list-style: disc;
  font-size: 0.68rem;
  opacity: 0.9;
}

.inline-cache-msg {
  font-size: var(--text-xs);
  color: var(--success);
  font-weight: 500;
  padding: var(--sp-1) 0;
}

.inline-sql-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.inline-sql-toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.inline-sql-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  flex: 1;
}

/* ── Responsive ────────────────────────────────────────────────────────────── */
@media (max-width: 1200px) {
  .detail-panel { width: 360px; }
}

@media (max-width: 1024px) {
  .schemas-layout { flex-direction: column; overflow: visible; }
  .detail-panel   { width: 100%; }
  .card-grid      { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
}

@media (max-width: 768px) {
  .ss           { padding: var(--sp-4); gap: var(--sp-4); }
  .form-grid    { grid-template-columns: 1fr; }
  .stats-strip  { flex-wrap: wrap; }
  .stat-sep     { display: none; }
  .stat-card    { flex: 1 1 40%; }
  .tab-btn      { padding: var(--sp-3) var(--sp-3); font-size: var(--text-xs); }
  .card-grid    { grid-template-columns: 1fr; }
}
</style>
