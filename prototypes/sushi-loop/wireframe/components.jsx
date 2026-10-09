import React from 'react';
import { Target, Icon, Money, Character } from './common.jsx';

// These composites are used directly in both the complete scenes and the isolated gallery.
export function RestaurantHud({ state = {}, children }) {
  return <div className="restaurant-hud">
    <div className="hud-top-row"><div className="hud-savings"><div className="coin-count"><Money amount={1240}/></div>{state._variant === 'offline' && <span className="income-toast">+420 while away</span>}</div>{children}</div>
    <nav className="restaurant-shortcuts" aria-label="Restaurant shortcuts"><Target action="navigate" data={{story:'shop'}} className="hud-action shop-shortcut" title="Shop"><Icon name="basket"/><strong>Shop</strong>{!state.shopVisited && <span className="stock-spark" aria-label="New Shop stock">✦</span>}</Target></nav>
  </div>;
}

function InventoryItem({ label, value, art, count, layer }) {
  const swatch = layer === 'floor';
  return <Target action={swatch ? 'paint' : 'place'} data={{value}} className={`inventory-item ${swatch ? 'floor-swatch' : ''}`} title={label}>{art}{!swatch && <><strong>{label}</strong><small>{count}</small></>}</Target>;
}

export function EditorControls({ state = {} }) {
  const layer = state.layer || (state._variant === 'floor' ? 'floor' : 'people');
  const open = state.trayOpen !== false;
  const palettes = [{label:'Plain tile',value:'plain'},{label:'Blue wave',value:'wave'},{label:'Checker',value:'checker'}];
  const inventory = [{label:'Belt tile',value:'belt',art:<span className="mini-belt" aria-hidden="true">→</span>,count:String(state.beltCount ?? 12)},{label:'Chair',value:'chair',art:<span className="mini-chair" aria-hidden="true">⊓</span>,count:'3'},{label:'Plant',value:'plant',art:<span className="mini-plant" aria-hidden="true">♧</span>,count:'1'}];
  return <div className={`editor-controls editor-layer-${layer}`} data-tray-open={open} aria-label="Restaurant editor">
    <Target action="navigate" data={{story:'restaurant-live'}} className="live-action" title="Live"><Icon name="play" /><span>Live</span></Target>
    <div className="layer-tabs" role="group" aria-label="Editing layer">{['people','layout','floor'].map(name=><Target key={name} action="layer" data={{value:name}} className={layer === name ? 'layer-tab active' : 'layer-tab'} title={`${name[0].toUpperCase()+name.slice(1)} layer`} aria-pressed={layer === name} aria-expanded={layer === name && open} aria-controls="editor-inventory-tray"><Icon name={name} /></Target>)}</div>
    <div id="editor-inventory-tray" className="edit-controls" aria-label={`${layer[0].toUpperCase()+layer.slice(1)} inventory`} aria-hidden={!open} inert={!open ? true : undefined}><div className="inventory-tray">{layer === 'people' ? <InventoryItem label="Omar" value="omar" art={<Character name="Omar" />} count="Unassigned chef" layer={layer} /> : layer === 'floor' ? palettes.map(item=><InventoryItem key={item.value} {...item} art={<span className={`floor-sample ${item.value}`} aria-hidden="true" />} layer={layer} />) : inventory.map(item=><InventoryItem key={item.value} {...item} layer={layer} />)}</div></div>
  </div>;
}

export function Dock({ state = {}, locked = false, future = false }) {
  const charging = state._variant === 'charging';
  return <div className={`dock-zone ${locked ? 'dock-locked' : ''}`}>
    <span className="reserved-label">Reserved dock footprint</span>
    {(locked || future) && <span className="dock-lock">Future access · clear a route</span>}
    <Target action={charging ? 'charging' : 'navigate'} data={charging ? {} : { story:'expedition-start' }} className="world-submarine" disabled={locked}><Icon name="submarine" /><strong>Submarine</strong><span className="dock-charge"><i className={`charge-cell ${charging ? 'half' : ''}`} />{charging ? 'Charging' : 'Ready'}</span></Target>
    <Target action="navigate" data={{story:'workshop'}} className="world-workshop" disabled={locked}><Icon name="workshop" /><strong>Workshop</strong><small>Small service hut</small></Target>
  </div>;
}

export function RecipeTile({ recipe, recipeKey, selected, current, seen = [], isNew = false }) {
  const unknown = recipeKey === 'unknown';
  const classes = ['recipe-tile', `tier-${recipe.tier.toLowerCase()}`, recipeKey === selected && 'is-inspected', recipeKey === current && 'is-preparing', unknown && 'is-undiscovered'].filter(Boolean).join(' ');
  return <Target action="select-recipe" className={classes} data={{value:recipeKey}} title={`Inspect ${recipe.name}`}>
    <span className={`recipe-dish ${unknown ? 'dish-silhouette' : ''}`} aria-hidden="true">{recipe.symbol}</span><span className="recipe-tile-name">{recipe.name}</span><span className="recipe-tier">{recipe.tier}</span>
    {isNew && !seen.includes(recipeKey) && <span className="new-label">NEW</span>}
    {recipeKey === current && <span className="sr-only">Currently preparing.</span>}{recipeKey === selected && <span className="sr-only">Selected for inspection.</span>}
  </Target>;
}

export function HullMeter({ percent = 78, danger = false }) {
  return <div className={`hull-meter ${danger ? 'low-hull' : ''}`}><span>Hull</span><i><b style={{width:`${percent}%`}} /></i></div>;
}

export function UpgradeCard({ track, level = 1, max = false, poor = false, selected = false }) {
  return <article className={`upgrade-card ${selected ? 'selected' : ''}`}><div className="upgrade-title"><Icon name={track.icon} /><h3>{track.name}</h3><span>Level {level}</span></div><div className="stat-preview"><span>{track.unit}</span><strong>{track.current}{!max && <> <i>→</i> {track.next}</>}</strong></div>{max ? <span className="max-state">MAX</span> : <Target action="upgrade" data={{value:track.id}} className="upgrade-action" disabled={poor}><Money kind="salvage" amount={track.price} /><span>Upgrade</span></Target>}</article>;
}

export function SalvageReceipt({ completed = true, repeatCatch = false }) {
  const repeatBonus = repeatCatch ? 18 : 0;
  const total = 72 + repeatBonus + (completed ? 30 : 0);
  return <div className="salvage-receipt"><h3>Salvage earned</h3><dl><div><dt>Pickups</dt><dd>72</dd></div>{repeatBonus > 0 && <div><dt>Repeat-catch bonus</dt><dd>18</dd></div>}<div><dt>Completion bonus</dt><dd>{completed ? 30 : 0}</dd></div></dl>{!completed && <small>No completion bonus because the route was not finished.</small>}<div className="receipt-total"><span>Total</span><Money kind="salvage" amount={total} /></div></div>;
}

const galleryRecipes = {
  salmon:{name:'Salmon nigiri',tier:'Wood',symbol:'◓'},
  eel:{name:'Eel roll',tier:'Copper',symbol:'≋'},
  unknown:{name:'Undiscovered dish',tier:'Silver',symbol:'?'},
};
const hullTrack = {id:'hull',name:'Hull',unit:'Maximum hull',current:'100',next:'125',price:90,icon:'submarine'};
const example = (label, children, className = '') => <section className={`component-example ${className}`} key={label}><h3>{label}</h3>{children}</section>;

export function ComponentGallery({ story, state = {} }) {
  const key = story.component || story.variant;
  let examples;
  switch (key) {
    case 'restaurant-hud': examples = <>{example('Fixed upper-left · Live and Edit',<RestaurantHud state={state}/>,'hud-example')}{example('Refreshed Shop stock · earnings beside savings',<RestaurantHud state={{...state,_variant:'offline'}}/>,'hud-example')}</>; break;
    case 'editor-controls': examples = example('Layer controls and owned inventory',<EditorControls state={state}/>,'editor-example'); break;
    case 'money': examples = <>{example('Restaurant coins',<div className="coin-count"><Money amount={1240} /></div>)}{example('Banked salvage',<Money kind="salvage" amount={180} />)}{example('Price in an action',<Target action="purchase" data={{value:'belt'}}><Money amount={40} /><span>Buy</span></Target>)}</>; break;
    case 'character': examples = <>{['Lena Brooks','Omar Haddad','Ama Mensah','Mateo Rivera','Noor Haddad'].map(name=>example(name,<Character name={name} />))}{['Rosa','Ellis','Samir','June'].map(name=>example(`${name} · guest`,<Character name={name} kind="guest" />))}</>; break;
    case 'dock': examples = <>{example('Ready · navigation available',<Dock state={state} />,'dock-example')}{example('Charging · stays in restaurant',<Dock state={{...state,_variant:'charging'}} />,'dock-example')}{example('Future access · unavailable',<Dock locked state={state} />,'dock-example')}</>; break;
    case 'recipe-tile': examples = <>{example('Current recipe',<RecipeTile recipe={galleryRecipes.salmon} recipeKey="salmon" current="salmon" selected={state.selectedRecipe} />)}{example('New discovery',<RecipeTile recipe={galleryRecipes.eel} recipeKey="eel" selected={state.selectedRecipe} seen={state.seenRecipes || []} isNew />)}{example('Undiscovered',<RecipeTile recipe={galleryRecipes.unknown} recipeKey="unknown" selected={state.selectedRecipe} />)}</>; break;
    case 'hull-meter': examples = <>{example('Healthy hull',<HullMeter />)}{example('Low hull',<HullMeter percent={22} danger />)}</>; break;
    case 'upgrade-card': examples = <>{example('Affordable upgrade',<UpgradeCard track={hullTrack} level={1+Number(state.upgradeLevels?.hull || 0)} />)}{example('Insufficient salvage',<UpgradeCard track={hullTrack} poor />)}{example('Capability ceiling',<UpgradeCard track={{...hullTrack,current:'200'}} level={5} max />)}</>; break;
    case 'receipt': examples = <>{example('Complete · first discovery',<SalvageReceipt />)}{example('Complete · repeat catch',<SalvageReceipt repeatCatch />)}{example('Unfinished route',<SalvageReceipt completed={false} />)}</>; break;
    case 'tap-target': examples = <>{example('Text navigation',<Target action="navigate" data={{story:'restaurant-live'}}>Restaurant</Target>)}{example('Icon target',<Target action="navigate" data={{story:'staff-roster'}} title="Open staff roster"><Icon name="staff" /></Target>)}{example('Disabled action',<Target action="purchase" disabled><Money amount={600} />Buy</Target>)}</>; break;
    default: examples = example('Shared component',<Icon name="info" />);
  }
  return <div className={`phone-scene component-gallery component-gallery-${key}`}><header className="scene-header"><div><h2>{story.title}</h2><p>The same React component used in the complete screens.</p></div></header><div className="component-examples">{examples}</div></div>;
}
