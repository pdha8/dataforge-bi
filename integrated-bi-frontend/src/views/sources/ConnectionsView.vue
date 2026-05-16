<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  Plug, Search, Plus, RefreshCcw, Trash2, Pencil, X,
  ChevronDown, CheckCircle2, XCircle, AlertTriangle,
  Database, Activity,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
interface DBConnection {
  id: string
  name: string
  connection_type: string
  host: string
  port: number | null
  database_name: string
  username: string
  is_active: boolean
  is_verified: boolean
  last_tested: string | null
  created_at: string
  description: string
}

const CONN_TYPES = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql',      label: 'MySQL' },
  { value: 'mssql',      label: 'SQL Server' },
  { value: 'oracle',     label: 'Oracle' },
  { value: 'sqlite',     label: 'SQLite' },
  { value: 'mongodb',    label: 'MongoDB' },
  { value: 'redis',      label: 'Redis' },
  { value: 'other',      label: 'Autre' },
]

// ── State ──────────────────────────────────────────────────
const connections  = ref<DBConnection[]>([])
const loading      = ref(true)
const listVisible  = ref(false)
const refreshing   = ref(false)
const searchQuery  = ref('')
const filterType   = ref('all')

const drawerOpen   = ref(false)
const submitting   = ref(false)
const formError    = ref<string | null>(null)
const editConn     = ref<DBConnection | null>(null)
const deleteConfirm = ref<string | null>(null)
const testingId    = ref<string | null>(null)
const testResults  = ref<Record<string, 'ok' | 'fail'>>({})

const form = ref({
  name: '',
  connection_type: 'postgresql',
  host: '',
  port: '',
  database_name: '',
  username: '',
  password: '',
  description: '',
  is_active: true,
})

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return connections.value.filter(c => {
    const matchSearch = !q || c.name.toLowerCase().includes(q) || c.host.toLowerCase().includes(q) || c.database_name.toLowerCase().includes(q)
    const matchType = filterType.value === 'all' || c.connection_type === filterType.value
    return matchSearch && matchType
  })
})

const stats = computed(() => ({
  total:    connections.value.length,
  active:   connections.value.filter(c => c.is_active).length,
  verified: connections.value.filter(c => c.is_verified).length,
  inactive: connections.value.filter(c => !c.is_active).length,
}))

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Jamais'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function connTypeLabel(t: string): string {
  return CONN_TYPES.find(c => c.value === t)?.label ?? t
}

// ── API ────────────────────────────────────────────────────
async function fetchConnections() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/data-sources/connections/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    connections.value = rows.map((c: any): DBConnection => ({
      id:              c.id,
      name:            c.data_source_name || c.name || c.host || '',
      connection_type: c.connection_type || c.db_type || 'postgresql',
      host:            c.host || '',
      port:            c.port ?? null,
      database_name:   c.database_name || c.database || '',
      username:        c.username || '',
      is_active:       c.is_active ?? true,
      is_verified:     c.is_verified ?? false,
      last_tested:     c.last_tested ?? null,
      created_at:      c.created_at || new Date().toISOString(),
      description:     c.description || '',
    }))
  } catch {
    connections.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function refresh() {
  refreshing.value = true
  await fetchConnections()
  refreshing.value = false
}

function openDrawer(conn?: DBConnection) {
  editConn.value = conn ?? null
  formError.value = null
  if (conn) {
    form.value = {
      name:            conn.name,
      connection_type: conn.connection_type,
      host:            conn.host,
      port:            conn.port != null ? String(conn.port) : '',
      database_name:   conn.database_name,
      username:        conn.username,
      password:        '',
      description:     conn.description,
      is_active:       conn.is_active,
    }
  } else {
    form.value = {
      name: '', connection_type: 'postgresql', host: '', port: '',
      database_name: '', username: '', password: '', description: '', is_active: true,
    }
  }
  drawerOpen.value = true
}

async function submitForm() {
  if (!form.value.name.trim() || !form.value.host.trim()) return
  submitting.value = true
  formError.value = null
  const payload: Record<string, any> = {
    name:            form.value.name.trim(),
    connection_type: form.value.connection_type,
    host:            form.value.host.trim(),
    database_name:   form.value.database_name.trim(),
    username:        form.value.username.trim(),
    description:     form.value.description.trim(),
    is_active:       form.value.is_active,
  }
  if (form.value.port) payload.port = parseInt(form.value.port)
  if (form.value.password) payload.password = form.value.password
  try {
    if (editConn.value) {
      await api.patch(`/api/data-sources/connections/${editConn.value.id}/`, payload)
    } else {
      await api.post('/api/data-sources/connections/', payload)
    }
    drawerOpen.value = false
    editConn.value = null
    await fetchConnections()
  } catch (err: any) {
    formError.value = err?.response?.data?.detail ?? err?.response?.data?.message ?? 'Erreur lors de la sauvegarde.'
  } finally {
    submitting.value = false
  }
}

async function testConnection(id: string) {
  testingId.value = id
  try {
    await api.post(`/api/data-sources/connections/${id}/test/`)
    testResults.value[id] = 'ok'
    const idx = connections.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      connections.value[idx].is_verified = true
      connections.value[idx].last_tested = new Date().toISOString()
    }
  } catch {
    testResults.value[id] = 'fail'
  } finally {
    testingId.value = null
    setTimeout(() => { delete testResults.value[id] }, 4000)
  }
}

async function deleteConnection(id: string) {
  try {
    await api.delete(`/api/data-sources/connections/${id}/`)
    connections.value = connections.value.filter(c => c.id !== id)
  } catch { /* ignore */ } finally {
    deleteConfirm.value = null
  }
}

onMounted(fetchConnections)
</script>

<template>
  <div class="conn-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Connexions base de données</h2>
        <p class="page-meta">{{ stats.total }} connexion{{ stats.total !== 1 ? 's' : '' }} configurée{{ stats.total !== 1 ? 's' : '' }}</p>
      </div>
      <div class="hd-actions">
        <button class="btn-ghost btn-icon" :class="{ 'btn-icon--spin': refreshing }" :disabled="refreshing" @click="refresh">
          <RefreshCcw :size="14" />
        </button>
        <button class="btn-primary" @click="openDrawer()">
          <Plus :size="15" />
          <span>Nouvelle connexion</span>
        </button>
      </div>
    </header>

    <!-- ── Stats ───────────────────────────────────────────── -->
    <section class="stats-rail">
      <div class="stat-cell">
        <Plug :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.total }}</span>
        <span class="sc-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Activity :size="15" class="sc-icon sc-icon--ok" />
        <span class="sc-val sc-val--ok">{{ stats.active }}</span>
        <span class="sc-lbl">Actives</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <CheckCircle2 :size="15" class="sc-icon sc-icon--vert" />
        <span class="sc-val sc-val--vert">{{ stats.verified }}</span>
        <span class="sc-lbl">Vérifiées</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <XCircle :size="15" class="sc-icon sc-icon--muted" />
        <span class="sc-val">{{ stats.inactive }}</span>
        <span class="sc-lbl">Inactives</span>
      </div>
    </section>

    <!-- ── Toolbar ─────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input v-model="searchQuery" type="search" class="search-input" placeholder="Rechercher par nom, hôte, base…" />
      </div>
      <div class="select-wrap">
        <select v-model="filterType" class="filter-select">
          <option value="all">Tous les types</option>
          <option v-for="ct in CONN_TYPES" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <template v-if="loading">
      <div v-for="i in 4" :key="i" class="row-skel"></div>
    </template>

    <!-- ── Empty ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <Database :size="40" class="empty-icon" />
      <p class="empty-title">{{ connections.length === 0 ? 'Aucune connexion' : 'Aucun résultat' }}</p>
      <p class="empty-sub">Configurez une connexion à une base de données externe.</p>
      <button class="btn-primary" @click="openDrawer()">
        <Plus :size="14" />
        <span>Nouvelle connexion</span>
      </button>
    </div>

    <!-- ── Table ────────────────────────────────────────────── -->
    <template v-else>
      <div class="conn-table" :class="{ 'conn-table--visible': listVisible }">
        <div class="table-hd">
          <span>Nom</span>
          <span>Type</span>
          <span>Hôte</span>
          <span>Base</span>
          <span>Utilisateur</span>
          <span>Statut</span>
          <span>Dernier test</span>
          <span></span>
        </div>
        <div
          v-for="(conn, i) in filtered"
          :key="conn.id"
          class="table-row"
          :style="{ '--ri': i }"
        >
          <div class="cell-name">
            <Plug :size="13" class="conn-icon" :class="conn.is_active ? 'conn-icon--active' : 'conn-icon--inactive'" />
            <div>
              <p class="conn-name">{{ conn.name }}</p>
              <p v-if="conn.description" class="conn-desc">{{ conn.description }}</p>
            </div>
          </div>
          <span class="cell-badge">{{ connTypeLabel(conn.connection_type) }}</span>
          <span class="cell-muted">{{ conn.host }}{{ conn.port ? `:${conn.port}` : '' }}</span>
          <span class="cell-muted">{{ conn.database_name || '—' }}</span>
          <span class="cell-muted">{{ conn.username || '—' }}</span>
          <div class="cell-status">
            <CheckCircle2 v-if="conn.is_verified" :size="13" class="status-icon status-icon--ok" />
            <AlertTriangle v-else :size="13" class="status-icon status-icon--warn" />
            <span :class="conn.is_active ? 'text-ok' : 'text-muted'">
              {{ conn.is_active ? 'Active' : 'Inactive' }}
            </span>
            <!-- Test result feedback -->
            <span v-if="testResults[conn.id] === 'ok'"  class="test-badge test-badge--ok">OK</span>
            <span v-if="testResults[conn.id] === 'fail'" class="test-badge test-badge--fail">Échoué</span>
          </div>
          <span class="cell-muted">{{ timeAgo(conn.last_tested) }}</span>
          <div class="cell-actions">
            <button
              class="act-btn act-btn--test"
              title="Tester la connexion"
              :disabled="testingId === conn.id"
              @click="testConnection(conn.id)"
            >
              <span v-if="testingId === conn.id" class="act-spinner"></span>
              <Activity v-else :size="13" />
            </button>
            <button class="act-btn" title="Modifier" @click="openDrawer(conn)">
              <Pencil :size="13" />
            </button>
            <template v-if="deleteConfirm === conn.id">
              <button class="act-btn act-btn--yes" @click="deleteConnection(conn.id)">Oui</button>
              <button class="act-btn" @click="deleteConfirm = null">Non</button>
            </template>
            <button v-else class="act-btn act-btn--del" @click="deleteConfirm = conn.id">
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Drawer ────────────────────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" :aria-label="editConn ? 'Modifier la connexion' : 'Nouvelle connexion'">
          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editConn ? 'Modifier la connexion' : 'Nouvelle connexion' }}</h3>
            <button class="drawer-close" @click="drawerOpen = false"><X :size="18" /></button>
          </div>
          <form class="drawer-form" @submit.prevent="submitForm">

            <div class="form-field">
              <label class="form-label" for="conn-name">Nom <span class="req">*</span></label>
              <input id="conn-name" v-model="form.name" class="form-input" type="text" placeholder="Ex : Production PostgreSQL" required />
            </div>

            <div class="form-field">
              <label class="form-label">Type de base de données</label>
              <div class="select-wrap">
                <select v-model="form.connection_type" class="form-input">
                  <option v-for="ct in CONN_TYPES" :key="ct.value" :value="ct.value">{{ ct.label }}</option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>

            <div class="form-row-2">
              <div class="form-field">
                <label class="form-label" for="conn-host">Hôte <span class="req">*</span></label>
                <input id="conn-host" v-model="form.host" class="form-input" type="text" placeholder="localhost ou IP" required />
              </div>
              <div class="form-field">
                <label class="form-label">Port</label>
                <input v-model="form.port" class="form-input" type="number" placeholder="5432" min="1" max="65535" />
              </div>
            </div>

            <div class="form-field">
              <label class="form-label">Nom de la base <span class="req">*</span></label>
              <input id="conn-db" v-model="form.database_name" class="form-input" type="text" placeholder="nom_de_la_base" required />
            </div>

            <div class="form-row-2">
              <div class="form-field">
                <label class="form-label">Utilisateur</label>
                <input v-model="form.username" class="form-input" type="text" placeholder="admin" />
              </div>
              <div class="form-field">
                <label class="form-label">Mot de passe</label>
                <input v-model="form.password" class="form-input" type="password" :placeholder="editConn ? '(inchangé)' : 'Mot de passe'" autocomplete="new-password" />
              </div>
            </div>

            <div class="form-field">
              <label class="form-label">Description</label>
              <textarea v-model="form.description" class="form-input form-textarea" rows="2" placeholder="Description optionnelle"></textarea>
            </div>

            <div class="form-field form-field--checkbox">
              <label class="form-label--inline">
                <input v-model="form.is_active" type="checkbox" class="form-checkbox" />
                Connexion active
              </label>
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>

            <div class="drawer-foot">
              <button type="button" class="btn-ghost" @click="drawerOpen = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="submitting" class="btn-spinner"></span>
                {{ submitting ? 'Enregistrement…' : (editConn ? 'Sauvegarder' : 'Créer') }}
              </button>
            </div>
          </form>
        </aside>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.conn-page { display: flex; flex-direction: column; gap: var(--sp-6); padding: var(--sp-8); min-height: 100%; }

.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
.page-meta  { font-size: var(--text-sm); color: var(--text-muted); margin-top: 2px; }
.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

.stats-rail { display: flex; align-items: center; gap: var(--sp-4); padding: var(--sp-3) var(--sp-5); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); flex-wrap: wrap; }
.stat-sep { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.stat-cell { display: flex; align-items: center; gap: var(--sp-2); }
.sc-icon { color: var(--text-muted); }
.sc-icon--ok   { color: oklch(76% 0.14 62); }
.sc-icon--vert { color: oklch(65% 0.13 148); }
.sc-icon--muted{ color: var(--text-muted); }
.sc-val { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.sc-val--ok   { color: oklch(76% 0.14 62); }
.sc-val--vert { color: oklch(65% 0.13 148); }
.sc-lbl { font-size: var(--text-xs); color: var(--text-muted); }

.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 220px; }
.search-icon { position: absolute; left: var(--sp-3); top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input { width: 100%; padding: var(--sp-2) var(--sp-3) var(--sp-2) calc(var(--sp-3) + 22px); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); }
.select-wrap { position: relative; }
.filter-select { padding: var(--sp-2) var(--sp-7) var(--sp-2) var(--sp-3); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-size: var(--text-sm); appearance: none; cursor: pointer; }
.select-arrow { position: absolute; right: var(--sp-2); top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-muted); }

/* Table */
.conn-table { border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; opacity: 0; transition: opacity 300ms; }
.conn-table--visible { opacity: 1; }
.table-hd {
  display: grid;
  grid-template-columns: 1.5fr 100px 160px 120px 120px 130px 110px 130px;
  padding: var(--sp-2) var(--sp-4);
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-display); font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase; color: var(--text-muted);
}
.table-row {
  display: grid;
  grid-template-columns: 1.5fr 100px 160px 120px 120px 130px 110px 130px;
  align-items: center; gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--border-subtle);
  font-size: var(--text-sm);
  opacity: 0; transform: translateY(3px);
  animation: row-in 220ms ease forwards;
  animation-delay: calc(var(--ri, 0) * 20ms);
}
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: var(--surface-overlay); }
@keyframes row-in { to { opacity: 1; transform: none; } }

.cell-name { display: flex; align-items: flex-start; gap: var(--sp-2); overflow: hidden; }
.conn-icon { flex-shrink: 0; margin-top: 2px; }
.conn-icon--active   { color: oklch(65% 0.13 148); }
.conn-icon--inactive { color: var(--text-muted); }
.conn-name { font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conn-desc { font-size: var(--text-xs); color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-muted { font-size: var(--text-xs); color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-badge { display: inline-block; padding: 2px var(--sp-2); border-radius: var(--radius-sm); font-size: 0.62rem; font-weight: 700; background: var(--surface-overlay); border: 1px solid var(--border-subtle); color: var(--text-secondary); white-space: nowrap; }
.cell-status { display: flex; align-items: center; gap: var(--sp-1); font-size: var(--text-xs); }
.status-icon { flex-shrink: 0; }
.status-icon--ok   { color: oklch(65% 0.13 148); }
.status-icon--warn { color: oklch(78% 0.14 80); }
.text-ok   { color: oklch(65% 0.13 148); font-weight: 600; }
.text-muted{ color: var(--text-muted); }
.test-badge { padding: 1px 5px; border-radius: var(--radius-sm); font-size: 0.6rem; font-weight: 700; text-transform: uppercase; }
.test-badge--ok   { background: oklch(14% 0.05 148); color: oklch(65% 0.13 148); }
.test-badge--fail { background: oklch(14% 0.05 24);  color: oklch(64% 0.19 24); }
.cell-actions { display: flex; align-items: center; gap: var(--sp-1); justify-content: flex-end; }

/* Action buttons */
.act-btn { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: var(--surface-overlay); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); color: var(--text-muted); cursor: pointer; transition: all 120ms; font-size: var(--text-xs); }
.act-btn:hover { border-color: var(--accent); color: var(--accent); }
.act-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.act-btn--test:hover { border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }
.act-btn--del:hover  { border-color: oklch(64% 0.19 24); color: oklch(64% 0.19 24); }
.act-btn--yes { border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); width: auto; padding: 0 var(--sp-2); }
.act-spinner { display: inline-block; width: 10px; height: 10px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Skeleton */
.row-skel { height: 52px; background: var(--surface-raised); border-radius: var(--radius-md); margin-bottom: var(--sp-2); animation: skel-pulse 1.4s ease-in-out infinite alternate; }
@keyframes skel-pulse { from { opacity: 0.4; } to { opacity: 0.8; } }

/* Empty */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-16); text-align: center; }
.empty-icon { color: var(--text-muted); opacity: 0.4; }
.empty-title { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.empty-sub { font-size: var(--text-sm); color: var(--text-muted); }

/* Drawer */
.drawer-overlay { position: fixed; inset: 0; background: oklch(0% 0 0 / 0.5); z-index: 200; display: flex; justify-content: flex-end; }
.drawer { width: min(500px, 95vw); background: var(--surface-base); border-left: 1px solid var(--border-subtle); display: flex; flex-direction: column; overflow-y: auto; }
.drawer-hd { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-4) var(--sp-5); border-bottom: 1px solid var(--border-subtle); }
.drawer-title { font-family: var(--font-display); font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.drawer-close { background: none; border: none; cursor: pointer; color: var(--text-muted); display: flex; padding: var(--sp-1); border-radius: var(--radius-sm); }
.drawer-close:hover { color: var(--text-primary); background: var(--surface-overlay); }
.drawer-form { display: flex; flex-direction: column; gap: var(--sp-4); padding: var(--sp-5); flex: 1; }
.drawer-foot { display: flex; gap: var(--sp-3); margin-top: auto; padding-top: var(--sp-4); border-top: 1px solid var(--border-subtle); }
.drawer-foot .btn-primary, .drawer-foot .btn-ghost { flex: 1; justify-content: center; }

.form-field { display: flex; flex-direction: column; gap: var(--sp-1); }
.form-label { font-family: var(--font-display); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-muted); }
.form-label--inline { display: flex; align-items: center; gap: var(--sp-2); font-size: var(--text-sm); color: var(--text-secondary); cursor: pointer; font-family: var(--font-ui); font-weight: 500; text-transform: none; letter-spacing: 0; }
.form-input { padding: var(--sp-2) var(--sp-3); background: var(--surface-overlay); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); }
.form-textarea { resize: vertical; min-height: 60px; }
.form-checkbox { width: 14px; height: 14px; cursor: pointer; accent-color: var(--accent); }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.form-error { padding: var(--sp-2) var(--sp-3); background: oklch(14% 0.05 24); border: 1px solid oklch(64% 0.19 24 / 0.3); border-radius: var(--radius-md); color: oklch(64% 0.19 24); font-size: var(--text-sm); }
.req { color: oklch(64% 0.19 24); }
.btn-spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; }

.btn-primary { display: inline-flex; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-4); background: var(--accent); border: none; border-radius: var(--radius-md); color: oklch(12% 0.05 62); font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 600; cursor: pointer; transition: all 120ms; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { display: inline-flex; align-items: center; gap: var(--sp-2); padding: var(--sp-2) var(--sp-4); background: transparent; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-secondary); font-family: var(--font-ui); font-size: var(--text-sm); cursor: pointer; transition: all 120ms; }
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.btn-icon { padding: var(--sp-2); }
.btn-icon--spin svg { animation: spin 1s linear infinite; }

.drawer-anim-enter-active, .drawer-anim-leave-active { transition: transform 280ms cubic-bezier(0.4, 0, 0.2, 1); }
.drawer-anim-enter-from, .drawer-anim-leave-to { transform: translateX(100%); }
</style>
