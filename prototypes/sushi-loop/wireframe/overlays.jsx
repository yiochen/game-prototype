import React from 'react';
import { Target, Icon, Character, Money } from './common.jsx';
import { RecipeTile } from './components.jsx';
import { ResumeDeck } from './applicants.jsx';
import { applicantSet, chefFor, roster, chefAssigned, chefSpeed } from './fixtures.js';

const recipes = {
  salmon: { name: 'Salmon nigiri', tier: 'Wood', level: 1, price: 18, seconds: 4.2, symbol: '◓' },
  cucumber: { name: 'Cucumber maki', tier: 'Wood', level: 1, price: 12, seconds: 2.8, symbol: '◎' },
  eel: { name: 'Eel roll', tier: 'Copper', level: 5, price: 48, seconds: 5.1, symbol: '≋' },
  unknown: { name: 'Undiscovered dish', tier: 'Silver', level: 8, symbol: '?' },
};
const variantFor = story => ({ 'recipe-unavailable': 'unavailable', 'recipe-undiscovered': 'undiscovered', 'recipe-new': 'new', 'recipe-idle': 'idle', 'staff-full': 'full', 'staff-max': 'max', 'staff-unaffordable': 'unaffordable', 'expansion-unaffordable': 'unaffordable' }[story.id]) || story.variant;
const tierFor = level => level >= 12 ? 'Gold' : level >= 8 ? 'Silver' : level >= 5 ? 'Copper' : level >= 3 ? 'Steel' : 'Wood';
function Navigate({ children, story, className = '' }) { return <Target action="navigate" data={{ story }} className={className}>{children}</Target>; }
function Fact({ label, children }) { return <div className="overlay-fact"><dt>{label}</dt><dd>{children}</dd></div>; }

export function Dialog({ story, title, eyebrow, className = '', children, footer, showClose = true, description }) {
  const titleId = `overlay-${story.id}-title`;
  return <div className={`overlay-scrim ${story.overlay === 'recipes' ? 'light-scrim' : ''}`} data-scrim>
    <dialog open className={`wire-dialog ${className}`} aria-modal="true" aria-labelledby={titleId} aria-describedby={description ? `${titleId}-description` : undefined} data-overlay={story.overlay}>
      <header className="dialog-header"><div>{eyebrow && <p className="dialog-eyebrow">{eyebrow}</p>}<h2 id={titleId}>{title}</h2>{description && <p id={`${titleId}-description`} className="dialog-description">{description}</p>}</div>{showClose && <Target action="dismiss" title="Close dialog" className="dialog-close"><Icon name="close"/><span className="sr-only">Close dialog</span></Target>}</header>
      {children}
      {footer && <footer className="dialog-footer">{footer}</footer>}
    </dialog>
  </div>;
}

function RecipeGroup({ title, keys, selected, current, seen, isNew, muted = false }) {
  return <section className={`recipe-group ${muted ? 'muted-recipes' : ''}`} aria-label={title}><div className="recipe-grid">{keys.map(key => <RecipeTile key={key} recipe={recipes[key]} recipeKey={key} selected={selected} current={current} seen={seen} isNew={isNew && key === 'eel'}/>)}</div></section>;
}

function Recipes({ story, state }) {
  const variant = variantFor(story), chef = chefFor(state), firstName = chef.name.split(' ')[0];
  const level = variant === 'new' ? Math.max(5, state.chefLevel) : state.chefLevel;
  const current = state.currentRecipe, selected = state.selectedRecipe, recipe = recipes[selected];
  const eligible = recipe && selected !== 'unknown' && level >= recipe.level;
  const available = ['salmon', 'cucumber', 'eel'];
  const cookable = available.filter(key => recipes[key].level <= level).sort((a,b) => recipes[b].level - recipes[a].level);
  const above = available.filter(key => recipes[key].level > level).sort((a,b) => recipes[b].level - recipes[a].level);
  const groupProps = { selected, current, seen: state.seenRecipes, isNew: variant === 'new' };
  let details;
  if (!recipe) details = <><div className="recipe-details-empty"><span className="recipe-dish" aria-hidden="true">◌</span><div><h3>Choose a recipe</h3><p>Inspect a dish above, then press Prepare.</p></div></div><Target action="prepare" className="primary-action full-width" disabled>Prepare</Target></>;
  else if (selected === 'unknown') details = <><div className="recipe-detail-heading"><span className="recipe-dish dish-silhouette" aria-hidden="true">?</span><div><h3>Undiscovered dish</h3></div></div><p className="unknown-recipe-note">Catch a new creature on an expedition to reveal this recipe.</p><Target action="prepare" className="primary-action full-width" disabled>Prepare</Target></>;
  else details = <><div className="recipe-detail-heading"><span className="recipe-dish" aria-hidden="true">{recipe.symbol}</span><div><h3>{recipe.name}</h3></div></div><dl className="overlay-facts recipe-facts"><Fact label="Price / dish"><Money kind="coins" amount={recipe.price}/></Fact><Fact label={`Prep with ${firstName}`}>{eligible ? `${recipe.seconds.toFixed(1)} sec` : '—'}</Fact><Fact label="Requires">Lv {recipe.level}</Fact></dl>{!eligible && <p className="inline-reason">{firstName} needs Level {recipe.level} to prepare this recipe.</p>}{selected === current ? <div className="noninteractive-status preparing-status">Preparing <span>Current recipe</span></div> : <Target action="prepare" className="primary-action full-width" disabled={!eligible}>Prepare</Target>}</>;
  return <Dialog story={story} title={`${firstName}’s recipes`} eyebrow={`Level ${level}`} className="recipe-dialog">
    <div className="recipe-catalog" tabIndex={0} aria-label="Scrollable recipe catalog"><RecipeGroup title="Can prepare" keys={cookable} {...groupProps}/>{!!above.length && <RecipeGroup title="Needs a higher chef level" keys={above} {...groupProps} muted/>}<RecipeGroup title="Still undiscovered" keys={['unknown']} {...groupProps}/><p className="catalog-key"><span className="current-key" aria-hidden="true"/>Current recipe <span className="inspection-key" aria-hidden="true"/>Inspecting</p></div>
    <section className={`recipe-details ${recipe ? `tier-${recipe.tier.toLowerCase()}` : ''}`} aria-live="polite" aria-label="Selected recipe details" aria-description={recipe ? `${recipe.tier} material board` : undefined}>{details}</section>
  </Dialog>;
}

function Applicants({ story, state }) {
  const count = variantFor(story) === 'full' ? 4 : Math.min(4, roster(state).length);
  const full = count >= 4, hired = state.hiredApplicants, refreshed = state.applicantRefresh;
  const candidates = applicantSet(state).filter(candidate => !hired.includes(candidate.id));
  return <Dialog story={story} title="Job applicants" eyebrow={`Staff ${count} / 4 · ${full ? 'Roster full' : `${4-count} spaces available`}`} className="applicants-dialog" footer={<><div className="refresh-row"><div><strong>Refresh applications</strong><p>{refreshed ? 'Cooldown preview · available in 04:59' : 'Free · replaces the complete set'}</p></div><Target action="refresh-applicants" disabled={refreshed}>{refreshed ? 'Wait' : 'Refresh'}</Target></div><Navigate story="staff-roster" className="full-width">Back to staff</Navigate></>}>
    <ResumeDeck candidates={candidates} full={full}/>
  </Dialog>;
}

function ChefDetail({ story, state }) {
  const chef = chefFor(state), max = variantFor(story) === 'max' || state.chefLevel >= chef.ceiling;
  const level = max ? chef.ceiling : state.chefLevel, unassigned = !chefAssigned(state, chef);
  const unaffordable = variantFor(story) === 'unaffordable', recipe = recipes[state.currentRecipe || 'salmon'];
  const speed = chefSpeed(chef, level), nextSpeed = chefSpeed(chef, level + 1);
  return <Dialog story={story} title={chef.name} eyebrow={unassigned ? 'Unassigned staff' : 'Assigned · restaurant panel 1'} className="chef-dialog" footer={<><div className="dialog-action-pair"><Target action="unassign" disabled={unassigned}>{unassigned ? 'Unassigned' : 'Unassign'}</Target><Navigate story="staff-fire" className="danger-action">Fire…</Navigate></div><Navigate story="staff-roster" className="full-width">Back to staff</Navigate></>}>
    <div className="dialog-scroll"><div className="chef-profile"><Character name={chef.name}/><div><h3>{chef.role}</h3><p>{chef.background}</p></div></div><dl className="overlay-facts chef-facts"><Fact label="Level">{level} / {chef.ceiling}</Fact><Fact label="Cooking speed">{speed}×</Fact><Fact label="Growth">+{Math.round(chef.growthRate*100)}% per level</Fact><Fact label="Highest tier">{tierFor(level)}</Fact></dl><section className="chef-level-section"><div><h3>{max ? 'Capability ceiling reached' : `Next: Level ${level+1}`}</h3><p>{max ? `${chef.name} keeps their final stats and unlocked recipe tiers.` : `Cooking speed ${speed}× → ${nextSpeed}×`}</p>{!max && [3,5,8,12].includes(level+1) && <p className="tier-unlock-preview">Unlocks {tierFor(level+1)} recipes</p>}{unaffordable && !max && <p className="inline-reason">Not enough coins for this level.</p>}</div>{max ? <span className="noninteractive-status max-status">MAX</span> : <Target action="level-up" className="primary-action" disabled={unaffordable}>Level up <Money kind="coins" amount={120}/></Target>}</section><section className="chef-recipe-section"><div><p className="dialog-eyebrow">{unassigned ? 'Recipe retained' : 'Currently preparing'}</p><h3>{recipe.name}</h3></div><Navigate story="recipe-picker">Recipes</Navigate></section><p className="inline-note">Unassign keeps {chef.name}, their level, and upgrades. Fire permanently removes them.</p></div>
  </Dialog>;
}

function Fire({ story, state }) {
  const chef = chefFor(state);
  return <Dialog story={story} title={`Fire ${chef.name}?`} className="confirmation-dialog" footer={<div className="dialog-action-pair"><Navigate story="staff-detail">Cancel</Navigate><Target action="fire-confirm" className="danger-action">Fire {chef.name.split(' ')[0]}</Target></div>}><div className="dialog-scroll"><div className="confirmation-portrait"><Character name={chef.name}/></div><p>{chef.name} will permanently leave your staff, including their level and upgrades.</p><p className="inline-reason">There is no coin refund.</p></div></Dialog>;
}

function Expansion({ story }) {
  const poor = variantFor(story) === 'unaffordable';
  return <Dialog story={story} title="Clear this patch?" className="expansion-dialog" showClose={false} footer={<div className="dialog-action-pair"><Target action="dismiss">Cancel</Target><Target action="clear-confirm" className="primary-action" disabled={poor}>Clear <Money kind="coins" amount={240}/></Target></div>}><div className="dialog-scroll"><div className="patch-preview" aria-label="Selected garbage patch">{Array.from({length:12},(_,i) => <span key={i}/>)}</div></div></Dialog>;
}

function Pause({ story }) {
  return <Dialog story={story} title="Paused" eyebrow="Expedition preserved" className="pause-dialog" showClose={false} footer={<><Target action="resume" className="primary-action full-width">Resume</Target><Navigate story="expedition-return" className="quiet-action full-width">Return early…</Navigate></>}><div className="dialog-scroll"><p>Your submarine, creature, and hazards are waiting right here.</p></div></Dialog>;
}

function EarlyReturn({ story }) {
  return <Dialog story={story} title="Return early?" className="confirmation-dialog" showClose={false} footer={<div className="dialog-action-pair"><Navigate story="expedition-pause">Stay paused</Navigate><Target action="confirm-return" className="danger-action">Return early</Target></div>}><div className="dialog-scroll"><p>Keep your collected salvage and any earned recipes.</p><p>You will receive no completion bonus. An unfinished pursuit earns no recipe.</p><p className="inline-note">Your submarine must recharge before another departure.</p></div></Dialog>;
}

function RecipeAward({ story }) {
  return <Dialog story={story} title="New recipe discovered!" eyebrow="First catch · Eel" className="recipe-award-dialog" showClose={false} footer={<Navigate story="results-complete" className="primary-action full-width">Continue</Navigate>}><div className="dialog-scroll"><div className="award-dish" aria-hidden="true"><span>≋</span><i/><i/><i/><i/></div><h3 className="award-name">Eel roll</h3><p className="award-subtitle">Added to your restaurant collection</p><dl className="overlay-facts award-facts"><Fact label="Price / dish"><Money kind="coins" amount={48}/></Fact><Fact label="Base prep time">6.0 sec</Fact><Fact label="Chef requirement">Copper · Lv 5</Fact></dl><p className="inline-note">Already earned. Continue opens your expedition receipt.</p></div></Dialog>;
}

export function Overlay({ story, state }) {
  const Component = { recipes: Recipes, applicants: Applicants, 'chef-detail': ChefDetail, fire: Fire, expansion: Expansion, pause: Pause, 'early-return': EarlyReturn, 'recipe-award': RecipeAward }[story.overlay];
  return Component ? <Component story={story} state={state}/> : null;
}
