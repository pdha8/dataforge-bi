<!--
  StatusPill — small inline pill for execution / health / pipeline
  state, used across Pipelines, Executions, Sources, Warehouse.

  Mirrors the showcase's status tones (ok / warn / error / info /
  running / idle / paused) with one consistent shape. Each tone reads
  from a semantic surface + foreground variable pair, so the same
  component flips correctly under a future light theme without code
  changes.

  ## Why not just a div with inline class?

  Status pills appear in 8+ views with subtle drift between them
  (border-radius, padding, icon alignment, colour spelling). One
  component closes that drift and gives a place to add accessibility
  affordances (the `role`, `aria-label`) without touching every view.
-->
<script setup lang="ts">
import { computed } from 'vue'

type Tone =
  | 'ok' | 'success'
  | 'warn' | 'warning'
  | 'error' | 'failed'
  | 'info'
  | 'running'
  | 'paused' | 'idle'
  | 'scheduled' | 'pending'

const props = withDefaults(defineProps<{
  tone?:    Tone
  label:    string
  /** When true a 6px dot leads the label — best for compact rows. */
  dot?:     boolean
  /** Smaller variant for dense tables. */
  size?:    'sm' | 'md'
}>(), {
  tone: 'info',
  dot:  false,
  size: 'md',
})

/**
 * Normalise the many tone aliases we accept from the API into a
 * stable set used for styling. The API uses `success/failed`,
 * older code uses `ok/error`, and some pages use `paused`.
 */
const normalised = computed<'ok' | 'warn' | 'error' | 'info' | 'running' | 'paused' | 'scheduled'>(() => {
  const t = props.tone
  if (t === 'success')   return 'ok'
  if (t === 'warning')   return 'warn'
  if (t === 'failed')    return 'error'
  if (t === 'idle')      return 'paused'
  if (t === 'pending')   return 'scheduled'
  return t as 'ok' | 'warn' | 'error' | 'info' | 'running' | 'paused' | 'scheduled'
})
</script>

<template>
  <span
    class="pill"
    :class="[`pill--${normalised}`, `pill--${size}`]"
    role="status"
    :aria-label="label"
  >
    <span v-if="dot" class="pill__dot" aria-hidden="true" />
    <span class="pill__label">{{ label }}</span>
  </span>
</template>

<style scoped>
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  font-family: var(--font-ui);
  font-weight: 500;
  letter-spacing: 0.01em;
  white-space: nowrap;
  /* tabular-nums so a row of pills with counts (e.g. "12 errors")
     aligns vertically in a table column */
  font-variant-numeric: tabular-nums;
}

.pill--md {
  padding: 3px 10px;
  font-size: var(--text-xs);
  line-height: 1.4;
}

.pill--sm {
  padding: 2px 8px;
  font-size: 11px;
  line-height: 1.3;
  gap: 5px;
}

.pill__dot {
  /* a slightly inset dot — currentColor inherits the foreground tone */
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* ─── Tone variants ───────────────────────────────────────── */

.pill--ok {
  color: var(--success);
  background: var(--success-surface);
  border-color: oklch(70% 0.15 148 / 0.25);
}

.pill--warn {
  color: var(--warning);
  background: var(--warning-surface);
  border-color: oklch(78% 0.14 80 / 0.25);
}

.pill--error {
  color: var(--error);
  background: var(--error-surface);
  border-color: oklch(64% 0.19 24 / 0.25);
}

.pill--info {
  color: var(--info);
  background: var(--info-surface);
  border-color: oklch(67% 0.13 245 / 0.25);
}

.pill--scheduled {
  color: var(--text-secondary);
  background: var(--surface-muted);
  border-color: var(--border-subtle);
}

.pill--paused {
  color: var(--text-low);
  background: var(--surface-muted);
  border-color: var(--border-subtle);
}

/* Running gets a soft pulsing dot so it reads as live state, not
   a static class. Keep at 1.6s — anything faster reads as broken. */
.pill--running {
  color: var(--accent);
  background: var(--accent-surface);
  border-color: oklch(76% 0.14 62 / 0.3);
}

.pill--running .pill__dot {
  animation: pill-pulse 1.6s ease-in-out infinite;
}

@keyframes pill-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .pill--running .pill__dot { animation: none; }
}
</style>
