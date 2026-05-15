<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Filler, Tooltip, Legend, RadialLinearScale,
  ArcElement,
} from 'chart.js'
import { Bar, Doughnut } from 'vue-chartjs'
import api from '@/api/axios'
import {
  Brain, TrendingUp, AlertTriangle, CheckCircle2,
  XCircle, RefreshCcw, Plus, Search, X, Pencil, Trash2,
  ChevronDown, Layers, Play, Activity, Target, Cpu,
  Zap, Eye, Minus,
} from 'lucide-vue-next'

ChartJS.register(
  CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Filler, Tooltip, Legend, RadialLinearScale, ArcElement,
)

// ── Types ──────────────────────────────────────────────────
type ActiveTab = 'models' | 'forecasts' | 'anomalies' | 'segmentation' | 'recommendations' | 'training_logs'

interface MLModel {
  id: string
  name: string
  description: string
  model_type: string
  algorithm: string
  status: string
  version: string
  accuracy: number | null
  precision: number | null
  recall: number | null
  f1_score: number | null
  rmse: number | null
  mae: number | null
  mape: number | null
  last_trained: string | null
  is_active: boolean
  tags: string[]
}

interface Forecast {
  id: string
  name: string
  description: string
  forecast_period: string
  horizon: number
  confidence_level: number
  accuracy: number | null
  mape: number | null
  forecast_date: string
  generated_at: string
  is_used: boolean
  data: any
}

interface Anomaly {
  id: string
  detected_at: string
  date: string
  value: number
  expected_value: number
  deviation: number
  deviation_percentage: number
  severity: string
  is_confirmed: boolean
  is_resolved: boolean
  notes: string
}

interface Segmentation {
  id: string
  segment_name: string
  segment_description: string
  segment_id: number
  size: number
  percentage: number
  characteristics: any
  avg_value: number
  min_value: number
  max_value: number
}

interface Recommendation {
  id: string
  recommendation_type: string
  title: string
  description: string
  confidence: number
  priority: string
  score: number
  reason: string
  is_applied: boolean
  is_dismissed: boolean
  applied_at: string | null
}

interface TrainingLog {
  id: string
  model: string
  model_name: string
  status: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  accuracy: number | null
  loss: number | null
  epochs: number | null
  error_message: string
  parameters: any
}

// ── Metadata ───────────────────────────────────────────────
const MODEL_TYPE_META: Record<string, { label: string; color: string }> = {
  classification:  { label: 'Classification',   color: 'oklch(62% 0.13 240)' },
  regression:      { label: 'Régression',       color: 'oklch(76% 0.14 62)'  },
  clustering:      { label: 'Clustering',       color: 'oklch(65% 0.13 148)' },
  forecasting:     { label: 'Prévision',        color: 'oklch(68% 0.12 290)' },
  anomaly_detection:{ label: 'Anomalies',       color: 'oklch(64% 0.19 24)'  },
  recommendation:  { label: 'Recommandation',   color: 'oklch(70% 0.12 200)' },
  nlp:             { label: 'NLP',              color: 'oklch(60% 0.16 155)' },
  computer_vision: { label: 'Vision',           color: 'oklch(65% 0.14 310)' },
}

const STATUS_META: Record<string, { label: string; cls: string; icon: any }> = {
  active:    { label: 'Actif',       cls: 'st--active',   icon: CheckCircle2  },
  training:  { label: 'Entraînem.', cls: 'st--training', icon: Cpu           },
  inactive:  { label: 'Inactif',    cls: 'st--inactive', icon: Minus         },
  failed:    { label: 'Échoué',     cls: 'st--failed',   icon: XCircle       },
  draft:     { label: 'Brouillon',  cls: 'st--draft',    icon: Minus         },
  deployed:  { label: 'Déployé',    cls: 'st--deployed', icon: Zap           },
}

const SEVERITY_META: Record<string, { label: string; cls: string }> = {
  low:      { label: 'Faible',   cls: 'sev--low'      },
  medium:   { label: 'Moyen',   cls: 'sev--medium'   },
  high:     { label: 'Élevé',   cls: 'sev--high'     },
  critical: { label: 'Critique', cls: 'sev--critical' },
}

const PRIORITY_META: Record<string, { label: string; cls: string }> = {
  low:      { label: 'Faible',  cls: 'prio--low'    },
  medium:   { label: 'Moyen',  cls: 'prio--medium'  },
  high:     { label: 'Élevé',  cls: 'prio--high'    },
  critical: { label: 'Urgent', cls: 'prio--crit'    },
}

// ── State ──────────────────────────────────────────────────
const activeTab        = ref<ActiveTab>('models')
const loading          = ref(true)
const refreshing       = ref(false)
const listVisible      = ref(false)
const searchQuery      = ref('')
const submitting       = ref(false)
const deleteConfirm    = ref<string | null>(null)

// Models
const models           = ref<MLModel[]>([])
const modelDrawerOpen  = ref(false)
const editModel        = ref<MLModel | null>(null)
const modelForm        = ref({
  name: '', description: '', model_type: 'regression', algorithm: '',
  version: '1.0', is_active: true,
})

// Forecasts
const forecasts        = ref<Forecast[]>([])
const forecastDrawerOpen = ref(false)
const editForecast     = ref<Forecast | null>(null)
const forecastForm     = ref({
  name: '', description: '', forecast_period: 'monthly',
  horizon: 12, confidence_level: 0.95,
})

// Anomalies
const anomalies        = ref<Anomaly[]>([])
const anomalyFilter    = ref<'all' | 'unresolved' | 'critical'>('all')

// Segmentation
const segments         = ref<Segmentation[]>([])

// Recommendations
const recommendations  = ref<Recommendation[]>([])
const recFilter        = ref<'all' | 'pending' | 'applied'>('all')
const applyingId       = ref<string | null>(null)

// Training logs
const trainingLogs     = ref<TrainingLog[]>([])
const trainingLogFilter = ref<'all' | 'success' | 'failed'>('all')

// ── Computed ───────────────────────────────────────────────
const filteredModels = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return models.value.filter(m =>
    !q || m.name.toLowerCase().includes(q) || m.algorithm.toLowerCase().includes(q)
  )
})

const filteredAnomalies = computed(() => {
  const q = searchQuery.value.toLowerCase()
  return anomalies.value.filter(a => {
    const matchQ = !q || a.severity.includes(q)
    const matchF = anomalyFilter.value === 'all'
      ? true
      : anomalyFilter.value === 'unresolved'
        ? !a.is_resolved
        : a.severity === 'critical'
    return matchQ && matchF
  })
})

const filteredRecommendations = computed(() => {
  return recommendations.value.filter(r => {
    if (recFilter.value === 'pending')  return !r.is_applied && !r.is_dismissed
    if (recFilter.value === 'applied')  return r.is_applied
    return true
  })
})

const filteredTrainingLogs = computed(() => {
  return trainingLogs.value.filter(l => {
    if (trainingLogFilter.value === 'success') return l.status === 'success' || l.status === 'completed'
    if (trainingLogFilter.value === 'failed')  return l.status === 'failed' || l.status === 'error'
    return true
  })
})

const stats = computed(() => ({
  totalModels:     models.value.length,
  activeModels:    models.value.filter(m => m.status === 'active' || m.status === 'deployed').length,
  avgAccuracy:     models.value.filter(m => m.accuracy !== null).length
    ? (models.value.filter(m => m.accuracy !== null).reduce((s, m) => s + (m.accuracy ?? 0), 0) /
       models.value.filter(m => m.accuracy !== null).length * 100)
    : 0,
  totalForecasts:  forecasts.value.length,
  unresolvedAnomalies: anomalies.value.filter(a => !a.is_resolved).length,
  criticalAnomalies:   anomalies.value.filter(a => a.severity === 'critical' && !a.is_resolved).length,
  pendingRecs:     recommendations.value.filter(r => !r.is_applied && !r.is_dismissed).length,
}))

// ── Chart data ─────────────────────────────────────────────
const accuracyChartData = computed(() => {
  const top = [...models.value].filter(m => m.accuracy !== null)
    .sort((a, b) => (b.accuracy ?? 0) - (a.accuracy ?? 0)).slice(0, 6)
  return {
    labels: top.map(m => m.name.slice(0, 16)),
    datasets: [{
      label: 'Accuracy (%)',
      data: top.map(m => parseFloat(((m.accuracy ?? 0) * 100).toFixed(1))),
      backgroundColor: 'oklch(76% 0.14 62 / 0.7)',
      borderColor: 'oklch(76% 0.14 62)',
      borderWidth: 1.5,
      borderRadius: 6,
    }],
  }
})

const anomalySeverityData = computed(() => ({
  labels: ['Faible', 'Moyen', 'Élevé', 'Critique'],
  datasets: [{
    data: [
      anomalies.value.filter(a => a.severity === 'low').length,
      anomalies.value.filter(a => a.severity === 'medium').length,
      anomalies.value.filter(a => a.severity === 'high').length,
      anomalies.value.filter(a => a.severity === 'critical').length,
    ],
    backgroundColor: [
      'oklch(65% 0.13 148 / 0.7)',
      'oklch(76% 0.14 62 / 0.7)',
      'oklch(78% 0.14 80 / 0.7)',
      'oklch(64% 0.19 24 / 0.7)',
    ],
    borderWidth: 0,
  }],
}))

const chartOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: true } },
  scales: {
    x: {
      grid: { color: 'oklch(100% 0 0 / 0.05)' },
      ticks: { color: 'oklch(65% 0.02 258)', font: { size: 11 } },
    },
    y: {
      grid: { color: 'oklch(100% 0 0 / 0.05)' },
      ticks: { color: 'oklch(65% 0.02 258)', font: { size: 11 } },
      min: 0, max: 100,
    },
  },
}

const donutOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: true, position: 'right' as const, labels: { color: 'oklch(75% 0.02 258)', boxWidth: 12, padding: 16 } } },
}

// ── Helpers ────────────────────────────────────────────────
function timeAgo(dateStr?: string | null): string {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function fmtPct(v: number | null): string {
  if (v === null || v === undefined) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function fmtScore(v: number | null): string {
  if (v === null || v === undefined) return '—'
  return v.toFixed(4)
}

function typeMeta(t: string) {
  return MODEL_TYPE_META[t] ?? { label: t, color: 'oklch(65% 0.08 258)' }
}

function statusMeta(s: string) {
  return STATUS_META[s] ?? { label: s, cls: 'st--inactive', icon: Minus }
}

function severityMeta(s: string) {
  return SEVERITY_META[s] ?? { label: s, cls: 'sev--low' }
}

function priorityMeta(p: string) {
  return PRIORITY_META[p] ?? { label: p, cls: 'prio--medium' }
}

// ── API: Models ────────────────────────────────────────────
async function fetchModels() {
  try {
    const { data } = await api.get('/api/ml-analytics/models/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    models.value = rows.map((m: any): MLModel => ({
      id:           m.id,
      name:         m.name || '',
      description:  m.description || '',
      model_type:   m.model_type || 'regression',
      algorithm:    m.algorithm || '',
      status:       m.status || 'draft',
      version:      m.version || '1.0',
      accuracy:     m.accuracy ?? null,
      precision:    m.precision ?? null,
      recall:       m.recall ?? null,
      f1_score:     m.f1_score ?? null,
      rmse:         m.rmse ?? null,
      mae:          m.mae ?? null,
      mape:         m.mape ?? null,
      last_trained: m.last_trained ?? null,
      is_active:    m.is_active ?? true,
      tags:         Array.isArray(m.tags) ? m.tags : [],
    }))
  } catch { models.value = [] }
}

async function submitModel() {
  submitting.value = true
  const body = {
    name:        modelForm.value.name,
    description: modelForm.value.description,
    model_type:  modelForm.value.model_type,
    algorithm:   modelForm.value.algorithm,
    version:     modelForm.value.version,
    is_active:   modelForm.value.is_active,
  }
  try {
    if (editModel.value) {
      await api.patch(`/api/ml-analytics/models/${editModel.value.id}/`, body)
    } else {
      await api.post('/api/ml-analytics/models/', body)
    }
    await fetchModels()
    modelDrawerOpen.value = false
    editModel.value = null
  } catch { /* ignore */ } finally {
    submitting.value = false
  }
}

async function deleteModel(id: string) {
  try { await api.delete(`/api/ml-analytics/models/${id}/`) } catch { /* ignore */ }
  models.value = models.value.filter(m => m.id !== id)
  deleteConfirm.value = null
}

async function trainModel(model: MLModel) {
  try {
    await api.post(`/api/ml-analytics/models/${model.id}/train/`)
    await fetchModels()
  } catch { /* ignore */ }
}

function openModelDrawer(m?: MLModel) {
  editModel.value = m ?? null
  modelForm.value = {
    name:        m?.name ?? '',
    description: m?.description ?? '',
    model_type:  m?.model_type ?? 'regression',
    algorithm:   m?.algorithm ?? '',
    version:     m?.version ?? '1.0',
    is_active:   m?.is_active ?? true,
  }
  modelDrawerOpen.value = true
}

// ── API: Forecasts ─────────────────────────────────────────
async function fetchForecasts() {
  try {
    const { data } = await api.get('/api/ml-analytics/forecasts/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    forecasts.value = rows.map((f: any): Forecast => ({
      id:               f.id,
      name:             f.name || '',
      description:      f.description || '',
      forecast_period:  f.forecast_period || 'monthly',
      horizon:          f.horizon ?? 12,
      confidence_level: f.confidence_level ?? 0.95,
      accuracy:         f.accuracy ?? null,
      mape:             f.mape ?? null,
      forecast_date:    f.forecast_date || f.created_at || '',
      generated_at:     f.generated_at || f.created_at || '',
      is_used:          f.is_used ?? false,
      data:             f.data ?? null,
    }))
  } catch { forecasts.value = [] }
}

async function submitForecast() {
  submitting.value = true
  const body = {
    name:             forecastForm.value.name,
    description:      forecastForm.value.description,
    forecast_period:  forecastForm.value.forecast_period,
    horizon:          forecastForm.value.horizon,
    confidence_level: forecastForm.value.confidence_level,
  }
  try {
    if (editForecast.value) {
      await api.patch(`/api/ml-analytics/forecasts/${editForecast.value.id}/`, body)
    } else {
      await api.post('/api/ml-analytics/forecasts/', body)
    }
    await fetchForecasts()
    forecastDrawerOpen.value = false
    editForecast.value = null
  } catch { /* ignore */ } finally {
    submitting.value = false
  }
}

async function deleteForecast(id: string) {
  try { await api.delete(`/api/ml-analytics/forecasts/${id}/`) } catch { /* ignore */ }
  forecasts.value = forecasts.value.filter(f => f.id !== id)
  deleteConfirm.value = null
}

function openForecastDrawer(f?: Forecast) {
  editForecast.value = f ?? null
  forecastForm.value = {
    name:             f?.name ?? '',
    description:      f?.description ?? '',
    forecast_period:  f?.forecast_period ?? 'monthly',
    horizon:          f?.horizon ?? 12,
    confidence_level: f?.confidence_level ?? 0.95,
  }
  forecastDrawerOpen.value = true
}

// ── API: Anomalies ─────────────────────────────────────────
async function fetchAnomalies() {
  try {
    const { data } = await api.get('/api/ml-analytics/anomalies/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    anomalies.value = rows.map((a: any): Anomaly => ({
      id:                 a.id,
      detected_at:        a.detected_at || a.created_at || '',
      date:               a.date || '',
      value:              a.value ?? 0,
      expected_value:     a.expected_value ?? 0,
      deviation:          a.deviation ?? 0,
      deviation_percentage: a.deviation_percentage ?? 0,
      severity:           a.severity || 'low',
      is_confirmed:       a.is_confirmed ?? false,
      is_resolved:        a.is_resolved ?? false,
      notes:              a.notes || '',
    }))
  } catch { anomalies.value = [] }
}

async function resolveAnomaly(id: string) {
  try {
    await api.patch(`/api/ml-analytics/anomalies/${id}/`, { is_resolved: true })
    const idx = anomalies.value.findIndex(a => a.id === id)
    if (idx !== -1) anomalies.value[idx].is_resolved = true
  } catch { /* ignore */ }
}

async function confirmAnomaly(id: string) {
  try {
    await api.patch(`/api/ml-analytics/anomalies/${id}/`, { is_confirmed: true })
    const idx = anomalies.value.findIndex(a => a.id === id)
    if (idx !== -1) anomalies.value[idx].is_confirmed = true
  } catch { /* ignore */ }
}

// ── API: Segmentation ──────────────────────────────────────
async function fetchSegments() {
  try {
    const { data } = await api.get('/api/ml-analytics/segmentations/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    segments.value = rows.map((s: any): Segmentation => ({
      id:                  s.id,
      segment_name:        s.segment_name || `Segment ${s.segment_id}`,
      segment_description: s.segment_description || '',
      segment_id:          s.segment_id ?? 0,
      size:                s.size ?? 0,
      percentage:          s.percentage ?? 0,
      characteristics:     s.characteristics ?? {},
      avg_value:           s.avg_value ?? 0,
      min_value:           s.min_value ?? 0,
      max_value:           s.max_value ?? 0,
    }))
  } catch { segments.value = [] }
}

// ── API: Recommendations ───────────────────────────────────
async function fetchRecommendations() {
  try {
    const { data } = await api.get('/api/ml-analytics/recommendations/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    recommendations.value = rows.map((r: any): Recommendation => ({
      id:                  r.id,
      recommendation_type: r.recommendation_type || 'general',
      title:               r.title || '',
      description:         r.description || '',
      confidence:          r.confidence ?? 0,
      priority:            r.priority || 'medium',
      score:               r.score ?? 0,
      reason:              r.reason || '',
      is_applied:          r.is_applied ?? false,
      is_dismissed:        r.is_dismissed ?? false,
      applied_at:          r.applied_at ?? null,
    }))
  } catch { recommendations.value = [] }
}

async function applyRecommendation(id: string) {
  applyingId.value = id
  try {
    await api.patch(`/api/ml-analytics/recommendations/${id}/`, { is_applied: true })
    const idx = recommendations.value.findIndex(r => r.id === id)
    if (idx !== -1) recommendations.value[idx].is_applied = true
  } catch { /* ignore */ } finally {
    applyingId.value = null
  }
}

async function dismissRecommendation(id: string) {
  try {
    await api.patch(`/api/ml-analytics/recommendations/${id}/`, { is_dismissed: true })
    const idx = recommendations.value.findIndex(r => r.id === id)
    if (idx !== -1) recommendations.value[idx].is_dismissed = true
  } catch { /* ignore */ }
}

// ── API: Training Logs ─────────────────────────────────────
async function fetchTrainingLogs() {
  try {
    const { data } = await api.get('/api/ml-analytics/training-logs/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    trainingLogs.value = rows.map((l: any): TrainingLog => ({
      id:               l.id,
      model:            l.model,
      model_name:       l.model_name || l.model || '',
      status:           l.status || 'unknown',
      started_at:       l.started_at ?? null,
      completed_at:     l.completed_at ?? null,
      duration_seconds: l.duration_seconds ?? null,
      accuracy:         l.accuracy ?? null,
      loss:             l.loss ?? null,
      epochs:           l.epochs ?? null,
      error_message:    l.error_message || '',
      parameters:       l.parameters ?? {},
    }))
  } catch { trainingLogs.value = [] }
}

// ── Main fetch ─────────────────────────────────────────────
async function fetchAll() {
  loading.value = true
  listVisible.value = false
  await Promise.all([
    fetchModels(), fetchForecasts(), fetchAnomalies(),
    fetchSegments(), fetchRecommendations(), fetchTrainingLogs(),
  ])
  loading.value = false
  requestAnimationFrame(() => { listVisible.value = true })
}

async function refresh() {
  refreshing.value = true
  await fetchAll()
  refreshing.value = false
}

function switchTab(tab: ActiveTab) {
  activeTab.value = tab
  searchQuery.value = ''
}

onMounted(fetchAll)
</script>

<template>
  <div class="ml-page">

    <!-- ── Header ──────────────────────────────────────────── -->
    <header class="page-hd">
      <div>
        <h2 class="page-title">ML Analytics</h2>
        <p class="page-meta">
          {{ stats.totalModels }} modèle{{ stats.totalModels !== 1 ? 's' : '' }} ·
          {{ stats.activeModels }} actifs ·
          {{ stats.unresolvedAnomalies }} anomalie{{ stats.unresolvedAnomalies !== 1 ? 's' : '' }} non résolues
        </p>
      </div>
      <div class="hd-actions">
        <button
          class="btn-ghost btn-icon"
          :class="{ 'btn-icon--spin': refreshing }"
          :disabled="refreshing"
          title="Actualiser"
          @click="refresh"
        >
          <RefreshCcw :size="14" />
        </button>
        <button
          v-if="activeTab === 'models'"
          class="btn-primary"
          @click="openModelDrawer()"
        >
          <Plus :size="15" />
          <span>Nouveau modèle</span>
        </button>
        <button
          v-if="activeTab === 'forecasts'"
          class="btn-primary"
          @click="openForecastDrawer()"
        >
          <Plus :size="15" />
          <span>Nouvelle prévision</span>
        </button>
      </div>
    </header>

    <!-- ── Stats rail ──────────────────────────────────────── -->
    <section class="stats-rail">
      <div class="stat-cell">
        <Brain :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.totalModels }}</span>
        <span class="sc-lbl">Modèles</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Activity :size="15" class="sc-icon sc-icon--ok" />
        <span class="sc-val sc-val--ok">{{ stats.avgAccuracy.toFixed(1) }}%</span>
        <span class="sc-lbl">Précision moy.</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <TrendingUp :size="15" class="sc-icon sc-icon--accent" />
        <span class="sc-val sc-val--accent">{{ stats.totalForecasts }}</span>
        <span class="sc-lbl">Prévisions</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <AlertTriangle :size="15" class="sc-icon sc-icon--warn" />
        <span class="sc-val sc-val--warn">{{ stats.unresolvedAnomalies }}</span>
        <span class="sc-lbl">Anomalies</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Zap :size="15" class="sc-icon sc-icon--crit" />
        <span class="sc-val sc-val--crit">{{ stats.criticalAnomalies }}</span>
        <span class="sc-lbl">Critiques</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-cell">
        <Target :size="15" class="sc-icon" />
        <span class="sc-val">{{ stats.pendingRecs }}</span>
        <span class="sc-lbl">Recommandations</span>
      </div>
    </section>

    <!-- ── Charts row ──────────────────────────────────────── -->
    <div class="charts-row" v-if="!loading">
      <div class="chart-card">
        <p class="chart-title">Précision par modèle</p>
        <div class="chart-area">
          <Bar :data="accuracyChartData" :options="chartOpts" />
        </div>
      </div>
      <div class="chart-card">
        <p class="chart-title">Anomalies par sévérité</p>
        <div class="chart-area">
          <Doughnut :data="anomalySeverityData" :options="donutOpts" />
        </div>
      </div>
    </div>

    <!-- ── Tabs ────────────────────────────────────────────── -->
    <div class="tab-bar" role="tablist">
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'models' }"
        @click="switchTab('models')">
        <Brain :size="14" />
        Modèles
        <span class="tab-badge">{{ models.length }}</span>
      </button>
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'forecasts' }"
        @click="switchTab('forecasts')">
        <TrendingUp :size="14" />
        Prévisions
        <span class="tab-badge">{{ forecasts.length }}</span>
      </button>
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'anomalies' }"
        @click="switchTab('anomalies')">
        <AlertTriangle :size="14" />
        Anomalies
        <span class="tab-badge" :class="stats.criticalAnomalies > 0 ? 'tab-badge--crit' : ''">
          {{ anomalies.length }}
        </span>
      </button>
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'segmentation' }"
        @click="switchTab('segmentation')">
        <Layers :size="14" />
        Segmentation
        <span class="tab-badge">{{ segments.length }}</span>
      </button>
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'recommendations' }"
        @click="switchTab('recommendations')">
        <Zap :size="14" />
        Recommandations
        <span class="tab-badge" :class="stats.pendingRecs > 0 ? 'tab-badge--accent' : ''">
          {{ recommendations.length }}
        </span>
      </button>
      <button role="tab" class="tab" :class="{ 'tab--active': activeTab === 'training_logs' }"
        @click="switchTab('training_logs')">
        <Activity :size="14" />
        Historique entraînement
        <span class="tab-badge">{{ trainingLogs.length }}</span>
      </button>
    </div>

    <!-- ── Search ─────────────────────────────────────────── -->
    <div class="toolbar">
      <div class="search-wrap">
        <Search :size="14" class="search-icon" />
        <input v-model="searchQuery" type="search" class="search-input" placeholder="Rechercher…" />
      </div>
      <!-- Anomaly filter -->
      <template v-if="activeTab === 'anomalies'">
        <div class="select-wrap">
          <select v-model="anomalyFilter" class="filter-select">
            <option value="all">Toutes</option>
            <option value="unresolved">Non résolues</option>
            <option value="critical">Critiques</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
      </template>
      <!-- Rec filter -->
      <template v-if="activeTab === 'recommendations'">
        <div class="select-wrap">
          <select v-model="recFilter" class="filter-select">
            <option value="all">Toutes</option>
            <option value="pending">En attente</option>
            <option value="applied">Appliquées</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
      </template>
      <!-- Training logs filter -->
      <template v-if="activeTab === 'training_logs'">
        <div class="select-wrap">
          <select v-model="trainingLogFilter" class="filter-select">
            <option value="all">Tous les entraînements</option>
            <option value="success">Réussis</option>
            <option value="failed">Échoués</option>
          </select>
          <ChevronDown :size="13" class="select-arrow" />
        </div>
      </template>
    </div>

    <!-- ── Loading ────────────────────────────────────────── -->
    <template v-if="loading">
      <div class="skel-list">
        <div v-for="i in 5" :key="i" class="row-skel"></div>
      </div>
    </template>

    <template v-else>

      <!-- ══ TAB: MODELS ══════════════════════════════════ -->
      <div v-if="activeTab === 'models'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="filteredModels.length === 0" class="empty-state">
          <Brain :size="40" class="empty-icon" />
          <p class="empty-title">Aucun modèle ML</p>
          <p class="empty-sub">Créez votre premier modèle pour démarrer l'analyse prédictive.</p>
          <button class="btn-primary" @click="openModelDrawer()"><Plus :size="14" /><span>Nouveau modèle</span></button>
        </div>

        <div v-else class="data-table">
          <div class="tbl-head">
            <span>Modèle</span>
            <span>Type</span>
            <span>Algorithme</span>
            <span>Statut</span>
            <span>Accuracy</span>
            <span>F1 Score</span>
            <span>RMSE</span>
            <span>MAPE</span>
            <span>Entraîné</span>
            <span></span>
          </div>
          <div
            v-for="(model, i) in filteredModels"
            :key="model.id"
            class="tbl-row"
            :style="{ '--ri': i }"
          >
            <div class="tbl-name-cell">
              <span class="tbl-name">{{ model.name }}</span>
              <span v-if="model.description" class="tbl-desc">{{ model.description }}</span>
              <div v-if="model.tags.length" class="tag-list">
                <span v-for="t in model.tags.slice(0, 3)" :key="t" class="tag">{{ t }}</span>
              </div>
            </div>
            <span class="type-badge" :style="{ '--tc': typeMeta(model.model_type).color }">
              {{ typeMeta(model.model_type).label }}
            </span>
            <span class="mono-cell">{{ model.algorithm || '—' }}</span>
            <span class="status-chip" :class="statusMeta(model.status).cls">
              <component :is="statusMeta(model.status).icon" :size="10" />
              {{ statusMeta(model.status).label }}
            </span>
            <span class="metric-cell" :class="model.accuracy !== null && model.accuracy > 0.85 ? 'metric--good' : model.accuracy !== null && model.accuracy > 0.7 ? 'metric--mid' : 'metric--bad'">
              {{ fmtPct(model.accuracy) }}
            </span>
            <span class="metric-cell">{{ fmtScore(model.f1_score) }}</span>
            <span class="metric-cell">{{ fmtScore(model.rmse) }}</span>
            <span class="metric-cell">{{ model.mape !== null ? `${(model.mape * 100).toFixed(2)}%` : '—' }}</span>
            <span class="tbl-time">{{ timeAgo(model.last_trained) }}</span>
            <div class="tbl-actions">
              <button class="act-btn act-btn--train" title="Entraîner" @click="trainModel(model)">
                <Play :size="12" />
              </button>
              <button class="act-btn" title="Modifier" @click="openModelDrawer(model)"><Pencil :size="12" /></button>
              <template v-if="deleteConfirm === model.id">
                <button class="act-btn act-btn--yes" @click="deleteModel(model.id)">Oui</button>
                <button class="act-btn" @click="deleteConfirm = null">Non</button>
              </template>
              <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = model.id">
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ TAB: FORECASTS ═══════════════════════════════ -->
      <div v-if="activeTab === 'forecasts'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="forecasts.length === 0" class="empty-state">
          <TrendingUp :size="40" class="empty-icon" />
          <p class="empty-title">Aucune prévision</p>
          <p class="empty-sub">Créez des prévisions à partir de vos modèles ML entraînés.</p>
          <button class="btn-primary" @click="openForecastDrawer()"><Plus :size="14" /><span>Nouvelle prévision</span></button>
        </div>

        <div v-else class="forecast-grid">
          <article
            v-for="(fc, i) in forecasts"
            :key="fc.id"
            class="forecast-card"
            :style="{ '--ci': i }"
          >
            <div class="fc-top">
              <span class="fc-period">{{ fc.forecast_period }}</span>
              <span v-if="fc.is_used" class="fc-used-badge">Utilisé</span>
            </div>
            <h3 class="fc-name">{{ fc.name }}</h3>
            <p v-if="fc.description" class="fc-desc">{{ fc.description }}</p>
            <div class="fc-metrics">
              <div class="fc-metric">
                <span class="fc-metric-lbl">Horizon</span>
                <span class="fc-metric-val">{{ fc.horizon }} périodes</span>
              </div>
              <div class="fc-metric">
                <span class="fc-metric-lbl">Confiance</span>
                <span class="fc-metric-val">{{ (fc.confidence_level * 100).toFixed(0) }}%</span>
              </div>
              <div class="fc-metric">
                <span class="fc-metric-lbl">Accuracy</span>
                <span class="fc-metric-val" :class="fc.accuracy !== null && fc.accuracy > 0.8 ? 'metric--good' : ''">
                  {{ fmtPct(fc.accuracy) }}
                </span>
              </div>
              <div class="fc-metric">
                <span class="fc-metric-lbl">MAPE</span>
                <span class="fc-metric-val">{{ fc.mape !== null ? `${(fc.mape * 100).toFixed(2)}%` : '—' }}</span>
              </div>
            </div>
            <div class="fc-footer">
              <span class="fc-time">{{ timeAgo(fc.generated_at) }}</span>
              <div class="fc-actions">
                <button class="act-btn" title="Modifier" @click="openForecastDrawer(fc)"><Pencil :size="12" /></button>
                <template v-if="deleteConfirm === fc.id">
                  <button class="act-btn act-btn--yes" @click="deleteForecast(fc.id)">Oui</button>
                  <button class="act-btn" @click="deleteConfirm = null">Non</button>
                </template>
                <button v-else class="act-btn act-btn--del" title="Supprimer" @click="deleteConfirm = fc.id">
                  <Trash2 :size="12" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>

      <!-- ══ TAB: ANOMALIES ══════════════════════════════ -->
      <div v-if="activeTab === 'anomalies'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="filteredAnomalies.length === 0" class="empty-state">
          <AlertTriangle :size="40" class="empty-icon" />
          <p class="empty-title">Aucune anomalie</p>
          <p class="empty-sub">Aucune anomalie détectée pour les filtres actuels.</p>
        </div>

        <div v-else class="data-table">
          <div class="tbl-head tbl-head--anomaly">
            <span>Détectée le</span>
            <span>Valeur</span>
            <span>Attendu</span>
            <span>Écart</span>
            <span>Sévérité</span>
            <span>Confirmée</span>
            <span>Résolue</span>
            <span></span>
          </div>
          <div
            v-for="(an, i) in filteredAnomalies"
            :key="an.id"
            class="tbl-row tbl-row--anomaly"
            :class="{ 'tbl-row--critical': an.severity === 'critical' && !an.is_resolved }"
            :style="{ '--ri': i }"
          >
            <span class="tbl-time">{{ new Date(an.detected_at).toLocaleString('fr-FR') }}</span>
            <span class="metric-cell metric--bad">{{ an.value.toFixed(2) }}</span>
            <span class="metric-cell">{{ an.expected_value.toFixed(2) }}</span>
            <span class="metric-cell" :class="Math.abs(an.deviation_percentage) > 20 ? 'metric--bad' : 'metric--mid'">
              {{ an.deviation_percentage > 0 ? '+' : '' }}{{ an.deviation_percentage.toFixed(1) }}%
            </span>
            <span class="status-chip" :class="severityMeta(an.severity).cls">
              {{ severityMeta(an.severity).label }}
            </span>
            <span class="bool-cell">
              <CheckCircle2 v-if="an.is_confirmed" :size="14" class="bool--yes" />
              <XCircle v-else :size="14" class="bool--no" />
            </span>
            <span class="bool-cell">
              <CheckCircle2 v-if="an.is_resolved" :size="14" class="bool--yes" />
              <XCircle v-else :size="14" class="bool--no" />
            </span>
            <div class="tbl-actions">
              <button
                v-if="!an.is_confirmed"
                class="act-btn act-btn--confirm"
                title="Confirmer"
                @click="confirmAnomaly(an.id)"
              >
                <CheckCircle2 :size="12" />
              </button>
              <button
                v-if="!an.is_resolved"
                class="act-btn act-btn--resolve"
                title="Résoudre"
                @click="resolveAnomaly(an.id)"
              >
                <Eye :size="12" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ══ TAB: SEGMENTATION ════════════════════════════ -->
      <div v-if="activeTab === 'segmentation'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="segments.length === 0" class="empty-state">
          <Layers :size="40" class="empty-icon" />
          <p class="empty-title">Aucun segment</p>
          <p class="empty-sub">Les résultats de segmentation apparaîtront ici une fois les modèles entraînés.</p>
        </div>

        <div v-else class="segment-grid">
          <article
            v-for="(seg, i) in segments"
            :key="seg.id"
            class="segment-card"
            :style="{ '--ci': i }"
          >
            <div class="seg-top">
              <span class="seg-id">#{{ seg.segment_id }}</span>
              <span class="seg-pct">{{ seg.percentage.toFixed(1) }}%</span>
            </div>
            <h3 class="seg-name">{{ seg.segment_name }}</h3>
            <p v-if="seg.segment_description" class="seg-desc">{{ seg.segment_description }}</p>
            <div class="seg-bar-wrap">
              <div class="seg-bar">
                <div class="seg-bar-fill" :style="{ width: `${Math.min(seg.percentage, 100)}%` }"></div>
              </div>
            </div>
            <div class="seg-metrics">
              <div class="seg-metric"><span class="seg-lbl">Taille</span><span class="seg-val">{{ seg.size.toLocaleString('fr-FR') }}</span></div>
              <div class="seg-metric"><span class="seg-lbl">Moy.</span><span class="seg-val">{{ seg.avg_value.toFixed(2) }}</span></div>
              <div class="seg-metric"><span class="seg-lbl">Min</span><span class="seg-val">{{ seg.min_value.toFixed(2) }}</span></div>
              <div class="seg-metric"><span class="seg-lbl">Max</span><span class="seg-val">{{ seg.max_value.toFixed(2) }}</span></div>
            </div>
          </article>
        </div>
      </div>

      <!-- ══ TAB: RECOMMENDATIONS ═════════════════════════ -->
      <div v-if="activeTab === 'recommendations'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="filteredRecommendations.length === 0" class="empty-state">
          <Zap :size="40" class="empty-icon" />
          <p class="empty-title">Aucune recommandation</p>
          <p class="empty-sub">Les recommandations IA apparaîtront ici.</p>
        </div>

        <div v-else class="rec-list">
          <article
            v-for="(rec, i) in filteredRecommendations"
            :key="rec.id"
            class="rec-card"
            :class="{ 'rec-card--applied': rec.is_applied, 'rec-card--dismissed': rec.is_dismissed }"
            :style="{ '--ci': i }"
          >
            <div class="rec-top">
              <span class="rec-type">{{ rec.recommendation_type }}</span>
              <span class="rec-prio" :class="priorityMeta(rec.priority).cls">
                {{ priorityMeta(rec.priority).label }}
              </span>
              <div class="rec-confidence">
                <span class="rec-conf-lbl">Confiance</span>
                <div class="conf-bar">
                  <div class="conf-fill" :style="{ width: `${(rec.confidence * 100).toFixed(0)}%` }"></div>
                </div>
                <span class="rec-conf-val">{{ (rec.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
            <h3 class="rec-title">{{ rec.title }}</h3>
            <p class="rec-desc">{{ rec.description }}</p>
            <p v-if="rec.reason" class="rec-reason">{{ rec.reason }}</p>
            <div class="rec-footer">
              <span v-if="rec.is_applied" class="rec-status rec-status--applied">
                <CheckCircle2 :size="12" /> Appliqué
              </span>
              <span v-else-if="rec.is_dismissed" class="rec-status rec-status--dismissed">
                <XCircle :size="12" /> Ignoré
              </span>
              <div v-else class="rec-actions">
                <button
                  class="btn-ghost btn-sm"
                  :disabled="applyingId === rec.id"
                  @click="applyRecommendation(rec.id)"
                >
                  <span v-if="applyingId === rec.id" class="spinner"></span>
                  <CheckCircle2 v-else :size="13" />
                  Appliquer
                </button>
                <button class="btn-ghost btn-sm btn-sm--muted" @click="dismissRecommendation(rec.id)">
                  <XCircle :size="13" />
                  Ignorer
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>

      <!-- ══ TAB: TRAINING LOGS ══════════════════════════════ -->
      <div v-if="activeTab === 'training_logs'" class="content-area" :class="{ 'content-area--visible': listVisible }">

        <div v-if="filteredTrainingLogs.length === 0" class="empty-state">
          <Activity :size="40" class="empty-icon" />
          <p class="empty-title">Aucun historique d'entraînement</p>
          <p class="empty-sub">Les sessions d'entraînement apparaîtront ici après l'exécution de modèles.</p>
        </div>

        <table v-else class="tlog-table">
          <thead>
            <tr>
              <th>Modèle</th>
              <th>Statut</th>
              <th>Démarré</th>
              <th>Durée</th>
              <th>Époques</th>
              <th>Accuracy</th>
              <th>Loss</th>
              <th>Erreur</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in filteredTrainingLogs" :key="log.id" class="tlog-row">
              <td class="tlog-model">{{ log.model_name }}</td>
              <td>
                <span
                  class="status-chip"
                  :class="{
                    'st--active':   log.status === 'success' || log.status === 'completed',
                    'st--failed':   log.status === 'failed'  || log.status === 'error',
                    'st--training': log.status === 'running' || log.status === 'training',
                    'st--draft':    log.status === 'pending',
                  }"
                >{{ log.status }}</span>
              </td>
              <td class="tlog-muted">
                {{ log.started_at ? new Date(log.started_at).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—' }}
              </td>
              <td class="tlog-muted">
                {{ log.duration_seconds != null ? (log.duration_seconds < 60 ? `${Math.round(log.duration_seconds)}s` : `${Math.floor(log.duration_seconds/60)}m ${Math.round(log.duration_seconds%60)}s`) : '—' }}
              </td>
              <td class="tlog-muted">{{ log.epochs ?? '—' }}</td>
              <td class="tlog-num">{{ log.accuracy != null ? `${(log.accuracy * 100).toFixed(2)}%` : '—' }}</td>
              <td class="tlog-num">{{ log.loss != null ? log.loss.toFixed(6) : '—' }}</td>
              <td class="tlog-err">{{ log.error_message || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </template>

    <!-- ══ DRAWER: New/Edit Model ══════════════════════════ -->
    <Transition name="drawer-anim">
      <div v-if="modelDrawerOpen" class="drawer-overlay" @click.self="modelDrawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true">
          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editModel ? 'Modifier le modèle' : 'Nouveau modèle ML' }}</h3>
            <button class="drawer-close" @click="modelDrawerOpen = false; editModel = null"><X :size="18" /></button>
          </div>
          <form class="drawer-form" @submit.prevent="submitModel">

            <div class="form-section">
              <p class="form-section-title">Identité</p>
              <div class="form-field">
                <label class="form-label">Nom <span class="req">*</span></label>
                <input v-model="modelForm.name" class="form-input" required placeholder="Ex : Prévision ventes Q4" />
              </div>
              <div class="form-field">
                <label class="form-label">Description</label>
                <textarea v-model="modelForm.description" class="form-textarea" rows="2" placeholder="Objectif du modèle…"></textarea>
              </div>
            </div>

            <div class="form-section">
              <p class="form-section-title">Configuration</p>
              <div class="form-row-2">
                <div class="form-field">
                  <label class="form-label">Type de modèle <span class="req">*</span></label>
                  <div class="select-wrap">
                    <select v-model="modelForm.model_type" class="form-select">
                      <option v-for="(m, k) in MODEL_TYPE_META" :key="k" :value="k">{{ m.label }}</option>
                    </select>
                    <ChevronDown :size="13" class="select-arrow" />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label">Version</label>
                  <input v-model="modelForm.version" class="form-input" placeholder="1.0" />
                </div>
              </div>
              <div class="form-field">
                <label class="form-label">Algorithme</label>
                <input v-model="modelForm.algorithm" class="form-input" placeholder="Ex : Random Forest, LSTM, XGBoost…" />
              </div>
              <div class="form-field">
                <label class="form-label">
                  <input type="checkbox" v-model="modelForm.is_active" class="form-checkbox" />
                  Modèle actif
                </label>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="modelDrawerOpen = false; editModel = null">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="!submitting">{{ editModel ? 'Enregistrer' : 'Créer' }}</span>
                <span v-else class="spinner"></span>
              </button>
            </div>
          </form>
        </aside>
      </div>
    </Transition>

    <!-- ══ DRAWER: New/Edit Forecast ═══════════════════════ -->
    <Transition name="drawer-anim">
      <div v-if="forecastDrawerOpen" class="drawer-overlay" @click.self="forecastDrawerOpen = false">
        <aside class="drawer" role="dialog" aria-modal="true">
          <div class="drawer-hd">
            <h3 class="drawer-title">{{ editForecast ? 'Modifier la prévision' : 'Nouvelle prévision' }}</h3>
            <button class="drawer-close" @click="forecastDrawerOpen = false; editForecast = null"><X :size="18" /></button>
          </div>
          <form class="drawer-form" @submit.prevent="submitForecast">

            <div class="form-section">
              <p class="form-section-title">Identité</p>
              <div class="form-field">
                <label class="form-label">Nom <span class="req">*</span></label>
                <input v-model="forecastForm.name" class="form-input" required placeholder="Ex : Prévision CA Mensuel" />
              </div>
              <div class="form-field">
                <label class="form-label">Description</label>
                <textarea v-model="forecastForm.description" class="form-textarea" rows="2"></textarea>
              </div>
            </div>

            <div class="form-section">
              <p class="form-section-title">Paramètres</p>
              <div class="form-field">
                <label class="form-label">Période <span class="req">*</span></label>
                <div class="select-wrap">
                  <select v-model="forecastForm.forecast_period" class="form-select">
                    <option value="daily">Quotidien</option>
                    <option value="weekly">Hebdomadaire</option>
                    <option value="monthly">Mensuel</option>
                    <option value="quarterly">Trimestriel</option>
                    <option value="yearly">Annuel</option>
                  </select>
                  <ChevronDown :size="13" class="select-arrow" />
                </div>
              </div>
              <div class="form-row-2">
                <div class="form-field">
                  <label class="form-label">Horizon (périodes) <span class="req">*</span></label>
                  <input v-model.number="forecastForm.horizon" class="form-input" type="number" min="1" max="365" required />
                </div>
                <div class="form-field">
                  <label class="form-label">Niveau de confiance</label>
                  <input v-model.number="forecastForm.confidence_level" class="form-input" type="number" step="0.05" min="0.5" max="0.99" />
                </div>
              </div>
            </div>

            <div class="drawer-footer">
              <button type="button" class="btn-ghost" @click="forecastDrawerOpen = false; editForecast = null">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                <span v-if="!submitting">{{ editForecast ? 'Enregistrer' : 'Créer' }}</span>
                <span v-else class="spinner"></span>
              </button>
            </div>
          </form>
        </aside>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.ml-page {
  padding: var(--sp-8);
  display: flex; flex-direction: column;
  gap: var(--sp-6); min-height: 100%;
}

/* ── Header ──────────────────────────────────────────────── */
.page-hd { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--sp-4); }
.page-title { font-family: var(--font-display); font-size: var(--text-2xl); font-weight: 700; letter-spacing: -0.01em; color: var(--text-primary); line-height: 1.2; }
.page-meta { font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--sp-1); }
.hd-actions { display: flex; align-items: center; gap: var(--sp-2); }

/* ── Buttons ─────────────────────────────────────────────── */
.btn-primary {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent); color: var(--text-on-accent);
  border: none; border-radius: var(--radius-md);
  cursor: pointer; font-family: var(--font-ui);
  font-size: var(--text-sm); font-weight: 600;
  min-height: 38px; white-space: nowrap;
  transition: background 150ms, box-shadow 150ms;
}
.btn-primary:hover:not(:disabled) { background: oklch(80% 0.14 62); box-shadow: 0 4px 16px oklch(76% 0.14 62 / 0.28); }
.btn-primary:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-ghost {
  display: flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: none; border: 1px solid var(--border-default);
  border-radius: var(--radius-md); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-secondary); min-height: 38px;
  transition: border-color 150ms, color 150ms;
}
.btn-ghost:hover:not(:disabled) { border-color: var(--border-strong); color: var(--text-primary); }
.btn-ghost:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-sm { min-height: 30px; padding: 0 var(--sp-3); font-size: var(--text-xs); }
.btn-sm--muted:hover { color: var(--error); border-color: var(--error); }

.btn-icon { padding: var(--sp-2); min-height: unset; width: 38px; height: 38px; justify-content: center; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-icon--spin svg { animation: spin 0.7s linear infinite; }

/* ── Stats rail ──────────────────────────────────────────── */
.stats-rail {
  display: flex; align-items: center;
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); overflow: hidden;
}
.stat-cell { flex: 1; display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-4) var(--sp-5); }
.stat-sep { width: 1px; height: 28px; background: var(--border-subtle); flex-shrink: 0; }
.sc-icon        { color: var(--text-muted); flex-shrink: 0; }
.sc-icon--ok    { color: oklch(65% 0.13 148); }
.sc-icon--accent{ color: var(--accent-dim); }
.sc-icon--warn  { color: var(--warning); }
.sc-icon--crit  { color: var(--error); }
.sc-val         { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
.sc-val--ok     { color: oklch(65% 0.13 148); }
.sc-val--accent { color: var(--accent-dim); }
.sc-val--warn   { color: var(--warning); }
.sc-val--crit   { color: var(--error); }
.sc-lbl         { font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; }

/* ── Charts ──────────────────────────────────────────────── */
.charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: var(--sp-4); }
.chart-card {
  background: var(--surface-raised); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); padding: var(--sp-4);
}
.chart-title { font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); margin-bottom: var(--sp-3); }
.chart-area { height: 160px; }

/* ── Tabs ────────────────────────────────────────────────── */
.tab-bar {
  display: flex; gap: var(--sp-1);
  border-bottom: 1px solid var(--border-subtle);
}
.tab {
  display: inline-flex; align-items: center; gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid transparent; border-bottom: none;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: none; cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-sm); font-weight: 500;
  color: var(--text-muted);
  transition: all 150ms;
}
.tab:hover { color: var(--text-secondary); background: var(--surface-overlay); }
.tab--active {
  color: var(--text-primary); background: var(--surface-raised);
  border-color: var(--border-default);
  margin-bottom: -1px; padding-bottom: calc(var(--sp-2) + 1px);
}
.tab-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 20px; height: 18px; padding: 0 5px;
  background: var(--surface-muted); border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 700; color: var(--text-muted);
}
.tab-badge--crit  { background: var(--error-surface);  color: var(--error);   }
.tab-badge--accent{ background: var(--accent-surface); color: var(--accent);  }

/* ── Toolbar ─────────────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; max-width: 320px; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-input {
  width: 100%; height: 38px; padding: 0 var(--sp-4) 0 34px;
  background: var(--surface-raised); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-primary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none;
  transition: border-color 150ms;
}
.search-input:focus { border-color: var(--accent-dim); }
.search-input::placeholder { color: var(--text-muted); }

.select-wrap { position: relative; }
.filter-select {
  appearance: none; height: 38px; padding: 0 30px 0 var(--sp-3);
  background: var(--surface-raised); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-secondary);
  font-family: var(--font-ui); font-size: var(--text-sm); outline: none; cursor: pointer;
}
.filter-select:focus { border-color: var(--accent-dim); }
.filter-select option { background: var(--surface-raised); }
.select-arrow { position: absolute; right: 9px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }

/* ── Content area ────────────────────────────────────────── */
.content-area { opacity: 0; transition: opacity 280ms; }
.content-area--visible { opacity: 1; }

/* ── Table ───────────────────────────────────────────────── */
.data-table { border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; }
.tbl-head {
  display: grid;
  grid-template-columns: 1fr 100px 100px 90px 75px 75px 75px 75px 90px 90px;
  padding: var(--sp-2) var(--sp-4);
  background: var(--surface-overlay);
  border-bottom: 1px solid var(--border-subtle);
  font-family: var(--font-display); font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase; color: var(--text-muted);
}
.tbl-head--anomaly {
  grid-template-columns: 160px 90px 90px 80px 90px 80px 80px 80px;
}
.tbl-row {
  display: grid;
  grid-template-columns: 1fr 100px 100px 90px 75px 75px 75px 75px 90px 90px;
  align-items: center; gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--border-subtle);
  transition: background 100ms;
  opacity: 0; transform: translateY(3px);
  animation: row-in 240ms ease forwards;
  animation-delay: calc(var(--ri, 0) * 25ms);
}
@keyframes row-in { to { opacity: 1; transform: translateY(0); } }
.tbl-row:last-child { border-bottom: none; }
.tbl-row:hover { background: var(--surface-overlay); }
.tbl-row--anomaly { grid-template-columns: 160px 90px 90px 80px 90px 80px 80px 80px; }
.tbl-row--critical { background: oklch(12% 0.03 24 / 0.4); }

.tbl-name-cell { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.tbl-name { font-size: var(--text-sm); font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tbl-desc { font-size: var(--text-xs); color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tag-list { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.tag { font-size: 0.6rem; padding: 1px 6px; border-radius: var(--radius-full); background: var(--surface-muted); color: var(--text-muted); }

.type-badge {
  display: inline-flex; padding: 2px 8px;
  background: color-mix(in oklch, var(--tc) 14%, oklch(10% 0.013 258));
  color: var(--tc); border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
  white-space: nowrap;
}

.mono-cell { font-family: monospace; font-size: var(--text-xs); color: var(--text-secondary); }
.tbl-time { font-size: var(--text-xs); color: var(--text-muted); }

.metric-cell { font-family: var(--font-display); font-size: var(--text-sm); font-weight: 700; color: var(--text-primary); }
.metric--good { color: oklch(65% 0.13 148); }
.metric--mid  { color: var(--accent-dim); }
.metric--bad  { color: var(--error); }

.bool-cell { display: flex; align-items: center; justify-content: center; }
.bool--yes { color: oklch(65% 0.13 148); }
.bool--no  { color: var(--error); }

/* ── Status chips ────────────────────────────────────────── */
.status-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 7px; border-radius: var(--radius-full);
  font-size: 0.62rem; font-weight: 700; white-space: nowrap;
}
.st--active   { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.st--deployed { background: var(--accent-surface); color: var(--accent); }
.st--training { background: oklch(14% 0.04 240); color: oklch(62% 0.13 240); }
.st--inactive { background: var(--surface-muted); color: var(--text-muted); }
.st--failed   { background: var(--error-surface); color: var(--error); }
.st--draft    { background: var(--surface-overlay); color: var(--text-secondary); }

.sev--low      { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); }
.sev--medium   { background: oklch(17% 0.05 80);  color: var(--warning); }
.sev--high     { background: oklch(15% 0.04 50);  color: oklch(76% 0.14 62); }
.sev--critical { background: var(--error-surface); color: var(--error); }

.prio--low     { background: oklch(14% 0.04 148); color: oklch(65% 0.13 148); font-size: 0.62rem; padding: 2px 7px; border-radius: var(--radius-full); font-weight: 700; }
.prio--medium  { background: oklch(17% 0.05 80);  color: var(--warning);       font-size: 0.62rem; padding: 2px 7px; border-radius: var(--radius-full); font-weight: 700; }
.prio--high    { background: oklch(15% 0.04 50);  color: oklch(76% 0.14 62);   font-size: 0.62rem; padding: 2px 7px; border-radius: var(--radius-full); font-weight: 700; }
.prio--crit    { background: var(--error-surface); color: var(--error);         font-size: 0.62rem; padding: 2px 7px; border-radius: var(--radius-full); font-weight: 700; }

/* ── Act buttons ─────────────────────────────────────────── */
.tbl-actions { display: flex; align-items: center; gap: var(--sp-1); justify-content: flex-end; }
.act-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: var(--radius-sm);
  border: 1px solid transparent; background: none;
  color: var(--text-muted); cursor: pointer;
  font-family: var(--font-ui); font-size: var(--text-xs); font-weight: 600;
  transition: all 120ms;
}
.act-btn:hover:not(:disabled) { background: var(--surface-overlay); border-color: var(--border-default); color: var(--text-secondary); }
.act-btn--del:hover { background: var(--error-surface); border-color: var(--error); color: var(--error); }
.act-btn--yes { background: var(--error-surface); border-color: var(--error); color: var(--error); width: auto; padding: 0 var(--sp-2); }
.act-btn--train:hover { background: oklch(14% 0.04 148); border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }
.act-btn--confirm:hover { background: var(--accent-surface); border-color: var(--accent-dim); color: var(--accent); }
.act-btn--resolve:hover { background: oklch(14% 0.04 148); border-color: oklch(65% 0.13 148); color: oklch(65% 0.13 148); }

/* ── Forecast grid ───────────────────────────────────────── */
.forecast-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--sp-4);
}
.forecast-card {
  background: var(--surface-raised); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); padding: var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-3);
  transition: border-color 200ms, box-shadow 200ms;
  opacity: 0; animation: row-in 300ms ease forwards;
  animation-delay: calc(var(--ci, 0) * 40ms);
}
.forecast-card:hover { border-color: var(--border-default); box-shadow: 0 4px 16px oklch(5% 0 0 / 0.3); }
.fc-top { display: flex; align-items: center; justify-content: space-between; }
.fc-period { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); }
.fc-used-badge { font-size: 0.62rem; padding: 2px 7px; background: var(--accent-surface); color: var(--accent); border-radius: var(--radius-full); font-weight: 700; }
.fc-name { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-primary); }
.fc-desc { font-size: var(--text-xs); color: var(--text-secondary); line-height: 1.4; }
.fc-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
.fc-metric { display: flex; flex-direction: column; gap: 2px; }
.fc-metric-lbl { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.fc-metric-val { font-family: var(--font-display); font-size: var(--text-sm); font-weight: 700; color: var(--text-primary); }
.fc-footer { display: flex; align-items: center; justify-content: space-between; padding-top: var(--sp-2); border-top: 1px solid var(--border-subtle); }
.fc-time { font-size: var(--text-xs); color: var(--text-muted); }
.fc-actions { display: flex; gap: var(--sp-1); }

/* ── Segment grid ────────────────────────────────────────── */
.segment-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--sp-4); }
.segment-card {
  background: var(--surface-raised); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); padding: var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-3);
  opacity: 0; animation: row-in 300ms ease forwards;
  animation-delay: calc(var(--ci, 0) * 40ms);
}
.seg-top { display: flex; align-items: center; justify-content: space-between; }
.seg-id { font-size: 0.62rem; font-weight: 700; color: var(--text-muted); }
.seg-pct { font-family: var(--font-display); font-size: var(--text-lg); font-weight: 800; color: var(--accent); }
.seg-name { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-primary); }
.seg-desc { font-size: var(--text-xs); color: var(--text-secondary); }
.seg-bar-wrap { }
.seg-bar { height: 5px; background: var(--surface-muted); border-radius: var(--radius-full); overflow: hidden; }
.seg-bar-fill { height: 100%; background: var(--accent); border-radius: var(--radius-full); transition: width 600ms ease; }
.seg-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--sp-1); }
.seg-metric { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.seg-lbl { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.seg-val { font-family: var(--font-display); font-size: var(--text-xs); font-weight: 700; color: var(--text-primary); }

/* ── Recommendation list ─────────────────────────────────── */
.rec-list { display: flex; flex-direction: column; gap: var(--sp-3); }
.rec-card {
  background: var(--surface-raised); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg); padding: var(--sp-4);
  display: flex; flex-direction: column; gap: var(--sp-3);
  opacity: 0; animation: row-in 240ms ease forwards;
  animation-delay: calc(var(--ci, 0) * 30ms);
}
.rec-card--applied  { opacity: 0.6; }
.rec-card--dismissed{ opacity: 0.4; }
.rec-top { display: flex; align-items: center; gap: var(--sp-3); }
.rec-type { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); }
.rec-confidence { display: flex; align-items: center; gap: var(--sp-2); margin-left: auto; }
.rec-conf-lbl { font-size: 0.62rem; color: var(--text-muted); }
.conf-bar { width: 60px; height: 4px; background: var(--surface-muted); border-radius: var(--radius-full); overflow: hidden; }
.conf-fill { height: 100%; background: var(--accent); border-radius: var(--radius-full); }
.rec-conf-val { font-size: var(--text-xs); font-weight: 700; color: var(--accent); min-width: 28px; }
.rec-title { font-family: var(--font-display); font-size: var(--text-base); font-weight: 700; color: var(--text-primary); }
.rec-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: 1.5; }
.rec-reason { font-size: var(--text-xs); color: var(--text-muted); font-style: italic; }
.rec-footer { display: flex; align-items: center; justify-content: flex-end; gap: var(--sp-2); padding-top: var(--sp-2); border-top: 1px solid var(--border-subtle); }
.rec-status { display: flex; align-items: center; gap: var(--sp-1); font-size: var(--text-xs); font-weight: 600; }
.rec-status--applied  { color: oklch(65% 0.13 148); }
.rec-status--dismissed{ color: var(--text-muted); }
.rec-actions { display: flex; align-items: center; gap: var(--sp-2); }

/* ── Training Logs ───────────────────────────────────────── */
.tlog-table {
  width: 100%; border-collapse: collapse;
  font-size: var(--text-xs);
}
.tlog-table thead tr {
  background: var(--surface-overlay);
  font-family: var(--font-display);
  font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--text-muted);
}
.tlog-table th, .tlog-table td {
  padding: var(--sp-2) var(--sp-3);
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}
.tlog-table tbody tr:last-child td { border-bottom: none; }
.tlog-table tbody tr:hover { background: var(--surface-overlay); }
.tlog-model { font-weight: 600; color: var(--text-primary); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tlog-muted { color: var(--text-muted); }
.tlog-num { font-variant-numeric: tabular-nums; font-weight: 600; }
.tlog-err { color: oklch(64% 0.19 24); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.st--failed { background: oklch(14% 0.05 24); color: oklch(64% 0.19 24); }

/* ── Empty ───────────────────────────────────────────────── */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: var(--sp-4); padding: var(--sp-16) var(--sp-8); text-align: center; }
.empty-icon  { color: var(--text-muted); }
.empty-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-secondary); }
.empty-sub   { font-size: var(--text-sm); color: var(--text-muted); max-width: 40ch; line-height: 1.6; }

/* ── Skeleton ────────────────────────────────────────────── */
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.skel-list { display: flex; flex-direction: column; gap: var(--sp-2); }
.row-skel {
  height: 52px; border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%; animation: shimmer 1.4s infinite;
}
.row-skel:nth-child(2) { animation-delay: 0.07s; }
.row-skel:nth-child(3) { animation-delay: 0.14s; }

/* ── Drawer ──────────────────────────────────────────────── */
.drawer-overlay { position: fixed; inset: 0; background: oklch(5% 0.01 258 / 0.72); z-index: var(--z-modal); display: flex; justify-content: flex-end; }
.drawer { width: 480px; max-width: 100vw; height: 100dvh; background: var(--surface-raised); border-left: 1px solid var(--border-default); display: flex; flex-direction: column; overflow-y: auto; }
.drawer-hd { display: flex; align-items: center; justify-content: space-between; padding: var(--sp-6); border-bottom: 1px solid var(--border-subtle); flex-shrink: 0; position: sticky; top: 0; background: var(--surface-raised); z-index: 1; }
.drawer-title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); }
.drawer-close { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--border-default); background: none; color: var(--text-secondary); cursor: pointer; transition: all 150ms; }
.drawer-close:hover { border-color: var(--border-strong); color: var(--text-primary); }
.drawer-form { display: flex; flex-direction: column; gap: var(--sp-6); padding: var(--sp-6); flex: 1; }
.drawer-footer { display: flex; gap: var(--sp-3); justify-content: flex-end; padding-top: var(--sp-4); margin-top: auto; border-top: 1px solid var(--border-subtle); }

/* ── Form ────────────────────────────────────────────────── */
.form-section { display: flex; flex-direction: column; gap: var(--sp-4); }
.form-section-title { font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-muted); padding-bottom: var(--sp-2); border-bottom: 1px solid var(--border-subtle); }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.form-field { display: flex; flex-direction: column; gap: var(--sp-2); }
.form-label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); display: flex; align-items: center; gap: var(--sp-2); cursor: pointer; }
.form-input { height: 40px; padding: 0 var(--sp-4); background: var(--surface-overlay); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none; transition: border-color 150ms; }
.form-input:focus { border-color: var(--accent-dim); box-shadow: 0 0 0 3px oklch(76% 0.14 62 / 0.12); }
.form-input::placeholder { color: var(--text-muted); }
.form-textarea { padding: var(--sp-3) var(--sp-4); background: var(--surface-overlay); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none; resize: vertical; transition: border-color 150ms; }
.form-textarea:focus { border-color: var(--accent-dim); }
.form-select { height: 40px; padding: 0 30px 0 var(--sp-3); appearance: none; background: var(--surface-overlay); border: 1px solid var(--border-default); border-radius: var(--radius-md); color: var(--text-primary); font-family: var(--font-ui); font-size: var(--text-sm); outline: none; width: 100%; cursor: pointer; }
.form-select:focus { border-color: var(--accent-dim); }
.form-checkbox { width: 16px; height: 16px; accent-color: var(--accent); cursor: pointer; }
.req { color: var(--accent-dim); }

/* ── Spinner ─────────────────────────────────────────────── */
@keyframes spin-sm { to { transform: rotate(360deg); } }
.spinner { display: block; width: 16px; height: 16px; border: 2px solid oklch(14% 0.013 258 / 0.3); border-top-color: var(--text-on-accent); border-radius: 50%; animation: spin-sm 0.7s linear infinite; }

/* ── Drawer animation ────────────────────────────────────── */
.drawer-anim-enter-active { transition: opacity 220ms ease; }
.drawer-anim-leave-active { transition: opacity 180ms ease; }
.drawer-anim-enter-from, .drawer-anim-leave-to { opacity: 0; }
.drawer-anim-enter-active .drawer { transition: transform 380ms cubic-bezier(0.16, 1, 0.3, 1); }
.drawer-anim-leave-active .drawer  { transition: transform 220ms cubic-bezier(0.4, 0, 1, 1); }
.drawer-anim-enter-from .drawer, .drawer-anim-leave-to .drawer { transform: translateX(100%); }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1200px) {
  .forecast-grid, .segment-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .tbl-head, .tbl-row { grid-template-columns: 1fr 90px 90px 80px 65px 65px 65px 65px 80px 80px; }
}
@media (max-width: 900px) {
  .ml-page { padding: var(--sp-6); gap: var(--sp-4); }
  .stats-rail { flex-wrap: wrap; }
  .stat-sep { display: none; }
  .stat-cell { min-width: 33%; }
  .forecast-grid, .segment-grid { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .ml-page { padding: var(--sp-4); }
  .tab-bar { overflow-x: auto; }
}
@media (prefers-reduced-motion: reduce) {
  .tbl-row, .forecast-card, .segment-card, .rec-card { animation: none; opacity: 1; }
  .row-skel { animation: none; }
}
</style>
