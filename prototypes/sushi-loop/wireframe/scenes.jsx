import React from 'react';
import { Target, Icon, Money, Character } from './common.jsx';
import { RestaurantHud, EditorControls, Dock, HullMeter, UpgradeCard, SalvageReceipt, ComponentGallery } from './components.jsx';
import { roster, chefAssigned } from './fixtures.js';
import { RosterTray } from './staff-tray.jsx';
import { PaperPage } from './paper-page.jsx';

function Nav({ children, story = 'restaurant-live', className = '', data = {}, ...rest }) {
  return <Target action="navigate" data={{story,...data}} className={className} {...rest}>{children}</Target>;
}
function Header({ title, subtitle, balance, actions }) { return <header className="scene-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{balance}{actions}</header>; }
function Entry({ panel, active = false }) { return <div className={`customer-entry ${active ? 'active' : ''}`}><span className="entry-door" /><span>Entry {panel+1}</span>{active ? <small>Customer access</small> : <small><Icon name="lock" /> Future access</small>}</div>; }

function Garbage({ panel, state, full = false }) {
  const partial = state.demoPatchCleared && panel === 1;
  return <div className={`garbage-field ${full ? 'plan-garbage' : ''} ${partial ? 'partial-clearance' : ''}`} aria-label="Garbage awaiting clearance"><span className="debris d1">▧</span><span className="debris d2">▱</span><span className="debris d3">▧</span><span className="debris d4">▱</span><p className="garbage-label">Garbage to clear</p><Nav story="expansion" className={`clearance-target ${panel === 2 ? 'later-patch' : ''}`}><Icon name="trash" /><strong>{partial ? 'Next patch' : 'Clear patch'}</strong><small>Expand this way →</small></Nav></div>;
}

function SelectedFootprint({ state }) {
  return <div className="selected-footprint"><Target action="select-object" data={{value:'chair'}} className="chair-target object-selected" title="Selected chair"><span className="mini-chair" aria-hidden="true" style={{transform:`rotate(${Number(state.rotation || 0)}deg)`}}>⊓</span></Target><div className="object-tools"><Target action="rotate" data={{value:'chair'}} className="icon-control" title="Rotate selected chair"><Icon name="rotate" /></Target><Target action="remove" data={{value:'chair'}} className="icon-control" title="Remove selected chair"><Icon name="trash" /></Target></div></div>;
}

function FloorPanels({ state, map = false }) {
  const expanded = state.restaurantExpanded || ['expanded','charging'].includes(state._variant) || state.demoPatchCleared;
  const previewChef = roster(state).find(chef => chef.id === state.rosterPlacement?.chefId);
  const showPreview = previewChef && chefAssigned(state, previewChef);
  return [0,1,2].map(panel=><section key={panel} className={`floor-panel ${panel === 0 || (panel === 1 && expanded) ? 'cleared' : 'uncleared'} ${state.painted && panel === 0 ? 'painted-floor' : ''}`} data-floor-panel={panel} aria-label={`Restaurant panel ${panel+1}`}>
    {map && <span className="panel-name">Panel {panel+1} · {panel === 0 ? 'usable at start' : 'future expansion'}</span>}
    <Entry panel={panel} active={panel === 0 || (panel === 1 && expanded)} />
    {panel === 0 && map && <div className="starter-label"><strong>Starter restaurant</strong><span>Cleared, usable floor</span></div>}
    {panel === 0 && !map && state._variant === 'selected' && <SelectedFootprint state={state} />}
    {panel === 0 && !map && showPreview && <Target action="navigate" data={{story:'staff-detail',value:previewChef.id}} className="roster-placed-chef" title={`Inspect ${previewChef.name}`} style={{left:`${state.rosterPlacement.x*100}%`,top:`${state.rosterPlacement.y*100}%`}}><Character name={previewChef.name} /></Target>}
    {panel > 0 && (panel === 2 || !expanded) && <Garbage panel={panel} state={state} full={map} />}
    {panel === 1 && <Dock state={state} locked={!map && !expanded} future={map} />}
    {map && <span className="viewport-guide">Viewport guide · no dividing wall</span>}
  </section>);
}

function FloorPlan({ state }) {
  return <div className="floorplan-scene"><Header title="Full restaurant floor plan" subtitle="Three portrait panels · one continuous room" actions={<Nav story="shop" className="hud-action plan-shop-shortcut"><Icon name="basket"/><strong>Shop</strong></Nav>}/><div className="plan-scroll" tabIndex={0} aria-label="Scroll full restaurant plan"><div className="floor-plan-world"><FloorPanels state={state} map /></div></div><div className="plan-legend"><span><i className="legend-clear" />Usable at start</span><span><i className="legend-garbage" />Garbage patches</span><span><i className="legend-guide" />Viewport guides</span><span>Shop is a floating HUD button · no floor footprint</span></div><div className="scene-footer"><Nav className="primary-action"><Icon name="play" /><span>Open restaurant view</span></Nav><Nav story="expansion"><Icon name="trash" /><span>Preview clearance popup</span></Nav></div></div>;
}

function Restaurant({ state }) {
  const edit = ['edit','floor','selected'].includes(state._variant);
  return <div className={`phone-scene restaurant-scene ${edit ? 'edit-scene' : ''}`}><div className="restaurant-viewport" data-pan-scroll tabIndex={0} aria-label="Pan restaurant floor"><div className="restaurant-world"><FloorPanels state={state} /></div></div><RestaurantHud state={state}/>{!edit && <div className="restaurant-actions"><Nav story="restaurant-edit" className="hud-action"><Icon name="edit" /><span>Edit</span></Nav><Nav story="staff-roster" className="hud-action"><Icon name="staff" /><span>Staff</span></Nav></div>}{edit && <EditorControls state={state} />}{state.placement && !['omar','chef'].includes(state.placement) && <div className="placement-preview"><span><Icon name="layout" /> {state.placement === 'belt' ? 'Belt tile' : state.placement === 'chair' ? 'Chair' : 'Plant'}</span><Target action="finish-placement" className="place-here">Place here</Target><Target action="cancel-placement" className="icon-control" title="Cancel placement preview"><Icon name="close" /></Target></div>}</div>;
}

function ShopCard({ label, description, art, value, price, qty, state, poor }) {
  return <article className="catalog-card"><div className="catalog-art">{art}</div><div><h3>{label}</h3><p>{description}</p>{qty && <small>{qty}</small>}{state.purchasedItems?.includes(value) && <small className="added-marker">✓ Added to inventory</small>}</div><Target action="purchase" data={{value}} className="buy-action" title={`Buy ${label}`} disabled={poor}><Money amount={price} /></Target></article>;
}
function PaperRestaurant({ state }) {
  return <div className="restaurant-viewport" data-pan-scroll><div className="restaurant-world"><FloorPanels state={{...state,_variant:state.paperBackdropVariant || 'live'}} /></div></div>;
}
function Shop({ state }) {
  const owned = state._variant === 'owned' || state.purchasedItems?.includes('blue-wave');
  const poor = state._variant === 'unaffordable';
  return <div className="phone-scene shop-scene"><PaperPage title="Shop" balance={<Money amount={poor ? 24 : 1240} />} background={<PaperRestaurant state={state}/>}><div className="catalog-content"><ShopCard label="Belt tile" description="Connect your conveyor route." art={<span className="mini-belt">→</span>} value="belt" price={40} state={state} poor={poor} /><ShopCard label="Chair" description="A simple seat beside the belt." art={<span className="mini-chair">⊓</span>} value="chair" price={80} state={state} poor={poor} /><ShopCard label="Comfy chair" description="An appearance upgrade." art={<span className="mini-chair fancy">⊓</span>} value="comfy-chair" price={320} qty="2 remaining" state={state} poor={poor} /><article className="catalog-card floor-offer"><div className="catalog-art"><span className="floor-sample wave" /></div><div><h3>Blue Wave</h3><p>Floor style</p></div>{owned ? <span className="owned-state"><Icon name="check" />Owned</span> : <Target action="purchase" data={{value:'blue-wave'}} className="buy-action" title="Buy Blue Wave" disabled={poor}><Money amount={600} /></Target>}</article></div></PaperPage></div>;
}

function Staff({ state }) {
  return <div className="phone-scene restaurant-scene staff-scene"><div className="restaurant-viewport" data-pan-scroll tabIndex={0} aria-label="Pan restaurant floor"><div className="restaurant-world"><FloorPanels state={state} /></div></div><RestaurantHud state={state} /><RosterTray state={state} /></div>;
}

const upgradeTracks = [{id:'hull',name:'Hull',unit:'Maximum hull',price:90,icon:'submarine'},{id:'harpoon',name:'Harpoon',unit:'Reeling strength',price:110,icon:'harpoon'},{id:'collector',name:'Collector',unit:'Pickup reach',price:80,icon:'salvage'}];
function exampleStat(track, steps = 0) { return track.id === 'hull' ? String(100+25*steps) : track.id === 'harpoon' ? `${(1+.2*steps).toFixed(1)}×` : `${1+.5*steps} ${steps === 0 ? 'cell' : 'cells'}`; }
function Workshop({ state }) {
  const max = state._variant === 'max';
  const poor = state._variant === 'unaffordable';
  return <div className="phone-scene workshop-scene"><PaperPage title="Workshop" balance={<Money kind="salvage" amount={poor ? 18 : 180} />} background={<PaperRestaurant state={state}/>}><div className="ship-preview"><Icon name="submarine" /></div><div className="catalog-content">{upgradeTracks.map(track=>{
    const steps = Number(state.upgradeLevels?.[track.id] || 0);
    const capped = max && track.id === 'hull';
    return <UpgradeCard key={track.id} track={{...track,current:capped ? '200' : exampleStat(track,steps),next:exampleStat(track,steps+1)}} level={capped ? 5 : 1+steps} max={capped} poor={poor} selected={state.selectedUpgrade === track.id} />;
  })}</div></PaperPage></div>;
}

function SeaDecor() { return <><div className="sea-dashes"><i /><i /><i /><i /></div><div className="sea-floor"><span>⌁</span><span>♧</span><span>⌁</span><span>♧</span></div><span className="salvage-fragment sf-one">◇</span><span className="salvage-fragment sf-two">◇</span></>; }
function Creature({ danger = false, pursuit = false }) { return <div className={`sea-creature ${danger ? 'escaping' : ''}`}><div className="creature-body"><span>•</span><i /></div><small>{pursuit ? 'Hooked creature' : 'Shooting window'}</small></div>; }
function ExpeditionStart() {
  return <div className="phone-scene ocean-scene preparation-scene"><SeaDecor /><h2 className="underwater-title">Ready to depart</h2><Nav className="prep-airlock"><span className="airlock"><Icon name="arrow-left" /><b>Sushi Bar</b><small>Return before departure</small></span></Nav><div className="prep-sub"><Icon name="submarine" /><span className="battery-ready">Battery full</span></div><div className="start-action"><Nav story="expedition-travel" className="primary-action"><Icon name="play" /><strong>Start</strong></Nav><p>Begin a new expedition</p></div></div>;
}
function Expedition({ state }) {
  const variant = state._variant;
  const paused = ['pause','return','resume'].includes(variant);
  const backdrop = paused ? String(state.expeditionBackdrop || 'pursuit').replace(/^expedition-/,'') : variant;
  const encounter = ['encounter','pursuit','danger'].includes(backdrop);
  const pursuit = ['pursuit','danger'].includes(backdrop);
  const danger = backdrop === 'danger';
  return <div className={`phone-scene ocean-scene expedition-scene ${danger ? 'danger-scene' : ''} ${paused ? 'paused-scene' : ''}`}><SeaDecor /><div className="expedition-hud"><HullMeter percent={danger ? 22 : 78} danger={danger} /><div className="run-salvage"><Money kind="salvage" amount={36} /></div><Nav story="expedition-pause" className="icon-control pause-control"><Icon name="pause" /><span className="sr-only">Pause</span></Nav></div>{encounter && <div className="creature-meter"><span>Eel · {pursuit ? 'Reeling resistance' : 'Creature resistance'}</span><i><b style={{width:`${pursuit ? 46 : 100}%`}} /></i></div>}{!paused && <div className="expedition-world-label">{variant === 'travel' ? 'Travelling' : danger ? 'Cable at its limit' : pursuit ? 'Pursuit' : 'Encounter'}</div>}{pursuit && <><div className={`following-strip ${danger ? 'taut' : ''}`}><span>Following range</span></div><div className={`harpoon-cable ${danger ? 'frayed' : ''}`} /></>}{danger && <div className="attack-column"><span>Attack warning</span></div>}{encounter && <Creature danger={danger} pursuit={pursuit} />}<div className="expedition-ship"><Icon name="submarine" /><span>You</span></div>{encounter && !pursuit && <Nav story="expedition-pursuit" className="harpoon-control" disabled={paused}><Icon name="harpoon" /><strong>Harpoon</strong></Nav>}{variant === 'resume' && <div className="resume-countdown" role="status"><strong>3</strong><span>Returning to ship...</span></div>}{!paused && <p className="steering-hint">Drag to steer · illustrated interaction area</p>}</div>;
}
function Catch({ state }) {
  const repeat = state._variant === 'repeat';
  return <div className="phone-scene ocean-scene catch-scene"><SeaDecor /><div className="catch-focus"><span className="catch-rings" /><div className="sea-creature"><div className="creature-body"><span>•</span><i /></div></div><h2>Catch secured</h2><p>{repeat ? 'A familiar creature' : 'First discovery'}</p>{repeat && <span className="repeat-reward"><Money kind="salvage" amount={18} /><small>Repeat-catch bonus</small></span>}</div></div>;
}
function Results({ state }) {
  const early = state._variant === 'early';
  const hull = state._variant === 'hull';
  const completed = !early && !hull;
  return <div className={`phone-scene results-scene ${completed ? 'complete-result' : early ? 'early-result' : 'hull-result'}`}><div className="result-background" aria-hidden="true"><Icon name="submarine" /><span>{completed ? '✦' : early ? '⌁' : '⚒'}</span></div><div className="result-content"><span className="outcome-icon"><Icon name={completed ? 'check' : early ? 'arrow-left' : 'submarine'} /></span><h2>{completed ? 'Expedition complete' : early ? 'Returned early' : 'Hull depleted'}</h2><p>{completed ? 'Your route is complete.' : early ? 'Collected salvage stays with you.' : 'The expedition ended. Collected salvage is safe.'}</p><SalvageReceipt completed={completed} repeatCatch={state.repeatCatch === true} /><Nav className="primary-action"><Icon name="arrow-left" /><span>Restaurant</span></Nav><small className="recharge-note">Submarine recharge begins after the run.</small></div></div>;
}

export function Scene({ story, state = {} }) {
  const sceneState = {...state,_variant:story.variant || 'live'};
  switch (story.scene) {
    case 'component': return <ComponentGallery story={story} state={sceneState} paperBackground={story.component === 'paper-page' ? <PaperRestaurant state={sceneState} /> : undefined} />;
    case 'floor-plan': return <FloorPlan state={sceneState} />;
    case 'restaurant': return <Restaurant state={sceneState} />;
    case 'shop': return <Shop state={sceneState} />;
    case 'staff': return <Staff state={sceneState} />;
    case 'workshop': return <Workshop state={sceneState} />;
    case 'expedition-start': return <ExpeditionStart state={sceneState} />;
    case 'expedition': return <Expedition state={sceneState} />;
    case 'catch': return <Catch state={sceneState} />;
    case 'results': return <Results state={sceneState} />;
    default: return <Restaurant state={sceneState} />;
  }
}
