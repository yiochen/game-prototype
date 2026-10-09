import React, { useState } from 'react';
import { Target } from './common.jsx';
import './concept-catalog.css';

const catalogImage = new URL('../design/art-directions/doodle.png', import.meta.url).href;

// Display the supplied reference unchanged; the wireframes own screen controls.
export function ConceptCatalog() {
  const [zoomed, setZoomed] = useState(false);
  return <div className="phone-scene concept-catalog-scene">
    <header className="concept-catalog-header">
      <h2>Doodle UI &amp; art catalog</h2>
      <p>Materials, shapes, icons and sprites. Screen controls follow the wireframes.</p>
      <div className="concept-catalog-tools">
        <Target className="concept-catalog-zoom" title={zoomed ? 'Fit catalog' : 'Zoom catalog'} aria-pressed={zoomed} onClick={() => setZoomed(!zoomed)}>{zoomed ? 'Fit catalog' : 'Zoom catalog'}</Target>
        <a className="tap-target catalog-original-link" href={catalogImage} target="_blank" rel="noopener noreferrer">Open full-size catalog</a>
      </div>
    </header>
    <figure className={`concept-catalog-scroll ${zoomed ? 'catalog-zoomed' : ''}`} tabIndex={0} aria-label="Scroll doodle UI and art catalog">
      <img className="concept-catalog-image" src={catalogImage} width="1024" height="1536" alt="Doodle UI and art catalog: square tile grids, sprite anchors, button states, popups, characters, conveyor belts, dishes and environment examples." />
    </figure>
  </div>;
}
