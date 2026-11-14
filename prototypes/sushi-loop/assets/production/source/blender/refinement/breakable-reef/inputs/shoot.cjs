// node shoot.cjs PAGE.html OUT.png — screenshot the assembled patch at 1:1.
const { chromium } = require('playwright');
(async () => {
  const [page, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1800, height: 1800 }, deviceScaleFactor: 1 });
  await p.goto('file://' + require('path').resolve(page)); await p.waitForLoadState('networkidle');
  await p.locator('#p').screenshot({ path: out }); await b.close();
})();
