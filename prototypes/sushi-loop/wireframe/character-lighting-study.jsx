import React, { useId, useState } from 'react';
import { lightingStudy, lightingVariants, lightingImage, lightingCapture, lightingSource } from './character-lighting-study-data.js';
import conceptUrl from '../design/art-directions/restaurant-concept.png?url';
import './character-lighting-study.css';

const facingNames = { S: 'Front · South', E: 'Right side · East', N: 'Back · North', W: 'Left side · West' };
function Capture({ variant, direction, guides }) {
  const id = useId();
  const entry = lightingCapture(variant, direction);
  const url = lightingImage(entry?.image);
  const cell = lightingStudy.cellSize;
  const frame = lightingStudy.frame || lightingStudy.frameSize;
  const root = lightingStudy.root;
  const crop = variant.hatCrop || lightingStudy.hatCrop;
  const validCrop = Array.isArray(crop) && crop.length === 4 && crop.every(Number.isFinite);
  return <article className="lighting-variant" data-lighting-variant={variant.id}>
    <header><h3>{variant.name}</h3><p>{variant.description}</p></header>
    {url ? <figure>
      <svg className="lighting-capture" viewBox={[-root[0], -root[1], ...frame].join(' ')} role="img" aria-label={`${variant.name}: ${facingNames[direction]}`} data-lighting-direction={direction} data-frame-root={root.join(' ')} data-cell-size={cell}>
        <defs><pattern id={id} width={cell} height={cell} patternUnits="userSpaceOnUse" x={-cell / 2} y={-cell / 2}><rect width={cell} height={cell} fill="#f4e9cb"/><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke="#cabb9a" strokeWidth="1.5"/></pattern></defs>
        <rect x={-cell / 2} y={-cell / 2} width={cell} height={cell} fill={`url(#${id})`} data-lighting-floor="true"/>
        <image href={url} x={-root[0]} y={-root[1]} width={frame[0]} height={frame[1]} preserveAspectRatio="none" data-lighting-source={entry.image}/>
        {guides && <g className="lighting-ground-guides"><rect x={-cell / 2} y={-cell / 2} width={cell} height={cell}/><path d="M -7 0 H 7 M 0 -7 V 7"/><circle r="2"/></g>}
      </svg>
      <figcaption><span>{facingNames[direction]}</span><a href={url} target="_blank" rel="noopener noreferrer">Native PNG ↗</a></figcaption>
      {validCrop && <div className="lighting-hat-comparison"><p>Hat detail</p><svg className="lighting-hat-detail" viewBox={crop.join(' ')} role="img" aria-label={`${variant.name}: enlarged hat detail`}><image href={url} width={frame[0]} height={frame[1]} preserveAspectRatio="none"/></svg></div>}
    </figure> : <p className="lighting-pending" role="status">Native capture pending.</p>}
  </article>;
}

export function CharacterLightingStudy() {
  const [direction, setDirection] = useState('S');
  const [guides, setGuides] = useState(true);
  const blend = lightingSource(lightingStudy.source?.blend);
  const recipe = lightingSource(lightingStudy.source?.recipe);
  const count = lightingVariants.reduce((sum, variant) => sum + ['N', 'E', 'S', 'W'].filter(facing => lightingImage(lightingCapture(variant, facing)?.image)).length, 0);
  return <div className="phone-scene character-lighting-study">
    <header className="lighting-study-header"><span className="lighting-eyebrow">ONE CHARACTER · NATIVE BLENDER LIGHTING</span><h2>Light on Noor’s green hat.</h2><p>Compare the current emission baseline with three overhead-light treatments. Look for a readable light top and darker sides while keeping the face clear. C125 anatomy, the 35° camera and native 135% contrast stay fixed.</p><nav aria-label="Lighting study sources"><a href="#object-chef-noor">Noor in the production library ↗</a>{blend && <a href={blend} target="_blank" rel="noopener noreferrer">Editable Blender study ↗</a>}{recipe && <a href={recipe} target="_blank" rel="noopener noreferrer">Lighting recipe ↗</a>}</nav><p className="lighting-study-status" role="status">{count} / 16 native stills · isolated study · production unchanged</p></header>
    <div className="lighting-study-controls"><label>Facing<select aria-label="Lighting study facing" value={direction} onChange={event => setDirection(event.target.value)}>{['S', 'E', 'N', 'W'].map(value => <option key={value} value={value}>{facingNames[value]}</option>)}</select></label><label><input type="checkbox" checked={guides} onChange={event => setGuides(event.target.checked)}/> Tile &amp; root guides</label></div>
    <section className="lighting-comparison" aria-label="Baseline and three native lighting candidates">{lightingVariants.map(variant => <Capture key={variant.id} variant={variant} direction={direction} guides={guides}/>)}</section>
    {!lightingVariants.length && <p className="lighting-pending" role="status">The isolated Blender lighting captures are being prepared.</p>}
    <p className="lighting-registration-note">Every capture uses the same {lightingStudy.frame?.join(' × ') || '192 × 320'} logical frame and ground root. Native PNGs are displayed directly, without browser image filters. Use Comments to review the lighting before changing production assets.</p>
    <details className="lighting-concept-reference"><summary>Original restaurant concept reference</summary><figure><img src={conceptUrl} width="1024" height="1536" alt="Original restaurant concept art with bright top planes and shaded sides on characters and furniture."/><figcaption>The original concept is preserved unchanged.</figcaption></figure></details>
  </div>;
}
