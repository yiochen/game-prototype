import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Icon } from './common.jsx';
import { ChefPortrait } from './chef-portrait.jsx';
import './recipe-maple.css';

import chefArt from '../design/editor-dock-preview/assets/chef-lena.png';
import beltArt from '../design/editor-dock-preview/assets/belt-straight-e.png';
import conceptArt from '../design/recipe-picker-preview/raw/composition.png';
export const plateRecipes = {
  salmon: { name: 'Salmon nigiri', tier: 'White', level: 1, price: 18, baseSeconds: 6.2, art: 2 },
  cucumber: { name: 'Cucumber maki', tier: 'White', level: 1, price: 12, baseSeconds: 4.1, art: 3 },
  tamago: { name: 'Tamago nigiri', tier: 'Yellow', level: 3, price: 32, baseSeconds: 5.6, art: 1 },
  eel: { name: 'Eel roll', tier: 'Red', level: 5, price: 48, baseSeconds: 7.5, art: 0 },
  unknown: { name: 'Undiscovered dish', tier: 'Blue', level: 8, unknown: true, art: 4 },
  'unknown-black': { name: 'Undiscovered dish', tier: 'Black', level: 12, unknown: true, art: 5 },
};
const rims = { White: 'double-ring', Yellow: 'dotted', Red: 'dashed', Blue: 'wave', Black: 'scalloped' };
export function PlatedDish({ recipe, className = '' }) {
  const plate = {White:0,Yellow:1,Red:2,Blue:3,Black:4}[recipe.tier];
  const food = recipe.unknown ? 4 : recipe.art;
  return <span className={`wr-dish ${className}`} aria-hidden="true"><span className={`wr-plate wr-cell-${plate}`}/><span className={`wr-food wr-cell-${food}`}/></span>;
}
function Coins({ amount }) { return <span className="wr-coins"><span className="wr-coin" aria-hidden="true">✦</span>{amount}</span>; }

export function WoodRecipeTile({ recipeKey, selected, current, seen = [], isNew = false, level = 5, onInspect }) {
  const recipe = plateRecipes[recipeKey] || plateRecipes.unknown;
  const inspected = selected === recipeKey, preparing = current === recipeKey;
  const isAbove = !recipe.unknown && level < recipe.level;
  return <button type="button" className={`wr-tile ${inspected ? 'wr-inspected' : ''} ${preparing ? 'wr-current' : ''} ${isAbove ? 'wr-above' : ''}`} data-action={onInspect ? undefined : 'select-recipe'} data-value={recipeKey} onClick={onInspect ? () => onInspect(recipeKey) : undefined}
    aria-label={`Inspect ${recipe.name}, ${recipe.tier} plate, ${rims[recipe.tier]} rim, requires Level ${recipe.level}${recipe.unknown ? '' : `, ${recipe.price} coins`}${preparing ? ', currently preparing' : ''}${inspected ? ', selected for inspection' : ''}${isNew && !seen.includes(recipeKey) ? ', new discovery' : ''}`} aria-pressed={inspected}>
    <PlatedDish recipe={recipe}/><span className="wr-tile-name">{recipe.unknown ? '???' : recipe.name}</span>
    {!recipe.unknown && <Coins amount={recipe.price}/>}
    {isNew && !seen.includes(recipeKey) && <span className="wr-new">NEW</span>}
    {preparing && <span className="wr-current-dot" aria-hidden="true"/>}
  </button>;
}

export function MapleRecipePanel({ state, chefName = 'Lena', chefId = 'lena', level = 5, onInspect, onPrepare, onClose }) {
  const selected = state.selectedRecipe, current = state.currentRecipe;
  const recipe = plateRecipes[selected], eligible = recipe && !recipe.unknown && level >= recipe.level;
  const currentSelected = eligible && current === selected;
  const available = Object.keys(plateRecipes).filter(key => !plateRecipes[key].unknown);
  const sorted = [...available.filter(key => level >= plateRecipes[key].level).sort((a,b) => plateRecipes[b].level - plateRecipes[a].level), ...available.filter(key => level < plateRecipes[key].level).sort((a,b) => plateRecipes[b].level - plateRecipes[a].level), 'unknown', 'unknown-black'];
  const close = useRef(null), catalog = useRef(null);
  useLayoutEffect(() => {
    if (!selected || !catalog.current) return;
    const tile = catalog.current.querySelector(`[data-value="${selected}"]`);
    if (!tile) return;
    const a = tile.getBoundingClientRect(), b = catalog.current.getBoundingClientRect();
    if (a.bottom > b.bottom) catalog.current.scrollTop += a.bottom - b.bottom + 8;
    else if (a.top < b.top) catalog.current.scrollTop -= b.top - a.top + 8;
  }, [selected]);
  useEffect(() => { close.current?.focus({preventScroll:true}); }, []);
  const prep = recipe ? (recipe.baseSeconds / (1 + (level - 1) * .12)).toFixed(1) : '';
  return <div className="wr-scrim" onClick={onInspect ? event => event.stopPropagation() : undefined}>
    <dialog open className="wr-panel" aria-modal="true" aria-labelledby="wr-title">
      <header className="wr-header"><ChefPortrait className="wr-chef" chefId={chefId} bust/><div><h2 id="wr-title">{chefName}’s recipes</h2><p>Level {level}</p></div><button ref={close} type="button" className="wr-close" aria-label="Close recipes" data-action={onClose ? undefined : 'dismiss'} onClick={onClose}><Icon name="close"/></button></header>
      <div ref={catalog} className="wr-catalog" aria-label="Scrollable recipe catalog" tabIndex={0}>
        <div className="wr-grid">{sorted.map(key => <WoodRecipeTile key={key} recipeKey={key} selected={selected} current={current} seen={state.seenRecipes} isNew={key === 'eel'} level={level} onInspect={onInspect}/>)}</div>
      </div>
      <section className="wr-details" aria-label="Selected recipe details" aria-live="polite" aria-atomic="true">
        {recipe ? <div className="wr-detail-row"><PlatedDish recipe={recipe}/><div className="wr-detail-copy"><h3>{recipe.name}</h3>{recipe.unknown ? <p className="wr-discover">Find new creatures on expeditions to discover this dish.</p> : <><Coins amount={recipe.price}/><dl><div><dt>Prep with {chefName}</dt><dd>{eligible ? `${prep} sec` : '—'}</dd></div><div><dt>Requires</dt><dd>Lv {recipe.level}</dd></div></dl></>}</div></div> : <div className="wr-empty"><span className="wr-empty-plate" aria-hidden="true"/><h3>Choose a recipe</h3><p>Pick a dish above to see its details.</p></div>}
        {recipe && !recipe.unknown && !eligible && <p className="wr-requirement">{chefName} needs Level {recipe.level} to prepare this dish.</p>}
        {currentSelected ? <div className="wr-preparing"><Icon name="check"/>Preparing<span>Current recipe</span></div> : <button type="button" className="wr-prepare" disabled={!eligible} data-action={onPrepare ? undefined : 'prepare'} onClick={onPrepare}>Prepare</button>}
      </section>
      <div className="wr-wave" aria-hidden="true"/>
    </dialog>
  </div>;
}

const reviewStates = [{id:'eligible',name:'Choose a recipe',selected:'cucumber',level:5}, {id:'current',name:'Preparing',selected:'salmon',level:5}, {id:'new',name:'New discovery',selected:'eel',level:5}, {id:'unavailable',name:'Needs Level 5',selected:'eel',level:2}, {id:'unknown',name:'Undiscovered',selected:'unknown',level:5}, {id:'idle',name:'Idle chef',selected:null,level:5}];
export function RecipeExperience({ initial = 'new' }) {
  const preset = reviewStates.find(x => x.id === initial) || reviewStates[2];
  const [scenario, setScenario] = useState(preset.id), [level, setLevel] = useState(preset.level);
  const [state, setState] = useState({selectedRecipe:preset.selected,currentRecipe:initial === 'idle' ? null : 'salmon',seenRecipes:[]});
  const [open, setOpen] = useState(true), [notice, setNotice] = useState('');
  const launch = useRef(null), panel = useRef(null);
  const close = () => { setOpen(false); requestAnimationFrame(() => launch.current?.focus()); };
  useEffect(() => {
    const keyboard = event => {
      if (!open) return;
      if (event.key === 'Escape') { event.stopImmediatePropagation(); close(); }
      if (event.key !== 'Tab') return;
      const targets = [...panel.current.querySelectorAll('dialog button:not(:disabled), dialog [tabindex="0"]')];
      const first=targets[0],last=targets.at(-1);
      if (event.shiftKey && (document.activeElement===first || !panel.current.querySelector('dialog').contains(document.activeElement))) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement===last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown',keyboard,true);return () => document.removeEventListener('keydown',keyboard,true);
  }, [open]);
  function changeScenario(id) { const s=reviewStates.find(x=>x.id===id);setScenario(id);setLevel(s.level);setState({selectedRecipe:s.selected,currentRecipe:id==='idle'?null:'salmon',seenRecipes:[]});setOpen(true);setNotice(''); }
  const inspect = key => setState(s=>({...s,selectedRecipe:key,seenRecipes:[...new Set([...s.seenRecipes,key])]}));
  const prepare = () => { const r=plateRecipes[state.selectedRecipe];if(!r||r.unknown||r.level>level)return;setState(s=>({...s,currentRecipe:s.selectedRecipe}));setNotice(`${r.name} is now preparing.`);close(); };
  return <div className="wr-review"><nav className="wr-review-controls" aria-label="Prototype review states"><span>REVIEW STATES</span>{reviewStates.map(s=><button type="button" key={s.id} aria-pressed={scenario===s.id} onClick={()=>changeScenario(s.id)}>{s.name}</button>)}<a href={conceptArt} target="_blank" rel="noreferrer">ImageGen concept ↗</a></nav>
    <div className="wr-phone" ref={panel}>
      <div className="wr-room" inert={open}><div className="wr-room-wall"/><div className="wr-room-floor"/><div className="wr-room-hud"><Coins amount={120}/><span>Live</span></div><img className="wr-belt" src={beltArt} alt=""/><img className="wr-room-chef" src={chefArt} alt="Lena"/><div className="wr-blackboard"><PlatedDish recipe={plateRecipes[state.currentRecipe] || plateRecipes.salmon}/></div><div className="wr-room-footer"><button ref={launch} className="wr-reopen" type="button" onClick={()=>{setState(s=>({...s,selectedRecipe:s.currentRecipe}));setOpen(true);setNotice('');}}>Lena’s recipes</button></div>{notice && <p className="wr-notice" role="status">{notice}</p>}</div>
      {open && <MapleRecipePanel state={state} level={level} onInspect={inspect} onPrepare={prepare} onClose={close}/>}
    </div>
  </div>;
}
