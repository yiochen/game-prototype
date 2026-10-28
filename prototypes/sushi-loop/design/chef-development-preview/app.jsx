import React,{useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ChefPortrait} from '../../wireframe/chef-portrait.jsx';
import {MapleRecipePanel,plateRecipes} from '../../wireframe/recipe-maple.jsx';
import {storageKey,fixture,restore,command,speed,cost,tier,balance,beltCells,validCell} from './model.js';
import '../editor-dock-preview/shared.css';
import '../staff-hiring-preview/style.css';
import './style.css';

const sources=import.meta.glob('../staff-hiring-preview/assets/*.png',{eager:true,query:'?url',import:'default'});
const room=import.meta.glob('../editor-dock-preview/assets/*.png',{eager:true,query:'?url',import:'default'});
const art=n=>sources[`../staff-hiring-preview/assets/${n}.png`];
const backdrop=n=>room[`../editor-dock-preview/assets/${n}.png`];
const given=c=>c.name.split(' ')[0];
const stateNames={develop:'Develop chef',recipes:'Recipes → Manage',poor:'Insufficient coins',max:'At maximum level','near-max':'One level before MAX',unassigned:'Unassigned chef',fire:'Firing application',people:'People · Edit',gallery:'Shared components'};
const initial=new URLSearchParams(location.search).get('state')||'develop';
const paths={close:'m7 7 10 10M17 7 7 17',play:'m8 4 12 8-12 8Z',people:'M4 21v-3a8 8 0 0 1 16 0v3M8 6a4 4 0 1 0 8 0 4 4 0 0 0-8 0',layout:'M4 5h16v14H4ZM4 10h16M10 10v9',floor:'M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z',left:'m14 6-6 6 6 6'};
function Icon({name}){return <svg className="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]}/></svg>;}
function Coin({amount}){return <span className="money"><span className="mini-coin" aria-hidden="true">★</span>{amount.toLocaleString()}</span>;}
function Close({onClick,label}){return <button className="round" onClick={onClick} aria-label={label}><Icon name="close"/></button>;}
function Plate({level}){const color=tier(level);return <span className={`tier-plate plate-${color.toLowerCase()}`} role="img" aria-label={`${color} plate tier, requires Level ${balance.thresholds[balance.tiers.indexOf(color)]}`}/>;}
function Photo({chef,...props}){return <button {...props} className="staff-photo" data-chef={chef.id} aria-label={`Open ${given(chef)}’s recipes, ${chef.assigned?'assigned':'unassigned'}`}><img className="photo-paper" src={art('photo-outer')} alt="" draggable="false"/><img className="photo-inner" src={art('photo-inner')} alt="" draggable="false"/><span className="photo-portrait"><ChefPortrait chefId={chef.id} bust/></span><strong className="photo-name">{given(chef)}</strong>{chef.assigned&&<span className="assigned-stamp"><img src={art('assigned-stamp')} alt=""/>Assigned</span>}</button>;}

function IdentityHeader({chef,onClose,confirm=false}){return <><ChefPortrait chefId={chef.id} bust className="development-portrait"/><header className="development-header"><div><h1 id={confirm?'fire-title':'development-title'}>{confirm?`Fire ${given(chef)}?`:given(chef)}</h1><p>{confirm?chef.name:chef.assigned?'Assigned · restaurant':'Unassigned staff'}</p></div><Close label={confirm?'Cancel dismissal':'Close chef management'} onClick={onClose}/></header></>;}
function Development({chef,coins,onUpgrade,onUnassign,onPlace,onFire,onRecipes,onClose,message='',gallery=false,embedded=false}){
 const max=chef.level>=chef.ceiling,unlock=tier(chef.level+1)!==tier(chef.level),affordable=coins>=cost(chef);
 return <section className="development-panel" onClickCapture={e=>{if(e.detail>1){e.preventDefault();e.stopPropagation();}}} role={embedded?undefined:gallery?'region':'dialog'} aria-modal={embedded||gallery?undefined:'true'} aria-labelledby={embedded||gallery?undefined:'development-title'} aria-label={gallery?`${given(chef)} development sample`:undefined}>
  {!embedded&&<IdentityHeader chef={chef} onClose={onClose}/>}
  <div className="development-interior"><div className="development-scroll" tabIndex={0} aria-label="Chef development details">
   <p className="manage-assignment">{chef.assigned?'Assigned · restaurant':'Unassigned staff'}</p><dl className="current-facts"><div><dt>Level</dt><dd>{chef.level}<small> / {chef.ceiling}</small></dd></div><div><dt>Cooking speed</dt><dd>{speed(chef).toFixed(2)}<small>×</small></dd></div><div><dt>Growth / level</dt><dd>+{Math.round(chef.growthRate*100)}<small>%</small></dd></div></dl>
   <div className="tier-fact"><Plate level={chef.level}/><p><strong>{tier(chef.level)} recipes</strong><span>Ceiling: Level {chef.ceiling} · {tier(chef.ceiling)} plates</span></p></div>
   <section className={`next-level ${max?'is-max':''}`} aria-label={max?'Final chef stats':'Next level preview'}>
    <div className="next-heading"><h2>{max?'Capability ceiling reached':`Next: Level ${chef.level+1}`}</h2>{max&&<strong className="max-label">MAX</strong>}</div>
    {max?<p>Final speed <strong>{speed(chef).toFixed(2)}×</strong> · {tier(chef.level)} recipes</p>:<><p className="speed-preview"><span>Cooking speed</span><span><strong>{speed(chef).toFixed(2)}×</strong><span className="stat-arrow" aria-hidden="true"> → </span><strong>{speed(chef,chef.level+1).toFixed(2)}×</strong></span></p>{unlock&&<div className="unlock-preview"><Plate level={chef.level+1}/><p><strong>Unlocks {tier(chef.level+1)} recipes</strong><span>Available at Level {chef.level+1}</span></p></div>}</>}
   </section>
   <p className={`upgrade-result ${message?'has-result':''}`} role="status">{message||' '}</p>
  </div>
  <div className="development-actions"><div className="purchase-slot">{!max&&<><button className="primary upgrade" disabled={!affordable} onClick={e=>{if(e.detail<2)onUpgrade(chef.level);}} aria-label={`Level up ${given(chef)} to Level ${chef.level+1} for ${cost(chef)} coins`}>Level up <Coin amount={cost(chef)}/></button>{!affordable&&<p className="budget-reason">{coins} / {cost(chef)} coins · Not enough coins</p>}</>}</div>
   <div className="management-row"><button className="secondary" onClick={chef.assigned?onUnassign:onPlace}>{chef.assigned?'Unassign':'Place in restaurant'}</button><button className="fire-action" onClick={onFire}>Fire…</button></div>
  </div><div className="panel-waves" aria-hidden="true"/></div>
 </section>;
}
function ChefPopup({chef,tab,onTab,onClose,children,gallery=false}){
 const tabs=useRef(null);
 function select(next,focus=false){onTab(next);if(focus)tabs.current?.querySelector(`[data-tab="${next}"]`)?.focus();}
 return <section className="development-panel chef-popup" role={gallery?'region':'dialog'} aria-modal={gallery?undefined:'true'} aria-label={gallery?'Chef popup sample':`${given(chef)}’s chef popup`}>
  <ChefPortrait chefId={chef.id} bust className="development-portrait"/>
  <header className="chef-popup-header"><div><h1>{tab==='recipes'?`${given(chef)}’s recipes`:given(chef)}</h1><nav ref={tabs} className="chef-tabs" role="tablist" aria-label="Chef pages" onKeyDown={e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();select(e.key==='Home'?'recipes':e.key==='End'?'develop':tab==='recipes'?'develop':'recipes',true);}}}>
   <button id="recipe-tab" role="tab" data-tab="recipes" aria-controls="recipe-page" aria-selected={tab==='recipes'} tabIndex={tab==='recipes'?0:-1} onClick={()=>select('recipes')}>Recipes</button><button id="manage-tab" role="tab" data-tab="develop" aria-controls="manage-page" aria-selected={tab==='develop'} tabIndex={tab==='develop'?0:-1} onClick={()=>select('develop')}>Manage</button>
  </nav></div><Close label={tab==='recipes'?'Close recipes':'Close chef management'} onClick={onClose}/><span className="chef-header-separator" hidden={tab!=='develop'} aria-hidden="true"/></header>
  <div className="chef-content-window"><div className="chef-page-track" data-tab={tab} style={{transform:`translateX(${tab==='recipes'?0:-50}%)`}}>
   <div id="recipe-page" role="tabpanel" aria-labelledby="recipe-tab" aria-hidden={tab!=='recipes'} inert={tab!=='recipes'} className="chef-page recipe-page">{children[0]}</div>
   <div id="manage-page" role="tabpanel" aria-labelledby="manage-tab" aria-hidden={tab!=='develop'} inert={tab!=='develop'} className="chef-page manage-page">{children[1]}</div>
  </div></div>
 </section>;
}
function FiringApplication({chef,fired,onCancel,onConfirm,onClose,gallery=false}){
 const visual=useRef(null),paper=useRef(null),ink=useRef(null),stamp=useRef(null);
 useLayoutEffect(()=>{
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const animation=visual.current.animate(reduced?[{opacity:0},{opacity:1}]:[{opacity:0,transform:'translateY(100%)'},{opacity:1,transform:'translateY(0)'}],{duration:reduced?100:340,easing:'cubic-bezier(.22,1,.36,1)',fill:'both'});
  return()=>animation.cancel();
 },[]);
 useLayoutEffect(()=>{
  if(!fired)return;const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,duration=reduced?180:1100;
  const imprint=ink.current.animate(reduced?[{opacity:0},{opacity:.94}]:[
   {opacity:0,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.16)',offset:0},
   {opacity:0,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.16)',offset:.31},
   {opacity:1,transform:'translate(-50%,-50%) rotate(-12deg) scale(1.06)',offset:.33},
   {opacity:.94,transform:'translate(-50%,-50%) rotate(-12deg) scale(1)',offset:.42},
   {opacity:.94,transform:'translate(-50%,-50%) rotate(-12deg) scale(1)',offset:1}],{duration,fill:'both'});
  const prop=reduced?null:stamp.current.animate([
   {opacity:0,transform:'translateY(-160px) rotate(-5deg) scale(1.1)',offset:0},
   {opacity:1,transform:'translateY(-150px) rotate(-5deg) scale(1.1)',offset:.16,easing:'cubic-bezier(.45,0,.9,.55)'},
   {opacity:1,transform:'translateY(0) rotate(0deg) scale(1)',offset:.32},
   {opacity:1,transform:'translateY(-10px) rotate(-2deg)',offset:.39},
   {opacity:1,transform:'translateY(-4px) rotate(-1deg)',offset:.45},
   {opacity:0,transform:'translateY(-175px) rotate(-9deg)',offset:.64},
   {opacity:0,transform:'translateY(-175px) rotate(-9deg)',offset:1}],{duration,fill:'both'});
  const contact=reduced?null:paper.current.animate([{transform:'scale(1)',offset:0},{transform:'scale(1.025)',offset:.2},{transform:'translateY(2px) scale(1.01)',offset:.33},{transform:'scale(1.025)',offset:.42},{transform:'scale(1)',offset:1}],{duration,fill:'both'});
  return()=>{imprint.cancel();prop?.cancel();contact?.cancel();};
 },[fired]);
 return <section ref={visual} className={`dismissal-sheet ${fired?'is-fired':''}`} onClickCapture={e=>{if(e.detail>1){e.preventDefault();e.stopPropagation();}}} role={gallery?'region':'dialog'} aria-modal={gallery?undefined:'true'} aria-label={gallery?'Dismissal confirmation sample':fired?`${chef.name} fired`:`Fire ${chef.name}?`}>
  <header className="dismissal-header"><h1>{fired?'Application':`Fire ${given(chef)}?`}</h1><Close label={fired?'Close fired application':'Cancel dismissal'} onClick={fired?onClose:onCancel}/></header>
  <div className="dismissal-paper-holder"><article className="resume-paper dismissal-paper" ref={paper}>
   <header className="resume-heading"><ChefPortrait chefId={chef.id} bust/><div><p className="eyebrow">Application</p><h2>{chef.name}</h2><p className="occupation">{chef.role}</p></div></header><p className="background-copy">{chef.background}</p>
   <dl className="resume-facts"><div><dt>Current level</dt><dd>{chef.level} / {chef.ceiling}</dd></div><div><dt>Cooking speed</dt><dd>{speed(chef).toFixed(2)}×</dd></div><div><dt>Growth / level</dt><dd>+{Math.round(chef.growthRate*100)}%</dd></div><div><dt>Maximum level</dt><dd>{chef.ceiling}</dd></div></dl>
   <p className="dismissal-copy">{fired?`${chef.name} has left your staff.`:`${chef.name} will permanently leave your staff, including their level and upgrades.`}</p>
   {fired&&<div className="firing-confirmation"><div className="fired-imprint" ref={ink} role="status" aria-label={`${chef.name} fired`}><img src={art('assigned-stamp')} alt=""/><span>Fired</span></div><img className="firing-rubber-stamp" ref={stamp} src={art('hiring-stamp')} alt=""/></div>}
  </article></div>
  <footer className="confirm-actions">{fired?<button className="secondary" onClick={onClose}>Close</button>:<><button className="secondary" onClick={onCancel}>Cancel</button><button className="primary" onClick={e=>{if(e.detail<2)onConfirm();}}>Fire {given(chef)}</button></>}</footer>
 </section>;
}
function Gallery({reset}){
 const [sample,setSample]=useState('normal'),[message,setMessage]=useState(''),[tab,setTab]=useState('develop'),[fired,setFired]=useState(false);const c=fixture(sample==='max'?'max':'develop').staff[0];
 return <div className="development-gallery"><header><p className="eyebrow">Shared components · #17</p><h1>Chef development</h1><p>Tabbed popup and firing application.</p></header><div className="gallery-switches">{['normal','pressed','disabled','max','confirmation','fired'].map(s=><button className="secondary" key={s} aria-pressed={sample===s} onClick={()=>{setSample(s);setMessage('');setTab('develop');setFired(s==='fired');}}>{s==='max'?'MAX':s}</button>)}</div>
 <div className={`gallery-panel-host ${sample==='pressed'?'show-pressed':''}`}>{['confirmation','fired'].includes(sample)?<FiringApplication chef={c} gallery fired={fired} onCancel={()=>setSample('normal')} onConfirm={()=>setFired(true)} onClose={()=>setSample('normal')}/>:<ChefPopup chef={c} gallery tab={tab} onTab={setTab} onClose={()=>reset('people')}><MapleRecipePanel embedded chefId={c.id} chefName={given(c)} level={c.level} state={{selectedRecipe:'salmon',currentRecipe:'salmon',seenRecipes:[]}} onInspect={()=>{}}/><Development embedded chef={c} coins={sample==='disabled'?60:1240} onUpgrade={()=>setMessage('Open the scene to buy a level.')} onUnassign={()=>reset('people')} onFire={()=>{setSample('confirmation');setFired(false);}} message={message}/></ChefPopup>}</div><button className="secondary" onClick={()=>reset('develop')}>Try the restaurant</button></div>;
}

function App(){
 const [model,setModel]=useState(()=>restore(localStorage,initial)),modelRef=useRef(model);
 const [review,setReview]=useState(initial),[selected,setSelected]=useState('lena'),[overlay,setOverlay]=useState(['people','gallery'].includes(initial)?null:initial==='recipes'?'recipes':initial==='fire'?'fire':'develop');
 const [category,setCategory]=useState('People'),[mode,setMode]=useState('edit'),[message,setMessage]=useState(''),[toast,setToast]=useState(''),[placement,setPlacement]=useState(null),[drag,setDrag]=useState(null),[inspected,setInspected]=useState('salmon');
 const [dismissal,setDismissal]=useState(initial==='fire'?{chef:fixture(initial).staff[0],fired:false}:null);
 const previousOverlay=useRef(null);
 const scene=useRef(null),modal=useRef(null),lastFocus=useRef(null),pointer=useRef(null),suppressClick=useRef(false),scroll=useRef(null),timer=useRef(null);
 const chef=model.staff.find(c=>c.id===selected),gallery=review==='gallery';
 const commit=action=>{const prev=modelRef.current,next=command(prev,action);if(next!==prev){localStorage.setItem(storageKey,JSON.stringify(next));modelRef.current=next;setModel(next);}return next;};
 function notify(text){clearTimeout(timer.current);setToast(text);timer.current=setTimeout(()=>setToast(''),3000);}
 function open(kind,id=selected){if(!overlay)lastFocus.current=document.activeElement;setSelected(id);setMessage('');setOverlay(kind);if(kind==='recipes')setInspected(modelRef.current.staff.find(c=>c.id===id)?.recipe||null);}
 function close(){setDismissal(null);setOverlay(null);setMessage('');requestAnimationFrame(()=>{if(lastFocus.current?.isConnected)lastFocus.current.focus({preventScroll:true});else scene.current?.querySelector('.staff-photo')?.focus({preventScroll:true});});}
 function reset(state=review){const next=fixture(state);localStorage.setItem(storageKey,JSON.stringify(next));modelRef.current=next;setModel(next);setReview(state);setSelected('lena');setCategory('People');setMode('edit');setOverlay(['people','gallery'].includes(state)?null:state==='recipes'?'recipes':state==='fire'?'fire':'develop');setMessage('');setToast('');setPlacement(null);setDrag(null);setInspected('salmon');setDismissal(state==='fire'?{chef:next.staff[0],fired:false}:null);pointer.current=null;}
 useEffect(()=>{localStorage.setItem(storageKey,JSON.stringify(modelRef.current));return()=>clearTimeout(timer.current);},[]);
 useLayoutEffect(()=>{if(overlay){const target=modal.current?.querySelector(previousOverlay.current==='fire'&&overlay==='develop'?'.fire-action':'.chef-popup-header>.round,.dismissal-header>.round');target?.focus({preventScroll:true});}previousOverlay.current=overlay;},[overlay==='fire'?'fire':!!overlay]);
 useEffect(()=>{if(overlay!=='fire'&&!model.staff.some(c=>c.id===selected)){setSelected(model.staff[0]?.id||null);setOverlay(null);}},[model.staff,selected,overlay]);
 useEffect(()=>{
  const key=e=>{if(e.key==='Escape'){e.preventDefault();if(drag||placement){pointer.current=null;setDrag(null);setPlacement(null);return;}if(overlay==='fire'){if(dismissal?.fired)close();else{setDismissal(null);setOverlay('develop');}return;}if(overlay)close();return;}if(e.key==='Tab'&&overlay){const nodes=[...modal.current.querySelectorAll('button:not(:disabled),[tabindex="0"]')].filter(el=>el.getClientRects().length&&!el.closest('[inert]')&&el.tabIndex>=0);const first=nodes[0],last=nodes.at(-1);if(e.shiftKey&&(document.activeElement===first||!modal.current.contains(document.activeElement))){e.preventDefault();last?.focus();}else if(!e.shiftKey&&(document.activeElement===last||!modal.current.contains(document.activeElement))){e.preventDefault();first?.focus();}}};
  const cancel=()=>{pointer.current=null;setDrag(null);};
  document.addEventListener('keydown',key,true);window.addEventListener('blur',cancel);document.addEventListener('visibilitychange',cancel);return()=>{document.removeEventListener('keydown',key,true);window.removeEventListener('blur',cancel);document.removeEventListener('visibilitychange',cancel);};
 },[overlay,drag,placement,dismissal]);
 function upgrade(expectedLevel){const old=modelRef.current.staff.find(c=>c.id===selected),next=commit({type:'upgrade',id:selected,expectedLevel}),now=next.staff.find(c=>c.id===selected);if(old===now)return;setMessage(tier(now.level)!==tier(old.level)?`Level ${now.level} · ${tier(now.level)} recipes unlocked!`:`Level ${now.level} · Cooking speed ${speed(now).toFixed(2)}×`);}
 function place(id,cell){const prev=modelRef.current,next=commit({type:'place',id,cell});setPlacement(null);if(next===prev)return;open('recipes',id);setInspected(null);notify('Chef placed. Choose a recipe to begin.');}
 function hit(x,y){const cells=scene.current.querySelectorAll('.world-cell');return [...cells].findIndex(el=>{const b=el.getBoundingClientRect();return x>=b.left&&x<b.right&&y>=b.top&&y<b.bottom;});}
 function start(e,c){if(e.button!==0||overlay)return;pointer.current={id:e.pointerId,x:e.clientX,y:e.clientY,chef:c,lock:null,scroll:scroll.current.scrollLeft};suppressClick.current=false;}
 function move(e){const p=pointer.current;if(!p||p.id!==e.pointerId)return;const dx=e.clientX-p.x,dy=e.clientY-p.y;if(!p.lock&&Math.hypot(dx,dy)>8){p.lock=dy<0&&Math.abs(dy)>Math.abs(dx)&&!p.chef.assigned?'place':'scroll';e.currentTarget.setPointerCapture(e.pointerId);}if(p.lock==='scroll')scroll.current.scrollLeft=p.scroll-dx;if(p.lock==='place'){const b=scene.current.getBoundingClientRect(),cell=hit(e.clientX,e.clientY);setDrag({id:p.chef.id,x:e.clientX-b.x,y:e.clientY-b.y,cell,valid:validCell(modelRef.current,cell,p.chef.id)});}}
 function finish(e,cancel=false){const p=pointer.current;if(!p||p.id!==e.pointerId)return;pointer.current=null;setDrag(null);suppressClick.current=!!p.lock;if(p.lock==='place'&&!cancel)place(p.chef.id,hit(e.clientX,e.clientY));}
 return <div className="review-shell"><nav className="review-toolbar" aria-label="Prototype review controls"><a href="../../#staff-detail">Sushi Loop <span>· #17</span></a><label><span className="sr-only">Review state</span><select value={review} onChange={e=>reset(e.target.value)}>{Object.entries(stateNames).map(([s,n])=><option value={s} key={s}>{n}</option>)}</select></label><button onClick={()=>reset()}>Reset</button></nav>
 <main ref={scene} className={`scene hiring-scene development-scene ${gallery?'gallery-scene':''}`} aria-label="Chef development prototype" data-mode={mode}>
 {gallery?<Gallery reset={reset}/>:<><div className="development-background" inert={!!overlay}>
 <div className="world"><img className="world-sky" src={backdrop('restaurant-sky')} alt=""/><div className="blue-wall"/><img className="world-wall" src={backdrop('restaurant-wall')} alt=""/><div className="world-floor"><img src={backdrop('restaurant-floor')} alt=""/></div></div>
 <header className="hiring-hud"><div className="coin-pill" aria-label={`${model.coins} coins`}><Coin amount={model.coins}/></div><button className="secondary" onClick={()=>{setMode('edit');setCategory('People');}}>Editing</button><button className="primary" onClick={()=>setMode(m=>m==='edit'?'live':'edit')}><Icon name="play"/>{mode==='edit'?'Live':'Edit'}</button></header>
 <div className={`placement-grid ${drag||placement?'placing':''}`} aria-label="Restaurant placement grid">{Array.from({length:42},(_,cell)=><div className={`world-cell ${drag?.cell===cell?'hover-cell':''} ${(drag||placement)&&validCell(model,cell,drag?.id||placement)?'valid-cell':''}`} key={cell}>
 {beltCells.includes(cell)&&<img className="belt-sprite" src={art('world-'+([13,31].includes(cell)?'belt-start-e':[16,34].includes(cell)?'belt-end-e':'belt-straight-e'))} alt="Conveyor belt"/>}
 {placement&&validCell(model,cell,placement)&&<button className="cell-target" aria-label={`Place chef beside belt, cell ${cell}`} onClick={()=>place(placement,cell)}/>}
 {model.staff.filter(c=>c.assigned&&c.cell===cell).map(c=><button key={c.id} className="world-chef" aria-label={`${given(c)}, ${c.recipe?'preparing':'idle'}`} onClick={()=>open('recipes',c.id)}><img src={art('world-'+c.id)} alt=""/>{!c.recipe&&<span className="idle-badge">Idle</span>}</button>)}</div>)}</div>
 {mode==='edit'&&<section className="staff-dock edit-dock" aria-label="People inventory"><nav className="dock-tabs" aria-label="Editor categories">{['People','Layout','Floor'].map((n,i)=><button key={n} className={category===n?'selected':''} aria-pressed={category===n} onClick={()=>setCategory(n)}><Icon name={['people','layout','floor'][i]}/>{n}</button>)}</nav><div className="roster-cap"><h2>{category} {category==='People'&&<span>{model.staff.length} / 4</span>}</h2>{category==='People'&&<a className="applicants-reference" href="../staff-hiring-preview/?state=people">Applicants ›</a>}</div>{category==='People'?<div className="roster-scroll" ref={scroll}><div className="roster-row">{model.staff.map(c=><Photo chef={c} key={c.id} onPointerDown={e=>start(e,c)} onPointerMove={move} onPointerUp={e=>finish(e)} onPointerCancel={e=>finish(e,true)} onLostPointerCapture={e=>finish(e,true)} onClick={()=>{if(suppressClick.current){suppressClick.current=false;return;}open('recipes',c.id);}}/>)}{!model.staff.length&&<p className="empty-staff">Your roster is empty. Meet new applicants.</p>}</div></div>:<p className="other-tab">{category} inventory · <button className="secondary" onClick={()=>setCategory('People')}>Back to People</button></p>}<div className="dock-waves" aria-hidden="true"/></section>}
 {placement&&<div className="placement-hint" role="status">Choose a cell beside a belt.<Close label="Cancel placement" onClick={()=>setPlacement(null)}/></div>}
 </div>
 {drag&&<div className="chef-ghost" style={{left:drag.x,top:drag.y}} aria-hidden="true"><img src={art('world-'+drag.id)} alt=""/><span>{drag.valid?'Place here':'Beside a belt'}</span></div>}
 {overlay&&(chef||dismissal)&&<div className={`modal-host development-modal ${overlay==='fire'?'firing-modal':'tabbed-modal'}`} ref={modal}><div className="scrim"/>{overlay==='fire'?<FiringApplication chef={dismissal.chef} fired={dismissal.fired} onCancel={()=>{setDismissal(null);setOverlay('develop');}} onConfirm={()=>{commit({type:'fire',id:dismissal.chef.id});setToast('');setDismissal(d=>({...d,fired:true}));}} onClose={close}/>:<ChefPopup chef={chef} tab={overlay} onTab={setOverlay} onClose={close}>
 <MapleRecipePanel embedded chefId={chef.id} chefName={given(chef)} level={chef.level} assigned={chef.assigned} cookingSpeed={speed(chef)} state={{selectedRecipe:inspected,currentRecipe:chef.assigned?chef.recipe:null,seenRecipes:['eel']}} onInspect={setInspected} onPrepare={()=>{const r=plateRecipes[inspected];if(!r||r.unknown||r.level>chef.level)return;commit({type:'prepare',id:chef.id,recipe:inspected,requiredLevel:r.level});notify(`${given(chef)} is preparing ${r.name.toLowerCase()}.`);close();}}/>
 <Development embedded chef={chef} coins={model.coins} onUpgrade={upgrade} onUnassign={()=>{commit({type:'unassign',id:chef.id});setMessage('Unassigned · Level and upgrades retained');}} onPlace={()=>{close();setPlacement(chef.id);}} onFire={()=>{setDismissal({chef:{...chef},fired:false});setOverlay('fire');}} message={message}/>
 </ChefPopup>}</div>}
 </>}
 <p className={`notice ${toast?'visible':''}`} role="status" aria-live="polite">{toast}</p>
 </main></div>;
}
createRoot(document.getElementById('root')).render(<App/>);
