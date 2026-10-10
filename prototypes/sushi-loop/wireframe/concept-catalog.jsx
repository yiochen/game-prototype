import React, { useEffect, useState } from 'react';
import { Target } from './common.jsx';
import './concept-catalog.css';

const catalogs = {
  doodle: {
    image: new URL('../design/art-directions/doodle.png', import.meta.url).href,
    title: 'Doodle UI & art catalog',
    description: 'Materials, shapes, icons and sprites. Screen controls follow the wireframes.',
    label: 'doodle UI and art catalog', width:1024, height:1536,
    alt: 'Doodle UI and art catalog: square tile grids, sprite anchors, button states, popups, characters, conveyor belts, dishes and environment examples.',
  },
  'underwater-tile-kit': {
    image: new URL('../design/art-directions/underwater-tunnel-tile-kit.jpg', import.meta.url).href,
    title: 'Underwater tunnel tile kit',
    description: 'Square tiles, connected obstacles and layered scenery for the expedition.',
    label: 'underwater tunnel tile kit', width:1280, height:960,
    alt: 'Underwater tunnel tile kit: square-cell floor and wall obstacles, one-cell and multi-cell footprints, layered underwater decoration and a combined tunnel layout.',
  },
};

// Display the supplied reference unchanged; the wireframes own screen controls.
export function ConceptCatalog({ catalog = 'doodle' }) {
  const reference = catalogs[catalog] || catalogs.doodle;
  const [zoomed, setZoomed] = useState(false);
  useEffect(() => setZoomed(false), [catalog]);
  return <div className="phone-scene concept-catalog-scene">
    <header className="concept-catalog-header">
      <h2>{reference.title}</h2>
      <p>{reference.description}</p>
      <div className="concept-catalog-tools">
        <Target className="concept-catalog-zoom" title={zoomed ? 'Fit catalog' : 'Zoom catalog'} aria-pressed={zoomed} onClick={() => setZoomed(!zoomed)}>{zoomed ? 'Fit catalog' : 'Zoom catalog'}</Target>
        <a className="tap-target catalog-original-link" href={reference.image} target="_blank" rel="noopener noreferrer">Open full-size catalog</a>
      </div>
    </header>
    <figure className={`concept-catalog-scroll ${zoomed ? 'catalog-zoomed' : ''}`} style={{'--catalog-width':`${reference.width}px`}} tabIndex={0} aria-label={`Scroll ${reference.label}`}>
      <img className="concept-catalog-image" src={reference.image} width={reference.width} height={reference.height} alt={reference.alt} />
    </figure>
  </div>;
}
