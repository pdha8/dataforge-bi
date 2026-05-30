<!--
  Donut — a lightweight SVG ring chart, ported from the ssss showcase
  (tokens.jsx Donut). Used on the KPI detail screen for "progress to
  target" and composition breakdowns.

  Unlike Chart.js this stays a pure SVG: no canvas, crisp at any DPI,
  and it can host a centred value label cheaply. Pass concrete colour
  strings (oklch / hex / var(--...)) per segment — the component does
  not reach into the token table itself.
-->
<script setup lang="ts">
import { computed } from 'vue'

interface Segment {
  label: string
  value: number
  color: string
}

const props = withDefaults(defineProps<{
  segments: Segment[]
  size?:        number
  thickness?:   number
  /** Big number shown in the middle (e.g. "88%"). Omit to hide. */
  centerValue?: string
  /** Small caption under the center value. */
  centerLabel?: string
  /** Track (unfilled ring) colour. */
  trackColor?:  string
  /** Gap in degrees between segments — keeps slices visually distinct. */
  gap?:         number
}>(), {
  size:       150,
  thickness:  24,
  centerValue: '',
  centerLabel: '',
  trackColor: 'var(--surface-muted)',
  gap:        0,
})

const r  = computed(() => props.size / 2 - props.thickness / 2)
const cx = computed(() => props.size / 2)
const C  = computed(() => 2 * Math.PI * r.value)

const total = computed(() =>
  props.segments.reduce((s, seg) => s + Math.max(0, seg.value), 0) || 1,
)

/** Pre-compute each arc's dash length + offset so the template stays declarative. */
const arcs = computed(() => {
  let acc = 0
  const gapLen = (props.gap / 360) * C.value
  return props.segments.map((seg) => {
    const share = Math.max(0, seg.value) / total.value
    const dash  = Math.max(0, share * C.value - gapLen)
    const offset = -acc
    acc += share * C.value
    return { color: seg.color, dash, gap: C.value - dash, offset }
  })
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    :viewBox="`0 0 ${size} ${size}`"
    role="img"
    class="donut"
  >
    <!-- Track -->
    <circle
      :cx="cx" :cy="cx" :r="r"
      fill="none"
      :stroke="trackColor"
      :stroke-width="thickness"
    />
    <!-- Segments -->
    <circle
      v-for="(a, i) in arcs"
      :key="i"
      :cx="cx" :cy="cx" :r="r"
      fill="none"
      :stroke="a.color"
      :stroke-width="thickness"
      :stroke-dasharray="`${a.dash} ${a.gap}`"
      :stroke-dashoffset="a.offset"
      stroke-linecap="butt"
      :transform="`rotate(-90 ${cx} ${cx})`"
      class="donut__seg"
    />
    <!-- Center label -->
    <text
      v-if="centerValue"
      :x="cx"
      :y="centerLabel ? cx - 2 : cx"
      text-anchor="middle"
      dominant-baseline="central"
      class="donut__value"
    >{{ centerValue }}</text>
    <text
      v-if="centerLabel"
      :x="cx"
      :y="cx + 16"
      text-anchor="middle"
      dominant-baseline="central"
      class="donut__caption"
    >{{ centerLabel }}</text>
  </svg>
</template>

<style scoped>
.donut { display: block; }

.donut__seg {
  transition: stroke-dasharray 600ms var(--ease-out-expo);
}

.donut__value {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  fill: var(--text-hi);
  letter-spacing: -0.01em;
}

.donut__caption {
  font-family: var(--font-ui);
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  fill: var(--text-mute);
}

@media (prefers-reduced-motion: reduce) {
  .donut__seg { transition: none; }
}
</style>
