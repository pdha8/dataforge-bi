<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/sidebar/AppSidebar.vue'
import AppHeader from '@/components/header/AppHeader.vue'
import { useSidebar } from '@/composables/useSidebar'

const { collapsed, mobileOpen, closeMobile } = useSidebar()
const route = useRoute()

watch(() => route.path, () => {
  if (mobileOpen.value) closeMobile()
})
</script>

<template>
  <div
    class="app-shell"
    :class="{
      'app-shell--collapsed': collapsed,
      'app-shell--mobile-open': mobileOpen,
    }"
  >
    <AppSidebar />

    <Transition name="backdrop-fade">
      <div
        v-if="mobileOpen"
        class="mobile-backdrop"
        aria-hidden="true"
        @click="closeMobile"
      ></div>
    </Transition>

    <div class="app-right">
      <AppHeader />
      <main class="app-content">
        <RouterView v-slot="{ Component, route }">
          <Transition name="page-fade">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100dvh;
  transition: grid-template-columns 320ms cubic-bezier(0.25, 1, 0.5, 1);
}

.app-shell--collapsed {
  grid-template-columns: 64px 1fr;
}

.app-right {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  overflow: hidden;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  background-color: var(--surface-base);
  position: relative;
}

/* Page transition — leave element is absolutely positioned so the entering
   component is already in the DOM; the container never collapses to zero height */
.page-fade-enter-active {
  transition: opacity 160ms ease 80ms, transform 160ms var(--ease-out-quart) 80ms;
}
.page-fade-leave-active {
  transition: opacity 160ms ease, transform 160ms var(--ease-out-quart);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  pointer-events: none;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Mobile backdrop — only visible when drawer is open on small screens */
.mobile-backdrop {
  display: none;
}

@media (max-width: 768px) {
  /* Sidebar is position: fixed on mobile (out of grid flow), so the grid
     becomes single-column to let .app-right take the full viewport width. */
  .app-shell,
  .app-shell--collapsed {
    grid-template-columns: 1fr;
  }

  .mobile-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: oklch(0% 0 0 / 0.5);
    z-index: calc(var(--z-modal) - 1);
  }
  .backdrop-fade-enter-active,
  .backdrop-fade-leave-active {
    transition: opacity 220ms ease;
  }
  .backdrop-fade-enter-from,
  .backdrop-fade-leave-to {
    opacity: 0;
  }
}
</style>
