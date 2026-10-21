import React, { useState } from 'react';
import { backdropLayout } from './restaurant-backdrop-layout.js';
import nativeCamera from '../assets/restaurant-backdrop/blender35/camera.json';
import flatCamera from '../assets/restaurant-backdrop/flat35/camera.json';
import uniformCamera from '../assets/restaurant-backdrop/uniform35/camera.json';
import './restaurant-backdrop.css';

export const backdropFamilies = {
  uniform35: {
    label: 'Wood wall · even light',
    camera: uniformCamera,
    images: {
      gate: new URL('../assets/restaurant-backdrop/uniform35/renders/gate.png', import.meta.url).href,
      'wall-plain': new URL('../assets/restaurant-backdrop/uniform35/renders/wall-plain.png', import.meta.url).href,
    },
  },
  flat35: {
    label: 'Earlier plaster wall',
    camera: flatCamera,
    images: {
      gate: new URL('../assets/restaurant-backdrop/flat35/renders/gate.png', import.meta.url).href,
      'wall-plain': new URL('../assets/restaurant-backdrop/flat35/renders/wall-plain.png', import.meta.url).href,
    },
  },
  blender35: {
    label: 'Earlier Blender · 35°',
    camera: nativeCamera,
    images: {
      gate: new URL('../assets/restaurant-backdrop/blender35/renders/gate.png', import.meta.url).href,
      'wall-plain': new URL('../assets/restaurant-backdrop/blender35/renders/wall-plain.png', import.meta.url).href,
      'wall-window': new URL('../assets/restaurant-backdrop/blender35/renders/wall-window.png', import.meta.url).href,
    },
  },
  imagegen: {
    label: 'ImageGen',
    images: {
      gate: new URL('../assets/restaurant-backdrop/raw/gate.png', import.meta.url).href,
      'wall-plain': new URL('../assets/restaurant-backdrop/raw/wall-plain.png', import.meta.url).href,
      'wall-window': new URL('../assets/restaurant-backdrop/raw/wall-window.png', import.meta.url).href,
    },
  },
};
const assemblies = {
  uniform35: new URL('../assets/restaurant-backdrop/uniform35/renders/assembled.png', import.meta.url).href,
  flat35: new URL('../assets/restaurant-backdrop/flat35/renders/assembled.png', import.meta.url).href,
  blender35: new URL('../assets/restaurant-backdrop/blender35/renders/assembled.png', import.meta.url).href,
};
const lightingFamilies = { flat35: [
  { id: 'ambient', label: 'Even ambient', src: new URL('../assets/restaurant-backdrop/flat35/lighting-proof/ambient.png', import.meta.url).href },
  { id: 'lanterns', label: 'Lanterns on', src: new URL('../assets/restaurant-backdrop/flat35/lighting-proof/lanterns.png', import.meta.url).href },
  { id: 'left-dim', label: 'Left lantern dimmed', src: new URL('../assets/restaurant-backdrop/flat35/lighting-proof/left-dim.png', import.meta.url).href },
], uniform35: [
  { id: 'ambient', label: 'Even ambient', src: new URL('../assets/restaurant-backdrop/uniform35/lighting-proof/ambient.png', import.meta.url).href },
  { id: 'lanterns', label: 'Lanterns on', src: new URL('../assets/restaurant-backdrop/uniform35/lighting-proof/lanterns.png', import.meta.url).href },
  { id: 'left-dim', label: 'Left lantern dimmed', src: new URL('../assets/restaurant-backdrop/uniform35/lighting-proof/left-dim.png', import.meta.url).href },
] };

export function RestaurantBackdrop({ columns = 7, cell = 128, showGrid = false, renderer = 'uniform35' }) {
  const layout = backdropLayout(columns, ['imagegen', 'blender35'].includes(renderer));
  const family = backdropFamilies[renderer] || backdropFamilies.uniform35;
  return <g data-restaurant-backdrop="true" data-reserved-rows="3" data-backdrop-renderer={renderer} data-wall-decorations={['flat35', 'uniform35'].includes(renderer) ? 'none' : 'historical'}>
    {[...layout.walls, layout.gate].map(piece => {
      const props = { 'data-backdrop-piece': piece.id, 'data-backdrop-asset': piece.asset, x: piece.x * cell, y: piece.y * cell, width: piece.width * cell, height: piece.height * cell };
      if (renderer === 'imagegen') return <image key={piece.id} {...props} href={family.images[piece.asset]} preserveAspectRatio="none"/>;
      const source = family.camera.assets[piece.asset];
      // Fixed authored camera viewport: preserve square pixels and source pitch.
      // The padded render stays intact; no alpha fitting or sprite stretching.
      return <svg key={piece.id} {...props} viewBox={source.contentRect.join(' ')} overflow="hidden" preserveAspectRatio="xMidYMid meet"><image href={family.images[piece.asset]} width={source.frame[0] * source.captureScale} height={source.frame[1] * source.captureScale}/></svg>;
    })}
    {showGrid && <g data-backdrop-grid="true" fill="none" stroke="#fff2cb" strokeWidth="1.5" opacity=".65" pointerEvents="none">
      {Array.from({ length: columns + 1 }, (_, x) => <path key={`x-${x}`} d={`M ${x * cell} 0 V ${3 * cell}`}/>)}
      {[0, 1, 2, 3].map(y => <path key={`y-${y}`} d={`M 0 ${y * cell} H ${columns * cell}`}/>)}
    </g>}
  </g>;
}

export function BackdropAssetReview({ renderer = 'uniform35' }) {
  const family = backdropFamilies[renderer] || backdropFamilies.uniform35;
  return <section className="backdrop-asset-review" aria-labelledby="backdrop-assets-title">
    <div className="world-section-heading"><div><span className="world-section-eyebrow">BACKDROP STUDY</span><h3 id="backdrop-assets-title">One continuous back wall</h3></div><span className="world-review-status">{family.label}</span></div>
    <p>{renderer === 'uniform35' ? 'Even lighting across the flat roof tiles and honey-wood wall, with a continuous wooden baseboard. Windows and paintings can be added as separate decorations later. ' : 'An earlier version, kept here for comparison. '}The top three tile rows form the backdrop: a four-tile gate, two-tile opening, and one-tile wall modules.</p>
    <svg className="backdrop-strip" viewBox="0 0 1408 384" role="img" aria-label="Three blank wall tiles, a four-tile entrance with a two-tile opening, then more blank wall tiles"><RestaurantBackdrop columns={11} renderer={renderer}/></svg>
    <div className={`backdrop-asset-cards has-${Object.keys(family.images).length}`}>
      {[['gate', 'Entrance gate', '4 × 3 tiles · 2-tile opening'], ['wall-plain', 'Plain wall', '1 × 3 tiles'], ['wall-window', 'Window wall', '1 × 3 tiles']].filter(([id]) => family.images[id]).map(([id, title, dimensions]) => <a href={family.images[id]} target="_blank" rel="noopener noreferrer" className="backdrop-asset-card" key={id}><span className="backdrop-asset-art"><img src={family.images[id]} alt={title} loading="lazy"/></span><strong>{title} ↗</strong><span>{dimensions}</span></a>)}
    </div>
    {renderer === 'uniform35' && <p><a href="#object-backdrop-wall">Blank wall in the catalog ↗</a> · <a href="#object-backdrop-entrance">Entrance in the catalog ↗</a></p>}
    {renderer !== 'imagegen' && <details className="backdrop-native-proof"><summary>View the original centered Blender study</summary><img src={assemblies[renderer]} width="2880" height="1344" alt="Original seven-tile Blender study at 35 degrees, with the gate centered" loading="lazy"/><p>The original assembly verifies the shared roofline and wall joins. The current layout above places three blank walls before the entrance.</p></details>}
    {lightingFamilies[renderer] && <LanternLightingProof key={renderer} renderer={renderer}/>}
  </section>;
}

function LanternLightingProof({ renderer }) {
  const lightStates = lightingFamilies[renderer];
  const [stateId, setStateId] = useState(renderer === 'uniform35' ? 'ambient' : 'lanterns');
  const selected = lightStates.find(state => state.id === stateId);
  return <section className="backdrop-lighting-proof" aria-labelledby="lantern-lighting-title">
    <div className="world-section-heading"><div><span className="world-section-eyebrow">GODOT LIGHTING TEST</span><h3 id="lantern-lighting-title">{renderer === 'uniform35' ? 'Uniform lighting' : 'Light from the lanterns'}</h3></div></div>
    <p>{renderer === 'uniform35' ? 'Even ambient lighting is the default. The optional lantern comparison adds a gentle warm light over the same uniformly lit sprite.' : "These captures use the same wall sprite in Godot. Each lantern is an independent light; the wall's base color stays even."}</p>
    <div className="backdrop-lighting-controls" role="group" aria-label="Lantern lighting comparison">{lightStates.map(state => <button key={state.id} type="button" aria-pressed={state.id === stateId} onClick={() => setStateId(state.id)}>{state.label}</button>)}</div>
    <figure data-lighting-state={stateId}><img src={selected.src} width="1120" height="480" alt={`Godot sprite lighting: ${selected.label}`} loading="lazy"/><figcaption>{selected.label} · captured in Godot's Compatibility renderer</figcaption></figure>
  </section>;
}
