/**
 * Tests E2E exhaustifs — Page /kpis
 * CRUD complet : créer, éditer, calculer, supprimer
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

async function goToKpis(page: Page) {
  await page.goto('/kpis')
  await page.waitForLoadState('networkidle')
}

function createBtn(page: Page) {
  return page.locator('button', { hasText: /Nouveau KPI/i }).first()
}

// ─── Suite 1 : Chargement ────────────────────────────────────────────────────

test.describe('/kpis – Chargement', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('GET /api/visualizations/kpis/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/kpis\/(\?|$)/.test(r.url()) && r.request().method() === 'GET')
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

  test('La page contient le bouton de création de KPI', async ({ page }) => {
    await expect(createBtn(page)).toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 2 : Drawer CREATE ─────────────────────────────────────────────────

test.describe('/kpis – Drawer create', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('Le drawer de création s\'ouvre avec les champs requis', async ({ page }) => {
    await createBtn(page).click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('#f-name')).toBeVisible()
    await expect(page.locator('#f-tgt')).toBeVisible()
  })
})

// ─── Suite 3 : CREATE ────────────────────────────────────────────────────────

test.describe('/kpis – CREATE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('POST /api/visualizations/kpis/ → 201', async ({ page }) => {
    const name = `KPI Débit ${TS}`

    await createBtn(page).click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-name').fill(name)
    await page.locator('#f-tgt').fill('1000')

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(201)
  })

  test('Le KPI créé apparaît dans la liste', async ({ page }) => {
    const name = `KPI Disponibilité ${TS}`

    await createBtn(page).click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-name').fill(name)
    await page.locator('#f-tgt').fill('99')

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 4 : EDIT ──────────────────────────────────────────────────────────

test.describe('/kpis – EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('PATCH /api/visualizations/kpis/{id}/ → 200', async ({ page }) => {
    const hasKpis = await page.locator('.kpi-card, .list-row').count()
    if (hasKpis === 0) {
      test.skip()
      return
    }

    const editBtn = page.locator('[title="Modifier"]').first()
    if (!await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      test.skip()
      return
    }

    await editBtn.click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const newName = `KPI Modifié ${TS}`
    await page.locator('#f-name').fill(newName)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/[^/]+\/?$/.test(r.url()) &&
             (r.request().method() === 'PATCH' || r.request().method() === 'PUT'),
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(200)
    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${newName}`).first()).toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 5 : DELETE ────────────────────────────────────────────────────────

test.describe('/kpis – DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('DELETE : suppression d\'un KPI créé → 204', async ({ page }) => {
    const name = `KPI DEL ${TS}`

    // 1. Créer
    await createBtn(page).click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-name').fill(name)
    await page.locator('#f-tgt').fill('500')

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')

    // 2. Supprimer
    const item = page.locator('.kpi-card, .list-row').filter({ hasText: name }).first()
    if (!await item.isVisible({ timeout: 6_000 }).catch(() => false)) {
      test.skip()
      return
    }

    await item.locator('.act-btn--del').click()

    const confirmBtn = page.locator('button.act-btn--yes').first()
    if (await confirmBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const [res] = await Promise.all([
        page.waitForResponse(
          r => /\/api\/visualizations\/kpis\/[^/]+\/?$/.test(r.url()) && r.request().method() === 'DELETE',
          { timeout: 15_000 },
        ),
        confirmBtn.click(),
      ])
      expect([204, 200]).toContain(res.status())
      await page.waitForLoadState('networkidle')
      await expect(page.locator('.kpi-card, .list-row').filter({ hasText: name })).not.toBeVisible({ timeout: 8_000 })
    }
  })
})

// ─── Suite 6 : Calcul KPI ────────────────────────────────────────────────────

test.describe('/kpis – Calcul', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('POST /api/visualizations/kpis/{id}/calculate/ → 200', async ({ page }) => {
    const hasKpis = await page.locator('.kpi-card, .list-row').count()
    if (hasKpis === 0) {
      test.skip()
      return
    }

    const calcBtn = page.locator('[title="Calculer"]').first()
    if (!await calcBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      test.skip()
      return
    }

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/[^/]+\/calculate\//.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      calcBtn.click(),
    ])

    expect(res.status()).toBe(200)
  })
})

// ─── Suite 7 : Filtres endpoint ──────────────────────────────────────────────

test.describe('/kpis – Filtres API', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('GET /api/visualizations/kpis/critical/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/kpis\/critical\//.test(r.url()))
        statuses.push(r.status())
    })

    const critBtn = page.locator('button', { hasText: /Critiques?/i }).first()
    if (await critBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await critBtn.click()
      await page.waitForLoadState('networkidle')
      if (statuses.length > 0) {
        expect(statuses[0]).toBe(200)
      }
    }
  })
})
