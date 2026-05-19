<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// Rehydrate profile on app boot if we have a token but no valid user
// (handles refresh after login + recovery from corrupted localStorage)
onMounted(() => {
  if (auth.isAuthenticated && !auth.user) {
    auth.fetchProfile()
  }
})
</script>

<template>
  <RouterView />
</template>
