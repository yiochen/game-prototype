import React, { useId, useState } from 'react';
import variedStudy from '../assets/decoration-study/study.json';
import originalStudy from '../assets/decoration-study/original/study.json';
import concept from '../design/art-directions/underwater-concept.png?url';
import previous from '../review/33/seven-column-scenes/underwater-phone.png?url';
import './decoration-study.css';
const images = import.meta.glob(['../assets/decoration-study/sprites/**/*.png', '../assets/decoration-study/original/sprites/**/*.png'], { eager: true, query: '?url', import: 'default' });
const studies = { varied: variedStudy, original: originalStudy };
const folders = { varied: '', original: 'original/' };
const directions = ['S', 'E', 'N', 'W'];
const profileFor = (item, mode) => mode === 'mixed' && item.profiles?.ordinary35 && item.baselineSilhouetteHeight > 2 ? 'ordinary35' : 'oblique70';
const heightFactor = (item, mode) => profileFor(item, mode) === 'ordinary35' ? Math.cos(35 * Math.PI / 180) : .7;
const image = (version, id, direction = 'S', mode = 'oblique') => {
  const item = studies[version].objects.find(item => item.id === id);
  const path = item.profiles?.[profileFor(item, mode)]?.images[direction] ?? item.images[direction];
  return images[`../assets/decoration-study/${folders[version]}${path}`];
};
const sourceBase = 'https://github.com/yiochen/game-prototype/blob/';
const left = ['spire', 'kelp', 'low-rock', 'column', 'low-rock', 'coral', 'spire', 'kelp', 'low-rock'];
const right = ['coral', 'low-rock', 'kelp', 'spire', 'coral', 'low-rock', 'column', 'low-rock', 'kelp'];
function shoreline(variant) {
  const out = [];
  for (let y = 0; y < 9; y++) {
    const index = (y + variant * 3) % 9;
    out.push({ id: left[index], x: 0, y, direction: directions[(y + variant) % 4] });
    out.push({ id: right[(index + 2) % 9], x: 6, y, direction: directions[(y + 2 + variant) % 4] });
    if (![2, 6].includes(y)) out.push({ id: ['low-rock', 'coral', 'kelp'][index % 3], x: 1, y, direction: directions[(y + 1) % 4] });
    if (![1, 4, 7].includes(y)) out.push({ id: ['kelp', 'low-rock', 'coral'][index % 3], x: 5, y, direction: directions[(y + 3) % 4] });
  }
  out.push({ id: 'low-rock', x: 2, y: 8, direction: 'E' }, { id: 'coral', x: 4, y: 8, direction: 'W' });
  return out;
}
function TileScene({ version, projection, columns, rows, placements, grid, decor = true, label, className = '' }) {
  const key = useId();
  const study = studies[version];
  const cell = study.cellSize;
  const [fw, fh] = study.frameSize;
  const [rx, ry] = study.root;
  const place = (src, x, y, id) => <image key={id} href={src} x={(x + .5) * cell - rx} y={(y + .5) * cell - ry} width={fw} height={fh} data-decor-placement={id}/>;
  const top = Math.max(32, ...placements.map(item => Math.ceil(study.objects.find(obj => obj.id === item.id).height * heightFactor(study.objects.find(obj => obj.id === item.id), projection) * cell - item.y * cell + 24)));
  return <svg className={`decor-tile-scene ${className}`} viewBox={`-16 ${-top} ${columns * cell + 32} ${rows * cell + top + 16}`} role="img" aria-label={label} data-decor-columns={columns} data-decor-rows={rows} data-height-ratio={study.heightRatio} data-height-version={version} data-projection-mode={projection}>
    <defs><pattern id={key} width={cell} height={cell} patternUnits="userSpaceOnUse"><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke="#b8e3d8" strokeOpacity=".7" strokeWidth="1.4"/></pattern></defs>
    <rect x="0" y="0" width={columns * cell} height={rows * cell} fill="#20a2bb"/>
    <g data-decor-layer="ground">{Array.from({ length: columns * rows }, (_, i) => place(image(version, 'bed-0'), i % columns, Math.floor(i / columns), `floor-${i}`))}</g>
    {decor && <g data-decor-layer="objects">{[...placements].sort((a, b) => a.y - b.y || a.x - b.x).map((item, i) => place(image(version, item.id, item.direction, projection), item.x, item.y, `${item.id}-${i}`))}</g>}
    {grid && <g data-decor-layer="guides"><rect width={columns * cell} height={rows * cell} fill={`url(#${key})`}/>{placements.map((item, i) => <circle key={i} cx={(item.x + .5) * cell} cy={(item.y + .5) * cell} r="3" fill="#fff3c9" stroke="#305b65" strokeWidth="1"/>)}</g>}
  </svg>;
}
export function DecorationStudy() {
  const [version, setVersion] = useState('varied');
  const [projection, setProjection] = useState('mixed');
  const source = `${sourceBase}${version === 'original' ? '0edc5ae993c09ec1434ea8879a9d5543bd9a76c3' : 'codex/sushi-loop-33-art-catalog'}/prototypes/sushi-loop/assets/decoration-study/`;
  const study = studies[version];
  const pieces = study.objects.filter(item => item.heightBand !== 'ground');
  const [grid, setGrid] = useState(false);
  const [decor, setDecor] = useState(true);
  const [variant, setVariant] = useState(0);
  const [direction, setDirection] = useState('S');
  const [patch, setPatch] = useState('mixed');
  const [turns, setTurns] = useState(true);
  const patchIds = ['spire', 'kelp', 'column', 'coral', 'low-rock', 'kelp', 'low-rock', 'coral', 'low-rock'];
  const patchPlacements = patchIds.map((id, i) => ({ id: patch === 'mixed' ? id : patch, x: i % 3, y: Math.floor(i / 3), direction: turns ? directions[i % 4] : 'S' }));
  return <div className="phone-scene decoration-study">
    <header className="decor-header"><span className="decor-kicker">DECORATION STUDY · NATIVE BLENDER</span><h2>Living ledges. Deeper shadows.</h2><p>Five revised underwater pieces over a separate ocean bed. Each fills a physical tile footprint over the square ground grid. Uneven crowns, growth on lower, middle and upper ledges, and dark bases graduating into bright upper faces. Plant proportions stay compact. Compare a consistent 70% oblique camera with a 35° orthographic camera for taller objects.</p><nav><a href="#scene-underwater">Current underwater scene ↗</a><a href="#character-scale-study">Character study ↗</a></nav></header>
    <div className="decor-controls"><label>Height study<select aria-label="Decoration height study" value={version} onChange={e => setVersion(e.target.value)}><option value="varied">Decorated rock variations</option><option value="original">Original · 0.25–0.91 tiles</option></select></label><label>Projection<select aria-label="Decoration projection" value={projection} onChange={e => setProjection(e.target.value)} disabled={version === 'original'}><option value="mixed">Mixed · tall objects at 35°</option><option value="oblique">All objects · 70% oblique</option></select></label><label><input type="checkbox" checked={decor} onChange={e => setDecor(e.target.checked)}/> Decoration layer</label><label><input type="checkbox" checked={grid} onChange={e => setGrid(e.target.checked)}/> Tile grid & roots</label><button type="button" onClick={() => setVariant(v => 1 - v)}>Arrangement {variant ? 'B' : 'A'} · switch</button></div>
    <section className="decor-section"><div className="decor-section-heading"><span>01 · CONNECTED EDGES</span><h3>A shoreline built from individual tiles</h3><p>The same five pieces form two different edges and lower corners. Tall shapes sit mainly outside, lower pieces soften the inner edge, and the central passage stays open. Switch the decoration layer off to inspect the continuous floor.</p></div><div className="decor-scene-wrap"><TileScene version={version} projection={projection} columns={7} rows={9} placements={shoreline(variant)} grid={grid} decor={decor} label={`Underwater decoration shoreline arrangement ${variant ? 'B' : 'A'}`}/></div><p className="decor-caption">Square ground and fixed roots in both modes. Mixed switches objects taller than two tiles in the reference silhouette to 35°; visible object depth then foreshortens. This camera rule is experimental.</p></section>
    <section className="decor-section"><div className="decor-section-heading"><span>02 · COVERAGE & REPETITION</span><h3>Nine neighbors, no padded cells</h3><p>Compare mixed heights with a repeated single object. Quarter-turns use separately rendered directions, so the lighting and projection stay consistent.</p></div><div className="decor-controls"><label>Tile selection<select aria-label="Decoration patch selection" value={patch} onChange={e => setPatch(e.target.value)}><option value="mixed">Mixed heights</option>{pieces.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label><input type="checkbox" checked={turns} onChange={e => setTurns(e.target.checked)}/> Vary facing</label></div><div className="decor-patch"><TileScene version={version} projection={projection} columns={3} rows={3} placements={patchPlacements} grid={grid} decor={decor} label="Three by three decoration coverage test"/></div></section>
    <section className="decor-section"><div className="decor-section-heading"><span>03 · THE FIVE PIECES</span><h3>One-cell footprint, a varied skyline</h3><p>The original rock, coral, kelp and ruin families are rebuilt as broad tile compositions. Natural notches expose the shared bed; the main mass fills the cell. Uneven rock crowns support compact plants at multiple levels; shading darkens the lower rock faces.</p></div><div className="decor-controls"><label>Inspect facing<select aria-label="Decoration object facing" value={direction} onChange={e => setDirection(e.target.value)}>{directions.map(d => <option key={d} value={d}>{d}</option>)}</select></label></div><div className="decor-piece-grid">{pieces.map(item => <article key={item.id} className="decor-piece" data-decor-piece={item.id}><TileScene version={version} projection={projection} columns={1} rows={1} placements={[{ id: item.id, x: 0, y: 0, direction }]} grid decor label={`${item.name} facing ${direction}`}/><div><span className="decor-height-band">{item.heightBand}</span><h4>{item.name}</h4><p>1 × 1 tile footprint<br/><strong>{(item.height * heightFactor(item, projection)).toFixed(2)} tiles of vertical rise</strong><br/>{profileFor(item, projection) === 'ordinary35' ? '35° ordinary orthographic' : '70% square-grid oblique'}{version === 'varied' && <><br/>Bottom · middle · top growth<br/>Dark-base material gradient</>}</p><a href={image(version, item.id, direction, projection)} target="_blank" rel="noreferrer">Native capture ↗</a></div></article>)}</div></section>
    <details className="decor-reference"><summary>Compare the original concept and previous live border</summary><div className="decor-reference-grid"><figure><img src={concept} alt="Original underwater concept with dense, varied rock, coral and kelp edges" loading="lazy"/><figcaption>Original concept · color and composition reference</figcaption></figure><figure><img src={previous} alt="Previous live underwater scene with straight walls and repeating large reef patches" loading="lazy"/><figcaption>Previous live composition · repeating four-tile garden patches</figcaption></figure></div></details>
    <footer className="decor-footer"><p>Native shape, shading and camera study for issue #33. The lower-rock gradient is stylized surface shading; ground-contact shadows remain a future runtime layer. Static captures only; animation, final surface refinement, gameplay collision and runtime shadows are outside this experiment. Existing full scenes and production sprites remain available for comparison.</p><a href={`${source}decoration-study.blend`} target="_blank" rel="noreferrer">Editable Blender project ↗</a><a href={`${source}source/create_and_capture.py`} target="_blank" rel="noreferrer">Modeling & capture source ↗</a></footer>
  </div>;
}
