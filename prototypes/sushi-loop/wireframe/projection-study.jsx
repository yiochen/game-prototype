import React, { useEffect, useId, useRef, useState } from 'react';
import { projectionStudy, projectionGroups, projectionRatios, studyGeometry, studyImageUrl, studySourceUrl } from './projection-study-data.js';
import './projection-study.css';
import characterProportionsUrl from '../design/art-directions/character-proportions-v1.png?url';

function StudyCapture({ group, ratio, tilePitch, overlays, reference = false }) {
  const patternId = useId();
  const host = useRef(null);
  const [near, setNear] = useState(false);
  const geometry = studyGeometry(group, reference);
  const image = reference ? group.reference?.image : group.images?.[ratio.id];
  const url = studyImageUrl(image);
  useEffect(() => {
    if (!host.current) return;
    if (!('IntersectionObserver' in window)) { setNear(true); return; }
    const observer = new IntersectionObserver(entries => setNear(entries[0].isIntersecting), { root: null, rootMargin: '160px 96px' });
    observer.observe(host.current);
    return () => observer.disconnect();
  }, [url, Boolean(geometry)]);
  if (!geometry || !url) return <div className="projection-capture-pending" role="status">Awaiting native capture</div>;
  const { cell, frameSize, groundRoot, gridBounds, imageX, imageY, bounds } = geometry;
  const camera = studySourceUrl(reference ? group.reference?.camera : group.source?.cameras?.[ratio.id]);
  return <figure ref={host} className="projection-capture" data-capture-mounted={near ? 'true' : 'false'} data-study-group={group.id} data-study-ratio={reference ? 'reference' : ratio.id}>
    <svg viewBox={bounds.join(' ')} width={bounds[2] / cell * tilePitch} height={bounds[3] / cell * tilePitch} role="img" aria-label={`${group.name}: ${reference ? group.reference.label : `${ratio.label} vertical height`}`} data-cell-size={cell} data-tile-pitch={tilePitch} data-frame-root={geometry.root.join(' ')}>
      <defs><pattern id={patternId} x={gridBounds[0] * cell} y={gridBounds[1] * cell} width={cell} height={cell} patternUnits="userSpaceOnUse"><rect width={cell} height={cell} fill="#eff1e7"/><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke="#adbcb1" strokeWidth="1.5"/></pattern></defs>
      <rect x={gridBounds[0] * cell} y={gridBounds[1] * cell} width={gridBounds[2] * cell} height={gridBounds[3] * cell} fill={`url(#${patternId})`} data-study-floor="true"/>
      {near && <image href={url} x={imageX} y={imageY} width={frameSize[0]} height={frameSize[1]} preserveAspectRatio="none" data-study-source={image}/>}
      {!near && <text x={bounds[0] + bounds[2] / 2} y={bounds[1] + bounds[3] / 2} textAnchor="middle" className="projection-deferred">Capture loads near view</text>}
      {overlays && <g className="projection-registration">
        {(group.footprints || []).map((footprint, index) => <rect key={footprint.id || index} x={footprint.x * cell} y={footprint.y * cell} width={footprint.width * cell} height={footprint.depth * cell} className="projection-footprint"/>)}
        <path d={`M ${groundRoot[0] * cell - 10} ${groundRoot[1] * cell} h20 M ${groundRoot[0] * cell} ${groundRoot[1] * cell - 10} v20`}/><circle cx={groundRoot[0] * cell} cy={groundRoot[1] * cell} r="3" data-study-root="true"/>
      </g>}
    </svg>
    <figcaption><span>{reference ? group.reference.label : `Top/floor 100% · height ${ratio.label}`}</span><span className="projection-capture-links"><a href={url} target="_blank" rel="noopener noreferrer">Native PNG ↗</a>{camera && <a href={camera} target="_blank" rel="noopener noreferrer">Camera ↗</a>}</span></figcaption>
  </figure>;
}

function ComparisonTable({ groups, tilePitch, overlays, label }) {
  const logicalWidth = Math.max(0, ...groups.map(group => studyGeometry(group)?.bounds[2] || 0));
  const columnWidth = Math.max(146, logicalWidth / (projectionStudy.cellSize || 128) * tilePitch + 16);
  return <div className="projection-comparison-scroll" tabIndex="0" role="region" aria-label={`Pan ${label} horizontally`}>
    <table className={`projection-comparison-table${groups.every(group => group.kind === 'assembly') ? ' is-assembly' : ''}`} style={{ '--projection-column-width': `${columnWidth}px` }}>
      <thead><tr><th scope="col">Same world scale</th>{projectionRatios.map(ratio => <th scope="col" key={ratio.id}><strong>{ratio.label}</strong><span>vertical height</span></th>)}</tr></thead>
      <tbody>{groups.map(group => <tr key={group.id} data-comparison-group={group.id}><th scope="row"><strong>{group.name}</strong>{group.description && <p>{group.description}</p>}<small>{group.kind === 'assembly' ? 'Connected arrangement' : 'Single native object'}</small></th>{projectionRatios.map(ratio => <td key={ratio.id}><StudyCapture group={group} ratio={ratio} tilePitch={tilePitch} overlays={overlays}/></td>)}</tr>)}</tbody>
    </table>
  </div>;
}

export function ProjectionStudy() {
  const [tilePitch, setTilePitch] = useState(48);
  const [overlays, setOverlays] = useState(true);
  const objects = projectionGroups.filter(group => group.kind !== 'assembly');
  const assemblies = projectionGroups.filter(group => group.kind === 'assembly');
  const references = projectionGroups.filter(group => group.reference);
  const count = projectionGroups.reduce((sum, group) => sum + projectionRatios.filter(ratio => studyImageUrl(group.images?.[ratio.id])).length, 0);
  return <div className="phone-scene projection-study">
    <header className="projection-study-header">
      <div className="projection-study-kicker"><span>PROJECTION STUDY</span><span className="projection-study-badge">70% environment selected</span></div>
      <h2>Same tiles. Four heights.</h2>
      <p>70% environment height is selected. Production recapture is pending; characters will keep their separate 35° ordinary orthographic camera. The historical comparisons below retain their original geometry and registration.</p>
      <nav aria-label="Art review pages"><a href="#character-scale-study">B / C Blender scale comparison ↗</a><a href="#scene-restaurant">Restaurant scene ↗</a><a href="#scene-underwater">Underwater scene ↗</a><a href="#object-library">Production library ↗</a></nav>
      <p className="projection-study-status" role="status">{count} comparison captures · {references.filter(group => studyImageUrl(group.reference.image)).length} camera reference · {projectionGroups.length} comparisons</p>
    </header>
    <section className="projection-character-concepts" aria-labelledby="character-proportions-title">
      <div className="projection-section-heading"><span>NEXT · CHARACTER SHAPE</span><h3 id="character-proportions-title">Character proportions · choose a direction</h3><p>Four concepts for Lena with shorter legs and a more cartoony silhouette: A · Compact, B · Playful, C · Chunky, D · Super chibi. The intended camera stays at 35° ordinary orthographic.</p></div>
      <figure><a href={characterProportionsUrl} target="_blank" rel="noopener noreferrer" aria-label="Open full-size character proportion concepts"><img src={characterProportionsUrl} alt="Lena character proportion concepts: A Compact, B Playful, C Chunky and D Super chibi" width="1774" height="887"/></a><figcaption>ImageGen anatomy concepts for choosing proportions. These are not calibrated Blender captures or registered sprites. <a href={characterProportionsUrl} target="_blank" rel="noopener noreferrer">Open full-size concept board ↗</a></figcaption></figure>
    </section>
    <div className="projection-study-controls" aria-label="Projection comparison controls">
      <label>World scale<select aria-label="Study tile size" value={tilePitch} onChange={event => setTilePitch(Number(event.target.value))}><option value="48">48 px / tile</option><option value="64">64 px / tile</option><option value="96">96 px / tile</option></select></label>
      <label className="projection-overlay-toggle"><input type="checkbox" checked={overlays} onChange={event => setOverlays(event.target.checked)}/> Ground roots</label>
      <p>One display scale for every object and ratio. Pan comparison columns sideways; scroll the page vertically.</p>
    </div>
    {!projectionGroups.length && <p className="projection-study-empty">Native study captures are being prepared. Each published ratio will appear here without substitute artwork.</p>}
    {!!objects.length && <section className="projection-study-section"><div className="projection-section-heading"><span>01 · INDIVIDUAL OBJECTS</span><h3>Read the silhouette and side faces</h3><p>Every column uses its declared capture canvas and the same world pitch. The images are displayed uniformly; no alpha fitting or browser height squash is applied.</p></div><ComparisonTable groups={objects} tilePitch={tilePitch} overlays={overlays} label="individual projection comparisons"/></section>}
    {!!references.length && <section className="projection-study-section projection-reference-section"><div className="projection-section-heading"><span>CHARACTER CAMERA REFERENCE</span><h3>The current character camera is separate</h3><p>The chef’s four study captures above use the environment projection. This additional reference uses the current 35° ordinary orthographic character camera; it is not the 100% environment baseline.</p></div><div className="projection-reference-scroll">{references.map(group => <div className="projection-character-reference" key={group.id}><h4>{group.name}</h4><StudyCapture group={group} reference tilePitch={tilePitch} overlays={overlays}/></div>)}</div></section>}
    {!!assemblies.length && <section className="projection-study-section"><div className="projection-section-heading"><span>02 · SHARED ARRANGEMENT</span><h3>Compare the connected group</h3><p>Conveyor joins and neighboring props use one captured native arrangement in all four projections. The wider comparison retains the same tile size as the individual objects.</p></div><ComparisonTable groups={assemblies} tilePitch={tilePitch} overlays={overlays} label="connected projection arrangement"/></section>}
    <footer className="projection-study-footer"><p>70% environment height has been selected; production recapture is pending. The original comparison captures stay here as a reference. Characters retain the separate 35° camera while their proportions are reviewed. Final asset approval and Godot Android integration remain separate review steps.</p><p>Ambient and contact shading are deferred to Godot. This page adds only square calibration lines and optional registration guides.</p></footer>
  </div>;
}
