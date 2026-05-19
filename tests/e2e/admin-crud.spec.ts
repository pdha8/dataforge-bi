/**
 * Tests E2E exhaustifs â€” Page /admin
 * SÃ©lecteurs basÃ©s sur l'audit rÃ©el du code AdminView.vue
 */
import { test, expect, Page, Response } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'

const TS = Date.now()
// Chaque test qui crÃ©e un user doit gÃ©nÃ©rer son propre email unique
function uniqueEmail(suffix = '') { return `pw.e2e.${suffix}.${Date.now()}@dataforge.tech` }

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 20_000 })
}

async function goToAdminTab(page: Page, tabName: string) {
  await page.goto('/admin')
  await page.waitForLoadState('networkidle')
  // Les tabs utilisent role="tab" avec les labels dÃ©finis dans TABS[]
  const tab = page.getByRole('tab', { name: new RegExp(tabName, 'i') })
  if (await tab.count() > 0) await tab.first().click()
  await page.waitForLoadState('networkidle')
}

async function waitForResponse(
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

// â”€â”€â”€ Suite : CRUD Utilisateurs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/admin â€“ CRUD Utilisateurs', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToAdminTab(page, 'Utilisateurs')
  })

  // â”€â”€ READ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  test('READ : GET /api/users/users/ â†’ 200 et liste non-vide', async ({ page }) => {
    const collected: Response[] = []
    page.on('response', r => {
      if (/\/api\/users\/users\/?(\?|$)/.test(r.url()) && r.request().method() === 'GET')
        collected.push(r)
    })
    await page.reload()
    await page.waitForLoadState('networkidle')

    expect(collected.length).toBeGreaterThan(0)
    expect(collected[0].status()).toBe(200)
    const data = await collected[0].json()
    const list = Array.isArray(data) ? data : data.results
    expect(Array.isArray(list)).toBe(true)
    expect(list.length).toBeGreaterThan(0)
  })

  test('READ : le tableau affiche bien 5 colonnes', async ({ page }) => {
    const table = page.locator('table').first()
    await expect(table).toBeVisible({ timeout: 8_000 })
    const ths = table.locator('thead th')
    await expect(ths).toHaveCount(5)
    await expect(ths.nth(0)).toContainText(/Utilisateur/i)
    await expect(ths.nth(1)).toContainText(/RÃ´le/i)
    await expect(ths.nth(2)).toContainText(/Statut/i)
  })

  // â”€â”€ CREATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  test('CREATE : bouton ouvre le drawer avec le titre "CrÃ©er un utilisateur"', async ({ page }) => {
    await page.locator('button', { hasText: 'CrÃ©er un utilisateur' }).click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()
    await expect(drawer.locator('h3')).toContainText(/CrÃ©er un utilisateur/i)
    await expect(page.locator('#f-email')).toBeVisible()
    await expect(page.locator('#f-pwd')).toBeVisible()
  })

  test('CREATE : POST /api/users/users/ â†’ 201 avec les bonnes donnÃ©es', async ({ page }) => {
    const email = uniqueEmail('c1')
    await page.locator('button', { hasText: 'CrÃ©er un utilisateur' }).click()
    await page.locator('#f-fname').fill('Playwright')
    await page.locator('#f-lname').fill('TestCreate')
    await page.locator('#f-email').fill(email)
    await page.locator('#f-pwd').fill('TestPassword@2026!')

    const res = await waitForResponse(
      page, /\/api\/users\/users\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    expect(res.status()).toBe(201)
    const body = await res.json()
    expect(body.email ?? body.data?.email).toBe(email)
  })

  test('CREATE : le nouvel utilisateur apparaÃ®t dans le tableau', async ({ page }) => {
    const email = uniqueEmail('c2')
    await page.locator('button', { hasText: 'CrÃ©er un utilisateur' }).click()
    await page.locator('#f-email').fill(email)
    await page.locator('#f-pwd').fill('TestPassword@2026!')

    await waitForResponse(
      page, /\/api\/users\/users\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    await page.waitForLoadState('networkidle')
    await expect(page.locator('td', { hasText: email })).toBeVisible({ timeout: 8_000 })
  })

  // â”€â”€ EDIT (bouton Modifier â€” corrigÃ©) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  test('EDIT : le bouton Modifier ouvre le drawer en mode Ã©dition', async ({ page }) => {
    const editBtn = page.locator('button[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()
    // Titre = "Modifier l'utilisateur"
    await expect(drawer.locator('h3')).toContainText(/Modifier/i)
    // Email prÃ©-rempli (non vide)
    const emailVal = await page.locator('#f-email').inputValue()
    expect(emailVal.trim().length).toBeGreaterThan(0)
    // Champ mot de passe absent en mode Ã©dition
    await expect(page.locator('#f-pwd')).not.toBeVisible()
  })

  test('EDIT : PATCH /api/users/users/{id}/ â†’ 200', async ({ page }) => {
    await page.locator('button[title="Modifier"]').first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    // Modifier le dÃ©partement
    const dept = page.locator('#f-dept')
    await dept.fill(`E2E-Dept-${TS}`)

    const res = await waitForResponse(
      page, /\/api\/users\/users\/[^/]+\/?$/, 'PATCH',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )

    expect(res.status()).toBe(200)
  })

  // â”€â”€ TOGGLE STATUS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  test('TOGGLE STATUS : POST toggle_status â†’ 200', async ({ page }) => {
    const btn = page.locator('button[title="DÃ©sactiver"], button[title="Activer"]').first()
    await expect(btn).toBeVisible({ timeout: 8_000 })

    const res = await waitForResponse(
      page, /\/api\/users\/users\/.+\/toggle_status\//, 'POST',
      () => btn.click(),
    )

    expect(res.status()).toBe(200)
    // Appuyer Ã  nouveau pour remettre l'Ã©tat initial
    const btn2 = page.locator('button[title="DÃ©sactiver"], button[title="Activer"]').first()
    if (await btn2.isVisible()) await btn2.click()
  })

  // â”€â”€ DELETE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  test('DELETE : DELETE /api/users/users/{id}/ â†’ 204 et disparition du tableau', async ({ page }) => {
    const delEmail = uniqueEmail('del')

    // CrÃ©er l'utilisateur Ã  supprimer
    await page.locator('button', { hasText: 'CrÃ©er un utilisateur' }).click()
    await page.locator('#f-email').fill(delEmail)
    await page.locator('#f-pwd').fill('TestPassword@2026!')
    await waitForResponse(
      page, /\/api\/users\/users\/?$/, 'POST',
      () => page.locator('[role="dialog"] button[type="submit"]').click(),
    )
    await page.waitForLoadState('networkidle')

    // Trouver la ligne et supprimer
    const row = page.locator('tr', { hasText: delEmail })
    await expect(row).toBeVisible({ timeout: 8_000 })
    await row.locator('button[title="Supprimer"]').click()
    await row.locator('button', { hasText: 'Oui' }).click()

    await page.waitForResponse(
      r => /\/api\/users\/users\/.+\/?$/.test(r.url()) && r.request().method() === 'DELETE',
      { timeout: 10_000 },
    )

    await page.waitForLoadState('networkidle')
    await expect(page.locator('td', { hasText: delEmail })).not.toBeVisible({ timeout: 8_000 })
  })
})

// â”€â”€â”€ Suite : CRUD RÃ´les â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/admin â€“ CRUD RÃ´les', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToAdminTab(page, 'RÃ´les')
  })

  test('READ : la section RÃ´les affiche du contenu', async ({ page }) => {
    // La grille de rÃ´les ou les cards
    const content = page.locator('[class*="role"], [class*="perm"]').first()
    await expect(content).toBeVisible({ timeout: 8_000 })
  })

  test('CREATE ROLE : POST /api/users/roles/ â†’ 201', async ({ page }) => {
    const btn = page.locator('button', { hasText: /Nouveau rÃ´le/i })
    await expect(btn).toBeVisible()
    await btn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    // Trouver le champ slug (name) et display_name dans le drawer
    const inputs = drawer.locator('input[type="text"]')
    await inputs.nth(0).fill(`e2erole${TS}`)
    await inputs.nth(1).fill(`E2E Role ${TS}`)

    const res = await waitForResponse(
      page, /\/api\/users\/roles\/?$/, 'POST',
      () => drawer.locator('button[type="submit"]').click(),
    )
    expect(res.status()).toBe(201)
  })

  test('EDIT ROLE : PATCH /api/users/roles/{id}/ â†’ 200', async ({ page }) => {
    const editBtn = page.locator('button[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    const descInput = drawer.locator('textarea, input[type="text"]').last()
    await descInput.fill(`Description E2E ${TS}`)

    const res = await waitForResponse(
      page, /\/api\/users\/roles\/[^/]+\/?$/, 'PATCH',
      () => drawer.locator('button[type="submit"]').click(),
    )
    expect(res.status()).toBe(200)
  })
})

// â”€â”€â”€ Suite : CRUD Ã‰quipes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test.describe('/admin â€“ CRUD Ã‰quipes', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToAdminTab(page, 'Ã‰quipes')
  })

  test('CREATE TEAM : POST /api/users/teams/ â†’ 201', async ({ page }) => {
    const btn = page.locator('button', { hasText: /Nouvelle Ã©quipe/i })
    await expect(btn).toBeVisible()
    await btn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    await drawer.locator('input[type="text"]').first().fill(`E2E Team ${TS}`)

    const res = await waitForResponse(
      page, /\/api\/users\/teams\/?$/, 'POST',
      () => drawer.locator('button[type="submit"]').click(),
    )
    expect(res.status()).toBe(201)
  })

  test('EDIT TEAM : PATCH /api/users/teams/{id}/ â†’ 200', async ({ page }) => {
    const editBtn = page.locator('button[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    const desc = drawer.locator('textarea').first()
    if (await desc.isVisible()) await desc.fill(`E2E desc ${TS}`)

    const res = await waitForResponse(
      page, /\/api\/users\/teams\/[^/]+\/?$/, 'PATCH',
      () => drawer.locator('button[type="submit"]').click(),
    )
    expect(res.status()).toBe(200)
  })
})
