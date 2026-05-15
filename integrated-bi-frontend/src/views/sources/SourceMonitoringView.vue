<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api/axios'
import {
  Activity, RefreshCcw, Search, AlertCircle, AlertTriangle,
  Info, Bug, ChevronLeft, ChevronRight, Database, Cpu,
  Wifi, Layers, Clock,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────────
type LogLevel = 'debug' | 'info' | 'warning' | 'error'

interface DataSourceLog {
  id: number
  data_source_name: string
  level: LogLevel
  message: string
  query_text: string | null
  execution_time_ms: number | null
  rows_affected: number | null
  created_at: string
}

interface LogStats {
  total: number
  errors: number
  warnings: number
  infos: number
  debugs?: number
}

interface DataSourceMetric {
  id: number
  data_source_name: string
  query_time_ms: number | null
  rows_returned: number | null
  cpu_time_ms: number | null
  io_wait_ms: number | null
  bytes_sent: number | null
  bytes_received: number | null
  network_latency_ms: number | null
  connection_time_ms: number | null
  active_connections: number | null
  timestamp: string
}

interface LatestMetric {
  data_source_name: string
  query_time_ms: number | null
  rows_returned: number | null
  active_connections: number | null
  timestamp?: string
}

interface DataSource {
  id: number
  name: string
}

// ── State — tabs ───────────────────────────────────────────────
const activeTab = ref<'logs' | 'metrics'>('logs')

// ── State — sources list ───────────────────────────────────────
const sources = ref<DataSource[]>([])

// ── State — logs ───────────────────────────────────────────────
const logs          = ref<DataSourceLog[]>([])
const logsLoading   = ref(true)
const logsError     = ref<string | null>(null)
const expandedLogId = ref<number | null>(null)

const logFilterSource = ref('')
const logFilterLevel  = ref('')
const logSearch       = ref('')

const logPage    = ref(1)
const logPerPage = ref(20)
const logTotal   = ref(0)

// ── State — log stats ──────────────────────────────────────────
const logStats        = ref<LogStats | null>(null)
const logStatsLoading = ref(true)

// ── State — metrics ────────────────────────────────────────────
const metrics         = ref<DataSourceMetric[]>([])
const metricsLoading  = ref(true)
const metricsError    = ref<string | null>(null)
const latestMetrics   = ref<LatestMetric[]>([])
const latestLoading   = ref(true)

const metricFilterSource = ref('')
const metricAfter        = ref('')
const metricBefore       = ref('')

// ── Auto-refresh ───────────────────────────────────────────────
let refreshTimer: ReturnType<typeof setInterval> | null = null

// ── Helpers ────────────────────────────────────────────────────
function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function fmtMs(val: number | null): string {
  if (val === null || val === undefined) return '—'
  return `${val} ms`
}

function fmtNum(val: number | null): string {
  if (val === null || val === undefined) return '—'
  return val.toLocaleString('fr-FR')
}

// ── API — sources ──────────────────────────────────────────────
async function fetchSources() {
  try {
    const { data } = await api.get('/api/data-sources/sources/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    sources.value = rows
  } catch {
    sources.value = []
  }
}

// ── API — log stats ────────────────────────────────────────────
async function fetchLogStats() {
  logStatsLoading.value = true
  try {
    const { data } = await api.get('/api/data-sources/logs/stats/')
    logStats.value = data
  } catch {
    logStats.value = null
  } finally {
    logStatsLoading.value = false
  }
}

// ── API — logs ─────────────────────────────────────────────────
async function fetchLogs() {
  logsLoading.value = true
  logsError.value   = null
  try {
    const params: Record<string, string | number> = {
      page:     logPage.value,
      per_page: logPerPage.value,
      ordering: '-created_at',
    }
    if (logFilterSource.value) params.data_source = logFilterSource.value
    if (logFilterLevel.value)  params.level        = logFilterLevel.value
    if (logSearch.value.trim()) params.search       = logSearch.value.trim()

    const { data } = await api.get('/api/data-sources/logs/', { params })
    logs.value  = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    logTotal.value = data?.count ?? logs.value.length
  } catch (err: unknown) {
    logsError.value = 'Impossible de charger les logs.'
    logs.value = []
  } finally {
    logsLoading.value = false
  }
}

// ── API — metrics ──────────────────────────────────────────────
async function fetchMetrics() {
  metricsLoading.value = true
  metricsError.value   = null
  try {
    const params: Record<string, string | number> = { ordering: '-timestamp' }
    if (metricFilterSource.value) params.data_source       = metricFilterSource.value
    if (metricAfter.value)        params.timestamp_after   = metricAfter.value
    if (metricBefore.value)       params.timestamp_before  = metricBefore.value

    const { data } = await api.get('/api/data-sources/metrics/', { params })
    metrics.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    metricsError.value = 'Impossible de charger les métriques.'
    metrics.value = []
  } finally {
    metricsLoading.value = false
  }
}

async function fetchLatestMetrics() {
  latestLoading.value = true
  try {
    const { data } = await api.get('/api/data-sources/metrics/latest/')
    latestMetrics.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    latestMetrics.value = []
  } finally {
    latestLoading.value = false
  }
}

// ── Pagination ─────────────────────────────────────────────────
const logPageStart = () => (logPage.value - 1) * logPerPage.value + 1
const logPageEnd   = () => Math.min(logPage.value * logPerPage.value, logTotal.value)
const logPageMax   = () => Math.ceil(logTotal.value / logPerPage.value)

function prevPage() {
  if (logPage.value > 1) { logPage.value--; fetchLogs() }
}
function nextPage() {
  if (logPage.value < logPageMax()) { logPage.value++; fetchLogs() }
}

// ── Filter actions ─────────────────────────────────────────────
function applyLogFilters() {
  logPage.value = 1
  fetchLogs()
}

function applyMetricFilters() {
  fetchMetrics()
}

function refreshAll() {
  fetchLogs()
  fetchLogStats()
  fetchLatestMetrics()
  fetchMetrics()
}

function toggleExpand(id: number) {
  expandedLogId.value = expandedLogId.value === id ? null : id
}

// ── Lifecycle ──────────────────────────────────────────────────
onMounted(async () => {
  await fetchSources()
  fetchLogs()
  fetchLogStats()
  fetchLatestMetrics()
  fetchMetrics()

  refreshTimer = setInterval(() => {
    fetchLogs()
    fetchLogStats()
    fetchLatestMetrics()
    fetchMetrics()
  }, 30_000)
})

onUnmounted(() => {
  if (refreshTimer !== null) clearInterval(refreshTimer)
})
</script>

<template>
  <div class="mon-page">

    <!-- ── Page header ─────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">
          <Activity :size="22" class="page-title-icon" />
          Monitoring Sources
        </h2>
        <p class="page-meta">Logs et métriques de performance des sources de données</p>
      </div>
      <button class="btn-ghost btn-icon" title="Actualiser" @click="refreshAll">
        <RefreshCcw :size="15" />
      </button>
    </header>

    <!-- ── Tabs ───────────────────────────────────────────────── -->
    <div class="tabs-bar">
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'logs' }"
        @click="activeTab = 'logs'"
      >
        <AlertCircle :size="14" />
        Logs
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'metrics' }"
        @click="activeTab = 'metrics'"
      >
        <Activity :size="14" />
        Métriques
      </button>
    </div>

    <!-- ════════════════════════════════════════════════════════
         TAB — LOGS
    ════════════════════════════════════════════════════════ -->
    <template v-if="activeTab === 'logs'">

      <!-- Stats strip -->
      <section class="stats-strip">
        <template v-if="logStatsLoading">
          <div v-for="i in 4" :key="i" class="stat-skel"></div>
        </template>
        <template v-else-if="logStats">
          <div class="stat-cell">
            <Layers :size="14" class="sc-icon" />
            <span class="sc-val">{{ fmtNum(logStats.total) }}</span>
            <span class="sc-lbl">Total logs</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat-cell">
            <AlertCircle :size="14" class="sc-icon sc-icon--error" />
            <span class="sc-val sc-val--error">{{ fmtNum(logStats.errors) }}</span>
            <span class="sc-lbl">Erreurs</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat-cell">
            <AlertTriangle :size="14" class="sc-icon sc-icon--warning" />
            <span class="sc-val sc-val--warning">{{ fmtNum(logStats.warnings) }}</span>
            <span class="sc-lbl">Avertissements</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat-cell">
            <Info :size="14" class="sc-icon sc-icon--info" />
            <span class="sc-val sc-val--info">{{ fmtNum(logStats.infos) }}</span>
            <span class="sc-lbl">Infos</span>
          </div>
        </template>
      </section>

      <!-- Toolbar -->
      <div class="toolbar">
        <select
          v-model="logFilterSource"
          class="filter-select"
          @change="applyLogFilters"
        >
          <option value="">Toutes les sources</option>
          <option v-for="src in sources" :key="src.id" :value="src.id">
            {{ src.name }}
          </option>
        </select>

        <select
          v-model="logFilterLevel"
          class="filter-select"
          @change="applyLogFilters"
        >
          <option value="">Tous les niveaux</option>
          <option value="debug">Debug</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>

        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input
            v-model="logSearch"
            type="search"
            class="search-input"
            placeholder="Rechercher dans les logs…"
            @keydown.enter="applyLogFilters"
          />
        </div>

        <button class="btn-ghost btn-icon" title="Appliquer la recherche" @click="applyLogFilters">
          <Search :size="14" />
        </button>
      </div>

      <!-- Error -->
      <div v-if="logsError" class="error-banner">
        <AlertCircle :size="16" />
        {{ logsError }}
      </div>

      <!-- Loading skeleton -->
      <div v-else-if="logsLoading" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Horodatage</th>
              <th>Source</th>
              <th>Niveau</th>
              <th>Message</th>
              <th>Temps exec.</th>
              <th>Lignes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in 5" :key="i" class="skel-row">
              <td><div class="cell-skel" style="width:120px"></div></td>
              <td><div class="cell-skel" style="width:90px"></div></td>
              <td><div class="cell-skel" style="width:60px"></div></td>
              <td><div class="cell-skel" style="width:240px"></div></td>
              <td><div class="cell-skel" style="width:60px"></div></td>
              <td><div class="cell-skel" style="width:50px"></div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Data table -->
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Horodatage</th>
              <th>Source</th>
              <th>Niveau</th>
              <th>Message</th>
              <th>Temps exec.</th>
              <th>Lignes affectées</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="logs.length === 0">
              <tr>
                <td colspan="6" class="empty-cell">
                  <span>Aucun log trouvé</span>
                </td>
              </tr>
            </template>
            <template v-else>
              <template v-for="log in logs" :key="log.id">
                <tr
                  class="data-row"
                  :class="{ 'data-row--expanded': expandedLogId === log.id }"
                  @click="toggleExpand(log.id)"
                >
                  <td class="cell-mono">{{ formatDate(log.created_at) }}</td>
                  <td>
                    <span class="source-tag">{{ log.data_source_name }}</span>
                  </td>
                  <td>
                    <span class="level-badge" :class="`level-badge--${log.level}`">
                      <Bug        v-if="log.level === 'debug'"   :size="10" />
                      <Info       v-if="log.level === 'info'"    :size="10" />
                      <AlertTriangle v-if="log.level === 'warning'" :size="10" />
                      <AlertCircle   v-if="log.level === 'error'"   :size="10" />
                      {{ log.level }}
                    </span>
                  </td>
                  <td class="cell-message">{{ log.message }}</td>
                  <td class="cell-num">{{ fmtMs(log.execution_time_ms) }}</td>
                  <td class="cell-num">{{ fmtNum(log.rows_affected) }}</td>
                </tr>
                <!-- Expanded query_text -->
                <tr v-if="expandedLogId === log.id && log.query_text" class="expand-row">
                  <td colspan="6">
                    <div class="expand-body">
                      <span class="expand-label">Requête SQL</span>
                      <pre class="expand-code">{{ log.query_text }}</pre>
                    </div>
                  </td>
                </tr>
                <tr v-else-if="expandedLogId === log.id && !log.query_text" class="expand-row">
                  <td colspan="6">
                    <div class="expand-body">
                      <span class="expand-label expand-label--muted">Aucune requête associée à ce log.</span>
                    </div>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="!logsLoading && logTotal > 0" class="pagination">
        <button
          class="page-btn"
          :disabled="logPage === 1"
          @click="prevPage"
          title="Page précédente"
        >
          <ChevronLeft :size="15" />
        </button>
        <span class="page-info">
          {{ logPageStart() }}–{{ logPageEnd() }} de {{ fmtNum(logTotal) }}
        </span>
        <button
          class="page-btn"
          :disabled="logPage >= logPageMax()"
          @click="nextPage"
          title="Page suivante"
        >
          <ChevronRight :size="15" />
        </button>
      </div>

    </template>

    <!-- ════════════════════════════════════════════════════════
         TAB — MÉTRIQUES
    ════════════════════════════════════════════════════════ -->
    <template v-else-if="activeTab === 'metrics'">

      <!-- Latest metrics cards -->
      <section class="latest-section">
        <h3 class="section-title">Dernières métriques par source</h3>

        <div v-if="latestLoading" class="latest-grid">
          <div v-for="i in 3" :key="i" class="latest-skel"></div>
        </div>

        <div v-else-if="latestMetrics.length === 0" class="latest-empty">
          Aucune métrique disponible.
        </div>

        <div v-else class="latest-grid">
          <div v-for="lm in latestMetrics" :key="lm.data_source_name" class="latest-card">
            <div class="latest-card-hd">
              <Database :size="14" class="lc-icon" />
              <span class="lc-name">{{ lm.data_source_name }}</span>
            </div>
            <div class="lc-stats">
              <div class="lc-stat">
                <Clock :size="12" class="lcs-icon" />
                <span class="lcs-val">{{ fmtMs(lm.query_time_ms) }}</span>
                <span class="lcs-lbl">Temps requête</span>
              </div>
              <div class="lc-stat">
                <Layers :size="12" class="lcs-icon" />
                <span class="lcs-val">{{ fmtNum(lm.rows_returned) }}</span>
                <span class="lcs-lbl">Lignes retournées</span>
              </div>
              <div class="lc-stat">
                <Wifi :size="12" class="lcs-icon" />
                <span class="lcs-val">{{ fmtNum(lm.active_connections) }}</span>
                <span class="lcs-lbl">Connexions actives</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Filters -->
      <div class="toolbar">
        <select
          v-model="metricFilterSource"
          class="filter-select"
          @change="applyMetricFilters"
        >
          <option value="">Toutes les sources</option>
          <option v-for="src in sources" :key="src.id" :value="src.id">
            {{ src.name }}
          </option>
        </select>

        <label class="date-label">
          Depuis
          <input
            v-model="metricAfter"
            type="datetime-local"
            class="date-input"
            @change="applyMetricFilters"
          />
        </label>

        <label class="date-label">
          Jusqu'à
          <input
            v-model="metricBefore"
            type="datetime-local"
            class="date-input"
            @change="applyMetricFilters"
          />
        </label>
      </div>

      <!-- Error -->
      <div v-if="metricsError" class="error-banner">
        <AlertCircle :size="16" />
        {{ metricsError }}
      </div>

      <!-- Skeleton -->
      <div v-else-if="metricsLoading" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Horodatage</th>
              <th>Source</th>
              <th>Temps requête</th>
              <th>Lignes retournées</th>
              <th>CPU (ms)</th>
              <th>I/O wait (ms)</th>
              <th>Latence réseau</th>
              <th>Connexions actives</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in 5" :key="i" class="skel-row">
              <td v-for="j in 8" :key="j"><div class="cell-skel" style="width:80px"></div></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Metrics table -->
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Horodatage</th>
              <th>Source</th>
              <th>Temps requête</th>
              <th>Lignes retournées</th>
              <th>CPU (ms)</th>
              <th>I/O wait (ms)</th>
              <th>Latence réseau</th>
              <th>Connexions actives</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="metrics.length === 0">
              <tr>
                <td colspan="8" class="empty-cell">Aucune métrique trouvée</td>
              </tr>
            </template>
            <tr v-for="m in metrics" :key="m.id" class="data-row">
              <td class="cell-mono">{{ formatDate(m.timestamp) }}</td>
              <td>
                <span class="source-tag">{{ m.data_source_name }}</span>
              </td>
              <td class="cell-num cell-num--accent">{{ fmtMs(m.query_time_ms) }}</td>
              <td class="cell-num">{{ fmtNum(m.rows_returned) }}</td>
              <td class="cell-num">
                <span :class="{ 'val--warn': (m.cpu_time_ms ?? 0) > 500 }">
                  {{ fmtMs(m.cpu_time_ms) }}
                </span>
              </td>
              <td class="cell-num">
                <span :class="{ 'val--warn': (m.io_wait_ms ?? 0) > 200 }">
                  {{ fmtMs(m.io_wait_ms) }}
                </span>
              </td>
              <td class="cell-num">{{ fmtMs(m.network_latency_ms) }}</td>
              <td class="cell-num">{{ fmtNum(m.active_connections) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>

  </div>
</template>

<style scoped>
/* ── Page shell ──────────────────────────────────────────────── */
.mon-page {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────────── */
.page-hd {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}

.page-title-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.page-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--sp-1);
}

/* ── Buttons ─────────────────────────────────────────────────── */
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

.btn-ghost:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.btn-icon {
  padding: var(--sp-2);
  min-height: unset;
  width: 38px;
  height: 38px;
  justify-content: center;
}

/* ── Tabs ────────────────────────────────────────────────────── */
.tabs-bar {
  display: flex;
  gap: var(--sp-1);
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: var(--sp-1);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  border: none;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: none;
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: color 150ms, background-color 150ms;
}

.tab-btn:hover {
  color: var(--text-secondary);
  background-color: var(--surface-overlay);
}

.tab-btn--active {
  color: var(--accent);
  background-color: var(--accent-surface);
  font-weight: 600;
}

/* ── Stats strip ─────────────────────────────────────────────── */
.stats-strip {
  display: flex;
  align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.stat-cell {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-6);
}

.stat-sep {
  width: 1px;
  height: 28px;
  background: var(--border-subtle);
  flex-shrink: 0;
}

.stat-skel {
  flex: 1;
  height: 52px;
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.sc-icon         { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--error  { color: var(--error); }
.sc-icon--warning{ color: oklch(76% 0.14 62); }
.sc-icon--info   { color: oklch(60% 0.13 240); }

.sc-val          { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.sc-val--error   { color: var(--error); }
.sc-val--warning { color: oklch(76% 0.14 62); }
.sc-val--info    { color: oklch(60% 0.13 240); }
.sc-lbl          { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Toolbar ─────────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.filter-select {
  height: 38px;
  padding: 0 var(--sp-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms;
}

.filter-select:focus { border-color: var(--accent-dim); }

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

.date-label {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-family: var(--font-ui);
}

.date-input {
  height: 38px;
  padding: 0 var(--sp-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms;
  color-scheme: dark;
}

.date-input:focus { border-color: var(--accent-dim); }

/* ── Error banner ────────────────────────────────────────────── */
.error-banner {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: var(--error-surface);
  border: 1px solid var(--error);
  border-radius: var(--radius-md);
  color: var(--error);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

/* ── Table ───────────────────────────────────────────────────── */
.table-wrap {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}

.data-table thead tr {
  border-bottom: 1px solid var(--border-subtle);
}

.data-table th {
  padding: var(--sp-3) var(--sp-4);
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  white-space: nowrap;
}

.data-row {
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: background-color 120ms;
}

.data-row:hover { background-color: var(--surface-overlay); }

.data-row:last-child { border-bottom: none; }

.data-row--expanded {
  background-color: var(--accent-surface);
}

.data-table td {
  padding: var(--sp-3) var(--sp-4);
  color: var(--text-secondary);
  vertical-align: middle;
}

.cell-mono {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.cell-message {
  max-width: 340px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-num {
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--text-secondary);
  text-align: right;
  white-space: nowrap;
}

.cell-num--accent { color: var(--accent-dim); }

.val--warn { color: oklch(76% 0.14 62); font-weight: 700; }

/* Skeleton cells */
.skel-row td { padding: var(--sp-3) var(--sp-4); }

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.cell-skel {
  height: 14px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* Empty cell */
.empty-cell {
  padding: var(--sp-12) var(--sp-4) !important;
  text-align: center;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

/* ── Level badge ─────────────────────────────────────────────── */
.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.level-badge--debug   { background: var(--surface-overlay);  color: var(--text-muted); }
.level-badge--info    { background: oklch(12% 0.04 240);      color: oklch(60% 0.13 240); }
.level-badge--warning { background: var(--accent-surface);    color: oklch(76% 0.14 62); }
.level-badge--error   { background: var(--error-surface);     color: var(--error); }

/* ── Source tag ──────────────────────────────────────────────── */
.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  white-space: nowrap;
}

/* ── Expanded row ────────────────────────────────────────────── */
.expand-row td {
  padding: 0 !important;
}

.expand-body {
  padding: var(--sp-3) var(--sp-5) var(--sp-4);
  background: var(--surface-overlay);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.expand-label {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent-dim);
}

.expand-label--muted { color: var(--text-muted); }

.expand-code {
  background: oklch(8% 0.01 258);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3) var(--sp-4);
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  color: var(--accent-dim);
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre;
  line-height: 1.6;
}

/* ── Pagination ──────────────────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  justify-content: center;
}

.page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: var(--surface-raised);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--accent-dim);
  color: var(--accent);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-family: var(--font-ui);
}

/* ── Latest metrics section ──────────────────────────────────── */
.latest-section {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: -0.01em;
}

.latest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--sp-4);
}

.latest-skel {
  height: 110px;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.latest-empty {
  font-size: var(--text-sm);
  color: var(--text-muted);
  padding: var(--sp-4);
}

.latest-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  transition: border-color 200ms, box-shadow 200ms;
}

.latest-card:hover {
  border-color: var(--accent-dim);
  box-shadow: 0 4px 20px oklch(76% 0.14 62 / 0.1);
}

.latest-card-hd {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.lc-icon { color: var(--accent); flex-shrink: 0; }

.lc-name {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lc-stats {
  display: flex;
  gap: var(--sp-4);
}

.lc-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  flex: 1;
}

.lcs-icon { color: var(--text-muted); }

.lcs-val {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.lcs-lbl {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
}

/* ── Reduced motion ──────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .cell-skel,
  .latest-skel,
  .stat-skel { animation: none; }
}
</style>
