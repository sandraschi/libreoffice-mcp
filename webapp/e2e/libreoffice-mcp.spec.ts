import { expect, test } from '@playwright/test'

const BACKEND = 'http://127.0.0.1:10981'

test.describe('LibreOffice MCP dashboard', () => {
  test('dashboard loads with health banner and stats', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
    await expect(page.getByText('LibreOffice MCP')).toBeVisible()
    await expect(page.getByText('Templates')).toBeVisible()
    await expect(page.getByText('Jobs')).toBeVisible()
  })

  test('sidebar navigates all primary routes', async ({ page }) => {
    await page.goto('/')
    const routes: Array<{ link: string; heading: string }> = [
      { link: 'Simple Actions', heading: 'Simple Actions' },
      { link: 'Workflows', heading: 'Workflows' },
      { link: 'Convert', heading: 'Convert' },
      { link: 'Templates', heading: 'Templates' },
      { link: 'Batch Pack', heading: 'Batch Pack' },
      { link: 'Output', heading: 'Output' },
      { link: 'Upload', heading: 'Upload' },
      { link: 'Jobs', heading: 'Jobs' },
      { link: 'Apps Hub', heading: 'Fleet Apps Hub' },
      { link: 'Chat', heading: 'Chat' },
      { link: 'Tests', heading: 'Tests' },
      { link: 'Tools', heading: 'Tools Hub' },
      { link: 'Settings', heading: 'Settings' },
      { link: 'Skills', heading: 'Skills' },
      { link: 'Logs', heading: 'Logs' },
      { link: 'API Docs', heading: 'API Docs' },
      { link: 'Status', heading: 'Status' },
      { link: 'Help', heading: 'Help' },
    ]
    for (const { link, heading } of routes) {
      await page.getByRole('link', { name: link, exact: true }).click()
      await expect(page.getByRole('heading', { name: heading })).toBeVisible()
    }
  })

  test('convert page has queue form', async ({ page }) => {
    await page.goto('/convert')
    await expect(page.getByPlaceholder(/fleet-pulse/)).toBeVisible()
    await expect(
      page.getByRole('button', { name: /Queue convert job/i }),
    ).toBeVisible()
  })

  test('templates gallery lists fleet templates', async ({ page }) => {
    await page.goto('/templates')
    await expect(page.getByText('fleet-report.odt')).toBeVisible({
      timeout: 15_000,
    })
    await expect(page.getByText('fleet-board-pack.odt')).toBeVisible()
  })

  test('tools hub shows libreoffice portmanteau', async ({ page }) => {
    await page.goto('/tools')
    await expect(page.getByText('libreoffice')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('portmanteau')).toBeVisible()
    await expect(page.getByText('batch_pack')).toBeVisible()
  })

  test('help page shows coworker flows', async ({ page }) => {
    await page.goto('/help')
    await expect(page.getByText('LibreOffice MCP')).toBeVisible()
    await expect(page.getByText('coworker_weekly_report_pdf')).toBeVisible()
  })
})

test.describe('LibreOffice MCP REST API', () => {
  test('GET /health', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/health`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.status).toBe('healthy')
    expect(data.ports.backend).toBe(10981)
  })

  test('GET /api/tools', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/tools`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.tools[0].name).toBe('libreoffice')
  })

  test('GET /api/capabilities', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/capabilities`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.features.fleet_apps_hub).toBe(true)
    expect(data.features.simple_actions).toBe(true)
    expect(data.features.webapp_tests).toBe(true)
  })

  test('GET /api/actions catalog', async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/actions`)
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.success).toBe(true)
    expect(data.simple_actions.length).toBeGreaterThan(0)
  })

  test('POST /api/agentic plan', async ({ request }) => {
    const resp = await request.post(`${BACKEND}/api/agentic`, {
      data: { goal: 'check soffice status', execute: false },
    })
    expect(resp.ok()).toBeTruthy()
    const data = await resp.json()
    expect(data.success).toBe(true)
    expect(data.steps.length).toBeGreaterThan(0)
  })
})
