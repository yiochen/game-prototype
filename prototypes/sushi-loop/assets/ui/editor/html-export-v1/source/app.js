const asset = name => new URL(`./assets/${name}.png`, import.meta.url).href;
const root = document.querySelector('.scene');
const initial = new URLSearchParams(location.search).get('state') || document.body.dataset.state || 'layout';
const stockless = initial === 'out-of-stock';
const goods = [
  {id:'belt',name:'Belt',art:'belt-straight-e',count:5},
  {id:'stool',name:'Stool',art:'stool-wood',count:1},
  {id:'plant',name:'Plant',art:'plant-angular',count:2},
  {id:'crate',name:'Crate',art:'crate-wood',count:2},
  {id:'barrel',name:'Barrel',art:'barrel-wood',count:2},
].map(item => ({...item,count:stockless?0:item.count}));
const people = [
  {id:'lena',name:'Lena',art:'chef-lena',status:'Placed'},
  {id:'omar',name:'Omar',art:'chef-omar',status:'Placed'},
  {id:'mina',name:'Mina',art:'chef-lena',status:'Placed'},
];
const floors = [{id:'floor',name:'Cream tile',art:'floor-cream',status:'Current',unavailable:true}];
// Simple profile and basket geometry follows the existing wireframe/common.jsx
// glyph family, with the solid furniture/grid treatment of the approved dock.
const glyphs = {
  people:'<circle cx="12" cy="6" r="4"/><path d="M3 22v-4a9 7 0 0 1 18 0v4Z"/>',
  layout:'<path d="M5 3h14l3 8H2ZM4 13h16l-1 8h-4l-1-5h-4l-1 5H5Z"/>',
  floor:'<rect x="2" y="2" width="9" height="9" rx="1.5"/><rect x="13" y="2" width="9" height="9" rx="1.5"/><rect x="2" y="13" width="9" height="9" rx="1.5"/><rect x="13" y="13" width="9" height="9" rx="1.5"/>',
  shop:'<path d="M3 9h18l-2 11H5L3 9M7 9l3-6M17 9l-3-6M9 12v5M15 12v5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
  'caret-left':'<path d="m15 5-7 7 7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
  star:'<path d="m12 2 3 6 6.6 1-4.8 4.7 1.1 6.6-5.9-3.1-5.9 3.1 1.1-6.6L2.4 9 9 8Z"/>',
  pencil:'<path d="m4 15-1 6 6-1L21 8l-5-5ZM14 5l5 5"/>',
  play:'<path d="M5 3v18l16-9Z"/>',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${glyphs[name]}</svg>`;
root.innerHTML = `
  <div class="world" aria-label="Restaurant scene reference" data-mocklens-ignore="This noninteractive restaurant floor illustration deliberately crops to fill the space above the HTML UI."><img class="world-sky" src="${asset('restaurant-sky')}" alt=""><div class="blue-wall"></div><img class="world-wall" src="${asset('restaurant-wall')}" alt=""><div class="world-floor"><img src="${asset('restaurant-floor')}" alt=""></div></div>
  <header class="hud" aria-label="Restaurant controls">
    <div class="hud-coins" aria-label="7680 coins"><span class="coin-art" aria-hidden="true">${icon('star')}</span><span>7680</span></div>
    <button class="hud-mode hud-editing" aria-pressed="true" data-mocklens-action="Return to the Editing presentation with the same category and inventory scroll. This HTML assembly does not run the game simulation."><span class="hud-surface" aria-hidden="true"></span>${icon('pencil')}<span>Editing</span></button>
    <button class="hud-mode hud-live" aria-pressed="false" data-mocklens-action="Show the read-only Live presentation with the inventory dock hidden. Editing or Escape restores the editor; no simulation or save changes occur."><span class="hud-surface" aria-hidden="true"></span>${icon('play')}<span>Live</span></button>
  </header>
  <section class="dock" aria-label="Restaurant editor">
    <div class="board" aria-hidden="true"></div>
    <div class="wave-window" aria-hidden="true"><div class="waves"></div></div>
    <nav class="category-navigation" aria-label="Editor categories and Shop">
      <div class="tabs" role="tablist" aria-label="Editing category">${['people','layout','floor'].map(key=>`<button class="tab" role="tab" id="tab-${key}" aria-controls="inventory" aria-selected="false" data-category="${key}" data-mocklens-action="Select ${key} to connect this category to the board and show its inventory. Left and right arrow keys switch categories."><span class="surface" aria-hidden="true"></span>${icon(key)}<span class="caption">${key[0].toUpperCase()+key.slice(1)}</span></button>`).join('')}</div>
      <button class="shop-action" aria-haspopup="dialog" data-mocklens-action="Open the separate Shop view. Back or Escape returns to the current category and scroll position."><span class="surface" aria-hidden="true"></span>${icon('shop')}<span>Shop</span></button>
    </nav>
    <div id="inventory" class="inventory" role="tabpanel" aria-label="Layout inventory" data-mocklens-ignore="This horizontal inventory viewport deliberately clips the fifth good as a scroll cue. All goods are reachable by scrolling, mouse wheel or keyboard focus."><div class="inventory-row"></div></div>
  </section>
  <section class="shop-view" role="dialog" aria-modal="true" aria-labelledby="shop-title" hidden>
    <header class="shop-header"><button class="back" data-mocklens-action="Return to the editor with the same selected category and scroll position.">${icon('caret-left')}<span>Back</span></button><h1 id="shop-title">Shop</h1></header>
    <div class="shop-message">${icon('shop')}<h2>Coming soon</h2><p>The Shop is not available yet.</p></div>
    <div class="wave-window" aria-hidden="true"><div class="waves"></div></div>
  </section>
  <p class="sr-only" role="status" aria-live="polite"></p>`;

const dock = root.querySelector('.dock');
const strip = root.querySelector('.inventory');
const row = root.querySelector('.inventory-row');
const tabs = [...root.querySelectorAll('.tab')];
const shop = root.querySelector('.shop-view');
const status = root.querySelector('[role=status]');
const positions = {};
let category = '';
let selected = '';
let gesture = null;
let ghost = null;

function available(item){return !item.unavailable && (item.count === undefined || item.count > 0);}
function selectItem(card){
  if(card.getAttribute('aria-disabled')==='true')return;
  selected = card.dataset.item;
  for(const item of row.children)item.setAttribute('aria-pressed',String(item===card));
  status.textContent=`${card.dataset.name} selected. Drag upward for a visual preview. Escape clears selection.`;
}
function showCategory(next){
  cancelGesture();
  if(category)positions[category]=strip.scrollLeft;
  category=next;
  selected='';
  tabs.forEach(tab=>{const active=tab.dataset.category===next;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
  strip.dataset.category=next;
  strip.setAttribute('aria-labelledby',`tab-${next}`);
  strip.setAttribute('aria-label',`${next[0].toUpperCase()+next.slice(1)} inventory`);
  const items=next==='people'?people:next==='floor'?floors:goods;
  row.innerHTML=items.map(item=>`<button class="inventory-item" data-item="${item.id}" data-name="${item.name}" data-art="${item.art}" aria-pressed="false" aria-disabled="${!available(item)}" aria-label="${item.name}${item.count===undefined?`, ${item.status}`:`, ${item.count} available`}" data-mocklens-action="Swipe sideways to browse. ${available(item)?'Drag upward to preview this item; release ends the visual preview. Tap or Enter selects it. Escape cancels.':'This item is unavailable for pickup; sideways browsing still works.'} Arrow keys focus and reveal neighboring items."><span class="item-preview"><img src="${asset(item.art)}" alt="" draggable="false">${item.count===undefined?'':`<span class="quantity" aria-hidden="true">${item.count}</span>`}</span><span class="item-name">${item.name}</span>${item.status?`<span class="item-status">${item.status}</span>`:''}</button>`).join('');
  strip.scrollLeft=positions[next]||0;
  requestAnimationFrame(()=>{updatePartialItems();updateWoodAlignment();});
}
function updatePartialItems(){
  const viewport=strip.getBoundingClientRect();
  for(const card of row.children){const bounds=card.getBoundingClientRect();card.classList.toggle('is-partial',bounds.left<viewport.left-1 || bounds.right>viewport.right+1);}
}
// The board and caps share a grain plane; their complete outlines are CSS.
function updateWoodAlignment(){
  const board = root.querySelector('.board').getBoundingClientRect();
  if(!board.width)return;
  for(const surface of root.querySelectorAll('.category-navigation .surface')){
    const bounds=surface.getBoundingClientRect();
    surface.style.setProperty('--wood-size',`${board.width}px auto`);
    surface.style.setProperty('--wood-position',`${board.left-bounds.left}px ${board.top-bounds.top}px`);
  }
}
new ResizeObserver(updateWoodAlignment).observe(dock);
strip.addEventListener('scroll',updatePartialItems,{passive:true});
new ResizeObserver(updatePartialItems).observe(strip);
tabs.forEach((tab,index)=>{
  tab.addEventListener('click',()=>showCategory(tab.dataset.category));
  tab.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();
    const target=event.key==='Home'?0:event.key==='End'?2:(index+(event.key==='ArrowRight'?1:2))%3;
    showCategory(tabs[target].dataset.category);tabs[target].focus();
  });
});
function openShop(){cancelGesture();shop.hidden=false;dock.hidden=true;root.querySelector('.hud').inert=true;root.querySelector('.back').focus();}
function closeShop(){shop.hidden=true;dock.hidden=false;root.querySelector('.hud').inert=false;updateWoodAlignment();root.querySelector('.shop-action').focus();}
root.querySelector('.shop-action').addEventListener('click',openShop);
root.querySelector('.back').addEventListener('click',closeShop);
function showMode(mode){
  cancelGesture();
  root.dataset.mode=mode;
  root.querySelector('.hud-editing').setAttribute('aria-pressed',String(mode==='editing'));
  root.querySelector('.hud-live').setAttribute('aria-pressed',String(mode==='live'));
  requestAnimationFrame(updateWoodAlignment);
}
root.querySelector('.hud-editing').addEventListener('click',()=>showMode('editing'));
root.querySelector('.hud-live').addEventListener('click',()=>showMode('live'));
row.addEventListener('click',event=>{if(event.detail===0){const card=event.target.closest('.inventory-item');if(card)selectItem(card);}});
row.addEventListener('keydown',event=>{
  const card=event.target.closest('.inventory-item');
  if(!card||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  event.preventDefault();
  const cards=[...row.children];const index=cards.indexOf(card);
  const next=event.key==='Home'?0:event.key==='End'?cards.length-1:Math.max(0,Math.min(cards.length-1,index+(event.key==='ArrowRight'?1:-1)));
  cards[next].focus({preventScroll:true});cards[next].scrollIntoView({block:'nearest',inline:'nearest',behavior:'instant'});
});
strip.addEventListener('wheel',event=>{
  if(Math.abs(event.deltaY)>Math.abs(event.deltaX)&&strip.scrollWidth>strip.clientWidth){event.preventDefault();strip.scrollLeft+=event.deltaY;}
},{passive:false});
strip.addEventListener('pointerdown',event=>{
  if(!event.isPrimary || (event.pointerType==='mouse'&&event.button!==0))return;
  cancelGesture();
  gesture={pointer:event.pointerId,type:event.pointerType,x:event.clientX,y:event.clientY,scroll:strip.scrollLeft,owner:'pending',card:event.target.closest('.inventory-item')};
  strip.setPointerCapture(event.pointerId);
});
strip.addEventListener('pointermove',event=>{
  if(!gesture||event.pointerId!==gesture.pointer)return;
  const dx=event.clientX-gesture.x,dy=event.clientY-gesture.y;
  if(gesture.owner==='pending'&&Math.hypot(dx,dy)>10){
    if(Math.abs(dx)>Math.abs(dy)*1.3)gesture.owner='scroll';
    else if(dy<0&&Math.abs(dy)>Math.abs(dx)*1.3){
      gesture.owner=gesture.card?.getAttribute('aria-disabled')==='false'?'placement':'cancel';
      if(gesture.owner==='placement'){
        ghost=document.createElement('img');ghost.className='drag-ghost';ghost.src=asset(gesture.card.dataset.art);ghost.alt='';ghost.setAttribute('aria-hidden','true');root.append(ghost);
        status.textContent=`Previewing ${gesture.card.dataset.name}. Release or Escape to end the preview.`;
      }
    }else if(dy>0&&Math.abs(dy)>Math.abs(dx)*1.3)gesture.owner='cancel';
  }
  if(gesture.owner==='scroll'&&gesture.type==='mouse')strip.scrollLeft=gesture.scroll-dx;
  if(gesture.owner==='placement'){
    event.preventDefault();const bounds=root.getBoundingClientRect();ghost.style.left=`${event.clientX-bounds.left}px`;ghost.style.top=`${event.clientY-bounds.top}px`;
  }
});
strip.addEventListener('pointerup',event=>{
  if(!gesture||event.pointerId!==gesture.pointer)return;
  const distance=Math.hypot(event.clientX-gesture.x,event.clientY-gesture.y);
  if(gesture.owner==='pending'&&distance<=10&&gesture.card)selectItem(gesture.card);
  cancelGesture();
});
strip.addEventListener('pointercancel',cancelGesture);
function cancelGesture(){if(gesture&&strip.hasPointerCapture(gesture.pointer))strip.releasePointerCapture(gesture.pointer);gesture=null;ghost?.remove();ghost=null;}
window.addEventListener('blur',cancelGesture);
document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelGesture();});
document.addEventListener('keydown',event=>{
  if(event.key!=='Escape')return;
  if(!shop.hidden)closeShop();
  if(root.dataset.mode==='live'){showMode('editing');root.querySelector('.hud-editing').focus();}
  cancelGesture();selected='';for(const card of row.children)card.setAttribute('aria-pressed','false');
});
showCategory(['people','floor'].includes(initial)?initial:'layout');
if(initial==='shop')openShop();
showMode(initial==='live'?'live':'editing');
document.documentElement.dataset.ready='true';
