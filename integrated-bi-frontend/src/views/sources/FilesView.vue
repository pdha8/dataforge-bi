<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api/axios'
import {
  FolderOpen, Search, Plus, RefreshCcw, Trash2, Eye,
  Play, X, ChevronDown, Upload, FileText, CheckCircle2,
  AlertTriangle, Clock,
} from 'lucide-vue-next'

// ── Types ──────────────────────────────────────────────────
interface DataFile {
  id: string
  name: string
  file_type: string
  file_size: number
  status: string
  row_count: number | null
  column_count: number | null
  source: string | null
  source_name: string
  created_at: string
  updated_at: string
  is_processed: boolean
}

interface FilePreview {
  headers: string[]
  rows: any[][]
  total_rows: number
}

const STATUS_META: Record<string, { label: string; cls: string }> = {
  pending:    { label: 'En attente',  cls: 'st--pending'  },
  processing: { label: 'Traitement', cls: 'st--running'  },
  processed:  { label: 'Traité',     cls: 'st--success'  },
  error:      { label: 'Erreur',     cls: 'st--error'    },
}

// ── State ──────────────────────────────────────────────────
const files        = ref<DataFile[]>([])
const loading      = ref(true)
const listVisible  = ref(false)
const refreshing   = ref(false)
const searchQuery  = ref('')
const filterType   = ref('all')

const drawerOpen   = ref(false)
const submitting   = ref(false)
const formError    = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const form = ref({ name: '', source: '', file_type: 'csv' })

const previewFile  = ref<DataFile | null>(null)
const preview      = ref<FilePreview | null>(null)
const previewLoading = ref(false)

const processingId = ref<string | null>(null)
const deleteConfirm = ref<string | null>(null)

// ── Computed ───────────────────────────────────────────────
const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return files.value.filter(f => {
    const matchSearch = !q || f.name.toLowerCase().includes(q) || (f.source_name || '').toLowerCase().includes(q)
    const matchType   = filterType.value === 'all' || f.file_type === filterType.value
    return matchSearch && matchType
  })
})

const stats = computed(() => ({
  total:      files.value.length,
  processed:  files.value.filter(f => f.is_processed).length,
  pending:    files.value.filter(f => !f.is_processed && f.status !== 'error').length,
  errors:     files.value.filter(f => f.status === 'error').length,
}))

const fileTypes = computed(() => [...new Set(files.value.map(f => f.file_type).filter(Boolean))])

// ── Helpers ────────────────────────────────────────────────
function fmtSize(bytes: number): string {
  if (!bytes) return '—'
  if (bytes < 1024)       return `${bytes} B`
  if (bytes < 1048576)    return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(2)} MB`
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function statusMeta(s: string) {
  return STATUS_META[s] ?? { label: s, cls: 'st--pending' }
}

// ── API ────────────────────────────────────────────────────
async function fetchFiles() {
  loading.value = true
  listVisible.value = false
  try {
    const { data } = await api.get('/api/data-sources/files/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    files.value = rows.map((f: any): DataFile => ({
      id:            f.id,
      name:          f.name || f.file_name || '',
      file_type:     f.file_type || f.format || 'csv',
      file_size:     f.file_size ?? 0,
      status:        f.status || 'pending',
      row_count:     f.row_count ?? null,
      column_count:  f.column_count ?? null,
      source:        f.source ?? null,
      source_name:   f.source_name || '',
      created_at:    f.created_at || new Date().toISOString(),
      updated_at:    f.updated_at || f.created_at || new Date().toISOString(),
      is_processed:  f.is_processed ?? f.status === 'processed',
    }))
  } catch {
    files.value = []
  } finally {
    loading.value = false
    requestAnimationFrame(() => { listVisible.value = true })
  }
}

async function refresh() {
  refreshing.value = true
  await fetchFiles()
  refreshing.value = false
}

async function uploadFile() {
  if (!selectedFile.value) return
  submitting.value = true
  formError.value = null
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  if (form.value.name.trim()) fd.append('name', form.value.name.trim())
  if (form.value.source.trim()) fd.append('source', form.value.source.trim())
  fd.append('file_type', form.value.file_type)
  try {
    await api.post('/api/data-sources/files/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    drawerOpen.value = false
    selectedFile.value = null
    form.value = { name: '', source: '', file_type: 'csv' }
    await fetchFiles()
  } catch (err: any) {
    formError.value = err?.response?.data?.detail ?? err?.response?.data?.message ?? 'Erreur lors de l\'upload.'
  } finally {
    submitting.value = false
  }
}

async function processFile(id: string) {
  processingId.value = id
  try {
    await api.post(`/api/data-sources/files/${id}/process/`)
    await fetchFiles()
  } catch { /* ignore */ } finally {
    processingId.value = null
  }
}

async function openPreview(file: DataFile) {
  previewFile.value = file
  preview.value = null
  previewLoading.value = true
  try {
    const { data } = await api.get(`/api/data-sources/files/${file.id}/preview/`)
    preview.value = {
      headers:    data.headers ?? data.columns ?? [],
      rows:       data.rows ?? data.data ?? [],
      total_rows: data.total_rows ?? data.row_count ?? 0,
    }
  } catch {
    preview.value = { headers: [], rows: [], total_rows: 0 }
  } finally {
    previewLoading.value = false
  }
}

async function deleteFile(id: string) {
  try {
    await api.delete(`/api/data-sources/files/${id}/`)
    files.value = files.value.filter(f => f.id !== id)
  } catch { /* ignore */ } finally {
    deleteConfirm.value = null
  }
}

function onFileInput(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0]
    if (!form.value.name) {
      form.value.name = input.files[0].name.replace(/\.[^.]+$/, '')
    }
    const ext = input.files[0].name.split('.').pop()?.toLowerCase()
    if (ext === 'csv' || ext === 'json' || ext === 'xlsx' || ext === 'xml' || ext === 'parquet') {
      form.value.file_type = ext
    }
  }
}

onMounted(fetchFiles)
</script>

<template>
  <div class="files-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">Fichiers de données</h2>
        <p class="page-meta">{{ stats.total }} fichier{{ stats.total !== 1 ? 's' : '' }}</p>
      </div>
      <div class="hd-actions">
        <button
          class="btn-ghost btn-icon"
          :class="{ 'btn-icon--spin': refreshing }"
          :disabled="refreshing"
          @click="refresh"
        >
          <RefreshCcw :size="14" />
        </button>
        <button class="btn-primary" @click="drawerOpen = true">
          <Upload :size="15" />
          <span>Importer un fichier</span>
        </button>
      </div>
    </header>

    <!-- ── Stats ───────────────────────────────────────────── -->
    <section class="stats-rail">
      <div class="stat-cell">
        <FolderOpen :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.total }}</span>
        <span class="sc-lbl">Total</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <CheckCircle2 :size="15" class="sc-icon sc-icon--ok" />
        <span class="sc-val sc-val--ok">{{ stats.processed }}</span>
        <span class="sc-lbl">Traités</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Clock :size="15" class="sc-icon sc-icon--warn" />
        <span class="sc-val sc-val--warn">{{ stats.pending }}</span>
        <span class="sc-lbl">En attente</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <AlertTriangle :size="15" class="sc-icon sc-icon--err" />
        <span class="sc-val sc-val--err">{{ stats.errors }}</span>
        <span class="sc-lbl">Erreurs</span>
      </div>
    </section>

    <!-- ── Toolbar ─────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input v-model="searchQuery" type="search" class="search-input" placeholder="Rechercher un fichier…" />
      </div>
      <div class="select-wrap">
        <select v-model="filterType" class="filter-select">
          <option value="all">Tous les formats</option>
          <option v-for="t in fileTypes" :key="t" :value="t">{{ t.toUpperCase() }}</option>
        </select>
        <ChevronDown :size="13" class="select-arrow" />
      </div>
    </div>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <template v-if="loading">
      <div v-for="i in 5" :key="i" class="row-skel"></div>
    </template>

    <!-- ── Empty ───────────────────────────────────────────── -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <FolderOpen :size="40" class="empty-icon" />
      <p class="empty-title">{{ files.length === 0 ? 'Aucun fichier importé' : 'Aucun résultat' }}</p>
      <p class="empty-sub">Importez un fichier CSV, Excel, JSON ou Parquet pour commencer.</p>
      <button class="btn-primary" @click="drawerOpen = true">
        <Upload :size="14" />
        <span>Importer un fichier</span>
      </button>
    </div>

    <!-- ── Table ────────────────────────────────────────────── -->
    <template v-else>
      <div class="files-table" :class="{ 'files-table--visible': listVisible }">
        <div class="table-hd">
          <span>Nom</span>
          <span>Format</span>
          <span>Taille</span>
          <span>Lignes</span>
          <span>Colonnes</span>
          <span>Source</span>
          <span>Statut</span>
          <span>Importé</span>
          <span></span>
        </div>
        <div
          v-for="(file, i) in filtered"
          :key="file.id"
          class="table-row"
          :style="{ '--ri': i }"
        >
          <div class="cell-name">
            <FileText :size="14" class="file-icon" />
            <span>{{ file.name }}</span>
          </div>
          <span class="cell-badge cell-badge--type">{{ file.file_type.toUpperCase() }}</span>
          <span class="cell-muted">{{ fmtSize(file.file_size) }}</span>
          <span class="cell-muted">{{ file.row_count?.toLocaleString('fr-FR') ?? '—' }}</span>
          <span class="cell-muted">{{ file.column_count ?? '—' }}</span>
          <span class="cell-muted">{{ file.source_name || '—' }}</span>
          <span class="status-chip" :class="statusMeta(file.status).cls">
            {{ statusMeta(file.status).label }}
          </span>
          <span class="cell-muted">{{ timeAgo(file.created_at) }}</span>
          <div class="cell-actions">
            <button class="act-btn" title="Aperçu" @click="openPreview(file)">
              <Eye :size="13" />
            </button>
            <button
              class="act-btn act-btn--run"
              title="Traiter"
              :disabled="processingId === file.id || file.is_processed"
              @click="processFile(file.id)"
            >
              <span v-if="processingId === file.id" class="act-spinner"></span>
              <Play v-else :size="13" />
            </button>
            <template v-if="deleteConfirm === file.id">
              <button class="act-btn act-btn--yes" @click="deleteFile(file.id)">Oui</button>
              <button class="act-btn" @click="deleteConfirm = null">Non</button>
            </template>
            <button v-else class="act-btn act-btn--del" @click="deleteConfirm = file.id">
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ── Upload drawer ────────────────────────────────────── -->
    <Transition name="drawer-anim">
      <div v-if="drawerOpen" class="drawer-overlay" @click.self="drawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true" aria-label="Importer un fichier">
          <div class="drawer-hd">
            <h3 class="drawer-title">Importer un fichier</h3>
            <button class="drawer-close" @click="drawerOpen = false"><X :size="18" /></button>
          </div>
          <form class="drawer-form" @submit.prevent="uploadFile">

            <div class="form-field">
              <label class="form-label">Fichier <span class="req">*</span></label>
              <input
                type="file"
                class="form-input"
                accept=".csv,.json,.xlsx,.xls,.xml,.parquet,.txt"
                @change="onFileInput"
                required
              />
              <p v-if="selectedFile" class="form-hint">
                {{ selectedFile.name }} — {{ fmtSize(selectedFile.size) }}
              </p>
            </div>

            <div class="form-field">
              <label class="form-label">Nom affiché</label>
              <input v-model="form.name" class="form-input" type="text" placeholder="Nom du fichier (optionnel)" />
            </div>

            <div class="form-field">
              <label class="form-label">Format</label>
              <div class="select-wrap">
                <select v-model="form.file_type" class="form-input">
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="xlsx">Excel (XLSX)</option>
                  <option value="xml">XML</option>
                  <option value="parquet">Parquet</option>
                  <option value="txt">Texte</option>
                </select>
                <ChevronDown :size="13" class="select-arrow" />
              </div>
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>

            <div class="drawer-foot">
              <button type="button" class="btn-ghost" @click="drawerOpen = false">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting || !selectedFile">
                <span v-if="submitting" class="btn-spinner"></span>
                {{ submitting ? 'Upload en cours…' : 'Importer' }}
              </button>
            </div>
          </form>
        </aside>
      </div>
    </Transition>

    <!-- ── Preview modal ────────────────────────────────────── -->
    <Transition name="modal-anim">
      <div v-if="previewFile" class="modal-overlay" @click.self="previewFile = null">
        <div class="preview-modal">
          <div class="preview-hd">
            <h3 class="preview-title">{{ previewFile.name }}</h3>
            <button class="drawer-close" @click="previewFile = null"><X :size="18" /></button>
          </div>
          <div class="preview-body">
            <div v-if="previewLoading" class="preview-loading">
              <span class="spinner"></span>
            </div>
            <template v-else-if="preview">
              <p v-if="preview.total_rows" class="preview-meta">
                {{ preview.total_rows.toLocaleString('fr-FR') }} lignes au total
                — affichage des {{ preview.rows.length }} premières
              </p>
              <div class="preview-scroll">
                <table class="preview-table">
                  <thead>
                    <tr>
                      <th v-for="col in preview.headers" :key="col">{{ col }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in preview.rows" :key="ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-if="preview.headers.length === 0" class="preview-empty">Aucune donnée disponible.</p>
            </template>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.files-page {
  display: flex; flex-direction: column; gap: var(--sp-6); padding: var(--sp-8); min-height: 100%;
}

.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
.page-meta  { font-size: var(--text-sm); color: var(--text-muted); margin-top: 2px; }
.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

.stats-rail { display: flex; align-items: center; gap: var(--sp-4); padding: var(--sp-3) var(--sp-5); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); flex-wrap: wrap; }
.stat-sep { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.stat-cell { display: flex; align-items: center; gap: var(--sp-2); }
.sc-icon { color: var(--text-muted); }
.sc-icon--ok  { color: oklch(65% 0.13 148); }
.sc-icon--warn{ color: oklch(76% 0.14 62); }
.sc-icon--err { color: oklch(64% 0.19 24); }
.sc-val { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.sc-val--ok   { color: oklch(65% 0.13 148); }
.sc-val--warn { color: oklch(76% 0.14 62); }
.sc-val--err  { color: oklch(64% 0.19 24); }
.sc-lbl { font-size: var(--text-xs); color: var(--text-muted); }

.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 220px; }
.search-icon { position: absolute; left: var(--sp-3); top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input { width: 100%; padding: var(--sp-2) var(--sp-3) var(--sp-2) calc(var(--sp-3) + 22px); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); }
.select-wrap { position: relative; }
.filter-select { padding: var(--sp-2) var(--sp-7) var(--sp-2) var(--sp-3); background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-size: var(--text-sm); appearance: none; cursor: pointer; }
.select-arrow { position: absolute; right: var(--sp-2); top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--text-muted); }

/* Table */
.files-table { border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; opacity: 0; transition: opacity 300ms; }
.files-table--visible { opacity: 1; }
.table-hd {
  display: grid;
  grid-template-columns: 1fr 70px 80px 80px 70px 120px 90px 100px 130px;
  padding: var(--sp-2) var(--sp-4);
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-display); font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase; color: var(--text-muted);
}
.table-row {
  display: grid;
  grid-template-columns: 1fr 70px 80px 80px 70px 120px 90px 100px 130px;
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

.cell-name { display: flex; align-items: center; gap: var(--sp-2); font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-icon { color: var(--accent); flex-shrink: 0; }
.cell-muted { font-size: var(--text-xs); color: var(--text-muted); }
.cell-badge { display: inline-block; padding: 2px var(--sp-2); border-radius: var(--radius-sm); font-size: 0.62rem; font-weight: 700; }
.cell-badge--type { background: var(--surface-overlay); border: 1px solid var(--border-subtle); color: var(--text-secondary); }
.cell-actions { display: flex; align-items: center; gap: var(--sp-1); justify-content: flex-end; }

/* Status chips */
.status-chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px var(--sp-2); border-radius: var(--radius-full); font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
.st--pending  { background: oklch(16% 0.04 258); color: oklch(65% 0.06 258); }
.st--running  { background: oklch(16% 0.05 62);  color: oklch(76% 0.14 62); }
.st--success  { background: oklch(14% 0.05 148); color: oklch(65% 0.13 148); }
.st--error    { background: oklch(14% 0.05 24);  color: oklch(64% 0.19 24); }

/* Action buttons */
.act-btn { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: var(--surface-overlay); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); color: var(--text-muted); cursor: pointer; transition: all 120ms; font-size: var(--text-xs); }
.act-btn:hover { border-color: var(--accent); color: var(--accent); }
.act-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.act-btn--run:hover { border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }
.act-btn--del:hover { border-color: oklch(64% 0.19 24); color: oklch(64% 0.19 24); }
.act-btn--yes { border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); width: auto; padding: 0 var(--sp-2); }
.act-spinner { display: inline-block; width: 10px; height: 10px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Skeleton */
.row-skel { height: 48px; background: var(--surface-raised); border-radius: var(--radius-md); margin-bottom: var(--sp-2); animation: skel-pulse 1.4s ease-in-out infinite alternate; }
@keyframes skel-pulse { from { opacity: 0.4; } to { opacity: 0.8; } }

/* Empty */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--sp-3); padding: var(--sp-16); text-align: center; }
.empty-icon { color: var(--text-muted); opacity: 0.4; }
.empty-title { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.empty-sub { font-size: var(--text-sm); color: var(--text-muted); }

/* Drawer */
.drawer-overlay { position: fixed; inset: 0; background: oklch(0% 0 0 / 0.5); z-index: 200; display: flex; justify-content: flex-end; }
.drawer { width: min(460px, 95vw); background: var(--surface-base); border-left: 1px solid var(--border-subtle); display: flex; flex-direction: column; overflow-y: auto; }
.drawer-hd { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-4) var(--sp-5); border-bottom: 1px solid var(--border-subtle); }
.drawer-title { font-family: var(--font-display); font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.drawer-close { background: none; border: none; cursor: pointer; color: var(--text-muted); display: flex; padding: var(--sp-1); border-radius: var(--radius-sm); }
.drawer-close:hover { color: var(--text-primary); background: var(--surface-overlay); }
.drawer-form { display: flex; flex-direction: column; gap: var(--sp-4); padding: var(--sp-5); flex: 1; }
.drawer-foot { display: flex; gap: var(--sp-3); margin-top: auto; padding-top: var(--sp-4); border-top: 1px solid var(--border-subtle); }
.drawer-foot .btn-primary, .drawer-foot .btn-ghost { flex: 1; justify-content: center; }

.form-field { display: flex; flex-direction: column; gap: var(--sp-1); }
.form-label { font-family: var(--font-display); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: var(--text-muted); }
.form-input { padding: var(--sp-2) var(--sp-3); background: var(--surface-overlay); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); }
.form-hint { font-size: var(--text-xs); color: var(--text-muted); }
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

/* Drawer animation */
.drawer-anim-enter-active, .drawer-anim-leave-active { transition: transform 280ms cubic-bezier(0.4, 0, 0.2, 1); }
.drawer-anim-enter-from, .drawer-anim-leave-to { transform: translateX(100%); }

/* Preview modal */
.modal-overlay { position: fixed; inset: 0; background: oklch(0% 0 0 / 0.6); z-index: 300; display: flex; align-items: center; justify-content: center; padding: var(--sp-6); }
.preview-modal { background: var(--surface-base); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); width: min(900px, 95vw); max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; }
.preview-hd { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-4) var(--sp-5); border-bottom: 1px solid var(--border-subtle); }
.preview-title { font-family: var(--font-display); font-size: 1rem; font-weight: 700; color: var(--text-primary); }
.preview-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; gap: var(--sp-3); padding: var(--sp-4); }
.preview-meta { font-size: var(--text-xs); color: var(--text-muted); }
.preview-loading { display: flex; align-items: center; justify-content: center; padding: var(--sp-12); }
.spinner { display: inline-block; width: 24px; height: 24px; border: 3px solid var(--surface-overlay); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
.preview-scroll { overflow: auto; flex: 1; }
.preview-table { width: 100%; border-collapse: collapse; font-size: var(--text-xs); }
.preview-table th { background: var(--surface-overlay); padding: var(--sp-2) var(--sp-3); text-align: left; font-family: var(--font-display); font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); white-space: nowrap; border-bottom: 1px solid var(--border-subtle); }
.preview-table td { padding: var(--sp-2) var(--sp-3); border-bottom: 1px solid var(--border-subtle); color: var(--text-secondary); white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
.preview-empty { color: var(--text-muted); font-size: var(--text-sm); text-align: center; padding: var(--sp-8); }

.modal-anim-enter-active, .modal-anim-leave-active { transition: opacity 200ms; }
.modal-anim-enter-from, .modal-anim-leave-to { opacity: 0; }
</style>
