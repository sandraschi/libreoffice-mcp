import { defineConfig } from '@playwright/test'

const backendPort = 10981
const frontendPort = 10983

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: `uv run libreoffice-mcp --http --port ${backendPort}`,
      cwd: '..',
      port: backendPort,
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: `npm run dev -- --port ${frontendPort} --host 127.0.0.1`,
      port: frontendPort,
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
