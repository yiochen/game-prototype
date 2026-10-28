import {SharedClose} from '../../wireframe/shared-close.jsx';
import React,{useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {catalog,timing} from './balance.js';
import {storageKey,fixture,restore,command,validCell,beltCells} from './model.js';
import '../editor-dock-preview/shared.css';
import '../../wireframe/recipe-maple.css';
import './style.css';
const dock=import.meta.glob('../editor-dock-preview/assets/*.png',{eager:true,query:'?url',import:'default'});
const world=import.meta.glob('./assets/*.png',{eager:true,query:'?url',import:'default'});
const art=n=>dock[`../editor-dock-preview/assets/${n}.png`];
const worldArt=n=>world[`./assets/world-${n}.png`]||art(n);
const paths={people:'M4 21v-3a8 8 0 0 1 16 0v3M8 6a4 4 0 1 0 8 0 4 4 0 0 0-8 0',layout:'M4 5h16v14H4ZM4 10h16M10 10v9',floor:'M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z',shop:'M3 8h18l-2 13H5ZM7 8l3-6M17 8l-3-6',play:'m8 4 12 8-12 8Z',edit:'m4 16 11-11 4 4L8 20l-5 1 1-5',bag:'M5 7h14l2 14H3L5 7Zm3 0V5a4 4 0 0 1 8 0v2',return:'M4 14v7h16v-7M12 2v13m-5-5 5 5 5-5'};
function Icon({name}){return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]}/></svg>;}
function Coin({amount}){return <span className="shop-money"><span className="shop-coin" aria-hidden="true">★</span><span>{amount.toLocaleString()}</span></span>;}
function ShopRow({item,model,onBuy,pressed=false}){const stock=model.stock[item.id],sold=stock===0;return <article className={`supply-row ${sold?'sold-out':''}`} aria-label={item.name}>
 <div className="supply-art"><img src={art(item.art)} alt="" draggable="false"/></div><div className="supply-copy"><h2>{item.name}</h2><p>{item.description}</p><small>{stock===null?'Always available':sold?'Sold out':`${stock} remaining`}</small></div>
 <button className={`cost-action ${pressed?'sample-pressed':''}`} disabled={sold||model.coins<item.price} onClick={e=>{if(e.detail<2)onBuy(item.id,e.currentTarget.closest('.supply-row').querySelector('.supply-art img').getBoundingClientRect());}} aria-label={`Buy ${item.name} for ${item.price} coins${sold?', sold out':''}`}><Coin amount={item.price}/></button>
 </article>;}
function PurchaseFlight({flight,bag,onArrival}){
 const node=useRef(null);
 useLayoutEffect(()=>{
  const target=bag.current?.getBoundingClientRect();if(!target)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduced){onArrival(flight.key);return;}
  const parent=node.current.parentElement.getBoundingClientRect(),x=flight.rect.x+flight.rect.width/2-parent.x,y=flight.rect.y+flight.rect.height/2-parent.y,dx=target.x+target.width/2-parent.x-x,dy=target.y+target.height/2-parent.y-y;
  node.current.style.left=x+'px';node.current.style.top=y+'px';
  const a=node.current.animate([{transform:'translate(-50%,-50%) scale(1)',opacity:1,offset:0},{transform:`translate(calc(-50% + ${dx*.36}px),calc(-50% + ${Math.min(-65,dy*.2)}px)) scale(.9) rotate(-9deg)`,opacity:1,offset:.4},{transform:`translate(calc(-50% + ${dx}px),calc(-50% + ${dy}px)) scale(.12) rotate(8deg)`,opacity:0,offset:1}],{duration:timing.purchaseFlightMs,easing:'cubic-bezier(.36,0,.66,1)',fill:'forwards'});
  a.onfinish=()=>onArrival(flight.key);return()=>a.cancel();
 },[]);
 return <img ref={node} className="purchase-flight" src={art(flight.art)} alt="" aria-hidden="true"/>;
}
function ShopPopup({model,onBuy,onClose,pressed=false}){
 const [flights,setFlights]=useState([]),bag=useRef(null),serial=useRef(0),pulse=useRef(null);
 function arrive(key){setFlights(a=>a.filter(f=>f.key!==key));pulse.current?.cancel();pulse.current=bag.current?.animate(matchMedia('(prefers-reduced-motion: reduce)').matches?[{opacity:.65},{opacity:1}]:[{transform:'scale(1)'},{transform:'scale(1.13)',offset:.4},{transform:'scale(1)'}],{duration:240,easing:'ease-out'});}
 function buy(id,rect){if(onBuy(id)){setFlights(a=>[...a,{key:++serial.current,rect,art:catalog.find(i=>i.id===id).art}]);}}
 useEffect(()=>{const cancel=()=>{setFlights([]);pulse.current?.cancel();};window.addEventListener('blur',cancel);document.addEventListener('visibilitychange',cancel);return()=>{pulse.current?.cancel();window.removeEventListener('blur',cancel);document.removeEventListener('visibilitychange',cancel);};},[]);
 return <div className="shop-overlay" role="dialog" aria-modal="true" aria-labelledby="shop-heading">
 <section className="shop-panel wr-panel"><header className="catalog-heading"><div className="paper-balance" aria-label={`${model.coins} coins`}><Coin amount={model.coins}/></div><h1 id="shop-heading">Shop</h1></header>
 <div className="supply-scroll wr-catalog" tabIndex={0} aria-label="Shop catalog"><div className="supply-list">{catalog.map(item=><ShopRow key={item.id} item={item} model={model} onBuy={buy} pressed={pressed&&item.id==='belt'}/>)}</div><div className="catalog-end" aria-hidden="true"><span/> <Icon name="shop"/> <span/></div></div>
 <SharedClose label="Close Shop" onClick={onClose}/>
 <footer className="shop-footer"><div className="shop-footer-waves" aria-hidden="true"/><button type="button" className="shopping-bag" ref={bag} aria-label="Back to inventory" title="Back to inventory" onClick={onClose}><Icon name="bag"/></button></footer></section>
 {flights.map(f=><PurchaseFlight key={f.key} flight={f} bag={bag} onArrival={arrive}/>)}
 </div>;
}
const reviewNames={shop:'Shop · Edit origin',poor:'Not enough coins',live:'Live restaurant',restaurant:'Restaurant',sold:'Sold out',gallery:'Shared components'};
const initial=new URLSearchParams(location.search).get('state')||'restaurant';
function App(){
 const [model,setModel]=useState(()=>restore(localStorage,initial)),ref=useRef(model);
 const [review,setReview]=useState(initial),[open,setOpen]=useState(!['restaurant','live','gallery'].includes(initial)&&model.mode==='edit'),[selected,setSelected]=useState(null),[picked,setPicked]=useState(null),[drag,setDrag]=useState(null),[notice,setNotice]=useState(''),[sample,setSample]=useState('normal');
 const scene=useRef(null),shopRef=useRef(null),opener=useRef(null),strip=useRef(null),gesture=useRef(null),pan=useRef(null),ignoreClick=useRef(false),timer=useRef(null),positions=useRef({});
 const gallery=review==='gallery';
 function commit(a){const prev=ref.current,next=command(prev,a);if(next!==prev){localStorage.setItem(storageKey,JSON.stringify(next));ref.current=next;setModel(next);}return next!==prev;}
 function tell(s){clearTimeout(timer.current);setNotice(s);timer.current=setTimeout(()=>setNotice(''),2400);}
 function buy(id){return commit({type:'buy',id});}
 function show(e){if(ref.current.mode!=='edit')return;opener.current=e.currentTarget;gesture.current=null;pan.current=null;setDrag(null);setOpen(true);history.pushState({shop:true},'');}
 function hide(){setOpen(false);requestAnimationFrame(()=>opener.current?.isConnected?opener.current.focus({preventScroll:true}):scene.current?.querySelector('.shop-action').focus({preventScroll:true}));}
 function close(){if(history.state?.shop)history.back();else hide();}
 function reset(s=review){let v=fixture(s);if(s==='sold')v={...v,stock:{...v.stock,plant:0,barrel:0}};localStorage.setItem(storageKey,JSON.stringify(v));ref.current=v;setModel(v);setReview(s);setOpen(!['restaurant','live','gallery'].includes(s));setSelected(null);setPicked(null);setDrag(null);setNotice('');positions.current={};if(strip.current)strip.current.scrollLeft=0;}
 useEffect(()=>{localStorage.setItem(storageKey,JSON.stringify(ref.current));const pop=()=>hide();window.addEventListener('popstate',pop);return()=>{window.removeEventListener('popstate',pop);clearTimeout(timer.current);};},[]);
 useEffect(()=>{let last=performance.now();const id=setInterval(()=>{const now=performance.now(),seconds=(now-last)/1000;last=now;commit({type:'tick',seconds});},1000);return()=>clearInterval(id);},[]);
 useLayoutEffect(()=>{if(open&&!gallery)shopRef.current?.querySelector('.shared-close')?.focus({preventScroll:true});},[open,gallery]);
 useEffect(()=>{const key=e=>{if(e.key==='Escape'){e.preventDefault();if(open)close();else if(drag||selected){gesture.current=null;setDrag(null);setSelected(null);}else setPicked(null);}if(e.key==='Tab'&&open&&!gallery){const nodes=[...shopRef.current.querySelectorAll('button:not(:disabled),[tabindex="0"]')];const first=nodes[0],last=nodes.at(-1);if(e.shiftKey&&(document.activeElement===first||!shopRef.current.contains(document.activeElement))){e.preventDefault();last?.focus();}else if(!e.shiftKey&&(document.activeElement===last||!shopRef.current.contains(document.activeElement))){e.preventDefault();first?.focus();}}};
 const cancel=()=>{gesture.current=null;pan.current=null;setDrag(null);};document.addEventListener('keydown',key,true);window.addEventListener('blur',cancel);document.addEventListener('visibilitychange',cancel);return()=>{document.removeEventListener('keydown',key,true);window.removeEventListener('blur',cancel);document.removeEventListener('visibilitychange',cancel);};},[open,selected,drag,gallery]);
 function category(c){positions.current[ref.current.category]=strip.current?.scrollLeft||0;commit({type:'category',value:c});setSelected(null);requestAnimationFrame(()=>{if(strip.current)strip.current.scrollLeft=positions.current[c]||0;});}
 function hit(x,y){return [...scene.current.querySelectorAll('.floor-cell')].findIndex(el=>{const b=el.getBoundingClientRect();return x>=b.left&&x<b.right&&y>=b.top&&y<b.bottom;});}
 function place(id,cell){if(commit({type:'place',id,cell})){setSelected(null);setPicked(null);setNotice('');}else tell('Choose an empty floor cell');}
 function down(e,item){if(e.button!==0)return;ignoreClick.current=false;gesture.current={id:e.pointerId,x:e.clientX,y:e.clientY,item:item.id,lock:null,scroll:strip.current.scrollLeft};}
 function move(e){const g=gesture.current;if(!g||g.id!==e.pointerId)return;const dx=e.clientX-g.x,dy=e.clientY-g.y;if(!g.lock&&Math.hypot(dx,dy)>8){g.lock=dy<0&&Math.abs(dy)>Math.abs(dx)&&ref.current.inventory[g.item]>0?'place':'scroll';e.currentTarget.setPointerCapture(e.pointerId);}if(g.lock==='scroll')strip.current.scrollLeft=g.scroll-dx;if(g.lock==='place'){const b=scene.current.getBoundingClientRect(),cell=hit(e.clientX,e.clientY);setDrag({id:g.item,x:e.clientX-b.left,y:e.clientY-b.top,cell});}}
 function finish(e,cancel=false){const g=gesture.current;if(!g||g.id!==e.pointerId)return;gesture.current=null;setDrag(null);ignoreClick.current=!!g.lock;if(g.lock==='place'&&!cancel)place(g.item,hit(e.clientX,e.clientY));}
 const sampleModel=sample==='disabled'?{...model,coins:24}:sample==='sold'?{...model,stock:{...model.stock,plant:0,barrel:0}}:model;
 return <div className="shop-review"><nav className="review-toolbar" aria-label="Prototype review controls"><a href="../../#shop">Sushi Loop · #18</a><label><span className="sr-only">Review state</span><select value={review} onChange={e=>reset(e.target.value)}>{Object.entries(reviewNames).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label><button onClick={()=>reset()}>Reset</button></nav>
 <main className={`scene shop-scene ${gallery?'shop-gallery':''}`} ref={scene} aria-label="Shop UI prototype" data-mode={model.mode}>
 <div className="restaurant-origin" inert={open||gallery} aria-hidden={open||gallery}>
 <div className="room-viewport" onPointerDown={e=>{if(e.button!==0||e.target.closest('button'))return;pan.current={id:e.pointerId,startX:e.clientX,startY:e.clientY,x:ref.current.camera.x,y:ref.current.camera.y};e.currentTarget.setPointerCapture(e.pointerId);}} onPointerMove={e=>{const p=pan.current;if(p?.id===e.pointerId)commit({type:'pan',x:p.x+e.clientX-p.startX,y:p.y+e.clientY-p.startY});}} onPointerUp={()=>pan.current=null} onPointerCancel={()=>pan.current=null}>
 <div className="moving-room" style={{transform:`translate(${model.camera.x}px,${model.camera.y}px)`}}><div className="room-wall"><img src={art('restaurant-wall')} alt=""/></div><div className="floor-grid">{Array.from({length:49},(_,cell)=><div key={cell} className={`floor-cell ${selected||drag?'placing':''} ${validCell(model,cell)?'free-cell':''} ${drag?.cell===cell?'over-cell':''}`}>
 {beltCells.includes(cell)&&<img className="placed-art fixed-belt" src={worldArt('belt-straight-e')} alt="Conveyor"/>}
 {[22,24].includes(cell)&&<img className="scene-chef" src={art(cell===22?'chef-lena':'chef-omar')} alt="Chef"/>}
 {model.objects.filter(o=>o.cell===cell).map(o=><button key={o.id} data-kind={o.kind} className={`placed-object ${picked===o.id?'object-selected':''}`} aria-label={`Select placed ${catalog.find(i=>i.id===o.kind).name}`} onClick={()=>{if(model.mode==='edit'){setPicked(o.id);setSelected(null);}}}><img src={worldArt(catalog.find(i=>i.id===o.kind).world)} alt=""/></button>)}
 {selected&&validCell(model,cell)&&<button className="place-target" aria-label={`Place ${catalog.find(i=>i.id===selected).name} in cell ${cell}`} onClick={()=>place(selected,cell)}/>}
 </div>)}</div></div></div>
 <header className="shop-hud"><div className="coin-pill" aria-label={`${model.coins} coins`}><Coin amount={model.coins}/></div><span className="mode-label">{model.mode==='edit'?'Editing':''}</span><button className={`mode-action ${model.mode==='edit'?'vermilion':''}`} onClick={()=>{commit({type:'mode',value:model.mode==='edit'?'live':'edit'});setPicked(null);setSelected(null);}}><Icon name={model.mode==='edit'?'play':'edit'}/>{model.mode==='edit'?'Live':'Edit'}</button></header>
 {model.mode==='live'&&<div className="charge-status" aria-label={`Submarine charge ${Math.floor(model.charge/timing.chargeSeconds*100)} percent`}><span>Submarine</span><progress value={model.charge} max={timing.chargeSeconds}/></div>}
 {picked!==null&&model.mode==='edit'&&<button className="store-action" onClick={()=>{commit({type:'return',id:picked});setPicked(null);setNotice('');}}><Icon name="return"/>Return</button>}
 {selected&&<div className="placement-note" role="status">Tap an empty cell <button aria-label="Cancel placement" onClick={()=>setSelected(null)}>×</button></div>}
 {model.mode==='edit'&&<section className="dock" hidden={open||gallery} aria-label="Restaurant editor"><div className="board"/><div className="wave-window"><div className="waves"/></div><nav className="category-navigation"><div className="tabs" role="tablist" aria-label="Editing category">{['people','layout','floor'].map(c=><button className="tab" key={c} role="tab" aria-selected={model.category===c} onClick={()=>category(c)}><span className="surface"/><Icon name={c}/><span className="caption">{c[0].toUpperCase()+c.slice(1)}</span></button>)}</div><button className="shop-action" onClick={show}><span className="surface"/><Icon name="shop"/>Shop</button></nav><div className="inventory" ref={strip} data-category={model.category} aria-label={`${model.category} inventory`}><div className="inventory-row">{model.category==='layout'?catalog.map(i=><button key={i.id} className="inventory-item" aria-pressed={selected===i.id} aria-disabled={!model.inventory[i.id]} aria-label={`${i.name}, ${model.inventory[i.id]} available`} onPointerDown={e=>down(e,i)} onPointerMove={move} onPointerUp={e=>finish(e)} onPointerCancel={e=>finish(e,true)} onLostPointerCapture={e=>{if(e.target===e.currentTarget)finish(e,true);}} onClick={()=>{if(ignoreClick.current){ignoreClick.current=false;return;}if(model.inventory[i.id]){setSelected(i.id);setPicked(null);}}}><span className="item-preview"><img src={art(i.art)} alt="" draggable="false"/><span className="quantity">{model.inventory[i.id]}</span></span><span className="item-name">{i.name}</span></button>):model.category==='people'?<div className="people-preview">{['lena','omar'].map(n=><div key={n}><img src={art('chef-'+n)} alt=""/><span>{n==='lena'?'Lena':'Omar'}</span></div>)}</div>:<div className="floor-preview"><img src={art('floor-cream')} alt=""/><span>Cream tile · Current</span></div>}</div></div></section>}
 </div>
 {open&&!gallery&&<div className="paper-host" ref={shopRef}><ShopPopup model={model} onBuy={buy} onClose={close}/></div>}
 {gallery&&<><div className="gallery-controls"><h1>Shop · Shared components</h1><div>{['normal','pressed','disabled','sold'].map(s=><button key={s} aria-pressed={sample===s} onClick={()=>setSample(s)}>{s==='sold'?'Sold out':s}</button>)}</div></div><div className="gallery-paper"><ShopPopup model={sampleModel} onBuy={buy} onClose={()=>reset('restaurant')} pressed={sample==='pressed'}/></div></>}
 {drag&&<div className="goods-ghost" style={{left:drag.x,top:drag.y}}><img src={art(catalog.find(i=>i.id===drag.id).art)} alt=""/><span>{validCell(model,drag.cell)?'Place here':'Empty floor only'}</span></div>}
 <p className={`shop-notice ${notice?'visible':''}`} role="status" aria-live="polite">{notice}</p>
 </main></div>;
}
createRoot(document.getElementById('root')).render(<App/>);
