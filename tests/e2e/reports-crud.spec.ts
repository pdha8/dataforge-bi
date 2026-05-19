/**
 * Tests E2E exhaustifs â€” Page /reports
 * Dashboard : <select> dynamique depuis l'API  (#f-dash)
 * Destinataires : tags selector depuis liste utilisateurs (#f-recip)
 */
import { test, expect, Page, Response } from '@playwright/test'

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

async function goToReports(page: Page) {
  await page.goto('/reports')
  await page.waitForLoadState('networkidle')
}

async function waitForApiResponse(
  page: Page,
  urlPattern: RegExp,
  method: string,
  action: () => Promise<void>,
): Promise<Response> {
  const [res] = await Promise.all([
    page.waitForResponse(
      r => urlPattern.test(r.url()) && r.request().method() === method,
      { timeout: 15_000 },
    ),
    action(),
  ])
  return res
}

/**
 * SÃ©lectionne le premier vrai dashboard dans le select #f-dash s'il existe.
 * Le select est chargÃ© dynamiquement depuis l'API â€” on attend que les options arrivent.
 */
async function selectFirstDashboardIfAvailable(page: Page) {
  const select = page.locator('#f-dash')
  // Attendre que le select ait au moins 2 options (option vide + au moins 1 dashboard)
  try {
    await page.waitForFunction(
      () => (document.querySelector('#f-dash') as HTMLSelectElement)?.options.length > 1,
      { timeout: 5_000 },
    )
    await select.selectOption({ index: 1 })  // premiÃ¨re option non-vide
  } catch {
    // Pas de dashboard disponible â€” laisser vide (champ optionnel)
  }
}

// â”€â”€â”€ Suite 1 : Chargement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/reports â€“ Chargement et affichage', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToReports(page)
  })

  test('GET /api/visualizations/reports/ â†’ 200 avec liste valide', async ({ page }) => {
    const collected: Response[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/reports\/(\?|$)/.test(r.url()) && r.request().method() === 'GET')
        collected.push(r)
    })
    await page.reload()
    await page.waitForLoadState('networkidle')

    expect(collected.length).toBeGreaterThan(0)
    expect(collected[0].status()).toBe(200)
    const data = await collected[0].json()
    const list = Array.isArray(data) ? data : data.results
    expect(Array.isArray(list)).toBe(true)
  })

  test('La vue liste affiche les colonnes attendues', async ({ page }) => {
    // Basculer en vue liste
    const listBtn = page.locator('button').filter({ has: page.locator('svg') }).nth(1)
    // Si pas de bouton toggle visible, chercher directement le tableau
    const table = page.locator('table').first()
    if (await table.isVisible()) {
      const ths = table.locator('thead th')
      const count = await ths.count()
      expect(count).toBeGreaterThanOrEqual(5)
    } else {
      // Mode grille par dÃ©faut â€” vÃ©rifier les cards
      const cards = page.locator('[class*="card"], [class*="report-"]').first()
      await expect(cards).toBeVisible({ timeout: 8_000 })
    }
  })

  test('Pas d\'erreur API 5xx au chargement', async ({ page }) => {
    const errors5xx: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/'))
        errors5xx.push(`${r.status()} ${r.url()}`)
    })
    await page.reload()
    await page.waitForLoadState('networkidle')
    expect(errors5xx, `Erreurs 5xx:\n${errors5xx.join('\n')}`).toHaveLength(0)
  })
})

// â”€â”€â”€ Suite 2 : CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/reports â€“ CREATE rapport', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToReports(page)
  })

  test('Le drawer contient le select Dashboard et le tags selector Destinataires', async ({ page }) => {
    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()
    await expect(page.locator('#f-name')).toBeVisible()
    await expect(page.locator('#f-fmt')).toBeVisible()
    // #f-dash est maintenant un <select>
    await expect(page.locator('#f-dash')).toBeVisible()
    const tag = page.locator('#f-dash')
    expect(await tag.evaluate((el: HTMLSelectElement) => el.tagName.toLowerCase())).toBe('select')
    // #f-recip est le tag-input pour les destinataires
    await expect(page.locator('#f-recip')).toBeVisible()
  })

  test('Le select #f-dash est un vrai <select> avec l\'option vide par dÃ©faut', async ({ page }) => {
    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    const select = page.locator('#f-dash')
    await expect(select).toBeVisible()

    // Doit Ãªtre un <select> natif
    const tagName = await select.evaluate((el: HTMLSelectElement) => el.tagName.toLowerCase())
    expect(tagName).toBe('select')

    // L'option vide "â€” Aucun tableau de bord â€”" doit exister
    const emptyOpt = select.locator('option[value=""]')
    await expect(emptyOpt).toHaveCount(1)

    // Les options sont chargÃ©es depuis l'API (au moins l'option vide)
    const optCount = await select.locator('option').count()
    expect(optCount).toBeGreaterThanOrEqual(1)
  })

  test('CREATE : POST /api/visualizations/reports/ â†’ 201 avec nom correct', async ({ page }) => {
    const reportName = `E2E Create ${TS}`

    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    await page.locator('#f-name').fill(reportName)
    await page.locator('#f-fmt').selectOption('json')
    await selectFirstDashboardIfAvailable(page)

    const res = await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    expect(res.status()).toBe(201)
    const body = await res.json()
    expect(body.name ?? body.data?.name).toBe(reportName)
  })

  test('CREATE : le rapport apparaÃ®t dans la liste aprÃ¨s crÃ©ation', async ({ page }) => {
    const reportName = `E2E List ${TS}`

    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    await page.locator('#f-name').fill(reportName)
    await page.locator('#f-fmt').selectOption('json')
    await selectFirstDashboardIfAvailable(page)

    await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${reportName}`).first()).toBeVisible({ timeout: 8_000 })
  })

  test('CREATE : les prÃ©sets CRON remplissent correctement le champ schedule', async ({ page }) => {
    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    // Le champ schedule existe
    await expect(page.locator('#f-sched')).toBeVisible()

    // Cliquer le prÃ©set "Quotidien" (class cron-preset-btn)
    const quotidienBtn = page.locator('button.cron-preset-btn', { hasText: /Quotidien/i })
    await expect(quotidienBtn).toBeVisible()
    await quotidienBtn.click()

    // Le champ doit maintenant contenir une expression CRON
    const val = await page.locator('#f-sched').inputValue()
    expect(val.trim().length).toBeGreaterThan(0)
    expect(val).toContain('*')
  })
})

// â”€â”€â”€ Suite 3 : GENERATE (tÃ©lÃ©chargement rÃ©el) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/** CrÃ©e un rapport dans le format donnÃ© et retourne son ID */
async function createReport(page: Page, format: string, suffix = ''): Promise<string> {
  await page.locator('button', { hasText: /Nouveau rapport/i }).click()
  await page.locator('#f-name').fill(`E2E Gen ${suffix || format} ${TS}`)
  await page.locator('#f-fmt').selectOption(format)
  const res = await waitForApiResponse(
    page, /\/api\/visualizations\/reports\/?$/, 'POST',
    () => page.locator('[role="dialog"] button[type="submit"]').click(),
  )
  await page.waitForLoadState('networkidle')
  const body = await res.json()
  return body.id ?? body.data?.id ?? ''
}

test.describe('/reports â€“ GENERATE (tÃ©lÃ©chargement fichier)', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToReports(page)
  })

  test('GENERATE CSV : POST â†’ 200 + Content-Disposition attachment + extension .csv', async ({ page }) => {
    await createReport(page, 'csv')
    const generateBtn = page.locator('button[title*="GÃ©nÃ©rer"]').first()
    await expect(generateBtn).toBeVisible({ timeout: 8_000 })

    const res = await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/.+\/generate\//, 'POST',
      () => generateBtn.click(),
    )

    expect(res.status()).toBe(200)
    const disposition = res.headers()['content-disposition'] ?? ''
    expect(disposition).toContain('attachment')
    expect(disposition).toMatch(/\.csv/i)
  })

  test('GENERATE PDF : WeasyPrint â†’ 200 + Content-Type application/pdf', async ({ page }) => {
    await createReport(page, 'pdf')
    const generateBtn = page.locator('button[title*="GÃ©nÃ©rer"]').first()
    await expect(generateBtn).toBeVisible({ timeout: 8_000 })

    const res = await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/.+\/generate\//, 'POST',
      () => generateBtn.click(),
    )

    expect(res.status()).toBe(200)
    const contentType = res.headers()['content-type'] ?? ''
    expect(contentType).toContain('application/pdf')
    const disposition = res.headers()['content-disposition'] ?? ''
    expect(disposition).toMatch(/\.pdf/i)
  })

  test('GENERATE : le clic dÃ©clenche un tÃ©lÃ©chargement de fichier physique (download event)', async ({ page }) => {
    await createReport(page, 'json')
    const generateBtn = page.locator('button[title*="GÃ©nÃ©rer"]').first()
    await expect(generateBtn).toBeVisible({ timeout: 8_000 })

    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 20_000 }),
      generateBtn.click(),
    ])

    expect(download.suggestedFilename()).toMatch(/\.(pdf|csv|json|xlsx|tsv|yaml|html)$/i)
  })

  test('GENERATE : le toast "Fichier tÃ©lÃ©chargÃ©" apparaÃ®t aprÃ¨s le download', async ({ page }) => {
    await createReport(page, 'csv', 'toast')
    const generateBtn = page.locator('button[title*="GÃ©nÃ©rer"]').first()
    await expect(generateBtn).toBeVisible({ timeout: 8_000 })

    await Promise.all([
      page.waitForEvent('download', { timeout: 20_000 }),
      generateBtn.click(),
    ])

    const toast = page.locator('.toast-success')
    await expect(toast).toBeVisible({ timeout: 8_000 })
    await expect(toast).toContainText(/Fichier tÃ©lÃ©chargÃ©/i)
  })
})

// â”€â”€â”€ Suite 4 : EDIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/reports â€“ EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToReports(page)
  })

  test('EDIT : le bouton crayon ouvre le drawer avec le nom prÃ©-rempli', async ({ page }) => {
    const editBtn = page.locator('button[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    const nameVal = await page.locator('#f-name').inputValue()
    expect(nameVal.trim().length).toBeGreaterThan(0)
  })

  test('EDIT : PATCH /api/visualizations/reports/{id}/ â†’ 200 avec donnÃ©es mises Ã  jour', async ({ page }) => {
    const editBtn = page.locator('button[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const newName = `ModifiÃ© E2E ${TS}`
    await page.locator('#f-name').fill(newName)

    const res = await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/[^/]+\/?$/, 'PATCH',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.name ?? body.data?.name).toContain('ModifiÃ©')
  })
})

// â”€â”€â”€ Suite 5 : DELETE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/reports â€“ DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToReports(page)
  })

  test('DELETE : DELETE /api/visualizations/reports/{id}/ â†’ 204 et disparition', async ({ page }) => {
    const delName = `DEL E2E ${TS}`

    // CrÃ©er via le formulaire UI pour un test 100% E2E
    await page.locator('button', { hasText: /Nouveau rapport/i }).click()
    await page.locator('#f-name').fill(delName)
    await page.locator('#f-fmt').selectOption('json')
    await selectFirstDashboardIfAvailable(page)
    await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )
    await page.waitForLoadState('networkidle')

    // Trouver la card avec la vraie classe .rp-card
    const card = page.locator('.rp-card').filter({ hasText: delName })
    await expect(card).toBeVisible({ timeout: 8_000 })

    // Cliquer le bouton Supprimer sur cette card
    await card.locator('button[title="Supprimer"]').click()

    // Modale de confirmation â†’ bouton .btn-danger
    const confirmBtn = page.locator('.btn-danger', { hasText: /Supprimer/i })
    const res = await waitForApiResponse(
      page, /\/api\/visualizations\/reports\/[^/]+\/?$/, 'DELETE',
      () => confirmBtn.click(),
    )

    expect(res.status()).toBe(204)
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.rp-card').filter({ hasText: delName })).not.toBeVisible({ timeout: 8_000 })
  })
})
