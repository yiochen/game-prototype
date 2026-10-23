import {test,expect} from '@playwright/test';
const url='/prototypes/sushi-loop/design/editor-dock-preview/';
const ready=async page=>{await page.waitForSelector('html[data-ready=true]');await page.evaluate(()=>document.fonts.ready);};
async function drag(page,from,to){await page.mouse.move(from.x,from.y);await page.mouse.down();await page.mouse.move(to.x,to.y,{steps:8});}
const center=box=>({x:box.x+box.width/2,y:box.y+box.height/2});

test('wood assembly preserves tabs, badge counts, scroll reachability and separate Shop navigation',async({page})=>{
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.setViewportSize({width:390,height:844});await page.goto(url);await ready(page);
  await expect(page.getByRole('tab')).toHaveCount(3);
  await expect(page.getByRole('tab',{name:'Layout',exact:true})).toHaveAttribute('aria-selected','true');
  await expect(page.locator('.quantity')).toHaveText(['5','1','2','2','2']);
  await expect(page.locator('.inventory-item').last()).toHaveClass(/is-partial/);
  await page.locator('.inventory').hover();await page.mouse.wheel(0,200);
  await expect.poll(()=>page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBeGreaterThan(20);
  await expect(page.locator('[data-item=barrel]')).not.toHaveClass(/is-partial/);
  await expect(page.locator('.inventory [aria-pressed=true]')).toHaveCount(0);
  const offset=await page.locator('.inventory').evaluate(el=>el.scrollLeft);
  await page.getByRole('button',{name:'Shop',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading',{name:'Shop',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Back',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeHidden();
  expect(await page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBe(offset);
  await expect(page.getByRole('tab',{name:'Layout',exact:true})).toHaveAttribute('aria-selected','true');
  expect(errors).toEqual([]);
});

test('direction locking prevents horizontal browsing from turning into pickup',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto(url);await ready(page);
  const box=await page.locator('[data-item=stool]').boundingBox();const from=center(box);
  await drag(page,from,{x:from.x-45,y:from.y-2});
  await page.mouse.move(from.x-45,from.y-100,{steps:8});
  await expect(page.locator('.drag-ghost')).toHaveCount(0);
  await page.mouse.up();
  await expect(page.locator('.inventory [aria-pressed=true]')).toHaveCount(0);
  await expect.poll(()=>page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBeGreaterThan(20);
  await page.locator('.inventory').evaluate(el=>el.scrollLeft=0);
  const next=center(await page.locator('[data-item=stool]').boundingBox());
  await drag(page,next,{x:next.x+2,y:next.y-45});
  await expect(page.locator('.drag-ghost')).toHaveCount(1);
  const lockedOffset=await page.locator('.inventory').evaluate(el=>el.scrollLeft);
  await page.mouse.move(next.x+100,next.y-100,{steps:8});
  expect(await page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBe(lockedOffset);
  await page.mouse.up();await expect(page.locator('.drag-ghost')).toHaveCount(0);
  await expect(page.locator('.quantity')).toHaveText(['5','1','2','2','2']);
});

test('keyboard reveals the last item; unavailable fixtures stay unavailable',async({page})=>{
  await page.goto(url);await ready(page);
  await page.locator('[data-item=belt]').focus();await page.keyboard.press('End');
  await expect(page.locator('[data-item=barrel]')).toBeFocused();
  await expect(page.locator('[data-item=barrel]')).not.toHaveClass(/is-partial/);
  await page.keyboard.press('Enter');await expect(page.locator('[data-item=barrel]')).toHaveAttribute('aria-pressed','true');
  await page.keyboard.press('Escape');await expect(page.locator('.inventory [aria-pressed=true]')).toHaveCount(0);
  await page.getByRole('tab',{name:'People',exact:true}).click();await expect(page.locator('.inventory-item')).toHaveCount(3);
  const peopleStatus=await page.locator('.item-status').last().boundingBox();
  const peopleStrip=await page.locator('.inventory').boundingBox();
  expect(peopleStatus.y+peopleStatus.height).toBeLessThanOrEqual(peopleStrip.y+peopleStrip.height);
  await page.getByRole('tab',{name:'Floor',exact:true}).click();await expect(page.locator('.inventory-item')).toHaveCount(1);
  await expect(page.locator('.inventory-item')).toHaveAttribute('aria-disabled','true');
  const floorStatus=await page.locator('.item-status').boundingBox();
  const floorStrip=await page.locator('.inventory').boundingBox();
  expect(floorStatus.y+floorStatus.height).toBeLessThanOrEqual(floorStrip.y+floorStrip.height);
  await page.goto(url+'?state=out-of-stock');await ready(page);
  await expect(page.locator('.quantity')).toHaveText(['0','0','0','0','0']);
  const from=center(await page.locator('[data-item=belt]').boundingBox());await drag(page,from,{x:from.x,y:from.y-60});
  await expect(page.locator('.drag-ghost')).toHaveCount(0);await page.mouse.up();
});

test('touch scrolling uses the native horizontal pan without arming an item',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  const page=await context.newPage();await page.goto((process.env.TEST_URL||'http://127.0.0.1:4175')+url);await ready(page);
  const strip=await page.locator('.inventory').boundingBox();const x=strip.x+strip.width*.65,y=strip.y+strip.height*.5;
  const client=await context.newCDPSession(page);
  await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
  for(let step=1;step<=10;step++){
    await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-step*10,y:y-1}]});
    await page.waitForTimeout(16);
  }
  await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  await expect.poll(()=>page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBeGreaterThan(20);
  await expect(page.locator('.drag-ghost')).toHaveCount(0);
  await expect(page.locator('.inventory [aria-pressed=true]')).toHaveCount(0);
  await context.close();
});

for(const viewport of [{width:320,height:720},{width:984,height:1224},{width:1280,height:720}]){
  test(`dock containment and safe footer at ${viewport.width}x${viewport.height}`,async({page})=>{
    await page.setViewportSize(viewport);await page.goto(url);await ready(page);
    const frame=await page.locator('.scene').boundingBox();const dock=await page.locator('.dock').boundingBox();
    expect(dock.y+dock.height).toBeCloseTo(viewport.height,0);
    if(viewport.width>viewport.height)expect(frame.width).toBeLessThan(500);
    await expect(page.getByLabel('7680 coins',{exact:true})).toBeVisible();
    for(const control of await page.locator('.hud-mode').all()){
      const box=await control.boundingBox();
      expect(box.height).toBeGreaterThanOrEqual(44);
      expect(box.x).toBeGreaterThanOrEqual(frame.x);
      expect(box.x+box.width).toBeLessThanOrEqual(frame.x+frame.width);
    }
    for(const control of await page.locator('.category-navigation button').all()){
      const box=await control.boundingBox();expect(box.width).toBeGreaterThanOrEqual(44);expect(box.height).toBeGreaterThanOrEqual(44);
      expect(box.x).toBeGreaterThanOrEqual(frame.x-1);expect(box.x+box.width).toBeLessThanOrEqual(frame.x+frame.width+1);
      const icon=await control.locator('.icon').boundingBox();const caption=await control.locator('span').last().boundingBox();
      expect(icon.x-box.x).toBeGreaterThanOrEqual(8);
      expect(box.x+box.width-caption.x-caption.width).toBeGreaterThanOrEqual(8);
    }
    const shopFace=await page.locator('.shop-action .surface').boundingBox();
    const floorFace=await page.locator('#tab-floor .surface').boundingBox();
    expect(shopFace.height).toBeCloseTo(floorFace.height,2);
    expect(shopFace.y).toBeCloseTo(floorFace.y,2);
    const name=await page.locator('[data-item=crate] .item-name').boundingBox();
    const strip=await page.locator('.inventory').boundingBox();
    expect(name.y+name.height).toBeLessThan(strip.y+strip.height);
    expect(strip.x).toBeGreaterThan(frame.x+4);
    expect(strip.x+strip.width).toBeLessThan(frame.x+frame.width-4);
    expect(await page.evaluate(({x,y})=>!document.elementFromPoint(x,y)?.closest('.inventory-item'),
      {x:strip.x+strip.width+2,y:strip.y+strip.height/2})).toBe(true);
    const waves=await page.locator('.dock .wave-window').boundingBox();
    expect(waves.x).toBeGreaterThan(frame.x+8);
    expect(waves.x+waves.width).toBeLessThan(frame.x+frame.width-8);
    expect(waves.y).toBeGreaterThan(name.y+name.height);
    expect(waves.y+waves.height).toBeLessThan(viewport.height);
    const broken=await page.locator('img').evaluateAll(images=>images.filter(img=>!img.complete||img.naturalWidth===0).map(img=>img.src));
    expect(broken).toEqual([]);
  });
}


test('HTML HUD mode preview restores the editor without changing inventory',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto(url);await ready(page);
  await page.locator('.inventory').hover();await page.mouse.wheel(0,120);
  const offset=await page.locator('.inventory').evaluate(el=>el.scrollLeft);
  await page.getByRole('button',{name:'Live',exact:true}).click();
  await expect(page.locator('.dock')).toBeHidden();
  await expect(page.getByRole('button',{name:'Live',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.getByRole('button',{name:'Editing',exact:true}).click();
  await expect(page.locator('.dock')).toBeVisible();
  expect(await page.locator('.inventory').evaluate(el=>el.scrollLeft)).toBe(offset);
  await expect(page.locator('.quantity')).toHaveText(['5','1','2','2','2']);
  await page.getByRole('button',{name:'Live',exact:true}).click();await page.keyboard.press('Escape');
  await expect(page.locator('.dock')).toBeVisible();
});

test('UI surfaces use only the wood-grain and wave bitmap backgrounds',async({page})=>{
  await page.goto(url);await ready(page);
  const images=await page.evaluate(()=>{
    const urls=new Set();
    for(const el of document.querySelectorAll('.scene,.scene *')){
      for(const pseudo of [null,'::before','::after']){
        const style=getComputedStyle(el,pseudo);
        for(const match of style.backgroundImage.matchAll(/url\(["']?(.*?)["']?\)/g))urls.add(new URL(match[1],location.href).pathname.split('/').pop());
        if(style.borderImageSource!=='none')throw new Error('Baked border image on '+el.className);
      }
    }
    return [...urls].map(name=>name.replace(/^(waves|wood-grain)(?:-[A-Za-z0-9_-]+)?\.png$/,'$1.png')).sort();
  });
  expect(images).toEqual(['waves.png','wood-grain.png']);
  await expect(page.locator('.hud img,.category-navigation img,.quantity img,.shop-view img')).toHaveCount(0);
});
