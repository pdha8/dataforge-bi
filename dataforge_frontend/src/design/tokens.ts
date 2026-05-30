/**
 * Design tokens — TypeScript companion to `src/assets/main.css`.
 *
 * CSS variables remain the source of truth for the UI. This module
 * exposes the same values to JavaScript consumers that cannot read
 * computed style cheaply (Chart.js datasets, canvas primitives, etc.).
 *
 * If you change a value here, update `main.css` in lockstep — and
 * vice versa.
 */

export const FONTS = {
  ui:      "'Figtree', -apple-system, system-ui, sans-serif",
  display: "'Barlow Condensed', 'Figtree', system-ui, sans-serif",
  mono:    "'JetBrains Mono', ui-monospace, monospace",
} as const

/**
 * Brand chart palette — used by Chart.js datasets and any inline SVG
 * that needs concrete colour values rather than CSS variables.
 *
 * Order matters: chart1 is the brand amber, then blue/green/violet.
 * This keeps revenue/primary metrics in the brand accent across all
 * dashboards without per-component lookups.
 */
export const CHART = {
  c1: 'oklch(76% 0.14 62)',
  c2: 'oklch(70% 0.13 245)',
  c3: 'oklch(72% 0.16 148)',
  c4: 'oklch(70% 0.14 310)',
} as const

/** Translucent companions for area fills, hover overlays, etc. */
export const CHART_SOFT = {
  c1: 'oklch(76% 0.14 62 / 0.18)',
  c2: 'oklch(70% 0.13 245 / 0.18)',
  c3: 'oklch(72% 0.16 148 / 0.18)',
  c4: 'oklch(70% 0.14 310 / 0.18)',
} as const

/**
 * Semantic colours mirroring `--success`, `--warning`, `--error`,
 * `--info` from `main.css`. Use these in Chart.js / SVG; in CSS
 * always prefer `var(--success)` etc.
 */
export const SEMANTIC = {
  success: 'oklch(70% 0.15 148)',
  warning: 'oklch(78% 0.14 80)',
  error:   'oklch(64% 0.19 24)',
  info:    'oklch(67% 0.13 245)',
} as const

/** Read a CSS variable at runtime — falls back to the literal token
 *  table above so SSR / unit tests don't crash on `getComputedStyle`. */
export function readToken(name: string, fallback = ''): string {
  if (typeof window === 'undefined' || !document?.documentElement) return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}
