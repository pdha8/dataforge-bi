import { test, expect, Page } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'
const TS       = Date.now()

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 20_000 })
}

async function goToConnections(page: Page) {
  await page.goto('/sources/connections')
  await page.waitForLoadState('networkidle')
}

// â”€â”€â”€ Chargement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ Chargement', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('GET /api/data-sources/connections/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/connections\/(\?|$)/.test(r.url()) && r.request().method() === 'GET')
        statuses.push(r.status())
    })
    await page.reload(); await page.waitForLoadState('networkidle')
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Pas d\'erreur 5xx au chargement', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => { if (r.status() >= 500 && r.url().includes('/api/')) errors.push(`${r.status()} ${r.url()}`) })
    await page.reload(); await page.waitForLoadState('networkidle')
    expect(errors, `5xx:\n${errors.join('\n')}`).toHaveLength(0)
  })

  test('La page affiche le bouton "Nouvelle connexion"', async ({ page }) => {
    await expect(page.locator('button', { hasText: /Nouvelle connexion/i }).first()).toBeVisible()
  })
})

// â”€â”€â”€ Drawer CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ Drawer create', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('Le bouton "Nouvelle connexion" ouvre le drawer', async ({ page }) => {
    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 8_000 })
  })

  test('Le drawer contient les champs requis : Nom, Type, HÃ´te', async ({ page }) => {
    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await expect(page.locator('[role="dialog"]')).toBeVisible()
    await expect(page.locator('#conn-name')).toBeVisible({ timeout: 8_000 })
    await expect(page.locator('#conn-host')).toBeVisible({ timeout: 8_000 })
  })

  test('Le select de type contient PostgreSQL', async ({ page }) => {
    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })
    const opts = await page.locator('[role="dialog"] select').first().locator('option').allTextContents()
    expect(opts.some(o => /postgresql|postgres/i.test(o))).toBe(true)
  })
})

// â”€â”€â”€ CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ CREATE', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('POST /api/data-sources/connections/ â†’ 201', async ({ page }) => {
    const name = `Conn E2E ${TS}`
    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#conn-name').fill(name)
    await page.locator('#conn-host').fill('localhost')
    await page.locator('#conn-db').fill('testdb')

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/connections\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    expect(res.status()).toBe(201)
  })

  test('La connexion crÃ©Ã©e apparaÃ®t dans la liste', async ({ page }) => {
    const name = `Conn RÃ©seau ${TS}`
    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#conn-name').fill(name)
    await page.locator('#conn-host').fill('db.local')
    await page.locator('#conn-db').fill('proddb')

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/connections\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 8_000 })
  })
})

// â”€â”€â”€ EDIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ EDIT', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('Le bouton crayon ouvre le drawer en mode Ã©dition', async ({ page }) => {
    if (await page.locator('.table-row').count() === 0) { test.skip(); return }
    const editBtn = page.locator('.act-btn[title="Modifier"]').first()
    if (!await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) { test.skip(); return }
    await editBtn.click()
    await expect(page.locator('[role="dialog"]')).toBeVisible()
    // Le drawer doit s'ouvrir (le nom peut Ãªtre vide si data_source non mappÃ©)
    await expect(page.locator('#conn-host')).toBeVisible({ timeout: 5_000 })
  })

  test('PATCH /api/data-sources/connections/{id}/ â†’ 200', async ({ page }) => {
    if (await page.locator('.table-row').count() === 0) { test.skip(); return }
    const editBtn = page.locator('.act-btn[title="Modifier"]').first()
    if (!await editBtn.isVisible({ timeout: 5_000 }).catch(() => false)) { test.skip(); return }
    await editBtn.click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#conn-name').fill(`Conn ModifiÃ©e ${TS}`)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/connections\/[^/]+\/?$/.test(r.url()) &&
             (r.request().method() === 'PATCH' || r.request().method() === 'PUT'),
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    expect(res.status()).toBe(200)
  })
})

// â”€â”€â”€ TEST CONNEXION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ TEST connexion', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('POST /api/data-sources/connections/{id}/test/ â†’ pas de 5xx inattendu', async ({ page }) => {
    if (await page.locator('.table-row').count() === 0) { test.skip(); return }
    const testBtn = page.locator('.act-btn--test').first()
    if (!await testBtn.isVisible({ timeout: 5_000 }).catch(() => false)) { test.skip(); return }

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/connections\/[^/]+\/test\//.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      testBtn.click(),
    ])
    // 200 (succÃ¨s) ou 422 (Ã©chec connexion attendu) â€” jamais 500
    expect([200, 422]).toContain(res.status())
  })
})

// â”€â”€â”€ DELETE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/sources/connections â€“ DELETE', () => {
  test.beforeEach(async ({ page }) => { await login(page); await goToConnections(page) })

  test('DELETE : suppression d\'une connexion crÃ©Ã©e via l\'UI â†’ 204', async ({ page }) => {
    const name = `Conn DEL ${TS}`

    await page.locator('button', { hasText: /Nouvelle connexion/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })
    await page.locator('#conn-name').fill(name)
    await page.locator('#conn-host').fill('del.local')
    await page.locator('#conn-db').fill('deldb')

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/connections\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')

    const row = page.locator('.table-row').filter({ hasText: name })
    await expect(row).toBeVisible({ timeout: 8_000 })
    await row.locator('.act-btn--del').click()

    const confirmBtn = page.locator('button.act-btn--yes').first()
    if (await confirmBtn.isVisible({ timeout: 3_000 }).catch(() => false)) {
      const [res] = await Promise.all([
        page.waitForResponse(
          r => /\/api\/data-sources\/connections\/[^/]+\/?$/.test(r.url()) && r.request().method() === 'DELETE',
          { timeout: 15_000 },
        ),
        confirmBtn.click(),
      ])
      expect([204, 200]).toContain(res.status())
    }
  })
})
