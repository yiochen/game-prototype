import React, { useRef, useState } from 'react';
import { worldAssetFamilies, conceptPanels } from './world-asset-catalog-data.js';
import './world-asset-catalog.css';
import { finalAssetsApproved } from './object-review-data.js';

const sheet = new URL('../design/issue-33-art-catalog/concept/world-asset-catalog-v02.png', import.meta.url).href;

export function WorldAssetCatalog() {
  const [view, setView] = useState('sheet');
  const [zoomed, setZoomed] = useState(false);
  const [selected, setSelected] = useState(0);
  const scroll = useRef(null);
  const family = worldAssetFamilies[selected];
  function switchView(next) {
    setView(next);
    if (scroll.current) { scroll.current.scrollTop = 0; scroll.current.scrollLeft = 0; }
  }

  function browse(index) {
    setSelected(index);
    if (scroll.current) scroll.current.scrollTop = 0;
  }

  return <div className="phone-scene world-catalog-scene">
    <header className="world-catalog-header">
      <span className="world-catalog-status">{finalAssetsApproved ? 'ISSUE 33 · ASSETS APPROVED' : 'ISSUE 33 · ART APPROVED · ROLLOUT IN PROGRESS'}</span>
      <h2>World asset catalog</h2>
      <p>17 families · 8 chefs · 4 customers · 3 dishes</p>
      <div className="world-catalog-tabs" role="group" aria-label="Catalog view">
        <button type="button" aria-pressed={view === 'sheet'} onClick={() => switchView('sheet')}>Concept sheet</button>
        <button type="button" aria-pressed={view === 'items'} onClick={() => switchView('items')}>Browse items</button>
      </div>
    </header>
    <div ref={scroll} className="world-catalog-scroll" tabIndex={0} aria-label={view === 'sheet' ? 'Scroll world concept sheet' : 'Scroll asset family details'}>
      {view === 'sheet' ? <>
        <div className="world-catalog-sheet-tools">
          <button type="button" aria-pressed={zoomed} onClick={() => setZoomed(!zoomed)}>{zoomed ? 'Fit sheet' : 'Zoom sheet'}</button>
          <a href={sheet} target="_blank" rel="noopener noreferrer">Open full-size sheet ↗</a>
        </div>
        <figure className={`world-catalog-sheet ${zoomed ? 'is-zoomed' : ''}`}>
          <img src={sheet} width="1024" height="1536" alt="Issue 33 low-poly world concept sheet with 17 numbered panels: chefs, customers, dishes, restaurant furniture and terrain, connected conveyors, dock, submarine, underwater modules, creatures and effects." />
        </figure>
        <p className="world-catalog-caption">Approved concept reference. Browse items for the full list of assets and animation states.</p>
      </> : <div className="world-catalog-details">
        <div className="world-catalog-picker"><label htmlFor="world-asset-family">Asset family</label><select id="world-asset-family" value={selected} onChange={event => browse(Number(event.target.value))}>{worldAssetFamilies.map((item, index) => <option key={item.id} value={index}>{item.id} · {item.name}</option>)}</select></div>
        <div className="world-catalog-paging">
          <button type="button" aria-label="Previous asset family" disabled={selected === 0} onClick={() => browse(selected - 1)}>← Previous</button>
          <span aria-live="polite">{selected + 1} / {worldAssetFamilies.length}</span>
          <button type="button" aria-label="Next asset family" disabled={selected === worldAssetFamilies.length - 1} onClick={() => browse(selected + 1)}>Next →</button>
        </div>
        <article className="world-catalog-family" aria-labelledby="world-family-name">
          <span className="world-catalog-family-id">{family.id} · SHEET {family.panels.length === 1 ? 'PANEL' : 'PANELS'} {family.panels.join(', ')}</span>
          <h3 id="world-family-name">{family.name}</h3>
          {family.panels.map(number => <figure className="world-catalog-detail-figure" key={number}><svg className="world-catalog-panel" viewBox={conceptPanels[number].join(' ')} role="img" aria-label={`${family.name} concept detail, sheet panel ${number}`}><image href={sheet} width="1024" height="1536" /></svg><figcaption>Concept panel {number}</figcaption></figure>)}
          <h4>Items</h4><p>{family.items}</p>
          <h4>Directions &amp; states to review</h4><p>{family.states}</p>
          <p className="world-catalog-caption">Historical concept detail. <a href="#object-library">Open the current production sprites and animations ↗</a></p>
        </article>
        <section className="world-catalog-contract" aria-label="Asset review contract">
          <h4>Production review contract</h4>
          <p>Review actual reusable sprites, 12 fps animation, square-cell joins, fixed anchors and occupied-seat layering here on the wireframe site. Each animated clip has at least six unique frames.</p>
          <p>Connected belts need four straight flows, eight directed corners, four starts and four ends. Empty joins, moving slats, separate plates and paused frames must all be inspectable.</p>
          <p>The scene art and materials are approved. HUDs, menus and Godot Android game integration are outside this art milestone.</p>
        </section>
      </div>}
    </div>
    <footer className="world-catalog-footer">Use Comments above for feedback; include a panel or family ID.</footer>
  </div>;
}
