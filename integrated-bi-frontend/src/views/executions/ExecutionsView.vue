<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '@/api/axios'
import {
  Activity, RefreshCw, Search, Eye, X, ChevronLeft, ChevronRight,
  Clock, Globe, User, GitBranch, RotateCw, Webhook,
  AlertCircle, CheckCircle, Loader2, Ban, SkipForward,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────────────────────────
type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'skipped' | 'retrying'
type TriggerType = 'manual' | 'schedule' | 'api' | 'dependency' | 'retry' | 'webhook'

interface ExecutionLog {
  id: string
  execution_id: string
  pipeline: string
  pipeline_name: string
  status: ExecutionStatus
  status_display: string
  triggered_by: TriggerType
  triggered_by_display: string
  triggered_by_user_name: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  duration_formatted: string
  rows_read: number
  rows_written: number
  rows_errors: number
  error_message: string
  error_traceback: string
  result_summary: unknown
  execution_metadata: unknown
  transformation_logs: unknown
  created_at: string
  updated_at: string
}

interface ExecutionStats {
  total?: number
  running?: number
  failed?: number
  completed?: number
  success_rate?: number
  [key: string]: unknown
}

interface PaginatedResponse<T> {
  results: T[]
  count: number
  next: string | null
  previous: string | null
}

// ── Status metadata ────────────────────────────────────────────────────────────
const STATUS_META: Record<ExecutionStatus | string, { label: string; cls: string }> = {
  pending:   { label: 'En attente',  cls: 'status--pending'   },
  running:   { label: 'En cours',    cls: 'status--running'   },
  completed: { label: 'Terminé',     cls: 'status--completed' },
  failed:    { label: 'Échec',       cls: 'status--failed'    },
  cancelled: { label: 'Annulé',      cls: 'status--cancelled' },
  skipped:   { label: 'Ignoré',      cls: 'status--skipped'   },
  retrying:  { label: 'Reprise',     cls: 'status--retrying'  },
}

// ── State ──────────────────────────────────────────────────────────────────────
const executions      = ref<ExecutionLog[]>([])
const loading         = ref(true)
const refreshing      = ref(false)
const stats           = ref<ExecutionStats>({})
const statsLoading    = ref(true)

// Filters
const searchQuery     = ref('')
const statusFilter    = ref('')
const triggerFilter   = ref('')
let   searchDebounce: ReturnType<typeof setTimeout> | null = null

// Pagination
const currentPage     = ref(1)
const perPage         = ref(20)
const totalCount      = ref(0)

// Detail panel
const selectedId      = ref<string | null>(null)
const detailData      = ref<ExecutionLog | null>(null)
const detailLoading   = ref(false)
const tracebackOpen   = ref(false)

// Auto-refresh
const autoRefresh     = ref(false)
let   autoRefreshInterval: ReturnType<typeof setInterval> | null = null

// ── Computed ───────────────────────────────────────────────────────────────────
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / perPage.value)))

const hasRunningOrPending = computed(() =>
  executions.value.some(e => e.status === 'running' || e.status === 'pending')
)

const successRate = computed(() => {
  const r = stats.value.success_rate
  if (r == null) return '—'
  return `${Math.round(Number(r))}%`
})

// ── Helpers ────────────────────────────────────────────────────────────────────
function getStatusMeta(status: string) {
  return STATUS_META[status] ?? { label: status, cls: 'status--cancelled' }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

function formatShortDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function prettyJson(val: unknown): string {
  if (val == null) return ''
  if (typeof val === 'string') return val
  return JSON.stringify(val, null, 2)
}

function rowsProgressPct(ex: ExecutionLog): number {
  if (!ex.rows_read || ex.rows_read === 0) return 0
  return Math.min(100, Math.round((ex.rows_written / ex.rows_read) * 100))
}

// ── Trigger icon component helper ──────────────────────────────────────────────
const TRIGGER_ICONS: Record<TriggerType | string, typeof User> = {
  manual:     User,
  schedule:   Clock,
  api:        Globe,
  dependency: GitBranch,
  retry:      RotateCw,
  webhook:    Webhook,
}

function triggerIcon(trigger: string) {
  return TRIGGER_ICONS[trigger] ?? Globe
}

// ── API ────────────────────────────────────────────────────────────────────────
async function fetchStats() {
  statsLoading.value = true
  try {
    const { data } = await api.get('/api/etl/executions/stats/')
    stats.value = data ?? {}
  } catch {
    stats.value = {}
  } finally {
    statsLoading.value = false
  }
}

async function fetchExecutions(opts: { silent?: boolean } = {}) {
  if (!opts.silent) loading.value = true
  else refreshing.value = true

  try {
    const params: Record<string, string | number> = {
      page:     currentPage.value,
      per_page: perPage.value,
    }
    if (statusFilter.value)  params.status       = statusFilter.value
    if (triggerFilter.value) params.triggered_by  = triggerFilter.value
    if (searchQuery.value)   params.pipeline_name = searchQuery.value

    const { data } = await api.get<PaginatedResponse<ExecutionLog>>('/api/etl/executions/', { params })

    if (Array.isArray(data?.results)) {
      executions.value = data.results
      totalCount.value = data.count ?? data.results.length
    } else if (Array.isArray(data)) {
      executions.value = data as unknown as ExecutionLog[]
      totalCount.value = (data as unknown as ExecutionLog[]).length
    } else {
      executions.value = []
      totalCount.value = 0
    }
  } catch {
    executions.value = []
    totalCount.value = 0
  } finally {
    loading.value  = false
    refreshing.value = false
  }
}

async function fetchDetail(id: string) {
  detailLoading.value = true
  tracebackOpen.value = false
  try {
    const { data } = await api.get<ExecutionLog>(`/api/etl/executions/${id}/details/`)
    detailData.value = data
  } catch {
    // Fallback to the list item if details endpoint fails
    detailData.value = executions.value.find(e => e.id === id) ?? null
  } finally {
    detailLoading.value = false
  }
}

// ── Actions ────────────────────────────────────────────────────────────────────
function openDetail(ex: ExecutionLog) {
  selectedId.value = ex.id
  fetchDetail(ex.id)
}

function closeDetail() {
  selectedId.value = null
  detailData.value = null
  tracebackOpen.value = false
}

async function handleRefresh() {
  await Promise.all([fetchExecutions({ silent: true }), fetchStats()])
}

function setPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

// ── Auto-refresh ───────────────────────────────────────────────────────────────
function startAutoRefresh() {
  if (autoRefreshInterval) return
  autoRefreshInterval = setInterval(async () => {
    await fetchExecutions({ silent: true })
    if (!hasRunningOrPending.value) {
      stopAutoRefresh()
      autoRefresh.value = false
    }
  }, 10000)
}

function stopAutoRefresh() {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) startAutoRefresh()
  else stopAutoRefresh()
}

// ── Watchers ───────────────────────────────────────────────────────────────────
watch(statusFilter, () => {
  currentPage.value = 1
  fetchExecutions()
})

watch(triggerFilter, () => {
  currentPage.value = 1
  fetchExecutions()
})

watch(searchQuery, () => {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    currentPage.value = 1
    fetchExecutions()
  }, 400)
})

watch(currentPage, () => fetchExecutions())

// ── Lifecycle ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([fetchExecutions(), fetchStats()])
})

onUnmounted(() => {
  stopAutoRefresh()
  if (searchDebounce) clearTimeout(searchDebounce)
})
</script>

<template>
  <div class="exec-page" :class="{ 'exec-page--split': selectedId }">

    <!-- ═══════════════════════════════════════════════════════ MAIN COLUMN -->
    <div class="exec-main">

      <!-- ── Header ──────────────────────────────────────────────────────── -->
      <header class="page-hd">
        <div class="page-hd-left">
          <Activity :size="22" class="page-icon" />
          <div>
            <h2 class="page-title">Surveillance des exécutions ETL</h2>
            <p class="page-subtitle">Suivi en temps réel des exécutions de pipelines</p>
          </div>
        </div>
        <!-- Live indicator -->
        <div v-if="autoRefresh" class="live-badge" aria-label="Rafraîchissement automatique actif">
          <span class="live-dot"></span>
          <span class="live-label">Live</span>
        </div>
      </header>

      <!-- ── Stats strip ────────────────────────────────────────────────── -->
      <div class="stats-strip">
        <div class="stat-cell">
          <span class="stat-n">{{ statsLoading ? '—' : (stats.total ?? 0) }}</span>
          <span class="stat-l">Total</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat-cell">
          <span class="stat-n stat-n--running">{{ statsLoading ? '—' : (stats.running ?? 0) }}</span>
          <span class="stat-l">En cours</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat-cell">
          <span class="stat-n stat-n--err">{{ statsLoading ? '—' : (stats.failed ?? 0) }}</span>
          <span class="stat-l">Échecs</span>
        </div>
        <div class="stat-div"></div>
        <div class="stat-cell">
          <span class="stat-n stat-n--ok">{{ statsLoading ? '—' : successRate }}</span>
          <span class="stat-l">Taux de succès</span>
        </div>
      </div>

      <!-- ── Toolbar ──────────────────────────────────────────────────────── -->
      <div class="toolbar">
        <!-- Search -->
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input
            v-model="searchQuery"
            class="search-input"
            type="search"
            placeholder="Rechercher par nom de pipeline…"
          />
        </div>

        <!-- Status filter -->
        <div class="select-wrap">
          <select v-model="statusFilter" class="filter-select">
            <option value="">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="running">En cours</option>
            <option value="completed">Terminé</option>
            <option value="failed">Échec</option>
            <option value="cancelled">Annulé</option>
            <option value="retrying">Reprise</option>
            <option value="skipped">Ignoré</option>
          </select>
        </div>

        <!-- Trigger filter -->
        <div class="select-wrap">
          <select v-model="triggerFilter" class="filter-select">
            <option value="">Tous les déclencheurs</option>
            <option value="manual">Manuel</option>
            <option value="schedule">Planifié</option>
            <option value="api">API</option>
            <option value="dependency">Dépendance</option>
            <option value="retry">Reprise</option>
            <option value="webhook">Webhook</option>
          </select>
        </div>

        <!-- Refresh button -->
        <button class="btn-refresh" :disabled="refreshing || loading" @click="handleRefresh" title="Rafraîchir">
          <RefreshCw :size="15" :class="{ 'spin': refreshing }" />
          <span>Rafraîchir</span>
        </button>

        <!-- Auto-refresh toggle -->
        <button
          class="btn-auto-refresh"
          :class="{ 'btn-auto-refresh--active': autoRefresh }"
          @click="toggleAutoRefresh"
          title="Rafraîchissement automatique (10 s)"
        >
          <Loader2 :size="14" :class="{ 'spin': autoRefresh }" />
          <span>Auto</span>
        </button>
      </div>

      <!-- ── Table header ─────────────────────────────────────────────────── -->
      <div v-if="!loading && executions.length > 0" class="col-headers">
        <span class="col-pipeline">Pipeline</span>
        <span class="col-status">Statut</span>
        <span class="col-trigger">Déclencheur</span>
        <span class="col-started">Démarré</span>
        <span class="col-duration">Durée</span>
        <span class="col-rows">Lignes L/E/Err</span>
        <span class="col-actions"></span>
      </div>

      <!-- ── Execution rows ────────────────────────────────────────────────── -->
      <section class="exec-list" v-if="!loading">

        <!-- Empty state -->
        <div v-if="executions.length === 0" class="empty-state">
          <Activity :size="40" class="empty-icon" />
          <p class="empty-title">Aucune exécution trouvée</p>
          <p class="empty-sub">Modifiez vos filtres ou attendez le démarrage d'un pipeline.</p>
        </div>

        <!-- Rows -->
        <div
          v-for="(ex, i) in executions"
          :key="ex.id"
          class="exec-row"
          :class="{
            'exec-row--running':   ex.status === 'running',
            'exec-row--failed':    ex.status === 'failed',
            'exec-row--selected':  selectedId === ex.id,
          }"
          :style="{ '--row-i': i }"
          @click="openDetail(ex)"
        >
          <!-- Pipeline name -->
          <div class="col-pipeline exec-pipeline">
            <span class="exec-pipeline-name">{{ ex.pipeline_name || '—' }}</span>
            <span class="exec-id-sub">{{ ex.execution_id }}</span>
          </div>

          <!-- Status badge -->
          <div class="col-status">
            <div class="status-badge" :class="getStatusMeta(ex.status).cls">
              <CheckCircle v-if="ex.status === 'completed'" :size="13" class="status-icon" />
              <AlertCircle v-else-if="ex.status === 'failed'" :size="13" class="status-icon" />
              <Loader2    v-else-if="ex.status === 'running'" :size="13" class="status-icon spin" />
              <Loader2    v-else-if="ex.status === 'retrying'" :size="13" class="status-icon spin" />
              <Ban        v-else-if="ex.status === 'cancelled'" :size="13" class="status-icon" />
              <SkipForward v-else-if="ex.status === 'skipped'" :size="13" class="status-icon" />
              <Clock      v-else :size="13" class="status-icon" />
              <span>{{ ex.status_display || getStatusMeta(ex.status).label }}</span>
            </div>
          </div>

          <!-- Trigger -->
          <div class="col-trigger exec-trigger">
            <div class="trigger-badge">
              <component :is="triggerIcon(ex.triggered_by)" :size="12" class="trigger-icon" />
              <span>{{ ex.triggered_by_display || ex.triggered_by }}</span>
            </div>
            <span v-if="ex.triggered_by_user_name" class="trigger-user">{{ ex.triggered_by_user_name }}</span>
          </div>

          <!-- Started at -->
          <div class="col-started exec-date">
            {{ formatShortDate(ex.started_at) }}
          </div>

          <!-- Duration -->
          <div class="col-duration exec-duration">
            {{ ex.duration_formatted || '—' }}
          </div>

          <!-- Rows -->
          <div class="col-rows exec-rows">
            <span class="rows-read">{{ ex.rows_read?.toLocaleString('fr-FR') ?? '—' }}</span>
            <span class="rows-sep">/</span>
            <span class="rows-written">{{ ex.rows_written?.toLocaleString('fr-FR') ?? '—' }}</span>
            <span class="rows-sep">/</span>
            <span class="rows-errors" :class="{ 'rows-errors--has': ex.rows_errors > 0 }">
              {{ ex.rows_errors?.toLocaleString('fr-FR') ?? '0' }}
            </span>
          </div>

          <!-- Actions -->
          <div class="col-actions exec-actions" @click.stop>
            <button class="btn-detail" @click="openDetail(ex)" title="Voir les détails">
              <Eye :size="14" />
            </button>
          </div>

          <!-- Running sweep -->
          <div v-if="ex.status === 'running'" class="run-sweep" aria-hidden="true"></div>
        </div>

      </section>

      <!-- ── Skeletons ────────────────────────────────────────────────────── -->
      <section v-else class="exec-list">
        <div v-for="i in 8" :key="i" class="exec-skel"></div>
      </section>

      <!-- ── Pagination ────────────────────────────────────────────────────── -->
      <div v-if="totalCount > 0" class="pagination">
        <span class="page-info">
          {{ (currentPage - 1) * perPage + 1 }}–{{ Math.min(currentPage * perPage, totalCount) }}
          sur {{ totalCount.toLocaleString('fr-FR') }}
        </span>
        <div class="page-btns">
          <button
            class="page-btn"
            :disabled="currentPage === 1"
            @click="setPage(currentPage - 1)"
            aria-label="Page précédente"
          >
            <ChevronLeft :size="16" />
          </button>
          <span class="page-cur">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="page-btn"
            :disabled="currentPage >= totalPages"
            @click="setPage(currentPage + 1)"
            aria-label="Page suivante"
          >
            <ChevronRight :size="16" />
          </button>
        </div>
      </div>

    </div><!-- end exec-main -->

    <!-- ═══════════════════════════════════════════════════════ DETAIL PANEL -->
    <Transition name="detail-anim">
      <aside v-if="selectedId" class="detail-panel" aria-label="Détails de l'exécution">

        <!-- Panel loading -->
        <div v-if="detailLoading" class="detail-loading">
          <Loader2 :size="28" class="spin detail-spinner" />
        </div>

        <template v-else-if="detailData">

          <!-- Panel header -->
          <div class="detail-hd">
            <div class="detail-hd-info">
              <p class="detail-pipeline-name">{{ detailData.pipeline_name }}</p>
              <code class="detail-exec-id">{{ detailData.execution_id }}</code>
            </div>
            <button class="btn-close" @click="closeDetail" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <!-- Scrollable body -->
          <div class="detail-body">

            <!-- ── Status & timing ────────────────────────────────────── -->
            <section class="detail-section">
              <div class="detail-status-row">
                <div class="status-badge status-badge--lg" :class="getStatusMeta(detailData.status).cls">
                  <CheckCircle v-if="detailData.status === 'completed'" :size="15" class="status-icon" />
                  <AlertCircle v-else-if="detailData.status === 'failed'" :size="15" class="status-icon" />
                  <Loader2    v-else-if="detailData.status === 'running' || detailData.status === 'retrying'" :size="15" class="status-icon spin" />
                  <Ban        v-else-if="detailData.status === 'cancelled'" :size="15" class="status-icon" />
                  <SkipForward v-else-if="detailData.status === 'skipped'" :size="15" class="status-icon" />
                  <Clock      v-else :size="15" class="status-icon" />
                  <span>{{ detailData.status_display || getStatusMeta(detailData.status).label }}</span>
                </div>
                <div class="trigger-badge trigger-badge--detail">
                  <component :is="triggerIcon(detailData.triggered_by)" :size="13" class="trigger-icon" />
                  <span>{{ detailData.triggered_by_display || detailData.triggered_by }}</span>
                  <span v-if="detailData.triggered_by_user_name" class="trigger-user-detail">
                    ({{ detailData.triggered_by_user_name }})
                  </span>
                </div>
              </div>

              <dl class="detail-meta-grid">
                <div class="meta-item">
                  <dt>Démarré</dt>
                  <dd>{{ formatDate(detailData.started_at) }}</dd>
                </div>
                <div class="meta-item">
                  <dt>Terminé</dt>
                  <dd>{{ formatDate(detailData.completed_at) }}</dd>
                </div>
                <div class="meta-item">
                  <dt>Durée</dt>
                  <dd class="meta-duration">{{ detailData.duration_formatted || '—' }}</dd>
                </div>
              </dl>
            </section>

            <!-- ── Rows stats + progress bar ──────────────────────────── -->
            <section class="detail-section">
              <h4 class="section-title">Lignes traitées</h4>

              <!-- Progress bar: written vs read -->
              <div class="rows-bar-wrap" v-if="detailData.rows_read > 0">
                <div class="rows-bar">
                  <div
                    class="rows-bar-fill"
                    :style="{ width: rowsProgressPct(detailData) + '%' }"
                    :class="{ 'rows-bar-fill--error': detailData.rows_errors > 0 }"
                  ></div>
                </div>
                <span class="rows-bar-label">{{ rowsProgressPct(detailData) }}% écrites</span>
              </div>

              <div class="rows-stats-grid">
                <div class="rows-stat-cell">
                  <span class="rows-stat-n">{{ detailData.rows_read?.toLocaleString('fr-FR') ?? '—' }}</span>
                  <span class="rows-stat-l">Lues</span>
                </div>
                <div class="rows-stat-cell">
                  <span class="rows-stat-n rows-stat-n--written">{{ detailData.rows_written?.toLocaleString('fr-FR') ?? '—' }}</span>
                  <span class="rows-stat-l">Écrites</span>
                </div>
                <div class="rows-stat-cell">
                  <span
                    class="rows-stat-n"
                    :class="{ 'rows-stat-n--err': detailData.rows_errors > 0 }"
                  >{{ detailData.rows_errors?.toLocaleString('fr-FR') ?? '0' }}</span>
                  <span class="rows-stat-l">Erreurs</span>
                </div>
              </div>
            </section>

            <!-- ── Error section ──────────────────────────────────────── -->
            <section v-if="detailData.error_message" class="detail-section detail-section--error">
              <h4 class="section-title section-title--error">
                <AlertCircle :size="14" />
                Message d'erreur
              </h4>
              <p class="error-message-text">{{ detailData.error_message }}</p>

              <!-- Collapsible traceback -->
              <div v-if="detailData.error_traceback" class="traceback-wrap">
                <button class="btn-traceback" @click="tracebackOpen = !tracebackOpen">
                  <span>{{ tracebackOpen ? 'Masquer' : 'Afficher' }} la traceback</span>
                  <ChevronLeft
                    :size="13"
                    class="traceback-chevron"
                    :class="{ 'traceback-chevron--open': tracebackOpen }"
                  />
                </button>
                <pre v-if="tracebackOpen" class="code-block code-block--error">{{ detailData.error_traceback }}</pre>
              </div>
            </section>

            <!-- ── Result summary ─────────────────────────────────────── -->
            <section v-if="detailData.result_summary != null" class="detail-section">
              <h4 class="section-title">Résumé du résultat</h4>
              <pre class="code-block">{{ prettyJson(detailData.result_summary) }}</pre>
            </section>

            <!-- ── Transformation logs ────────────────────────────────── -->
            <section v-if="detailData.transformation_logs != null" class="detail-section">
              <h4 class="section-title">Logs de transformation</h4>
              <pre class="code-block">{{ prettyJson(detailData.transformation_logs) }}</pre>
            </section>

            <!-- ── Execution metadata ─────────────────────────────────── -->
            <section v-if="detailData.execution_metadata != null" class="detail-section">
              <h4 class="section-title">Métadonnées</h4>
              <pre class="code-block">{{ prettyJson(detailData.execution_metadata) }}</pre>
            </section>

          </div><!-- end detail-body -->
        </template>

        <!-- Error fallback if detail failed to load -->
        <div v-else class="detail-error">
          <AlertCircle :size="28" class="detail-error-icon" />
          <p>Impossible de charger les détails.</p>
          <button class="btn-retry" @click="selectedId && fetchDetail(selectedId)">Réessayer</button>
        </div>

      </aside>
    </Transition>

  </div><!-- end exec-page -->
</template>

<style scoped>
/* ══════════════════════════════════════════════════════════ Page layout */
.exec-page {
  display: flex;
  flex-direction: row;
  min-height: 100%;
  align-items: flex-start;
}

.exec-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  padding: var(--sp-8);
  overflow: hidden;
}

/* ══════════════════════════════════════════════════════════ Header */
.page-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
}

.page-hd-left {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
}

.page-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.page-title {
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

/* Live badge */
.live-badge {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-1) var(--sp-3);
  background-color: oklch(14% 0.04 148);
  border: 1px solid oklch(45% 0.12 148);
  border-radius: 99px;
  flex-shrink: 0;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: oklch(70% 0.15 148);
  animation: pulse 1.4s ease-in-out infinite;
}

.live-label {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: oklch(70% 0.15 148);
}

/* ══════════════════════════════════════════════════════════ Stats strip */
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
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1;
}

.stat-n--running { color: var(--info); }
.stat-n--err     { color: var(--error); }
.stat-n--ok      { color: var(--success); }

.stat-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* ══════════════════════════════════════════════════════════ Toolbar */
.toolbar {
  display: flex;
  gap: var(--sp-3);
  align-items: center;
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 340px;
  min-width: 180px;
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
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms ease;
}

.search-input:focus { border-color: var(--accent); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }

.filter-select {
  appearance: none;
  height: 38px;
  padding: 0 var(--sp-4);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms ease;
}

.filter-select:focus { border-color: var(--accent); }
.filter-select option { background-color: var(--surface-raised); }

.btn-refresh,
.btn-auto-refresh {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  height: 38px;
  padding: 0 var(--sp-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
  white-space: nowrap;
}

.btn-refresh {
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}

.btn-refresh:hover:not(:disabled) {
  border-color: var(--border-strong);
  color: var(--text-primary);
  background-color: var(--surface-overlay);
}

.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-auto-refresh {
  background-color: var(--surface-raised);
  border: 1px solid var(--border-default);
  color: var(--text-muted);
}

.btn-auto-refresh:hover {
  border-color: var(--border-strong);
  color: var(--text-secondary);
}

.btn-auto-refresh--active {
  background-color: oklch(14% 0.04 148);
  border-color: oklch(45% 0.12 148);
  color: oklch(70% 0.15 148);
}

/* ══════════════════════════════════════════════════════════ Table column headers */
.col-headers {
  display: grid;
  grid-template-columns: 1fr 130px 140px 160px 90px 130px 44px;
  gap: var(--sp-3);
  padding: 0 var(--sp-4);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
}

/* ══════════════════════════════════════════════════════════ Execution list */
.exec-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

/* ══════════════════════════════════════════════════════════ Execution row */
.exec-row {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 130px 140px 160px 90px 130px 44px;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  overflow: hidden;
  transition: background-color 150ms ease, border-color 150ms ease;

  opacity: 0;
  transform: translateY(4px);
  animation: row-in 240ms ease forwards;
  animation-delay: calc(var(--row-i, 0) * 30ms);
}

@keyframes row-in {
  to { opacity: 1; transform: none; }
}

.exec-row:hover {
  background-color: var(--surface-overlay);
  border-color: var(--border-default);
}

.exec-row--selected {
  border-color: var(--accent) !important;
  background-color: var(--accent-surface) !important;
}

.exec-row--running {
  background-color: oklch(12% 0.02 230);
  border-color: oklch(22% 0.06 230);
}

.exec-row--failed {
  background-color: oklch(12.5% 0.03 24);
  border-color: oklch(20% 0.05 24);
}

/* Running sweep at bottom */
.run-sweep {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, var(--info) 50%, transparent 100%);
  animation: sweep 2.4s linear infinite;
}

@keyframes sweep {
  from { transform: translateX(-100%); }
  to   { transform: translateX(100%); }
}

/* ── Row cell content ────────────────────────────────────────────── */
.exec-pipeline {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.exec-pipeline-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.exec-id-sub {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.7;
}

.exec-trigger {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.exec-date,
.exec-duration {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  white-space: nowrap;
}

.exec-rows {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: var(--text-xs);
  font-family: 'Courier New', monospace;
}

.rows-read    { color: var(--text-secondary); }
.rows-written { color: var(--success); }
.rows-sep     { color: var(--text-muted); }
.rows-errors  { color: var(--text-muted); }
.rows-errors--has { color: var(--error); font-weight: 700; }

.exec-actions {
  display: flex;
  justify-content: center;
}

/* ══════════════════════════════════════════════════════════ Status badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  padding: 2px var(--sp-2);
  border-radius: 99px;
  font-size: var(--text-xs);
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid transparent;
}

.status-badge--lg {
  padding: var(--sp-1) var(--sp-3);
  font-size: var(--text-sm);
}

.status-icon { flex-shrink: 0; }

/* Status color classes */
.status--pending {
  background-color: var(--surface-muted);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}

.status--running {
  background-color: oklch(14% 0.04 230);
  border-color: oklch(35% 0.1 230);
  color: var(--info);
}

.status--completed {
  background-color: oklch(14% 0.04 148);
  border-color: oklch(35% 0.1 148);
  color: var(--success);
}

.status--failed {
  background-color: oklch(12% 0.04 24);
  border-color: oklch(30% 0.08 24);
  color: var(--error);
}

.status--cancelled {
  background-color: var(--surface-muted);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}

.status--skipped {
  background-color: var(--surface-muted);
  border-color: var(--border-subtle);
  color: var(--text-muted);
}

.status--retrying {
  background-color: oklch(14% 0.04 80);
  border-color: oklch(40% 0.1 80);
  color: var(--warning);
}

/* ══════════════════════════════════════════════════════════ Trigger badge */
.trigger-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
}

.trigger-badge--detail {
  padding: 2px var(--sp-2);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: 99px;
}

.trigger-icon { color: var(--text-muted); flex-shrink: 0; }

.trigger-user {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.trigger-user-detail {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

/* ══════════════════════════════════════════════════════════ Detail button */
.btn-detail {
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
}

.btn-detail:hover {
  background-color: var(--accent-surface);
  border-color: var(--accent);
  color: var(--accent);
}

/* ══════════════════════════════════════════════════════════ Skeletons */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.exec-skel {
  height: 60px;
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

/* ══════════════════════════════════════════════════════════ Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-24) var(--sp-8);
  text-align: center;
}

.empty-icon  { color: var(--text-muted); }
.empty-title { font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.empty-sub   { font-size: var(--text-sm); color: var(--text-muted); max-width: 42ch; line-height: 1.6; }

/* ══════════════════════════════════════════════════════════ Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding-top: var(--sp-2);
}

.page-info {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.page-btns {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.page-btn {
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

.page-btn:hover:not(:disabled) {
  background-color: var(--surface-overlay);
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.page-cur {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 60px;
  text-align: center;
}

/* ══════════════════════════════════════════════════════════ Detail panel */
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
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.detail-hd-info {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  min-width: 0;
}

.detail-pipeline-name {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-exec-id {
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  color: var(--text-muted);
  word-break: break-all;
}

.btn-close {
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
  flex-shrink: 0;
}

.btn-close:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
  background-color: var(--surface-overlay);
}

/* ── Detail body scroll area */
.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

/* ── Detail sections */
.detail-section {
  padding: var(--sp-4) 0;
  border-bottom: 1px solid var(--border-subtle);
}

.detail-section:last-child { border-bottom: none; }

.detail-section--error {
  background-color: oklch(12% 0.03 24 / 0.5);
  border-radius: var(--radius-md);
  padding: var(--sp-4);
  border: 1px solid oklch(28% 0.06 24);
  margin: 0 calc(-1 * var(--sp-1));
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: var(--sp-3);
}

.section-title--error { color: var(--error); }

/* ── Status row */
.detail-status-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  flex-wrap: wrap;
  margin-bottom: var(--sp-4);
}

/* ── Meta grid */
.detail-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--sp-3);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.meta-item dt {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-item dd {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  word-break: break-word;
}

.meta-duration {
  font-family: 'Courier New', monospace;
  color: var(--text-primary) !important;
  font-weight: 600;
}

/* ── Rows bar */
.rows-bar-wrap {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-3);
}

.rows-bar {
  flex: 1;
  height: 6px;
  background-color: var(--surface-overlay);
  border-radius: 99px;
  overflow: hidden;
}

.rows-bar-fill {
  height: 100%;
  background-color: var(--success);
  border-radius: 99px;
  transition: width 600ms ease;
}

.rows-bar-fill--error { background-color: var(--warning); }

.rows-bar-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  min-width: 60px;
}

/* ── Rows stats grid */
.rows-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--sp-3);
}

.rows-stat-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: var(--sp-3);
  background-color: var(--surface-overlay);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  text-align: center;
}

.rows-stat-n {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.rows-stat-n--written { color: var(--success); }
.rows-stat-n--err     { color: var(--error); }

.rows-stat-l {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Error */
.error-message-text {
  font-size: var(--text-sm);
  color: var(--error);
  line-height: 1.5;
  margin-bottom: var(--sp-3);
  word-break: break-word;
}

.traceback-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.btn-traceback {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 150ms ease;
}

.btn-traceback:hover { color: var(--text-secondary); }

.traceback-chevron {
  transition: transform 200ms ease;
  transform: rotate(-90deg);
}

.traceback-chevron--open { transform: rotate(90deg); }

/* ── Code blocks */
.code-block {
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  line-height: 1.6;
  color: var(--text-secondary);
  background-color: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3);
  overflow: auto;
  white-space: pre;
  max-height: 280px;
}

.code-block--error {
  background-color: oklch(10% 0.03 24);
  border-color: oklch(25% 0.06 24);
  color: oklch(75% 0.1 24);
}

/* ── Detail loading / error */
.detail-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  color: var(--text-muted);
  text-align: center;
  padding: var(--sp-8);
}

.detail-error-icon { color: var(--error); }

.btn-retry {
  padding: var(--sp-2) var(--sp-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-retry:hover {
  background-color: var(--surface-overlay);
  border-color: var(--border-strong);
  color: var(--text-primary);
}

/* ══════════════════════════════════════════════════════════ Spin animation */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

/* ══════════════════════════════════════════════════════════ Detail panel transition */
.detail-anim-enter-active { transition: transform 300ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease; }
.detail-anim-leave-active { transition: transform 200ms cubic-bezier(0.4, 0, 1, 1), opacity 160ms ease; }
.detail-anim-enter-from,
.detail-anim-leave-to {
  transform: translateX(40px);
  opacity: 0;
}

/* ══════════════════════════════════════════════════════════ Responsive */
@media (max-width: 1300px) {
  .exec-row     { grid-template-columns: 1fr 120px 130px 140px 80px 110px 40px; }
  .col-headers  { grid-template-columns: 1fr 120px 130px 140px 80px 110px 40px; }
  .detail-panel { width: 380px; }
}

@media (max-width: 1100px) {
  .exec-row {
    grid-template-columns: 1fr 110px 120px 90px 80px 44px;
    grid-template-areas:
      "pipeline status trigger started duration actions"
      "pipeline rows    rows    rows    rows     actions";
  }
  .col-headers { display: none; }
}

@media (max-width: 900px) {
  .exec-page { flex-direction: column; }
  .detail-panel {
    width: 100%;
    height: auto;
    max-height: 75dvh;
    position: static;
    border-left: none;
    border-top: 1px solid var(--border-default);
  }
}

@media (max-width: 680px) {
  .exec-main { padding: var(--sp-4); }
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-wrap { max-width: none; }
  .exec-row {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "pipeline actions"
      "status   trigger"
      "rows     duration";
    row-gap: var(--sp-2);
  }
  .stat-div  { display: none; }
  .stats-strip { flex-wrap: wrap; }
  .stat-cell { min-width: 45%; }
}

@media (prefers-reduced-motion: reduce) {
  .exec-row      { animation: none; opacity: 1; transform: none; }
  .exec-skel     { animation: none; }
  .run-sweep     { display: none; }
  .spin          { animation: none; }
  .live-dot      { animation: none; }
}
</style>
