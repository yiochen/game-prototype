// Publish v2 native captures at the production atlas scale.
//
//   node prototypes/sushi-loop/assets/expedition/v2/publish.mjs
//
// Like the production delivery, each 4x native frame is downsampled 2x as a
// whole canvas with Lanczos (no cropping or fitting). Entries use the
// production library schema so the route composer reads both libraries alike.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';

const here = new URL('.', import.meta.url);
const path = (p) => new URL(p, here).pathname;
const objects = [];

function publish(id, native, frame, root, footprint, directions, extra) {
  const clipDirections = {};
  for (const d of directions) {
    const src = path(`native/${native}/${id}/static-${d}.png`);
    if (!existsSync(src)) throw new Error(`Missing capture ${src}`);
    mkdirSync(path(`sprites/${id}`), { recursive: true });
    const out = `sprites/${id}/static-${d}.png`;
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', src, '-vf', `scale=${frame[0] * 2}:${frame[1] * 2}:flags=lanczos,format=rgba`, '-frames:v', '1', path(out)]);
    clipDirections[d] = { image: out, columns: 1, rows: 1, atlasSize: [frame[0] * 2, frame[1] * 2], rects: [[0, 0, frame[0] * 2, frame[1] * 2]] };
  }
  objects.push({ id, footprint, frameSize: frame, root, sourceScale: 2, ...extra,
    clips: [{ id: 'static', frames: 1, fps: 12, static: true, loop: false, frameOrder: [0], directions: clipDirections }] });
}

const rocks = JSON.parse(readFileSync(path('native/rocks/variants.json'), 'utf8'));
for (const [id, v] of Object.entries(rocks.variants)) {
  publish(id, 'rocks', rocks.frame, rocks.root, [1, 1], ['N', 'E', 'S', 'W'],
    { kind: 'terrain', family: 'rock', height: v.height, palette: v.palette, source: 'v2/rocks.py (boulder-underwater round-04 recipe)' });
}
const ruins = JSON.parse(readFileSync(path('native/ruins/pieces.json'), 'utf8'));
for (const [id, p] of Object.entries(ruins.pieces)) {
  publish(id, 'ruins', p.frame, p.root, p.footprint, p.directions,
    { kind: /^(arch|bridge)-/.test(id) ? 'landmark' : 'terrain', family: /^(arch|bridge)-/.test(id) ? 'landmark' : 'ruin', span: /^(arch|bridge)-/.test(id) ? p.footprint[0] - 2 : undefined, solidCells: p.solidCells, source: 'v2/ruins.py (decor-ruin-fragment round-03 style)' });
}
const sealife = JSON.parse(readFileSync(path('native/sealife/pieces.json'), 'utf8'));
for (const [id, p] of Object.entries(sealife.pieces)) {
  publish(id, 'sealife', p.frame, p.root, p.footprint, p.directions,
    { kind: p.family === 'sealife-edge' ? 'terrain' : 'decor', family: p.family, solidCells: p.solidCells, source: 'v2/sealife.py (ruin round-03 kit)' });
}
writeFileSync(path('library.json'), JSON.stringify({ version: 1, cellSize: 128, objects }, null, 1) + '\n');
console.log(`published ${objects.length} objects`);
