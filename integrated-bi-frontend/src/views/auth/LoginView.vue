<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Eye, EyeOff, AlertCircle } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ email: '', password: '', rememberMe: false })
const errors = reactive({ email: '', password: '' })
const showPassword = ref(false)
const isLoading = ref(false)
const loginError = ref('')
const isVisible = ref(false)
const shaking = ref(false)

onMounted(() => {
  requestAnimationFrame(() => { isVisible.value = true })
})

function validateEmail(): boolean {
  if (!form.email.trim()) {
    errors.email = 'L\'adresse e-mail est requise'
    return false
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Adresse e-mail invalide'
    return false
  }
  errors.email = ''
  return true
}

function validatePassword(): boolean {
  if (!form.password) {
    errors.password = 'Le mot de passe est requis'
    return false
  }
  errors.password = ''
  return true
}

function triggerShake() {
  shaking.value = true
  setTimeout(() => { shaking.value = false }, 500)
}

async function handleSubmit() {
  const validU = validateEmail()
  const validP = validatePassword()
  if (!validU || !validP) { triggerShake(); return }

  isLoading.value = true
  loginError.value = ''

  try {
    await authStore.login(form.email, form.password)
    router.push('/dashboard')
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    loginError.value = status === 401
      ? 'Identifiant ou mot de passe incorrect.'
      : 'Impossible de se connecter. Vérifiez votre connexion.'
    triggerShake()
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-page">

    <!-- ── Left: Form Panel ─────────────────────────── -->
    <section class="form-panel" :class="{ 'form-panel--visible': isVisible }">
      <div class="form-inner">

        <!-- Logo -->
        <div class="logo">
          <span class="logo-mark">IBI</span>
          <span class="logo-sep"></span>
          <span class="logo-label">DataForge BI</span>
        </div>

        <!-- Heading -->
        <div class="form-heading">
          <h1>Connexion</h1>
          <p>Accédez à votre espace analytique</p>
        </div>

        <!-- Global error -->
        <Transition name="error-slide">
          <div v-if="loginError" class="alert-error" role="alert" aria-live="polite">
            <AlertCircle :size="16" class="alert-icon" />
            <span>{{ loginError }}</span>
          </div>
        </Transition>

        <!-- Form -->
        <form
          class="form"
          :class="{ 'form--shaking': shaking }"
          novalidate
          @submit.prevent="handleSubmit"
        >

          <!-- Email -->
          <div class="field" :class="{ 'field--error': errors.email }">
            <label class="field-label" for="email">Identifiant</label>
            <input
              id="email"
              v-model="form.email"
              class="field-input"
              type="email"
              placeholder="votre@email.com"
              autocomplete="email"
              spellcheck="false"
              @blur="validateEmail"
            />
            <Transition name="error-slide">
              <p v-if="errors.email" class="field-message" role="alert">
                {{ errors.email }}
              </p>
            </Transition>
          </div>

          <!-- Password -->
          <div class="field" :class="{ 'field--error': errors.password }">
            <label class="field-label" for="password">Mot de passe</label>
            <div class="field-input-wrap">
              <input
                id="password"
                v-model="form.password"
                class="field-input"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Votre mot de passe"
                autocomplete="current-password"
                @blur="validatePassword"
              />
              <button
                type="button"
                class="eye-btn"
                :aria-label="showPassword ? 'Masquer' : 'Afficher'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" :size="18" />
                <Eye v-else :size="18" />
              </button>
            </div>
            <Transition name="error-slide">
              <p v-if="errors.password" class="field-message" role="alert">
                {{ errors.password }}
              </p>
            </Transition>
          </div>

          <!-- Options row -->
          <div class="form-row">
            <label class="check-label">
              <input v-model="form.rememberMe" type="checkbox" class="check-input" />
              <span class="check-box" aria-hidden="true"></span>
              <span class="check-text">Se souvenir de moi</span>
            </label>
            <a href="#" class="forgot-link">Mot de passe oublié ?</a>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            class="submit-btn"
            :class="{ 'submit-btn--loading': isLoading }"
            :disabled="isLoading"
          >
            <span v-if="!isLoading" class="submit-text">SE CONNECTER</span>
            <span v-else class="spinner" aria-label="Connexion en cours…"></span>
          </button>

        </form>

        <!-- Footer -->
        <p class="panel-footer">&copy; 2026 DataForge BI — Open Source</p>
      </div>
    </section>

    <!-- ── Right: Brand Panel ───────────────────────── -->
    <section class="brand-panel" aria-hidden="true">
      <div class="brand-grid"></div>

      <div class="brand-content">
        <div class="brand-type">
          <span class="brand-word brand-word--a">INTEGRATED</span>
          <span class="brand-word brand-word--b">BUSINESS</span>
          <span class="brand-word brand-word--c">INTELLIGENCE</span>
        </div>

        <p class="brand-tagline">
          Transformez vos données brutes<br>en décisions stratégiques
        </p>

        <div class="brand-stats">
          <div class="stat">
            <span class="stat-value">98.4%</span>
            <span class="stat-label">Disponibilité</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat">
            <span class="stat-value">1.2M</span>
            <span class="stat-label">Événements / jour</span>
          </div>
          <div class="stat-sep"></div>
          <div class="stat">
            <span class="stat-value">+12.3%</span>
            <span class="stat-label">Performance</span>
          </div>
        </div>

        <!-- Decorative bars (abstract bar chart) -->
        <div class="brand-bars" aria-hidden="true">
          <span class="bar" style="--h: 38%"></span>
          <span class="bar" style="--h: 55%"></span>
          <span class="bar" style="--h: 42%"></span>
          <span class="bar" style="--h: 71%"></span>
          <span class="bar" style="--h: 60%"></span>
          <span class="bar" style="--h: 85%"></span>
          <span class="bar" style="--h: 68%"></span>
          <span class="bar" style="--h: 92%"></span>
          <span class="bar" style="--h: 76%"></span>
          <span class="bar" style="--h: 48%"></span>
          <span class="bar" style="--h: 65%"></span>
          <span class="bar" style="--h: 80%"></span>
        </div>
      </div>
    </section>

  </div>
</template>

<style scoped>
/* ── Page Layout ─────────────────────────────────────────── */
.login-page {
  display: grid;
  grid-template-columns: 42% 1fr;
  min-height: 100dvh;
  overflow: hidden;
}

/* ── Form Panel ──────────────────────────────────────────── */
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-12) var(--sp-8);
  background-color: var(--surface-raised);
  position: relative;
  z-index: 1;

  /* Entrance animation */
  opacity: 0;
  transform: translateX(-24px);
  transition:
    opacity var(--duration-enter) var(--ease-out-expo),
    transform var(--duration-enter) var(--ease-out-expo);
}

.form-panel--visible {
  opacity: 1;
  transform: translateX(0);
}

.form-inner {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: var(--sp-8);
}

/* ── Logo ────────────────────────────────────────────────── */
.logo {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.logo-mark {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--accent);
  line-height: 1;
}

.logo-sep {
  display: block;
  width: 1px;
  height: 20px;
  background-color: var(--border-default);
}

.logo-label {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.03em;
}

/* ── Form Heading ────────────────────────────────────────── */
.form-heading h1 {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  line-height: 1.15;
}

.form-heading p {
  margin-top: var(--sp-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ── Alert ───────────────────────────────────────────────── */
.alert-error {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  background-color: var(--error-surface);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--error);
  font-weight: 500;
}

.alert-icon { flex-shrink: 0; }

/* ── Form ────────────────────────────────────────────────── */
.form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  15%       { transform: translateX(-7px); }
  30%       { transform: translateX(7px); }
  45%       { transform: translateX(-5px); }
  60%       { transform: translateX(5px); }
  75%       { transform: translateX(-3px); }
  90%       { transform: translateX(3px); }
}

.form--shaking {
  animation: shake 0.45s var(--ease-out-expo);
}

/* ── Fields ──────────────────────────────────────────────── */
.field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.field-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.field-input-wrap {
  position: relative;
}

.field-input {
  width: 100%;
  height: 48px;
  padding: 0 var(--sp-4);
  background-color: var(--surface-overlay);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: var(--text-base);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  transition:
    border-color var(--duration-fast) ease,
    box-shadow var(--duration-fast) ease;
  outline: none;
}

.field-input-wrap .field-input {
  padding-right: 48px;
}

.field-input::placeholder { color: var(--text-muted); }

.field-input:hover {
  border-color: var(--border-strong);
}

.field-input:focus {
  border-color: var(--accent-dim);
  box-shadow: var(--shadow-focus);
}

.field--error .field-input {
  border-color: var(--error);
  box-shadow: 0 0 0 3px oklch(64% 0.19 24 / 0.12);
}

.field-message {
  font-size: var(--text-xs);
  color: var(--error);
  font-weight: 500;
}

/* ── Eye toggle ──────────────────────────────────────────── */
.eye-btn {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: var(--sp-1);
  transition: color var(--duration-fast) ease;
}

.eye-btn:hover { color: var(--text-secondary); }

/* ── Options row ─────────────────────────────────────────── */
.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
}

.check-label {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  cursor: pointer;
  user-select: none;
}

.check-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.check-box {
  display: block;
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--border-strong);
  border-radius: 4px;
  background-color: var(--surface-overlay);
  flex-shrink: 0;
  transition:
    border-color var(--duration-fast) ease,
    background-color var(--duration-fast) ease;
  position: relative;
}

.check-input:checked + .check-box {
  background-color: var(--accent);
  border-color: var(--accent);
}

.check-input:checked + .check-box::after {
  content: '';
  position: absolute;
  inset: 2px;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 10 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 4l3 3 5-6' stroke='%2311131a' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.check-input:focus-visible + .check-box {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.check-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.forgot-link {
  font-size: var(--text-sm);
  color: var(--accent-dim);
  text-decoration: none;
  font-weight: 500;
  transition: color var(--duration-fast) ease;
  white-space: nowrap;
}

.forgot-link:hover { color: var(--accent); }

/* ── Submit button ───────────────────────────────────────── */
.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 50px;
  background-color: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  transition:
    background-color var(--duration-fast) ease,
    transform var(--duration-fast) ease,
    box-shadow var(--duration-fast) ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: oklch(80% 0.14 62);
  box-shadow: 0 4px 20px oklch(76% 0.14 62 / 0.35);
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
  background-color: var(--accent-dim);
}

.submit-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.submit-text { letter-spacing: 0.1em; }

/* Spinner */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner {
  display: block;
  width: 20px;
  height: 20px;
  border: 2.5px solid oklch(14% 0.013 258 / 0.3);
  border-top-color: var(--text-on-accent);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}

/* ── Panel footer ────────────────────────────────────────── */
.panel-footer {
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-align: center;
  margin-top: var(--sp-4);
}

/* ── Brand Panel ─────────────────────────────────────────── */
.brand-panel {
  position: relative;
  background-color: var(--surface-base);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* Dot grid background */
.brand-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(
    circle,
    oklch(30% 0.01 258) 1px,
    transparent 1px
  );
  background-size: 28px 28px;
  pointer-events: none;
}

.brand-content {
  position: relative;
  z-index: 1;
  padding: var(--sp-12);
  width: 100%;
  max-width: 680px;
  display: flex;
  flex-direction: column;
  gap: var(--sp-10);
}

/* ── Brand Typography ────────────────────────────────────── */
.brand-type {
  display: flex;
  flex-direction: column;
  line-height: 0.9;
}

.brand-word {
  display: block;
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(3.5rem, 8vw, 7rem);
  letter-spacing: -0.02em;
}

.brand-word--a { color: var(--accent); }
.brand-word--b { color: oklch(55% 0.10 62); }
.brand-word--c { color: oklch(38% 0.07 62); }

/* ── Brand tagline ───────────────────────────────────────── */
.brand-tagline {
  font-family: var(--font-ui);
  font-size: var(--text-lg);
  color: var(--text-muted);
  line-height: 1.6;
  font-weight: 400;
  max-width: 42ch;
}

/* ── Brand stats ─────────────────────────────────────────── */
.brand-stats {
  display: flex;
  align-items: center;
  gap: var(--sp-6);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.stat-sep {
  width: 1px;
  height: 36px;
  background-color: var(--border-subtle);
  flex-shrink: 0;
}

/* ── Decorative bar chart ────────────────────────────────── */
.brand-bars {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 72px;
}

@keyframes bar-rise {
  from { transform: scaleY(0); }
  to   { transform: scaleY(1); }
}

.bar {
  display: block;
  flex: 1;
  height: var(--h);
  background-color: oklch(76% 0.14 62 / 0.18);
  border-radius: 3px 3px 0 0;
  transform-origin: bottom;
  animation: bar-rise 0.9s var(--ease-out-expo) both;
}

.bar:nth-child(1)  { animation-delay: 0.05s; }
.bar:nth-child(2)  { animation-delay: 0.10s; }
.bar:nth-child(3)  { animation-delay: 0.15s; }
.bar:nth-child(4)  { animation-delay: 0.20s; }
.bar:nth-child(5)  { animation-delay: 0.25s; }
.bar:nth-child(6)  { animation-delay: 0.30s; }
.bar:nth-child(7)  { animation-delay: 0.35s; }
.bar:nth-child(8)  { animation-delay: 0.40s; }
.bar:nth-child(9)  { animation-delay: 0.45s; }
.bar:nth-child(10) { animation-delay: 0.50s; }
.bar:nth-child(11) { animation-delay: 0.55s; }
.bar:nth-child(12) { animation-delay: 0.60s; }

/* ── Transitions ─────────────────────────────────────────── */
.error-slide-enter-active {
  transition: all 0.2s var(--ease-out-expo);
}
.error-slide-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
.error-slide-leave-active {
  transition: all 0.15s ease;
}
.error-slide-leave-to {
  opacity: 0;
}

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }

  .brand-panel {
    grid-row: 1;
    min-height: 220px;
    padding: var(--sp-8);
  }

  .brand-content {
    gap: var(--sp-4);
    padding: var(--sp-6);
  }

  .brand-word {
    font-size: clamp(2.5rem, 10vw, 4rem);
  }

  .brand-tagline,
  .brand-bars { display: none; }

  .brand-stats { gap: var(--sp-4); }

  .form-panel {
    grid-row: 2;
    padding: var(--sp-8) var(--sp-6);
  }

  .form-panel--visible {
    transform: translateX(0);
  }
}

@media (max-width: 480px) {
  .form-inner { max-width: 100%; }
  .form-row { flex-direction: column; align-items: flex-start; }
}
</style>
