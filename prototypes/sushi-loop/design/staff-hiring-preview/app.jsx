import {SharedClose} from '../../wireframe/shared-close.jsx';
import React, {useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {applicants,refreshedApplicants,startingChefs} from '../../wireframe/fixtures.js';
import {ChefPortrait} from '../../wireframe/chef-portrait.jsx';
import {MapleRecipePanel} from '../../wireframe/recipe-maple.jsx';
import '../editor-dock-preview/shared.css';
import './style.css';
import {ApplicationCardSurface} from './application-card-surface.jsx';
import {useNewChefNotices} from './use-new-chef-notices.js';

const files=import.meta.glob('./assets/*.png',{eager:true,query:'?url',import:'default'});
const art=name=>files[`./assets/${name}.png`];
const dockFiles=import.meta.glob('../editor-dock-preview/assets/*.png',{eager:true,query:'?url',import:'default'});
const dockArt=name=>dockFiles[`../editor-dock-preview/assets/${name}.png`];
const key='sushi-loop-issue16-ui-review-v1', capacity=4, cooldown=5*60*1000;
const all=[...startingChefs,...applicants,...refreshedApplicants];
const byId=id=>all.find(c=>c.id===id);
const given=c=>c.name.split(' ')[0];
const tierLevel={White:1,Yellow:3,Red:5,Blue:8,Black:12};
const patterns={White:'double ring',Yellow:'dots',Red:'dashes',Blue:'waves',Black:'scallops'};
const beltCells=[13,14,15,16,31,32,33,34];
const names={available:'Applicants',roster:'Staff tray',people:'People · Edit',full:'Capacity full',poor:'Not enough coins',empty:'No offers left',gallery:'Shared components'};
const initial=new URLSearchParams(location.search).get('state')||'available';
function fixture(name='available'){
 const staff=startingChefs.map((c,i)=>({...c,assigned:i===0,cell:i===0?19:null,recipe:i===0?'salmon':null}));
 if(name==='full')staff.push(...applicants.slice(0,2).map(c=>({...c,assigned:false,cell:null,recipe:null})));
 return {coins:name==='poor'?60:1240,staff,pool:name==='empty'?[]:applicants.filter(c=>!staff.some(s=>s.id===c.id)).map(c=>c.id),deadline:0,generation:0};
}
function restore(){try{const v=JSON.parse(localStorage.getItem(key));if(v&&Array.isArray(v.staff)&&Array.isArray(v.pool)&&Number.isFinite(v.coins)&&Number.isFinite(v.deadline))return v;}catch{}return fixture(initial);}
const paths={close:'m7 7 10 10M17 7 7 17',left:'m15 5-7 7 7 7',right:'m9 5 7 7-7 7',refresh:'M20 8a8 8 0 1 0 0 8M20 3v6h-6',people:'M4 21v-3a8 8 0 0 1 16 0v3M8 6a4 4 0 1 0 8 0 4 4 0 0 0-8 0',edit:'m4 16 11-11 4 4L8 20l-5 1 1-5',play:'m7 4 14 8-14 8Z',layout:'M4 5h16v14H4ZM4 10h16M10 10v9',floor:'M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z',shop:'M3 8h18l-2 13H5ZM7 8l3-6M17 8l-3-6',check:'m4 13 5 5L21 5',arrow:'M12 21V3m-7 7 7-7 7 7'};
function Icon({name}){return <svg viewBox="0 0 24 24" aria-hidden="true" className="ui-icon" fill={name==='play'?'currentColor':'none'} stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]}/></svg>;}
function Coin({amount}){return <span className="money"><span className="mini-coin" aria-hidden="true">★</span>{amount.toLocaleString()}</span>;}
function Plate({tier}){return <span className={`tier-plate plate-${tier.toLowerCase()}`} role="img" aria-label={`${tier} plate, ${patterns[tier]} rim, requires Level ${tierLevel[tier]}`}/>;}
function Close({onClick,label='Close applicants'}){return <SharedClose label={label} onClick={onClick}/>;}
function Photo({chef,...props}){return <button {...props} className={`staff-photo ${props.className||''}`} aria-label={`Inspect ${chef.name}, ${chef.assigned?'assigned':'unassigned'}${chef.isNew?', new chef':''}`}><img className="photo-paper" src={art('photo-outer')} alt="" draggable="false"/><img className="photo-inner" src={art('photo-inner')} alt="" draggable="false"/><span className="photo-portrait"><ChefPortrait chefId={chef.id} bust/></span><strong className="photo-name">{given(chef)}</strong>{chef.isNew&&<span className="new-chef-dot" role="img" aria-label="New chef"/>}{chef.assigned&&<span className="assigned-stamp"><img src={art('assigned-stamp')} alt=""/>Assigned</span>}</button>;}
function Resume({chef,full,coins,onHire,tabIndex=0}){return <article className="resume-paper" aria-label={`${chef.name} résumé`} tabIndex={tabIndex}>
 <header className="resume-heading"><ChefPortrait chefId={chef.id} bust/><div><p className="eyebrow">Application</p><h2>{chef.name}</h2><p className="occupation">{chef.role}</p></div></header>
 <p className="background-copy">{chef.background}</p>
 <dl className="resume-facts application-stats"><div><dt>Cooking speed</dt><dd>{chef.speed||'1.0×'}</dd></div><div><dt>Growth / level</dt><dd>+{Math.round(chef.growthRate*100)}%</dd></div><div><dt>Max level</dt><dd>{chef.ceiling}</dd></div></dl>
 <div className="hire-area"><button className="primary hire" disabled={full||coins<chef.cost} onClick={e=>{if(e.detail<2)onHire(chef.id);}} aria-label={`Hire ${chef.name} for ${chef.cost} coins${coins<chef.cost?`, ${coins} coins available`:full?', roster full':''}`}>Hire{coins<chef.cost?<span className="money hire-budget"><span className="mini-coin" aria-hidden="true">★</span><span className="current-coins">{coins.toLocaleString()}</span><span className="cost-separator">/</span><span className="required-coins">{chef.cost.toLocaleString()}</span></span>:<Coin amount={chef.cost}/>}</button></div>
 </article>;}

// Scroll position is expressed in card pitches. The spring and drag share the live
// presentation value, so a settling hand can be grabbed and reversed without a jump.
function ApplicationFan({candidates,full,coins,onHire}){
 const viewport=useRef(null),pendingHires=useRef(new Set()),gesture=useRef(null),frame=useRef(0),wheelTimer=useRef(0);
 const motion=useRef({position:0,velocity:0,target:0}),pitch=useRef(250),activeRef=useRef(0);
 const [hireAnnouncement,setHireAnnouncement]=useState('');
 const [position,setPosition]=useState(0),[active,setActive]=useState(0),[cardHeight,setCardHeight]=useState(330),[dragging,setDragging]=useState(false);
 const [entries,setEntries]=useState(()=>candidates.map((candidate,slot)=>({candidate,slot,phase:'enter',serial:0,delay:slot*28})));
 const entrySerial=useRef(0),renderedIds=entries.map(entry=>entry.candidate.id+':'+entry.phase).join('|');
 const count=candidates.length,ids=candidates.map(c=>c.id).join('|');
 const lastIds=useRef([]),lastActive=useRef(null),reduced=useRef(matchMedia('(prefers-reduced-motion: reduce)').matches);
 const max=Math.max(0,count-1),clamp=value=>Math.max(0,Math.min(max,value));
 function paint(value){motion.current.position=value;setPosition(value);}
 function stop(){cancelAnimationFrame(frame.current);frame.current=0;}
 function settle(target,velocity=motion.current.velocity){
  stop();target=clamp(target);activeRef.current=target;setActive(target);motion.current.target=target;motion.current.velocity=velocity;
  if(reduced.current){paint(target);motion.current.velocity=0;return;}
  let previous=performance.now();
  const tick=now=>{const dt=Math.min((now-previous)/1000,1/30);previous=now;const m=motion.current;
   m.velocity+=((m.target-m.position)*240-m.velocity*27)*dt;const next=m.position+m.velocity*dt;
   if(Math.abs(next-m.target)<.0006&&Math.abs(m.velocity)<.008){paint(m.target);m.velocity=0;frame.current=0;return;}
   paint(next);frame.current=requestAnimationFrame(tick);
  };frame.current=requestAnimationFrame(tick);
 }
 function browse(index){gesture.current=null;setDragging(false);settle(index);}
 useLayoutEffect(()=>{
  // Capture presentation before reconciling keyed offers. Departing paper stays
  // alive until its exit completes; survivors flow into the newly centered slot.
  const presentation=new Map([...viewport.current.querySelectorAll('.fan-card')].map(el=>{
   const visual=el.querySelector('.application-card-visual'),style=getComputedStyle(visual),matrix=new DOMMatrixReadOnly(style.transform==='none'?undefined:style.transform);
   return [el.dataset.applicant,{offset:Number(el.style.getPropertyValue('--card-offset')),x:matrix.m41,y:matrix.m42,opacity:Number(style.opacity)}];
  }));
  const previous=lastActive.current,kept=candidates.findIndex(c=>c.id===previous);
  const replacement=!candidates.some(c=>lastIds.current.includes(c.id));
  const next=kept>=0?kept:replacement?0:Math.min(activeRef.current,Math.max(0,count-1));
  const serial=++entrySerial.current,priorIds=lastIds.current,justHired=new Set(pendingHires.current);
  const hireInProgress=justHired.size>0||entries.some(entry=>entry.phase==='hire');
  pendingHires.current.clear();
  setEntries(old=>[
   ...candidates.map((candidate,slot)=>{const before=presentation.get(candidate.id),enter=!priorIds.includes(candidate.id);return {candidate,slot,phase:enter?'enter':'move',serial,delay:enter?slot*28+(hireInProgress?1100:priorIds.length?190:0):hireInProgress?1000:priorIds.some(id=>!candidates.some(c=>c.id===id))?100:0,fromX:before?(before.offset-(slot-next))*pitch.current+before.x:0,fromY:before?.y||0,fromOpacity:before?.opacity??1};}),
   ...old.filter(entry=>(entry.phase==='exit'||entry.phase==='hire')&&!candidates.some(c=>c.id===entry.candidate.id)),
   ...old.filter(entry=>entry.phase!=='exit'&&entry.phase!=='hire'&&!candidates.some(c=>c.id===entry.candidate.id)).map(entry=>{const before=presentation.get(entry.candidate.id);return {...entry,phase:justHired.has(entry.candidate.id)?'hire':'exit',serial,exitOffset:before?.offset??entry.slot-motion.current.position,fromX:before?.x||0,fromY:before?.y||0,fromOpacity:before?.opacity??1};})
  ]);
  stop();gesture.current=null;setDragging(false);activeRef.current=next;setActive(next);motion.current={position:next,velocity:0,target:next};setPosition(next);
  lastIds.current=candidates.map(c=>c.id);lastActive.current=candidates[next]?.id;
 },[ids]);
 useEffect(()=>{lastActive.current=candidates[active]?.id;},[active,ids]);
 useLayoutEffect(()=>{
  const element=viewport.current;if(!element)return;
  const measure=()=>{pitch.current=Math.min(326,element.clientWidth-72)*.88;const heights=[...element.querySelectorAll('.resume-paper')].map(el=>el.offsetHeight);setCardHeight(Math.ceil(Math.max(0,...heights)));};
  const observer=new ResizeObserver(measure);observer.observe(element);element.querySelectorAll('.resume-paper').forEach(el=>observer.observe(el));measure();
  return()=>observer.disconnect();
 },[renderedIds]);
 useEffect(()=>{
  const element=viewport.current;
  const wheel=e=>{if(!count)return;e.preventDefault();stop();const delta=Math.abs(e.deltaX)>Math.abs(e.deltaY)?e.deltaX:e.deltaY;const next=clamp(motion.current.position+delta/pitch.current);paint(next);motion.current.velocity=0;clearTimeout(wheelTimer.current);wheelTimer.current=setTimeout(()=>settle(Math.round(motion.current.position),0),90);};
  const cancel=()=>{if(gesture.current){gesture.current=null;setDragging(false);settle(activeRef.current,0);}};
  const media=matchMedia('(prefers-reduced-motion: reduce)'),change=()=>{reduced.current=media.matches;if(media.matches){stop();paint(motion.current.target);}};
  element.addEventListener('wheel',wheel,{passive:false});window.addEventListener('blur',cancel);media.addEventListener('change',change);
  return()=>{stop();clearTimeout(wheelTimer.current);element.removeEventListener('wheel',wheel);window.removeEventListener('blur',cancel);media.removeEventListener('change',change);};
 },[ids]);
 function start(e){if(e.button!==0||!e.isPrimary||!count)return;stop();clearTimeout(wheelTimer.current);gesture.current={id:e.pointerId,x:e.clientX,y:e.clientY,start:motion.current.position,last:motion.current.position,time:performance.now(),velocity:0,lock:null,target:activeRef.current,button:!!e.target.closest('button'),moved:false};}
 function move(e){const g=gesture.current;if(!g||g.id!==e.pointerId)return;const dx=e.clientX-g.x,dy=e.clientY-g.y;
  if(!g.lock&&Math.hypot(dx,dy)>6){g.lock=Math.abs(dx)>=Math.abs(dy)?'horizontal':'vertical';g.moved=true;if(g.lock==='horizontal'){e.currentTarget.setPointerCapture(e.pointerId);setDragging(true);}}
  if(g.lock!=='horizontal')return;e.preventDefault();let next=g.start-dx/pitch.current;
  if(next<0)next=next/(1+Math.abs(next)*3)*.42;else if(next>max){const beyond=next-max;next=max+beyond/(1+beyond*3)*.42;}
  else next-=Math.sin(next*Math.PI*2)*.024; // A small magnetic well at each card.
  const now=performance.now(),dt=Math.max(1,now-g.time)/1000;g.velocity=g.velocity*.45+((next-g.last)/dt)*.55;g.last=next;g.time=now;paint(next);
 }
 function finish(e,cancel=false){const g=gesture.current;if(!g||g.id!==e.pointerId)return;gesture.current=null;setDragging(false);
  if(cancel||g.lock==='vertical'){settle(g.target,0);return;}
  if(g.lock==='horizontal'){const velocity=performance.now()-g.time>100?0:Math.max(-5,Math.min(5,g.velocity));const projected=motion.current.position+velocity*.14;settle(Math.round(clamp(projected)),velocity);return;}
  settle(activeRef.current,0);
 }
 return <section className={`application-fan ${dragging?'is-dragging':''}`} ref={viewport} aria-label="Applicant applications" aria-roledescription="carousel" tabIndex={0} style={{'--fan-height':`${cardHeight+48}px`}} data-active-applicant={candidates[active]?.id||''}
  onKeyDown={e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();browse(e.key==='Home'?0:e.key==='End'?max:activeRef.current+(e.key==='ArrowRight'?1:-1));}}}
  onPointerDown={start} onPointerMove={move} onPointerUp={e=>finish(e)} onPointerCancel={e=>finish(e,true)} onLostPointerCapture={e=>{if(e.target===e.currentTarget)finish(e,true);}}
  onClickCapture={e=>{if(dragging||Math.abs(motion.current.position-motion.current.target)>.025){e.preventDefault();e.stopPropagation();}}}>
  <span className="sr-only" role="status">{hireAnnouncement}</span><span className="sr-only" aria-live="polite">{candidates[active]?`${candidates[active].name}. Use left and right arrow keys to browse.`:'No applications left.'}</span>
  {entries.map(entry=>{const candidate=entry.candidate,i=entry.slot,exiting=entry.phase==='exit'||entry.phase==='hire',hiring=entry.phase==='hire';const distance=exiting?entry.exitOffset:i-position,depth=Math.min(1,Math.abs(distance)),current=!exiting&&i===active;return <div key={candidate.id} className={`fan-card ${current?'is-active':''} ${exiting?'is-exiting':''} ${hiring?'is-hiring':''}`} data-applicant={candidate.id} aria-hidden={!current} style={{'--card-offset':distance,'--card-tilt':`${Math.max(-14,Math.min(14,distance*9))}deg`,'--card-lift':`${depth*20}px`,'--card-scale':1-depth*.045,zIndex:(exiting?20:10)-Math.round(Math.abs(distance)*2)}}
   onClick={()=>{if(!current&&!exiting)browse(i);}}><ApplicationCardSurface entry={entry} onExit={(id,serial)=>setEntries(current=>current.filter(item=>!(item.candidate.id===id&&(item.phase==='exit'||item.phase==='hire')&&item.serial===serial)))}><div inert={!current}><Resume chef={candidate} full={full} coins={coins} onHire={id=>{if(Math.abs(motion.current.position-i)<.025&&!full&&coins>=candidate.cost){pendingHires.current.add(id);setHireAnnouncement(`${candidate.name} hired.`);onHire(id);}}} tabIndex={current?0:-1}/></div></ApplicationCardSurface></div>;})}
  {!count&&<article className="resume-paper empty-paper"><Icon name="check"/><h2>No applications left</h2><p>Your new chefs are waiting in the roster.</p><p>Refresh to meet new applicants.</p></article>}
 </section>;
}
function ApplicantPanel({model,update,onClose,notify,clearNotice}){
 const [now,setNow]=useState(Date.now),full=model.staff.length>=capacity;
 const seconds=Math.max(0,Math.ceil((model.deadline-now)/1000));
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),500);return()=>clearInterval(timer);},[]);
 function hire(id){clearNotice?.();update(s=>{const c=byId(id);if(!s.pool.includes(id)||s.staff.length>=capacity||s.coins<c.cost)return s;return {...s,coins:s.coins-c.cost,staff:[...s.staff,{...c,assigned:false,cell:null,recipe:null,isNew:true}],pool:s.pool.filter(x=>x!==id)};});}
 function refresh(){const refreshedAt=Date.now();if(refreshedAt<model.deadline)return;setNow(refreshedAt);update(s=>{if(refreshedAt<s.deadline)return s;const pool=[...(s.generation%2?applicants:refreshedApplicants),...(s.generation%2?refreshedApplicants:applicants)].filter(c=>!s.staff.some(x=>x.id===c.id)).slice(0,3).map(c=>c.id);return {...s,pool,generation:s.generation+1,deadline:refreshedAt+cooldown};});notify('Applications refreshed. Your staff and coins are unchanged.');}
 return <div className="panel applicants-panel" role="dialog" aria-modal="true" aria-labelledby="applicant-title">
  <header className="panel-header"><div><h1 id="applicant-title">Applicants</h1><p>Staff <strong>{model.staff.length} / {capacity}</strong><span className="dot">·</span><span className={full?'roster-full':''}>{full?'Roster full':`${capacity-model.staff.length} spaces available`}</span></p></div><Close onClick={onClose}/></header>
  <ApplicationFan candidates={model.pool.map(byId)} full={full} coins={model.coins} onHire={hire}/>
  <footer className="refresh-row"><div><strong>Fresh faces?</strong><p>{seconds?`Available in ${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')}`:'Free · replaces remaining offers'}</p></div><button className="secondary refresh" onClick={refresh} disabled={seconds>0} aria-label="Refresh applications"><Icon name="refresh"/>Refresh</button></footer><div className="panel-waves" aria-hidden="true"/>
 </div>;
}
function DetailPanel({chef,onClose,onPlace,onRecipes}){return <section className="panel detail-panel" role="dialog" aria-modal="true" aria-labelledby="chef-title"><ChefPortrait chefId={chef.id} bust className="detail-head"/><header className="panel-header"><div><h1 id="chef-title">{given(chef)}</h1><p>{chef.assigned?chef.recipe?'Preparing a recipe':'Assigned · idle':'Unassigned staff'}</p></div><Close label="Close chef details" onClick={onClose}/></header><div className="detail-body"><h2>{chef.role}</h2><p>{chef.background}</p><p className="strength"><span>Strength</span><strong>{chef.trait}</strong></p><dl className="resume-facts"><div><dt>Current level</dt><dd>{chef.level} / {chef.ceiling}</dd></div><div><dt>Growth / level</dt><dd>+{Math.round(chef.growthRate*100)}%</dd></div><div><dt>Cooking speed</dt><dd>{chef.speed||'1.0×'}</dd></div><div className="reach"><dt>Highest reachable tier</dt><dd><Plate tier={chef.tier}/><span>{chef.tier}<small>at Level {tierLevel[chef.tier]}</small></span></dd></div></dl><p className="detail-note">{chef.assigned?'Choose a recipe explicitly to begin preparation.':'Drag this chef from the roster onto an empty cell beside a belt.'}</p></div><footer className="detail-footer"><button className="primary" onClick={chef.assigned?onRecipes:onPlace}>{chef.assigned?'Recipes':'Place in restaurant'}{!chef.assigned&&<Icon name="arrow"/>}</button></footer><div className="panel-waves"/></section>;}
function App(){
 const [model,setModel]=useState(restore),[review,setReview]=useState(initial),[mode,setMode]=useState(initial==='people'?'edit':'live'),[tray,setTray]=useState(true),[overlay,setOverlay]=useState(['roster','people','gallery'].includes(initial)?null:'applicants'),[selected,setSelected]=useState('omar'),[recipeState,setRecipeState]=useState({selectedRecipe:null,currentRecipe:null,seenRecipes:[]}),[toast,setToast]=useState(''),[drag,setDrag]=useState(null),[placement,setPlacement]=useState(null);
 const scene=useRef(null),reviewEpoch=useRef(0),pointer=useRef(null),suppressClick=useRef(false),lastFocus=useRef(null),modal=useRef(null),closing=useRef(null),timer=useRef(null),strip=useRef(null),trayScroll=useRef(0);
 const chef=model.staff.find(c=>c.id===selected)||model.staff[0],gallery=review==='gallery';
 const markSeen=useCallback(ids=>setModel(s=>{if(!s.staff.some(c=>c.isNew&&ids.includes(c.id)))return s;return {...s,staff:s.staff.map(c=>ids.includes(c.id)?{...c,isNew:false}:c)};}),[]);
 useNewChefNotices({staff:model.staff,strip,enabled:!overlay&&tray&&!gallery,onSeen:markSeen});
 useEffect(()=>{try{localStorage.setItem(key,JSON.stringify(model));}catch{}},[model]);
 useEffect(()=>()=>clearTimeout(timer.current),[]);
 useEffect(()=>{const cancel=()=>{if(pointer.current){suppressClick.current=true;pointer.current=null;setDrag(null);}};window.addEventListener('blur',cancel);return()=>window.removeEventListener('blur',cancel);},[]);
 const notify=message=>{setToast(message);clearTimeout(timer.current);timer.current=setTimeout(()=>setToast(''),4500);};
 function open(kind,id){if(kind==='details'&&id)markSeen([id]);lastFocus.current=document.activeElement;if(strip.current)trayScroll.current=strip.current.scrollLeft;if(id)setSelected(id);if(kind==='recipes'){const c=model.staff.find(s=>s.id===id)||chef;setRecipeState({selectedRecipe:null,currentRecipe:c.recipe,seenRecipes:[]});}setOverlay(kind);}
 function close(){
  const finish=()=>{setOverlay(null);requestAnimationFrame(()=>{if(strip.current)strip.current.scrollLeft=trayScroll.current;lastFocus.current?.focus({preventScroll:true});});};
  const panel=modal.current?.querySelector('.applicants-panel');
  if(!panel){finish();return;}if(closing.current)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,token=Symbol('close');
  const animation=panel.animate(reduced?[{opacity:1},{opacity:0}]:[{opacity:1,transform:'translateY(0) scale(1)'},{opacity:0,transform:'translateY(12px) scale(.99)'}],{duration:reduced?80:170,easing:'cubic-bezier(.4,0,1,1)',fill:'both'});
  panel.inert=true;closing.current={token,animation};
  animation.finished.then(()=>{if(closing.current?.token===token){closing.current=null;finish();}}).catch(()=>{});
 }

 useEffect(()=>{for(const el of scene.current.querySelectorAll('.world,.hiring-hud,.placement-grid,.staff-dock,.staff-launch,.placement-hint'))el.inert=!!overlay;},[overlay,mode,tray]);
 useEffect(()=>{if(overlay)requestAnimationFrame(()=>modal.current?.querySelector('button:not(:disabled)')?.focus({preventScroll:true}));},[overlay]);
 useEffect(()=>{function keydown(e){if(e.key==='Escape'){if(pointer.current||drag||placement){suppressClick.current=true;pointer.current=null;setDrag(null);setPlacement(null);notify('Placement cancelled. Your chef is still in the roster.');}else if(overlay)close();else if(tray&&mode==='live')setTray(false);}if(e.key==='Tab'&&overlay){const targets=[...modal.current.querySelectorAll('button:not(:disabled),[tabindex="0"]')].filter(el=>el.getClientRects().length);const first=targets[0],last=targets.at(-1);if(e.shiftKey&&(document.activeElement===first||!modal.current.contains(document.activeElement))){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}}document.addEventListener('keydown',keydown,true);return()=>document.removeEventListener('keydown',keydown,true);},[overlay,tray,mode,drag,placement]);
 function reset(next=review){reviewEpoch.current++;if(closing.current){closing.current.animation.cancel();closing.current=null;}const priorPanel=modal.current?.querySelector('.applicants-panel');if(priorPanel)priorPanel.inert=false;setReview(next);setModel(fixture(next));setMode(next==='people'?'edit':'live');setTray(true);setSelected('omar');setOverlay(['roster','people','gallery'].includes(next)?null:'applicants');setDrag(null);setPlacement(null);setToast('');history.replaceState(null,'',`?state=${next}`);}
 function validCell(cell,id){return Number.isInteger(cell)&&cell>=0&&cell<42&&!beltCells.includes(cell)&&!model.staff.some(c=>c.id!==id&&c.assigned&&c.cell===cell)&&beltCells.some(b=>Math.abs(b-cell)===6||(Math.floor(b/6)===Math.floor(cell/6)&&Math.abs(b-cell)===1));}
 function hit(x,y){const trayBounds=scene.current.querySelector('.staff-dock')?.getBoundingClientRect();if(trayBounds&&y>=trayBounds.top)return null;const grid=scene.current.querySelector('.placement-grid').getBoundingClientRect();if(x<grid.x||y<grid.y||x>=grid.right||y>=grid.bottom)return null;return Math.floor((y-grid.y)/(grid.width/6))*6+Math.floor((x-grid.x)/(grid.width/6));}
 function place(id,cell){if(!validCell(cell,id)){notify('Choose an empty cell beside a belt.');return;}setModel(s=>({...s,staff:s.staff.map(c=>c.id===id?{...c,assigned:true,cell,recipe:null,isNew:false}:c)}));setSelected(id);setPlacement(null);setDrag(null);setToast('');setRecipeState({selectedRecipe:null,currentRecipe:null,seenRecipes:[]});lastFocus.current=scene.current.querySelector(`[data-chef="${id}"]`);setOverlay('recipes');}
 function start(e,c){if(e.button!==0)return;suppressClick.current=false;pointer.current={id:e.pointerId,chef:c,x:e.clientX,y:e.clientY,scroll:strip.current.scrollLeft,lock:null};e.currentTarget.setPointerCapture(e.pointerId);}
 function move(e){const p=pointer.current;if(!p||p.id!==e.pointerId)return;const dx=e.clientX-p.x,dy=e.clientY-p.y;if(!p.lock&&Math.hypot(dx,dy)>10)p.lock=Math.abs(dx)>Math.abs(dy)?'scroll':'place';if(p.lock==='scroll'){strip.current.scrollLeft=p.scroll-dx;return;}if(p.lock==='place'&&!p.chef.assigned){e.preventDefault();const b=scene.current.getBoundingClientRect(),cell=hit(e.clientX,e.clientY);setDrag({id:p.chef.id,x:e.clientX-b.x,y:e.clientY-b.y,cell,valid:validCell(cell,p.chef.id)});}}
 function finish(e,cancel=false){const p=pointer.current;if(!p||p.id!==e.pointerId)return;pointer.current=null;setDrag(null);suppressClick.current=!!p.lock;if(p.lock==='place'&&!p.chef.assigned&&!cancel){const cell=hit(e.clientX,e.clientY);if(validCell(cell,p.chef.id))place(p.chef.id,cell);else notify('Chef returned to the roster. Drop beside a belt.');}}
 return <div className="review-shell"><nav className="review-toolbar" aria-label="Prototype review controls"><a href="../../#staff-applicants" title="Open wireframe catalog">Sushi Loop <span>· #16</span></a><label><span className="sr-only">Review state</span><select value={review} onChange={e=>reset(e.target.value)}>{Object.entries(names).map(([k,n])=><option key={k} value={k}>{n}</option>)}</select></label><button onClick={()=>reset()}>Reset</button></nav>
 <main className={`scene hiring-scene ${gallery?'gallery-scene':''}`} ref={scene} data-mode={mode} aria-label="Sushi Loop staff hiring prototype">
 {gallery?<Gallery model={model} reset={reset}/>:<>
 <div className="world" aria-label="Restaurant floor"><img className="world-sky" src={dockArt('restaurant-sky')} alt=""/><div className="blue-wall"/><img className="world-wall" src={dockArt('restaurant-wall')} alt=""/><div className="world-floor"><img src={dockArt('restaurant-floor')} alt=""/></div></div>
 <header className="hiring-hud"><div className="coin-pill"><Coin amount={model.coins}/></div><button className={mode==='edit'?'secondary':'quiet-mode'} onClick={()=>{setMode('edit');setTray(true);}}><Icon name="edit"/>{mode==='edit'?'Editing':'Edit'}</button><button className={mode==='live'?'live-pill':'primary'} onClick={()=>{setMode('live');setTray(true);}}><Icon name="play"/>Live</button></header>
 <div className={`placement-grid ${drag||placement?'placing':''}`} aria-label="Restaurant placement grid">{Array.from({length:42},(_,cell)=><div key={cell} className={`world-cell ${beltCells.includes(cell)?'belt-cell':''} ${(drag||placement)&&validCell(cell,drag?.id||placement)?'valid-cell':''} ${drag?.cell===cell?'hover-cell':''}`}>
 {beltCells.includes(cell)&&<img className="belt-sprite" src={art('world-'+([13,31].includes(cell)?'belt-start-e':[16,34].includes(cell)?'belt-end-e':'belt-straight-e'))} alt="Conveyor belt"/>}
 {placement&&validCell(cell,placement)&&<button className="cell-target" aria-label={`Place ${given(byId(placement))} beside belt, cell ${cell}`} onClick={()=>place(placement,cell)}/>}
 {model.staff.filter(c=>c.assigned&&c.cell===cell).map(c=><button className="world-chef" key={c.id} aria-label={`${given(c)}, ${c.recipe?'preparing':'idle'}`} onClick={()=>open('recipes',c.id)}><img src={art('world-'+c.id)} alt=""/>{!c.recipe&&<span className="idle-badge">Idle</span>}</button>)}
 </div>)}</div>
 {!tray&&<button className="staff-launch secondary" onClick={()=>setTray(true)}><Icon name="people"/>Staff</button>}
 {tray&&<section className={`staff-dock ${mode==='edit'?'edit-dock':'live-dock'}`} aria-label={mode==='edit'?'People inventory':'Staff roster'}>
 <div className="roster-cap"><h2>{mode==='edit'?'People':'Staff'} <span>{model.staff.length} / {capacity}</span></h2><button className="secondary applicants-launch" onClick={()=>open('applicants')}><Icon name="people"/>Applicants</button>{mode==='live'&&<Close label="Close staff tray" onClick={()=>setTray(false)}/>}</div>
 {mode==='edit'&&<nav className="dock-tabs" aria-label="Editor categories"><button className="selected" aria-pressed="true"><Icon name="people"/>People</button><button onClick={()=>notify('Layout editing is outside this applicant prototype.')}><Icon name="layout"/>Layout</button><button onClick={()=>notify('Floor editing is outside this applicant prototype.')}><Icon name="floor"/>Floor</button></nav>}
 <div className="roster-scroll" ref={strip}><div className="roster-row">{model.staff.map(c=><Photo chef={c} key={c.id} data-chef={c.id} onPointerDown={e=>start(e,c)} onPointerMove={move} onPointerUp={e=>finish(e)} onPointerCancel={e=>finish(e,true)} onLostPointerCapture={e=>finish(e,true)} onClick={()=>{if(suppressClick.current){suppressClick.current=false;return;}open('details',c.id);}}/>)}</div></div><div className="dock-waves" aria-hidden="true"/></section>}
 {placement&&<div className="placement-hint" role="status">Choose a highlighted cell beside a belt.<button className="round" aria-label="Cancel placement" onClick={()=>setPlacement(null)}><Icon name="close"/></button></div>}
 {drag&&<div className={`chef-ghost ${drag.valid?'drop-ok':''}`} style={{left:drag.x,top:drag.y}} aria-hidden="true"><img src={art('world-'+drag.id)} alt=""/><span>{drag.valid?'Place here':'Beside a belt'}</span></div>}
 {overlay&&<div className="modal-host" ref={modal}><div className="scrim"/>{overlay==='applicants'?<ApplicantPanel key={`${review}-${reviewEpoch.current}`} model={model} update={setModel} onClose={close} notify={notify} clearNotice={()=>setToast('')}/>:overlay==='details'?<DetailPanel chef={chef} onClose={close} onPlace={()=>{close();setPlacement(chef.id);notify(`Choose an empty cell beside a belt for ${given(chef)}.`);}} onRecipes={()=>open('recipes',chef.id)}/>:<MapleRecipePanel state={recipeState} chefName={given(chef)} chefId={chef.id} level={chef.level} onInspect={id=>setRecipeState(s=>({...s,selectedRecipe:id,seenRecipes:[...s.seenRecipes,id]}))} onClose={close} onPrepare={()=>{if(!recipeState.selectedRecipe)return;setModel(s=>({...s,staff:s.staff.map(c=>c.id===chef.id?{...c,recipe:recipeState.selectedRecipe}:c)}));notify(`${given(chef)} is now preparing.`);close();}}/>}</div>}
 </>}
 <p className={`notice ${toast?'visible':''}`} role="status" aria-live="polite">{toast}</p>
 </main></div>;
}
function HireGalleryPreview(){
 const [playing,setPlaying]=useState(false),[serial,setSerial]=useState(0),[isNew,setIsNew]=useState(true);
 const play=()=>{setSerial(value=>value+1);setPlaying(true);};
 return <><section className="hire-gallery-demo"><h2>Hired confirmation</h2><div className="hire-gallery-paper"><ApplicationCardSurface entry={{candidate:applicants[0],serial,phase:playing?'hire':'move'}} onExit={()=>{setSerial(value=>value+1);setPlaying(false);}}><Resume chef={applicants[0]} full={false} coins={1240} onHire={play}/></ApplicationCardSurface></div><button className="secondary" onClick={play}>Play hire animation</button></section><section><h2>New chef indicator</h2><div className="gallery-photos"><Photo chef={{...applicants[0],assigned:false,isNew}} onClick={()=>setIsNew(false)}/></div><button className="secondary" onClick={()=>setIsNew(true)}>Show new-chef dot</button></section></>;
}
function Gallery({model,reset}){return <div className="shared-gallery"><header><p className="eyebrow">Shared components · Issue 16</p><h1>Staff & applicants</h1><p>The same components, artwork and live type as the scene.</p></header><section><h2>Applicant résumés</h2><ApplicationFan candidates={applicants} coins={1240} full={false} onHire={()=>reset('available')}/></section><HireGalleryPreview/><section><h2>Insufficient coins</h2><Resume chef={applicants[0]} coins={60} full={false} onHire={()=>{}}/></section><section><h2>Hire states</h2><button className="primary">Hire<Coin amount={180}/></button><button className="primary pressed-example">Hire<Coin amount={180}/></button><button className="primary" disabled>Hire<Coin amount={180}/></button><p>Normal · pressed · disabled</p></section><section><h2>Shared roster</h2><div className="gallery-photos">{model.staff.map(c=><Photo key={c.id} chef={c} onClick={()=>reset('roster')}/>)}</div></section><section><h2>Reachable plate tiers</h2><div className="gallery-tiers">{Object.keys(tierLevel).map(t=><div key={t}><Plate tier={t}/><strong>{t}</strong><small>Level {tierLevel[t]}</small></div>)}</div></section><section><h2>Try the complete scene</h2>{['available','full','poor','roster','people'].map(s=><button className="secondary" key={s} onClick={()=>reset(s)}>{names[s]}</button>)}</section></div>;}
createRoot(document.getElementById('root')).render(<App/>);
