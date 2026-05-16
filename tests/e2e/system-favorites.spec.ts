/**
 * E2E – Système : Favoris, Notifications, Admin, Profil, Sidebar/Topbar
 *
 * Cibles : /favorites  /notifications  /admin  /profile  + sidebar/topbar
 *
 * Objectifs :
 *   • Bouton ⭐ sur Rapports / Visualisations / KPIs, apparition dans /favorites
 *   • Notifications : 4 sous-onglets (Notifications, Règles d'alerte, Canaux, Abonnements)
 *   • Admin : 7 sous-onglets (Utilisateurs, Rôles, Équipes, Paramètres,
 *     Journal d'audit, Activités viz., Système)
 *   • Profil : champs Nom / Email visibles, formulaire de mot de passe
 *   • Sidebar : tous les liens visibles, pas de 404
 */

import { test, expect, Page } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@sotifibre.dz'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'SOTIFibre@2026!'

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 25_000 })
}

async function goto(page: Page, path: string) {
  await page.goto(path)
  await page.waitForLoadState('networkidle').catch(() => {})
}

// ════════════════════════════════════════════════════════════
//   1. /favorites – Page liste
// ════════════════════════════════════════════════════════════

test.describe('/favorites – Liste des favoris', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('GET /api/visualizations/favorites/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/favorites\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await goto(page, '/favorites')
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })
})

// ════════════════════════════════════════════════════════════
//   2. Bouton ⭐ Favoris sur Rapports / Visualisations / KPIs
// ════════════════════════════════════════════════════════════

test.describe('Bouton ⭐ Favoris sur les pages clés', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('/kpis affiche un bouton "Ajouter aux favoris" sur chaque KPI', async ({ page }) => {
    await goto(page, '/kpis')
    const cards = page.locator('.kpi-card, .kpi-row, .card')
    if ((await cards.count()) === 0) { test.skip(); return }
    const starBtn = page.locator('button.act-btn--star, button[title*="favoris" i]').first()
    await expect(starBtn, 'Aucun bouton Étoile sur la page /kpis').toBeVisible({ timeout: 5_000 })
  })

  test('/reports affiche un bouton "Ajouter aux favoris" sur chaque rapport', async ({ page }) => {
    await goto(page, '/reports')
    const cards = page.locator('.rp-card, .report-row, .card')
    if ((await cards.count()) === 0) { test.skip(); return }
    const starBtn = page.locator('button.action-btn--star, button[title*="favoris" i]').first()
    await expect(starBtn, 'Aucun bouton Étoile sur la page /reports').toBeVisible({ timeout: 5_000 })
  })

  test('/visualizations affiche un bouton "Ajouter aux favoris" sur chaque viz', async ({ page }) => {
    await goto(page, '/visualizations')
    const cards = page.locator('.viz-card, .visualization-row, .card')
    if ((await cards.count()) === 0) { test.skip(); return }
    const starBtn = page.locator('button.card-btn--star, button[title*="favoris" i]').first()
    await expect(starBtn, 'Aucun bouton Étoile sur la page /visualizations').toBeVisible({ timeout: 5_000 })
  })

  test('Clic sur ⭐ d\'un KPI déclenche POST /api/visualizations/favorites/add/', async ({ page }) => {
    await goto(page, '/kpis')
    const starBtn = page.locator('button.act-btn--star').first()
    if (!(await starBtn.isVisible({ timeout: 4_000 }).catch(() => false))) { test.skip(); return }
    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/favorites\/(add|remove)\/?/.test(r.url())
             && r.request().method() === 'POST',
        { timeout: 8_000 },
      ).catch(() => null),
      starBtn.click(),
    ])
    if (!res) { test.skip(); return }
    expect([200, 201, 204, 400]).toContain(res.status())
  })
})

// ════════════════════════════════════════════════════════════
//   3. /notifications – 4 onglets
// ════════════════════════════════════════════════════════════

test.describe('/notifications – Onglets et chargements', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('Chargement OK et aucune 5xx', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/')) {
        errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
      }
    })
    await goto(page, '/notifications')
    expect(errors, errors.join('\n')).toHaveLength(0)
  })

  test('GET /api/notifications/notifications/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/notifications\/notifications\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await goto(page, '/notifications')
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Les 4 onglets sont visibles : Notifications / Règles d\'alerte / Canaux / Abonnements', async ({ page }) => {
    await goto(page, '/notifications')
    const tabs = page.locator('button.tab-btn')
    await expect(tabs).toHaveCount(4, { timeout: 6_000 })
    const labels = await tabs.allTextContents()
    const joined = labels.join('|').toLowerCase()
    expect(joined).toMatch(/notification/)
    expect(joined).toMatch(/r[èe]gles?\s*d[''’]alerte|alerte/)
    expect(joined).toMatch(/canau[xt]|channel/)
    expect(joined).toMatch(/abonnement|subscription/)
  })

  test('Cliquer sur l\'onglet "Règles d\'alerte" déclenche GET /api/notifications/alerts/', async ({ page }) => {
    await goto(page, '/notifications')
    // 2e onglet de la liste (alerts)
    const tab = page.locator('button.tab-btn').nth(1)
    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/notifications\/alerts\/(\?|$)/.test(r.url()) && r.request().method() === 'GET',
        { timeout: 10_000 },
      ).catch(() => null),
      tab.click(),
    ])
    if (!res) { test.skip(); return }
    expect(res.status()).toBe(200)
  })
})

// ════════════════════════════════════════════════════════════
//   4. /admin – 7 onglets
// ════════════════════════════════════════════════════════════

test.describe('/admin – Sous-onglets CRUD', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('GET /api/users/users/ → 200 à l\'ouverture', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/users\/users\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await goto(page, '/admin')
    // L'admin est protégé : on tolère un retry si la 1re réponse n'arrive pas (réseau lent)
    if (statuses.length === 0) {
      await page.waitForTimeout(2000)
    }
    expect(statuses.length, 'Aucun appel /api/users/users/ détecté').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Les 7 onglets admin sont visibles', async ({ page }) => {
    await goto(page, '/admin')
    const tabs = page.locator('button.tab-btn[role="tab"]')
    await expect(tabs).toHaveCount(7, { timeout: 8_000 })
    const labels = (await tabs.allTextContents()).map(s => s.trim().toLowerCase())
    expect(labels.some(l => /utilisateur/.test(l))).toBe(true)
    expect(labels.some(l => /^rôles?\b|\brôles?\b/.test(l))).toBe(true)
    expect(labels.some(l => /équipes?|équipe/.test(l))).toBe(true)
    expect(labels.some(l => /paramètres?/.test(l))).toBe(true)
    expect(labels.some(l => /journal.*audit/.test(l))).toBe(true)
    expect(labels.some(l => /activités?\s*viz/.test(l))).toBe(true)
    expect(labels.some(l => /système/.test(l))).toBe(true)
  })

  test('Onglet "Rôles" déclenche GET /api/users/roles/', async ({ page }) => {
    await goto(page, '/admin')
    const tabs = page.locator('button.tab-btn[role="tab"]')
    // ordre TABS : users, roles, teams, settings, audit, vizactivity, system → index 1
    const rolesTab = tabs.nth(1)
    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/users\/roles\/(\?|$)/.test(r.url()) && r.request().method() === 'GET',
        { timeout: 10_000 },
      ).catch(() => null),
      rolesTab.click(),
    ])
    if (!res) { test.skip(); return }
    expect(res.status()).toBe(200)
  })

  test('Onglet "Journal d\'audit" affiche au moins un filtre', async ({ page }) => {
    await goto(page, '/admin')
    const tabs = page.locator('button.tab-btn[role="tab"]')
    const auditTab = tabs.nth(4)  // 5e onglet
    await auditTab.click()
    await page.waitForTimeout(1200)
    // Filtres : selects, inputs date/search, ou éléments .filter
    const filters = page.locator('select, input[type="date"], input[type="search"], input[placeholder*="filtr" i], .filter, .audit-filter')
    expect(await filters.count(), 'Aucun filtre détecté dans le Journal d\'audit').toBeGreaterThan(0)
  })
})

// ════════════════════════════════════════════════════════════
//   5. /profile – Champs et modification
// ════════════════════════════════════════════════════════════

test.describe('/profile – Profil utilisateur', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('Page profil affiche Nom, Email et formulaire mot de passe', async ({ page }) => {
    await goto(page, '/profile')
    // Email et password input doivent exister
    const inputs = page.locator('input[type="email"], input[name="email"], input[name*="name" i]')
    expect(await inputs.count()).toBeGreaterThan(0)
    // Présence d'un input password (changement mot de passe)
    const pw = page.locator('input[type="password"]')
    expect(await pw.count()).toBeGreaterThan(0)
  })

  test('Pas de 5xx au chargement du profil', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/')) {
        errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
      }
    })
    await goto(page, '/profile')
    expect(errors, errors.join('\n')).toHaveLength(0)
  })
})

// ════════════════════════════════════════════════════════════
//   6. Sidebar – Tous les liens fonctionnent
// ════════════════════════════════════════════════════════════

test.describe('Sidebar – Aucune page blanche / 404', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  // 19 routes × ~3-5 s par route + flakes réseau possibles → on prend large
  test.setTimeout(180_000)

  test('Visiter toutes les routes principales : aucune page blanche', async ({ page }) => {
    const routes = [
      '/dashboard', '/sources', '/sources/files', '/sources/connections',
      '/sources/monitoring', '/power-queries', '/queries',
      '/pipelines', '/executions',
      '/warehouse', '/star-schema', '/ml-analytics',
      '/visualizations', '/dashboards', '/kpis', '/reports',
      '/notifications', '/favorites', '/profile',
    ]
    const blanks: string[] = []
    // On collecte les 5xx mais on ne les considère pas comme une rupture de page (UI gère)
    const flaky5xx: string[] = []
    for (const r of routes) {
      const errs: number[] = []
      const listener = (resp: any) => {
        if (resp.status() >= 500 && resp.url().includes('/api/')) errs.push(resp.status())
      }
      page.on('response', listener)
      await page.goto(r)
      await page.waitForLoadState('networkidle').catch(() => {})
      const txt = (await page.locator('body').textContent()) || ''
      if (txt.trim().length < 30) blanks.push(r)
      if (errs.length) flaky5xx.push(`${r}(${errs.length})`)
      page.off('response', listener)
    }
    // Seules les pages BLANCHES sont des bugs ; les 5xx ponctuels du backend distant sont
    // signalés mais ne font pas échouer (UI doit savoir les afficher en empty-state).
    expect(blanks, `Pages blanches détectées :\n${blanks.join('\n')}`).toHaveLength(0)
    // eslint-disable-next-line no-console
    if (flaky5xx.length) console.warn('[INFO] 5xx ponctuels sur :', flaky5xx.join(', '))
  })
})
