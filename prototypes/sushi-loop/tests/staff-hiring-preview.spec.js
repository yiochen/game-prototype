import {test,expect} from '@playwright/test';
const url='/prototypes/sushi-loop/design/staff-hiring-preview/';
const storageKey='sushi-loop-issue16-ui-review-v1';
async function ready(page,state='available'){
 await page.setViewportSize({width:390,height:844});await page.goto(url+`?state=${state}`);await page.locator('.scene').waitFor();await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(200);
}
const save=page=>page.evaluate(key=>JSON.parse(localStorage.getItem(key)),storageKey);
async function browse(page,direction){await page.locator('.application-fan').focus();await page.keyboard.press(direction>0?'ArrowRight':'ArrowLeft');await page.waitForTimeout(650);}
const center=b=>({x:b.x+b.width/2,y:b.y+b.height/2});
async function drag(page,locator,to){const from=center(await locator.boundingBox());await page.mouse.move(from.x,from.y);await page.mouse.down();await page.mouse.move(from.x,from.y-20,{steps:4});await page.mouse.move(to.x,to.y,{steps:10});}

test('browsing never hires; hiring pays once, preserves remaining offers and disables at capacity',async({page})=>{
 await ready(page);await browse(page,1);await expect(page.getByRole('heading',{name:'Mateo Rivera'})).toBeVisible();expect((await save(page)).coins).toBe(1240);
 await browse(page,1);await expect(page.getByRole('heading',{name:'Noor Haddad'})).toBeVisible();await browse(page,-1);
 await page.getByRole('button',{name:'Hire Mateo Rivera for 90 coins'}).dblclick();await expect(page.getByRole('dialog')).toBeVisible();let s=await save(page);expect(s.coins).toBe(1150);expect(s.staff.map(c=>c.id)).toEqual(['lena','omar','mateo']);expect(s.pool).toEqual(['ama','noor']);
 await page.getByRole('button',{name:'Hire Noor Haddad for 360 coins'}).click();s=await save(page);expect(s.coins).toBe(790);expect(s.staff).toHaveLength(4);expect(s.pool).toEqual(['ama']);await expect(page.getByRole('button',{name:'Hire Ama Mensah for 180 coins, roster full'})).toBeDisabled();await expect(page.locator('.roster-full')).toHaveCSS('color','rgb(184, 68, 50)');await expect(page.locator('.panel-header')).toContainText('Staff 4 / 4');
 await page.reload();await expect(page.locator('.panel-header')).toContainText('Staff 4 / 4');expect((await save(page)).coins).toBe(790);
});

test('refresh replaces with three, costs nothing and retains its deadline while closed and across reload',async({page})=>{
 await page.clock.install({time:new Date('2026-10-26T15:00:00Z')});await ready(page);
 await page.getByRole('button',{name:'Refresh applications'}).click();let s=await save(page);expect(s.pool).toEqual(['dalia','ellis','rowan']);expect(s.coins).toBe(1240);const deadline=s.deadline;
 await expect(page.getByRole('button',{name:'Refresh applications'})).toBeDisabled();await page.getByRole('button',{name:'Close applicants',exact:true}).click();await page.clock.fastForward(120000);await page.getByRole('button',{name:'Applicants',exact:true}).click();await expect(page.locator('.refresh-row')).toContainText('03:00');
 await page.reload();expect((await save(page)).deadline).toBe(deadline);await expect(page.getByRole('button',{name:'Refresh applications'})).toBeDisabled();await page.clock.fastForward(180001);await expect(page.getByRole('button',{name:'Refresh applications'})).toBeEnabled();expect((await save(page)).pool).toEqual(['dalia','ellis','rowan']);await expect(page.locator('.application-fan')).toHaveAttribute('data-active-applicant','dalia');await page.getByRole('button',{name:'Refresh applications'}).click();expect((await save(page)).pool).toHaveLength(3);
});

test('details and applicants restore People mode, tray scroll and focus; disabled hire retains facts',async({page})=>{
 await ready(page,'people');await page.getByRole('button',{name:'Inspect Omar Haddad, unassigned'}).click();await expect(page.getByRole('dialog')).toContainText('Unassigned staff');await page.keyboard.press('Escape');await expect(page.locator('.scene')).toHaveAttribute('data-mode','edit');await expect(page.getByRole('button',{name:'Inspect Omar Haddad, unassigned'})).toBeFocused();
 await page.getByRole('button',{name:'Applicants',exact:true}).click();await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Applicants',exact:true})).toBeFocused();await expect(page.getByRole('region',{name:'People inventory'})).toBeVisible();
 await page.getByLabel('Review state').selectOption('poor');await expect(page.getByRole('button',{name:'Hire Ama Mensah for 180 coins, 60 coins available'})).toBeDisabled();await expect(page.locator('.hire-reason')).toHaveCount(0);await expect(page.locator('.is-active .hire-budget')).toHaveText('★60/180');await expect(page.locator('.is-active .required-coins')).toHaveCSS('color','rgb(184, 68, 50)');await expect(page.locator('.panel-header')).toContainText('2 / 4');await expect(page.locator('.is-active .hire')).toContainText('180');
});

test('invalid/cancelled drops preserve staff; valid drag opens idle picker and only Prepare begins cooking',async({page})=>{
 await ready(page,'roster');const omar=page.getByRole('button',{name:'Inspect Omar Haddad, unassigned'});const before=await save(page);
 await drag(page,omar,{x:180,y:100});await page.mouse.up();expect((await save(page)).staff).toEqual(before.staff);
 const target=center(await page.locator('.world-cell').nth(20).boundingBox());await drag(page,omar,target);await page.keyboard.press('Escape');await page.mouse.up();expect((await save(page)).staff).toEqual(before.staff);
 await drag(page,omar,target);await page.mouse.up();await expect(page.getByRole('dialog')).toBeVisible();await expect(page.getByRole('heading',{name:'Choose a recipe'})).toBeVisible();await expect(page.getByRole('button',{name:'Prepare',exact:true})).toBeDisabled();let c=(await save(page)).staff.find(c=>c.id==='omar');expect(c.assigned).toBe(true);expect(c.cell).toBe(20);expect(c.recipe).toBeNull();
 await page.getByRole('button',{name:'Close recipes'}).click();c=(await save(page)).staff.find(c=>c.id==='omar');expect(c.recipe).toBeNull();await page.getByRole('button',{name:'Omar, idle',exact:true}).click();await page.getByRole('button',{name:/Inspect Cucumber maki/}).click();await expect(page.getByRole('button',{name:'Prepare',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Prepare',exact:true}).click();expect((await save(page)).staff.find(c=>c.id==='omar').recipe).toBe('cucumber');await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('touch swipe only browses; keyboard remains trapped in modal',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const page=await context.newPage();await page.goto((process.env.TEST_URL||'http://127.0.0.1:4175')+url);await page.locator('.fan-card.is-active .resume-paper').waitFor();const client=await context.newCDPSession(page);const bounds=await page.locator('.fan-card.is-active .resume-heading').boundingBox();const x=bounds.x+bounds.width*.8,y=bounds.y+bounds.height*.6;
 await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});for(let i=1;i<=8;i++)await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-i*14,y}]});await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await expect(page.getByRole('heading',{name:'Mateo Rivera'})).toBeVisible();expect((await save(page)).staff).toHaveLength(2);
 const last=page.getByRole('button',{name:'Refresh applications'});await last.focus();await page.keyboard.press('Tab');await expect(page.getByRole('button',{name:'Close applicants',exact:true})).toBeFocused();await context.close();
});

for(const [width,height] of [[320,720],[390,844],[1440,1000],[844,390]])test(`review composition and controls fit ${width}×${height}`,async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.setViewportSize({width,height});await page.goto(url);await page.locator('.fan-card.is-active .resume-paper').waitFor();await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(200);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBe(width);const scene=await page.locator('.scene').boundingBox();expect(scene.x).toBeGreaterThanOrEqual(0);expect(scene.x+scene.width).toBeLessThanOrEqual(width+1);
 for(const selector of ['.is-active .hire','.refresh','.panel-header .round'])for(const box of await page.locator(selector).evaluateAll(es=>es.map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})))){expect(box.height).toBeGreaterThanOrEqual(44);expect(box.width).toBeGreaterThanOrEqual(44);}
 const hire=await page.locator('.is-active .hire').boundingBox(),fan=await page.locator('.application-fan').boundingBox();expect(hire.y+hire.height).toBeLessThanOrEqual(fan.y+fan.height+1);expect(fan.x).toBeCloseTo(scene.x,0);expect(fan.width).toBeCloseTo(scene.width,0);await expect(page.locator('.browse')).toHaveCount(0);await expect(page.locator('.application-fan')).not.toContainText('Strength');await expect(page.locator('.application-fan')).not.toContainText('Highest reachable tier');await expect(page.locator('.application-fan')).not.toContainText('Starts at Level');await page.locator('.application-fan').evaluate(e=>e.scrollTop=50);expect(await page.locator('.application-fan').evaluate(e=>e.scrollTop)).toBe(0);
 await page.screenshot({path:`prototypes/sushi-loop/review/16/hired-stamp/applicants-${width}x${height}.png`});await page.getByRole('button',{name:'Close applicants',exact:true}).click();await page.screenshot({path:`prototypes/sushi-loop/review/16/hired-stamp/roster-${width}x${height}.png`});expect(errors).toEqual([]);
});

test('touch pickup places an unassigned chef and horizontal gestures retain the roster',async({browser})=>{
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const page=await context.newPage();await page.goto((process.env.TEST_URL||'http://127.0.0.1:4175')+url+'?state=full');await page.locator('.panel').waitFor();await page.getByRole('button',{name:'Close applicants',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);const client=await context.newCDPSession(page);const scroll=page.locator('.roster-scroll');const first=center(await page.getByRole('button',{name:'Inspect Omar Haddad, unassigned'}).boundingBox());
 async function touch(from,to){await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[from]});for(let i=1;i<=10;i++)await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:from.x+(to.x-from.x)*i/10,y:from.y+(to.y-from.y)*i/10}]});await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
 await touch(first,{x:first.x-90,y:first.y});expect(await scroll.evaluate(e=>e.scrollLeft)).toBeGreaterThan(50);expect((await save(page)).staff.filter(c=>c.assigned)).toHaveLength(1);
 await scroll.evaluate(e=>e.scrollLeft=0);const from=center(await page.getByRole('button',{name:'Inspect Omar Haddad, unassigned'}).boundingBox());const target=center(await page.locator('.world-cell').nth(20).boundingBox());await touch(from,target);await expect(page.getByRole('heading',{name:'Choose a recipe'})).toBeVisible();expect((await save(page)).staff.find(c=>c.id==='omar').cell).toBe(20);await context.close();
});

test('card fan tracks a drag, snaps, rebounds at edges and can be reversed while settling',async({page})=>{
 await ready(page);const fan=page.locator('.application-fan'),first=page.locator('.fan-card').first();
 const position=async()=>-Number(await first.evaluate(el=>el.style.getPropertyValue('--card-offset')));
 const box=await fan.boundingBox(),from={x:box.x+box.width*.55,y:box.y+120};
 await page.mouse.move(from.x,from.y);await page.mouse.down();await page.mouse.move(from.x-125,from.y,{steps:10});expect(await position()).toBeGreaterThan(.3);expect(await position()).toBeLessThan(.55);await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/drag-tracking.png'});await page.mouse.up();
 // Interrupt the spring at its visible value, then reverse direction.
 const before=await position();await page.mouse.down();expect(Math.abs((await position())-before)).toBeLessThan(.12);await page.mouse.move(from.x+100,from.y,{steps:10});await page.mouse.up();await expect(fan).toHaveAttribute('data-active-applicant','ama');await expect.poll(position).toBeCloseTo(0,2);expect((await save(page)).staff).toHaveLength(2);
 await page.mouse.move(from.x,from.y);await page.mouse.down();await page.mouse.move(from.x+130,from.y,{steps:10});expect(await position()).toBeLessThan(0);expect(await position()).toBeGreaterThan(-.18);await page.mouse.up();await expect.poll(position).toBeCloseTo(0,2);
 await browse(page,1);await expect(fan).toHaveAttribute('data-active-applicant','mateo');const cards=await page.locator('.fan-card').evaluateAll(es=>es.map(el=>({tilt:el.style.getPropertyValue('--card-tilt'),left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right})));expect(cards[0].left).toBeLessThan(box.x);expect(cards[0].right).toBeGreaterThan(box.x);expect(cards[2].left).toBeLessThan(box.x+box.width);expect(cards[2].right).toBeGreaterThan(box.x+box.width);expect(cards[0].tilt).not.toBe('0deg');expect(cards[2].tilt).not.toBe('0deg');await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/middle-card-neighbors.png'});
});

test('vertical and wheel gestures never scroll the application vertically; reduced motion snaps immediately',async({page})=>{
 await ready(page);const fan=page.locator('.application-fan'),b=await fan.boundingBox();await page.mouse.move(b.x+b.width/2,b.y+100);await page.mouse.down();await page.mouse.move(b.x+b.width/2,b.y+220,{steps:8});await page.mouse.up();await expect(fan).toHaveAttribute('data-active-applicant','ama');expect(await fan.evaluate(el=>el.scrollTop)).toBe(0);
 await fan.hover();await page.mouse.wheel(0,270);await expect(fan).toHaveAttribute('data-active-applicant','mateo');expect(await fan.evaluate(el=>el.scrollTop)).toBe(0);expect((await save(page)).coins).toBe(1240);
 await page.emulateMedia({reducedMotion:'reduce'});await fan.focus();await page.keyboard.press('ArrowRight');await expect(fan).toHaveAttribute('data-active-applicant','noor');expect(Math.abs(Number(await page.locator('.fan-card.is-active').evaluate(el=>el.style.getPropertyValue('--card-offset'))))).toBe(0);
});

test('hiring and explicit refresh retain outgoing paper until its exit completes',async({page})=>{
 await ready(page);await expect(page.locator('.is-active .application-card-visual')).toHaveAttribute('data-presence','settled');
 await page.getByRole('button',{name:'Refresh applications'}).click();await expect(page.locator('[data-applicant=ama] .application-card-visual')).toHaveAttribute('data-presence','exiting');await expect(page.locator('[data-applicant=dalia] .application-card-visual')).toHaveAttribute('data-presence','entering');await expect(page.locator('[data-applicant=ama]')).toHaveAttribute('aria-hidden','true');
 await expect(page.locator('.fan-card.is-exiting')).toHaveCount(0);await expect(page.locator('.is-active .application-card-visual')).toHaveAttribute('data-presence','settled');expect((await save(page)).pool).toEqual(['dalia','ellis','rowan']);
 await page.getByRole('button',{name:'Hire Dalia Farouk for 180 coins'}).click();await expect(page.locator('[data-applicant=dalia] .application-card-visual')).toHaveAttribute('data-presence','hiring');expect((await save(page)).staff.map(c=>c.id)).toContain('dalia');await expect(page.locator('[data-applicant=dalia]')).toHaveCount(0);

});

test('full and unaffordable statuses use header and button facts, with no above-Hire error row',async({page})=>{
 await ready(page,'full');await expect(page.locator('.roster-full')).toHaveText('Roster full');await expect(page.locator('.roster-full')).toHaveCSS('color','rgb(184, 68, 50)');await expect(page.locator('.hire-reason')).toHaveCount(0);await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/capacity-full.png'});
 await page.getByLabel('Review state').selectOption('poor');await expect(page.locator('.is-active .application-card-visual')).toHaveAttribute('data-presence','settled');await expect(page.locator('.hire-reason')).toHaveCount(0);await expect(page.locator('.is-active .current-coins')).toHaveText('60');await expect(page.locator('.is-active .required-coins')).toHaveText('180');await expect(page.locator('.is-active .required-coins')).toHaveCSS('color','rgb(184, 68, 50)');await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/unaffordable.png'});
});

test('hire expands paper, lands a Hired stamp, flies out and commits exactly once without a toast',async({page})=>{
 await ready(page);await expect(page.locator('.is-active .application-card-visual')).toHaveAttribute('data-presence','settled');await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).click();
 const hired=page.locator('[data-applicant=ama]');await expect(hired.locator('.application-card-visual')).toHaveAttribute('data-presence','hiring');expect((await save(page)).coins).toBe(1060);expect((await save(page)).staff.filter(c=>c.id==='ama')).toHaveLength(1);expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(true);await expect(page.locator('.notice')).not.toHaveClass(/visible/);
 await expect.poll(()=>hired.locator('.hired-imprint').evaluate(el=>Number(getComputedStyle(el).opacity))).toBeGreaterThan(.9);await expect(hired.locator('.hired-imprint')).toHaveText('Hired');const transform=await hired.locator('.application-card-visual').evaluate(el=>new DOMMatrixReadOnly(getComputedStyle(el).transform).a);expect(transform).toBeGreaterThan(1);await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/hired-confirmation.png'});await expect(hired).toHaveCount(0);expect((await save(page)).coins).toBe(1060);
 await page.getByRole('button',{name:'Close applicants'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.locator('[data-chef=ama] .new-chef-dot')).toBeVisible();await page.screenshot({path:'prototypes/sushi-loop/review/16/hired-stamp/inventory-new-dot.png'});
});

test('unseen chef dots persist behind applicants, across reloads and offscreen until their photos are seen',async({page})=>{
 await page.clock.install();await ready(page);await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).click();await expect(page.locator('[data-applicant=ama]')).toHaveCount(0);await page.getByRole('button',{name:'Hire Mateo Rivera for 90 coins'}).click();await expect(page.locator('[data-applicant=mateo]')).toHaveCount(0);
 await page.clock.fastForward(5000);expect((await save(page)).staff.filter(c=>c.isNew).map(c=>c.id)).toEqual(['ama','mateo']);await page.reload();expect((await save(page)).staff.filter(c=>c.isNew).map(c=>c.id)).toEqual(['ama','mateo']);
 await page.getByRole('button',{name:'Close applicants'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.locator('[data-chef=ama] .new-chef-dot')).toBeVisible();await page.waitForTimeout(100);await page.clock.fastForward(1600);await expect.poll(async()=> (await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(false);expect((await save(page)).staff.find(c=>c.id==='mateo').isNew).toBe(true);
 await page.locator('.roster-scroll').evaluate(el=>el.scrollLeft=el.scrollWidth);await page.waitForTimeout(100);await page.clock.fastForward(1600);await expect.poll(async()=> (await save(page)).staff.find(c=>c.id==='mateo').isNew).toBe(false);
});

test('opening details acknowledges a new chef immediately; closing mid-hire preserves the paid chef',async({page})=>{
 await ready(page);await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).click();await expect(page.locator('[data-applicant=ama] .hired-imprint')).toHaveCount(1);await page.getByRole('button',{name:'Close applicants'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);expect((await save(page)).coins).toBe(1060);expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(true);
 await page.getByRole('button',{name:'Inspect Ama Mensah, unassigned, new chef'}).click();expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(false);await page.keyboard.press('Escape');await expect(page.locator('[data-chef=ama] .new-chef-dot')).toHaveCount(0);
});

test('reduced motion keeps Hired confirmation without a falling prop or paper expansion',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await ready(page);await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).click();const hired=page.locator('[data-applicant=ama]');await expect(hired.locator('.application-card-visual')).toHaveAttribute('data-presence','hiring');await expect(hired.locator('.hire-rubber-stamp')).toBeHidden();await expect.poll(()=>hired.locator('.hired-imprint').evaluate(el=>Number(getComputedStyle(el).opacity))).toBeGreaterThan(.9);const frames=await hired.locator('.application-card-visual').evaluate(el=>el.getAnimations()[0].effect.getKeyframes());expect(frames.every(frame=>!frame.transform)).toBe(true);await expect(hired).toHaveCount(0);expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(true);
});

test('seeing time pauses while a new photo is covered or the page is hidden',async({page})=>{
 await page.clock.install();await ready(page);await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).click();await expect(page.locator('[data-applicant=ama]')).toHaveCount(0);await page.getByRole('button',{name:'Close applicants'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.waitForTimeout(100);await page.clock.fastForward(500);
 await page.getByRole('button',{name:'Applicants',exact:true}).click();await page.clock.fastForward(2000);expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(true);await page.getByRole('button',{name:'Close applicants'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.waitForTimeout(100);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'));});await page.clock.fastForward(3000);expect((await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(true);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'visible'});document.dispatchEvent(new Event('visibilitychange'));});await page.clock.fastForward(1500);await expect.poll(async()=> (await save(page)).staff.find(c=>c.id==='ama').isNew).toBe(false);
});

test('Shared components replay the same hire confirmation and show the new-chef indicator',async({page})=>{
 await ready(page);await page.getByLabel('Review state').selectOption('gallery');await page.getByRole('button',{name:'Play hire animation'}).click();await expect(page.locator('.hire-gallery-demo .application-card-visual')).toHaveAttribute('data-presence','hiring');await expect(page.locator('.hire-gallery-demo .hired-imprint')).toHaveText('Hired');await page.getByRole('button',{name:'Show new-chef dot'}).click();await expect(page.locator('.gallery-photos .new-chef-dot')).toHaveCount(1);
});
