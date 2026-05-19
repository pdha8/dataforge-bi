import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://192.168.224.128:8000',
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
  // ─── Build prod (Render free tier = 512Mo, on optimise la mémoire) ──────
  build: {
    target: 'es2020',
    sourcemap: false,           // pas de source maps en prod = moins de RAM
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        // Vite 8 utilise rolldown qui exige manualChunks en FONCTION (pas en objet).
        // Découpe les grosses libs dans des chunks séparés → meilleur cache navigateur.
        manualChunks(id: string) {
          if (id.includes('node_modules')) {
            if (id.includes('chart.js') || id.includes('vue-chartjs')) return 'chart-vendor'
            if (id.includes('@headlessui') || id.includes('lucide-vue') || id.includes('@vueuse')) return 'ui-vendor'
            if (id.includes('/vue/') || id.includes('vue-router') || id.includes('pinia')) return 'vue-vendor'
          }
        },
      },
    },
  },
})
