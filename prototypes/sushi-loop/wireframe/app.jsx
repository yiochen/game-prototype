import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './studio.css';
import './scenes.css';
import './overlays.css';
import './feedback.css';
import { stories, storyGroups } from './stories.js';
import { Scene } from './scenes.jsx';
import { Overlay } from './overlays.jsx';
import { Icon } from './common.jsx';
import { Feedback } from './feedback.jsx';
import { chefFor } from './fixtures.js';

const byId = new Map(stories.map(story => [story.id, story]));
const route = () => byId.has(location.hash.slice(1)) ? location.hash.slice(1) : 'floor-plan';

function fixtureFor(story) {
  return {
    panel: ['expansion', 'expansion-unaffordable', 'restaurant-charging'].includes(story.id) ? 1 : 0,
    layer: story.variant === 'floor' ? 'floor' : 'people',
    selectedRecipe: story.variant === 'undiscovered' ? 'unknown' : ['new', 'unavailable'].includes(story.variant) ? 'eel' : ['idle', 'unassigned'].includes(story.variant) ? null : 'salmon',
    currentRecipe: ['idle', 'unassigned'].includes(story.variant) ? null : 'salmon', seenRecipes: [],
    selectedUpgrade: 'hull', selectedChef: 'lena', demoPatchCleared: false,
    placement: false, toast: '', hiredApplicants: [], applicantRefresh: false,
    chefLevel: story.variant === 'new' ? 5 : story.variant === 'max' && story.overlay === 'chef-detail' ? 8 : 2,
    chefUnassigned: false, chefLevels: {}, unassignedChefs: [], removedChefs: [],
    purchasedItems: [], upgradeLevels: {}, painted: false, rotation: 0, shopVisited: false,
    popupReturnStory: 'restaurant-live', expeditionBackdrop: 'travel',
    repeatCatch: ['catch-repeat', 'results-complete'].includes(story.id),
  };
}

const nextEvents = {
  'expedition-travel': ['expedition-encounter', 'Demo event: a creature appears near the end of the route.'],
  'expedition-encounter': ['expedition-pursuit', 'Inspect the hooked creature and following area.'],
  'expedition-pursuit': ['catch-first', 'Demo event: resistance reaches zero.'],
  'expedition-danger': ['results-hull', 'Demo event: the hull reaches zero.'],
  'expedition-resume': ['expedition-travel', 'The countdown is a frozen example. Preview the return to the preserved scene.'],
  'catch-first': ['recipe-award', 'In the game, this short cutscene opens the award automatically.'],
  'catch-repeat': ['results-complete', 'A repeat catch goes directly to the salvage receipt.'],
};

function Annotations({ story }) {
  return <>
    <div className="notes-heading"><span className="eyebrow">DESIGN ANNOTATIONS</span><h2>Behavior &amp; motion</h2></div>
    <p className="story-description">{story.description}</p>
    <Feedback key={story.id} story={story}/>
    <dl className="element-notes">{story.elements.map(element => <div className="element-note" key={element.name}><dt>{element.name}</dt><dd>{element.behavior}</dd><dd className="motion-note"><span>Motion</span>{element.motion}</dd></div>)}</dl>
    {!!story.notes?.length && <div className="design-decisions"><h3>For discussion</h3><ul>{story.notes.map(note => <li key={note}>{note}</li>)}</ul></div>}
    <p className="notes-disclaimer">Motion values are proposals. Reduced motion removes decorative movement. These wireframes are awaiting design approval.</p>
  </>;
}

function App() {
  const [view, setView] = useState(() => ({ id: route(), fixture: fixtureFor(byId.get(route())), returnRestaurant: 'restaurant-live', returnPanel: 0 }));
  const viewRef = useRef(view); viewRef.current = view;
  const [targets, setTargets] = useState(true);
  const [notes, setNotes] = useState(false);
  const [menu, setMenu] = useState(false);
  const [search, setSearch] = useState('');
  const [width, setWidth] = useState(innerWidth);
  const stage = useRef(null), sidebar = useRef(null), documentation = useRef(null);
  const snapshots = useRef(new Map());
  const story = byId.get(view.id);
  const mobileMenu = width < 900;
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  function go(requestedId, options = {}) {
    const previous = viewRef.current, previousStory = byId.get(previous.id);
    let id = requestedId;
    const destination = byId.get(id);
    if (!destination) return;
    snapshots.current.set(previous.id, structuredClone(previous));
    let returnRestaurant = previous.returnRestaurant, returnPanel = previous.returnPanel;
    let fixture = structuredClone(options.fixture || previous.fixture);
    if (['shop', 'workshop', 'staff'].includes(destination.scene) && ['restaurant', 'floor-plan'].includes(previousStory.scene)) {
      returnRestaurant = previousStory.scene === 'floor-plan' ? previous.id : previousStory.overlay === 'inventory-empty' ? 'restaurant-edit' : ['edit', 'floor', 'selected'].includes(previousStory.variant) ? previous.id : 'restaurant-live';
      if (destination.scene === 'shop' && !previousStory.overlay) returnRestaurant = previous.id;
      returnPanel = fixture.panel;
    }
    if (id === 'restaurant-live' && ['shop', 'workshop', 'staff'].includes(previousStory.scene) && !options.reset) {
      id = returnRestaurant; fixture.panel = previousStory.scene === 'workshop' ? 0 : returnPanel;
    }
    if (id === 'restaurant-live' && ['expedition-start', 'results'].includes(previousStory.scene) && !options.reset) fixture.panel = 0;
    if (options.reset) { fixture = fixtureFor(byId.get(id)); returnRestaurant = 'restaurant-live'; returnPanel = 0; }
    else {
      if (destination.overlay === 'recipes' && previousStory.overlay === 'chef-detail') fixture.popupReturnStory = previous.id;
      else if (['recipes', 'expansion'].includes(destination.overlay) && !previousStory.overlay) fixture.popupReturnStory = previousStory.scene === 'restaurant' ? previous.id : 'restaurant-live';
      if (previousStory.scene === 'expedition' && !previousStory.overlay && !['pause', 'return', 'resume'].includes(previousStory.variant)) fixture.expeditionBackdrop = previousStory.variant;
    }
    if (id === 'catch-first') fixture.repeatCatch = false;
    if (byId.get(id).scene === 'shop') fixture.shopVisited = true;
    if (id === 'catch-repeat') fixture.repeatCatch = true;
    if (['expansion', 'expansion-unaffordable'].includes(id)) fixture.panel = 1;
    if (options.panel !== undefined) fixture.panel = options.panel;
    const next = { id, fixture, returnRestaurant, returnPanel };
    viewRef.current = next; setView(next); setMenu(false);
    if (location.hash !== `#${id}`) history.pushState(null, '', `#${id}`);
  }

  function change(fixture, message) {
    const next = { ...viewRef.current, fixture: { ...fixture, ...(message ? { toast: message } : {}) } };
    viewRef.current = next; setView(next);
  }

  function dismiss() {
    const current = byId.get(viewRef.current.id), fixture = viewRef.current.fixture;
    const destinations = { recipes: fixture.popupReturnStory, applicants: 'staff-roster', 'chef-detail': 'staff-roster', fire: 'staff-detail', expansion: fixture.popupReturnStory, 'inventory-empty': 'restaurant-edit', 'early-return': 'expedition-pause' };
    if (destinations[current.overlay]) go(destinations[current.overlay], { panel: fixture.panel });
  }

  function act(event) {
    const button = event.target.closest('button[data-action]');
    if (!button || button.disabled) return;
    const { action, value, story: destination, panel } = button.dataset;
    const current = byId.get(viewRef.current.id), fixture = structuredClone(viewRef.current.fixture);
    const navigate = (id, message) => { if (message) fixture.toast = message; go(id, { fixture }); };
    switch (action) {
      case 'navigate':
        if ((destination === 'staff-detail' && value) || (destination === 'recipe-picker' && current.overlay !== 'chef-detail')) { fixture.selectedChef = value || fixture.placedChef || 'lena'; fixture.chefLevel = fixture.chefLevels[fixture.selectedChef] || chefFor(fixture).level; fixture.chefUnassigned = fixture.unassignedChefs.includes(fixture.selectedChef); }
        navigate(destination); break;
      case 'pan': fixture.panel = Number(panel); change(fixture); stage.current.querySelector('[data-pan-scroll]')?.scrollTo({ left: fixture.panel * stage.current.querySelector('[data-pan-scroll]').clientWidth, behavior: reduced() ? 'instant' : 'smooth' }); break;
      case 'layer': fixture.layer = value; navigate(value === 'floor' ? 'restaurant-floor' : 'restaurant-edit'); break;
      case 'select-object': navigate('restaurant-selected'); break;
      case 'select-recipe': fixture.selectedRecipe = value; fixture.seenRecipes = [...new Set([...fixture.seenRecipes, value])]; change(fixture); break;
      case 'prepare': fixture.currentRecipe = fixture.selectedRecipe; navigate(fixture.popupReturnStory, 'Recipe prepared in this example. The chef’s blackboard updates.'); break;
      case 'select-upgrade': fixture.selectedUpgrade = value; change(fixture); break;
      case 'purchase': fixture.purchasedItems = [...fixture.purchasedItems, value]; change(fixture, `${value || 'Item'} added to mock inventory.`); break;
      case 'upgrade': fixture.upgradeLevels[value || fixture.selectedUpgrade] = (fixture.upgradeLevels[value || fixture.selectedUpgrade] || 0) + 1; change(fixture, 'Upgrade preview advanced one example level.'); break;
      case 'hire': fixture.hiredApplicants = [...fixture.hiredApplicants, value]; change(fixture, 'Chef added to the mock roster, unassigned.'); break;
      case 'refresh-applicants': fixture.applicantRefresh = true; change(fixture, 'New example applications. Refresh now shows its cooldown state.'); break;
      case 'level-up': fixture.chefLevel += 1; fixture.chefLevels[fixture.selectedChef] = fixture.chefLevel; change(fixture, 'Chef level preview updated.'); break;
      case 'unassign': fixture.chefUnassigned = true; fixture.unassignedChefs = [...new Set([...fixture.unassignedChefs, fixture.selectedChef])]; change(fixture, 'Chef is unassigned in this example.'); break;
      case 'fire-confirm': fixture.removedChefs = [...fixture.removedChefs, fixture.selectedChef]; navigate('staff-roster', 'Confirmed dismissal shown. Reset restores the example.'); break;
      case 'clear-confirm': fixture.demoPatchCleared = true; go(['restaurant-edit', 'restaurant-floor', 'restaurant-selected'].includes(fixture.popupReturnStory) ? fixture.popupReturnStory : 'restaurant-expanded', { fixture, panel: 1 }); break;
      case 'resume': navigate('expedition-resume'); break;
      case 'confirm-return': navigate('results-early'); break;
      case 'place':
        if (['omar', 'lena', 'ama', 'mateo', 'noor'].includes(value)) { fixture.selectedChef = value; fixture.placedChef = value; fixture.unassignedChefs = fixture.unassignedChefs.filter(id => id !== value); fixture.chefUnassigned = false; fixture.chefLevel = fixture.chefLevels[value] || chefFor(fixture).level; fixture.currentRecipe = null; fixture.selectedRecipe = null; navigate('recipe-idle'); }
        else { fixture.placement = value || 'chair'; change(fixture); }
        break;
      case 'finish-placement': fixture.placement = false; change(fixture, 'Sample placement shown. No layout rules are simulated.'); break;
      case 'paint': fixture.painted = !fixture.painted; change(fixture, 'Floor swatch applied to the sample area.'); break;
      case 'rotate': fixture.rotation = (fixture.rotation + 90) % 360; change(fixture); break;
      case 'remove': case 'remove-object': navigate('restaurant-edit', 'Object returned to mock inventory.'); break;
      case 'cancel-placement': fixture.placement = false; change(fixture); break;
      case 'dock-charging': case 'charging': change(fixture, 'Charging — 1:24 left (illustrative).'); break;
      case 'dismiss': dismiss(); break;
      case 'dismiss-toast': fixture.toast = ''; change(fixture); break;
      default: change(fixture, 'Presentation-only control. Its intended behavior is described in Notes.');
    }
  }

  useEffect(() => {
    if (!byId.has(location.hash.slice(1))) history.replaceState(null, '', '#floor-plan');
    const restore = () => {
      const id = route(), previous = viewRef.current;
      if (id === previous.id) return;
      snapshots.current.set(previous.id, structuredClone(previous));
      const next = structuredClone(snapshots.current.get(id) || { id, fixture: fixtureFor(byId.get(id)), returnRestaurant: 'restaurant-live', returnPanel: 0 });
      viewRef.current = next; setView(next); setMenu(false);
    };
    const resize = () => setWidth(innerWidth);
    addEventListener('hashchange', restore); addEventListener('popstate', restore); addEventListener('resize', resize);
    return () => { removeEventListener('hashchange', restore); removeEventListener('popstate', restore); removeEventListener('resize', resize); };
  }, []);

  useEffect(() => {
    document.body.classList.toggle('menu-open', menu); document.body.classList.toggle('show-notes', notes);
    return () => { document.body.classList.remove('menu-open', 'show-notes'); };
  }, [menu, notes]);

  useEffect(() => {
    if (!view.fixture.toast) return;
    const timer = setTimeout(() => setView(previous => ({ ...previous, fixture: { ...previous.fixture, toast: '' } })), 4200);
    return () => clearTimeout(timer);
  }, [view.fixture.toast]);

  useLayoutEffect(() => {
    const viewport = stage.current.querySelector('[data-pan-scroll]');
    if (viewport) viewport.scrollLeft = viewRef.current.fixture.panel * viewport.clientWidth;
    const dialog = stage.current.querySelector('dialog');
    if (dialog) dialog.querySelector('button:not(:disabled), [href], input, select')?.focus({ preventScroll: true });
    document.title = `${story.title} · Sushi Loop wireframes`;
  }, [story.id, width]);

  useEffect(() => {
    if (menu) document.querySelector('#story-search')?.focus();
    const keyboard = event => {
      if (event.key === 'Escape') { if (menu) { setMenu(false); document.querySelector('#open-menu')?.focus(); } else dismiss(); }
      const dialog = menu ? sidebar.current : stage.current.querySelector('dialog');
      if (event.key !== 'Tab' || !dialog) return;
      const elements = [...dialog.querySelectorAll('button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), [tabindex="0"]')].filter(element => element.getClientRects().length);
      const first = elements[0], last = elements.at(-1);
      if (!first) return;
      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', keyboard);
    return () => document.removeEventListener('keydown', keyboard);
  }, [menu, story.id]);

  function showNotes(comments = false) {
    setNotes(true);
    requestAnimationFrame(() => (comments ? documentation.current.querySelector('.feedback-section') : documentation.current)?.scrollIntoView({ behavior: reduced() ? 'instant' : 'smooth', block: 'start' }));
  }

  const term = search.toLowerCase().trim();
  const visibleGroups = storyGroups.map(group => ({ ...group, stories: stories.filter(example => example.group === group.id && `${example.title} ${group.title}`.toLowerCase().includes(term)) })).filter(group => group.stories.length);
  const next = nextEvents[story.id];
  return <>
    <header className="studio-header"><a className="studio-brand" href="#floor-plan" aria-label="Sushi Loop wireframe studio" onClick={event => { event.preventDefault(); go('floor-plan', { reset: true }); }}><span className="brand-mark" aria-hidden="true"><Icon name="submarine"/></span><span>Sushi Loop<small>Wireframe studio</small></span></a><span className="draft-label">Review draft <span>· Mock data</span></span><a className="catalog-link" href="../../">Playground <Icon name="arrow-right"/></a></header>
    <div className="studio-layout">
      <button className="menu-scrim" aria-label="Close example menu" hidden={!menu} onClick={() => setMenu(false)}/>
      <aside ref={sidebar} id="story-sidebar" className="story-sidebar" aria-label="Wireframe examples" role={menu ? 'dialog' : undefined} aria-modal={menu ? true : undefined} inert={mobileMenu && !menu}>
        <div className="sidebar-heading"><span>EXAMPLES</span><button className="studio-button mobile-only" aria-label="Close example menu" onClick={() => setMenu(false)}><Icon name="close"/></button></div>
        <label className="search-label" htmlFor="story-search">Find a scene or component</label><input id="story-search" type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search examples…" autoComplete="off"/>
        <nav id="story-nav">{visibleGroups.map(group => <details className="story-group" open key={group.id}><summary>{group.title}<span>{group.stories.length}</span></summary>{group.stories.map(example => <a href={`#${example.id}`} key={example.id} className="story-link" data-story={example.id} aria-current={story.id === example.id ? 'page' : undefined} onClick={event => { event.preventDefault(); go(example.id, { reset: true }); }}><span className="story-dot" aria-hidden="true"/>{example.title}</a>)}</details>)}</nav>
        {!visibleGroups.length && <p>No matching examples.</p>}<div className="sidebar-footer">{stories.length} examples · shared React UI<br/>Presentation only. No saved game.</div>
      </aside>
      <main className="studio-main">
        <div className="preview-toolbar">
          <button id="open-menu" className="studio-button menu-trigger" aria-controls="story-sidebar" aria-expanded={menu} onClick={() => setMenu(true)}><Icon name="layout"/><span>Examples</span></button>
          <label className="example-select-label" htmlFor="example-select">Example<select id="example-select" value={story.id} onChange={event => go(event.target.value, { reset: true })}>{storyGroups.map(group => <optgroup label={group.title} key={group.id}>{stories.filter(example => example.group === group.id).map(example => <option value={example.id} key={example.id}>{example.title}</option>)}</optgroup>)}</select></label>
          <button id="reset-example" className="studio-button" aria-label="Reset" title="Reset this mock example" onClick={() => change(fixtureFor(story))}><Icon name="rotate"/><span>Reset</span></button>
          <label className="targets-toggle"><input type="checkbox" checked={targets} onChange={event => setTargets(event.target.checked)}/><span>Tap targets</span></label>
          <button id="toggle-notes" className="studio-button" aria-label="Notes" aria-controls="documentation" aria-expanded={notes} onClick={() => notes ? setNotes(false) : showNotes()}><Icon name="info"/><span>Notes</span></button>
          <button id="open-comments" className="studio-button" aria-label="Comments" title="Review this example" onClick={() => showNotes(true)}><Icon name="comment"/><span>Comments</span></button>
        </div>
        <div className="preview-heading"><div><p className="eyebrow">{storyGroups.find(group => group.id === story.group)?.title}</p><h1 id="story-title" tabIndex={-1}>{story.title}</h1></div><span className="target-key"><i/>Dashed = tap</span></div>
        <div className="stage-area"><div ref={stage} id="prototype-stage" className={`prototype-stage ${story.scene === 'floor-plan' ? 'frame--map' : 'frame--phone'} ${targets ? '' : 'hide-targets'}`} data-scene={story.scene} data-story={story.id} aria-label="Interactive wireframe preview" onClick={act} onScrollCapture={event => {
          const viewport = event.target;
          if (!viewport.hasAttribute('data-pan-scroll')) return;
          const panel = Math.min(2, Math.max(0, Math.round(viewport.scrollLeft / viewport.clientWidth)));
          if (panel !== viewRef.current.fixture.panel) setView(previous => ({ ...previous, fixture: { ...previous.fixture, panel } }));
        }}>
          <div className="scene-host" inert={!!story.overlay}><Scene story={story} state={view.fixture}/></div>
          {story.overlay && <Overlay story={story} state={view.fixture}/>}
          {view.fixture.toast && <div className="mock-toast" role="status">{view.fixture.toast}<button type="button" data-action="dismiss-toast" aria-label="Dismiss notification"><Icon name="close"/></button></div>}
        </div></div>
        <div className="flow-toolbar"><p>{next ? next[1] : story.scene === 'floor-plan' ? 'Swipe across the complete floor plan. Open a marked destination or clearance patch.' : 'Portrait composition · UI-only prototype'}</p>{next && <button className="studio-button" onClick={() => go(story.id === 'expedition-resume' ? `expedition-${view.fixture.expeditionBackdrop || 'travel'}` : next[0])}>Preview next event <Icon name="arrow-right"/></button>}</div>
        <p className="studio-hint">Switch examples to inspect a state, or tap the marked controls to follow a flow. All values are illustrative.</p>
      </main>
      <aside ref={documentation} className="documentation" id="documentation" aria-label="Behavior and animation notes"><Annotations story={story}/></aside>
    </div>
  </>;
}

createRoot(document.getElementById('app')).render(<App/>);
