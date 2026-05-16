/**
 * Tests E2E exhaustifs — Page /sources/files
 * CRUD complet : upload, edit, delete + contrôles de format et de validation
 */
import { test, expect, Page } from '@playwright/test'
import path from 'path'
import os from 'os'
import fs from 'fs'

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

async function goToFiles(page: Page) {
  await page.goto('/sources/files')
  await page.waitForLoadState('networkidle')
}

/** Crée un fichier temporaire CSV et retourne son chemin */
function makeTempCsv(filename: string, content?: string): string {
  const dir  = os.tmpdir()
  const fpath = path.join(dir, filename)
  const data  = content ?? `id,nom,valeur\n1,Alpha,100\n2,Beta,200\n3,Gamma,300\n`
  fs.writeFileSync(fpath, data)
  return fpath
}

/** Crée un fichier JSON temporaire */
function makeTempJson(filename: string): string {
  const dir   = os.tmpdir()
  const fpath = path.join(dir, filename)
  const data  = JSON.stringify([{ id: 1, site: 'Alger', debit: 1000 }, { id: 2, site: 'Oran', debit: 850 }])
  fs.writeFileSync(fpath, data)
  return fpath
}

// ─── Suite 1 : Chargement ────────────────────────────────────────────────────

test.describe('/sources/files – Chargement', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('GET /api/data-sources/files/ → 200 avec liste valide', async ({ page }) => {
    const responses: number[] = []
    page.on('response', r => {
      if (/\/api\/data-sources\/files\/(\?|$)/.test(r.url()) && r.request().method() === 'GET')
        responses.push(r.status())
    })
    await page.reload()
    await page.waitForLoadState('networkidle')
    expect(responses.length).toBeGreaterThan(0)
    expect(responses[0]).toBe(200)
  })

  test('La page affiche les colonnes : Nom, Format, Taille, Lignes, Statut', async ({ page }) => {
    const hd = page.locator('.table-hd')
    if (await hd.isVisible()) {
      const text = await hd.innerText()
      expect(text).toMatch(/nom/i)
      expect(text).toMatch(/format/i)
      expect(text).toMatch(/statut/i)
    } else {
      // Pas de fichiers — vérifier l'état vide ou la page elle-même
      await expect(page.locator('.files-page').first()).toBeVisible({ timeout: 8_000 })
    }
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
})

// ─── Suite 2 : Drawer CREATE ────────────────────────────────────────────────

test.describe('/sources/files – Drawer import', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('Le bouton "Importer" ouvre le drawer avec les bons champs', async ({ page }) => {
    await page.locator('button', { hasText: /Importer/i }).first().click()
    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    // Champ fichier (input[type=file] peut être non-visible pour Playwright → toBeAttached)
    await expect(page.locator('#f-file')).toBeAttached({ timeout: 8_000 })

    // Champ nom
    await expect(page.locator('#f-fname')).toBeVisible()

    // Champ format — doit être un <select> natif
    const ftype = page.locator('#f-ftype')
    await expect(ftype).toBeVisible()
    const tag = await ftype.evaluate((el: HTMLSelectElement) => el.tagName.toLowerCase())
    expect(tag).toBe('select')
  })

  test('Le select #f-ftype contient les 6 formats standards', async ({ page }) => {
    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const opts = page.locator('#f-ftype option')
    const count = await opts.count()
    expect(count).toBe(6)

    const values = await opts.evaluateAll(
      (els: HTMLOptionElement[]) => els.map(e => e.value)
    )
    expect(values).toContain('csv')
    expect(values).toContain('xlsx')
    expect(values).toContain('yaml')
    expect(values).toContain('json')
    expect(values).toContain('tsv')
    expect(values).toContain('html')
    // Anciens formats supprimés
    expect(values).not.toContain('excel')
    expect(values).not.toContain('parquet')
    expect(values).not.toContain('xml')
    expect(values).not.toContain('txt')
  })

  test('Le bouton Importer est désactivé sans fichier sélectionné', async ({ page }) => {
    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    const submitBtn = page.locator('[role="dialog"] button[type="submit"]')
    await expect(submitBtn).toBeDisabled()
  })
})

// ─── Suite 3 : UPLOAD (CREATE) ──────────────────────────────────────────────

test.describe('/sources/files – UPLOAD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('UPLOAD CSV : POST /api/data-sources/files/ → 201 avec nom correct', async ({ page }) => {
    const csvPath  = makeTempCsv(`inventaire_reseau_${TS}.csv`)
    const fileName = `Inventaire Réseau ${TS}`

    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-file').setInputFiles(csvPath)
    await page.locator('#f-fname').fill(fileName)
    await page.locator('#f-ftype').selectOption('csv')

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(201)
    const body = await res.json()
    expect(body.name ?? body.data?.name ?? body.original_name).toBeTruthy()
  })

  test('UPLOAD CSV : le fichier apparaît dans la liste après upload', async ({ page }) => {
    const csvPath  = makeTempCsv(`logs_serveur_mai2026_${TS}.csv`)
    const fileName = `Logs Serveur ${TS}`

    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-file').setInputFiles(csvPath)
    await page.locator('#f-fname').fill(fileName)

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${fileName}`).first()).toBeVisible({ timeout: 8_000 })
  })

  test('UPLOAD JSON : POST → 201 + format JSON affiché dans la liste', async ({ page }) => {
    const jsonPath = makeTempJson(`rapport_qualite_fibre_${TS}.json`)
    const fileName = `Rapport Qualité Fibre ${TS}`

    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-file').setInputFiles(jsonPath)
    await page.locator('#f-fname').fill(fileName)
    await page.locator('#f-ftype').selectOption('json')

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])

    expect(res.status()).toBe(201)
    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${fileName}`).first()).toBeVisible({ timeout: 8_000 })
  })

  test('La sélection d\'un fichier .csv auto-sélectionne le format CSV', async ({ page }) => {
    const csvPath = makeTempCsv(`auto_detect_${TS}.csv`)

    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })

    await page.locator('#f-file').setInputFiles(csvPath)
    // Après sélection, le format doit être auto-détecté
    const selectedVal = await page.locator('#f-ftype').inputValue()
    expect(selectedVal).toBe('csv')
  })
})

// ─── Suite 4 : EDIT ─────────────────────────────────────────────────────────

test.describe('/sources/files – EDIT', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('Le bouton crayon ouvre le drawer en mode édition avec le nom pré-rempli', async ({ page }) => {
    // S'assurer qu'il y a au moins un fichier
    const hasRows = await page.locator('.table-row').count()
    if (hasRows === 0) {
      test.skip()
      return
    }

    const editBtn = page.locator('.act-btn[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const drawer = page.locator('[role="dialog"]')
    await expect(drawer).toBeVisible()

    // Le drawer doit afficher "Modifier le fichier"
    await expect(drawer.locator('.drawer-title')).toContainText(/Modifier/i)

    // Le champ nom doit être pré-rempli
    const nameVal = await page.locator('#f-fname').inputValue()
    expect(nameVal.trim().length).toBeGreaterThan(0)

    // En mode édition, le champ fichier n'est pas présent
    await expect(page.locator('#f-file')).not.toBeVisible()
  })

  test('EDIT : PATCH /api/data-sources/files/{id}/ → 200 avec nouveau nom', async ({ page }) => {
    const hasRows = await page.locator('.table-row').count()
    if (hasRows === 0) {
      test.skip()
      return
    }

    const editBtn = page.locator('.act-btn[title="Modifier"]').first()
    await expect(editBtn).toBeVisible({ timeout: 8_000 })
    await editBtn.click()

    const newName = `Modifié E2E ${TS}`
    await page.locator('#f-fname').fill(newName)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/[^/]+\/?$/.test(r.url()) && r.request().method() === 'PATCH',
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

test.describe('/sources/files – DELETE', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('DELETE : suppression d\'un fichier créé via l\'UI → 204 + disparition', async ({ page }) => {
    // 1. Uploader un fichier dédié au test de suppression
    const csvPath  = makeTempCsv(`del_test_${TS}.csv`)
    const fileName = `DEL E2E ${TS}`

    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })
    await page.locator('#f-file').setInputFiles(csvPath)
    await page.locator('#f-fname').fill(fileName)

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')

    // 2. Retrouver la ligne et cliquer Supprimer
    const row = page.locator('.table-row').filter({ hasText: fileName })
    await expect(row).toBeVisible({ timeout: 8_000 })

    await row.locator('.act-btn--del').click()

    // 3. Confirmer avec "Oui"
    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/[^/]+\/?$/.test(r.url()) && r.request().method() === 'DELETE',
        { timeout: 15_000 },
      ),
      row.locator('.act-btn--yes').click(),
    ])

    expect(res.status()).toBe(204)
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.table-row').filter({ hasText: fileName })).not.toBeVisible({ timeout: 8_000 })
  })
})

// ─── Suite 6 : PROCESS + PREVIEW ─────────────────────────────────────────────

test.describe('/sources/files – PROCESS & PREVIEW', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goToFiles(page)
  })

  test('PROCESS : clic sur "Traiter" déclenche POST /process/ → met à jour le statut', async ({ page }) => {
    const csvPath  = makeTempCsv(
      `mesures_qualite_${TS}.csv`,
      `timestamp,site,signal_dbm,debit_mbps\n2026-05-01 08:00,Alger-Centre,-72,850\n2026-05-01 08:05,Oran-Ouest,-65,920\n`
    )
    const fileName = `Mesures Qualité ${TS}`

    // Upload
    await page.locator('button', { hasText: /Importer/i }).first().click()
    await page.locator('[role="dialog"]').waitFor({ state: 'visible' })
    await page.locator('#f-file').setInputFiles(csvPath)
    await page.locator('#f-fname').fill(fileName)

    await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15_000 },
      ),
      page.locator('[role="dialog"] button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle')

    // Traiter
    const row = page.locator('.table-row').filter({ hasText: fileName })
    await expect(row).toBeVisible({ timeout: 8_000 })

    const [processRes] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/data-sources\/files\/.+\/process\//.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      row.locator('.act-btn--run').click(),
    ])

    expect(processRes.status()).toBe(200)
    await page.waitForLoadState('networkidle')

    // Le statut devrait maintenant être "Traité"
    await expect(row.locator('.status-chip')).toContainText(/traité/i, { timeout: 8_000 })
  })
})
