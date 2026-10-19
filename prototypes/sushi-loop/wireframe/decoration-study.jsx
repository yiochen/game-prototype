import React, { useId, useState } from 'react';
import study from '../assets/concept-decoration/study.json';
import measurements from '../assets/concept-decoration/measurements.json';
import underwaterConcept from '../design/art-directions/underwater-concept.png?url';
import restaurantConcept from '../design/art-directions/restaurant-concept.png?url';
import './decoration-study.css';
const images = import.meta.glob('../assets/concept-decoration/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
const directions = ['S', 'E', 'N', 'W'];
const themes = {
  underwater: { title: 'Underwater', concept: underwaterConcept, floor: 'ocean-floor', background: '#19b3c8', scene: 'scene-underwater', note: 'Blue rocks frame the channel. Pink coral and branching kelp form substantial silhouettes between pale ruins. These families follow the specific forms shown in the reference.' },
  restaurant: { title: 'Restaurant', concept: restaurantConcept, floor: 'restaurant-floor', background: '#eed29d', scene: 'scene-restaurant', note: 'Slate rocks and dense green foliage frame the cream floor. Wooden planters, crates, construction corners and golden lanterns follow the warm materials and groupings in the reference.' },
};
const source = 'https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/concept-decoration/';
const profileFor = (item, mode) => mode === 'mixed' && item.heightBand !== 'ground' && measurements.objects[item.id].profiles.oblique70.maxProjectedHeight > 2 ? 'ordinary35' : 'oblique70';
function image(id, direction = 'S', mode = 'mixed') {
  const item = study.objects.find(item => item.id === id);
  return images[`../assets/concept-decoration/${item.profiles[profileFor(item, mode)].images[direction]}`];
}
// Deliberate perimeter compositions, with the concept's open center and protruding corners.
const layouts = {
  underwater: [
    ['cobalt-crags',0,0],['kelp-fan',0,1],['pink-coral',0,2],['cobalt-shelf',0,3],['pale-column',1,3],['kelp-fan',0,4],['cobalt-crags',0,5],['pink-coral',0,6],['pale-column',1,7],['kelp-fan',0,8],
    ['kelp-fan',6,0],['reef-face',6,1],['cobalt-crags',6,2],['pink-coral',6,3],['pale-column',5,4],['kelp-fan',6,5],['cobalt-shelf',6,6],['cobalt-crags',6,7],['pink-coral',6,8],['kelp-fan',5,8],
    ['pink-coral',1,1],['cobalt-shelf',5,2],['cobalt-crags',0,8],
  ],
  restaurant: [
    ['slate-bank',0,0],['lantern-garden',1,0],['lantern-garden',5,0],['slate-bank',6,0],['angular-shrub',0,1],['crate-stack',6,1],['slate-bank',0,2],['angular-shrub',6,2],['crate-stack',0,3],['slate-bank',6,3],['slate-bank',0,4],['wood-planter',6,4],['angular-shrub',0,5],['slate-bank',6,5],['cone-curb',0,6],['angular-shrub',6,6],['slate-bank',0,7],['angular-shrub',1,7],['wood-planter',5,7],['cone-curb',6,7],
  ],
};
function TileScene({ theme, mode, columns, rows, placements, grid, decor = true, label }) {
  const key = useId(); const cell = study.cellSize;
  const [fw, fh] = study.frameSize; const [rx, ry] = study.root;
  const place = (src,x,y,id) => <image key={id} href={src} x={(x+.5)*cell-rx} y={(y+.5)*cell-ry} width={fw} height={fh}/>;
  const top = Math.max(24, ...placements.map(p => Math.ceil(study.objects.find(o => o.id === p.id).height * (profileFor(study.objects.find(o => o.id === p.id), mode) === 'ordinary35' ? Math.cos(35*Math.PI/180) : .7)*cell-p.y*cell+24)));
  return <svg className="decor-tile-scene" viewBox={`-12 ${-top} ${columns*cell+24} ${rows*cell+top+12}`} role="img" aria-label={label} data-projection-mode={mode}>
    <defs><pattern id={key} width={cell} height={cell} patternUnits="userSpaceOnUse"><path d={`M ${cell} 0 H 0 V ${cell}`} fill="none" stroke={theme === 'underwater' ? '#b9eeee' : '#aa8a51'} strokeOpacity=".5" strokeWidth="1.2"/></pattern></defs>
    <rect width={columns*cell} height={rows*cell} fill={themes[theme].background}/>
    <g data-decor-layer="ground">{Array.from({length:columns*rows},(_,i)=>place(image(themes[theme].floor),i%columns,Math.floor(i/columns),`floor-${i}`))}</g>
    {decor && <g data-decor-layer="objects">{[...placements].sort((a,b)=>a.y-b.y||a.x-b.x).map((p,i)=>place(image(p.id,p.direction,mode),p.x,p.y,`${p.id}-${i}`))}</g>}
    {grid && <g data-decor-layer="guides"><rect width={columns*cell} height={rows*cell} fill={`url(#${key})`}/>{placements.map((p,i)=><circle key={i} cx={(p.x+.5)*cell} cy={(p.y+.5)*cell} r="3" fill="#fff0be" stroke="#366966"/>)}</g>}
  </svg>;
}
function ConceptCrop({ item }) {
  return <figure className="decor-crop"><svg viewBox={[item.referenceCrop[0], item.referenceCrop[1], item.referenceCrop[2]-item.referenceCrop[0], item.referenceCrop[3]-item.referenceCrop[1]].join(' ')} role="img" aria-label={`${item.name} concept reference`}><image href={themes[item.theme].concept} width="1024" height="1536"/></svg><figcaption>Crop from the approved concept</figcaption></figure>;
}
export function DecorationStudy() {
  const [theme,setTheme] = useState('underwater'); const [mode,setMode] = useState('mixed');
  const [grid,setGrid] = useState(false); const [decor,setDecor] = useState(true); const [patch,setPatch] = useState('mixed'); const [turns,setTurns] = useState(true);
  const selected = themes[theme]; const pieces = study.objects.filter(o=>o.theme===theme&&o.heightBand!=='ground');
  const patchOrder = theme==='underwater' ? ['cobalt-crags','reef-face','pale-column','kelp-fan','cobalt-shelf','pink-coral','pink-coral','kelp-fan','cobalt-shelf'] : ['slate-bank','lantern-garden','crate-stack','angular-shrub','wood-planter','slate-bank','wood-planter','cone-curb','angular-shrub'];
  const placements = patchOrder.map((id,i)=>({id:patch==='mixed'?id:patch,x:i%3,y:Math.floor(i/3),direction:turns?directions[i%4]:'S'}));
  return <div className="phone-scene decoration-study" data-decoration-theme={theme}>
    <header className="decor-header"><span className="decor-kicker">ISSUE 33 · CONCEPT-REFERENCED DECORATION</span><h2>Built from the concepts.</h2><p>Twelve native decoration pieces based on recognizable forms in the two approved scenes. Each card pairs its concept crop with four captured facings. Compare their silhouettes and density on a shared tile grid.</p><p className="decor-rules">Height-based projection · maximum three tiles of projected height · full tile width and depth · darker lower surfaces</p></header>
    <div className="decor-controls"><label>Scene<select aria-label="Decoration scene" value={theme} onChange={e=>{setTheme(e.target.value);setPatch('mixed');}}>{Object.entries(themes).map(([id,t])=><option key={id} value={id}>{t.title}</option>)}</select></label><label>Projection<select aria-label="Decoration projection" value={mode} onChange={e=>setMode(e.target.value)}><option value="mixed">By height · 70% / 35° upper view</option><option value="oblique">All pieces · 70% oblique</option></select></label><label><input type="checkbox" checked={grid} onChange={e=>setGrid(e.target.checked)}/> Tile grid & roots</label><label><input type="checkbox" checked={decor} onChange={e=>setDecor(e.target.checked)}/> Decoration layer</label></div>
    <section className="decor-section"><div className="decor-section-heading"><span>01 · CONCEPT & COMPOSITION</span><h3>{selected.title} perimeter</h3><p>{selected.note}</p></div><div className="decor-comparison"><figure><img src={selected.concept} alt={`Approved ${theme} concept art`}/><figcaption>Original concept · preserved unchanged</figcaption></figure><figure><TileScene theme={theme} mode={mode} columns={7} rows={theme==='underwater'?9:8} placements={layouts[theme].map(([id,x,y])=>({id,x,y,direction:'S'}))} grid={grid} decor={decor} label={`${selected.title} concept decoration perimeter`}/><figcaption>Native decorations · seven-column layout · shared ground beneath</figcaption></figure></div><p className="decor-caption">The center is left open to inspect the perimeter. <a href={`#${selected.scene}`}>Full {theme} scene ↗</a></p></section>
    <section className="decor-section"><div className="decor-section-heading"><span>02 · DENSITY & NEIGHBORS</span><h3>Full tiles, coherent families</h3><p>Inspect the mixed set or repeat one piece. Four native facings share the same roots, scale and lower-surface shading.</p></div><div className="decor-controls"><label>Tile selection<select aria-label="Decoration patch selection" value={patch} onChange={e=>setPatch(e.target.value)}><option value="mixed">Mixed concept families</option>{pieces.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label><input type="checkbox" checked={turns} onChange={e=>setTurns(e.target.checked)}/> Vary facing</label></div><div className="decor-patch"><TileScene theme={theme} mode={mode} columns={3} rows={3} placements={placements} grid={grid} decor={decor} label={`${selected.title} three by three decoration patch`}/></div></section>
    <section className="decor-section"><div className="decor-section-heading"><span>03 · REFERENCE & FOUR FACINGS</span><h3>{pieces.length} {theme} pieces</h3><p>Full tile width and depth means the assembled object occupies its ground cell; taller art rises over the row behind. The height measurement below includes the complete projected silhouette, with the largest of the four facings shown. The lower-camera profile retains square footing near ground.</p></div><div className="decor-asset-list">{pieces.map(item=>{
      const profile=profileFor(item,mode); const metric=measurements.objects[item.id].profiles[profile];
      return <article key={item.id} data-decor-piece={item.id} className="decor-asset"><div className="decor-asset-intro"><ConceptCrop item={item}/><div><span className="decor-height-band">{item.kind}</span><h4>{item.name}</h4><p>{item.description}</p><p><strong>{metric.maxProjectedHeight.toFixed(2)} tiles projected height</strong><br/>1 × 1 ground cell · {(measurements.objects[item.id].planCoverage*100).toFixed(0)}% top-down coverage<br/>{profile==='ordinary35'?'35° upper view · square footing':'70% square-grid oblique'}<br/>Darker lower surfaces · no directional capture lights</p></div></div><div className="decor-directions">{directions.map(direction=><figure key={direction}><TileScene theme={theme} mode={mode} columns={1} rows={1} placements={[{id:item.id,x:0,y:0,direction}]} grid decor label={`${item.name} facing ${direction}`}/><figcaption><a href={image(item.id,direction,mode)} target="_blank" rel="noreferrer">{direction} · native capture ↗</a></figcaption></figure>)}</div></article>;
    })}</div></section>
    <footer className="decor-footer"><p>Editable native Blender assets for visual review. The concepts guide silhouettes, palette and groupings; no random arrangement generator is used. Material height gradients keep lower parts dark in every facing. Contact shadows remain a separate runtime layer. These are static captures; final surface polish and any plant motion follow shape approval. Issue 33 stays open.</p><a href={`${source}concept-decoration.blend`} target="_blank" rel="noreferrer">Editable Blender project ↗</a><a href={`${source}source/create_and_capture.py`} target="_blank" rel="noreferrer">Modeling & capture source ↗</a></footer>
  </div>;
}
