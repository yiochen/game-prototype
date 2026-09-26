import { advanceDeal as settleDelivery, claimMilestone } from '../engine.js';

// Existing card tests take tips so upgrades and room output remain unchanged.
export function advanceDeal(state, moves) {
  const advanced = settleDelivery(state);
  while (state.phase === 'milestone') {
    claimMilestone(state, 'tips');
    moves?.push(['gift', 'tips']);
  }
  return advanced;
}
export async function claimTips(page) {
  while (await page.locator('#milestone-dialog').isVisible()) {
    await page.locator('[data-gift="tips"]').click();
  }
}
