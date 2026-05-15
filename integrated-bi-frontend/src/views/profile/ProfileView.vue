<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Mail, Phone, Building2, Briefcase, Shield, Key, Save, CheckCircle2, AlertCircle, Camera, Lock, Globe, Hash } from 'lucide-vue-next'
import api from '@/api/axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

interface ProfileData {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  phone?: string
  department?: string
  job_title?: string
  employee_id?: string
  timezone?: string
  language?: string
  two_factor_enabled?: boolean
  api_access_enabled?: boolean
  api_rate_limit?: number
  role?: string
  date_joined?: string
  last_login?: string
}

const loading = ref(true)
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref('')

// Change password state
const pwdForm = ref({ current_password: '', new_password: '', confirm_password: '' })
const pwdSaving = ref(false)
const pwdSuccess = ref(false)
const pwdError = ref('')

const form = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  department: '',
  job_title: '',
  employee_id: '',
  timezone: 'Africa/Algiers',
  language: 'fr',
  two_factor_enabled: false,
  api_access_enabled: false,
})

const profile = ref<ProfileData | null>(null)

const initials = computed(() => {
  const f = form.value.first_name
  const l = form.value.last_name
  if (f || l) return `${f[0] ?? ''}${l[0] ?? ''}`.toUpperCase()
  return form.value.username?.[0]?.toUpperCase() ?? 'U'
})

const displayName = computed(() => {
  const parts = [form.value.first_name, form.value.last_name].filter(Boolean)
  return parts.join(' ') || form.value.username
})

async function fetchProfile() {
  loading.value = true
  try {
    const { data } = await api.get<ProfileData>('/api/users/me/')
    profile.value = data
    form.value = {
      username: data.username ?? '',
      email: data.email ?? '',
      first_name: data.first_name ?? '',
      last_name: data.last_name ?? '',
      phone: data.phone ?? '',
      department: data.department ?? '',
      job_title: data.job_title ?? '',
      employee_id: data.employee_id ?? '',
      timezone: data.timezone ?? 'Africa/Algiers',
      language: data.language ?? 'fr',
      two_factor_enabled: data.two_factor_enabled ?? false,
      api_access_enabled: data.api_access_enabled ?? false,
    }
  } catch {
    // fallback to auth store user
    const u = auth.user
    if (u) {
      form.value.username = u.username
      form.value.email = u.email
      form.value.first_name = u.first_name
      form.value.last_name = u.last_name
    }
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  saveSuccess.value = false
  saveError.value = ''
  try {
    const id = profile.value?.id ?? auth.user?.id
    const payload: Record<string, unknown> = {
      username: form.value.username,
      email: form.value.email,
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      phone: form.value.phone || undefined,
      department: form.value.department || undefined,
      job_title: form.value.job_title || undefined,
      employee_id: form.value.employee_id || undefined,
      timezone: form.value.timezone || undefined,
      language: form.value.language || undefined,
    }

    const { data } = await api.patch<ProfileData>(`/api/users/users/${id}/`, payload)
    profile.value = data
    auth.setUser({
      id: data.id,
      username: data.username,
      email: data.email,
      first_name: data.first_name,
      last_name: data.last_name,
      role: data.role,
    })
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    saveError.value = err?.response?.data?.detail ?? 'Erreur lors de la sauvegarde.'
  } finally {
    saving.value = false
  }
}

async function toggle2FA() {
  const next = !form.value.two_factor_enabled
  form.value.two_factor_enabled = next
  try {
    const id = profile.value?.id ?? auth.user?.id
    await api.patch(`/api/users/users/${id}/`, { two_factor_enabled: next })
  } catch {
    form.value.two_factor_enabled = !next
  }
}

async function toggleApiAccess() {
  const next = !form.value.api_access_enabled
  form.value.api_access_enabled = next
  try {
    const id = profile.value?.id ?? auth.user?.id
    await api.patch(`/api/users/users/${id}/`, { api_access_enabled: next })
  } catch {
    form.value.api_access_enabled = !next
  }
}

async function changePassword() {
  pwdError.value = ''
  if (!pwdForm.value.current_password || !pwdForm.value.new_password) {
    pwdError.value = 'Veuillez remplir tous les champs.'
    return
  }
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) {
    pwdError.value = 'Les nouveaux mots de passe ne correspondent pas.'
    return
  }
  pwdSaving.value = true
  try {
    const id = profile.value?.id ?? auth.user?.id
    await api.post(`/api/users/users/${id}/change_password/`, {
      current_password: pwdForm.value.current_password,
      new_password:     pwdForm.value.new_password,
    })
    pwdForm.value = { current_password: '', new_password: '', confirm_password: '' }
    pwdSuccess.value = true
    setTimeout(() => { pwdSuccess.value = false }, 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string; current_password?: string[] } } }
    pwdError.value = err?.response?.data?.current_password?.[0]
      ?? err?.response?.data?.detail
      ?? 'Erreur lors du changement de mot de passe.'
  } finally {
    pwdSaving.value = false
  }
}

function formatDate(d?: string) {
  if (!d) return '—'
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(d))
}

onMounted(fetchProfile)
</script>

<template>
  <div class="profile-page">
    <!-- ── Header ───────────────────────────────────────────── -->
    <div class="profile-header">
      <h1 class="page-title">Mon profil</h1>
      <p class="page-sub">Gérez vos informations personnelles et préférences de sécurité.</p>
    </div>

    <!-- ── Skeleton ─────────────────────────────────────────── -->
    <div v-if="loading" class="skeleton-wrap">
      <div class="skel skel-avatar"></div>
      <div class="skel-fields">
        <div class="skel skel-line skel-w60"></div>
        <div class="skel skel-line skel-w40"></div>
        <div class="skel skel-line skel-w80"></div>
        <div class="skel skel-line skel-w60"></div>
      </div>
    </div>

    <!-- ── Content ──────────────────────────────────────────── -->
    <div v-else class="profile-body">

      <!-- Left: avatar + meta -->
      <aside class="profile-aside">
        <div class="avatar-wrap">
          <div class="avatar-circle">{{ initials }}</div>
          <button class="avatar-edit-btn" title="Changer la photo (non disponible)">
            <Camera :size="14" />
          </button>
        </div>
        <div class="aside-name">{{ displayName }}</div>
        <div class="aside-role">{{ profile?.role ?? 'Utilisateur' }}</div>

        <div class="aside-meta">
          <div class="meta-row">
            <span class="meta-label">Membre depuis</span>
            <span class="meta-val">{{ formatDate(profile?.date_joined) }}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Dernière connexion</span>
            <span class="meta-val">{{ formatDate(profile?.last_login) }}</span>
          </div>
        </div>
      </aside>

      <!-- Right: cards -->
      <main class="profile-main">

        <!-- Save feedback -->
        <Transition name="fade">
          <div v-if="saveSuccess" class="alert alert-success">
            <CheckCircle2 :size="16" />
            Profil mis à jour avec succès.
          </div>
        </Transition>
        <Transition name="fade">
          <div v-if="saveError" class="alert alert-error">
            <AlertCircle :size="16" />
            {{ saveError }}
          </div>
        </Transition>

        <!-- ─ Personal info card ──────────────────────────── -->
        <div class="profile-card">
          <div class="card-head">
            <User :size="18" class="card-icon" />
            <h2 class="card-title">Informations personnelles</h2>
          </div>

          <div class="form-grid">
            <div class="form-field">
              <label class="field-label">Prénom</label>
              <input class="field-input" v-model="form.first_name" placeholder="Votre prénom" />
            </div>
            <div class="form-field">
              <label class="field-label">Nom</label>
              <input class="field-input" v-model="form.last_name" placeholder="Votre nom" />
            </div>
            <div class="form-field">
              <label class="field-label">Nom d'utilisateur</label>
              <input class="field-input" v-model="form.username" placeholder="username" />
            </div>
            <div class="form-field">
              <label class="field-label">
                <Mail :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Email
              </label>
              <input class="field-input" type="email" v-model="form.email" placeholder="email@exemple.com" />
            </div>
            <div class="form-field">
              <label class="field-label">
                <Phone :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Téléphone
              </label>
              <input class="field-input" v-model="form.phone" placeholder="+33 6 00 00 00 00" />
            </div>
            <div class="form-field">
              <label class="field-label">
                <Building2 :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Département
              </label>
              <input class="field-input" v-model="form.department" placeholder="ex. Data & Analytics" />
            </div>
            <div class="form-field form-field--full">
              <label class="field-label">
                <Briefcase :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Poste
              </label>
              <input class="field-input" v-model="form.job_title" placeholder="ex. Data Engineer" />
            </div>
            <div class="form-field">
              <label class="field-label">
                <Hash :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Matricule employé
              </label>
              <input class="field-input" v-model="form.employee_id" placeholder="EMP-0042" />
            </div>
            <div class="form-field">
              <label class="field-label">
                <Globe :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Langue
              </label>
              <select class="field-input" v-model="form.language">
                <option value="fr">Français</option>
                <option value="en">English</option>
                <option value="ar">العربية</option>
              </select>
            </div>
            <div class="form-field form-field--full">
              <label class="field-label">
                <Globe :size="13" style="display:inline;vertical-align:-2px;margin-right:4px" />
                Fuseau horaire
              </label>
              <select class="field-input" v-model="form.timezone">
                <option value="Africa/Algiers">Africa/Algiers (GMT+1)</option>
                <option value="Europe/Paris">Europe/Paris (GMT+1/+2)</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">America/New_York</option>
                <option value="Asia/Dubai">Asia/Dubai (GMT+4)</option>
              </select>
            </div>
          </div>

          <div class="card-footer">
            <button class="btn-save" :disabled="saving" @click="saveProfile">
              <Save :size="15" />
              {{ saving ? 'Enregistrement…' : 'Enregistrer' }}
            </button>
          </div>
        </div>

        <!-- ─ Security card ───────────────────────────────── -->
        <div class="profile-card">
          <div class="card-head">
            <Shield :size="18" class="card-icon" />
            <h2 class="card-title">Sécurité</h2>
          </div>

          <div class="toggle-list">
            <!-- 2FA -->
            <div class="toggle-row">
              <div class="toggle-info">
                <span class="toggle-name">Double authentification (2FA)</span>
                <span class="toggle-desc">Protège votre compte avec un second facteur lors de la connexion.</span>
              </div>
              <button
                class="toggle-switch"
                :class="{ 'toggle-switch--on': form.two_factor_enabled }"
                @click="toggle2FA"
                :aria-checked="form.two_factor_enabled"
                role="switch"
                :aria-label="form.two_factor_enabled ? 'Désactiver la 2FA' : 'Activer la 2FA'"
              >
                <span class="toggle-knob"></span>
              </button>
            </div>

            <div class="toggle-divider"></div>

            <!-- API access -->
            <div class="toggle-row">
              <div class="toggle-info">
                <span class="toggle-name">
                  <Key :size="14" style="display:inline;vertical-align:-2px;margin-right:4px" />
                  Accès API
                </span>
                <span class="toggle-desc">Autorise l'utilisation des clés API pour accéder aux ressources de l'application.</span>
              </div>
              <button
                class="toggle-switch"
                :class="{ 'toggle-switch--on': form.api_access_enabled }"
                @click="toggleApiAccess"
                :aria-checked="form.api_access_enabled"
                role="switch"
                :aria-label="form.api_access_enabled ? 'Désactiver l\'accès API' : 'Activer l\'accès API'"
              >
                <span class="toggle-knob"></span>
              </button>
            </div>
          </div>
        </div>

        <!-- ─ Change password card ────────────────────────── -->
        <div class="profile-card">
          <div class="card-head">
            <Lock :size="18" class="card-icon" />
            <h2 class="card-title">Changer le mot de passe</h2>
          </div>

          <Transition name="fade">
            <div v-if="pwdSuccess" class="alert alert-success" style="margin: var(--sp-4) var(--sp-5) 0">
              <CheckCircle2 :size="16" />
              Mot de passe changé avec succès.
            </div>
          </Transition>
          <Transition name="fade">
            <div v-if="pwdError" class="alert alert-error" style="margin: var(--sp-4) var(--sp-5) 0">
              <AlertCircle :size="16" />
              {{ pwdError }}
            </div>
          </Transition>

          <div class="form-grid">
            <div class="form-field form-field--full">
              <label class="field-label">Mot de passe actuel</label>
              <input class="field-input" type="password" v-model="pwdForm.current_password" autocomplete="current-password" placeholder="••••••••" />
            </div>
            <div class="form-field">
              <label class="field-label">Nouveau mot de passe</label>
              <input class="field-input" type="password" v-model="pwdForm.new_password" autocomplete="new-password" placeholder="••••••••" />
            </div>
            <div class="form-field">
              <label class="field-label">Confirmer le nouveau mot de passe</label>
              <input class="field-input" type="password" v-model="pwdForm.confirm_password" autocomplete="new-password" placeholder="••••••••" />
            </div>
          </div>

          <div class="card-footer">
            <button class="btn-save" :disabled="pwdSaving" @click="changePassword">
              <Lock :size="15" />
              {{ pwdSaving ? 'Enregistrement…' : 'Changer le mot de passe' }}
            </button>
          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── Page shell ──────────────────────────────────────────────── */
.profile-page {
  padding: var(--sp-8) var(--sp-6);
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--sp-8);
}

.profile-header { display: flex; flex-direction: column; gap: var(--sp-1); }

.page-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-sub {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin: 0;
}

/* ── Skeleton ────────────────────────────────────────────────── */
.skeleton-wrap {
  display: flex;
  gap: var(--sp-6);
  align-items: flex-start;
}

.skel {
  background: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface-overlay) 50%, var(--surface-raised) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: var(--radius-md);
}

@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.skel-avatar { width: 100px; height: 100px; border-radius: var(--radius-full); flex-shrink: 0; }
.skel-fields { display: flex; flex-direction: column; gap: var(--sp-3); flex: 1; }
.skel-line   { height: 20px; }
.skel-w60    { width: 60%; }
.skel-w40    { width: 40%; }
.skel-w80    { width: 80%; }

/* ── Layout ──────────────────────────────────────────────────── */
.profile-body {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: var(--sp-6);
  align-items: start;
}

/* ── Aside ───────────────────────────────────────────────────── */
.profile-aside {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--sp-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  text-align: center;
}

.avatar-wrap { position: relative; }

.avatar-circle {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-full);
  background: var(--accent-surface);
  color: var(--accent);
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: -0.02em;
}

.avatar-edit-btn {
  position: absolute;
  bottom: 0; right: 0;
  width: 24px; height: 24px;
  border-radius: var(--radius-full);
  background: var(--surface-overlay);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  display: flex; align-items: center; justify-content: center;
  cursor: not-allowed;
  font-size: 0;
}

.aside-name {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.aside-role {
  font-size: var(--text-xs);
  color: var(--accent);
  font-weight: 600;
  background: var(--accent-surface);
  padding: 2px var(--sp-2);
  border-radius: var(--radius-sm);
  text-transform: capitalize;
}

.aside-meta {
  width: 100%;
  border-top: 1px solid var(--border-subtle);
  padding-top: var(--sp-3);
  margin-top: var(--sp-1);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.meta-row { display: flex; flex-direction: column; gap: 2px; text-align: left; }
.meta-label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.meta-val   { font-size: var(--text-xs); color: var(--text-secondary); }

/* ── Main content ────────────────────────────────────────────── */
.profile-main {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* ── Alerts ──────────────────────────────────────────────────── */
.alert {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
}

.alert-success { background: oklch(30% 0.06 145 / 0.3); color: oklch(75% 0.12 145); border: 1px solid oklch(50% 0.1 145 / 0.3); }
.alert-error   { background: oklch(30% 0.06 25 / 0.3);  color: oklch(75% 0.12 25);  border: 1px solid oklch(50% 0.1 25 / 0.3); }

.fade-enter-active, .fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Card ────────────────────────────────────────────────────── */
.profile-card {
  background: var(--surface-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--border-subtle);
}

.card-icon { color: var(--accent); flex-shrink: 0; }

.card-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.01em;
}

/* ── Form grid ───────────────────────────────────────────────── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
  padding: var(--sp-5);
}

.form-field { display: flex; flex-direction: column; gap: var(--sp-1); }
.form-field--full { grid-column: 1 / -1; }

.field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-input {
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  transition: border-color 150ms ease;
  outline: none;
}

.field-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}

.card-footer {
  padding: var(--sp-4) var(--sp-5);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: flex-end;
}

.btn-save {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-4);
  background: var(--accent);
  color: oklch(10% 0 0);
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: var(--font-ui);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity 150ms ease;
}

.btn-save:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-save:not(:disabled):hover { opacity: 0.88; }

/* ── Toggle list ─────────────────────────────────────────────── */
.toggle-list { padding: var(--sp-2); }

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-3);
}

.toggle-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 0 var(--sp-3);
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  min-width: 0;
}

.toggle-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.toggle-desc {
  font-size: var(--text-xs);
  color: var(--text-muted);
  line-height: 1.5;
}

/* Toggle switch */
.toggle-switch {
  flex-shrink: 0;
  width: 44px;
  height: 24px;
  border-radius: var(--radius-full);
  background: var(--surface-overlay);
  border: 1px solid var(--border-default);
  cursor: pointer;
  position: relative;
  transition: background-color 200ms ease, border-color 200ms ease;
  padding: 0;
}

.toggle-switch--on {
  background: var(--accent);
  border-color: var(--accent);
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: var(--radius-full);
  background: var(--text-muted);
  transition: transform 200ms cubic-bezier(0.25, 1, 0.5, 1), background-color 200ms ease;
}

.toggle-switch--on .toggle-knob {
  transform: translateX(20px);
  background: oklch(10% 0 0);
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 700px) {
  .profile-body { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
  .form-field--full { grid-column: 1; }
}
</style>
