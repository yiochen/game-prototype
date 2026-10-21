import React, { useEffect, useId, useRef, useState } from 'react';
import { libraryObjects, spriteLibrary, imageUrl, objectStoryId, finalAssetsApproved, productionArtStatus, refinementProgress, refinementById, refinementImageUrl } from './object-review-data.js';
import { DIRECTIONS, DIRECTION_NAMES, clipFor, spriteFrame, sceneBounds, orderPlacements, repeatedPlacements, directionPlacements, placementAtTime, reviewFrameCount, groundRoot, attachmentMarkers, footprintFor, reviewDirections, resolveSupportSocket } from './sprite-layout.js';
import './object-review.css';
import { RestaurantBackdrop } from './restaurant-backdrop.jsx';
import { useWorldSpriteRaster } from './world-sprite-raster.js';

const objectsById = new Map(libraryObjects.map(object => [object.id, object]));
const statuses = { ready: finalAssetsApproved ? 'Approved' : 'Ready to review', working: 'In production', queued: 'Queued' };
const refinementLabels = { queued: 'Refinement queued', skipped: 'Original floor retained', 'reviewing-baseline': 'Defining visual criteria', editing: 'Editor working', reviewing: 'Judge reviewing', approved: 'Warm cartoon approved', published: 'Warm cartoon published' };
const statusText = object => refinementProgress ? refinementLabels[refinementById.get(object.id)?.status] || 'Refinement queued' : statuses[object.status] || 'Queued';
const blendSourceUrl = path => {
  if (!path || path.startsWith('/') || path.split('/').includes('..')) return null;
  return `https://github.com/yiochen/game-prototype/blob/${refinementProgress?.branch || 'codex/sushi-loop-33-art-catalog'}/prototypes/sushi-loop/assets/production/${path.split('/').map(encodeURIComponent).join('/')}`;
};
const primaryClip = object => object.clips?.find(clip => clip.id === 'idle') || object.clips?.[0];
const backdropModelUrl = new URL('../assets/production/source/backdrop/restaurant-backdrop-35.blend', import.meta.url).href;
const exported = object => object.clips?.some(clip => DIRECTIONS.some(direction => imageUrl(clip.directions?.[direction]?.image)));

export function SpriteScene({ placements, gridSize = [3, 3], seconds = 0, overlays = false, zoom = 1, label, labels = false, floorId, showGrid = true, background = '#eef2ed', animateFloor = false, sceneId, cameraBounds, backdropRenderer = 'uniform35' }) {
  const pattern = useId();
  const cell = spriteLibrary.cellSize || 128;
  const firstObject = libraryObjects.find(object => object.id === placements[0]?.object);
  const underwater = Number(firstObject?.family?.replace('W', '')) >= 11;
  const floor = objectsById.get(floorId || (underwater ? 'floor-underwater' : 'floor-plain')) || (!underwater && objectsById.get('floor-cream'));
  const floorFrame = spriteFrame(floor, floor && primaryClip(floor), 'S', animateFloor ? seconds : 0);
  const floorUrl = imageUrl(floorFrame?.image);
  // A composed world has an authored camera; object studies still include their full capture canvases.
  const supportedPlacements = placements.map(placement => resolveSupportSocket(placement, objectsById));
  const bounds = cameraBounds ? cameraBounds.map(value => value * cell) : sceneBounds(supportedPlacements, libraryObjects, cell, gridSize);
  const timedPlacements = supportedPlacements.map(placement => placementAtTime(placement, seconds, objectsById.get(placement.object)));
  const sprites = orderPlacements(timedPlacements, libraryObjects).map(placement => {
    const object = objectsById.get(placement.object);
    if (!object) return { placement };
    const direction = object.facingPolicy === 'single-player-facing' ? 'S' : placement.direction || 'S';
    const clip = clipFor(object, placement.clip);
    const frame = spriteFrame(object, clip, direction, Math.max(0, seconds + (Number(placement.timeOffset) || 0)));
    const url = imageUrl(frame?.image);
    const [x, y] = groundRoot(placement, object, cell);
    return { placement, object, direction, clip, frame, url, x, y };
  });
  const raster = useWorldSpriteRaster(sprites.filter(sprite => sprite.url).map(({ url, frame, x, y }) => ({
    url, rect: frame.rect, x: x - frame.root[0], y: y - frame.root[1], width: frame.frameSize[0], height: frame.frameSize[1],
  })), bounds);
  return <div className="object-scene-scroll" style={{ background }} tabIndex={0} aria-label={`Pan ${label}`} data-scene-id={sceneId}>
    <svg className="object-tile-scene" style={{ width: `${zoom * 100}%`, background }} viewBox={bounds.join(' ')} role="img" aria-label={label} data-world-raster-ready={raster.ready} data-world-raster-error={raster.error || undefined}>
      <defs><pattern id={pattern} width={cell} height={cell} patternUnits="userSpaceOnUse">{floorUrl && <svg width={cell} height={cell} viewBox={floorFrame.rect.join(' ')} overflow="hidden" preserveAspectRatio="none"><image href={floorUrl} width={floorFrame.atlasSize[0]} height={floorFrame.atlasSize[1]} data-floor-source={floorFrame.image}/></svg>}{showGrid && <path d={`M ${cell} 0 L 0 0 0 ${cell}`} fill="none" stroke="#a8b7b6" strokeWidth="1.5" data-calibration-grid="true"/>}</pattern></defs>
      <rect x="0" y="0" width={gridSize[0] * cell} height={gridSize[1] * cell} fill="#f2f0e6"/>
      <rect x="0" y="0" width={gridSize[0] * cell} height={gridSize[1] * cell} fill={`url(#${pattern})`}/>
      {sceneId === 'restaurant' && <RestaurantBackdrop columns={gridSize[0]} cell={cell} showGrid={showGrid} renderer={backdropRenderer}/>}
      <foreignObject x={raster.plan.x} y={raster.plan.y} width={raster.plan.width / raster.plan.scale} height={raster.plan.height / raster.plan.scale} pointerEvents="none" style={{ visibility: raster.ready ? 'visible' : 'hidden' }} data-world-sprite-raster="true">
        <canvas ref={raster.canvas} style={{ display: 'block', width: '100%', height: '100%' }}/>
      </foreignObject>
      {sprites.map(({ placement, object, direction, clip, frame, url, x, y }, index) => {
        if (!object) return <g key={index}><title>Comparison object {placement.object} is not yet cataloged</title></g>;
        const footprint = footprintFor(object, direction);
        return <g key={placement.id || placement._index} data-placement={placement.id || `${object.id}-${placement._index}`} data-object={object.id} data-direction={direction} data-frame={url ? frame.frame : undefined} data-support-offset={placement.supportSocket ? JSON.stringify(placement.supportOffset) : undefined}>
          <title>{object.name}, {DIRECTION_NAMES[direction]}{url ? `, ${clip.name || clip.id}, frame ${frame.frame + 1} of ${frame.frames}` : ': export pending'}</title>
          {overlays && <rect x={placement.x * cell} y={placement.y * cell} width={footprint[0] * cell} height={footprint[1] * cell} className="object-footprint"/>}
          {url ? <svg x={x - frame.root[0]} y={y - frame.root[1]} width={frame.frameSize[0]} height={frame.frameSize[1]} viewBox={frame.rect.join(' ')} overflow="hidden" preserveAspectRatio="none" data-sprite-source={frame.image} opacity={raster.ready ? 0 : undefined}><image href={url} width={frame.atlasSize[0]} height={frame.atlasSize[1]}/></svg> : <g className="object-export-pending"><rect x={x - cell * .4} y={y - cell * .6} width={cell * .8} height={cell * .8} rx="8"/><text x={x} y={y - cell * .25} textAnchor="middle">Pending</text></g>}
          {overlays && attachmentMarkers(object, clip, direction).map((marker, markerIndex) => <g key={markerIndex} className={`object-attachment is-${marker.kind}`} data-attachment={marker.name}><circle cx={x + marker.position[0]} cy={y + marker.position[1]} r="5"/><text x={x + marker.position[0] + 8} y={y + marker.position[1] - 6}>{marker.name}</text></g>)}
          {overlays && <g className="object-root"><path d={`M ${x - 9} ${y} H ${x + 9} M ${x} ${y - 9} V ${y + 9}`}/><circle cx={x} cy={y} r="3"/></g>}
          {labels && <text className="object-direction-label" x={x} y={cell * gridSize[1] - 12} textAnchor="middle">{DIRECTION_NAMES[direction]}</text>}
        </g>;
      })}
    </svg>
  </div>;
}

export function usePlayback(maxFrames, { autoPlay = true } = {}) {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(() => autoPlay && !window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const frameRef = useRef(frame); frameRef.current = frame;
  useEffect(() => {
    if (!playing || maxFrames <= 1) return;
    let request, start, initial = frameRef.current;
    const tick = time => {
      start ??= time;
      setFrame((initial + Math.floor((time - start) * 12 / 1000)) % maxFrames);
      request = requestAnimationFrame(tick);
    };
    const visibility = () => { if (document.hidden) setPlaying(false); };
    document.addEventListener('visibilitychange', visibility);
    request = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(request); document.removeEventListener('visibilitychange', visibility); };
  }, [playing, maxFrames]);
  return { frame, playing: playing && maxFrames > 1, toggle: () => setPlaying(value => !value), scrub: value => { setPlaying(false); setFrame(Number(value)); } };
}

// A thumbnail retains its authored canvas. Only nearby cards mount an atlas image.
function LibraryThumbnail({ object }) {
  const host = useRef(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => setNear(entries[0].isIntersecting), { root: null, rootMargin: '96px 0px' });
      observer.observe(element);
      return () => observer.disconnect();
    }
    const measure = () => { const bounds = element.getBoundingClientRect(); setNear(bounds.bottom >= -96 && bounds.top <= window.innerHeight + 96); };
    measure(); window.addEventListener('scroll', measure, { passive: true }); window.addEventListener('resize', measure);
    return () => { window.removeEventListener('scroll', measure); window.removeEventListener('resize', measure); };
  }, []);
  const available = clip => DIRECTIONS.some(direction => imageUrl(clip.directions?.[direction]?.image));
  const clip = object.clips?.find(clip => clip.id === 'idle' && available(clip)) || object.clips?.find(available);
  const direction = ['S', 'N', 'E', 'W'].find(direction => imageUrl(clip?.directions?.[direction]?.image));
  const frame = direction && spriteFrame(object, clip, direction, 0);
  const url = imageUrl(frame?.image);
  const footprint = footprintFor(object, direction);
  const rootCell = object.directionRootCells?.[direction] || object.rootCell || [footprint[0] / 2, footprint[1] / 2];
  const cell = spriteLibrary.cellSize || 128;
  return <span ref={host} className="object-library-thumbnail" data-thumbnail-object={object.id} data-thumbnail-state={!url ? 'queued' : near ? 'mounted' : 'deferred'} aria-hidden="true">
    {near && url ? <svg viewBox={`0 0 ${frame.frameSize[0]} ${frame.frameSize[1]}`} preserveAspectRatio="xMidYMid meet">
      <rect x={frame.root[0] - rootCell[0] * cell} y={frame.root[1] - rootCell[1] * cell} width={footprint[0] * cell} height={footprint[1] * cell} fill="#e9e8dc" stroke="#b3c2b3" strokeWidth="2"/>
      <svg width={frame.frameSize[0]} height={frame.frameSize[1]} viewBox={frame.rect.join(' ')} overflow="hidden" preserveAspectRatio="none" data-thumbnail-source={frame.image}><image href={url} width={frame.atlasSize[0]} height={frame.atlasSize[1]}/></svg>
    </svg> : <span>{url ? 'Preview' : 'Queued'}</span>}
  </span>;
}

function ObjectLibrary() {
  const [filter, setFilter] = useState('');
  const [state, setState] = useState(() => libraryObjects.some(exported) ? 'exported' : 'all');
  const visible = libraryObjects.filter(object => `${object.name} ${object.family} ${object.id}`.toLowerCase().includes(filter.toLowerCase()) && (state === 'all' || (state === 'refined' ? ['approved', 'published'].includes(refinementById.get(object.id)?.status) : state === 'exported' ? exported(object) : !exported(object))));
  const count = libraryObjects.filter(exported).length;
  return <div className="phone-scene object-review-scene">
    <header className="object-review-header"><span className="object-review-eyebrow">ISSUE 33 · PRODUCTION REVIEW</span><h2>Object library</h2><p>Inspect registered native and 2D sprites, facings, interactions and animations.</p><p className="object-library-progress" role="status">{refinementProgress ? `${refinementProgress.completed} / ${refinementProgress.total} warm cartoon objects approved` : `${count} with exports · ${libraryObjects.length - count} awaiting exports`}</p>{refinementProgress && <p className="object-refinement-summary">Warm, softly lit cartoon rollout. Restaurant floor tiles retain their original art. Each included object gets a fresh editor and independent judge. Approved exports appear here as work continues; queued objects retain their original art.</p>}</header>
    <div className="object-review-scroll" aria-label="Scroll production object library">
      <nav className="object-showcase-links" aria-label="Full scene previews"><a href="#scene-restaurant">Restaurant scene ↗</a><a href="#scene-underwater">Underwater scene ↗</a></nav>
      <div className="object-library-filters"><label>Find an object<input type="search" value={filter} onChange={event => setFilter(event.target.value)} placeholder="Chef, belt, stool…"/></label><label>Show<select value={state} onChange={event => setState(event.target.value)}><option value="all">All objects</option><option value="exported">With sprite exports</option>{refinementProgress && <option value="refined">Warm cartoon approved</option>}<option value="queued">Awaiting exports</option></select></label></div>
      {!libraryObjects.length && <p className="object-queued-note">Blender production is starting. Object pages will appear here as the inventory is registered.</p>}
      {!!libraryObjects.length && !visible.length && <p className="object-queued-note">No objects match this filter.</p>}
      <div className="object-library-list">{visible.map(object => <a className="object-library-card" href={`#${objectStoryId(object)}`} key={object.id}><LibraryThumbnail object={object}/><span className="object-library-card-text"><small className="object-family">{object.family} · {object.id}</small><strong>{object.name}</strong><span className="object-card-meta">{object.footprint?.join(' × ') || '1 × 1'} cells · {object.clips?.length || 0} registered states</span><span className={`object-status is-${object.status || 'queued'}`}>{statusText(object)}</span></span><span aria-hidden="true">↗</span></a>)}</div>
      <a className="object-concept-return" href="#art-catalog">View approved concept sheet ↗</a>
      <p className="object-queued-note">{productionArtStatus}. Queued states show no substitute artwork.</p>
    </div>
  </div>;
}

function ObjectDetail({ object }) {
  const [overlays, setOverlays] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [direction, setDirection] = useState('S');
  const [clipId, setClipId] = useState(primaryClip(object)?.id || '');
  const [expandedClip, setExpandedClip] = useState(primaryClip(object)?.id || null);
  const clips = object.clips || [];
  const maxFrames = reviewFrameCount(object, libraryObjects);
  const { frame, playing, toggle, scrub } = usePlayback(maxFrames);
  const seconds = frame / 12;
  const currentClip = clipFor(object, clipId);
  const footprint = footprintFor(object, direction);
  const interactions = object.interactions || [];
  const sourceUrl = object.kind === 'backdrop' ? backdropModelUrl : blendSourceUrl(object.source?.blend);
  const cameraFacing = object.facingPolicy === 'camera-facing';
  const singleFacing = object.facingPolicy === 'single-player-facing';
  const lightingSubject = object.id === 'chef-noor' ? 'chef-noor' : object.id === 'crate-wood' ? 'crate-wood' : object.kind === 'belt' ? object.id.startsWith('belt-corner-') ? 'belt-connected' : 'belt-straight' : null;
  const lightingQuery = new URLSearchParams(window.location.search);
  if (lightingSubject) lightingQuery.set('lightingSubject', lightingSubject);
  const lightingHref = `?${lightingQuery.toString()}#character-lighting-study`;
  const directions = reviewDirections(object);
  const artworkUrl = blendSourceUrl(object.source?.artwork || object.source?.godot);
  const artworkLabel = object.source?.artwork ? object.source?.refinedSource ? 'Refined 2D artwork ↗' : 'Original ImageGen artwork ↗' : 'Editable Godot 2D effect ↗';
  const recipeUrl = blendSourceUrl(object.source?.recipe);
  const downloadUrl = object.kind === 'backdrop' ? backdropModelUrl : blendSourceUrl(object.source?.refinedBlend || spriteLibrary.production?.editableProject || object.source?.blend)?.replace('https://github.com/yiochen/game-prototype/blob/', 'https://raw.githubusercontent.com/yiochen/game-prototype/');
  const refinement = refinementById.get(object.id);
  const originalReference = refinementImageUrl(object.id, 'original');
  const styleReference = refinementImageUrl(object.id, 'target');
  const facings = directionPlacements(object, currentClip?.id);
  const extent = Math.max(...DIRECTIONS.flatMap(facing => footprintFor(object, facing)));
  const maxDepth = Math.max(...DIRECTIONS.map(facing => footprintFor(object, facing)[1]));
  const grid = [directions.length * (extent + 1) - 1, Math.max(2, maxDepth + 1)];
  return <div className="phone-scene object-review-scene">
    <header className="object-review-header"><a href="#object-library" className="object-library-return">← Object library</a><div className="object-review-heading"><h2>{object.name}</h2><span className={`object-status is-${object.status || 'queued'}`}>{statusText(object)}</span></div><p>{object.family} · {footprint.join(' × ')} cells · {object.projection === 'screen-space-2d' ? '2D artwork' : object.projection === 'height-dependent-35-square-footing' ? '35° upper view · square footing' : object.projection === 'character-orthographic' ? 'Orthographic art camera' : object.artStyle?.environmentHeightRatio === .7 ? 'Square ground · 70% height' : 'Square top/front grid'}</p>{singleFacing && <p className="object-facing-policy">{object.kind === 'backdrop' ? 'Fixed backdrop surface · three projected tile rows' : 'Single player-facing surface · front of shared tile'}</p>}{object.reviewNote && <p>{object.reviewNote}</p>}{artworkUrl && <div className="object-source-links"><a href={artworkUrl} target="_blank" rel="noopener noreferrer">{artworkLabel}</a>{recipeUrl && <a href={recipeUrl} target="_blank" rel="noopener noreferrer">Editable 2D recipe ↗</a>}</div>}{cameraFacing && <p className="object-facing-policy">Camera-facing artwork · four world-facing contexts</p>}{object.productionStage && <p className="object-production-stage">{object.productionStage}</p>}{lightingSubject && <div className="object-source-links"><a className="object-lighting-study-link" href={lightingHref}>{lightingSubject === 'chef-noor' ? 'Compare Noor’s lighting study ↗' : lightingSubject === 'crate-wood' ? 'Compare wood crate lighting ↗' : 'Compare conveyor lighting ↗'}</a></div>}{sourceUrl && <div className="object-source-links"><a className="object-blend-source" href={sourceUrl} target="_blank" rel="noopener noreferrer">Editable Blender source ↗</a>{downloadUrl && <a className="object-blend-source" href={downloadUrl} download>Download .blend ↓</a>}</div>}</header>
    <div className="object-review-controls" aria-label="Sprite review controls"><div className="object-playback-row"><button type="button" onClick={toggle} disabled={maxFrames <= 1} aria-label={playing ? 'Pause animations' : 'Play animations'}>{playing ? 'Ⅱ Pause' : '▶ Play'}</button><label className="object-scrub">Frame {frame + 1} / {maxFrames}<input aria-label="Animation frame" type="range" min="0" max={maxFrames - 1} value={frame} disabled={maxFrames <= 1} onChange={event => scrub(event.target.value)}/></label><span>12 fps</span></div><div className="object-grid-controls"><label><input type="checkbox" checked={overlays} onChange={event => setOverlays(event.target.checked)}/> Roots &amp; attachments</label><label>Zoom<select aria-label="Scene zoom" value={zoom} onChange={event => setZoom(Number(event.target.value))}><option value="1">Fit</option><option value="2">2×</option><option value="4">4×</option></select></label></div></div>
    <div className="object-review-scroll" aria-label={`Scroll ${object.name} review`}>
      {refinement && <section className="object-review-section object-refinement" data-refinement-status={refinement.status}><h3>Warm cartoon refinement</h3><p>{refinement.status === 'skipped' ? 'Original restaurant floor retained at your request.' : `${statusText(object)} · fresh editor and independent judge for this object.`}</p>{refinement.remainingDifferences && <p>{refinement.remainingDifferences.join(' ')}</p>}{originalReference && styleReference && <details><summary>Compare original export and style target</summary><div className="object-refinement-references"><figure><img src={originalReference} alt={`${object.name}, original export`} loading="lazy"/><figcaption>Original export</figcaption></figure><figure><img src={styleReference} alt={`${object.name}, imagegen style target`} loading="lazy"/><figcaption>Imagegen target · geometry may drift</figcaption></figure></div></details>}</section>}
      {!exported(object) && <p className="object-queued-note">This object is queued for Blender export. The grids below document its review layout; no finished sprite is shown.</p>}
      <div className="object-detail-metadata"><label>Scene state<select aria-label="Scene state" value={clipId} disabled={!clips.length} onChange={event => { setClipId(event.target.value); setExpandedClip(event.target.value); }}>{clips.length ? clips.map(clip => <option key={clip.id} value={clip.id}>{clip.name || clip.id}</option>) : <option value="">No exported states</option>}</select></label><label>Repeated facing<select aria-label="Repeated facing" value={direction} onChange={event => setDirection(event.target.value)}>{directions.map(value => <option key={value} value={value}>{DIRECTION_NAMES[value]}</option>)}</select></label></div>
      <section className="object-review-section"><h3><span>01</span> {singleFacing ? object.kind === 'backdrop' ? 'Backdrop surface' : 'Player-facing surface' : 'Four directions'}</h3><p>{singleFacing ? object.kind === 'backdrop' ? 'A fixed three-row backdrop surface. Roof, wall and baseboard keep their authored 35° camera and uniform lighting.' : 'One readable surface always faces the player. Its front-edge placement leaves room for a chef or decoration behind it.' : cameraFacing ? 'Four facing contexts: camera-facing artwork stays readable from North, East, South and West. The tile pitch and ground root stay fixed.' : 'Same tile pitch and ground root in every facing.'}</p><SpriteScene placements={facings} gridSize={grid} seconds={seconds} overlays={overlays} zoom={zoom} label={singleFacing ? `${object.name}: single player-facing surface on the shared tile` : cameraFacing ? `${object.name}: camera-facing artwork in North, East, South and West world-facing contexts` : `${object.name}: North, East, South and West on the tile grid`} labels/></section>
      <section className="object-review-section"><h3><span>02</span> Repeated 3 × 3</h3><p>Nine copies at their declared footprint spacing. Inspect joins and visual overlap.</p><SpriteScene placements={repeatedPlacements(object, direction, currentClip?.id)} gridSize={[footprint[0] * 3, footprint[1] * 3]} seconds={seconds} overlays={overlays} zoom={zoom} label={`${object.name}: 3 by 3 repeated tile arrangement`}/></section>
      <section className="object-review-section"><h3><span>03</span> Interaction &amp; scale</h3><p>One shared cell size; recorded placements preserve support heights.</p>{interactions.length ? interactions.map((interaction, index) => <figure className="object-interaction" key={index}><figcaption>{interaction.name}</figcaption><SpriteScene placements={interaction.placements || []} gridSize={interaction.gridSize || [4, 3]} seconds={seconds} overlays={overlays} zoom={zoom} label={`${object.name}: ${interaction.name}`}/>{interaction.note && <p>{interaction.note}</p>}</figure>) : <p className="object-queued-note">Interaction composition will appear when the related exports and attachment positions are ready.</p>}</section>
      <section className="object-review-section"><h3><span>04</span> {singleFacing ? 'Every animation · player-facing' : 'Every animation · all directions'}</h3><p>{singleFacing ? 'Open a state to inspect the single player-facing surface.' : 'Open a state to compare all four facings.'} Playback and frame scrubbing above apply to the open state. A missing facing stays labeled Pending.</p>{clips.map(clip => <details className="object-animation" key={clip.id} data-animation={clip.id} open={expandedClip === clip.id}><summary className="object-animation-title" onClick={event => { event.preventDefault(); const next = expandedClip === clip.id ? null : clip.id; setExpandedClip(next); if (next) setClipId(next); }}><span className="object-animation-name">{clip.name || clip.id}</span><span>{clip.frames || 1} frames · {clip.loop === false ? 'one shot' : (clip.frames || 1) > 1 ? 'loop' : 'static'}</span><span className="object-animation-caret" aria-hidden="true">⌄</span></summary>{expandedClip === clip.id && <SpriteScene placements={directionPlacements(object, clip.id)} gridSize={grid} seconds={seconds} overlays={overlays} zoom={zoom} label={`${object.name}: ${clip.name || clip.id}, ${singleFacing ? 'player-facing surface' : 'all four directions'}`}  labels/>}</details>)}{!clips.length && <p className="object-queued-note">No animation clips registered yet.</p>}</section>
      {object.requirements && <section className="object-review-section"><h3><span>↳</span> Required coverage</h3><p>{(object.requirements.states || []).join(' · ') || 'See approved inventory for required states.'}</p><p>{singleFacing ? 'One player-facing surface' : 'All four facing contexts'} · 12 fps · at least six unique frames per animated state.</p></section>}
      <footer className="object-review-caption">Registered floor sprites appear when available; square lines are calibration guides. Roots show the shared ground anchor; colored points show registered sockets/ports, not sprite bounds. Use Comments above to review {object.name}.</footer>
    </div>
  </div>;
}

export function ObjectReview({ objectId }) {
  const object = libraryObjects.find(candidate => candidate.id === objectId);
  return object ? <ObjectDetail object={object} key={object.id}/> : <ObjectLibrary/>;
}
