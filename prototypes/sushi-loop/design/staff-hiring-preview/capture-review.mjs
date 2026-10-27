import {chromium} from '@playwright/test';
import {fileURLToPath} from 'node:url';
const browser=await chromium.launch();
const out=fileURLToPath(new URL('../../review/16/hired-stamp/',import.meta.url));
const base=process.env.TEST_URL||'http://127.0.0.1:4176';
for(const [width,height,label] of [[320,720,'phone'],[1440,1000,'wide']]){
 const page=await browser.newPage({viewport:{width,height}});await page.goto(base+'/prototypes/sushi-loop/design/staff-hiring-preview/');await page.evaluate(()=>document.fonts.ready);
 const state=async key=>{await page.getByLabel('Review state').selectOption(key);await page.waitForTimeout(420);};const snap=async name=>page.screenshot({path:`${out}/${label}-${name}.png`});
 await state('available');await snap('01-applicants');await page.getByRole('button',{name:'Hire Ama Mensah for 180 coins'}).hover();await page.mouse.down();await snap('02-pressed-hire');await page.mouse.up();await snap('03-hired-remaining');await page.getByRole('button',{name:'Close applicants',exact:true}).click();await page.getByRole('dialog').waitFor({state:'detached'});await snap('04-roster-new-chef');
 await page.getByRole('button',{name:/Inspect Ama Mensah, unassigned/}).click();await page.waitForTimeout(200);await snap('05-chef-detail');await page.getByRole('button',{name:'Place in restaurant'}).click();await snap('06-placement');await page.getByRole('button',{name:'Place Ama beside belt, cell 20',exact:true}).click();await page.waitForTimeout(420);await snap('07-idle-picker');await page.getByRole('button',{name:'Close recipes'}).click();
 await state('full');await snap('08-capacity-full');await state('poor');await snap('09-unaffordable');await state('available');await page.locator('.application-fan').focus();await page.keyboard.press('ArrowRight');await page.waitForTimeout(650);await snap('10-mateo');await page.locator('.application-fan').focus();await page.keyboard.press('ArrowRight');await page.waitForTimeout(650);await snap('11-noor');await page.getByRole('button',{name:'Refresh applications'}).click();await snap('12-cooldown');await state('empty');await snap('13-empty');await state('people');await snap('14-people');await state('gallery');await snap('15-shared-top');await page.locator('.shared-gallery').evaluate(e=>e.scrollTop=560);await snap('16-shared-states');await page.locator('.shared-gallery').evaluate(e=>e.scrollTop=e.scrollHeight);await snap('17-shared-tiers');await page.close();
}
await browser.close();
