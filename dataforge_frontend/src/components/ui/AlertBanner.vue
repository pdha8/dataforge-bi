<!--
  AlertBanner — the dismissible-or-actionable notification surface
  used on Dashboard, Notifications, and Pipelines detail panes.

  Three tones (warn / success / info) match the showcase's alerts
  feed and the Notifications system. The component intentionally
  does NOT use a coloured left stripe — that pattern is banned in
  the design system because it screams "AI dashboard template."
  Instead, the icon and tinted background carry the tone, and the
  full border ties it back to the surface system.
-->
<script setup lang="ts">
import { computed } from 'vue'
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-vue-next'

type Tone = 'warn' | 'success' | 'info' | 'error'

const props = withDefaults(defineProps<{
  tone?:        Tone
  title:        string
  body?:        string
  /** Optional metadata line — e.g. "4 min ago". */
  meta?:        string
  /** When true the banner shows a close affordance and emits @dismiss. */
  dismissible?: boolean
}>(), {
  tone:        'info',
  dismissible: false,
})

defineEmits<{ dismiss: [] }>()

const iconMap = {
  warn:    AlertTriangle,
  success: CheckCircle2,
  info:    Info,
  error:   AlertTriangle,
} as const

const IconComp = computed(() => iconMap[props.tone])
</script>

<template>
  <div class="alert" :class="`alert--${tone}`" role="status">
    <div class="alert__icon" aria-hidden="true">
      <component :is="IconComp" :size="18" :stroke-width="2" />
    </div>

    <div class="alert__content">
      <p class="alert__title">{{ title }}</p>
      <p v-if="body" class="alert__body">{{ body }}</p>
      <p v-if="meta" class="alert__meta">{{ meta }}</p>
    </div>

    <!-- Slot for an inline action — "View pipeline", "Acknowledge", … -->
    <div v-if="$slots.action" class="alert__action">
      <slot name="action" />
    </div>

    <button
      v-if="dismissible"
      class="alert__close"
      type="button"
      aria-label="Fermer la notification"
      @click="$emit('dismiss')"
    >
      <X :size="16" :stroke-width="2" />
    </button>
  </div>
</template>

<style scoped>
.alert {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  align-items: start;
  gap: var(--sp-3);

  padding: var(--sp-3) var(--sp-4);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: var(--surface-raised);
}

.alert__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  /* the icon tile carries the tone tint so the body text
     keeps full contrast on the raised surface */
}

.alert__content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert__title {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-hi);
  line-height: 1.4;
}

.alert__body {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.5;
  /* Body lines stop short of the meta column so they don't crowd
     the action button on narrow widths. */
  max-width: 65ch;
}

.alert__meta {
  font-size: 11px;
  color: var(--text-mute);
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}

.alert__action {
  align-self: center;
}

.alert__close {
  align-self: start;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--text-low);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out-quart),
              color      var(--duration-fast) var(--ease-out-quart);
}

.alert__close:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

/* ─── Tone variants ──────────────────────────────────────── */

.alert--warn {
  background: var(--warning-surface);
  border-color: oklch(78% 0.14 80 / 0.3);
}
.alert--warn .alert__icon { color: var(--warning); background: oklch(78% 0.14 80 / 0.15); }

.alert--success {
  background: var(--success-surface);
  border-color: oklch(70% 0.15 148 / 0.3);
}
.alert--success .alert__icon { color: var(--success); background: oklch(70% 0.15 148 / 0.15); }

.alert--info {
  background: var(--info-surface);
  border-color: oklch(67% 0.13 245 / 0.3);
}
.alert--info .alert__icon { color: var(--info); background: oklch(67% 0.13 245 / 0.15); }

.alert--error {
  background: var(--error-surface);
  border-color: oklch(64% 0.19 24 / 0.3);
}
.alert--error .alert__icon { color: var(--error); background: oklch(64% 0.19 24 / 0.15); }

/* Stack vertically on narrow screens so the title and action
   don't fight for the same line. */
@media (max-width: 520px) {
  .alert {
    grid-template-columns: auto 1fr auto;
  }
  .alert__action {
    grid-column: 1 / -1;
    align-self: stretch;
  }
}
</style>
