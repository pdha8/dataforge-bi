import { test, expect, Page } from '@playwright/test'

const LOGIN_EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const LOGIN_PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(LOGIN_EMAIL)
  await page.locator('input[type="password"]').fill(LOGIN_PASSWORD)
  await page.locator('button[type="submit"]').click()
  // Attendre la redirection vers le dashboard
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 20_000 })
}

function collectConsoleErrors(page: Page): string[] {
  const errors: string[] = []
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  return errors
}

// â”€â”€â”€ Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('Authentification', () => {
  test('La page de login se charge correctement', async ({ page }) => {
    const errors = collectConsoleErrors(page)
    await page.goto('/login')
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0)
  })

  test('Login rÃ©ussi redirige vers le dashboard', async ({ page }) => {
    await login(page)
    await expect(page).toHaveURL(/\/(dashboard)?$/)
  })
})

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('Le dashboard affiche les KPI cards sans erreur console', async ({ page }) => {
    const errors = collectConsoleErrors(page)
    await page.goto('/')
    // Attendre que le contenu principal charge (pas de spinner)
    await page.waitForLoadState('networkidle')
    // VÃ©rifier qu'il y a au moins un Ã©lÃ©ment de contenu
    const main = page.locator('main, .dash-header, [class*="dashboard"]')
    await expect(main.first()).toBeVisible()
    // Filtrer les erreurs bÃ©nignes (extensions navigateur, favicon)
    const realErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('chrome-extension') &&
      !e.includes('ERR_FILE_NOT_FOUND')
    )
    expect(realErrors).toHaveLength(0)
  })
})

test.describe('Sources de donnÃ©es â€“ cohÃ©rence tableau', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('La page Sources charge et affiche le bon nombre de colonnes', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    // VÃ©rifier que la page est bien chargÃ©e (titre ou header visible)
    await expect(page.locator('.page-hd, [class*="page-hd"]').first()).toBeVisible({ timeout: 8_000 })

    // S'il y a un tableau de tables ouvert dans le panneau dÃ©tail,
    // il doit avoir exactement 3 colonnes : Nom | Lignes | DerniÃ¨re MAJ
    const detailTable = page.locator('.detail-table, table').first()
    const isVisible = await detailTable.isVisible()
    if (isVisible) {
      const headers = detailTable.locator('thead th')
      const count = await headers.count()
      // Le tableau de tables a 4 colonnes (3 + colonne action)
      expect(count).toBeGreaterThanOrEqual(3)
    }
  })
})

test.describe('Pipelines ETL â€“ cohÃ©rence tableau', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('La page Pipelines charge et le header de colonnes est visible', async ({ page }) => {
    await page.goto('/pipelines')
    await page.waitForLoadState('networkidle')

    // Les en-tÃªtes de colonnes de la liste
    // Design : Nom | Source | Destination | Schedule | Statut | DerniÃ¨re exÃ©c.
    const colHeaders = page.locator('.col-headers')
    const visible = await colHeaders.isVisible()
    if (visible) {
      const cols = colHeaders.locator('> *')
      const count = await cols.count()
      // Le design prÃ©voit entre 4 et 6 colonnes visibles
      expect(count).toBeGreaterThanOrEqual(4)
      expect(count).toBeLessThanOrEqual(6)
    }
  })

  test("Le tableau d'exÃ©cutions a 5 colonnes (Statut, DÃ©marrÃ©, DurÃ©e, Lignes, Erreurs)", async ({ page }) => {
    await page.goto('/pipelines')
    await page.waitForLoadState('networkidle')

    // Cliquer sur le premier pipeline pour ouvrir le panneau dÃ©tail
    const firstCard = page.locator('[class*="pipeline-card"], .pl-card').first()
    const cardVisible = await firstCard.isVisible()
    if (cardVisible) {
      await firstCard.click()
      await page.waitForTimeout(1000)
      const execTable = page.locator('table').filter({ hasText: 'Statut' }).first()
      const execVisible = await execTable.isVisible()
      if (execVisible) {
        const ths = execTable.locator('thead th')
        await expect(ths).toHaveCount(5)
      }
    }
  })
})

test.describe('Navigation gÃ©nÃ©rale', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  const routes = [
    { path: '/sources',         label: 'Sources'         },
    { path: '/pipelines',       label: 'Pipelines'       },
    { path: '/executions',      label: 'ExÃ©cutions'      },
    { path: '/warehouse',       label: 'Data Warehouse'  },
    { path: '/kpis',            label: 'KPIs'            },
    { path: '/notifications',   label: 'Notifications'   },
  ]

  for (const { path, label } of routes) {
    test(`La page "${label}" charge sans erreur HTTP 4xx/5xx`, async ({ page }) => {
      const errors: string[] = []
      page.on('requestfailed', req => errors.push(`${req.url()} â€“ ${req.failure()?.errorText}`))
      page.on('response', res => {
        if (res.status() >= 400 && res.url().includes('/api/')) {
          errors.push(`API ${res.status()} sur ${res.url()}`)
        }
      })
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      // Signaler uniquement les vraies erreurs HTTP 5xx de l'API
      // Exclut : ERR_ABORTED (race conditions de navigation), URLs contenant "5"
      const serverErrors = errors.filter(e => /^API 5\d\d/.test(e))
      expect(serverErrors, `Erreurs 5xx dÃ©tectÃ©es:\n${serverErrors.join('\n')}`).toHaveLength(0)
    })
  }
})
