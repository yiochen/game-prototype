import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const library = JSON.parse(readFileSync(new URL('../assets/production/library.json', import.meta.url), 'utf8'));
const approved = library.approval?.finalAssets === 'approved';
const productionStatus = approved ? 'Approved production art · Faceted lighting · matte wood · muted clay rails' : 'Art direction approved · native Faceted rollout in progress';

test('approved art status follows the production manifest and historical experiments remain clearly labeled', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const stage = page.locator('#prototype-stage');
  for (const story of ['object-library', 'object-crate-wood', 'scene-restaurant', 'scene-underwater']) {
    await page.goto(`/prototypes/sushi-loop/?ntl-drawer-state=hidden#${story}`);
    await expect(stage).toHaveAttribute('data-story', story);
    await expect(page.locator('.studio-hint')).toContainText(productionStatus);
    await expect(stage).not.toContainText('approval is still pending');
    if (story === 'object-crate-wood') await expect(stage.locator('.object-review-heading .object-status')).toHaveText(approved ? 'Approved' : 'Ready to review');
  }
  await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#art-catalog');
  await expect(stage.locator('.world-catalog-status')).toHaveText(approved ? 'ISSUE 33 · ASSETS APPROVED' : 'ISSUE 33 · ART APPROVED · ROLLOUT IN PROGRESS');
  for (const [story, historicalLabel] of [
    ['character-lighting-study', 'HISTORICAL BLENDER LIGHTING STUDY'],
    ['character-scale-study', 'HISTORICAL CHARACTER PROPORTION STUDY'],
    ['projection-study', 'HISTORICAL PROJECTION STUDY'],
    ['decoration-study', 'HISTORICAL CONCEPT DECORATION STUDY'],
  ]) {
    await page.goto(`/prototypes/sushi-loop/?ntl-drawer-state=hidden#${story}`);
    await expect(stage).toContainText(historicalLabel);
    await expect(stage).not.toContainText('production unchanged');
    await expect(stage).not.toContainText('Production recapture is pending');
    await expect(stage).not.toContainText('Issue 33 stays open');
  }
});
