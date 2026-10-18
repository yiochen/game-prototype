import React, { useEffect, useId, useRef, useState } from 'react';
import { characterScaleStudy, characterVariants, characterScales, characterStudyGeometry, characterScaleMeasurement, characterStudyImage, characterStudySource } from './character-scale-study-data.js';
import characterProportionsUrl from '../design/art-directions/character-proportions-v1.png?url';
import './character-scale-study.css';

const facings = { S: 'Front · S', E: 'Side · E', N: 'Back · N', W: 'Side · W' };
const decimal = value => Number.isFinite(value) ? value.toFixed(2).replace(/0$/, '') : '—';

function TileGuides({ id, cell, gridBounds, roots, footprint, guides }) {
  const [x, y, width, depth] = gridBounds.map(value => value * cell);
  return <>
    <defs><pattern id={id} x={x} y={y} width={cell} height={cell} patternUnits="userSpaceOnUse"><rect width={cell} height={cell} fill="#f0eadc"/><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke="#c9beaa" strokeWidth="1.4"/></pattern></defs>
    <rect x={x} y={y} width={width} height={depth} fill={`url(#${id})`} data-character-grid="true"/>
    {guides && <g className="character-scale-tile-guides">{roots.map(([rx, ry], index) => <g key={index} transform={`translate(${rx * cell} ${ry * cell})`}>
      <rect x={-cell / 2} y={-cell / 2} width={cell} height={cell} className="character-scale-cell-bound"/>
      {Number.isFinite(footprint?.width) && Number.isFinite(footprint?.depth) && <rect x={-footprint.width * cell / 2} y={-footprint.depth * cell / 2} width={footprint.width * cell} height={footprint.depth * cell} className="character-scale-ground-bound"/>}
    </g>)}</g>}
  </>;
}
function GroundRoots({ cell, roots, guides }) {
  if (!guides) return null;
  return <g className="character-scale-roots">{roots.map(([x, y], index) => <g key={index} transform={`translate(${x * cell} ${y * cell})`}><path d="M -7 0 H 7 M 0 -7 V 7"/><circle r="2.5"/></g>)}</g>;
}

function CharacterCapture({ variant, scale, direction, tilePitch, guides }) {
  const id = useId();
  const host = useRef(null);
  const [near, setNear] = useState(false);
  const geometry = characterStudyGeometry(variant);
  const entry = characterScaleMeasurement(variant, scale);
  const path = entry?.images?.[direction];
  const url = characterStudyImage(path);
  const camera = characterStudySource(entry?.cameras?.[direction]);
  useEffect(() => {
    if (!host.current) return;
    if (!('IntersectionObserver' in window)) { setNear(true); return; }
    const observer = new IntersectionObserver(entries => setNear(entries[0].isIntersecting), { root: null, rootMargin: '200px 160px' });
    observer.observe(host.current);
    return () => observer.disconnect();
  }, [url]);
  if (!geometry || !url) return <div className="character-scale-pending" role="status">Awaiting native {variant.id} · {scale.label} · {direction} capture</div>;
  const { cell, frameSize, root, bounds } = geometry;
  return <figure ref={host} className="character-scale-capture" style={{ width: frameSize[0] / cell * tilePitch }} data-character-variant={variant.id} data-character-scale={scale.id} data-character-direction={direction} data-capture-mounted={near ? 'true' : 'false'}>
    <svg viewBox={bounds.join(' ')} width={frameSize[0] / cell * tilePitch} height={frameSize[1] / cell * tilePitch} role="img" aria-label={`${variant.name}, ${scale.label}, ${facings[direction]}`} data-frame-root={root.join(' ')} data-cell-size={cell} data-tile-pitch={tilePitch}>
      <TileGuides id={id} cell={cell} gridBounds={[-.5, -.5, 1, 1]} roots={[[0, 0]]} footprint={entry.footprint} guides={guides}/>
      {near && <image href={url} x={-root[0]} y={-root[1]} width={frameSize[0]} height={frameSize[1]} preserveAspectRatio="none" data-character-source={path}/>}
      <GroundRoots cell={cell} roots={[[0, 0]]} guides={guides}/>
    </svg>
    <figcaption><strong>{facings[direction]}</strong><span><a href={url} target="_blank" rel="noopener noreferrer">Native PNG ↗</a>{camera && <a href={camera} target="_blank" rel="noopener noreferrer">Camera ↗</a>}</span></figcaption>
  </figure>;
}

function Measurements({ entry }) {
  return <div className="character-scale-measurements">
    <p><span>Turning footprint envelope</span><strong>{decimal(entry?.footprint?.width)} × {decimal(entry?.footprint?.depth)} tiles</strong></p>
    <p><span>On-screen height · hat included</span><strong>{decimal(entry?.heightTiles)} tiles</strong></p>
    <p><span>Widest on-screen facing</span><strong>{decimal(entry?.projectedWidthTiles)} tile</strong></p>
    <span className={`character-scale-fit${entry?.fitsOneTile === true ? ' is-fit' : entry?.fitsOneTile === false ? ' is-over' : ''}`}>{entry?.fitsOneTile === true ? '✓ Fits one floor cell' : entry?.fitsOneTile === false ? 'Exceeds one floor cell' : 'Native measurements pending'}</span>
  </div>;
}

function CharacterArrangement({ variant, scale, direction, tilePitch, guides }) {
  const id = useId();
  const geometry = characterStudyGeometry(variant);
  const entry = characterScaleMeasurement(variant, scale);
  const url = characterStudyImage(entry?.images?.[direction]);
  if (!geometry || !url) return null;
  const { cell, frameSize, root } = geometry;
  const roots = Array.from({ length: 9 }, (_, index) => [index % 3, Math.floor(index / 3)]);
  const bounds = [-root[0], -root[1], frameSize[0] + cell * 2, frameSize[1] + cell * 2];
  return <div className="character-scale-arrangement-scroll" tabIndex="0" role="region" aria-label="Pan the three by three character tile layout horizontally">
    <svg className="character-scale-arrangement" viewBox={bounds.join(' ')} width={bounds[2] / cell * tilePitch} height={bounds[3] / cell * tilePitch} role="img" aria-label={`Three by three tile layout: ${variant.name}, ${scale.label}, ${facings[direction]}`} data-layout-variant={variant.id} data-layout-scale={scale.id} data-layout-direction={direction} data-tile-pitch={tilePitch}>
      <TileGuides id={id} cell={cell} gridBounds={[-.5, -.5, 3, 3]} roots={roots} footprint={entry.footprint} guides={guides}/>
      {roots.map(([x, y], index) => <image key={index} href={url} x={x * cell - root[0]} y={y * cell - root[1]} width={frameSize[0]} height={frameSize[1]} preserveAspectRatio="none" data-character-placement={index}/>)}
      <GroundRoots cell={cell} roots={roots} guides={guides}/>
    </svg>
  </div>;
}

export function CharacterScaleStudy() {
  const [tilePitch, setTilePitch] = useState(64);
  const [pair, setPair] = useState('front');
  const [guides, setGuides] = useState(true);
  const [layoutVariant, setLayoutVariant] = useState('C');
  const [layoutScale, setLayoutScale] = useState('150');
  const [layoutDirection, setLayoutDirection] = useState('S');
  const directions = pair === 'front' ? ['S', 'E'] : ['N', 'W'];
  const variant = characterVariants.find(item => item.id === layoutVariant) || characterVariants[0];
  const scale = characterScales.find(item => item.id === layoutScale) || characterScales[0];
  const count = characterVariants.reduce((sum, item) => sum + characterScales.reduce((subtotal, size) => subtotal + Object.values(item.scales?.[size.id]?.images || {}).filter(path => characterStudyImage(path)).length, 0), 0);
  const geometry = characterVariants.map(item => characterStudyGeometry(item)).find(Boolean);
  const columnWidth = geometry ? geometry.frameSize[0] / geometry.cell * tilePitch * 2 + 24 : 424;
  return <div className="phone-scene character-scale-study">
    <header className="character-scale-header">
      <div className="character-scale-kicker"><span>CHARACTER PROPORTION STUDY</span><span className="character-scale-badge">Blender stills · 35° camera</span></div>
      <h2>B and C, on the same tiles.</h2>
      <p>Compare Playful and Chunky at 100%, 125% and 150%. Tiny feet, short leg stubs and fuller side volume are modeled in 3D; the camera stays at 35°. Every image retains the same native canvas, ground root and pixels per tile.</p>
      <nav aria-label="Related art reviews"><a href="#projection-study">Projection & concept reference ↗</a><a href="#scene-restaurant">Restaurant scene ↗</a><a href="#object-library">Production library ↗</a></nav>
      <p className="character-scale-status" role="status">{count} / 24 native captures · 2 designs · 3 scales · 4 directions</p>
    </header>
    <div className="character-scale-controls" aria-label="Character comparison controls">
      <label>Tile size<select aria-label="Character study tile size" value={tilePitch} onChange={event => setTilePitch(Number(event.target.value))}><option value="64">64 px</option><option value="80">80 px</option><option value="96">96 px</option></select></label>
      <label>View pair<select aria-label="Character view pair" value={pair} onChange={event => setPair(event.target.value)}><option value="front">Front + right side</option><option value="back">Back + left side</option></select></label>
      <label className="character-scale-check"><input type="checkbox" checked={guides} onChange={event => setGuides(event.target.checked)}/> Tile & footprint guides</label>
      <p>Orange square: one floor cell. Dotted box: the footprint envelope across all four facings. Cross: tile-center ground root. Height may rise above one tile; width and ground occupancy must stay inside it.</p>
    </div>
    {!characterVariants.length && <p className="character-scale-empty">Native Blender stills are being prepared. The study will show measured captures without substitute artwork.</p>}
    {!!characterVariants.length && <section className="character-scale-comparison-section" aria-labelledby="character-scale-comparison-title">
      <div className="character-scale-section-heading"><span>01 · B / C AT ONE WORLD SCALE</span><h3 id="character-scale-comparison-title">Compare the face and the side volume</h3><p>The three scale columns share one tile pitch. Pan sideways across the columns; use View pair to inspect the other two directions. Measurements cover all four facings.</p></div>
      <div className="character-scale-comparison-scroll" tabIndex="0" role="region" aria-label="Pan B and C scale comparisons horizontally">
        <table className="character-scale-table" style={{ '--character-scale-column': `${columnWidth}px` }}>
          <thead><tr><th scope="col">Native 35° camera</th>{characterScales.map(size => <th scope="col" key={size.id}><strong>{size.label}</strong><span>actual model scale</span></th>)}</tr></thead>
          <tbody>{characterVariants.map(item => <tr key={item.id} data-character-design={item.id}><th scope="row"><span className="character-scale-design-letter">{item.id}</span><strong>{item.name.replace(/^[BC][ ·—-]*/, '')}</strong><p>{item.description}</p></th>{characterScales.map(size => <td key={size.id} data-character-comparison={`${item.id}-${size.id}`}><div className="character-scale-facing-pair">{directions.map(direction => <CharacterCapture key={direction} variant={item} scale={size} direction={direction} tilePitch={tilePitch} guides={guides}/>)}</div><Measurements entry={characterScaleMeasurement(item, size)}/></td>)}</tr>)}</tbody>
        </table>
      </div>
    </section>}
    {variant && <section className="character-scale-layout-section" aria-labelledby="character-scale-layout-title">
      <div className="character-scale-section-heading"><span>02 · NEIGHBORING TILES</span><h3 id="character-scale-layout-title">Nine characters, one root per tile</h3><p>Check the spacing and overlap in a 3 × 3 tile layout. These are repeated registered sprites, drawn back to front, at the same tile pitch as the comparison above.</p></div>
      <div className="character-scale-controls character-scale-layout-controls">
        <label>Design<select aria-label="Tile layout character design" value={variant.id} onChange={event => setLayoutVariant(event.target.value)}>{characterVariants.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>Scale<select aria-label="Tile layout character scale" value={scale.id} onChange={event => setLayoutScale(event.target.value)}>{characterScales.map(size => <option key={size.id} value={size.id}>{size.label}</option>)}</select></label>
        <label>Facing<select aria-label="Tile layout character facing" value={layoutDirection} onChange={event => setLayoutDirection(event.target.value)}>{Object.entries(facings).map(([direction, label]) => <option key={direction} value={direction}>{label}</option>)}</select></label>
      </div>
      <CharacterArrangement variant={variant} scale={scale} direction={layoutDirection} tilePitch={tilePitch} guides={guides}/>
    </section>}
    <details className="character-scale-concept-reference"><summary>Original ImageGen proportion concepts</summary><figure><a href={characterProportionsUrl} target="_blank" rel="noopener noreferrer"><img src={characterProportionsUrl} alt="Original A Compact, B Playful, C Chunky and D Super chibi character proportion concepts" width="1774" height="887" loading="lazy"/></a><figcaption>B and C are the modeling references. The image concept was not tile-calibrated; the measured Blender captures above define this comparison.</figcaption></figure></details>
    <footer className="character-scale-footer"><p>The square guides show the game’s floor layout. Character meshes keep the separate ordinary 35° camera, whose depth is naturally foreshortened. The selected 70% environment height is awaiting production recapture; this page compares characters only.</p><p>One fixed pose per direction; no animation or production character replacement is included. Final scene-asset approval and issue #33 remain open.</p>{(characterScaleStudy.source?.blend || characterScaleStudy.nativeProject) && <a href={characterStudySource(characterScaleStudy.source?.blend || characterScaleStudy.nativeProject)} target="_blank" rel="noopener noreferrer">Editable Blender study source ↗</a>}</footer>
  </div>;
}
