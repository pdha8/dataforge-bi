import { ref } from 'vue'

const collapsed = ref(false)
const mobileOpen = ref(false)

function isMobile(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches
}

export function useSidebar() {
  function toggle() {
    if (isMobile()) {
      mobileOpen.value = !mobileOpen.value
    } else {
      collapsed.value = !collapsed.value
    }
  }

  function closeMobile() {
    mobileOpen.value = false
  }

  return { collapsed, mobileOpen, toggle, closeMobile }
}
