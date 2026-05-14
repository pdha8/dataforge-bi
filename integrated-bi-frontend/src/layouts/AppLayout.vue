<script setup lang="ts">
import AppSidebar from '@/components/sidebar/AppSidebar.vue'
import AppHeader from '@/components/header/AppHeader.vue'
import { useSidebar } from '@/composables/useSidebar'

const { collapsed } = useSidebar()
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--collapsed': collapsed }">
    <AppSidebar />
    <div class="app-right">
      <AppHeader />
      <main class="app-content">
        <RouterView v-slot="{ Component, route }">
          <Transition name="page-fade" mode="out-in">
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
}

/* Page transition */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 160ms ease, transform 160ms var(--ease-out-quart);
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 768px) {
  .app-shell { grid-template-columns: 0 1fr; }
  .app-shell--collapsed { grid-template-columns: 0 1fr; }
}
</style>
