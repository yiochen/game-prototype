import assert from 'node:assert/strict';
import { existsSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const folder = new URL('./', import.meta.url);
const names = ['browser-playback.json', 'browser-desktop.png', 'browser-phone-eat-salmon.png', 'browser-phone-empty-dark.png', 'headless-provenance.json'];
for (const name of names) assert.ok(!existsSync(new URL(name, folder)), `Refusing to overwrite ${name}`);
const browser = await chromium.launch({ headless: true });
const outputs = {};
const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  await page.goto('http://localhost:4178/prototypes/sushi-loop/assets/refinement/objects/customer-ellis/candidates/round-03/review.html');
  await page.waitForFunction(() => window.reviewReady === true);
  const identity = await page.evaluate(() => ({ userAgent: navigator.userAgent, platform: navigator.platform, hardwareConcurrency: navigator.hardwareConcurrency }));
  for (const [index, viewport] of [{ width: 1280, height: 720 }, { width: 390, height: 844 }].entries()) {
    await page.setViewportSize(viewport);
    await page.locator('#audit-playback').click();
    await page.waitForFunction(count => window.evidenceRuns.length === count, index + 1, { timeout: 60000 });
    const run = await page.evaluate(() => window.evidenceRuns.at(-1));
    assert.equal(run.clips.length, 12);
    assert.deepEqual(run.viewport, [viewport.width, viewport.height]);
    for (const clip of run.clips) {
      assert.equal(clip.midway.length, 4);
      assert.equal(clip.after.length, 4);
      for (const state of [...clip.midway, ...clip.after]) {
        assert.deepEqual(state.videoSize, [384, 640]);
        assert.ok(Math.abs(state.duration - 1) < 0.02);
        assert.equal(state.playbackRate, 1);
        assert.ok(state.readyState >= 2);
        assert.ok(state.totalVideoFrames > 0);
      }
      for (const state of clip.after) {
        assert.ok(state.totalVideoFrames >= 12, `${clip.id}/${state.direction}: incomplete decode`);
        if (!clip.loop) assert.equal(state.ended, true, `${clip.id}/${state.direction}: one-shot did not end`);
      }
    }
    console.log(JSON.stringify({ viewport, clips: run.clips.length, decodedStreams: run.clips.length * 4,
      maxDropped: Math.max(...run.clips.flatMap(c => c.after.map(v => v.droppedVideoFrames))) }));
    if (index === 0) {
      await page.locator('#clip').selectOption('stand');
      await page.waitForTimeout(550);
      await page.evaluate(() => currentPlayers.forEach(v => v.pause()));
      await page.locator('.players').scrollIntoViewIfNeeded();
      outputs['browser-desktop.png'] = await page.screenshot();
    } else {
      await page.locator('#clip').selectOption('eat-salmon');
      await page.waitForTimeout(550);
      await page.evaluate(() => currentPlayers.forEach(v => v.pause()));
      await page.locator('.card').first().scrollIntoViewIfNeeded();
      outputs['browser-phone-eat-salmon.png'] = await page.screenshot();
      await page.locator('#background').selectOption('#1c222a');
      await page.locator('#clip').selectOption('seated-wait-empty');
      await page.waitForTimeout(550);
      await page.evaluate(() => currentPlayers.forEach(v => v.pause()));
      await page.locator('.card').first().scrollIntoViewIfNeeded();
      outputs['browser-phone-empty-dark.png'] = await page.screenshot();
    }
  }
  const runs = await page.locator('#evidence').textContent();
  assert.equal(JSON.parse(runs).length, 2);
  assert.deepEqual(errors, []);
  outputs['browser-playback.json'] = runs + '\n';
  outputs['headless-provenance.json'] = JSON.stringify({
    browser: 'Playwright-managed Chromium', version: browser.version(), headless: true, ...identity,
    viewports: [[1280, 720], [390, 844]], deviceScaleFactor: 1, errors,
    checks: 'Actual review-page Play all 48 clips button in both viewports. Each native 384x640 stream decoded at least12 frames at normal playback speed; all nonloop clips ended. Raw page evidence retained without rewriting its metrics.',
    screenshots: names.filter(n => n.endsWith('.png')),
    limitation: 'Desktop headless Chromium at desktop and phone viewport sizes; not IAB, an Android device, or final integrated Godot gameplay. Playback/decode checks do not imply independent visual approval.'
  }, null, 2) + '\n';
} finally {
  await browser.close();
}
for (const [name, data] of Object.entries(outputs)) writeFileSync(new URL(name, folder), data);
