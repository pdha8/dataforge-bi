<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'

const route = useRoute()
import {
  Search, Plus, Play, Save, Trash2, Pencil, Star,
  RefreshCcw, Database, Code2, FileCode,
  Globe, Zap, X, AlertCircle, Loader2,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
interface DataQuery {
  id: string
  name: string
  description: string
  query_type: string
  query_type_display: string
  query_text: string
  data_source: string
  data_source_name: string
  is_favorite: boolean
  is_public: boolean
  is_cached: boolean
  execution_count: number
  avg_execution_time_ms: number
  last_executed: string | null
  tags: string[]
  created_at: string
}

interface DataSource {
  id: string
  name: string
  source_type?: string
}

interface ExecuteResult {
  columns: string[]
  rows: unknown[][]
  execution_time_ms: number
  row_count: number
  query_hash?: string
}

// ── Constants ──────────────────────────────────────────────
const QUERY_TYPES = [
  { value: 'sql',     label: 'SQL',     icon: '📊' },
  { value: 'nosql',   label: 'NoSQL',   icon: '🍃' },
  { value: 'rest',    label: 'REST',    icon: '🌐' },
  { value: 'graphql', label: 'GraphQL', icon: '⚡' },
  { value: 'soap',    label: 'SOAP',    icon: '🔧' },
  { value: 'custom',  label: 'Custom',  icon: '⚙️' },
]

function typeIcon(qt: string): string {
  return QUERY_TYPES.find(t => t.value === qt)?.icon ?? '📄'
}
function typeLabel(qt: string): string {
  return QUERY_TYPES.find(t => t.value === qt)?.label ?? qt
}

// ── State — list ──────────────────────────────────────────
const queries      = ref<DataQuery[]>([])
const sources      = ref<DataSource[]>([])
const loading      = ref(true)
const listVisible  = ref(false)
const searchQuery  = ref('')
const filterType   = ref('')
const favOnly      = ref(false)
const deleteConfirm = ref<string | null>(null)
const togglingFav  = ref<string | null>(null)
const clearingCache = ref<string | null>(null)

// ── State — editor ────────────────────────────────────────
type EditorMode = 'idle' | 'new' | 'edit'
const mode         = ref<EditorMode>('idle')
const activeQuery  = ref<DataQuery | null>(null)   // query shown in editor (may be unsaved)
const saving       = ref(false)
const executing    = ref(false)
const execResult   = ref<ExecuteResult | null>(null)
const execError    = ref<string | null>(null)

// editor form fields
const edName        = ref('')
const edDesc        = ref('')
const edSource      = ref('')
const edType        = ref('sql')
const edText        = ref('')
const edIsPublic    = ref(false)
const edTags        = ref('')

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  let list = queries.value
  const q = searchQuery.value.toLowerCase().trim()
  if (q) list = list.filter(x => x.name.toLowerCase().includes(q) || x.data_source_name?.toLowerCase().includes(q))
  if (filterType.value) list = list.filter(x => x.query_type === filterType.value)
  if (favOnly.value) list = list.filter(x => x.is_favorite)
  return list
})

const editorActive = computed(() => mode.value !== 'idle')

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Jamais'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs} h`
  return `${Math.floor(hrs / 24)} j`
}

function formatMs(ms: number | null): string {
  if (!ms) return '—'
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(2)} s`
}

function isSelected(q: DataQuery): boolean {
  return activeQuery.value?.id === q.id
}

// ── API — list ────────────────────────────────────────────
async function fetchQueries() {
  loading.value = true
  listVisible.value = false
  try {
    const params: Record<string, unknown> = { page: 1, per_page: 50 }
    const { data } = await api.get('/api/data-sources/queries/', { params })
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    queries.value = rows
  } catch {
    queries.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function fetchSources() {
  try {
    const { data } = await api.get('/api/data-sources/sources/')
    sources.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    sources.value = []
  }
}

async function toggleFavorite(q: DataQuery) {
  if (togglingFav.value) return
  togglingFav.value = q.id
  try {
    await api.post(`/api/data-sources/queries/${q.id}/toggle_favorite/`)
    const idx = queries.value.findIndex(x => x.id === q.id)
    if (idx !== -1) queries.value[idx] = { ...queries.value[idx], is_favorite: !queries.value[idx].is_favorite }
    if (activeQuery.value?.id === q.id) {
      activeQuery.value = { ...activeQuery.value, is_favorite: !activeQuery.value.is_favorite }
    }
  } catch { /* ignore */ }
  finally { togglingFav.value = null }
}

async function deleteQuery(id: string) {
  try {
    await api.delete(`/api/data-sources/queries/${id}/`)
    queries.value = queries.value.filter(q => q.id !== id)
    if (activeQuery.value?.id === id) closeEditor()
  } catch { /* ignore */ }
  deleteConfirm.value = null
}

async function clearCache(q: DataQuery) {
  if (clearingCache.value) return
  clearingCache.value = q.id
  try {
    await api.post(`/api/data-sources/queries/${q.id}/clear_cache/`)
    const idx = queries.value.findIndex(x => x.id === q.id)
    if (idx !== -1) queries.value[idx] = { ...queries.value[idx], is_cached: false }
    if (activeQuery.value?.id === q.id) activeQuery.value = { ...activeQuery.value, is_cached: false }
  } catch { /* ignore */ }
  finally { clearingCache.value = null }
}

// ── Editor ────────────────────────────────────────────────
function openNew() {
  mode.value = 'new'
  activeQuery.value = null
  edName.value = ''
  edDesc.value = ''
  edSource.value = sources.value[0]?.id ?? ''
  edType.value = 'sql'
  edText.value = ''
  edIsPublic.value = false
  edTags.value = ''
  execResult.value = null
  execError.value = null
}

function openEdit(q: DataQuery) {
  mode.value = 'edit'
  activeQuery.value = q
  edName.value = q.name
  edDesc.value = q.description ?? ''
  edSource.value = q.data_source ?? ''
  edType.value = q.query_type ?? 'sql'
  edText.value = q.query_text ?? ''
  edIsPublic.value = q.is_public ?? false
  edTags.value = (q.tags ?? []).join(', ')
  execResult.value = null
  execError.value = null
}

function selectQuery(q: DataQuery) {
  openEdit(q)
}

function closeEditor() {
  mode.value = 'idle'
  activeQuery.value = null
  execResult.value = null
  execError.value = null
}

async function saveQuery() {
  if (!edName.value.trim()) return
  saving.value = true
  const payload = {
    name:        edName.value.trim(),
    description: edDesc.value.trim(),
    data_source: edSource.value || null,
    query_type:  edType.value,
    query_text:  edText.value,
    is_public:   edIsPublic.value,
    tags:        edTags.value ? edTags.value.split(',').map(t => t.trim()).filter(Boolean) : [],
  }
  try {
    if (mode.value === 'edit' && activeQuery.value) {
      const { data } = await api.patch(`/api/data-sources/queries/${activeQuery.value.id}/`, payload)
      const idx = queries.value.findIndex(q => q.id === activeQuery.value!.id)
      if (idx !== -1) queries.value[idx] = data
      activeQuery.value = data
    } else {
      const { data } = await api.post('/api/data-sources/queries/', payload)
      queries.value = [data, ...queries.value]
      activeQuery.value = data
      mode.value = 'edit'
    }
  } catch { /* ignore */ }
  finally { saving.value = false }
}

async function executeQuery() {
  if (executing.value) return
  if (!activeQuery.value && mode.value !== 'edit') return
  // If editing an existing query, execute it
  if (!activeQuery.value) return
  executing.value = true
  execResult.value = null
  execError.value = null
  try {
    const { data } = await api.post(`/api/data-sources/queries/${activeQuery.value.id}/execute/`, { params: [] })
    execResult.value = data
    // refresh stats on the card
    const idx = queries.value.findIndex(q => q.id === activeQuery.value!.id)
    if (idx !== -1) {
      queries.value[idx] = {
        ...queries.value[idx],
        execution_count: (queries.value[idx].execution_count ?? 0) + 1,
        last_executed: new Date().toISOString(),
        avg_execution_time_ms: data.execution_time_ms ?? queries.value[idx].avg_execution_time_ms,
      }
    }
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; error?: string } }; message?: string }
    execError.value = e?.response?.data?.detail ?? e?.response?.data?.error ?? e?.message ?? 'Erreur d\'exécution'
  } finally {
    executing.value = false
  }
}

// ── Quick execute from list (without opening editor) ──────
const quickRunId  = ref<string | null>(null)
const quickResult = ref<Record<string, ExecuteResult | { error: string }>>({})

async function quickExecute(q: DataQuery) {
  if (quickRunId.value) return
  quickRunId.value = q.id
  try {
    const { data } = await api.post(`/api/data-sources/queries/${q.id}/execute/`, { params: [] })
    quickResult.value[q.id] = data
    const idx = queries.value.findIndex(x => x.id === q.id)
    if (idx !== -1) {
      queries.value[idx] = {
        ...queries.value[idx],
        execution_count: (queries.value[idx].execution_count ?? 0) + 1,
        last_executed: new Date().toISOString(),
        avg_execution_time_ms: data.execution_time_ms ?? queries.value[idx].avg_execution_time_ms,
      }
    }
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    quickResult.value[q.id] = { error: e?.response?.data?.detail ?? e?.message ?? 'Erreur' }
  } finally {
    quickRunId.value = null
  }
}

// ── Mount ─────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([fetchQueries(), fetchSources()])

  // Préremplissage depuis SourceMonitoringView : /queries?open=new&source=…&hint=…&from_log=…
  if (route.query.open === 'new') {
    openNew()
    const srcParam = String(route.query.source || '').trim()
    if (srcParam) {
      // si on a un nom de source, on tente de le résoudre en id via la liste chargée
      const match = sources.value.find(s => s.name === srcParam || String(s.id) === srcParam)
      if (match) edSource.value = match.id
    }
    const hint = String(route.query.hint || '').trim()
    const fromLog = String(route.query.from_log || '').trim()
    if (hint || fromLog) {
      const prefix = fromLog ? `-- Requête générée depuis le log #${fromLog}\n` : ''
      const body   = hint ? `-- Contexte : ${hint}\n\n` : ''
      edText.value = `${prefix}${body}SELECT *\nFROM ${srcParam || 'ma_table'}\nLIMIT 100;`
      if (!edName.value && srcParam) edName.value = `Requête ${srcParam} ${new Date().toLocaleDateString('fr-FR')}`
    }
  }
})
</script>

<template>
  <div class="qv-page">

    <!-- ── Page header ──────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Requêtes SQL</h2>
        <p class="page-meta">{{ queries.length }} requête{{ queries.length !== 1 ? 's' : '' }} enregistrée{{ queries.length !== 1 ? 's' : '' }}</p>
      </div>
      <div class="hd-actions">
        <button class="btn-ghost btn-icon" title="Actualiser" @click="fetchQueries">
          <RefreshCcw :size="14" />
        </button>
        <button class="btn-primary" @click="openNew">
          <Plus :size="15" />
          <span>Nouvelle requête</span>
        </button>
      </div>
    </header>

    <!-- ── 2-column layout ──────────────────────────────────── -->
    <div class="qv-layout">

      <!-- ══ Left column — Query list ═══════════════════════ -->
      <aside class="qv-left panel">

        <!-- Toolbar -->
        <div class="toolbar">
          <div class="search-wrap">
            <Search :size="13" class="search-icon" />
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Rechercher…"
            />
          </div>
          <select v-model="filterType" class="form-select form-select--sm">
            <option value="">Tous types</option>
            <option v-for="t in QUERY_TYPES" :key="t.value" :value="t.value">{{ t.icon }} {{ t.label }}</option>
          </select>
          <button
            class="fav-toggle"
            :class="{ 'fav-toggle--on': favOnly }"
            title="Favoris seulement"
            @click="favOnly = !favOnly"
          >
            <Star :size="14" :fill="favOnly ? 'currentColor' : 'none'" />
          </button>
        </div>

        <!-- Skeleton -->
        <div v-if="loading" class="card-list">
          <div v-for="i in 5" :key="i" class="q-skel"></div>
        </div>

        <!-- Empty -->
        <div v-else-if="filtered.length === 0" class="list-empty">
          <FileCode :size="32" class="empty-icon" />
          <p class="empty-title">Aucune requête</p>
          <p class="empty-sub">Créez votre première requête pour commencer.</p>
          <button class="btn-primary btn--sm" @click="openNew">
            <Plus :size="13" />
            <span>Nouvelle</span>
          </button>
        </div>

        <!-- Cards list -->
        <div v-else class="card-list" :class="{ 'card-list--visible': listVisible }">
          <div
            v-for="(q, i) in filtered"
            :key="q.id"
            class="q-card"
            :class="{ 'q-card--active': isSelected(q) }"
            :style="{ '--ci': i }"
            @click="selectQuery(q)"
          >
            <!-- Card top row -->
            <div class="q-card-hd">
              <span class="q-type-icon">{{ typeIcon(q.query_type) }}</span>
              <div class="q-name-wrap">
                <span class="q-name">{{ q.name }}</span>
                <span class="q-source">{{ q.data_source_name || '—' }}</span>
              </div>
              <span class="q-badge">{{ typeLabel(q.query_type) }}</span>
            </div>

            <!-- Stats row -->
            <div class="q-stats">
              <span class="q-stat">
                <Play :size="9" />
                {{ q.execution_count ?? 0 }} exec
              </span>
              <span class="q-stat-sep">·</span>
              <span class="q-stat">{{ formatMs(q.avg_execution_time_ms) }} moy</span>
              <span class="q-stat-sep">·</span>
              <span class="q-stat">{{ timeAgo(q.last_executed) }}</span>
            </div>

            <!-- Quick result snippet (from quick execute) -->
            <div v-if="quickResult[q.id]" class="q-quick-result" @click.stop>
              <template v-if="'error' in quickResult[q.id]">
                <span class="q-quick-err">{{ (quickResult[q.id] as { error: string }).error }}</span>
              </template>
              <template v-else>
                <span class="q-quick-ok">
                  {{ (quickResult[q.id] as ExecuteResult).row_count }} lignes en
                  {{ formatMs((quickResult[q.id] as ExecuteResult).execution_time_ms) }}
                </span>
              </template>
            </div>

            <!-- Actions row -->
            <div class="q-actions" @click.stop>
              <!-- Favorite -->
              <button
                class="act-btn"
                :class="{ 'act-btn--fav-on': q.is_favorite }"
                :disabled="togglingFav === q.id"
                title="Favori"
                @click="toggleFavorite(q)"
              >
                <Star :size="12" :fill="q.is_favorite ? 'currentColor' : 'none'" />
              </button>
              <!-- Quick execute -->
              <button
                class="act-btn act-btn--run"
                :disabled="quickRunId === q.id"
                title="Exécuter"
                @click="quickExecute(q)"
              >
                <span v-if="quickRunId === q.id" class="act-spinner"></span>
                <Play v-else :size="12" />
              </button>
              <!-- Edit -->
              <button class="act-btn" title="Modifier" @click="openEdit(q)">
                <Pencil :size="12" />
              </button>
              <!-- Delete -->
              <template v-if="deleteConfirm === q.id">
                <span class="del-lbl">Supprimer ?</span>
                <button class="act-btn act-btn--yes" @click="deleteQuery(q.id)">Oui</button>
                <button class="act-btn" @click="deleteConfirm = null">Non</button>
              </template>
              <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = q.id">
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
        </div>

      </aside>

      <!-- ══ Right column — Editor ═══════════════════════════ -->
      <section class="qv-right panel">

        <!-- Idle placeholder -->
        <div v-if="mode === 'idle'" class="editor-idle">
          <Code2 :size="48" class="idle-icon" />
          <p class="idle-title">Sélectionner ou créer une requête</p>
          <p class="idle-sub">Choisissez une requête dans la liste ou créez-en une nouvelle pour l'éditer et l'exécuter ici.</p>
          <button class="btn-primary" @click="openNew">
            <Plus :size="14" />
            <span>Nouvelle requête</span>
          </button>
        </div>

        <!-- Active editor -->
        <template v-else>

          <!-- Editor header -->
          <div class="editor-hd">
            <div class="editor-hd-fields">
              <input
                v-model="edName"
                class="form-input ed-name-input"
                type="text"
                placeholder="Nom de la requête *"
                required
              />
              <select v-model="edSource" class="form-select">
                <option value="">Source de données…</option>
                <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
              <select v-model="edType" class="form-select">
                <option v-for="t in QUERY_TYPES" :key="t.value" :value="t.value">{{ t.icon }} {{ t.label }}</option>
              </select>
            </div>
            <button class="btn-ghost btn-icon editor-close" title="Fermer l'éditeur" @click="closeEditor">
              <X :size="16" />
            </button>
          </div>

          <!-- Description -->
          <div class="editor-desc-wrap">
            <textarea
              v-model="edDesc"
              class="form-input form-textarea ed-desc"
              placeholder="Description (optionnel)…"
              rows="2"
            ></textarea>
          </div>

          <!-- Query text editor -->
          <div class="ed-code-wrap">
            <label class="ed-code-label">
              <Database :size="11" />
              Requête {{ typeLabel(edType) }}
            </label>
            <textarea
              v-model="edText"
              class="form-input form-textarea ed-code"
              :placeholder="edType === 'sql' ? 'SELECT * FROM table WHERE ...' : 'Saisissez la requête...'"
              rows="10"
              spellcheck="false"
            ></textarea>
          </div>

          <!-- Public + tags -->
          <div class="ed-meta-row">
            <label class="toggle-label">
              <input v-model="edIsPublic" type="checkbox" class="form-checkbox" />
              <span>Publique</span>
            </label>
            <div class="ed-tags-wrap">
              <Globe :size="11" class="tags-icon" />
              <input
                v-model="edTags"
                class="form-input ed-tags-input"
                type="text"
                placeholder="Tags séparés par virgule…"
              />
            </div>
          </div>

          <!-- Editor action buttons -->
          <div class="editor-actions">
            <button
              class="btn-run"
              :disabled="executing || !activeQuery"
              :title="!activeQuery ? 'Enregistrez d\'abord pour exécuter' : 'Exécuter la requête'"
              @click="executeQuery"
            >
              <span v-if="executing" class="btn-spinner"></span>
              <Play v-else :size="14" />
              <span>{{ executing ? 'Exécution…' : 'Exécuter' }}</span>
            </button>
            <button
              class="btn-save"
              :disabled="saving || !edName.trim()"
              @click="saveQuery"
            >
              <span v-if="saving" class="btn-spinner btn-spinner--save"></span>
              <Save v-else :size="14" />
              <span>{{ saving ? 'Enregistrement…' : 'Enregistrer' }}</span>
            </button>
            <button
              v-if="activeQuery?.is_cached"
              class="btn-ghost btn--sm"
              :disabled="clearingCache === activeQuery?.id"
              title="Vider le cache"
              @click="activeQuery && clearCache(activeQuery)"
            >
              <Zap :size="13" />
              <span>Vider le cache</span>
            </button>
          </div>

          <!-- Results panel -->
          <div class="results-panel">

            <!-- Loading -->
            <div v-if="executing" class="results-loading">
              <Loader2 :size="22" class="results-spinner" />
              <span>Exécution en cours…</span>
            </div>

            <!-- Error -->
            <div v-else-if="execError" class="results-error">
              <AlertCircle :size="16" />
              <span>{{ execError }}</span>
            </div>

            <!-- Results table -->
            <template v-else-if="execResult">
              <div class="results-meta">
                <span class="results-badge">
                  {{ execResult.row_count }} ligne{{ execResult.row_count !== 1 ? 's' : '' }}
                  en {{ formatMs(execResult.execution_time_ms) }}
                </span>
                <span v-if="execResult.query_hash" class="results-hash">hash: {{ execResult.query_hash.slice(0, 8) }}…</span>
              </div>
              <div class="results-table-wrap">
                <table class="results-table">
                  <thead>
                    <tr>
                      <th v-for="col in execResult.columns" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in execResult.rows.slice(0, 100)" :key="ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell !== null && cell !== undefined ? String(cell) : 'null' }}</td>
                    </tr>
                  </tbody>
                </table>
                <p v-if="execResult.row_count > 100" class="results-truncated">
                  Affichage limité à 100 lignes ({{ execResult.row_count }} au total)
                </p>
              </div>
            </template>

            <!-- Placeholder -->
            <div v-else class="results-placeholder">
              <Play :size="16" class="ph-icon" />
              <span>Les résultats apparaîtront ici après exécution</span>
            </div>

          </div>
        </template>

      </section>

    </div>

  </div>
</template>

<style scoped>
/* ── Page ────────────────────────────────────────────────── */
.qv-page {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
  min-height: 100%;
  box-sizing: border-box;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}
.page-meta { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }
.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

/* ── 2-column layout ─────────────────────────────────────── */
.qv-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--sp-4);
  flex: 1;
  min-height: 0;
  align-items: start;
}

.panel {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* ── Left panel ──────────────────────────────────────────── */
.qv-left {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-4);
  position: sticky;
  top: var(--sp-4);
  max-height: calc(100dvh - 140px);
  overflow-y: auto;
}

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 100px; }
.search-icon { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input {
  width: 100%; height: 34px;
  padding: 0 var(--sp-3) 0 30px;
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  outline: none;
  transition: border-color 150ms;
  box-sizing: border-box;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.form-select {
  height: 34px;
  padding: 0 var(--sp-3);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  outline: none;
  cursor: pointer;
  transition: border-color 150ms;
}
.form-select:focus { border-color: var(--accent-dim); }
.form-select--sm { max-width: 110px; }

.fav-toggle {
  display: flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; flex-shrink: 0;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 150ms;
}
.fav-toggle:hover { border-color: oklch(76% 0.14 62); color: oklch(76% 0.14 62); }
.fav-toggle--on { background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent); }

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.q-skel {
  height: 96px; border-radius: var(--radius-md); flex-shrink: 0;
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

/* ── Card list ───────────────────────────────────────────── */
.card-list {
  display: flex; flex-direction: column; gap: var(--sp-2);
  opacity: 0; transition: opacity 300ms;
}
.card-list--visible { opacity: 1; }

/* ── Query card ──────────────────────────────────────────── */
.q-card {
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3);
  display: flex; flex-direction: column; gap: var(--sp-2);
  cursor: pointer;
  transition: border-color 150ms, box-shadow 150ms, background 150ms;
  opacity: 0; transform: translateY(4px);
  animation: card-in 260ms var(--ease-out-expo, cubic-bezier(0.16,1,0.3,1)) forwards;
  animation-delay: calc(var(--ci, 0) * 25ms);
}
@keyframes card-in { to { opacity: 1; transform: none; } }
.q-card:hover { border-color: var(--border-default); box-shadow: 0 2px 12px oklch(5% 0.01 258 / 0.25); }
.q-card--active {
  border-color: var(--accent-dim);
  background: var(--accent-surface);
  box-shadow: 0 0 0 1px var(--accent-dim);
}

/* Card header */
.q-card-hd { display: flex; align-items: center; gap: var(--sp-2); }
.q-type-icon { font-size: 1rem; line-height: 1; flex-shrink: 0; }
.q-name-wrap { flex: 1; min-width: 0; }
.q-name { display: block; font-family: var(--font-display); font-size: var(--text-sm); font-weight: 700; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.q-source { display: block; font-size: 0.68rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 1px; }
.q-badge {
  padding: 2px 7px; border-radius: var(--radius-full);
  font-size: 0.6rem; font-weight: 700; letter-spacing: 0.04em;
  background: var(--surface-muted); color: var(--text-muted);
  white-space: nowrap; flex-shrink: 0;
}
.q-card--active .q-badge { background: oklch(14% 0.06 62 / 0.5); color: var(--accent-dim); }

/* Stats */
.q-stats { display: flex; align-items: center; gap: 4px; }
.q-stat { display: flex; align-items: center; gap: 3px; font-size: 0.65rem; color: var(--text-muted); }
.q-stat-sep { color: var(--border-default); font-size: 0.65rem; }

/* Quick result */
.q-quick-result { padding: var(--sp-1) var(--sp-2); border-radius: var(--radius-sm); font-size: 0.65rem; }
.q-quick-ok { color: oklch(65% 0.13 148); font-weight: 600; }
.q-quick-err { color: var(--error); font-weight: 600; }

/* Actions */
.q-actions { display: flex; align-items: center; gap: 3px; }
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: none; color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) { background: var(--surface-muted); border-color: var(--border-default); color: var(--text-secondary); }
.act-btn--fav-on { color: oklch(76% 0.14 62); }
.act-btn--fav-on:hover:not(:disabled) { background: oklch(14% 0.05 62); border-color: oklch(76% 0.14 62 / 0.5); }
.act-btn--run:hover:not(:disabled) { background: oklch(14% 0.05 148); border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }
.act-btn--del:hover:not(:disabled) { background: var(--error-surface); border-color: var(--error); color: var(--error); }
.act-btn--yes { background: var(--error-surface); border-color: var(--error); color: var(--error); width: auto; padding: 0 var(--sp-2); }
.act-btn:disabled { opacity: 0.5; cursor: not-allowed; }
@keyframes act-spin { to { transform: rotate(360deg); } }
.act-spinner { display: block; width: 9px; height: 9px; border: 1.5px solid var(--border-default); border-top-color: oklch(65% 0.13 148); border-radius: 50%; animation: act-spin 0.6s linear infinite; }
.del-lbl { font-size: 0.68rem; color: var(--error); white-space: nowrap; }

/* List empty */
.list-empty { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-10) var(--sp-4); text-align: center; }
.empty-icon  { color: var(--text-muted); }
.empty-title { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-secondary); }
.empty-sub   { font-size: var(--text-xs); color: var(--text-muted); line-height: 1.5; }

/* ── Right panel ─────────────────────────────────────────── */
.qv-right {
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

/* ── Editor idle ─────────────────────────────────────────── */
.editor-idle {
  flex: 1;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: var(--sp-4); padding: var(--sp-12); text-align: center;
}
.idle-icon  { color: var(--text-muted); margin-bottom: var(--sp-2); }
.idle-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.idle-sub   { font-size: var(--text-sm); color: var(--text-muted); max-width: 38ch; line-height: 1.6; }

/* ── Editor header ───────────────────────────────────────── */
.editor-hd {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.editor-hd-fields { display: flex; align-items: center; gap: var(--sp-3); flex: 1; flex-wrap: wrap; }
.ed-name-input { flex: 1; min-width: 140px; height: 36px; font-weight: 600; }
.editor-close { flex-shrink: 0; }

/* ── Editor desc ─────────────────────────────────────────── */
.editor-desc-wrap {
  padding: var(--sp-4) var(--sp-5) 0;
}
.ed-desc { resize: none; line-height: 1.5; }

/* ── Code editor ─────────────────────────────────────────── */
.ed-code-wrap {
  padding: var(--sp-3) var(--sp-5);
  display: flex; flex-direction: column; gap: var(--sp-2);
  flex: 1;
}
.ed-code-label {
  display: flex; align-items: center; gap: var(--sp-1);
  font-size: var(--text-xs); font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.ed-code {
  font-family: 'Courier New', 'Cascadia Code', 'Fira Code', monospace;
  font-size: var(--text-sm);
  color: var(--accent-dim);
  line-height: 1.65;
  min-height: 200px;
  resize: vertical;
  tab-size: 2;
}

/* ── Meta row ────────────────────────────────────────────── */
.ed-meta-row {
  display: flex; align-items: center; gap: var(--sp-4);
  padding: 0 var(--sp-5) var(--sp-3);
  flex-wrap: wrap;
}
.toggle-label {
  display: flex; align-items: center; gap: var(--sp-2);
  font-size: var(--text-sm); color: var(--text-secondary);
  cursor: pointer; white-space: nowrap;
}
.form-checkbox { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
.ed-tags-wrap { display: flex; align-items: center; gap: var(--sp-2); flex: 1; }
.tags-icon { color: var(--text-muted); flex-shrink: 0; }
.ed-tags-input { flex: 1; height: 32px; font-size: var(--text-xs); }

/* ── Editor actions ──────────────────────────────────────── */
.editor-actions {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.btn-run {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: oklch(14% 0.05 148);
  border: 1px solid oklch(65% 0.13 148 / 0.5);
  color: oklch(65% 0.13 148);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 600;
  min-height: 36px;
  transition: all 150ms;
}
.btn-run:hover:not(:disabled) { background: oklch(20% 0.07 148); border-color: oklch(65% 0.13 148); box-shadow: 0 2px 10px oklch(65% 0.13 148 / 0.2); }
.btn-run:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-save {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent);
  border: none;
  color: var(--text-on-accent);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 600;
  min-height: 36px;
  transition: all 150ms;
}
.btn-save:hover:not(:disabled) { background: oklch(80% 0.14 62); box-shadow: var(--shadow-accent); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes spin-btn { to { transform: rotate(360deg); } }
.btn-spinner {
  display: block; width: 14px; height: 14px;
  border: 2px solid oklch(65% 0.13 148 / 0.3);
  border-top-color: oklch(65% 0.13 148);
  border-radius: 50%;
  animation: spin-btn 0.7s linear infinite;
}
.btn-spinner--save {
  border-color: oklch(14% 0.013 258 / 0.3);
  border-top-color: var(--text-on-accent);
}

/* ── Results panel ───────────────────────────────────────── */
.results-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  overflow: hidden;
}

.results-loading {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: var(--sp-3); color: var(--text-muted); font-size: var(--text-sm);
}
@keyframes results-spin { to { transform: rotate(360deg); } }
.results-spinner { animation: results-spin 1s linear infinite; color: var(--accent-dim); }

.results-error {
  flex: 1; display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-5) var(--sp-5);
  color: var(--error);
  font-size: var(--text-sm);
  font-weight: 500;
  background: var(--error-surface);
}

.results-placeholder {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: var(--sp-2); color: var(--text-muted); font-size: var(--text-sm);
  padding: var(--sp-8);
}
.ph-icon { opacity: 0.5; }

.results-meta {
  display: flex; align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.results-badge {
  padding: 3px 10px; border-radius: var(--radius-full);
  background: oklch(14% 0.04 148); color: oklch(65% 0.13 148);
  font-size: var(--text-xs); font-weight: 700;
}
.results-hash { font-size: var(--text-xs); color: var(--text-muted); font-family: monospace; }

.results-table-wrap {
  overflow: auto;
  flex: 1;
}
.results-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
}
.results-table th {
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-overlay);
  color: var(--text-muted);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
  position: sticky; top: 0; z-index: 1;
}
.results-table td {
  padding: var(--sp-2) var(--sp-3);
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-subtle);
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.results-table tr:last-child td { border-bottom: none; }
.results-table tr:hover td { background: var(--surface-overlay); color: var(--text-primary); }
.results-truncated {
  padding: var(--sp-3) var(--sp-5);
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-align: center;
  border-top: 1px solid var(--border-subtle);
}

/* ── Shared form inputs ──────────────────────────────────── */
.form-input {
  height: 36px;
  padding: 0 var(--sp-3);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color 150ms;
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--accent-dim); box-shadow: var(--shadow-focus); }
.form-input::placeholder { color: var(--text-muted); }
.form-textarea { height: auto; padding: var(--sp-3) var(--sp-3); resize: vertical; line-height: 1.55; }

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent); color: var(--text-on-accent);
  border: none; border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 600;
  min-height: 40px; white-space: nowrap;
  transition: background 150ms, box-shadow 150ms;
}
.btn-primary:hover:not(:disabled) { background: oklch(80% 0.14 62); box-shadow: var(--shadow-accent); }
.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--sm { min-height: 32px; padding: var(--sp-1) var(--sp-3); font-size: var(--text-xs); }

.btn-ghost {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-secondary); min-height: 40px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover:not(:disabled) { border-color: var(--border-strong); color: var(--text-primary); }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-icon { padding: var(--sp-2); min-height: unset; width: 36px; height: 36px; justify-content: center; }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 900px) {
  .qv-layout { grid-template-columns: 1fr; }
  .qv-left { position: static; max-height: 380px; }
}

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .q-card { animation: none; opacity: 1; transform: none; }
  .q-skel { animation: none; }
}
</style>
