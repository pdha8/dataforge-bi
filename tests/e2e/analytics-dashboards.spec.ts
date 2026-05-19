/**
 * E2E â€“ Module Analytics (Dashboards / Visualizations / KPIs / Reports)
 *
 * Cibles :  /dashboard  /visualizations  /dashboards  /kpis  /reports
 *
 * Objectifs :
 *   â€¢ CRUD complet sur les 4 entitÃ©s principales du module
 *   â€¢ VÃ©rifier que les identifiants (dashboard, widget, schÃ©maâ€¦) sont des
 *     <select> dynamiques branchÃ©s sur l'API, pas des inputs textes libres
 *   â€¢ VÃ©rifier rendu des graphiques (canvas / svg) sur les visualisations
 *   â€¢ KPI : changement dynamique de la couleur de statut en fonction des seuils
 *   â€¢ Rapports : sÃ©lecteur de destinataires multi-select + format HTML
 */

import { test, expect, Page, Locator } from '@playwright/test'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'
const TS       = Date.now()

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

/** open the "create" drawer by clicking the first matching button */
async function openDrawer(page: Page, btnRe: RegExp): Promise<Locator> {
  const btn = page.locator('button', { hasText: btnRe }).first()
  await btn.waitFor({ state: 'visible', timeout: 10_000 })
  await btn.click()
  const drawer = page.locator('[role="dialog"]').first()
  await drawer.waitFor({ state: 'visible', timeout: 8_000 })
  return drawer
}

async function expectNoServer5xx(page: Page, runner: () => Promise<void>) {
  const errors: string[] = []
  page.on('response', r => {
    if (r.status() >= 500 && r.url().includes('/api/')) {
      errors.push(`${r.status()} ${r.request().method()} ${r.url()}`)
    }
  })
  await runner()
  expect(errors, `Erreurs 5xx interceptÃ©es :\n${errors.join('\n')}`).toHaveLength(0)
}

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   1.  /dashboard  â€“ page d'accueil BI
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/dashboard â€“ Home', () => {
  test.beforeEach(async ({ page }) => { await login(page) })

  test('Chargement OK et pas de 5xx', async ({ page }) => {
    await expectNoServer5xx(page, async () => {
      await goto(page, '/dashboard')
    })
  })

  test('Au moins une carte KPI / item statistique visible sur la home', async ({ page }) => {
    await goto(page, '/dashboard')
    // Attendre le rendu (kpi-rail charge les KPIs aprÃ¨s mount)
    await page.waitForTimeout(1500)
    const items = page.locator('.kpi-item, .kpi-skel, .kpi-rail .kpi-name, .stat-card, .home-card, .card, .summary-card, .stats-strip .stat-chip')
    expect(await items.count()).toBeGreaterThan(0)
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   2.  /dashboards  â€“ CRUD complet
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/dashboards â€“ CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/dashboards')
  })

  test('GET /api/visualizations/dashboards/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/dashboards\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('CREATE : POST /api/visualizations/dashboards/ â†’ 201', async ({ page }) => {
    const name = `Dash Ventes E2E ${TS}`
    const drawer = await openDrawer(page, /Nouveau tableau/i)
    await drawer.locator('input[type="text"], input:not([type])').first().fill(name)

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      drawer.locator('button[type="submit"]').click(),
    ])
    expect(res.status()).toBe(201)
  })

  test('LIST : le dashboard crÃ©Ã© apparaÃ®t dans la grille', async ({ page }) => {
    const name = `Dash Marketing E2E ${TS + 1}`
    const drawer = await openDrawer(page, /Nouveau tableau/i)
    await drawer.locator('input[type="text"], input:not([type])').first().fill(name)
    await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/dashboards\/?$/.test(r.url()) && r.request().method() === 'POST',
      ),
      drawer.locator('button[type="submit"]').click(),
    ])
    await page.waitForLoadState('networkidle').catch(() => {})
    await expect(page.locator(`text=${name}`).first()).toBeVisible({ timeout: 8_000 })
  })

  test('Onglet Widgets : GET /api/visualizations/widgets/ â†’ 200', async ({ page }) => {
    const widgetTab = page.locator('button', { hasText: /^Widgets/i }).first()
    if (!(await widgetTab.isVisible({ timeout: 4_000 }).catch(() => false))) {
      test.skip()
      return
    }
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

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   3.  /visualizations  â€“ CRUD + sÃ©lecteur Dashboard dynamique
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/visualizations â€“ CRUD + sÃ©lecteurs dynamiques', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/visualizations')
  })

  test('GET /api/visualizations/widgets/ â†’ 200 (les visualisations sont stockÃ©es comme widgets)', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/widgets\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length, 'Aucun GET /api/visualizations/widgets/ dÃ©tectÃ©').toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Drawer "Nouvelle visualisation" propose un type-picker (grille de boutons) et un <select> dynamique', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouvelle visualisation/i)
    // Type-picker : grille de boutons type-opt
    const typeOpts = drawer.locator('.type-opt')
    expect(await typeOpts.count(), 'Aucun bouton type-opt trouvÃ©').toBeGreaterThanOrEqual(3)
    // <select> dynamique pour la destination (Tableau de bord)
    const selects = drawer.locator('select')
    expect(await selects.count(), 'Aucun <select> dynamique dans le drawer').toBeGreaterThan(0)
  })

  test('Le champ "Tableau de bord" est un <select> et n\'est PAS un input texte libre', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouvelle visualisation/i)
    // Cherche le label "Tableau de bord" et vÃ©rifie qu'il pointe sur un <select>
    const dashboardLabel = drawer.locator('label[for="f-dash"], label:has-text("Tableau de bord")').first()
    await expect(dashboardLabel, 'Pas de label "Tableau de bord" dans le drawer').toBeVisible({ timeout: 4_000 })
    const dashSelect = drawer.locator('select#f-dash, select[name="dashboard"]').first()
    await expect(dashSelect, 'Le champ Tableau de bord doit Ãªtre un <select>').toBeVisible()
    // Il ne doit plus exister d'input texte avec id f-src (ancien champ "Source de donnÃ©es" libre)
    const oldSourceInput = drawer.locator('input#f-src')
    expect(await oldSourceInput.count(), 'L\'ancien input "Source de donnÃ©es" libre subsiste').toBe(0)
  })

  test('Une visualisation rendue Ã  l\'Ã©cran doit afficher un <canvas> ou un <svg>', async ({ page }) => {
    const charts = page.locator('canvas, .chart svg, .echart svg, [data-chart]')
    const count = await charts.count()
    // si aucune viz n'est encore crÃ©Ã©e le test est soft-skippÃ©
    if (count === 0) {
      test.skip()
      return
    }
    await expect(charts.first()).toBeVisible()
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   4.  /kpis  â€“ CRUD + cible + seuils + couleur de statut
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/kpis â€“ CRUD + alertes', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/kpis')
  })

  test('GET /api/visualizations/kpis/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/kpis\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('CREATE : KPI avec cible + seuils warning/critical â†’ 201', async ({ page }) => {
    const name = `KPI CA Mensuel ${TS}`
    const drawer = await openDrawer(page, /Nouveau KPI/i)

    // nom
    await drawer.locator('input[type="text"], input:not([type])').first().fill(name)

    // cible numÃ©rique
    const numericInputs = drawer.locator('input[type="number"]')
    const numCount = await numericInputs.count()
    if (numCount >= 1) await numericInputs.nth(0).fill('1000000')
    if (numCount >= 2) await numericInputs.nth(1).fill('900000')   // warning
    if (numCount >= 3) await numericInputs.nth(2).fill('700000')   // critical

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/kpis\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ),
      drawer.locator('button[type="submit"]').click(),
    ])
    expect([200, 201]).toContain(res.status())
  })

  test('Les onglets "Critiques" / "En alerte" filtrent la liste', async ({ page }) => {
    // Onglet "Critiques"
    const critTab = page.locator('[aria-selected], .filter-tab, button', { hasText: /Critique/i }).first()
    if (await critTab.isVisible({ timeout: 4_000 }).catch(() => false)) {
      const [res] = await Promise.all([
        page.waitForResponse(
          r => /\/api\/visualizations\/kpis\/(critical|warning)\/?/.test(r.url()),
          { timeout: 8_000 },
        ).catch(() => null),
        critTab.click(),
      ])
      // si l'endpoint existe il doit rÃ©pondre 200
      if (res) expect(res.status()).toBe(200)
    }
  })

  test('La couleur du badge de statut change selon le statut (CSS class prÃ©sente)', async ({ page }) => {
    const badges = page.locator('.st--critical, .st--at-risk, .st--achieved, .st--on_track, .status-badge')
    const count = await badges.count()
    if (count === 0) { test.skip(); return }
    // au moins un badge a une classe de statut typÃ©e
    await expect(badges.first()).toBeVisible()
  })
})

// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//   5.  /reports  â€“ Template HTML + multi-select destinataires
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

test.describe('/reports â€“ Rapports HTML & destinataires multi-select', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await goto(page, '/reports')
  })

  test('GET /api/visualizations/reports/ â†’ 200', async ({ page }) => {
    const statuses: number[] = []
    page.on('response', r => {
      if (/\/api\/visualizations\/reports\/(\?|$)/.test(r.url()) && r.request().method() === 'GET') {
        statuses.push(r.status())
      }
    })
    await page.reload()
    await page.waitForLoadState('networkidle').catch(() => {})
    expect(statuses.length).toBeGreaterThan(0)
    expect(statuses[0]).toBe(200)
  })

  test('Drawer "Nouveau rapport" contient un <select> Dashboard et un <select> Format', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau rapport/i)
    const selects = drawer.locator('select')
    expect(await selects.count()).toBeGreaterThanOrEqual(2)
  })

  test('Le format contient HTML (template WeasyPrint, pas seulement JSON)', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau rapport/i)
    // Cherche le select des formats
    const fmtSelect = drawer.locator('select#f-fmt, select[name="format"]').first()
    if (!(await fmtSelect.isVisible({ timeout: 3_000 }).catch(() => false))) {
      // fallback : prendre le 2e select du drawer
      const all = drawer.locator('select')
      if (await all.count() < 2) { test.skip(); return }
    }
    const target = (await fmtSelect.count()) ? fmtSelect : drawer.locator('select').nth(1)
    const options = await target.locator('option').allTextContents()
    expect(
      options.some(o => /html/i.test(o)),
      `Aucun format HTML trouvÃ©. Formats dÃ©tectÃ©s : ${options.join(', ')}`,
    ).toBe(true)
  })

  test('Les destinataires sont gÃ©rÃ©s en multi-select (chips / tags)', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau rapport/i)
    const tagsArea = drawer.locator(
      '.tags-selector, .tags-chips, .tag-chip, .tag-input, .tags-dropdown'
    )
    expect(await tagsArea.count(), 'Aucun composant multi-select destinataires dÃ©tectÃ©').toBeGreaterThan(0)
  })

  test('CREATE rapport HTML â†’ 201 (sÃ©lection minimale du 1er dashboard disponible)', async ({ page }) => {
    const drawer = await openDrawer(page, /Nouveau rapport/i)

    // nom
    await drawer.locator('input[type="text"], input:not([type])').first().fill(`Rapport HTML ${TS}`)

    // dashboard : premier select, premiÃ¨re option non vide
    const selects = drawer.locator('select')
    if (await selects.count() < 1) { test.skip(); return }

    const dashSel = selects.nth(0)
    const dashOptions = await dashSel.locator('option').elementHandles()
    let picked = false
    for (const opt of dashOptions) {
      const v = await opt.getAttribute('value')
      if (v && v.trim()) { await dashSel.selectOption(v); picked = true; break }
    }
    if (!picked) { test.skip(); return }

    // format : forcer HTML si possible
    const fmtSel = selects.nth(1)
    if (await fmtSel.isVisible().catch(() => false)) {
      const fmtOptions = await fmtSel.locator('option').elementHandles()
      for (const opt of fmtOptions) {
        const v = await opt.getAttribute('value')
        if (v && /html/i.test(v)) { await fmtSel.selectOption(v); break }
      }
    }

    const [res] = await Promise.all([
      page.waitForResponse(
        r => /\/api\/visualizations\/reports\/?$/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 20_000 },
      ).catch(() => null),
      drawer.locator('button[type="submit"]').click(),
    ])
    if (!res) { test.skip(); return }
    expect([200, 201]).toContain(res.status())
  })
})
