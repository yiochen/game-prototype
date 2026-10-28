import {test,expect} from '@playwright/test';
const url='/prototypes/sushi-loop/design/chef-development-preview/';
const key='sushi-loop-issue17-ui-review-v1';
const save=page=>page.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);
async function ready(page,state='develop',size={width:390,height:844}){await page.setViewportSize(size);await page.goto(url+`?state=${state}`);await page.locator('.scene').waitFor();await page.evaluate(()=>document.fonts.ready);}
const levelButton=page=>page.getByRole('button',{name:/^Level up Lena/});

test('one affordable input buys a level once, updates speed, unlocks tier and persists',async({page})=>{
 await ready(page);await expect(page.getByLabel('Next level preview')).toContainText('1.12× → 1.24×');await expect(page.getByLabel('Next level preview')).toContainText('Unlocks Yellow recipes');
 await levelButton(page).dblclick();let s=await save(page);expect(s.coins).toBe(1120);expect(s.staff[0].level).toBe(3);await expect(page.locator('.upgrade-result')).toContainText('Yellow recipes unlocked');await page.screenshot({path:'prototypes/sushi-loop/review/17/header-separator/upgraded-yellow-390x844.png'});
 await page.getByRole('tab',{name:'Recipes',exact:true}).click();const tamago=page.getByRole('button',{name:/Inspect Tamago/});await expect(tamago).not.toHaveClass(/wr-above/);await tamago.click();await expect(page.getByRole('button',{name:'Prepare',exact:true})).toBeEnabled();
 await page.getByRole('tab',{name:'Manage',exact:true}).click();await page.reload();expect((await save(page)).coins).toBe(1120);await expect(page.locator('.current-facts')).toContainText('1.24');
});

test('poor retains benefit/cost; MAX retains final stats without purchase; last level cannot exceed ceiling',async({page})=>{
 await ready(page,'poor');await expect(levelButton(page)).toBeDisabled();await expect(page.getByLabel('Next level preview')).toContainText('1.24×');await expect(page.locator('.budget-reason')).toHaveText('60 / 120 coins · Not enough coins');expect((await save(page)).coins).toBe(60);
 await page.getByLabel('Review state').selectOption('max');await expect(page.locator('.max-label')).toHaveText('MAX');await expect(page.locator('.current-facts')).toContainText('8');await expect(levelButton(page)).toHaveCount(0);await expect(page.getByLabel('Final chef stats')).toContainText('1.84×');await expect(page.getByRole('button',{name:'Unassign',exact:true})).toBeEnabled();
 await page.getByLabel('Review state').selectOption('near-max');await levelButton(page).dblclick();expect((await save(page)).staff[0].level).toBe(8);expect((await save(page)).coins).toBe(820);await expect(page.locator('.max-label')).toHaveText('MAX');
});

test('unassign preserves development; placing again opens idle recipes; explicit Prepare starts work',async({page})=>{
 await ready(page);await levelButton(page).click();await page.getByRole('button',{name:'Unassign',exact:true}).click();let c=(await save(page)).staff[0];expect(c.level).toBe(3);expect(c.assigned).toBe(false);expect(c.cell).toBeNull();await expect(page.getByRole('dialog')).toContainText('Unassigned staff');
 await page.getByRole('tab',{name:'Recipes',exact:true}).click();await expect(page.getByRole('button',{name:'Prepare',exact:true})).toHaveCount(0);await page.getByRole('button',{name:'Close recipes'}).click();await page.getByRole('button',{name:/Open Lena’s recipes/}).click();await expect(page.getByRole('heading',{name:'Lena’s recipes'})).toBeVisible();await page.getByRole('tab',{name:'Manage',exact:true}).click();
 await page.getByRole('button',{name:'Place in restaurant'}).click();await expect(page.getByRole('button',{name:'Place chef beside belt, cell 13'})).toHaveCount(0);await page.getByRole('button',{name:'Place chef beside belt, cell 20'}).click();await expect(page.getByRole('heading',{name:'Choose a recipe'})).toBeVisible();c=(await save(page)).staff[0];expect(c.level).toBe(3);expect(c.ceiling).toBe(8);expect(c.growthRate).toBe(.12);expect(c.recipe).toBeNull();
 await page.getByRole('button',{name:/Inspect Tamago/}).click();await expect(page.locator('.wr-detail-copy')).toContainText('4.5 sec');await page.getByRole('button',{name:'Prepare',exact:true}).click();expect((await save(page)).staff[0].recipe).toBe('tamago');expect((await save(page)).coins).toBe(1120);await page.reload();expect((await save(page)).staff[0].cell).toBe(20);
});

for(const state of ['develop','unassigned'])test(`named firing can cancel or remove permanently (${state})`,async({page})=>{
 await ready(page,state);const before=await save(page);await page.getByRole('button',{name:'Fire…'}).click();await expect(page.getByRole('heading',{name:'Fire Lena?'})).toBeVisible();await expect(page.getByRole('dialog')).toContainText('Lena Brooks');await expect(page.getByRole('dialog')).not.toContainText('refund');await page.getByRole('button',{name:'Cancel',exact:true}).click();expect(await save(page)).toEqual(before);await expect(page.getByRole('button',{name:'Fire…'})).toBeFocused();
 await page.getByRole('button',{name:'Fire…'}).click();await page.getByRole('button',{name:'Fire Lena',exact:true}).dblclick();expect((await save(page)).staff.map(c=>c.id)).toEqual(['omar','mateo']);expect((await save(page)).coins).toBe(before.coins);await page.reload();await expect(page.getByRole('button',{name:/Open Lena/})).toHaveCount(0);await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:/Open Omar/})).toBeVisible();
});

test('Escape, focus trap, and return to Edit keep categories and Live usable',async({page})=>{
 await ready(page);await page.getByRole('button',{name:'Fire…'}).focus();await page.keyboard.press('Tab');await expect(page.getByRole('tab',{name:'Manage',exact:true})).toBeFocused();await page.getByRole('button',{name:'Fire…'}).click();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Fire…'})).toBeFocused();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'People',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Layout',exact:true}).click();await expect(page.getByRole('button',{name:'Layout',exact:true})).toHaveAttribute('aria-pressed','true');await page.getByRole('button',{name:'Back to People'}).click();await page.getByRole('button',{name:'Live',exact:true}).click();await expect(page.locator('.scene')).toHaveAttribute('data-mode','live');await expect(page.getByRole('button',{name:'Staff',exact:true})).toHaveCount(0);
});

test('direction owned touch placement, invalid drop and cancellation preserve progression',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const page=await context.newPage();await page.goto((process.env.TEST_URL||'http://127.0.0.1:4175')+url+'?state=people');await page.locator('.staff-photo').first().waitFor();const cdp=await context.newCDPSession(page);
 async function touch(to,cancel=false){const b=await page.getByRole('button',{name:/Open Omar/}).boundingBox(),from={x:b.x+b.width/2,y:b.y+b.height/2};await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[from]});for(let i=1;i<=10;i++)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:from.x+(to.x-from.x)*i/10,y:from.y+(to.y-from.y)*i/10}]});await cdp.send('Input.dispatchTouchEvent',{type:cancel?'touchCancel':'touchEnd',touchPoints:[]});}
 const before=await save(page);await touch({x:190,y:150});expect(await save(page)).toEqual(before);const b=await page.locator('.world-cell').nth(20).boundingBox(),target={x:b.x+b.width/2,y:b.y+b.height/2};await touch(target,true);expect(await save(page)).toEqual(before);await touch(target);expect((await save(page)).staff[1].assigned).toBe(true);await expect(page.getByRole('heading',{name:'Omar’s recipes'})).toBeVisible();await expect(page.getByRole('button',{name:'Prepare',exact:true})).toBeDisabled();await context.close();
});

for(const [width,height] of [[320,720],[390,844],[1440,1000],[844,390]])test(`rendered states fit ${width}×${height}`,async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await ready(page,'develop',{width,height});
 for(const state of ['develop','poor','max','fire','recipes','gallery']){
  await page.getByLabel('Review state').selectOption(state);await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(200);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);const scene=await page.locator('.scene').boundingBox();expect(scene.x).toBeGreaterThanOrEqual(0);expect(scene.y+scene.height).toBeLessThanOrEqual(height+1);expect(scene.x+scene.width).toBeLessThanOrEqual(width+1);
  for(const b of await page.locator('.chef-popup button,.dismissal-sheet button').evaluateAll(es=>es.filter(e=>e.getClientRects().length&&!e.closest('[inert]')).map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})))){expect(b.height).toBeGreaterThanOrEqual(43.9);expect(b.width).toBeGreaterThanOrEqual(43.9);}
  if(state==='develop'){
   await expect(page.getByText('Unlocks Yellow recipes',{exact:true})).toBeInViewport();
   const portrait=await page.locator('.chef-popup>.development-portrait').boundingBox(),separator=await page.locator('.chef-header-separator').boundingBox();
   expect(Math.abs(portrait.y+portrait.height-separator.y)).toBeLessThan(.6);
   const visibleAtBottom=await page.locator('.chef-popup>.development-portrait').evaluate(el=>{const img=el.querySelector('img'),b=el.getBoundingClientRect(),r=img.getBoundingClientRect(),canvas=document.createElement('canvas');canvas.width=Math.ceil(r.width);canvas.height=Math.ceil(r.height);const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0,r.width,r.height);const row=ctx.getImageData(0,Math.floor(b.bottom-r.top-1),canvas.width,1).data;return [...row].filter((a,i)=>i%4===3&&a>128).length;});
   expect(visibleAtBottom).toBeGreaterThan(8);
  }
  if(state!=='gallery'){const panel=await page.getByRole('dialog').boundingBox();expect(panel.y).toBeGreaterThanOrEqual(scene.y);expect(panel.y+panel.height).toBeLessThanOrEqual(scene.y+scene.height+1);}
  await expect.poll(()=>page.locator('img').evaluateAll(es=>es.filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.src)),{timeout:15000}).toEqual([]);
  await page.screenshot({path:`prototypes/sushi-loop/review/17/header-separator/${state}-${width}x${height}.png`});
 }
 expect(errors).toEqual([]);
});

for(const [width,height] of [[320,720],[1440,1000]])test(`Shared uses the same pressed, disabled, MAX and confirmation panels ${width}×${height}`,async({page})=>{
 await ready(page,'gallery',{width,height});for(const state of ['pressed','disabled','max','confirmation','fired']){
  await page.locator('.gallery-switches button').filter({hasText:state==='max'?'MAX':state}).click();
  if(state==='disabled')await expect(levelButton(page)).toBeDisabled();
  if(state==='max'){await expect(page.locator('.max-label')).toBeVisible();await expect(levelButton(page)).toHaveCount(0);}
  if(state==='fired')await expect(page.locator('.fired-imprint')).toHaveCSS('opacity','0.94');
  if(state==='confirmation')await expect(page.getByRole('region',{name:'Dismissal confirmation sample'})).toContainText('Lena Brooks');
  await page.screenshot({path:`prototypes/sushi-loop/review/17/header-separator/shared-${state}-${width}x${height}.png`});
 }
});

test('tabs replace header facts, slide in both directions without remounting, and preserve recipe inspection',async({page})=>{
 await ready(page,'recipes');await expect(page.getByRole('tab',{name:'Recipes',exact:true})).toHaveAttribute('aria-selected','true');await expect(page.locator('.chef-popup-header')).not.toContainText('Level');await expect(page.getByRole('button',{name:/Manage chef/})).toHaveCount(0);
 await page.getByRole('button',{name:/Inspect Eel roll/}).click();const scroll=await page.locator('.wr-catalog').evaluate(e=>e.scrollTop);const before=await save(page),shell=await page.locator('.chef-popup').boundingBox();
 await page.getByRole('tab',{name:'Manage',exact:true}).click();await page.waitForTimeout(50);let x=await page.locator('.chef-page-track').evaluate(e=>new DOMMatrix(getComputedStyle(e).transform).m41);expect(x).toBeLessThan(0);expect(x).toBeGreaterThan(-shell.width);await expect(page.getByRole('tabpanel',{name:'Manage'})).toBeVisible();
 await page.getByRole('tab',{name:'Recipes',exact:true}).click();await page.waitForTimeout(300);x=await page.locator('.chef-page-track').evaluate(e=>new DOMMatrix(getComputedStyle(e).transform).m41);expect(x).toBe(0);await expect(page.locator('.wr-detail-copy h3')).toHaveText('Eel roll');expect(await page.locator('.wr-catalog').evaluate(e=>e.scrollTop)).toBe(scroll);expect(await save(page)).toEqual(before);
 await page.getByRole('tab',{name:'Recipes',exact:true}).focus();await page.keyboard.press('ArrowRight');await expect(page.getByRole('tab',{name:'Manage',exact:true})).toBeFocused();await expect(page.getByRole('tab',{name:'Manage',exact:true})).toHaveAttribute('aria-selected','true');await page.waitForTimeout(300);await expect(page.locator('.manage-page .development-interior')).toHaveCSS('background-color','rgba(0, 0, 0, 0)');await expect(page.locator('.manage-page .development-actions')).toHaveCSS('background-color','rgba(0, 0, 0, 0)');
});

test('firing slides up the same chef application, lands a persistent Fired stamp, and never shows a toast',async({page})=>{
 await ready(page);const before=await save(page);await page.getByRole('button',{name:'Fire…'}).click();await expect(page.locator('.dismissal-paper h2')).toHaveText('Lena Brooks');await expect(page.locator('.dismissal-paper .chef-portrait')).toHaveAttribute('aria-label',/Lena Brooks/);await page.waitForTimeout(380);await page.screenshot({path:'prototypes/sushi-loop/review/17/header-separator/fire-application-390x844.png'});
 await page.getByRole('button',{name:'Fire Lena',exact:true}).dblclick();expect((await save(page)).staff.map(c=>c.id)).toEqual(['omar','mateo']);expect((await save(page)).coins).toBe(before.coins);await expect(page.locator('.notice')).not.toHaveClass(/visible/);
 await page.locator('.dismissal-sheet').evaluate(el=>el.getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=363;}));await expect(page.locator('.firing-rubber-stamp')).toHaveCSS('opacity','1');await page.screenshot({path:'prototypes/sushi-loop/review/17/header-separator/stamp-contact-390x844.png'});
 await page.locator('.dismissal-sheet').evaluate(el=>el.getAnimations({subtree:true}).forEach(a=>{a.currentTime=1100;a.play();}));await page.waitForTimeout(100);await expect(page.locator('.fired-imprint')).toHaveCSS('opacity','0.94');await expect(page.locator('.firing-rubber-stamp')).toHaveCSS('opacity','0');await expect(page.getByRole('dialog',{name:'Lena Brooks fired'})).toBeVisible();await page.screenshot({path:'prototypes/sushi-loop/review/17/header-separator/fired-390x844.png'});await page.waitForTimeout(800);await expect(page.locator('.fired-imprint')).toBeVisible();await page.getByRole('button',{name:'Close',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.reload();expect((await save(page)).staff.map(c=>c.id)).toEqual(['omar','mateo']);
});

test('reduced motion switches tabs immediately and fades the Fired imprint without a moving stamp',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await ready(page,'recipes');await page.getByRole('tab',{name:'Manage',exact:true}).click();await expect(page.locator('.chef-page-track')).toHaveCSS('transition-duration','0s');await page.getByRole('button',{name:'Fire…'}).click();await page.getByRole('button',{name:'Fire Lena',exact:true}).click();await page.waitForTimeout(250);await expect(page.locator('.firing-rubber-stamp')).toHaveCSS('display','none');await expect(page.locator('.fired-imprint')).toHaveCSS('opacity','0.94');await expect(page.locator('.notice')).not.toHaveClass(/visible/);await page.keyboard.press('Escape');expect((await save(page)).staff).toHaveLength(2);
});
