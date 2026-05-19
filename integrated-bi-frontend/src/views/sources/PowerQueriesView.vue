<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  Plus, Search, Play, Trash2, Pencil, X,
  ChevronDown, Database, RefreshCcw, Code2,
  CheckCircle2, Clock, Layers,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
interface PowerQuery {
  id: string
  name: string
  description: string
  sql_query: string
  m_code: string
  query_steps: any[]
  output_schema: any
  is_enabled: boolean
  is_cached: boolean
  cache_ttl_minutes: number
  created_at: string
  updated_at: string
}

// ── State ──────────────────────────────────────────────────
const queries      = ref<PowerQuery[]>([])
const loading      = ref(true)
const listVisible  = ref(false)
const searchQuery  = ref('')
const drawerOpen   = ref(false)
const editQuery    = ref<PowerQuery | null>(null)
const deleteConfirm = ref<string | null>(null)
const submitting   = ref(false)
const runningId    = ref<string | null>(null)
const runResults   = ref<Record<string, any>>({})
const stepsId      = ref<string | null>(null)
const steps        = ref<any[]>([])
const stepsLoading = ref(false)

const form = ref({
  name: '',
  description: '',
  sql_query: '',
  m_code: '',
  is_enabled: true,
  is_cached: false,
  cache_ttl_minutes: 60,
})

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return queries.value.filter(pq =>
    !q || pq.name.toLowerCase().includes(q) || pq.description.toLowerCase().includes(q)
  )
})

const stats = computed(() => ({
  total:   queries.value.length,
  enabled: queries.value.filter(q => q.is_enabled).length,
  cached:  queries.value.filter(q => q.is_cached).length,
}))

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
async function fetchQueries() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/data-sources/power-queries/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    queries.value = rows
  } catch {
    queries.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function executeQuery(pq: PowerQuery) {
  if (runningId.value) return
  runningId.value = pq.id
  try {
    const { data } = await api.post(`/api/data-sources/power-queries/${pq.id}/execute/`, {})
    runResults.value[pq.id] = data
  } catch {
    runResults.value[pq.id] = { error: 'Échec de l\'exécution' }
  } finally {
    runningId.value = null
  }
}

async function loadSteps(pq: PowerQuery) {
  if (stepsId.value === pq.id) { stepsId.value = null; steps.value = []; return }
  stepsId.value = pq.id
  stepsLoading.value = true
  try {
    const { data } = await api.get(`/api/data-sources/power-queries/${pq.id}/steps/`)
    steps.value = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
  } catch {
    steps.value = []
  } finally {
    stepsLoading.value = false
  }
}

async function deleteQuery(id: string) {
  try {
    await api.delete(`/api/data-sources/power-queries/${id}/`)
    queries.value = queries.value.filter(q => q.id !== id)
  } catch { /* ignore */ }
  deleteConfirm.value = null
}

function openDrawer() {
  editQuery.value = null
  form.value = { name: '', description: '', sql_query: '', m_code: '', is_enabled: true, is_cached: false, cache_ttl_minutes: 60 }
  drawerOpen.value = true
}

function openEditDrawer(pq: PowerQuery) {
  editQuery.value = pq
  form.value = {
    name: pq.name, description: pq.description,
    sql_query: pq.sql_query, m_code: pq.m_code,
    is_enabled: pq.is_enabled, is_cached: pq.is_cached,
    cache_ttl_minutes: pq.cache_ttl_minutes,
  }
  drawerOpen.value = true
}

async function submitForm() {
  if (!form.value.name.trim()) return
  submitting.value = true
  const payload = {
    name:               form.value.name,
    description:        form.value.description,
    sql_query:          form.value.sql_query,
    m_code:             form.value.m_code,
    is_enabled:         form.value.is_enabled,
    is_cached:          form.value.is_cached,
    cache_ttl_minutes:  form.value.cache_ttl_minutes,
  }
  try {
    if (editQuery.value) {
      const { data } = await api.patch(`/api/data-sources/power-queries/${editQuery.value.id}/`, payload)
      const idx = queries.value.findIndex(q => q.id === editQuery.value!.id)
      if (idx !== -1) queries.value[idx] = data
    } else {
      const { data } = await api.post('/api/data-sources/power-queries/', payload)
      queries.value = [data, ...queries.value]
    }
    drawerOpen.value = false
    editQuery.value = null
  } catch { /* ignore */ }
  finally { submitting.value = false }
}

onMounted(fetchQueries)
</script>

<template>
  <div class="pq-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Power Queries</h2>
        <p class="page-meta">{{ stats.total }} requête{{ stats.total !== 1 ? 's' : '' }} configurée{{ stats.total !== 1 ? 's' : '' }}</p>
      </div>
      <div class="hd-actions">
        <button class="btn-ghost btn-icon" title="Actualiser" @click="fetchQueries">
          <RefreshCcw :size="14" />
        </button>
        <button class="btn-primary" @click="openDrawer">
          <Plus :size="15" />
          <span>Nouvelle requête</span>
        </button>
      </div>
    </header>

    <!-- ── Stats ─────────────────────────────────────────────── -->
    <section class="stats-strip">
      <div class="stat-cell">
        <Database :size="14" class="sc-icon" />
        <span class="sc-val">{{ stats.total }}</span>
        <span class="sc-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <CheckCircle2 :size="14" class="sc-icon sc-icon--ok" />
        <span class="sc-val sc-val--ok">{{ stats.enabled }}</span>
        <span class="sc-lbl">Activées</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Clock :size="14" class="sc-icon sc-icon--cache" />
        <span class="sc-val sc-val--cache">{{ stats.cached }}</span>
        <span class="sc-lbl">En cache</span>
      </div>
    </section>

    <!-- ── Toolbar ────────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input v-model="searchQuery" type="search" class="search-input" placeholder="Rechercher une requête…" />
      </div>
    </div>

    <!-- ── Loading ────────────────────────────────────────────── -->
    <div v-if="loading" class="pq-list">
      <div v-for="i in 4" :key="i" class="pq-skel"></div>
    </div>

    <!-- ── Empty ──────────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <Code2 :size="40" class="empty-icon" />
      <p class="empty-title">Aucune Power Query</p>
      <p class="empty-sub">Créez des requêtes paramétrées réutilisables sur vos sources de données.</p>
      <button class="btn-primary" @click="openDrawer">
        <Plus :size="14" />
        <span>Nouvelle requête</span>
      </button>
    </div>

    <!-- ── Query list ─────────────────────────────────────────── -->
    <div v-else class="pq-list" :class="{ 'pq-list--visible': listVisible }">
      <div
        v-for="(pq, i) in filtered"
        :key="pq.id"
        class="pq-card"
        :class="{ 'pq-card--disabled': !pq.is_enabled }"
        :style="{ '--ci': i }"
      >
        <!-- Card header -->
        <div class="pq-card-hd">
          <div class="pq-title-row">
            <span class="pq-name">{{ pq.name }}</span>
            <span class="pq-badge" :class="pq.is_enabled ? 'badge--ok' : 'badge--off'">
              {{ pq.is_enabled ? 'Actif' : 'Inactif' }}
            </span>
            <span v-if="pq.is_cached" class="pq-badge badge--cache">
              <Clock :size="9" /> Cache {{ pq.cache_ttl_minutes }}min
            </span>
          </div>
          <div class="pq-actions">
            <button
              class="act-btn act-btn--run"
              title="Exécuter"
              :disabled="runningId === pq.id"
              @click="executeQuery(pq)"
            >
              <span v-if="runningId === pq.id" class="act-spinner"></span>
              <Play v-else :size="12" />
            </button>
            <button
              class="act-btn"
              :class="{ 'act-btn--steps-on': stepsId === pq.id }"
              title="Voir les étapes"
              @click="loadSteps(pq)"
            >
              <Layers :size="12" />
            </button>
            <button class="act-btn" title="Modifier" @click="openEditDrawer(pq)">
              <Pencil :size="12" />
            </button>
            <template v-if="deleteConfirm === pq.id">
              <span class="del-label">Supprimer ?</span>
              <button class="act-btn act-btn--yes" @click="deleteQuery(pq.id)">Oui</button>
              <button class="act-btn" @click="deleteConfirm = null">Non</button>
            </template>
            <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = pq.id">
              <Trash2 :size="12" />
            </button>
          </div>
        </div>

        <!-- Description -->
        <p v-if="pq.description" class="pq-desc">{{ pq.description }}</p>

        <!-- SQL preview -->
        <pre v-if="pq.sql_query" class="pq-sql">{{ pq.sql_query }}</pre>

        <!-- Steps panel -->
        <div v-if="stepsId === pq.id" class="pq-steps">
          <div v-if="stepsLoading" class="steps-loading">
            <span class="spinner steps-spinner"></span>
          </div>
          <div v-else-if="steps.length === 0" class="steps-empty">Aucune étape définie.</div>
          <ol v-else class="steps-list">
            <li v-for="(step, si) in steps" :key="si" class="step-item">
              <span class="step-num">{{ si + 1 }}</span>
              <span class="step-name">{{ step.name || step.action || JSON.stringify(step) }}</span>
            </li>
          </ol>
        </div>

        <!-- Execution result -->
        <div v-if="runResults[pq.id]" class="pq-result">
          <span class="result-label">Résultat :</span>
          <pre class="result-body">{{ JSON.stringify(runResults[pq.id], null, 2) }}</pre>
        </div>

        <!-- Footer -->
        <div class="pq-footer">
          <span class="pq-time"><Clock :size="10" /> {{ timeAgo(pq.updated_at) }}</span>
          <span class="pq-steps-count">{{ pq.query_steps?.length ?? 0 }} étape{{ (pq.query_steps?.length ?? 0) !== 1 ? 's' : '' }}</span>
        </div>
      </div>
    </div>

    <!-- ── Create / Edit drawer ───────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false; editQuery = null">
        <aside class="drawer" role="dialog" aria-modal="true">

          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editQuery ? 'Modifier la requête' : 'Nouvelle Power Query' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false; editQuery = null" aria-label="Fermer">
              <X :size="18" />
            </button>
          </div>

          <form class="drawer-form" @submit.prevent="submitForm">

            <div class="form-field">
              <label class="form-label">Nom <span class="req">*</span></label>
              <input v-model="form.name" class="form-input" type="text" placeholder="Ex : Ventes par région" required />
            </div>

            <div class="form-field">
              <label class="form-label">Description <span class="opt">optionnel</span></label>
              <textarea v-model="form.description" class="form-input form-textarea" placeholder="Description de la requête…" rows="2"></textarea>
            </div>

            <div class="form-field">
              <label class="form-label">Requête SQL</label>
              <textarea v-model="form.sql_query" class="form-input form-textarea form-code" placeholder="SELECT * FROM ..." rows="6" spellcheck="false"></textarea>
            </div>

            <div class="form-field">
              <label class="form-label">Code M (Power Query) <span class="opt">optionnel</span></label>
              <textarea v-model="form.m_code" class="form-input form-textarea form-code" placeholder="let ... in ..." rows="4" spellcheck="false"></textarea>
            </div>

            <div class="pq-form-row">
              <label class="toggle-label">
                <input v-model="form.is_enabled" type="checkbox" class="form-checkbox" />
                <span>Requête active</span>
              </label>
              <label class="toggle-label">
                <input v-model="form.is_cached" type="checkbox" class="form-checkbox" />
                <span>Activer le cache</span>
              </label>
            </div>

            <div v-if="form.is_cached" class="form-field">
              <label class="form-label">Durée du cache (minutes)</label>
              <input v-model.number="form.cache_ttl_minutes" class="form-input" type="number" min="1" max="1440" />
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="drawerOpen = false; editQuery = null">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="!submitting">{{ editQuery ? 'Enregistrer' : 'Créer' }}</span>
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
.pq-page {
  padding: var(--sp-8);
  display: flex; flex-direction: column;
  gap: var(--sp-6); min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title { font-family: var(--font-display); font-size: var(--text-2xl); font-weight: 700; letter-spacing: -0.01em; color: var(--text-primary); line-height: 1.2; }
.page-meta  { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }
.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

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

.btn-ghost {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-secondary); min-height: 40px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover { border-color: var(--border-strong); color: var(--text-primary); }
.btn-icon { padding: var(--sp-2); min-height: unset; width: 40px; height: 40px; justify-content: center; }

/* ── Stats ───────────────────────────────────────────────── */
.stats-strip { display: flex; align-items: center; background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; }
.stat-cell   { flex: 1; display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-4) var(--sp-6); }
.stat-sep    { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.sc-icon       { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--ok   { color: oklch(65% 0.13 148); }
.sc-icon--cache{ color: var(--accent-dim); }
.sc-val        { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.sc-val--ok    { color: oklch(65% 0.13 148); }
.sc-val--cache { color: var(--accent-dim); }
.sc-lbl        { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); }
.search-wrap { position: relative; flex: 1; max-width: 400px; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input {
  width: 100%; height: 40px; padding: 0 var(--sp-4) 0 34px;
  background: var(--surface-raised); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.pq-skel {
  height: 120px; border-radius: var(--radius-lg);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%; animation: shimmer 1.4s infinite;
}

/* ── List ────────────────────────────────────────────────── */
.pq-list {
  display: flex; flex-direction: column; gap: var(--sp-3);
  opacity: 0; transition: opacity 300ms;
}
.pq-list--visible { opacity: 1; }

/* ── Card ────────────────────────────────────────────────── */
.pq-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-4) var(--sp-5);
  display: flex; flex-direction: column; gap: var(--sp-3);
  transition: border-color 200ms, box-shadow 200ms;

  opacity: 0; transform: translateY(6px);
  animation: card-in 280ms var(--ease-out-expo) forwards;
  animation-delay: calc(var(--ci, 0) * 30ms);
}
@keyframes card-in { to { opacity: 1; transform: none; } }
.pq-card:hover { border-color: var(--border-default); box-shadow: 0 4px 20px oklch(5% 0.01 258 / 0.3); }
.pq-card--disabled { opacity: 0.65; }

/* Card header */
.pq-card-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-3); }
.pq-title-row { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.pq-name { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-primary); }
.pq-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em;
}
.badge--ok    { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.badge--off   { background: var(--surface-muted); color: var(--text-muted); }
.badge--cache { background: var(--accent-surface); color: var(--accent-dim); }

/* Actions */
.pq-actions { display: flex; align-items: center; gap: var(--sp-1); flex-shrink: 0; }
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none; color: var(--text-muted);
  cursor: pointer; font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) { background: var(--surface-overlay); border-color: var(--border-default); color: var(--text-secondary); }
.act-btn--run:hover:not(:disabled) { background: oklch(14% 0.05 148); border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }
.act-btn--del:hover:not(:disabled) { background: var(--error-surface); border-color: var(--error); color: var(--error); }
.act-btn--yes { background: var(--error-surface); border-color: var(--error); color: var(--error); width: auto; padding: 0 var(--sp-2); }
.act-btn--steps-on { background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent-dim); }
.act-btn:disabled { opacity: 0.55; cursor: not-allowed; }

@keyframes act-spin { to { transform: rotate(360deg); } }
.act-spinner { display: block; width: 10px; height: 10px; border: 1.5px solid var(--border-default); border-top-color: var(--accent-dim); border-radius: 50%; animation: act-spin 0.7s linear infinite; }

.del-label { font-size: var(--text-xs); color: var(--error); white-space: nowrap; }

/* Content */
.pq-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5; }

.pq-sql {
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3) var(--sp-4);
  font-family: 'Courier New', monospace;
  font-size: var(--text-xs);
  color: var(--accent-dim);
  overflow-x: auto;
  max-height: 120px;
  overflow-y: auto;
  white-space: pre;
  line-height: 1.5;
}

/* Steps */
.pq-steps {
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-3) var(--sp-4);
}
.steps-loading { display: flex; justify-content: center; padding: var(--sp-4); }
.steps-empty   { font-size: var(--text-sm); color: var(--text-muted); text-align: center; padding: var(--sp-3); }
.steps-list { list-style: none; display: flex; flex-direction: column; gap: var(--sp-2); }
.step-item { display: flex; align-items: center; gap: var(--sp-2); }
.step-num { font-family: var(--font-display); font-size: 0.7rem; font-weight: 800; color: var(--accent-dim); min-width: 20px; }
.step-name { font-size: var(--text-sm); color: var(--text-secondary); }

/* Result */
.pq-result { background: var(--surface-overlay); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: var(--sp-3); }
.result-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: var(--sp-2); }
.result-body { font-family: 'Courier New', monospace; font-size: var(--text-xs); color: var(--text-secondary); white-space: pre; overflow-x: auto; max-height: 160px; overflow-y: auto; }

/* Footer */
.pq-footer { display: flex; align-items: center; justify-content: space-between; padding-top: var(--sp-2); border-top: 1px solid var(--border-subtle); }
.pq-time { display: flex; align-items: center; gap: 4px; font-size: var(--text-xs); color: var(--text-muted); }
.pq-steps-count { font-size: var(--text-xs); color: var(--text-muted); }

/* ── Empty state ─────────────────────────────────────────── */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--sp-4); padding: var(--sp-24) var(--sp-8); text-align: center; }
.empty-icon  { color: var(--text-muted); margin-bottom: var(--sp-2); }
.empty-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.empty-sub   { font-size: var(--text-sm); color: var(--text-muted); max-width: 42ch; line-height: 1.6; }

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay { position: fixed; inset: 0; background: oklch(5% 0.01 258 / 0.72); z-index: var(--z-modal); display: flex; justify-content: flex-end; }
.drawer { width: 520px; max-width: 100vw; height: 100dvh; background: var(--surface-raised); border-left: 1px solid var(--border-default); display: flex; flex-direction: column; overflow-y: auto; }
.drawer-hd { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-6); border-bottom: 1px solid var(--border-subtle); flex-shrink: 0; position: sticky; top: 0; background: var(--surface-raised); z-index: 1; }
.drawer-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); }
.drawer-close { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--border-default); background: none; color: var(--text-secondary); cursor: pointer; transition: all 150ms; }
.drawer-close:hover { border-color: var(--border-strong); color: var(--text-primary); }
.drawer-form { display: flex; flex-direction: column; gap: var(--sp-5); padding: var(--sp-6); flex: 1; }
.form-field { display: flex; flex-direction: column; gap: var(--sp-2); }
.form-label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.req { color: var(--accent-dim); }
.opt { font-size: var(--text-xs); font-weight: 400; color: var(--text-muted); margin-left: 4px; }
.form-input { height: 40px; padding: 0 var(--sp-4); background: var(--surface-overlay); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none; transition: border-color 150ms; }
.form-input:focus { border-color: var(--accent-dim); box-shadow: var(--shadow-focus); }
.form-input::placeholder { color: var(--text-muted); }
.form-textarea { height: auto; padding: var(--sp-3) var(--sp-4); resize: vertical; line-height: 1.55; }
.form-code { font-family: 'Courier New', monospace; font-size: var(--text-xs); color: var(--accent-dim); }
.pq-form-row { display: flex; gap: var(--sp-6); }
.form-checkbox { accent-color: var(--accent); width: 14px; height: 14px; cursor: pointer; }
.toggle-label { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--text-sm); color: var(--text-secondary); cursor: pointer; }
.drawer-footer { display: flex; gap: var(--sp-3); justify-content: flex-end; padding-top: var(--sp-4); margin-top: auto; border-top: 1px solid var(--border-subtle); flex-shrink: 0; }

@keyframes spin-sm { to { transform: rotate(360deg); } }
.spinner { display: block; width: 16px; height: 16px; border: 2px solid oklch(14% 0.013 258 / 0.3); border-top-color: var(--text-on-accent); border-radius: 50%; animation: spin-sm 0.7s linear infinite; }
.steps-spinner { width: 20px; height: 20px; border: 2px solid var(--border-default); border-top-color: var(--accent-dim); border-radius: 50%; animation: spin-sm 0.7s linear infinite; display: block; }

.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from, .drawer-anim-leave-to { opacity: 0; }
.drawer-anim-enter-active .drawer { transition: transform 380ms var(--ease-out-expo); }
.drawer-anim-leave-active .drawer { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer, .drawer-anim-leave-to .drawer { transform: translateX(100%); }

@media (prefers-reduced-motion: reduce) {
  .pq-card { animation: none; opacity: 1; transform: none; }
  .pq-skel { animation: none; }
}
</style>
