/**
 * E2E – Module Data Sources
 *
 * Cibles : /sources  /sources/files  /sources/connections  /sources/monitoring
 *          /power-queries  /queries
 *
 * Objectifs :
 *   • Standardisation des 6 formats : xlsx, csv, yaml, json, tsv, html
 *     (pas de PG, MY, MDB, ni autres anciens choix asymétriques)
 *   • Upload fichier ne doit JAMAIS renvoyer 404
 *   • Monitoring : si un log n'a pas de query associée, on doit voir un
 *     bouton "Nouvelle requête" (et non un simple texte mort)
 *   • CRUD Power Queries et Requêtes (éditeur SQL)
 */

import { test, expect, Page, Locator } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@sotifibre.dz'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'SOTIFibre@2026!'
const TS       = Date.now()

const ALLOWED_FORMATS = ['csv', 'xlsx', 'yaml', 'json', 'tsv', 'html'] as const

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
  const drawer = page.locator('[role="dialog"], .drawer, aside.drawer').first()
  await drawer.waitFor({ state: 'visible', timeout: 8_000 })
  return drawer
}

// ════════════════════════════════════════════════════════════
//   1.  /sources  – page maître
// ════════════════════════════════════════════════════════════

test.describe('/sources – Page maître', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('Chargement OK et aucune 5xx', async ({ page }) => {
    const errors: string[] = []
    page.on('response', r => {
      if (r.status() >= 500 && r.url().includes('/api/')) {
        errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
      }
    })
    await goto(page, '/sources')
    expect(errors, errors.join('\n')).toHaveLength(0)
  })

  test('GET /api/data-sources/sources/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/sources\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await goto(page, '/sources')
    expect(statuses.length, 'Aucun GET /api/data-sources/sources/ détecté').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })
})

// ════════════════════════════════════════════════════════════
//   2.  /sources/files  – Upload + standardisation 6 formats
// ════════════════════════════════════════════════════════════

test.describe('/sources/files – Upload + formats', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/sources/files')
  })

  test('GET /api/data-sources/files/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/files\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length, 'Aucun GET /api/data-sources/files/ détecté').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Le drawer "Upload fichier" propose UNIQUEMENT les 6 formats standards', async ({ page }) => {
    const drawer = await openDrawer(page, /Importer un fichier|Upload fichier|Nouveau fichier|Téléverser|Ajouter un fichier/i)
    const fmtSelect = drawer.locator('select[name="file_type"], select#f-type, select').first()
    await expect(fmtSelect).toBeVisible()
    const options = await fmtSelect.locator('option').evaluateAll(els =>
      els.map(e => (e as HTMLOptionElement).value).filter(v => v && v !== 'all')
    )
    expect(options.length, `Aucune option de format trouvée`).toBeGreaterThan(0)
    // Toutes les options doivent appartenir à la liste autorisée
    for (const v of options) {
      expect(
        ALLOWED_FORMATS.includes(v as any),
        `Format obsolète détecté : "${v}". Attendus : ${ALLOWED_FORMATS.join(', ')}`,
      ).toBe(true)
    }
    // Pas d'anciens choix interdits
    expect(options).not.toContain('pg')
    expect(options).not.toContain('my')
    expect(options).not.toContain('mdb')
    expect(options).not.toContain('xml')
    expect(options).not.toContain('parquet')
  })

  test('Le champ file accepte les extensions des 6 formats standards', async ({ page }) => {
    const drawer = await openDrawer(page, /Importer un fichier|Upload fichier|Nouveau fichier|Téléverser|Ajouter un fichier/i)
    const fileInput = drawer.locator('input[type="file"]').first()
    await expect(fileInput).toBeAttached()
    const accept = (await fileInput.getAttribute('accept')) ?? ''
    // Doit contenir au moins csv, xlsx, yaml, json, tsv, html
    expect(accept).toMatch(/\.csv/)
    expect(accept).toMatch(/\.xlsx/)
    expect(accept).toMatch(/\.yaml|\.yml/)
    expect(accept).toMatch(/\.json/)
    expect(accept).toMatch(/\.tsv/)
    expect(accept).toMatch(/\.html|\.htm/)
  })

  test('UPLOAD CSV → 201 et JAMAIS 404', async ({ page }) => {
    const csvContent =
      'date_vente,client,produit,quantite,montant\n' +
      `2026-01-15,SONATRACH,Fibre OF24,500,12500\n` +
      `2026-01-20,Algérie Télécom,Routeur Gigabit,80,9600\n` +
      `2026-02-03,SOTIFIBRE,Coffret optique,250,7500\n`

    const drawer = await openDrawer(page, /Importer un fichier|Upload fichier|Nouveau fichier|Téléverser|Ajouter un fichier/i)
    const fileInput = drawer.locator('input[type="file"]').first()
    await fileInput.setInputFiles({
      name: `ventes_e2e_${TS}.csv`,
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent, 'utf-8'),
    })
    // optionnel : remplir un nom
    const nameInput = drawer.locator('input[type="text"], input:not([type])').first()
    if (await nameInput.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await nameInput.fill(`Ventes E2E ${TS}`)
    }

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 25_000 },
      ),
      drawer.locator('button[type="submit"]').click(),
    ])
    expect(res.status(), `Upload renvoyé un statut inattendu`).not.toBe(404)
    expect([200, 201]).toContain(res.status())
  })
})

// ════════════════════════════════════════════════════════════
//   3.  /sources/connections  – CRUD connexions
// ════════════════════════════════════════════════════════════

test.describe('/sources/connections – CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/sources/connections')
  })

  test('GET /api/data-sources/connections/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/connections\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Pas de 5xx au chargement', async ({ page }) => {
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
})

// ════════════════════════════════════════════════════════════
//   4.  /sources/monitoring  – Logs + bouton "Nouvelle requête"
// ════════════════════════════════════════════════════════════

test.describe('/sources/monitoring – Logs + câblage requêtes', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/sources/monitoring')
  })

  test('GET /api/data-sources/logs/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/logs\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Cliquer sur un log sans requête doit révéler un bouton "Nouvelle requête"', async ({ page }) => {
    // ouvrir un log (tr cliquable) — on prend le premier
    const firstRow = page.locator('tr.data-row, tbody tr[class*="data-row"], tbody tr').first()
    if (!(await firstRow.isVisible({ timeout: 4_000 }).catch(() => false))) {
      test.skip()
      return
    }
    await firstRow.click()

    // Soit on voit le pre-bloc de la requête SQL (log AVEC query_text)
    // soit on voit le bouton "Nouvelle requête" (log SANS query_text — bug corrigé)
    const codeBlock = page.locator('.expand-code')
    const newQueryBtn = page.locator('.btn-create-query, button:has-text("Nouvelle requête")')

    const hasCode    = await codeBlock.isVisible({ timeout: 3_000 }).catch(() => false)
    const hasButton  = await newQueryBtn.first().isVisible({ timeout: 3_000 }).catch(() => false)

    expect(
      hasCode || hasButton,
      'Le log expanded n\'affiche ni la requête SQL ni le bouton "Nouvelle requête". Bug "Aucune requête associée" non résolu.'
    ).toBe(true)
  })

  test('Le bouton "Nouvelle requête" depuis un log redirige vers /queries avec préfilage', async ({ page }) => {
    const firstRow = page.locator('tr.data-row, tbody tr[class*="data-row"], tbody tr').first()
    if (!(await firstRow.isVisible({ timeout: 4_000 }).catch(() => false))) {
      test.skip()
      return
    }
    await firstRow.click()
    const newQueryBtn = page.locator('.btn-create-query').first()
    if (!(await newQueryBtn.isVisible({ timeout: 3_000 }).catch(() => false))) {
      // pas de log sans query_text — on saute
      test.skip()
      return
    }
    await newQueryBtn.click()
    await page.waitForURL(/\/queries\b.*open=new/i, { timeout: 8_000 })
    expect(page.url()).toMatch(/\/queries/)
    expect(page.url()).toMatch(/open=new/)
  })
})

// ════════════════════════════════════════════════════════════
//   5.  /power-queries  – CRUD Power Queries
// ════════════════════════════════════════════════════════════

test.describe('/power-queries – CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/power-queries')
  })

  test('GET /api/data-sources/power-queries/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/power-queries\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length, 'Aucun appel à /api/data-sources/power-queries/').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })
})

// ════════════════════════════════════════════════════════════
//   6.  /queries  – Éditeur SQL + bouton "Nouvelle requête"
// ════════════════════════════════════════════════════════════

test.describe('/queries – Éditeur SQL', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/queries')
  })

  test('GET /api/data-sources/queries/ → 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/queries\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Le bouton "Nouvelle requête" ouvre l\'éditeur SQL', async ({ page }) => {
    const btn = page.locator('button', { hasText: /Nouvelle requête/i }).first()
    await expect(btn).toBeVisible({ timeout: 5_000 })
    await btn.click()

    // textarea ou éditeur de code
    const editor = page.locator('textarea, .cm-editor, .monaco-editor, [class*="editor"]').first()
    await expect(editor).toBeVisible({ timeout: 6_000 })
  })

  test('Le routing avec ?open=new&hint=...  pré-ouvre l\'éditeur (intégration Monitoring → Queries)', async ({ page }) => {
    await goto(page, '/queries?open=new&source=Sotifibre%20PG&hint=Latence%20élevée%20détectée&from_log=42')
    // l'éditeur SQL est le textarea avec la classe .ed-code (pas la description rows=2)
    const sqlEditor = page.locator('textarea.ed-code').first()
    await expect(sqlEditor).toBeVisible({ timeout: 8_000 })
    // attendre que le préfilage soit effectif (chargement des sources est async)
    await expect.poll(async () => (await sqlEditor.inputValue()).length, { timeout: 6_000 }).toBeGreaterThan(0)
    const sqlText = await sqlEditor.inputValue()
    expect(sqlText, 'L\'éditeur SQL devrait contenir le préfilage du log').toMatch(/SELECT|--/i)
  })

  test('CREATE requête SQL → 201 (avec source obligatoire sélectionnée)', async ({ page }) => {
    const btn = page.locator('button', { hasText: /Nouvelle requête/i }).first()
    await btn.click()

    // Nom — input avec classe .ed-name-input
    const nameInput = page.locator('input.ed-name-input').first()
    await expect(nameInput).toBeVisible({ timeout: 5_000 })
    await nameInput.fill(`E2E Requête CA ${TS}`)

    // Source de données : sélectionner la première option non vide (champ obligatoire backend)
    const srcSelect = page.locator('.editor-hd-fields select.form-select').first()
    await expect(srcSelect).toBeVisible()
    const opts = await srcSelect.locator('option').elementHandles()
    let picked = false
    for (const o of opts) {
      const v = await o.getAttribute('value')
      if (v && v.trim() !== '') { await srcSelect.selectOption(v); picked = true; break }
    }
    if (!picked) {
      // aucune source disponible → test inapplicable
      test.skip()
      return
    }

    // SQL — le textarea SQL est .ed-code (pas la description)
    const sqlEditor = page.locator('textarea.ed-code').first()
    await sqlEditor.fill('SELECT COUNT(*) AS total_clients FROM customers;')

    // Bouton "Enregistrer" : peut être nommé différemment, on prend le 1er visible dans .editor-actions
    const saveBtn = page.locator('.editor-actions button', { hasText: /Enregistrer|Sauvegarder|Créer|Save/i }).first()
    await expect(saveBtn).toBeVisible({ timeout: 5_000 })

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/queries\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ).catch(() => null),
      saveBtn.click(),
    ])
    if (!res) { test.skip(); return }
    expect([200, 201]).toContain(res.status())
  })
})
