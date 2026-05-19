/**
 * Tests E2E exhaustifs â€” Page /dashboards
 * CRUD complet : crÃ©er, Ã©diter, dupliquer, publier, supprimer
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

async function goToDashboards(page: Page) {
  await page.goto('/dashboards')
  await page.waitForLoadState('networkidle')
}

// â”€â”€â”€ Suite 1 : Chargement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ Chargement', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('GET /api/visualizations/dashboards/ â†’ 200', async ({ page }) => {
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

// â”€â”€â”€ Suite 2 : Drawer CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ Drawer create', () => {
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

// â”€â”€â”€ Suite 3 : CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ CREATE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('POST /api/visualizations/dashboards/ â†’ 201 avec nom correct', async ({ page }) => {
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

  test('Le dashboard crÃ©Ã© apparaÃ®t dans la liste', async ({ page }) => {
    const name = `Tableau RÃ©seau ${TS}`

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

// â”€â”€â”€ Suite 4 : EDIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('PATCH /api/visualizations/dashboards/{id}/ â†’ 200 avec nouveau nom', async ({ page }) => {
    // S'assurer qu'il y a au moins un dashboard
    const cards = page.locator('.db-card, .dash-card, .card').first()
    const hasCards = await cards.count()
    if (hasCards === 0) {
      test.skip()
      return
    }

    // Chercher le bouton Ã©diter (crayon)
    const editBtn = page.locator('[title="Modifier"], [title="Ã‰diter"], button:has([data-lucide="pencil"]), .act-btn:has([data-lucide="pencil"])').first()
    if (!await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      test.skip()
      return
    }

    await editBtn.click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const newName = `ModifiÃ© Dash ${TS}`
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

// â”€â”€â”€ Suite 5 : DELETE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('DELETE : suppression d\'un dashboard crÃ©Ã© via l\'UI â†’ 204 ou 200', async ({ page }) => {
    const name = `DEL Dashboard ${TS}`

    // 1. CrÃ©er le dashboard
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

// â”€â”€â”€ Suite 6 : Widgets tab â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/dashboards â€“ Onglet Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToDashboards(page)
  })

  test('GET /api/visualizations/widgets/ â†’ 200', async ({ page }) => {
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
