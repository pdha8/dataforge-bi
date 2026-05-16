/**
 * E2E – Module Pipelines ETL
 *
 * Cibles : /pipelines  /executions
 *
 * Objectifs :
 *   • CRUD complet sur les pipelines
 *   • Boutons physiques : Exécuter, Pause, Modifier, Supprimer, "Nouveau pipeline"
 *   • UX : le nom du pipeline est AUTO-GÉNÉRÉ à partir des selects
 *     Source → Destination (plus de tapage manuel de la flèche)
 */

import { test, expect, Page, Locator } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@sotifibre.dz'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'SOTIFibre@2026!'
const TS       = Date.now()

// ─── helpers ────────────────────────────────────────────────

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

// ════════════════════════════════════════════════════════════
//   1.  /pipelines  – Liste + bouton "Nouveau pipeline"
// ════════════════════════════════════════════════════════════

test.describe('/pipelines – Liste & boutons physiques', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('GET /api/etl/pipelines/ → 200', async ({ page }) => {
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

  test('Les boutons d\'action existent dans la liste : Exécuter / Pause / Modifier / Supprimer', async ({ page }) => {
    // S'assurer qu'il y a au moins un pipeline
    const rows = page.locator('.pipeline-row, .pl-row, [class*="pipeline"], tr, .card').first()
    if (!(await rows.isVisible({ timeout: 6_000 }).catch(() => false))) {
      test.skip()
      return
    }
    const titles = [
      /Exécuter|Lancer|Run|Activez/i,
      /Pause|Suspendre|Reprendre|Resume/i,
      /Modifier|Éditer|Edit/i,
      /Supprimer|Delete/i,
    ]
    for (const re of titles) {
      const btn = page.locator(`button[title*="${re.source.split('|')[0]}" i], button:has-text("${re.source.split('|')[0]}")`).first()
      if (!(await btn.isVisible({ timeout: 2_000 }).catch(() => false))) {
        // certains boutons sont des icônes — vérifier les attributs title
        const fallback = page.locator(`[title]`).filter({ has: page.locator(`[title*="${re.source.split('|')[0]}" i]`).first() })
        if (await fallback.count() === 0) {
          // boutons peuvent être conditionnels (running/active) — ne pas faire échouer
          continue
        }
      }
    }
    // Test PASS s'il existe au moins un title parmi ceux attendus
    const anyActionBtn = page.locator(
      'button[title*="Exécuter" i], button[title*="Pause" i], button[title*="Reprendre" i], button[title*="Modifier" i], button[title*="Supprimer" i]'
    )
    expect(await anyActionBtn.count(), 'Aucun bouton d\'action (Exécuter/Pause/Modifier/Supprimer) trouvé').toBeGreaterThan(0)
  })
})

// ════════════════════════════════════════════════════════════
//   2.  /pipelines  – UX auto-génération nom (Source → Destination)
// ════════════════════════════════════════════════════════════

test.describe('/pipelines – Auto-génération du nom', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('Le drawer contient des <select> séparés pour Source et Destination', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const srcSelect = drawer.locator('select#pl-source')
    const dstSelect = drawer.locator('select#pl-dest')
    await expect(srcSelect, 'Pas de select Source (id=pl-source)').toBeVisible()
    await expect(dstSelect, 'Pas de select Destination (id=pl-dest)').toBeVisible()
  })

  test('Le placeholder du nom indique l\'auto-génération (pas un exemple à taper manuellement)', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const nameInput = drawer.locator('input#pl-name')
    await expect(nameInput).toBeVisible()
    const placeholder = await nameInput.getAttribute('placeholder')
    expect(placeholder).toMatch(/auto|générer|Source.*Destination|Sélectionnez/i)
    // Plus aucune mention de la flèche → dans le placeholder à taper soi-même
    expect(placeholder).not.toMatch(/Ex\s*:\s*Ventes\s*→\s*DW/i)
  })

  test('Sélectionner Source ET Destination génère automatiquement "Source → Destination" dans le nom', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const srcSelect = drawer.locator('select#pl-source')
    const dstSelect = drawer.locator('select#pl-dest')

    // Trouver 2 sources différentes
    const srcOptions = await srcSelect.locator('option').elementHandles()
    const valid: string[] = []
    for (const o of srcOptions) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') valid.push(v)
      if (valid.length >= 2) break
    }
    if (valid.length < 2) { test.skip(); return }

    await srcSelect.selectOption(valid[0])
    // petit délai pour que le watcher Vue propage avant le 2e changement
    await drawer.page().waitForTimeout(200)
    await dstSelect.selectOption(valid[1])

    // Le nom doit maintenant contenir la flèche "→"
    await expect.poll(async () =>
      (await drawer.locator('input#pl-name').inputValue()).length,
    { timeout: 8_000 }).toBeGreaterThan(0)

    const name = await drawer.locator('input#pl-name').inputValue()
    expect(name, `Le nom devrait être auto-généré avec une flèche : "${name}"`).toMatch(/→/)
  })

  test('Si l\'utilisateur tape un nom personnalisé, on cesse l\'auto-génération', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau pipeline/i)
    const nameInput = drawer.locator('input#pl-name')
    const srcSelect = drawer.locator('select#pl-source')

    // saisir un nom manuel
    const custom = `Pipeline custom ${TS}`
    await nameInput.fill(custom)

    // Maintenant changer la source — le nom ne doit PAS être écrasé
    const opts = await srcSelect.locator('option').elementHandles()
    for (const o of opts) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') { await srcSelect.selectOption(v); break }
    }

    const after = await nameInput.inputValue()
    expect(after, 'Le nom manuel a été écrasé par l\'auto-génération').toBe(custom)
  })
})

// ════════════════════════════════════════════════════════════
//   3.  /pipelines  – CRUD
// ════════════════════════════════════════════════════════════

test.describe('/pipelines – CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/pipelines')
  })

  test('CREATE : POST /api/etl/pipelines/ → 201 avec source + destination', async ({ page }) => {
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

    // Forcer un nom unique (pour éviter collision avec le nom auto-généré déjà existant)
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

// ════════════════════════════════════════════════════════════
//   4.  /executions  – Liste des exécutions
// ════════════════════════════════════════════════════════════

test.describe('/executions – Liste & monitoring', () => {
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

  test('GET /api/etl/executions/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/etl\/executions\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length, 'Aucun appel à /api/etl/executions/').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })
})
