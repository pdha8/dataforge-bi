<!--
  KpiCard — the signature tile of the showcase. One large value, a
  short label above, a delta with direction below, and an optional
  sparkline tucked against the right edge.

  This is the most-repeated visual unit across Dashboard, KPIs
  detail, and the mobile showcase. Centralising it here means:
   - the typography pairing (Barlow Condensed display for the
     number, Figtree for everything else) stays correct
   - direction colours (up = success, down = error, but with a flip
     for "lower is better" metrics like Churn) are decided once
   - the sparkline slot stays a slot — wire it to vue-chartjs or
     pass an inline SVG, the card doesn't care
-->
<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  /** Short label above the number — "Revenue MTD", "Churn (90d)". */
  label:    string
  /** The formatted value — keep the formatting (currency, %, ×) in the parent. */
  value:    string | number
  /** Pre-formatted delta string, e.g. "+12.4%" or "−0.27pt". */
  delta?:   string
  /** Trend direction. `inverse` is true when "down is good"
   *  (churn, error rate, etc.) so we flip the colour mapping. */
  dir?:     'up' | 'down' | 'flat'
  inverse?: boolean
  /** Optional small accent hint — e.g. "88% to target". */
  hint?:    string
  /** Tighter padding for grids of 4+ cards on smaller screens. */
  dense?:   boolean
}>(), {
  dir:     'flat',
  inverse: false,
  dense:   false,
})

/**
 * Map (direction, inverse) → tone.
 *
 * inverse=false  up → ok    down → error  (revenue, conversion)
 * inverse=true   up → error down → ok     (churn, error rate)
 */
const deltaTone = computed<'ok' | 'error' | 'muted'>(() => {
  if (props.dir === 'flat') return 'muted'
  if (props.dir === 'up')   return props.inverse ? 'error' : 'ok'
  return props.inverse ? 'ok' : 'error'
})
</script>

<template>
  <article class="kpi" :class="{ 'kpi--dense': dense }">
    <header class="kpi__head">
      <p class="kpi__label">{{ label }}</p>
      <p v-if="hint" class="kpi__hint">{{ hint }}</p>
    </header>

    <div class="kpi__body">
      <p class="kpi__value">{{ value }}</p>

      <p
        v-if="delta"
        class="kpi__delta"
        :class="`kpi__delta--${deltaTone}`"
      >
        <ArrowUpRight   v-if="dir === 'up'"   :size="14" :stroke-width="2" />
        <ArrowDownRight v-if="dir === 'down'" :size="14" :stroke-width="2" />
        <Minus          v-if="dir === 'flat'" :size="14" :stroke-width="2" />
        <span>{{ delta }}</span>
      </p>
    </div>

    <!-- Optional spark / chart / illustration — host whatever -->
    <div v-if="$slots.spark" class="kpi__spark">
      <slot name="spark" />
    </div>
  </article>
</template>

<style scoped>
.kpi {
  position: relative;
  display: grid;
  /* head sits at the top, body fills, spark anchors to the right
     and spans both rows so it reaches from label-row to value-row */
  grid-template-columns: 1fr auto;
  grid-template-rows: auto 1fr;
  gap: var(--sp-2) var(--sp-4);

  padding: var(--sp-4) var(--sp-4) var(--sp-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);

  transition:
    border-color var(--duration-fast) var(--ease-out-quart),
    transform    var(--duration-base) var(--ease-out-quart);
}

.kpi--dense {
  padding: var(--sp-3);
  gap: var(--sp-1) var(--sp-3);
}

.kpi:hover {
  border-color: var(--border-default);
}

.kpi__head {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  min-width: 0;
}

.kpi__label {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--text-low);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  /* don't let long labels push the hint off-screen */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kpi__hint {
  font-size: 11px;
  color: var(--text-mute);
  font-variant-numeric: tabular-nums;
}

.kpi__body {
  grid-column: 1;
  grid-row: 2;
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.kpi__value {
  /* Barlow Condensed shines at large sizes — this is its job. */
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(1.6rem, 1.2rem + 1.5vw, 2.25rem);
  line-height: 1;
  letter-spacing: -0.01em;
  color: var(--text-hi);
  font-variant-numeric: tabular-nums;
}

.kpi--dense .kpi__value {
  font-size: clamp(1.4rem, 1.1rem + 1vw, 1.75rem);
}

.kpi__delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.kpi__delta--ok    { color: var(--success); }
.kpi__delta--error { color: var(--error); }
.kpi__delta--muted { color: var(--text-mute); }

.kpi__spark {
  grid-column: 2;
  grid-row: 1 / span 2;
  display: flex;
  align-items: flex-end;
  /* keep the spark out of the way of long values — it never wins
     against the number, it's there to confirm the direction */
  min-width: 64px;
  max-width: 120px;
  opacity: 0.85;
}
</style>
