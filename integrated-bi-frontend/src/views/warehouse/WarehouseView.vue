<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Database, Table2, Hash, Type, Calendar, ToggleLeft,
  Key, Search, ChevronRight, ChevronDown, RefreshCcw,
  Copy, Check, Columns, Info, BarChart2, Loader2,
  CheckCircle2, AlertTriangle, Tag, Layers,
} from 'lucide-vue-next'
import api from '@/api/axios'

// ── Types ─────────────────────────────────────────────────
interface Column {
  name: string
  type: string
  nullable: boolean
  primary_key: boolean
  description?: string
}

interface TableDef {
  id?: string | number
  name: string
  row_count: number
  columns: Column[]
  last_updated?: string
  description?: string
}

interface Schema {
  name: string
  tables: TableDef[]
}

interface Measure {
  name: string
  data_type_display: string
  aggregation_type_display: string
  description?: string
  is_active: boolean
}

interface Attribute {
  name: string
  column: string
  data_type_display: string
  description?: string
  is_key: boolean
  is_hierarchical: boolean
  is_active: boolean
}

// ── Mapping helpers ───────────────────────────────────────
function mapColumns(rawCols: any): Column[] {
  if (!Array.isArray(rawCols)) return []
  return rawCols.map((c: any) => ({
    name:        c.name || c.column || '',
    type:        c.type || c.data_type || c.data_type_display || 'VARCHAR',
    nullable:    c.nullable ?? c.is_nullable ?? true,
    primary_key: c.primary_key ?? c.is_key ?? c.is_primary ?? false,
    description: c.description || undefined,
  }))
}

function mapDimTable(t: any): TableDef {
  return {
    id:           t.id ?? undefined,
    name:         t.name || '',
    row_count:    t.row_count ?? 0,
    columns:      mapColumns(t.columns),
    last_updated: t.last_refresh || t.updated_at || undefined,
    description:  t.description || undefined,
  }
}

// ── State ─────────────────────────────────────────────────
const schemas        = ref<Schema[]>([])
const loading        = ref(true)
const refreshing     = ref(false)
const expandedSchemas= ref<Set<string>>(new Set())
const selectedSchema = ref<string>('')
const selectedTable  = ref<TableDef | null>(null)
const searchQuery    = ref('')
const copiedCol      = ref<string | null>(null)
const lastUpdated    = ref(new Date())

// ── New state: left-panel tab ──────────────────────────────
const tableTypeTab      = ref<'dimensions' | 'facts'>('dimensions')
const factSchemas       = ref<Schema[]>([])
const factTablesLoading = ref(false)
const factExpanded      = ref<Set<string>>(new Set())

// ── New state: right-panel tab & selected type ─────────────
const selectedTableIsFactTable = ref(false)
const rightPanelTab    = ref<'columns' | 'measures' | 'attributes'>('columns')
const tableMeasures    = ref<Measure[]>([])
const tableAttributes  = ref<Attribute[]>([])
const rightPanelLoading= ref(false)

// ── New state: table actions ───────────────────────────────
const tableActionLoading = ref<string | null>(null)   // 'refresh'|'analyze'|'optimize'|null
const tableActionMsg     = ref('')
const showOptimizeDialog = ref(false)

// ── Computed ──────────────────────────────────────────────
const activeSchemas = computed(() =>
  tableTypeTab.value === 'dimensions' ? schemas.value : factSchemas.value
)

const activeExpandedSchemas = computed(() =>
  tableTypeTab.value === 'dimensions' ? expandedSchemas.value : factExpanded.value
)

const filteredSchemas = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return activeSchemas.value
  return activeSchemas.value
    .map(s => ({
      ...s,
      tables: s.tables.filter(t =>
        t.name.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
      ),
    }))
    .filter(s => s.tables.length > 0)
})

const totalTables = computed(() =>
  activeSchemas.value.reduce((n, s) => n + s.tables.length, 0)
)

const totalSchemas = computed(() => activeSchemas.value.length)

const totalRows = computed(() =>
  activeSchemas.value.reduce((n, s) =>
    s.tables.reduce((m, t) => m + t.row_count, n), 0)
)

const totalColumns = computed(() =>
  activeSchemas.value.reduce((n, s) =>
    s.tables.reduce((m, t) => m + t.columns.length, n), 0)
)

// ── Helpers ───────────────────────────────────────────────
function fmtRows(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

function timeAgo(dateStr?: string): string {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function typeIcon(type: string) {
  const t = type.toUpperCase()
  if (t.includes('INT') || t.includes('DECIMAL') || t.includes('FLOAT') || t.includes('NUMERIC')) return Hash
  if (t.includes('DATE') || t.includes('TIME')) return Calendar
  if (t.includes('BOOL')) return ToggleLeft
  return Type
}

function typeClass(type: string): string {
  const t = type.toUpperCase()
  if (t.includes('INT') || t.includes('DECIMAL') || t.includes('FLOAT') || t.includes('NUMERIC')) return 'tc--num'
  if (t.includes('DATE') || t.includes('TIME')) return 'tc--date'
  if (t.includes('BOOL')) return 'tc--bool'
  return 'tc--text'
}

function aggClass(agg: string): string {
  const a = agg.toUpperCase()
  if (a === 'SUM')   return 'agg--sum'
  if (a === 'AVG')   return 'agg--avg'
  if (a === 'COUNT') return 'agg--count'
  if (a === 'MAX' || a === 'MIN') return 'agg--minmax'
  return 'agg--other'
}

function toggleSchema(name: string) {
  const set = tableTypeTab.value === 'dimensions' ? expandedSchemas.value : factExpanded.value
  if (set.has(name)) {
    set.delete(name)
  } else {
    set.add(name)
  }
}

function selectTable(schema: Schema, table: TableDef, isFact = false) {
  selectedSchema.value = schema.name
  selectedTable.value  = table
  selectedTableIsFactTable.value = isFact
  rightPanelTab.value  = 'columns'
  tableMeasures.value  = []
  tableAttributes.value= []
  tableActionMsg.value = ''

  const set = isFact ? factExpanded.value : expandedSchemas.value
  if (!set.has(schema.name)) set.add(schema.name)
}

async function copyColName(name: string) {
  try {
    await navigator.clipboard.writeText(name)
    copiedCol.value = name
    setTimeout(() => { copiedCol.value = null }, 1500)
  } catch { /* ignore */ }
}

// ── API: dimension tables ─────────────────────────────────
async function fetchWarehouse() {
  try {
    const [schemasRes, tablesRes] = await Promise.all([
      api.get('/api/data-warehouse/schemas/'),
      api.get('/api/data-warehouse/dimension-tables/'),
    ])
    const schemaRows: any[] = Array.isArray(schemasRes.data?.results) ? schemasRes.data.results
                            : Array.isArray(schemasRes.data)          ? schemasRes.data
                            : []
    const tableRows: any[]  = Array.isArray(tablesRes.data?.results)  ? tablesRes.data.results
                            : Array.isArray(tablesRes.data)           ? tablesRes.data
                            : []

    const tablesBySchema: Record<string, TableDef[]> = {}
    for (const t of tableRows) {
      const sid = t.schema || ''
      if (!tablesBySchema[sid]) tablesBySchema[sid] = []
      tablesBySchema[sid].push(mapDimTable(t))
    }

    schemas.value = schemaRows.map(s => ({
      name:   s.name || '',
      tables: tablesBySchema[s.id] ?? [],
    }))
  } catch {
    schemas.value = []
  } finally {
    loading.value = false
  }
  if (!selectedTable.value && schemas.value[0]?.tables[0]) {
    selectedSchema.value = schemas.value[0].name
    selectedTable.value  = schemas.value[0].tables[0]
    expandedSchemas.value.add(schemas.value[0].name)
  }
}

// ── API: fact tables ──────────────────────────────────────
async function fetchFactTables() {
  if (factSchemas.value.length > 0) return   // already loaded
  factTablesLoading.value = true
  try {
    const res = await api.get('/api/data-warehouse/fact-tables/')
    const rows: any[] = Array.isArray(res.data?.results) ? res.data.results
                      : Array.isArray(res.data)          ? res.data
                      : []

    const bySchema: Record<string, { name: string; tables: TableDef[] }> = {}
    for (const t of rows) {
      const sname = t.schema_name || t.schema || 'default'
      if (!bySchema[sname]) bySchema[sname] = { name: sname, tables: [] }
      bySchema[sname].tables.push(mapDimTable(t))
    }
    factSchemas.value = Object.values(bySchema)
  } catch {
    factSchemas.value = []
  } finally {
    factTablesLoading.value = false
  }
}

// ── API: right-panel sub-tabs ──────────────────────────────
async function fetchRightPanelTab() {
  if (!selectedTable.value?.id) return
  if (rightPanelTab.value === 'columns') return

  rightPanelLoading.value = true
  try {
    if (rightPanelTab.value === 'measures' && selectedTableIsFactTable.value) {
      const res = await api.get(`/api/data-warehouse/fact-tables/${selectedTable.value.id}/measures/`)
      const rows: any[] = Array.isArray(res.data?.results) ? res.data.results
                        : Array.isArray(res.data)          ? res.data
                        : []
      tableMeasures.value = rows.map(m => ({
        name:                    m.name || '',
        data_type_display:       m.data_type_display || m.data_type || '—',
        aggregation_type_display:m.aggregation_type_display || m.aggregation_type || '—',
        description:             m.description || undefined,
        is_active:               m.is_active ?? true,
      }))
    } else if (rightPanelTab.value === 'attributes' && !selectedTableIsFactTable.value) {
      const res = await api.get(`/api/data-warehouse/dimension-tables/${selectedTable.value.id}/attributes/`)
      const rows: any[] = Array.isArray(res.data?.results) ? res.data.results
                        : Array.isArray(res.data)          ? res.data
                        : []
      tableAttributes.value = rows.map(a => ({
        name:           a.name || '',
        column:         a.column || '',
        data_type_display: a.data_type_display || a.data_type || '—',
        description:    a.description || undefined,
        is_key:         a.is_key ?? false,
        is_hierarchical:a.is_hierarchical ?? false,
        is_active:      a.is_active ?? true,
      }))
    }
  } catch { /* ignore */ } finally {
    rightPanelLoading.value = false
  }
}

// ── API: table actions ────────────────────────────────────
async function doTableAction(action: 'refresh' | 'analyze' | 'optimize') {
  if (!selectedTable.value?.id) return
  if (action === 'optimize' && !showOptimizeDialog.value) {
    showOptimizeDialog.value = true
    return
  }
  showOptimizeDialog.value = false
  tableActionLoading.value  = action
  tableActionMsg.value      = ''
  const base = selectedTableIsFactTable.value
    ? `/api/data-warehouse/fact-tables/${selectedTable.value.id}`
    : `/api/data-warehouse/dimension-tables/${selectedTable.value.id}`
  try {
    await api.post(`${base}/${action}/`)
    const labels: Record<string, string> = {
      refresh:  'Rafraîchissement effectué.',
      analyze:  'Analyse terminée.',
      optimize: 'Optimisation terminée.',
    }
    tableActionMsg.value = labels[action] ?? 'Opération réussie.'
    setTimeout(() => { tableActionMsg.value = '' }, 4000)
  } catch {
    tableActionMsg.value = 'Erreur lors de l\'opération.'
    setTimeout(() => { tableActionMsg.value = '' }, 4000)
  } finally {
    tableActionLoading.value = null
  }
}

// ── Watchers ──────────────────────────────────────────────
watch(tableTypeTab, async (tab) => {
  selectedTable.value  = null
  selectedSchema.value = ''
  tableActionMsg.value = ''
  rightPanelTab.value  = 'columns'
  if (tab === 'facts') await fetchFactTables()
})

watch(rightPanelTab, () => {
  fetchRightPanelTab()
})

async function refresh() {
  refreshing.value = true
  loading.value    = true
  selectedTable.value = null
  // Reset fact tables so they reload fresh on next switch
  factSchemas.value = []
  await fetchWarehouse()
  lastUpdated.value = new Date()
  refreshing.value  = false
}

onMounted(fetchWarehouse)
</script>

<template>
  <div class="wh">

    <!-- ── Page header ────────────────────────────────────── -->
    <header class="wh-header">
      <div>
        <h2 class="wh-title">Data Warehouse</h2>
        <p class="wh-meta">Schémas · tables · colonnes · Mis à jour {{ timeAgo(lastUpdated.toISOString()) }}</p>
      </div>
      <button
        class="refresh-btn"
        :class="{ 'refresh-btn--spinning': refreshing }"
        :disabled="refreshing"
        @click="refresh"
      >
        <RefreshCcw :size="14" />
        <span>Actualiser</span>
      </button>
    </header>

    <!-- ── Stats rail ──────────────────────────────────────── -->
    <section class="stats-rail" aria-label="Statistiques entrepôt">
      <div class="stat-item">
        <Database :size="16" class="stat-icon" />
        <span class="stat-value">{{ totalSchemas }}</span>
        <span class="stat-label">Schémas</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <Table2 :size="16" class="stat-icon" />
        <span class="stat-value">{{ totalTables }}</span>
        <span class="stat-label">Tables</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <Columns :size="16" class="stat-icon" />
        <span class="stat-value">{{ totalColumns }}</span>
        <span class="stat-label">Colonnes</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <BarChart2 :size="16" class="stat-icon" />
        <span class="stat-value">{{ fmtRows(totalRows) }}</span>
        <span class="stat-label">Enregistrements</span>
      </div>
    </section>

    <!-- ── Two-pane explorer ───────────────────────────────── -->
    <div class="explorer">

      <!-- Left: schema tree -->
      <aside class="tree-pane">

        <!-- ── Tab switcher ── -->
        <div class="tree-tabs">
          <button
            class="tree-tab"
            :class="{ 'tree-tab--active': tableTypeTab === 'dimensions' }"
            @click="tableTypeTab = 'dimensions'"
          >
            <Layers :size="13" />
            Dimensions
          </button>
          <button
            class="tree-tab"
            :class="{ 'tree-tab--active': tableTypeTab === 'facts' }"
            @click="tableTypeTab = 'facts'"
          >
            <BarChart2 :size="13" />
            Faits
          </button>
        </div>

        <div class="tree-search">
          <Search :size="14" class="tree-search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            class="tree-search-input"
            placeholder="Rechercher une table…"
            aria-label="Rechercher une table"
          />
        </div>

        <div class="tree-body">
          <!-- Dimension loading skeleton -->
          <template v-if="tableTypeTab === 'dimensions' && loading">
            <div v-for="i in 3" :key="i" class="tree-skel-group">
              <div class="tree-skel-schema"></div>
              <div v-for="j in 3" :key="j" class="tree-skel-table"></div>
            </div>
          </template>

          <!-- Fact loading skeleton -->
          <template v-else-if="tableTypeTab === 'facts' && factTablesLoading">
            <div v-for="i in 3" :key="i" class="tree-skel-group">
              <div class="tree-skel-schema"></div>
              <div v-for="j in 2" :key="j" class="tree-skel-table"></div>
            </div>
          </template>

          <template v-else>
            <div
              v-for="schema in filteredSchemas"
              :key="schema.name"
              class="tree-group"
            >
              <!-- Schema header -->
              <button
                class="tree-schema"
                :class="{ 'tree-schema--open': activeExpandedSchemas.has(schema.name) }"
                @click="toggleSchema(schema.name)"
                :aria-expanded="activeExpandedSchemas.has(schema.name)"
              >
                <component
                  :is="activeExpandedSchemas.has(schema.name) ? ChevronDown : ChevronRight"
                  :size="13"
                  class="tree-chevron"
                />
                <Database :size="14" class="tree-db-icon" />
                <span class="tree-schema-name">{{ schema.name }}</span>
                <span class="tree-count">{{ schema.tables.length }}</span>
              </button>

              <!-- Tables -->
              <Transition name="tree">
                <div v-if="activeExpandedSchemas.has(schema.name)" class="tree-tables">
                  <button
                    v-for="table in schema.tables"
                    :key="table.name"
                    class="tree-table"
                    :class="{
                      'tree-table--active':
                        selectedSchema === schema.name && selectedTable?.name === table.name,
                    }"
                    @click="selectTable(schema, table, tableTypeTab === 'facts')"
                  >
                    <Table2 :size="13" class="tree-table-icon" />
                    <span class="tree-table-name">{{ table.name }}</span>
                    <span class="tree-rows">{{ fmtRows(table.row_count) }}</span>
                  </button>
                </div>
              </Transition>
            </div>

            <p v-if="filteredSchemas.length === 0" class="tree-empty">
              <template v-if="searchQuery">Aucune table trouvée pour "{{ searchQuery }}"</template>
              <template v-else>Aucune table disponible</template>
            </p>
          </template>
        </div>
      </aside>

      <!-- Right: table detail -->
      <main class="detail-pane">
        <template v-if="!selectedTable">
          <div class="detail-empty">
            <Database :size="40" class="detail-empty-icon" />
            <p>Sélectionnez une table dans l'arborescence</p>
          </div>
        </template>

        <template v-else>
          <!-- Table header -->
          <div class="detail-header">
            <div class="detail-breadcrumb">
              <span class="bc-schema">{{ selectedSchema }}</span>
              <ChevronRight :size="13" class="bc-sep" />
              <span class="bc-table">{{ selectedTable.name }}</span>
              <span v-if="selectedTableIsFactTable" class="bc-type-badge bc-type-badge--fact">
                Fait
              </span>
              <span v-else class="bc-type-badge bc-type-badge--dim">
                Dimension
              </span>
            </div>
            <div class="detail-meta-row">
              <span class="meta-chip">
                <BarChart2 :size="11" />
                {{ fmtRows(selectedTable.row_count) }} lignes
              </span>
              <span class="meta-chip">
                <Columns :size="11" />
                {{ selectedTable.columns.length }} colonnes
              </span>
              <span class="meta-chip meta-chip--muted">
                <RefreshCcw :size="11" />
                {{ timeAgo(selectedTable.last_updated) }}
              </span>
            </div>
            <p v-if="selectedTable.description" class="detail-desc">
              <Info :size="12" class="desc-icon" />
              {{ selectedTable.description }}
            </p>

            <!-- ── Action buttons ── -->
            <div class="action-bar">
              <button
                class="action-btn action-btn--refresh"
                :disabled="!!tableActionLoading"
                @click="doTableAction('refresh')"
              >
                <Loader2
                  v-if="tableActionLoading === 'refresh'"
                  :size="13"
                  class="spin-icon"
                />
                <RefreshCcw v-else :size="13" />
                Rafraîchir
              </button>

              <button
                v-if="!selectedTableIsFactTable"
                class="action-btn action-btn--analyze"
                :disabled="!!tableActionLoading"
                @click="doTableAction('analyze')"
              >
                <Loader2
                  v-if="tableActionLoading === 'analyze'"
                  :size="13"
                  class="spin-icon"
                />
                <BarChart2 v-else :size="13" />
                Analyser
              </button>

              <button
                v-if="!selectedTableIsFactTable"
                class="action-btn action-btn--optimize"
                :disabled="!!tableActionLoading"
                @click="doTableAction('optimize')"
              >
                <Loader2
                  v-if="tableActionLoading === 'optimize'"
                  :size="13"
                  class="spin-icon"
                />
                <AlertTriangle v-else :size="13" />
                Optimiser
              </button>

              <span
                v-if="tableActionMsg"
                class="action-msg"
                :class="tableActionMsg.startsWith('Erreur') ? 'action-msg--err' : 'action-msg--ok'"
              >
                <CheckCircle2 v-if="!tableActionMsg.startsWith('Erreur')" :size="13" />
                <AlertTriangle v-else :size="13" />
                {{ tableActionMsg }}
              </span>
            </div>
          </div>

          <!-- ── Right-panel tab switcher ── -->
          <div class="rp-tabs">
            <button
              class="rp-tab"
              :class="{ 'rp-tab--active': rightPanelTab === 'columns' }"
              @click="rightPanelTab = 'columns'"
            >
              <Columns :size="13" />
              Colonnes
            </button>
            <button
              v-if="selectedTableIsFactTable"
              class="rp-tab"
              :class="{ 'rp-tab--active': rightPanelTab === 'measures' }"
              @click="rightPanelTab = 'measures'"
            >
              <Hash :size="13" />
              Mesures
            </button>
            <button
              v-if="!selectedTableIsFactTable"
              class="rp-tab"
              :class="{ 'rp-tab--active': rightPanelTab === 'attributes' }"
              @click="rightPanelTab = 'attributes'"
            >
              <Tag :size="13" />
              Attributs
            </button>
          </div>

          <!-- ══ Columns tab ══ -->
          <div v-if="rightPanelTab === 'columns'" class="col-table-wrap">
            <table class="col-table" aria-label="Colonnes de la table">
              <thead>
                <tr>
                  <th class="col-th">#</th>
                  <th class="col-th">Colonne</th>
                  <th class="col-th">Type</th>
                  <th class="col-th col-th--center">PK</th>
                  <th class="col-th col-th--center">Null</th>
                  <th class="col-th">Description</th>
                  <th class="col-th col-th--action"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(col, idx) in selectedTable.columns"
                  :key="col.name"
                  class="col-row"
                  :class="{ 'col-row--pk': col.primary_key }"
                >
                  <td class="col-td col-td--idx">{{ idx + 1 }}</td>
                  <td class="col-td col-td--name">
                    <Key v-if="col.primary_key" :size="11" class="pk-icon" />
                    <span class="col-name">{{ col.name }}</span>
                  </td>
                  <td class="col-td">
                    <span class="type-badge" :class="typeClass(col.type)">
                      <component :is="typeIcon(col.type)" :size="10" />
                      {{ col.type }}
                    </span>
                  </td>
                  <td class="col-td col-td--center">
                    <span v-if="col.primary_key" class="badge-pk">PK</span>
                    <span v-else class="dash-val">—</span>
                  </td>
                  <td class="col-td col-td--center">
                    <span class="null-dot" :class="col.nullable ? 'null-dot--yes' : 'null-dot--no'">
                      {{ col.nullable ? 'OUI' : 'NON' }}
                    </span>
                  </td>
                  <td class="col-td col-td--desc">
                    <span v-if="col.description" class="col-desc">{{ col.description }}</span>
                    <span v-else class="dash-val">—</span>
                  </td>
                  <td class="col-td col-td--action">
                    <button
                      class="copy-btn"
                      :class="{ 'copy-btn--done': copiedCol === col.name }"
                      :title="`Copier « ${col.name} »`"
                      @click="copyColName(col.name)"
                    >
                      <component :is="copiedCol === col.name ? Check : Copy" :size="12" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- ══ Measures tab ══ -->
          <div v-else-if="rightPanelTab === 'measures'" class="sub-panel">
            <div v-if="rightPanelLoading" class="sub-loading">
              <Loader2 :size="20" class="spin-icon" />
              <span>Chargement des mesures…</span>
            </div>
            <div v-else-if="tableMeasures.length === 0" class="sub-empty">
              <Hash :size="32" class="sub-empty-icon" />
              <p>Aucune mesure définie pour cette table</p>
            </div>
            <ul v-else class="measure-list">
              <li
                v-for="m in tableMeasures"
                :key="m.name"
                class="measure-item"
                :class="{ 'measure-item--inactive': !m.is_active }"
              >
                <div class="measure-top">
                  <span class="measure-name">{{ m.name }}</span>
                  <span class="agg-badge" :class="aggClass(m.aggregation_type_display)">
                    {{ m.aggregation_type_display }}
                  </span>
                  <span class="measure-active-dot" :class="m.is_active ? 'active-dot--on' : 'active-dot--off'"></span>
                </div>
                <div class="measure-bottom">
                  <span class="type-badge" :class="typeClass(m.data_type_display)">
                    <component :is="typeIcon(m.data_type_display)" :size="10" />
                    {{ m.data_type_display }}
                  </span>
                  <span v-if="m.description" class="measure-desc">{{ m.description }}</span>
                </div>
              </li>
            </ul>
          </div>

          <!-- ══ Attributes tab ══ -->
          <div v-else-if="rightPanelTab === 'attributes'" class="sub-panel">
            <div v-if="rightPanelLoading" class="sub-loading">
              <Loader2 :size="20" class="spin-icon" />
              <span>Chargement des attributs…</span>
            </div>
            <div v-else-if="tableAttributes.length === 0" class="sub-empty">
              <Tag :size="32" class="sub-empty-icon" />
              <p>Aucun attribut défini pour cette table</p>
            </div>
            <ul v-else class="attr-list">
              <li
                v-for="a in tableAttributes"
                :key="a.name"
                class="attr-item"
                :class="{ 'attr-item--inactive': !a.is_active }"
              >
                <div class="attr-top">
                  <span class="attr-name">{{ a.name }}</span>
                  <span v-if="a.is_key" class="attr-flag attr-flag--key">
                    <Key :size="10" /> Clé
                  </span>
                  <span v-if="a.is_hierarchical" class="attr-flag attr-flag--hier">
                    <Layers :size="10" /> Hiérarchie
                  </span>
                  <span class="measure-active-dot" :class="a.is_active ? 'active-dot--on' : 'active-dot--off'"></span>
                </div>
                <div class="attr-bottom">
                  <span class="attr-col">{{ a.column }}</span>
                  <span class="type-badge" :class="typeClass(a.data_type_display)">
                    <component :is="typeIcon(a.data_type_display)" :size="10" />
                    {{ a.data_type_display }}
                  </span>
                  <span v-if="a.description" class="measure-desc">{{ a.description }}</span>
                </div>
              </li>
            </ul>
          </div>

        </template>
      </main>

    </div>

    <!-- ── Optimize confirmation dialog ───────────────────── -->
    <Transition name="dialog">
      <div v-if="showOptimizeDialog" class="dialog-overlay" @click.self="showOptimizeDialog = false">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-title">
          <div class="dialog-header">
            <AlertTriangle :size="18" class="dlg-warn-icon" />
            <h3 id="dlg-title" class="dialog-title">Confirmer l'optimisation</h3>
          </div>
          <p class="dialog-body">
            Optimiser supprime les données obsolètes. Continuer&nbsp;?
          </p>
          <div class="dialog-footer">
            <button class="dialog-btn dialog-btn--cancel" @click="showOptimizeDialog = false">
              Annuler
            </button>
            <button class="dialog-btn dialog-btn--confirm" @click="doTableAction('optimize')">
              Confirmer
            </button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* ── Root layout ─────────────────────────────────────────── */
.wh {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  height: 100%;
  min-height: 0;
}

/* ── Header ──────────────────────────────────────────────── */
.wh-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-shrink: 0;
}

.wh-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}

.wh-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: none;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 150ms, color 150ms, background-color 150ms;
}
.refresh-btn:hover:not(:disabled) {
  border-color: var(--accent-dim);
  color: var(--accent);
  background-color: var(--accent-surface);
}
.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.refresh-btn--spinning svg { animation: spin 0.7s linear infinite; }
.spin-icon { animation: spin 0.8s linear infinite; flex-shrink: 0; }

/* ── Stats rail ──────────────────────────────────────────── */
.stats-rail {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-8);
  flex: 1;
}

.stat-sep {
  width: 1px;
  height: 36px;
  background: var(--border-subtle);
  flex-shrink: 0;
}

.stat-icon {
  color: var(--accent-dim);
  flex-shrink: 0;
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
}

/* ── Two-pane explorer ───────────────────────────────────── */
.explorer {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--sp-4);
  flex: 1;
  min-height: 0;
}

/* ── Tree pane ───────────────────────────────────────────── */
.tree-pane {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Tree tabs ───────────────────────────────────────────── */
.tree-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.tree-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-2);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  transition: color 150ms, border-color 150ms, background 150ms;
  white-space: nowrap;
  margin-bottom: -1px;
}
.tree-tab:hover { color: var(--text-primary); background: var(--surface-overlay); }
.tree-tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tree-search {
  position: relative;
  padding: var(--sp-3) var(--sp-3) var(--sp-2);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.tree-search-icon {
  position: absolute;
  left: calc(var(--sp-3) + 10px);
  top: 50%;
  transform: translateY(-58%);
  color: var(--text-muted);
  pointer-events: none;
}

.tree-search-input {
  width: 100%;
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 7px 10px 7px 32px;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-primary);
  outline: none;
  transition: border-color 150ms;
}
.tree-search-input::placeholder { color: var(--text-muted); }
.tree-search-input:focus { border-color: var(--accent-dim); }

.tree-body {
  overflow-y: auto;
  flex: 1;
  padding: var(--sp-2) 0;
}

/* Schema row */
.tree-schema {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px var(--sp-3);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--text-secondary);
  transition: background 100ms, color 100ms;
  border-radius: 0;
}
.tree-schema:hover { background: var(--surface-overlay); color: var(--text-primary); }
.tree-schema--open { color: var(--text-primary); }

.tree-chevron { color: var(--text-muted); flex-shrink: 0; }
.tree-db-icon { color: var(--accent-dim); flex-shrink: 0; }

.tree-schema-name {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: 600;
  letter-spacing: 0.04em;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tree-count {
  font-size: var(--text-xs);
  color: var(--text-muted);
  background: var(--surface-muted);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  font-weight: 500;
  flex-shrink: 0;
}

/* Table rows */
.tree-tables {
  padding-left: var(--sp-6);
  padding-bottom: var(--sp-1);
}

.tree-table {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 5px var(--sp-3);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  border-radius: var(--radius-sm);
  transition: background 100ms, color 100ms;
}
.tree-table:hover { background: var(--surface-overlay); color: var(--text-primary); }
.tree-table--active {
  background: var(--accent-surface);
  color: var(--accent);
}
.tree-table--active .tree-table-icon { color: var(--accent-dim); }

.tree-table-icon { color: var(--border-strong); flex-shrink: 0; }

.tree-table-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-rows {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* Skeleton */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.tree-skel-group { padding: var(--sp-1) var(--sp-3); }

.tree-skel-schema, .tree-skel-table {
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--surface-overlay) 25%,
    var(--surface-muted)   50%,
    var(--surface-overlay) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  margin-bottom: var(--sp-2);
}
.tree-skel-schema { height: 28px; width: 70%; }
.tree-skel-table  { height: 22px; width: 85%; margin-left: var(--sp-6); }

.tree-empty {
  padding: var(--sp-6) var(--sp-4);
  font-size: var(--text-sm);
  color: var(--text-muted);
  text-align: center;
}

/* Tree transition */
.tree-enter-active { transition: all var(--duration-base) var(--ease-out-expo); overflow: hidden; }
.tree-enter-from   { opacity: 0; max-height: 0; }
.tree-enter-to     { opacity: 1; max-height: 600px; }

/* ── Detail pane ─────────────────────────────────────────── */
.detail-pane {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-4);
  flex: 1;
  color: var(--text-muted);
  font-size: var(--text-sm);
  height: 100%;
  padding: var(--sp-16);
}

.detail-empty-icon { color: var(--border-default); }

/* Detail header */
.detail-header {
  padding: var(--sp-6);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  flex-shrink: 0;
}

.detail-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.bc-schema {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.bc-sep { color: var(--border-strong); }

.bc-table {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.bc-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.04em;
}
.bc-type-badge--fact {
  background: oklch(14% 0.05 258);
  color: oklch(65% 0.15 258);
  border: 1px solid oklch(25% 0.08 258);
}
.bc-type-badge--dim {
  background: oklch(14% 0.05 148);
  color: oklch(60% 0.14 148);
  border: 1px solid oklch(25% 0.08 148);
}

.detail-meta-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.meta-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
}

.meta-chip svg { color: var(--accent-dim); }
.meta-chip--muted svg { color: var(--text-muted); }
.meta-chip--muted { color: var(--text-muted); }

.detail-desc {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.desc-icon { color: var(--text-muted); flex-shrink: 0; }

/* ── Action bar ──────────────────────────────────────────── */
.action-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 6px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: none;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms, color 150ms, border-color 150ms;
  white-space: nowrap;
}
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.action-btn--refresh {
  color: var(--text-secondary);
}
.action-btn--refresh:hover:not(:disabled) {
  background: var(--accent-surface);
  border-color: var(--accent-dim);
  color: var(--accent);
}

.action-btn--analyze {
  color: oklch(65% 0.12 258);
}
.action-btn--analyze:hover:not(:disabled) {
  background: oklch(14% 0.04 258);
  border-color: oklch(30% 0.09 258);
}

.action-btn--optimize {
  color: var(--warning);
}
.action-btn--optimize:hover:not(:disabled) {
  background: oklch(17% 0.05 80);
  border-color: oklch(35% 0.10 80);
}

.action-msg {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  font-weight: 500;
  padding: 4px 10px;
  border-radius: var(--radius-full);
}
.action-msg--ok  { color: oklch(70% 0.15 148); background: oklch(15% 0.04 148); }
.action-msg--err { color: var(--error); background: oklch(14% 0.05 0); }

/* ── Right-panel tabs ────────────────────────────────────── */
.rp-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 var(--sp-6);
  flex-shrink: 0;
}

.rp-tab {
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
.rp-tab:hover { color: var(--text-primary); }
.rp-tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* Columns table */
.col-table-wrap {
  overflow: auto;
  flex: 1;
}

.col-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.col-th {
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

.col-th--center { text-align: center; }
.col-th--action { width: 40px; }

.col-row {
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;
}
.col-row:last-child { border-bottom: none; }
.col-row:hover { background: var(--surface-overlay); }
.col-row--pk { background: oklch(11% 0.04 62 / 0.5); }
.col-row--pk:hover { background: oklch(13% 0.05 62 / 0.5); }

.col-td {
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-secondary);
  vertical-align: middle;
  white-space: nowrap;
}

.col-td--idx {
  color: var(--text-muted);
  font-size: var(--text-xs);
  width: 36px;
  font-variant-numeric: tabular-nums;
}

.col-td--name {
  color: var(--text-primary);
  font-weight: 600;
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-base);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.col-td--center { text-align: center; }
.col-td--desc   { max-width: 240px; white-space: normal; }

.pk-icon { color: var(--accent); flex-shrink: 0; }

.col-name { white-space: nowrap; }

/* Type badge */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.03em;
}

.tc--num  { background: oklch(14% 0.04 258); color: oklch(65% 0.12 258); }
.tc--text { background: oklch(15% 0.04 148); color: oklch(65% 0.13 148); }
.tc--date { background: oklch(17% 0.05 80);  color: var(--warning); }
.tc--bool { background: oklch(15% 0.06 310); color: oklch(68% 0.13 310); }

/* PK badge */
.badge-pk {
  display: inline-block;
  padding: 1px 7px;
  border-radius: var(--radius-full);
  background: var(--accent-surface);
  border: 1px solid var(--accent-deep);
  color: var(--accent);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

/* Nullable */
.null-dot {
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
}
.null-dot--yes { color: var(--text-muted); }
.null-dot--no  { color: var(--error); }

.col-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: normal;
}

.dash-val { color: var(--border-strong); }

/* Copy button */
.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: background 100ms, color 100ms;
  opacity: 0;
}

.col-row:hover .copy-btn { opacity: 1; }

.copy-btn:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

.copy-btn--done { color: oklch(70% 0.15 148); opacity: 1; }

/* ── Sub-panels (Measures / Attributes) ──────────────────── */
.sub-panel {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4) var(--sp-6);
}

.sub-loading,
.sub-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  padding: var(--sp-12);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.sub-empty-icon { color: var(--border-default); }

/* Measure list */
.measure-list,
.attr-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.measure-item,
.attr-item {
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3) var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  transition: background 100ms;
}
.measure-item:hover,
.attr-item:hover {
  background: var(--surface-muted);
}
.measure-item--inactive,
.attr-item--inactive {
  opacity: 0.55;
}

.measure-top,
.attr-top {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.measure-name,
.attr-name {
  font-family: 'Barlow Condensed', monospace;
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.measure-bottom,
.attr-bottom {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.measure-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

/* Aggregation badge */
.agg-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
}
.agg--sum    { background: oklch(14% 0.05 258); color: oklch(65% 0.15 258); }
.agg--avg    { background: oklch(14% 0.05 196); color: oklch(65% 0.13 196); }
.agg--count  { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.agg--minmax { background: oklch(17% 0.05 80);  color: var(--warning); }
.agg--other  { background: var(--surface-muted); color: var(--text-muted); }

/* Active dot */
.measure-active-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-left: auto;
}
.active-dot--on  { background: oklch(65% 0.18 148); box-shadow: 0 0 4px oklch(65% 0.18 148 / 0.5); }
.active-dot--off { background: var(--border-strong); }

/* Attribute flags */
.attr-flag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}
.attr-flag--key  {
  background: var(--accent-surface);
  border: 1px solid var(--accent-deep);
  color: var(--accent);
}
.attr-flag--hier {
  background: oklch(14% 0.05 310);
  border: 1px solid oklch(25% 0.08 310);
  color: oklch(68% 0.13 310);
}

.attr-col {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-family: 'Barlow Condensed', monospace;
  font-style: italic;
}

/* ── Confirmation dialog ─────────────────────────────────── */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0% 0 0 / 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.dialog {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--sp-6);
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  box-shadow: 0 20px 60px oklch(0% 0 0 / 0.5);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.dlg-warn-icon { color: var(--warning); flex-shrink: 0; }

.dialog-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
}

.dialog-body {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

.dialog-btn {
  padding: 7px 18px;
  border-radius: var(--radius-md);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border-default);
  transition: background 150ms, color 150ms, border-color 150ms;
}
.dialog-btn--cancel {
  background: none;
  color: var(--text-secondary);
}
.dialog-btn--cancel:hover {
  background: var(--surface-overlay);
  color: var(--text-primary);
}
.dialog-btn--confirm {
  background: oklch(17% 0.05 80);
  color: var(--warning);
  border-color: oklch(35% 0.10 80);
}
.dialog-btn--confirm:hover {
  background: oklch(22% 0.07 80);
}

/* Dialog transition */
.dialog-enter-active, .dialog-leave-active { transition: opacity 150ms, transform 150ms; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; transform: scale(0.96); }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1024px) {
  .explorer { grid-template-columns: 240px 1fr; }
  .stat-item { padding: var(--sp-4) var(--sp-4); }
}

@media (max-width: 768px) {
  .wh { padding: var(--sp-4); }
  .explorer {
    grid-template-columns: 1fr;
    grid-template-rows: 260px 1fr;
  }
  .stats-rail { flex-wrap: wrap; }
  .stat-sep { display: none; }
  .stat-item { flex: 1 1 40%; }
}
</style>
