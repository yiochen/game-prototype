import React, { useId, useState } from 'react';
import { lightingSubjects, lightingImage, lightingCapture, lightingSource, lightingReviewVariants } from './character-lighting-study-data.js';
import { usePlayback } from './object-review.jsx';
import conceptUrl from '../design/art-directions/restaurant-concept.png?url';
import './character-lighting-study.css';

const facingNames = { S: 'Front · South', E: 'Right side · East', N: 'Back · North', W: 'Left side · West' };
const framePath = (capture, frame) => capture?.frames?.length ? capture.frames[frame % capture.frames.length] : capture?.image;

function Capture({ subject, variant, direction, guides, frameIndex }) {
  const id = useId();
  const entry = lightingCapture(variant, direction);
  const path = framePath(entry, frameIndex);
  const url = lightingImage(path, subject);
  const cell = subject.cellSize || 128;
  const frame = subject.frame || subject.frameSize;
  const root = subject.root;
  const crop = variant.detailCrop || subject.detailCrop;
  const validCrop = Array.isArray(crop) && crop.length === 4 && crop.every(Number.isFinite);
  const footprint = subject.footprint || [1, 1];
  const floor = subject.floorBounds || [-footprint[0] / 2, -footprint[1] / 2, ...footprint];
  const floorRect = floor.map(value => value * cell);
  return <article className="lighting-variant" data-lighting-variant={variant.id}>
    <header><h3>{variant.name}</h3>{variant.id === subject.selectedLighting && <span className="lighting-selection">Chosen lighting</span>}{variant.id === 'faceted-tuned' && <span className="lighting-selection is-trial">Material trial</span>}<p>{variant.description}</p></header>
    {url ? <figure>
      <svg className="lighting-capture" viewBox={[-root[0], -root[1], ...frame].join(' ')} style={{ aspectRatio: `${frame[0]} / ${frame[1]}` }} role="img" aria-label={`${subject.name}, ${variant.name}: ${facingNames[direction]}`} data-lighting-direction={direction} data-frame-root={root.join(' ')} data-cell-size={cell} data-frame-index={entry?.frames?.length ? frameIndex % entry.frames.length : 0}>
        <defs><pattern id={id} width={cell} height={cell} patternUnits="userSpaceOnUse" x={floorRect[0]} y={floorRect[1]}><rect width={cell} height={cell} fill="#f4e9cb"/><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke="#cabb9a" strokeWidth="1.5"/></pattern></defs>
        <rect x={floorRect[0]} y={floorRect[1]} width={floorRect[2]} height={floorRect[3]} fill={`url(#${id})`} data-lighting-floor="true"/>
        <image href={url} x={-root[0]} y={-root[1]} width={frame[0]} height={frame[1]} preserveAspectRatio="none" data-lighting-source={path}/>
        {guides && <g className="lighting-ground-guides"><rect x={floorRect[0]} y={floorRect[1]} width={floorRect[2]} height={floorRect[3]}/><path d="M -7 0 H 7 M 0 -7 V 7"/><circle r="2"/></g>}
      </svg>
      <figcaption><span>{facingNames[direction]}</span><a href={url} target="_blank" rel="noopener noreferrer">Native PNG ↗</a></figcaption>
      {validCrop && <div className="lighting-hat-comparison"><p>{subject.detailLabel || 'Surface detail'}</p><svg className="lighting-hat-detail" style={{ aspectRatio: `${crop[2]} / ${crop[3]}` }} viewBox={crop.join(' ')} role="img" aria-label={`${subject.name}, ${variant.name}: enlarged surface detail`}><image href={url} width={frame[0]} height={frame[1]} preserveAspectRatio="none"/></svg></div>}
    </figure> : <p className="lighting-pending" role="status">Native capture pending.</p>}
  </article>;
}

function Comparison({ subject, direction, guides }) {
  const variants = lightingReviewVariants(subject);
  const frames = Math.max(1, ...variants.map(variant => lightingCapture(variant, direction)?.frames?.length || 1));
  const { frame, playing, toggle, scrub } = usePlayback(frames, { autoPlay: false });
  const otherAnimatedFacing = frames === 1 && ['N', 'E', 'S', 'W'].find(facing => variants.some(variant => lightingCapture(variant, facing)?.frames?.length > 1));
  return <>
    {frames > 1 && <div className="lighting-playback" aria-label="Native lighting animation controls"><button type="button" onClick={toggle} aria-label={playing ? 'Pause lighting study animation' : 'Play lighting study animation'}>{playing ? 'Ⅱ Pause' : '▶ Play'}</button><label>Frame {frame + 1} / {frames}<input type="range" aria-label="Lighting study animation frame" min="0" max={frames - 1} value={frame} onChange={event => scrub(event.target.value)}/></label><span>12 fps · synchronized native frames</span></div>}
    {otherAnimatedFacing && <p className="lighting-animation-note">This facing is a native still. Choose {facingNames[otherAnimatedFacing]} to inspect the moving conveyor.</p>}
    <section className="lighting-comparison" style={{ '--lighting-columns': Math.min(4, Math.max(1, variants.length)), '--lighting-mobile-columns': Math.min(2, Math.max(1, variants.length)) }} aria-label="Native Blender surface comparison">{variants.map(variant => <Capture key={variant.id} subject={subject} variant={variant} direction={direction} guides={guides} frameIndex={frame}/>)}</section>
  </>;
}

export function CharacterLightingStudy() {
  const [subjectId, setSubjectId] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('lightingSubject');
    return lightingSubjects.some(subject => subject.id === requested) ? requested : 'chef-noor';
  });
  const [direction, setDirection] = useState('S');
  const [guides, setGuides] = useState(true);
  const subject = lightingSubjects.find(item => item.id === subjectId) || lightingSubjects[0];
  const variants = lightingReviewVariants(subject);
  const materialTrial = subject.reviewVariantIds?.includes('faceted-tuned');
  const blend = lightingSource(subject.source?.blend, subject);
  const recipe = lightingSource(subject.source?.recipe, subject);
  const historicalBlend = lightingSource('source/environment-lighting.blend', { studyRoot: 'environment-lighting-study' });
  const count = variants.reduce((sum, variant) => sum + ['N', 'E', 'S', 'W'].filter(facing => lightingImage(lightingCapture(variant, facing)?.image, subject)).length, 0);
  const footprint = subject.footprint || [1, 1];
  const character = subject.projection === 'character-orthographic';
  const catalogId = character ? 'chef-noor' : subject.placements?.length === 1 ? subject.placements[0].id : null;
  const observation = typeof subject.recommendation === 'string' ? subject.recommendation : subject.recommendation?.note;
  const changeSubject = id => {
    if (!lightingSubjects.some(subject => subject.id === id)) return;
    setSubjectId(id);
    const url = new URL(window.location.href);
    url.searchParams.set('lightingSubject', id);
    window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`);
  };
  return <div className="phone-scene character-lighting-study" data-lighting-subject={subject.id}>
    <header className="lighting-study-header"><span className="lighting-eyebrow">NATIVE BLENDER SURFACE REVIEW</span><h2>Light on surfaces.</h2><p>{materialTrial ? 'Faceted lighting is chosen. Compare the original materials with duller conveyor rails and less reflective wood under the same 140 W overhead light and four equal fills. Shape, camera, framing and the native 135% grade stay fixed.' : 'Faceted lighting is chosen. The original four-way lighting comparison remains available here: emission baseline, Soft, Faceted and Crisp. Shape, camera, framing and the native 135% grade stay fixed.'}</p><nav aria-label="Lighting study sources"><a href={catalogId ? `#object-${catalogId}` : '#object-library'}>{catalogId ? `${subject.name} in the production library ↗` : 'Production object library ↗'}</a>{blend && <a href={blend} target="_blank" rel="noopener noreferrer">Editable Blender study ↗</a>}{recipe && <a href={recipe} target="_blank" rel="noopener noreferrer">Lighting recipe ↗</a>}{materialTrial && <a href={historicalBlend} target="_blank" rel="noopener noreferrer">Historical lighting study ↗</a>}</nav><p className="lighting-study-status" role="status">{count} / {variants.length * 4} native stills · {materialTrial ? 'material changes pending review' : 'Faceted lighting chosen'} · production unchanged</p></header>
    <div className="lighting-study-controls"><label>Subject<select aria-label="Lighting study subject" value={subject.id} onChange={event => changeSubject(event.target.value)}>{lightingSubjects.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Facing<select aria-label="Lighting study facing" value={direction} onChange={event => setDirection(event.target.value)}>{['S', 'E', 'N', 'W'].map(value => <option key={value} value={value}>{facingNames[value]}</option>)}</select></label><label><input type="checkbox" checked={guides} onChange={event => setGuides(event.target.checked)}/> Tile &amp; root guides</label></div>
    <section className="lighting-subject-intro"><h3>{character ? 'Noor’s green hat' : subject.name}</h3><p>{subject.description}</p>{observation && <p className="lighting-observation">{observation}</p>}<p className="lighting-projection-note">{character ? 'C125 anatomy · 35° character camera' : '70% square-grid environment camera'} · {footprint.join(' × ')} tile footprint · 128 logical pixels per tile</p></section>
    <Comparison key={`${subject.id}-${direction}`} subject={subject} direction={direction} guides={guides}/>
    {!variants.length && <p className="lighting-pending" role="status">The isolated Blender lighting captures are being prepared.</p>}
    <p className="lighting-registration-note">Every {subject.name} capture uses the same {(subject.frame || subject.frameSize)?.join(' × ')} logical frame and ground root. Native PNGs are displayed directly, without browser image filters. {materialTrial ? 'Only the materials change between these two Faceted captures. Earlier lighting presets remain in the separate historical study linked above. Use Comments to review the material adjustment.' : 'Use Comments to review this chosen lighting treatment. Production recapture and final scene-asset approval remain pending.'}</p>
    <details className="lighting-concept-reference"><summary>Original restaurant concept reference</summary><figure><img src={conceptUrl} width="1024" height="1536" alt="Original restaurant concept art with bright top planes and shaded sides on characters and furniture."/><figcaption>The original concept is preserved unchanged.</figcaption></figure></details>
  </div>;
}
