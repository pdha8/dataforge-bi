<!--
  BrandMark — the DataForge folded-prism logo.

  Lifted from the Claude Design showcase (ssss/tokens.jsx BrandMark) and
  ported to a Vue SFC. The shape is a triangle peak with a smaller
  triangle ridge inside, a tinted fill behind it, and an apex dot.
  Read it as a folded sheet of data catching light.

  Default colour follows --accent so the mark adapts to any future
  theme switch without touching the component.
-->
<script setup lang="ts">
withDefaults(defineProps<{
  /** Width and height in px (square viewBox). */
  size?: number
  /** Stroke and dot colour; pass any CSS colour or a var(--...) literal. */
  accent?: string
  /** Optional aria-label. Omit for purely decorative uses (the SVG
   *  will then be marked aria-hidden). */
  label?: string
}>(), {
  size:   32,
  accent: 'var(--accent)',
  label:  '',
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 40 40"
    fill="none"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : true"
  >
    <!-- Tinted base — keeps the silhouette readable on busy backgrounds -->
    <path d="M6 30L20 6l14 24H6z" :fill="accent" opacity="0.18" />
    <!-- Outer peak -->
    <path
      d="M6 30L20 6l14 24"
      :stroke="accent"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <!-- Inner ridge -->
    <path
      d="M13 30L20 18l7 12"
      :stroke="accent"
      stroke-width="2.2"
      stroke-linejoin="round"
      opacity="0.7"
    />
    <!-- Apex dot -->
    <circle cx="20" cy="6" r="2.2" :fill="accent" />
  </svg>
</template>
