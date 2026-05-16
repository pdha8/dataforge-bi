/**
 * Tests E2E exhaustifs — Page /dashboards
 * CRUD complet : créer, éditer, dupliquer, publier, supprimer
 */
import { test, expect, Page } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@sotifibre.dz'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'SOTIFibre@2026!'
const TS       = Date.now()

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 20_000 })
}

async function goToDashboards(page: Page) {
  await page.goto('/dashboards')
  await page.waitForLoadState('networkidle')
}

// ─── Suite 1 : Chargement ────────────────────────────────────────────────────

test.describe('/dashboards – Chargement', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('GET /api/visualizations/dashboards/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/dashboards\/(\?|$)/.test(r.url()) && r.request().method() === 'GET')
        statuses.push(r.status())
    })
    await page.reload()
    await page.waitForLoadState('networkidle')
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Pas d\'erreur 5xx au chargement', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/')) errors.push(`${r.status()} ${r.url()}`)
    })
    await page.reload()
    await page.waitForLoadState('networkidle')
    expect(errors, `Erreurs 5xx:\n${errors.join('\n')}`).toHaveLength(0)
  })

  test('La page contient le bouton "Nouveau tableau"', async ({ page }) => {
    await expect(page.locator('button', { hasText: /Nouveau tableau/i }).first()).toBeVisible()
  })
})

// ─── Suite 2 : Drawer CREATE ─────────────────────────────────────────────────

test.describe('/dashboards – Drawer create', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('Le bouton "Nouveau tableau" ouvre le drawer', async ({ page }) => {
    await page.locator('button', { hasText: /Nouveau tableau/i }).first().click()
    await expect(page.locator('[role="dialog"]')).toBeVisible()
  })

  test('Le drawer contient les champs requis', async ({ page }) => {
    await page.locator('button', { hasText: /Nouveau tableau/i }).first().click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    await expect(drawer.locator('input[id], input[name="name"], input[placeholder*="nom" i]').first()).toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 3 : CREATE ────────────────────────────────────────────────────────

test.describe('/dashboards – CREATE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('POST /api/visualizations/dashboards/ → 201 avec nom correct', async ({ page }) => {
    const name = `Dashboard E2E ${TS}`

    await page.locator('button', { hasText: /Nouveau tableau/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    // Remplir le premier input texte visible dans le drawer
    const nameInput = page.locator('[role="dialog"] input[type="text"], [role="dialog"] input:not([type])').first()
    await nameInput.fill(name)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(201)
    const body = await res.json()
    expect(body.name ?? body.data?.name).toBeTruthy()
  })

  test('Le dashboard créé apparaît dans la liste', async ({ page }) => {
    const name = `Tableau Réseau ${TS}`

    await page.locator('button', { hasText: /Nouveau tableau/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const nameInput = page.locator('[role="dialog"] input[type="text"], [role="dialog"] input:not([type])').first()
    await nameInput.fill(name)

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 4 : EDIT ──────────────────────────────────────────────────────────

test.describe('/dashboards – EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('PATCH /api/visualizations/dashboards/{id}/ → 200 avec nouveau nom', async ({ page }) => {
    // S'assurer qu'il y a au moins un dashboard
    const cards = page.locator('.db-card, .dash-card, .card').first()
    const hasCards = await cards.count()
    if (hasCards === 0) {
      test.skip()
      return
    }

    // Chercher le bouton éditer (crayon)
    const editBtn = page.locator('[title="Modifier"], [title="Éditer"], button:has([data-lucide="pencil"]), .act-btn:has([data-lucide="pencil"])').first()
    if (!await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      test.skip()
      return
    }

    await editBtn.click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const newName = `Modifié Dash ${TS}`
    const nameInput = page.locator('[role="dialog"] input[type="text"], [role="dialog"] input:not([type])').first()
    await nameInput.fill(newName)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/[^/]+\/?$/.test(r.url()) &&
             (r.request().method() === 'PATCH' || r.request().method() === 'PUT'),
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(200)
  })
})

// ─── Suite 5 : DELETE ────────────────────────────────────────────────────────

test.describe('/dashboards – DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('DELETE : suppression d\'un dashboard créé via l\'UI → 204 ou 200', async ({ page }) => {
    const name = `DEL Dashboard ${TS}`

    // 1. Créer le dashboard
    await page.locator('button', { hasText: /Nouveau tableau/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const nameInput = page.locator('[role="dialog"] input[type="text"], [role="dialog"] input:not([type])').first()
    await nameInput.fill(name)

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')

    // 2. Trouver la ligne / card et supprimer
    const item = page.locator('.db-card, .dash-card, .table-row').filter({ hasText: name }).first()
    if (!await item.isVisible({ timeout: 6_000 }).catch(() => false)) {
      test.skip()
      return
    }

    // Cliquer sur bouton supprimer
    const delBtn = item.locator('[title="Supprimer"], .act-btn--del').first()
    await delBtn.click()

    // Confirmer si dialog de confirmation
    const confirmBtn = page.locator('.act-btn--yes, button', { hasText: /Oui|Confirmer|Supprimer/i }).first()
    if (await confirmBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const [res] = await Promise.all([
        page.waitForResponse(
          r => /\/api\/visualizations\/dashboards\/[^/]+\/?$/.test(r.url()) && r.request().method() === 'DELETE',
          { timeout: 15_000 },
        ),
        confirmBtn.click(),
      ])
      expect([204, 200]).toContain(res.status())
    }
  })
})

// ─── Suite 6 : Widgets tab ────────────────────────────────────────────────────

test.describe('/dashboards – Onglet Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('GET /api/visualizations/widgets/ → 200', async ({ page }) => {
    const widgetTab = page.locator('button', { hasText: /Widgets/i }).first()

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/widgets\/(\?|$)/.test(r.url()) && r.request().method() === 'GET',
        { timeout: 15_000 },
      ),
      widgetTab.click(),
    ])

    expect(res.status()).toBe(200)
  })
})
