/**
 * GÃ©nÃ©ration automatique des captures d'Ã©cran de l'application
 * pour la documentation. Sortie : ../docs/screenshots/<page>.png
 */
import { test, Page } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const EMAIL    = process.env.TEST_USER_EMAIL    ?? 'admin@dataforge.tech'
const PASSWORD = process.env.TEST_USER_PASSWORD ?? 'DataForge@2026!'

const OUT = path.resolve(__dirname, '../../docs/screenshots')
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true })

test.use({ viewport: { width: 1600, height: 900 } })

async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[type="email"], input[name="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL(/\/(dashboard)?$/, { timeout: 20_000 })
}

async function shot(page: Page, route: string, name: string, wait = 1500) {
  await page.goto(route)
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(wait)
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false })
}

// â”€â”€â”€ Pages principales â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

test('screenshot â€“ dashboard',        async ({ page }) => { await login(page); await shot(page, '/dashboard',        'dashboard') })
test('screenshot â€“ sources',          async ({ page }) => { await login(page); await shot(page, '/sources',          'sources') })
test('screenshot â€“ sources-files',    async ({ page }) => { await login(page); await shot(page, '/sources/files',    'sources-files') })
test('screenshot â€“ sources-connect',  async ({ page }) => { await login(page); await shot(page, '/sources/connections','sources-connections') })
test('screenshot â€“ sources-monitor',  async ({ page }) => { await login(page); await shot(page, '/sources/monitoring','sources-monitoring') })
test('screenshot â€“ power-queries',    async ({ page }) => { await login(page); await shot(page, '/power-queries',    'power-queries') })
test('screenshot â€“ queries',          async ({ page }) => { await login(page); await shot(page, '/queries',          'queries') })

test('screenshot â€“ pipelines',        async ({ page }) => { await login(page); await shot(page, '/pipelines',        'pipelines') })
test('screenshot â€“ executions',       async ({ page }) => { await login(page); await shot(page, '/executions',       'executions') })

test('screenshot â€“ warehouse',        async ({ page }) => { await login(page); await shot(page, '/warehouse',        'warehouse') })
test('screenshot â€“ star-schema',      async ({ page }) => { await login(page); await shot(page, '/star-schema',      'star-schema') })
test('screenshot â€“ ml-analytics',     async ({ page }) => { await login(page); await shot(page, '/ml-analytics',     'ml-analytics') })

test('screenshot â€“ visualizations',   async ({ page }) => { await login(page); await shot(page, '/visualizations',   'visualizations') })
test('screenshot â€“ dashboards',       async ({ page }) => { await login(page); await shot(page, '/dashboards',       'dashboards') })
test('screenshot â€“ kpis',             async ({ page }) => { await login(page); await shot(page, '/kpis',             'kpis') })
test('screenshot â€“ reports',          async ({ page }) => { await login(page); await shot(page, '/reports',          'reports') })

test('screenshot â€“ notifications',    async ({ page }) => { await login(page); await shot(page, '/notifications',    'notifications') })
test('screenshot â€“ favorites',        async ({ page }) => { await login(page); await shot(page, '/favorites',        'favorites') })
test('screenshot â€“ admin',            async ({ page }) => { await login(page); await shot(page, '/admin',            'admin') })
test('screenshot â€“ profile',          async ({ page }) => { await login(page); await shot(page, '/profile',          'profile') })
