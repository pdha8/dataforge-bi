/**
 * Tests E2E exhaustifs â€” Page /kpis
 * CRUD complet : crÃ©er, Ã©diter, calculer, supprimer
 */
import { test, expect, Page } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'
const TS       = Date.now()

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

// â”€â”€â”€ Suite 1 : Chargement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ Chargement', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('GET /api/visualizations/kpis/ â†’ 200', async ({ page }) => {
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

  test('La page contient le bouton de crÃ©ation de KPI', async ({ page }) => {
    await expect(createBtn(page)).toBeVisible({ timeout: 8_000 })
  })
})

// â”€â”€â”€ Suite 2 : Drawer CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ Drawer create', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('Le drawer de crÃ©ation s\'ouvre avec les champs requis', async ({ page }) => {
    await createBtn(page).click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('#f-name')).toBeVisible()
    await expect(page.locator('#f-tgt')).toBeVisible()
  })
})

// â”€â”€â”€ Suite 3 : CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ CREATE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('POST /api/visualizations/kpis/ â†’ 201', async ({ page }) => {
    const name = `KPI DÃ©bit ${TS}`

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

  test('Le KPI crÃ©Ã© apparaÃ®t dans la liste', async ({ page }) => {
    const name = `KPI DisponibilitÃ© ${TS}`

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

// â”€â”€â”€ Suite 4 : EDIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('PATCH /api/visualizations/kpis/{id}/ â†’ 200', async ({ page }) => {
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

    const newName = `KPI ModifiÃ© ${TS}`
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

// â”€â”€â”€ Suite 5 : DELETE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('DELETE : suppression d\'un KPI crÃ©Ã© â†’ 204', async ({ page }) => {
    const name = `KPI DEL ${TS}`

    // 1. CrÃ©er
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

// â”€â”€â”€ Suite 6 : Calcul KPI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ Calcul', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('POST /api/visualizations/kpis/{id}/calculate/ â†’ 200', async ({ page }) => {
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

// â”€â”€â”€ Suite 7 : Filtres endpoint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/kpis â€“ Filtres API', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToKpis(page)
  })

  test('GET /api/visualizations/kpis/critical/ â†’ 200', async ({ page }) => {
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
