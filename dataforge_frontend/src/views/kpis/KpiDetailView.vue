<!--
  KpiDetailView — screen 5 "Détail KPI" of the handoff.

  Reworked from the showcase DeskDetail: a breadcrumb toolbar, a hero
  band (value + delta + target), a "progress to target" Donut, a row
  of KpiCard reference tiles, and a data-lineage panel.

  Everything shown here is a REAL field returned by
  GET /api/visualizations/kpis/:id/ — no fabricated forecast or
  driver series. The only mutations are the two endpoints the list
  view already uses: /calculate/ and /favorites/{add,remove}/.
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'
import {
  ArrowLeft, Target, Clock, Calculator, Star,
  TrendingUp, TrendingDown, Minus, AlertTriangle,
} from 'lucide-vue-next'
import KpiCard from '@/components/ui/KpiCard.vue'
import Donut from '@/components/ui/Donut.vue'
import StatusPill from '@/components/ui/StatusPill.vue'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

// ── Types ──────────────────────────────────────────────────
interface Kpi {
  id: number | string
  name: string
  description?: string
  kpi_type?: string
  kpi_type_display?: string
  dimensional_schema_name?: string | null
  measure_name?: string | null
  target_value?: number | null
  warning_threshold?: number | null
  critical_threshold?: number | null
  format_string?: string | null
  unit?: string
  decimal_places?: number | null
  track_trend?: boolean
  trend_direction?: string
  trend_direction_display?: string
  trend_period?: string
  current_value?: number | null
  previous_value?: number | null
  trend_percentage?: number | null
  last_calculated?: string | null
  status?: string
}

// ── State ──────────────────────────────────────────────────
const kpi         = ref<Kpi | null>(null)
const loading     = ref(true)
const notFound    = ref(false)
const calculating = ref(false)
const starred     = ref(false)
const starBusy    = ref(false)

// ── Metadata ───────────────────────────────────────────────
const STATUS: Record<string, { label: string; tone: 'ok' | 'warn' | 'error' | 'info' }> = {
  success:  { label: 'Atteint',  tone: 'ok'    },
  achieved: { label: 'Atteint',  tone: 'ok'    },
  warning:  { label: 'À risque', tone: 'warn'  },
  at_risk:  { label: 'À risque', tone: 'warn'  },
  critical: { label: 'Critique', tone: 'error' },
  unknown:  { label: 'En cours', tone: 'info'  },
  on_track: { label: 'En cours', tone: 'info'  },
}

const PERIOD: Record<string, string> = {
  daily:     'Quotidienne',
  weekly:    'Hebdomadaire',
  monthly:   'Mensuelle',
  quarterly: 'Trimestrielle',
  yearly:    'Annuelle',
}

// ── Formatting ─────────────────────────────────────────────
function fmtUnit(v: number | null | undefined, unit?: string): string {
  if (v == null) return '—'
  const u = unit || ''
  if (u === 'M€') return `${v.toFixed(2)}M€`
  if (u === '%')  return `${v.toFixed(1)}%`
  if (u === 'x')  return `${v.toFixed(1)}x`
  if (u === 'j')  return `${v.toFixed(1)} j`
  if (u === '€')  return `${v.toLocaleString('fr-FR')} €`
  if (u)          return `${v.toLocaleString('fr-FR')} ${u}`
  return v.toLocaleString('fr-FR')
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

function fmtDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ── Derived ────────────────────────────────────────────────
const statusKey = computed(() => kpi.value?.status || 'unknown')
const statusInfo = computed(() => STATUS[statusKey.value] ?? STATUS.unknown)

const typeLabel = computed(() =>
  kpi.value?.kpi_type_display || kpi.value?.kpi_type || 'KPI',
)

const periodLabel = computed(() => {
  const p = kpi.value?.trend_period
  return p ? (PERIOD[p] ?? p) : '—'
})

const progressPct = computed(() => {
  const k = kpi.value
  if (!k || !k.target_value) return 0
  const value  = k.current_value ?? 0
  const target = k.target_value
  let pct: number
  if (k.trend_direction === 'down' && value > target) {
    // "lower is better" and we're above target → measure how close
    pct = (target / value) * 100
  } else {
    pct = (value / target) * 100
  }
  return Math.max(0, Math.min(Math.round(pct), 100))
})

const progressColor = computed(() => {
  const s = statusKey.value
  if (s === 'success' || s === 'achieved') return 'oklch(70% 0.15 148)'  // green
  if (s === 'warning' || s === 'at_risk')  return 'oklch(78% 0.14 80)'   // amber-warn
  if (s === 'critical')                    return 'oklch(64% 0.19 24)'   // red
  return 'oklch(76% 0.14 62)'                                            // accent — en cours
})

const donutSegments = computed(() => [
  { label: 'Atteint', value: progressPct.value,        color: progressColor.value },
  { label: 'Restant', value: 100 - progressPct.value,  color: 'var(--surface-muted)' },
])

const trendIcon = computed(() => {
  const d = kpi.value?.trend_direction
  if (d === 'up')   return TrendingUp
  if (d === 'down') return TrendingDown
  return Minus
})

const deltaText = computed(() => {
  const k = kpi.value
  const p = k?.trend_percentage ?? 0
  if (!p || k?.trend_direction === 'stable') return 'Stable'
  const sign = k?.trend_direction === 'up' ? '+' : '−'
  return `${sign}${Math.abs(p).toFixed(1)}%`
})

const deltaClass = computed(() => {
  const d = kpi.value?.trend_direction
  if (d === 'up')   return 'delta--pos'
  if (d === 'down') return 'delta--neg'
  return 'delta--flat'
})

// previous → current absolute change, shown on the "previous value" card
const prevDelta = computed<{ text: string; dir: 'up' | 'down' | 'flat' } | null>(() => {
  const k = kpi.value
  if (k?.current_value == null || k?.previous_value == null) return null
  const diff = k.current_value - k.previous_value
  if (Math.abs(diff) < 1e-9) return { text: '0', dir: 'flat' }
  return {
    text: `${diff > 0 ? '+' : '−'}${fmtUnit(Math.abs(diff), k.unit)}`,
    dir:  diff > 0 ? 'up' : 'down',
  }
})

// ── Data ───────────────────────────────────────────────────
async function fetchKpi(id: string) {
  loading.value  = true
  notFound.value = false
  try {
    const { data } = await api.get(`/api/visualizations/kpis/${id}/`)
    kpi.value = data
  } catch {
    kpi.value      = null
    notFound.value = true
  } finally {
    loading.value = false
  }
}

async function fetchStarred(id: string) {
  try {
    const { data } = await api.get('/api/visualizations/favorites/')
    const rows = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : []
    starred.value = rows.some((f: any) => String(f.kpi) === String(id))
  } catch {
    starred.value = false
  }
}

async function calculate() {
  const k = kpi.value
  if (!k || calculating.value) return
  calculating.value = true
  try {
    await api.post(`/api/visualizations/kpis/${k.id}/calculate/`)
    const { data } = await api.get(`/api/visualizations/kpis/${k.id}/`)
    kpi.value = data
  } catch {
    /* ignore — value simply stays as-is */
  } finally {
    calculating.value = false
  }
}

async function toggleStar() {
  const k = kpi.value
  if (!k || starBusy.value) return
  const was = starred.value
  starred.value = !was
  starBusy.value = true
  try {
    const url = was
      ? '/api/visualizations/favorites/remove/'
      : '/api/visualizations/favorites/add/'
    await api.post(url, { item_id: k.id, item_type: 'kpi' })
  } catch {
    starred.value = was
  } finally {
    starBusy.value = false
  }
}

function load(id: string) {
  fetchKpi(id)
  fetchStarred(id)
}

onMounted(() => load(String(route.params.id)))
watch(() => route.params.id, (id) => { if (id) load(String(id)) })
</script>

<template>
  <div class="detail">

    <!-- ── Breadcrumb toolbar ──────────────────────────────── -->
    <nav class="crumbs" aria-label="Fil d'Ariane">
      <RouterLink :to="{ name: 'kpis' }" class="crumb-back">
        <ArrowLeft :size="15" />
        <span>KPIs</span>
      </RouterLink>
      <span class="crumb-sep" aria-hidden="true">/</span>
      <span class="crumb-cur">{{ kpi?.name || 'Détail' }}</span>

      <div v-if="kpi" class="crumb-actions">
        <button
          class="tb-btn"
          :class="{ 'tb-btn--on': starred }"
          :disabled="starBusy"
          :title="starred ? 'Retirer des favoris' : 'Ajouter aux favoris'"
          @click="toggleStar"
        >
          <Star :size="14" :fill="starred ? 'currentColor' : 'none'" />
          <span>{{ starred ? 'Favori' : 'Favori' }}</span>
        </button>
        <button
          class="tb-btn tb-btn--primary"
          :disabled="calculating"
          title="Recalculer la valeur"
          @click="calculate"
        >
          <span v-if="calculating" class="tb-spinner" aria-hidden="true"></span>
          <Calculator v-else :size="14" />
          <span>{{ calculating ? 'Calcul…' : 'Calculer' }}</span>
        </button>
      </div>
    </nav>

    <!-- ── Loading ─────────────────────────────────────────── -->
    <div v-if="loading" class="state">
      <span class="state-spinner" aria-hidden="true"></span>
      <p>Chargement de l'indicateur…</p>
    </div>

    <!-- ── Not found ───────────────────────────────────────── -->
    <div v-else-if="notFound || !kpi" class="state">
      <AlertTriangle :size="28" class="state-icon" />
      <p class="state-title">Indicateur introuvable</p>
      <p class="state-sub">Ce KPI n'existe pas ou a été supprimé.</p>
      <button class="tb-btn tb-btn--primary" @click="router.push({ name: 'kpis' })">
        <ArrowLeft :size="14" /> Retour aux KPIs
      </button>
    </div>

    <!-- ── Content ─────────────────────────────────────────── -->
    <template v-else>
      <!-- Hero band -->
      <header class="hero">
        <div class="hero-meta">
          <span class="type-badge">{{ typeLabel }}</span>
          <StatusPill :tone="statusInfo.tone" :label="statusInfo.label" dot />
        </div>

        <h1 class="hero-name">{{ kpi.name }}</h1>
        <p v-if="kpi.description" class="hero-desc">{{ kpi.description }}</p>

        <div class="hero-value-row">
          <span class="hero-value">{{ fmtUnit(kpi.current_value, kpi.unit) }}</span>
          <span class="hero-delta" :class="deltaClass">
            <component :is="trendIcon" :size="16" :stroke-width="2.2" />
            <span>{{ deltaText }}</span>
          </span>
        </div>

        <div class="hero-sub">
          <span class="hs-item">
            <Target :size="13" />
            Objectif {{ fmtUnit(kpi.target_value, kpi.unit) }}
          </span>
          <span v-if="kpi.last_calculated" class="hs-item">
            <Clock :size="13" />
            Calculé {{ timeAgo(kpi.last_calculated) }}
          </span>
        </div>
      </header>

      <!-- Main grid -->
      <div class="grid">
        <!-- Progress donut -->
        <section class="card donut-card">
          <h2 class="card-title">Progression vers l'objectif</h2>
          <div class="donut-wrap">
            <Donut
              :segments="donutSegments"
              :size="184"
              :thickness="26"
              :center-value="`${progressPct}%`"
              center-label="Atteint"
              :gap="2"
            />
          </div>
          <ul class="legend">
            <li>
              <span class="legend-dot" :style="{ background: progressColor }"></span>
              Atteint <b>{{ progressPct }}%</b>
            </li>
            <li>
              <span class="legend-dot legend-dot--muted"></span>
              Restant <b>{{ 100 - progressPct }}%</b>
            </li>
          </ul>
        </section>

        <!-- Reference tiles -->
        <section class="card refs-card">
          <h2 class="card-title">Repères</h2>
          <div class="refs-grid">
            <KpiCard dense label="Objectif" :value="fmtUnit(kpi.target_value, kpi.unit)" />
            <KpiCard
              dense
              label="Valeur précédente"
              :value="fmtUnit(kpi.previous_value, kpi.unit)"
              :delta="prevDelta?.text"
              :dir="prevDelta?.dir"
            />
            <KpiCard dense label="Seuil d'alerte" :value="fmtUnit(kpi.warning_threshold, kpi.unit)" />
            <KpiCard dense label="Seuil critique" :value="fmtUnit(kpi.critical_threshold, kpi.unit)" />
          </div>
        </section>
      </div>

      <!-- Data lineage -->
      <section class="card lineage">
        <h2 class="card-title">Source de données</h2>
        <dl class="lineage-grid">
          <div class="li">
            <dt>Type</dt>
            <dd>{{ typeLabel }}</dd>
          </div>
          <div class="li">
            <dt>Mesure</dt>
            <dd>{{ kpi.measure_name || '—' }}</dd>
          </div>
          <div class="li">
            <dt>Schéma dimensionnel</dt>
            <dd>{{ kpi.dimensional_schema_name || '—' }}</dd>
          </div>
          <div class="li">
            <dt>Tendance suivie</dt>
            <dd>{{ kpi.track_trend ? (kpi.trend_direction_display || kpi.trend_direction || 'Oui') : 'Non' }}</dd>
          </div>
          <div class="li">
            <dt>Période</dt>
            <dd>{{ periodLabel }}</dd>
          </div>
          <div class="li">
            <dt>Format</dt>
            <dd>{{ kpi.format_string || '—' }}</dd>
          </div>
          <div class="li">
            <dt>Décimales</dt>
            <dd>{{ kpi.decimal_places ?? '—' }}</dd>
          </div>
          <div class="li">
            <dt>Dernier calcul</dt>
            <dd>{{ kpi.last_calculated ? fmtDateTime(kpi.last_calculated) : 'Jamais' }}</dd>
          </div>
        </dl>
      </section>
    </template>
  </div>
</template>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
  padding: var(--sp-6);
  max-width: 1100px;
  margin: 0 auto;
}

/* ── Breadcrumb toolbar ──────────────────────────────────── */
.crumbs {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
}

.crumb-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-low);
  text-decoration: none;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: color var(--duration-fast) var(--ease-out-quart),
              background var(--duration-fast) var(--ease-out-quart);
}
.crumb-back:hover { color: var(--text-hi); background: var(--surface-raised); }

.crumb-sep { color: var(--text-mute); }

.crumb-cur {
  color: var(--text-hi);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.crumb-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out-quart),
              color var(--duration-fast) var(--ease-out-quart),
              background var(--duration-fast) var(--ease-out-quart);
}
.tb-btn:hover:not(:disabled) { border-color: var(--border-default); color: var(--text-hi); }
.tb-btn:disabled { opacity: 0.55; cursor: default; }

.tb-btn--on { color: var(--accent); border-color: oklch(76% 0.14 62 / 0.4); background: var(--accent-surface); }

.tb-btn--primary {
  color: var(--surface-base);
  background: var(--accent);
  border-color: var(--accent);
}
.tb-btn--primary:hover:not(:disabled) { background: var(--accent-dim); border-color: var(--accent-dim); color: var(--surface-base); }

.tb-spinner {
  width: 13px; height: 13px;
  border: 2px solid oklch(20% 0.013 258 / 0.5);
  border-top-color: var(--surface-base);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Hero ────────────────────────────────────────────────── */
.hero {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-6);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.hero-meta { display: flex; align-items: center; gap: var(--sp-2); }

.type-badge {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-low);
  padding: 3px 9px;
  background: var(--surface-muted);
  border-radius: var(--radius-full);
}

.hero-name {
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 1.3rem + 1.6vw, 2.4rem);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.01em;
  color: var(--text-hi);
  margin: 0;
}

.hero-desc {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  max-width: 60ch;
  margin: 0;
}

.hero-value-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-top: var(--sp-2);
}

.hero-value {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(2.5rem, 1.8rem + 3.2vw, 4rem);
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--text-hi);
  font-variant-numeric: tabular-nums;
}

.hero-delta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--font-ui);
  font-size: var(--text-base);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.delta--pos  { color: var(--success); }
.delta--neg  { color: var(--error); }
.delta--flat { color: var(--text-mute); }

.hero-sub {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  flex-wrap: wrap;
  margin-top: var(--sp-1);
}
.hs-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--text-low);
  font-variant-numeric: tabular-nums;
}

/* ── Grid + cards ────────────────────────────────────────── */
.grid {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) 1.6fr;
  gap: var(--sp-4);
}

.card {
  padding: var(--sp-5, 20px);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.card-title {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-low);
  margin: 0 0 var(--sp-4);
}

/* Donut card */
.donut-card { display: flex; flex-direction: column; align-items: center; }
.donut-wrap { display: flex; justify-content: center; padding: var(--sp-2) 0; }

.legend {
  list-style: none;
  margin: var(--sp-4) 0 0;
  padding: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  gap: var(--sp-5, 20px);
}
.legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}
.legend b { color: var(--text-hi); font-variant-numeric: tabular-nums; }
.legend-dot { width: 9px; height: 9px; border-radius: 2px; flex-shrink: 0; }
.legend-dot--muted { background: var(--surface-muted); }

/* Reference tiles */
.refs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3);
}

/* Lineage */
.lineage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--sp-4);
  margin: 0;
}
.li { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.li dt {
  font-family: var(--font-ui);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--text-mute);
}
.li dd {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  color: var(--text-hi);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── States ──────────────────────────────────────────────── */
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
  padding: var(--sp-16) var(--sp-6);
  text-align: center;
  font-family: var(--font-ui);
  color: var(--text-low);
}
.state-title { font-size: var(--text-lg); font-weight: 600; color: var(--text-hi); margin: 0; }
.state-sub { font-size: var(--text-sm); color: var(--text-low); margin: 0; }
.state-icon { color: var(--warning); }
.state-spinner {
  width: 26px; height: 26px;
  border: 2.5px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 820px) {
  .grid { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .detail { padding: var(--sp-4); }
  .refs-grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  .tb-spinner, .state-spinner { animation: none; }
}
</style>
