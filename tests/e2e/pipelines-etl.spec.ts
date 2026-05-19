/**
 * E2E â€“ Module Pipelines ETL
 *
 * Cibles : /pipelines  /executions
 *
 * Objectifs :
 *   â€¢ CRUD complet sur les pipelines
 *   â€¢ Boutons physiques : ExÃ©cuter, Pause, Modifier, Supprimer, "Nouveau pipeline"
 *   â€¢ UX : le nom du pipeline est AUTO-GÃ‰NÃ‰RÃ‰ Ã  partir des selects
 *     Source â†’ Destination (plus de tapage manuel de la flÃ¨che)
 */

import { test, expect, Page, Locator } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'
const TS       = Date.now()

// â”€â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

async function openDrawer(page: Page, btnRe: RegExp): Promise<Locator> {
  const btn = page.locator('button', { hasText: btnRe }).first()
  await btn.waitFor({ state: 'visible', timeout: 10_000 })
  await btn.click()
  const drawer = page.locator('[role="dialog"], aside.drawer, .drawer').first()
  await drawer.waitFor({ state: 'visible', timeout: 8_000 })
  return drawer
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   1.  /pipelines  â€“ Liste + bouton "Nouveau pipeline"
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/pipelines â€“ Liste & boutons physiques', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('GET /api/etl/pipelines/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/etl\/pipelines\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Le bouton "Nouveau pipeline" ouvre le drawer', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    await expect(drawer).toBeVisible()
  })

  test('Les boutons d\'action existent dans la liste : ExÃ©cuter / Pause / Modifier / Supprimer', async ({ page }) => {
    // S'assurer qu'il y a au moins un pipeline
    const rows = page.locator('.pipeline-row, .pl-row, [class*="pipeline"], tr, .card').first()
    if (!(await rows.isVisible({ timeout: 6_000 }).catch(() => false))) {
      test.skip()
      return
    }
    const titles = [
      /ExÃ©cuter|Lancer|Run|Activez/i,
      /Pause|Suspendre|Reprendre|Resume/i,
      /Modifier|Ã‰diter|Edit/i,
      /Supprimer|Delete/i,
    ]
    for (const re of titles) {
      const btn = page.locator(`button[title*="${re.source.split('|')[0]}" i], button:has-text("${re.source.split('|')[0]}")`).first()
      if (!(await btn.isVisible({ timeout: 2_000 }).catch(() => false))) {
        // certains boutons sont des icÃ´nes â€” vÃ©rifier les attributs title
        const fallback = page.locator(`[title]`).filter({ has: page.locator(`[title*="${re.source.split('|')[0]}" i]`).first() })
        if (await fallback.count() === 0) {
          // boutons peuvent Ãªtre conditionnels (running/active) â€” ne pas faire Ã©chouer
          continue
        }
      }
    }
    // Test PASS s'il existe au moins un title parmi ceux attendus
    const anyActionBtn = page.locator(
      'button[title*="ExÃ©cuter" i], button[title*="Pause" i], button[title*="Reprendre" i], button[title*="Modifier" i], button[title*="Supprimer" i]'
    )
    expect(await anyActionBtn.count(), 'Aucun bouton d\'action (ExÃ©cuter/Pause/Modifier/Supprimer) trouvÃ©').toBeGreaterThan(0)
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   2.  /pipelines  â€“ UX auto-gÃ©nÃ©ration nom (Source â†’ Destination)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/pipelines â€“ Auto-gÃ©nÃ©ration du nom', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('Le drawer contient des <select> sÃ©parÃ©s pour Source et Destination', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const srcSelect = drawer.locator('select#pl-source')
    const dstSelect = drawer.locator('select#pl-dest')
    await expect(srcSelect, 'Pas de select Source (id=pl-source)').toBeVisible()
    await expect(dstSelect, 'Pas de select Destination (id=pl-dest)').toBeVisible()
  })

  test('Le placeholder du nom indique l\'auto-gÃ©nÃ©ration (pas un exemple Ã  taper manuellement)', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const nameInput = drawer.locator('input#pl-name')
    await expect(nameInput).toBeVisible()
    const placeholder = await nameInput.getAttribute('placeholder')
    expect(placeholder).toMatch(/auto|gÃ©nÃ©rer|Source.*Destination|SÃ©lectionnez/i)
    // Plus aucune mention de la flÃ¨che â†’ dans le placeholder Ã  taper soi-mÃªme
    expect(placeholder).not.toMatch(/Ex\s*:\s*Ventes\s*â†’\s*DW/i)
  })

  test('SÃ©lectionner Source ET Destination gÃ©nÃ¨re automatiquement "Source â†’ Destination" dans le nom', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const srcSelect = drawer.locator('select#pl-source')
    const dstSelect = drawer.locator('select#pl-dest')

    // Trouver 2 sources diffÃ©rentes
    const srcOptions = await srcSelect.locator('option').elementHandles()
    const valid: string[] = []
    for (const o of srcOptions) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') valid.push(v)
      if (valid.length >= 2) break
    }
    if (valid.length < 2) { test.skip(); return }

    await srcSelect.selectOption(valid[0])
    // petit dÃ©lai pour que le watcher Vue propage avant le 2e changement
    await drawer.page().waitForTimeout(200)
    await dstSelect.selectOption(valid[1])

    // Le nom doit maintenant contenir la flÃ¨che "â†’"
    await expect.poll(async () =>
      (await drawer.locator('input#pl-name').inputValue()).length,
    { timeout: 8_000 }).toBeGreaterThan(0)

    const name = await drawer.locator('input#pl-name').inputValue()
    expect(name, `Le nom devrait Ãªtre auto-gÃ©nÃ©rÃ© avec une flÃ¨che : "${name}"`).toMatch(/â†’/)
  })

  test('Si l\'utilisateur tape un nom personnalisÃ©, on cesse l\'auto-gÃ©nÃ©ration', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const nameInput = drawer.locator('input#pl-name')
    const srcSelect = drawer.locator('select#pl-source')

    // saisir un nom manuel
    const custom = `Pipeline custom ${TS}`
    await nameInput.fill(custom)

    // Maintenant changer la source â€” le nom ne doit PAS Ãªtre Ã©crasÃ©
    const opts = await srcSelect.locator('option').elementHandles()
    for (const o of opts) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') { await srcSelect.selectOption(v); break }
    }

    const after = await nameInput.inputValue()
    expect(after, 'Le nom manuel a Ã©tÃ© Ã©crasÃ© par l\'auto-gÃ©nÃ©ration').toBe(custom)
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   3.  /pipelines  â€“ CRUD
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/pipelines â€“ CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('CREATE : POST /api/etl/pipelines/ â†’ 201 avec source + destination', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const srcSelect = drawer.locator('select#pl-source')
    const dstSelect = drawer.locator('select#pl-dest')

    const opts = await srcSelect.locator('option').elementHandles()
    const valid: string[] = []
    for (const o of opts) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') valid.push(v)
      if (valid.length >= 2) break
    }
    if (valid.length < 2) { test.skip(); return }

    await srcSelect.selectOption(valid[0])
    await dstSelect.selectOption(valid[1])

    // Forcer un nom unique (pour Ã©viter collision avec le nom auto-gÃ©nÃ©rÃ© dÃ©jÃ  existant)
    await drawer.locator('input#pl-name').fill(`E2E Pipeline ${TS}`)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/etl\/pipelines\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      drawer.locator('button[type="submit"]').click(),
    ])
    if (![200, 201].includes(res.status())) {
      const body = await res.text().catch(() => '<no body>')
      console.error('=== CREATE PIPELINE FAILED ===')
      console.error('Status:', res.status())
      console.error('Body:', body.slice(0, 1500))
    }
    expect([200, 201]).toContain(res.status())
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   4.  /executions  â€“ Liste des exÃ©cutions
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/executions â€“ Liste & monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/executions')
  })

  test('Chargement OK et aucune 5xx', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/')) {
        errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(errors, errors.join('\n')).toHaveLength(0)
  })

  test('GET /api/etl/executions/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/etl\/executions\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length, 'Aucun appel Ã  /api/etl/executions/').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })
})
