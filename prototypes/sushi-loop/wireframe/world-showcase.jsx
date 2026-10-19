import React, { useMemo, useState } from 'react';
import { SpriteScene, usePlayback } from './object-review.jsx';
import { libraryObjects, finalAssetsApproved, productionArtStatus } from './object-review-data.js';
import { restaurantShowcase } from './restaurant-showcase-data.js';
import { underwaterShowcase } from './underwater-showcase-data.js';
import './world-showcase.css';

const showcases = { restaurant: restaurantShowcase, underwater: underwaterShowcase };
const conceptReferences = {
  restaurant: {
    src: new URL('../design/art-directions/restaurant-concept.png', import.meta.url).href,
    alt: 'Original restaurant concept art showing the cream tile floor, warm wood furniture, red conveyor loop, chefs and diners.',
  },
  underwater: {
    src: new URL('../design/art-directions/underwater-concept.png', import.meta.url).href,
    alt: 'Original underwater concept art showing a yellow submarine in turquoise water with cobalt cliffs, coral, kelp and ruins.',
  },
};
const objectById = new Map(libraryObjects.map(object => [object.id, object]));
const clock = frame => `${Math.floor(frame / 12 / 60).toString().padStart(2, '0')}:${Math.floor(frame / 12 % 60).toString().padStart(2, '0')}`;

function ObjectLinks({ ids, className = '' }) {
  return <ul className={`world-object-links ${className}`}>{[...new Set(ids)].map(id => {
    const object = objectById.get(id);
    return object && <li key={id}><a href={`#object-${id}`}>{object.name}<span aria-hidden="true">↗</span></a></li>;
  })}</ul>;
}

export function WorldShowcase({ sceneId = 'restaurant' }) {
  const showcase = showcases[sceneId] || restaurantShowcase;
  const concept = conceptReferences[showcase.id];
  const [zoom, setZoom] = useState(1);
  const [overlays, setOverlays] = useState(false);
  const [grid, setGrid] = useState(false);
  const duration = Number(showcase.duration) > 0 ? Number(showcase.duration) : 24;
  const frames = Math.max(1, Math.round(duration * 12));
  const { frame, playing, toggle, scrub } = usePlayback(frames);
  const used = useMemo(() => [...new Set([showcase.floorId, ...showcase.placements.map(placement => placement.object)].filter(id => objectById.has(id)))], [showcase]);
  return <div className={`phone-scene world-showcase world-showcase--${sceneId}`} data-showcase={sceneId}>
    <nav className="world-scene-tabs" aria-label="Scene previews">
      <a href="#scene-restaurant" aria-current={sceneId === 'restaurant' ? 'page' : undefined}>Restaurant scene</a>
      <a href="#scene-underwater" aria-current={sceneId === 'underwater' ? 'page' : undefined}>Underwater scene</a>
    </nav>
    <header className="world-showcase-header">
      <div className="world-showcase-kicker"><span>SCENE ART REVIEW</span><a href="#object-library">Object library <span aria-hidden="true">↗</span></a></div>
      <h2>{showcase.title}</h2><a href="#decoration-study">Decoration coverage study ↗</a>
      <p>{showcase.description}</p>
      <div className="world-showcase-meta"><span>{used.length} catalog objects</span><span>{showcase.gridSize.join(' × ')} tile map</span><span>12 fps</span></div>
    </header>
    <div className="world-showcase-controls" aria-label="Scene review controls">
      <div className="world-playback">
        <button type="button" onClick={toggle} aria-label={playing ? 'Pause scene animations' : 'Play scene animations'} aria-pressed={playing}><span aria-hidden="true">{playing ? 'Ⅱ' : '▶'}</span>{playing ? 'Pause' : 'Play'}</button>
        <label className="world-timeline"><span><span>Scene time</span><span>{clock(frame)} / {clock(frames)}</span></span><input type="range" aria-label="Scene animation frame" aria-valuetext={`${(frame / 12).toFixed(2)} seconds of ${duration} seconds`} min="0" max={frames - 1} step="1" value={frame} onChange={event => scrub(event.target.value)}/></label>
      </div>
      <div className="world-view-controls"><label>Zoom<select aria-label="Scene zoom" value={zoom} onChange={event => setZoom(Number(event.target.value))}><option value="1">Fit</option><option value="2">2×</option><option value="4">4×</option></select></label><div className="world-overlay-toggles"><label><input type="checkbox" checked={grid} onChange={event => setGrid(event.target.checked)}/> Tile grid</label><label><input type="checkbox" checked={overlays} onChange={event => setOverlays(event.target.checked)}/> Roots &amp; ports</label></div></div>
    </div>
    <figure className="world-showcase-figure">
      <SpriteScene sceneId={showcase.id || sceneId} placements={showcase.placements} gridSize={showcase.gridSize} cameraBounds={showcase.cameraBounds} floorId={showcase.floorId} background={showcase.background} animateFloor={showcase.id === 'underwater'} showGrid={grid} overlays={overlays} zoom={zoom} seconds={frame / 12} label={`${showcase.title}: complete composed scene`}/>
      <figcaption><span>{zoom === 1 ? 'Complete scene' : `${zoom}× detail · pan horizontally`}</span><span>Fit · 2× · 4×</span></figcaption>
    </figure>
    <section className="world-concept-reference" aria-labelledby={`world-concept-${sceneId}`}>
      <div className="world-section-heading"><div><span className="world-section-eyebrow">ART DIRECTION</span><h3 id={`world-concept-${sceneId}`}>Original concept art</h3></div><a href={concept.src} target="_blank" rel="noopener noreferrer">Open full-size <span aria-hidden="true">↗</span></a></div>
      <figure>
        <img src={concept.src} width="1024" height="1536" alt={concept.alt} loading="lazy" decoding="async"/>
        <figcaption>The original concept, preserved as a reference for composition, color and atmosphere.</figcaption>
      </figure>
    </section>
    <section className="world-highlights" aria-labelledby={`world-highlights-${sceneId}`}>
      <div className="world-section-heading"><div><span className="world-section-eyebrow">LOOK CLOSER</span><h3 id={`world-highlights-${sceneId}`}>The details in context</h3></div><span className="world-review-status">{finalAssetsApproved ? 'Approved art' : 'Art rollout'}</span></div>
      <div className="world-highlight-grid">{showcase.highlights.map((highlight, index) => <article className="world-highlight" key={highlight.title}><span className="world-highlight-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span><div><h4>{highlight.title}</h4><p>{highlight.description}</p><ObjectLinks ids={highlight.objectIds}/></div></article>)}</div>
    </section>
    <details className="world-asset-index"><summary><span>Inspect every object in this scene</span><span>{used.length} <span aria-hidden="true">↗</span></span></summary><ObjectLinks ids={used}/></details>
    <footer className="world-showcase-footer"><p>{showcase.note || 'A composed art preview using the registered catalog sprites.'}</p><p>Open an object to inspect its directions and animations. {productionArtStatus}.</p></footer>
  </div>;
}
