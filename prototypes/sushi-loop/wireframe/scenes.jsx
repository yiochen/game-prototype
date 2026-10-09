import React from 'react';
import { Target, Icon, Money, Character } from './common.jsx';
import { RestaurantHud, Dock, HullMeter, UpgradeCard, SalvageReceipt, ComponentGallery } from './components.jsx';
import { roster, chefAssigned, chefSpeed } from './fixtures.js';

function Nav({ children, story = 'restaurant-live', className = '', data = {}, ...rest }) {
  return <Target action="navigate" data={{story,...data}} className={className} {...rest}>{children}</Target>;
}
function ReturnDoor() { return <Nav className="scene-return"><Icon name="arrow-left" /><span>Restaurant</span></Nav>; }
function Dish({ type = 'salmon', className = '' }) { return <span className={`wire-dish ${className}`} aria-hidden="true"><i className="rice" /><i className={`fish ${type}`} /><i className="nori" /></span>; }
function Note({ children }) { return <p className="scene-note"><Icon name="info" />{children}</p>; }
function Header({ title, subtitle, balance, actions }) { return <header className="scene-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{balance}{actions}</header>; }
function Entry({ panel, active = false }) { return <div className={`customer-entry ${active ? 'active' : ''}`}><span className="entry-door" /><span>Entry {panel+1}</span>{active ? <small>Customer access</small> : <small><Icon name="lock" /> Future access</small>}</div>; }

function Garbage({ panel, state, full = false }) {
  const partial = state.demoPatchCleared && panel === 1;
  return <div className={`garbage-field ${full ? 'plan-garbage' : ''} ${partial ? 'partial-clearance' : ''}`} aria-label="Garbage awaiting clearance"><span className="debris d1">▧</span><span className="debris d2">▱</span><span className="debris d3">▧</span><span className="debris d4">▱</span><p className="garbage-label">Garbage to clear</p><Nav story="expansion" className={`clearance-target ${panel === 2 ? 'later-patch' : ''}`}><Icon name="trash" /><strong>{partial ? 'Next patch' : 'Clear patch'}</strong><small>Expand this way →</small></Nav></div>;
}

function StarterRestaurant({ state, edit = false }) {
  const placedChef = roster(state).find(chef => chef.id === (state.placedChef || 'lena') && chefAssigned(state, chef));
  const selected = state._variant === 'selected';
  const recipeName = state.currentRecipe === null ? 'Choose recipe' : ({eel:'Eel',tuna:'Tuna',cucumber:'Cucumber',salmon:'Salmon'}[state.currentRecipe] || 'Salmon');
  return <div className={`starter-service ${edit ? 'editable' : ''}`}>
    <div className="open-belt"><span className="belt-direction">→ → → →</span><Dish className="plate-one" /><Dish type="tuna" className="plate-two" /><span className="belt-direction return-direction">← ← ←</span></div>
    {placedChef ? <Nav story="recipe-picker" data={{value:placedChef.id}} className="placed-chef"><Character name={placedChef.name} /><span className="blackboard"><b>{recipeName}</b><small>{state.currentRecipe === null ? 'Idle' : state.currentRecipe === 'eel' ? 'Copper recipe' : 'Wood recipe'}</small></span></Nav> : <span className="scene-guest-name">No chef assigned · Choose one in Edit</span>}
    <div className="customer c-one"><span className="preference"><Dish /><i className="preference-time" /></span><Character name="Rosa" kind="guest" />{edit ? <Target action="select-object" data={{value:'chair'}} className={`chair-target ${selected ? 'object-selected' : ''}`}><span className="chair" style={{transform:`rotate(${Number(state.rotation || 0)}deg)`}}>Seat</span></Target> : <span className="chair">Seat</span>}</div>
    <div className="customer c-two"><span className="happy">☺</span><Character name="Ellis" kind="guest" /><span className="chair">Seat</span></div>
    <div className="customer c-three"><Character name="Samir" kind="guest" /><span className="chair">Seat</span></div>
    <div className="customer c-four"><Character name="June" kind="guest" /><span className="chair">Seat</span></div>
    {edit ? <div className="empty-cell"><span>Empty cell</span><Target action="place" data={{value:'chair'}} className="cell-place" title="Preview chair placement"><Icon name="plus" /></Target></div> : <div className="scene-guest-name">Rosa · bicycle mechanic</div>}
    {selected && <div className="object-tools"><Target action="rotate" data={{value:'chair'}} className="icon-control" title="Rotate selected chair"><Icon name="rotate" /></Target><Target action="remove" data={{value:'chair'}} className="icon-control" title="Remove selected chair"><Icon name="trash" /></Target></div>}
  </div>;
}

function FloorPanels({ state, map = false }) {
  const expanded = ['expanded','charging'].includes(state._variant) || state.demoPatchCleared;
  const edit = ['edit','floor','selected'].includes(state._variant);
  return [0,1,2].map(panel=><section key={panel} className={`floor-panel ${panel === 0 || (panel === 1 && expanded) ? 'cleared' : 'uncleared'} ${state.painted && panel === 0 ? 'painted-floor' : ''}`} data-floor-panel={panel} aria-label={`Restaurant panel ${panel+1}`}>
    {map ? <span className="panel-name">Panel {panel+1} · {panel === 0 ? 'usable at start' : 'future expansion'}</span> : <span className="world-panel-number">{panel+1} / 3</span>}
    <Entry panel={panel} active={panel === 0 || (panel === 1 && expanded)} />
    {panel === 0 && (map ? <div className="starter-label"><strong>Starter restaurant</strong><span>Cleared, usable floor</span><small>Place belts, chefs and seats here</small></div> : <StarterRestaurant state={state} edit={edit} />)}
    {panel > 0 && (panel === 2 || !expanded) && <Garbage panel={panel} state={state} full={map} />}
    {panel === 1 && <Dock state={state} locked={!map && !expanded} future={map} />}
    {map && <span className="viewport-guide">Viewport guide · no dividing wall</span>}
  </section>);
}

function FloorPlan({ state }) {
  return <div className="floorplan-scene"><Header title="Full restaurant floor plan" subtitle="Three portrait panels · one continuous room" actions={<Nav story="shop" className="hud-action plan-shop-shortcut"><Icon name="basket"/><strong>Shop</strong></Nav>}/><div className="plan-scroll" tabIndex={0} aria-label="Scroll full restaurant plan"><div className="floor-plan-world"><FloorPanels state={state} map /></div></div><div className="plan-legend"><span><i className="legend-clear" />Usable at start</span><span><i className="legend-garbage" />Garbage patches</span><span><i className="legend-guide" />Viewport guides</span><span>Shop is a floating HUD button · no floor footprint</span></div><Note>Swipe sideways to inspect. Blue dashed outlines mark tappable targets. Clearance, prices and access rules are preview states.</Note><div className="scene-footer"><Nav className="primary-action"><Icon name="play" /><span>Open restaurant view</span></Nav><Nav story="expansion"><Icon name="trash" /><span>Preview clearance popup</span></Nav></div></div>;
}

function InventoryItem({ label, value, art, count, layer }) {
  return <Target action={layer === 'floor' ? 'paint' : 'place'} data={{value}} className="inventory-item">{art}<strong>{label}</strong><small>{count}</small></Target>;
}
function EditTray({ state }) {
  const layer = state._variant === 'floor' ? 'floor' : (state.layer || 'people');
  const palettes = [{label:'Plain tile',value:'plain'},{label:'Blue wave',value:'wave'},{label:'Checker',value:'checker'}];
  const inventory = [{label:'Belt tile',value:'belt',art:<span className="mini-belt">→</span>,count:'12 in inventory'},{label:'Chair',value:'chair',art:<span className="mini-chair">⊓</span>,count:'3 in inventory'},{label:'Plant',value:'plant',art:<span className="mini-plant">♧</span>,count:'1 in inventory'}];
  return <div className="edit-controls"><div className="edit-toolbar"><span><Icon name="pause" /> Service paused</span><Nav className="live-action"><Icon name="play" /> Live</Nav></div><div className="layer-tabs" role="group" aria-label="Editing layer">{['people','layout','floor'].map(name=><Target key={name} action="layer" data={{value:name}} className={layer === name ? 'layer-tab active' : 'layer-tab'} title={`${name[0].toUpperCase()+name.slice(1)} layer`}><Icon name={name} /></Target>)}</div><div className="inventory-tray">{layer === 'people' ? <InventoryItem label="Omar" value="omar" art={<Character name="Omar" />} count="Unassigned chef" layer={layer} /> : layer === 'floor' ? palettes.map(item=><InventoryItem key={item.value} {...item} art={<span className={`floor-sample ${item.value}`} />} count="Owned" layer={layer} />) : inventory.map(item=><InventoryItem key={item.value} {...item} layer={layer} />)}</div><p className="tray-hint">{layer === 'floor' ? 'Select a style, then tap the floor to preview.' : 'Tap an item to preview placement. Edits are presentation only.'}</p></div>;
}

function Restaurant({ state }) {
  const edit = ['edit','floor','selected'].includes(state._variant);
  return <div className={`phone-scene restaurant-scene ${edit ? 'edit-scene' : ''}`}><div className="restaurant-viewport" data-pan-scroll tabIndex={0} aria-label="Pan restaurant floor"><div className="restaurant-world"><FloorPanels state={state} /></div></div><RestaurantHud state={state}/>{!edit && <div className="restaurant-actions"><Nav story="restaurant-edit" className="hud-action"><Icon name="edit" /><span>Edit</span></Nav><Nav story="staff-roster" className="hud-action"><Icon name="staff" /><span>Staff</span></Nav></div>}<div className="pan-controls" aria-label="Jump to restaurant panel">{[0,1,2].map(panel=><Target key={panel} action="pan" data={{panel}} aria-pressed={Number(state.panel || 0) === panel} className={`pan-dot ${Number(state.panel || 0) === panel ? 'active' : ''}`}><span>{panel+1}</span></Target>)}<small>Swipe to pan →</small></div>{edit && <EditTray state={state} />}{state.placement && !['omar','chef'].includes(state.placement) && <div className="placement-preview"><span><Icon name="layout" /> {state.placement === 'belt' ? 'Belt tile' : state.placement === 'chair' ? 'Chair' : 'Plant'} preview</span><Target action="finish-placement" className="place-here">Place here</Target><Target action="cancel-placement" className="icon-control" title="Cancel placement preview"><Icon name="close" /></Target></div>}</div>;
}

function ShopCard({ label, description, art, value, price, qty, state, poor }) {
  return <article className="catalog-card"><div className="catalog-art">{art}</div><div><h3>{label}</h3><p>{description}</p>{qty && <small>{qty}</small>}{state.purchasedItems?.includes(value) && <small className="added-marker">✓ Added to inventory</small>}</div><Target action="purchase" data={{value}} className="buy-action" disabled={poor}><Money amount={price} /><span>Buy</span></Target></article>;
}
function Shop({ state }) {
  const owned = state._variant === 'owned' || state.purchasedItems?.includes('blue-wave');
  const poor = state._variant === 'unaffordable';
  return <div className="phone-scene catalog-scene shop-scene"><Header title="Shop" subtitle="Supplies for your restaurant" balance={<Money amount={poor ? 24 : 1240} />} /><ReturnDoor /><div className="catalog-content"><h3 className="group-heading">Essentials <small>Always available</small></h3><ShopCard label="Belt tile" description="Connect your conveyor route." art={<span className="mini-belt">→</span>} value="belt" price={40} state={state} poor={poor} /><ShopCard label="Chair" description="A simple seat beside the belt." art={<span className="mini-chair">⊓</span>} value="chair" price={80} state={state} poor={poor} /><h3 className="group-heading">Rotating stock <small>Refreshes after an expedition</small></h3><ShopCard label="Comfy chair" description="An appearance upgrade." art={<span className="mini-chair fancy">⊓</span>} value="comfy-chair" price={320} qty="2 remaining" state={state} poor={poor} /><article className="catalog-card floor-offer"><div className="catalog-art"><span className="floor-sample wave" /></div><div><h3>Blue Wave</h3><p>Floor style · preview</p></div>{owned ? <span className="owned-state"><Icon name="check" />Owned</span> : <Target action="purchase" data={{value:'blue-wave'}} className="buy-action" disabled={poor}><Money amount={600} /><span>Buy</span></Target>}</article><Note>Purchased items appear in the editing tray. This wireframe only previews the purchase feedback.</Note></div></div>;
}

function Staff({ state }) {
  const chefs = roster(state);
  const count = state._variant === 'full' ? 4 : chefs.length;
  return <div className="phone-scene catalog-scene staff-scene"><Header title="Staff" subtitle="People, experience and potential" balance={<Money amount={1240} />} /><ReturnDoor /><div className="staff-tabs"><span className="staff-capacity">Staff {count} / 4</span><Nav story="staff-applicants">Job applicants</Nav></div><div className="catalog-content"><p className="roster-caption">Assigned and unassigned chefs share staff capacity.</p>{chefs.map(chef=>{
    const level = state.chefLevels?.[chef.id] || chef.level;
    const assigned = chefAssigned(state, chef);
    const tier = level >= 12 ? 'Gold' : level >= 8 ? 'Silver' : level >= 5 ? 'Copper' : level >= 3 ? 'Steel' : 'Wood';
    return <article className="staff-card" key={chef.id}><div className="staff-summary"><Character name={chef.name} /><div><h3>{chef.name}</h3><p>{chef.role}</p><span>{tier} · Level {level}</span></div></div><dl className="compact-facts"><div><dt>Cooking speed</dt><dd>{chefSpeed(chef, level)}×</dd></div><div><dt>Growth / level</dt><dd>+{Math.round(chef.growthRate*100)}%</dd></div><div><dt>Capability ceiling</dt><dd>Level {chef.ceiling} · {chef.tier}</dd></div></dl><p className="profile-line">{chef.trait}</p><Nav story="staff-detail" data={{value:chef.id}} className="staff-detail-action"><Icon name="info" /><span>{assigned ? 'Assigned' : 'Unassigned'} · details</span></Nav></article>;
  })}</div></div>;
}

const upgradeTracks = [{id:'hull',name:'Hull',unit:'Maximum hull',price:90,icon:'submarine'},{id:'harpoon',name:'Harpoon',unit:'Reeling strength',price:110,icon:'harpoon'},{id:'collector',name:'Collector',unit:'Pickup reach',price:80,icon:'salvage'}];
function exampleStat(track, steps = 0) { return track.id === 'hull' ? String(100+25*steps) : track.id === 'harpoon' ? `${(1+.2*steps).toFixed(1)}×` : `${1+.5*steps} ${steps === 0 ? 'cell' : 'cells'}`; }
function Workshop({ state }) {
  const max = state._variant === 'max';
  const poor = state._variant === 'unaffordable';
  return <div className="phone-scene catalog-scene workshop-scene"><Header title="Workshop" subtitle="Permanent submarine upgrades" balance={<Money kind="salvage" amount={poor ? 18 : 180} />} /><Nav className="workshop-door"><span className="airlock"><Icon name="arrow-left" /><b>Sushi Bar</b></span></Nav><div className="ship-preview"><Icon name="submarine" /><span>Equipment preview</span></div><div className="catalog-content">{upgradeTracks.map(track=>{
    const steps = Number(state.upgradeLevels?.[track.id] || 0);
    const capped = max && track.id === 'hull';
    return <UpgradeCard key={track.id} track={{...track,current:capped ? '200' : exampleStat(track,steps),next:exampleStat(track,steps+1)}} level={capped ? 5 : 1+steps} max={capped} poor={poor} selected={state.selectedUpgrade === track.id} />;
  })}<Note>One tap previews the new level. All numbers are illustrative; upgrades use salvage.</Note></div></div>;
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
  return <div className={`phone-scene ocean-scene expedition-scene ${danger ? 'danger-scene' : ''} ${paused ? 'paused-scene' : ''}`}><SeaDecor /><div className="expedition-hud"><HullMeter percent={danger ? 22 : 78} danger={danger} /><div className="run-salvage"><Money kind="salvage" amount={36} /></div><Nav story="expedition-pause" className="icon-control pause-control"><Icon name="pause" /><span className="sr-only">Pause</span></Nav></div>{encounter && <div className="creature-meter"><span>Eel · {pursuit ? 'Reeling resistance' : 'Creature resistance'}</span><i><b style={{width:`${pursuit ? 46 : 100}%`}} /></i></div>}<div className="expedition-world-label">{variant === 'travel' ? 'Travelling' : paused ? 'Frozen scene' : danger ? 'Cable at its limit' : pursuit ? 'Pursuit' : 'Encounter'}</div>{pursuit && <><div className={`following-strip ${danger ? 'taut' : ''}`}><span>Following range</span></div><div className={`harpoon-cable ${danger ? 'frayed' : ''}`} /></>}{danger && <div className="attack-column"><span>Attack warning</span></div>}{encounter && <Creature danger={danger} pursuit={pursuit} />}<div className="expedition-ship"><Icon name="submarine" /><span>You</span></div>{encounter && !pursuit && <Nav story="expedition-pursuit" className="harpoon-control" disabled={paused}><Icon name="harpoon" /><strong>Harpoon</strong></Nav>}{variant === 'resume' && <div className="resume-countdown" role="status"><strong>3</strong><span>Resuming expedition</span><small>Scene remains frozen during countdown</small></div>}<p className="steering-hint">{paused ? 'Paused · no steering' : 'Drag to steer · illustrated interaction area'}</p></div>;
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
    case 'component': return <ComponentGallery story={story} state={sceneState} />;
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
