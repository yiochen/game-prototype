import { defineConfig } from '@playwright/test';
const baseURL = process.env.TEST_URL || 'http://127.0.0.1:4175';
export default defineConfig({
  testDir: './prototypes',
  testMatch: '**/tests/*.spec.js',
  timeout: 60000,
  workers: 1,
  use: { baseURL, headless: true, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: process.env.TEST_URL ? undefined : {
    command: 'npm run preview -- --port 4175 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
  },
  reporter: 'list',
});
