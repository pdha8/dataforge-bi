import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.FRONTEND_URL ?? 'http://localhost:5173'

export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  retries: 1,
  reporter: [['list'], ['html', { outputFolder: '../test-results/playwright-report', open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
