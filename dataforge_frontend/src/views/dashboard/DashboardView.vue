<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  PointElement, LineElement,
  BarElement, ArcElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line, Bar, Doughnut } from 'vue-chartjs'
import api from '@/api/axios'
import { CHART, CHART_SOFT, SEMANTIC } from '@/design/tokens'
import {
  TrendingUp, TrendingDown, Minus,
  RefreshCcw, Activity,
  CheckCircle2, XCircle, AlertTriangle,
} from 'lucide-vue-next'

ChartJS.register(
  CategoryScale, LinearScale,
  PointElement, LineElement,
  BarElement, ArcElement,
  Title, Tooltip, Legend, Filler
)

// ── Types ─────────────────────────────────────────────────
interface KpiItem {
  id?: string | number
  name: string
  value: string | number
  unit?: string
  trend_direction?: 'up' | 'down' | 'stable'
  trend_percentage?: number | null
}

interface ActivityItem {
  id?: string | number
  title: string
  message?: string
  created_at: string
  notification_type?: string
  is_read?: boolean
}

function mapKpi(k: any): KpiItem {
  return {
    id:               k.id,
    name:             k.name || '',
    value:            k.current_value ?? 0,
    unit:             k.unit || undefined,
    trend_direction:  k.trend_direction || 'stable',
    trend_percentage: k.trend_percentage ?? null,
  }
}

function mapActivity(n: any): ActivityItem {
  return {
    id:                n.id,
    title:             n.title || '',
    message:           n.message || undefined,
    created_at:        n.created_at,
    notification_type: n.notification_type || 'system_alert',
    is_read:           n.status === 'read' || n.read_at !== null,
  }
}

const router = useRouter()

// ── State ─────────────────────────────────────────────────
const kpis           = ref<KpiItem[]>([])
const activity       = ref<ActivityItem[]>([])
const loadKpis       = ref(true)
const loadActivity   = ref(true)
const refreshing     = ref(false)
const lastUpdated    = ref(new Date())
const markingAllRead = ref(false)
const markingReadId  = ref<string | number | null>(null)

// ── Chart palette ─────────────────────────────────────────
// Sourced from the DataForge design tokens (src/design/tokens.ts)
// so charts stay in lockstep with the rest of the design system.
const C = {
  amber:      CHART.c1,
  amberFill:  CHART_SOFT.c1,
  blue:       CHART.c2,
  blueFill:   CHART_SOFT.c2,
  green:      CHART.c3,
  violet:     CHART.c4,
  red:        SEMANTIC.error,
  muted:      '#5C6B7C',
  grid:       'oklch(30% 0.015 255)',
  text:       '#8492A2',
  textPri:    '#F1E8DC',
  tipBg:      '#1A232E',
  tipBorder:  '#28333F',
}

const tooltipDefaults = {
  backgroundColor: C.tipBg,
  borderColor:     C.tipBorder,
  borderWidth:     1,
  titleColor:      C.textPri,
  bodyColor:       C.text,
  titleFont:       { family: 'Barlow Condensed', size: 13, weight: 'bold' as const },
  bodyFont:        { family: 'Figtree', size: 12 },
  padding:         12,
  cornerRadius:    8,
}

// ── Chart: Line ───────────────────────────────────────────
const lineData = {
  labels: ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'],
  datasets: [
    {
      label: 'Événements (×1000)',
      data: [850,920,890,1100,1050,1150,1200,1080,1250,1300,1180,1400],
      borderColor: C.amber,
      backgroundColor: C.amberFill,
      borderWidth: 2,
      pointRadius: 3,
      pointBackgroundColor: C.amber,
      pointHoverRadius: 5,
      fill: true,
      tension: 0.35,
    },
    {
      label: 'Pipelines exécutés',
      data: [120,135,128,162,148,170,185,158,192,204,178,220],
      borderColor: C.blue,
      backgroundColor: C.blueFill,
      borderWidth: 2,
      pointRadius: 3,
      pointBackgroundColor: C.blue,
      pointHoverRadius: 5,
      fill: false,
      tension: 0.35,
    },
  ],
}

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  resizeDelay: 150,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: {
      position: 'top' as const,
      align: 'end' as const,
      labels: {
        color: C.text,
        font: { family: 'Figtree', size: 11 },
        boxWidth: 10, boxHeight: 10,
        usePointStyle: true, pointStyle: 'circle' as const,
        padding: 16,
      },
    },
    tooltip: { ...tooltipDefaults, usePointStyle: true },
  },
  scales: {
    x: {
      grid: { color: C.grid },
      ticks: { color: C.text, font: { family: 'Figtree', size: 11 } },
      border: { display: false },
    },
    y: {
      grid: { color: C.grid },
      ticks: {
        color: C.text,
        font: { family: 'Figtree', size: 11 },
        callback(value: string | number) {
          const n = Number(value)
          return n >= 1000 ? `${(n / 1000).toFixed(0)}k` : value
        },
      },
      border: { display: false },
    },
  },
}

// ── Chart: Bar ────────────────────────────────────────────
const barData = {
  labels: ['CSV', 'API REST', 'PostgreSQL', 'Excel', 'Oracle', 'MySQL'],
  datasets: [{
    label: 'Pipelines',
    data: [45, 32, 28, 18, 14, 10],
    backgroundColor: [C.amber, C.blue, C.violet, C.green, SEMANTIC.warning, SEMANTIC.info],
    borderRadius: 5,
    borderSkipped: false as const,
  }],
}

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  resizeDelay: 150,
  plugins: {
    legend: { display: false },
    tooltip: tooltipDefaults,
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: C.text, font: { family: 'Figtree', size: 11 } },
      border: { display: false },
    },
    y: {
      grid: { color: C.grid },
      ticks: { color: C.text, font: { family: 'Figtree', size: 11 } },
      border: { display: false },
    },
  },
}

// ── Chart: Donut ──────────────────────────────────────────
const donutData = {
  labels: ['Succès', 'En cours', 'Erreur', 'Arrêté'],
  datasets: [{
    data: [68, 20, 7, 5],
    backgroundColor: [C.green, C.amber, C.red, C.muted],
    borderColor: '#121A23',
    borderWidth: 3,
    hoverOffset: 6,
  }],
}

const donutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false as const,
  resizeDelay: 150,
  cutout: '65%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        color: C.text,
        font: { family: 'Figtree', size: 11 },
        padding: 12,
        boxWidth: 10, boxHeight: 10,
        usePointStyle: true, pointStyle: 'circle' as const,
      },
    },
    tooltip: tooltipDefaults,
  },
}

// ── Helpers ───────────────────────────────────────────────
function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `il y a ${hrs} h`
  return `il y a ${Math.floor(hrs / 24)} j`
}

function trendIcon(d?: string) {
  if (d === 'up')   return TrendingUp
  if (d === 'down') return TrendingDown
  return Minus
}

function trendClass(d?: string) {
  if (d === 'up')   return 'trend--up'
  if (d === 'down') return 'trend--down'
  return 'trend--stable'
}

function activityIcon(t?: string) {
  if (t === 'pipeline_complete' || t === 'kpi_target_reached' || t === 'report_ready') return CheckCircle2
  if (t === 'pipeline_failed'   || t === 'system_alert' || t === 'anomaly_detected')   return XCircle
  if (t === 'kpi_alert'         || t === 'maintenance')                                return AlertTriangle
  return Activity
}

function activityIconClass(t?: string) {
  if (t === 'pipeline_complete' || t === 'kpi_target_reached' || t === 'report_ready') return 'ai--success'
  if (t === 'pipeline_failed'   || t === 'system_alert' || t === 'anomaly_detected')   return 'ai--error'
  if (t === 'kpi_alert'         || t === 'maintenance')                                return 'ai--warning'
  return 'ai--info'
}

// ── API ───────────────────────────────────────────────────
async function fetchKpis() {
  loadKpis.value = true
  try {
    const { data } = await api.get('/api/visualizations/kpis/')
    const rows = Array.isArray(data?.results) ? data.results
                : Array.isArray(data)          ? data
                : []
    kpis.value = rows.map(mapKpi)
  } catch {
    kpis.value = []
  } finally {
    loadKpis.value = false
  }
}

async function fetchActivity() {
  loadActivity.value = true
  try {
    const { data } = await api.get('/api/notifications/notifications/?page_size=6')
    const rows = Array.isArray(data?.results) ? data.results
                : Array.isArray(data)          ? data
                : []
    activity.value = rows.map(mapActivity)
  } catch {
    activity.value = []
  } finally {
    loadActivity.value = false
  }
}

async function markAllRead() {
  markingAllRead.value = true
  try {
    await api.post('/api/notifications/notifications/mark_all_read/', {})
    activity.value.forEach(a => { a.is_read = true })
  } catch { /* ignore */ }
  finally { markingAllRead.value = false }
}

async function markOneRead(item: ActivityItem) {
  if (item.is_read || markingReadId.value) return
  markingReadId.value = item.id ?? null
  try {
    if (item.id) await api.post(`/api/notifications/notifications/${item.id}/mark_read/`, {})
    item.is_read = true
  } catch { /* ignore */ }
  finally { markingReadId.value = null }
}

async function refresh() {
  refreshing.value = true
  await Promise.all([fetchKpis(), fetchActivity()])
  lastUpdated.value = new Date()
  refreshing.value = false
}

onMounted(() => {
  fetchKpis()
  fetchActivity()
})
</script>

<template>
  <div class="dashboard">

    <!-- ── Page header ──────────────────────────────────── -->
    <header class="dash-header">
      <div>
        <h2 class="dash-title">Vue d'ensemble</h2>
        <p class="dash-meta">
          Données en temps réel · Mis à jour {{ timeAgo(lastUpdated.toISOString()) }}
        </p>
      </div>
      <button
        class="refresh-btn"
        :class="{ 'refresh-btn--spinning': refreshing }"
        :disabled="refreshing"
        title="Actualiser les données"
        @click="refresh"
      >
        <RefreshCcw :size="15" />
        <span>Actualiser</span>
      </button>
    </header>

    <!-- ── KPI Rail ─────────────────────────────────────── -->
    <section class="kpi-rail" aria-label="Indicateurs clés">

      <template v-if="loadKpis">
        <div v-for="i in 4" :key="i" class="kpi-skel"></div>
      </template>

      <template v-else>
        <div
          v-for="kpi in kpis.slice(0, 4)"
          :key="kpi.id ?? kpi.name"
          class="kpi-item"
        >
          <div class="kpi-value">{{ kpi.value }}<span v-if="kpi.unit" class="kpi-unit">{{ kpi.unit }}</span></div>
          <div class="kpi-name">{{ kpi.name }}</div>
          <div class="kpi-trend" :class="trendClass(kpi.trend_direction)">
            <component :is="trendIcon(kpi.trend_direction)" :size="12" />
            <span v-if="kpi.trend_percentage">
              {{ kpi.trend_direction === 'down' ? '−' : '+' }}{{ Math.abs(kpi.trend_percentage).toFixed(1) }}%
            </span>
            <span v-else>stable</span>
          </div>
        </div>
      </template>

    </section>

    <!-- ── Dashboard Grid ───────────────────────────────── -->
    <div class="dash-grid">

      <!-- Area / Line chart -->
      <section class="panel panel--line">
        <div class="panel-hd">
          <span class="panel-title">Tendance des données</span>
          <span class="panel-meta">2026 · mensuel</span>
        </div>
        <div class="chart-wrap chart-wrap--lg">
          <Line :data="lineData" :options="(lineOptions as never)" />
        </div>
      </section>

      <!-- Activity feed -->
      <section class="panel panel--feed">
        <div class="panel-hd">
          <span class="panel-title">Activité récente</span>
          <div class="panel-hd-actions">
            <span class="notif-count">{{ activity.filter(a => !a.is_read).length }} nouvelles</span>
            <button
              v-if="activity.some(a => !a.is_read)"
              class="mark-all-btn"
              :disabled="markingAllRead"
              @click="markAllRead"
            >{{ markingAllRead ? '…' : 'Tout marquer comme lu' }}</button>
            <button class="see-all-link" @click="router.push('/notifications')">Voir toutes</button>
          </div>
        </div>

        <div class="feed-list">
          <template v-if="loadActivity">
            <div v-for="i in 5" :key="i" class="feed-skel"></div>
          </template>
          <template v-else>
            <div
              v-for="item in activity"
              :key="item.id ?? item.created_at"
              class="feed-item"
              :class="{ 'feed-item--unread': !item.is_read }"
              style="cursor: pointer"
              @click="markOneRead(item)"
            >
              <span class="feed-icon" :class="activityIconClass(item.notification_type)">
                <component :is="activityIcon(item.notification_type)" :size="14" />
              </span>
              <div class="feed-body">
                <p class="feed-title">{{ item.title }}</p>
                <p v-if="item.message" class="feed-msg">{{ item.message }}</p>
                <span class="feed-time">{{ timeAgo(item.created_at) }}</span>
              </div>
              <span v-if="!item.is_read" class="unread-dot" aria-label="Non lu"></span>
            </div>
          </template>
        </div>
      </section>

      <!-- Bar chart -->
      <section class="panel panel--bar">
        <div class="panel-hd">
          <span class="panel-title">Pipelines par source</span>
          <span class="panel-meta">ce mois</span>
        </div>
        <div class="chart-wrap chart-wrap--md">
          <Bar :data="barData" :options="(barOptions as never)" />
        </div>
      </section>

      <!-- Donut chart -->
      <section class="panel panel--donut">
        <div class="panel-hd">
          <span class="panel-title">Statuts pipelines</span>
          <span class="panel-meta">en direct</span>
        </div>
        <div class="chart-wrap chart-wrap--md">
          <Doughnut :data="donutData" :options="(donutOptions as never)" />
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
/* ── Layout ──────────────────────────────────────────────── */
.dashboard {
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
}

/* ── Header ──────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-4);
}

.dash-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.2;
}

.dash-meta {
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
  transition: border-color 150ms ease, color 150ms ease, background-color 150ms ease;
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--accent-dim);
  color: var(--accent);
  background-color: var(--accent-surface);
}

.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.refresh-btn--spinning svg { animation: spin 0.7s linear infinite; }

/* ── KPI Rail ────────────────────────────────────────────── */
.kpi-rail {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.kpi-item {
  padding: var(--sp-6);
  background-color: var(--surface-raised);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.kpi-item + .kpi-item {
  border-left: 1px solid var(--border-subtle);
}

.kpi-value {
  font-family: var(--font-display);
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1;
}

.kpi-unit {
  font-size: 1.1rem;
  margin-left: 2px;
}

.kpi-name {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 500;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 600;
  margin-top: var(--sp-1);
}

.trend--up     { color: oklch(70% 0.15 148); }
.trend--down   { color: var(--error); }
.trend--stable { color: var(--text-muted); }

/* KPI skeleton */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

.kpi-skel {
  padding: var(--sp-6);
  background-color: var(--surface-raised);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.kpi-skel::before,
.kpi-skel::after {
  content: '';
  display: block;
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

.kpi-skel::before { height: 36px; width: 55%; }
.kpi-skel::after  { height: 13px; width: 75%; animation-delay: 0.15s; }

/* ── Dashboard grid ──────────────────────────────────────── */
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 300px;
  grid-template-areas:
    "line  line  feed"
    "bar   donut feed";
  gap: var(--sp-6);
}

/* ── Panels ──────────────────────────────────────────────── */
.panel {
  background-color: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-6);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  min-width: 0;
}

.panel--line  { grid-area: line; }
.panel--feed  { grid-area: feed; overflow: hidden; }
.panel--bar   { grid-area: bar; }
.panel--donut { grid-area: donut; }

.panel-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-shrink: 0;
}

.panel-title {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.panel-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.notif-count {
  font-size: var(--text-xs);
  color: var(--accent-dim);
  font-weight: 600;
}

.panel-hd-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.mark-all-btn,
.see-all-link {
  background: none;
  border: none;
  padding: 0;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--text-muted);
  cursor: pointer;
  transition: color 150ms ease;
  white-space: nowrap;
}

.mark-all-btn:hover:not(:disabled),
.see-all-link:hover {
  color: var(--accent);
}

.mark-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.see-all-link {
  font-weight: 600;
}

.feed-item--unread .feed-title {
  color: var(--text-primary);
}

.feed-item:not(.feed-item--unread) {
  opacity: 0.75;
}

/* ── Chart wrappers ──────────────────────────────────────── */
.chart-wrap { position: relative; flex: 1; }
.chart-wrap--lg { height: 260px; }
.chart-wrap--md { height: 190px; }

/* ── Activity feed ───────────────────────────────────────── */
.feed-list {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex: 1;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
}

.feed-item:last-child { border-bottom: none; }

.feed-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  margin-top: 1px;
}

.ai--success { background-color: oklch(15% 0.05 148); color: oklch(70% 0.15 148); }
.ai--error   { background-color: var(--error-surface); color: var(--error); }
.ai--warning { background-color: oklch(17% 0.05 80);  color: var(--warning); }
.ai--info    { background-color: var(--accent-surface); color: var(--accent-dim); }

.feed-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feed-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-msg {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feed-time {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: 2px;
}

.unread-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--accent);
  flex-shrink: 0;
  margin-top: 7px;
}

/* Feed skeleton */
.feed-skel {
  display: flex;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--border-subtle);
}

.feed-skel::before {
  content: '';
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  background: linear-gradient(90deg, var(--surface-overlay) 25%, var(--surface-muted) 50%, var(--surface-overlay) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.feed-skel::after {
  content: '';
  flex: 1;
  height: 40px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--surface-overlay) 25%, var(--surface-muted) 50%, var(--surface-overlay) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  animation-delay: 0.1s;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 1280px) {
  .dash-grid {
    grid-template-columns: 1fr 1fr;
    grid-template-areas:
      "line  line"
      "bar   donut"
      "feed  feed";
  }
}

@media (max-width: 900px) {
  .dashboard { padding: var(--sp-6); }
  .kpi-rail  { grid-template-columns: 1fr 1fr; }
  .dash-grid {
    grid-template-columns: 1fr;
    grid-template-areas: "line" "bar" "donut" "feed";
  }
}

@media (max-width: 600px) {
  .kpi-rail { grid-template-columns: 1fr; }
  .chart-wrap--lg { height: 200px; }
  .chart-wrap--md { height: 160px; }
}

@media (max-width: 480px) {
  .dashboard { padding: var(--sp-4); }
}

/* ── Reduced motion ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .kpi-skel::before, .kpi-skel::after,
  .feed-skel::before, .feed-skel::after {
    animation: none;
  }
}
</style>
