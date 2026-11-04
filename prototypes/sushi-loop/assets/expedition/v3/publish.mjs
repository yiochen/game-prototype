// Publish v3 (issue #22) native captures at the production atlas scale, like v2/publish.mjs.
//
//   node prototypes/sushi-loop/assets/expedition/v3/publish.mjs
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const here = new URL('.', import.meta.url);
const path = (p) => new URL(p, here).pathname;
const objects = [];
const pieces = JSON.parse(readFileSync(path('native/pieces.json'), 'utf8')).pieces;
for (const [id, p] of Object.entries(pieces)) {
  const directions = {};
  for (const d of p.directions) {
    mkdirSync(path(`sprites/${id}`), { recursive: true });
    const out = `sprites/${id}/static-${d}.png`;
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', path(`native/${id}/static-${d}.png`), '-vf', `scale=${p.frame[0] * 2}:${p.frame[1] * 2}:flags=lanczos,format=rgba`, '-frames:v', '1', path(out)]);
    directions[d] = { image: out, columns: 1, rows: 1, atlasSize: [p.frame[0] * 2, p.frame[1] * 2], rects: [[0, 0, p.frame[0] * 2, p.frame[1] * 2]] };
  }
  objects.push({ id, footprint: p.footprint, frameSize: p.frame, root: p.root, sourceScale: 2, kind: 'feature', family: 'portal', solidCells: p.solidCells,
    source: 'v3/portal.py (v2 ruin kit, decor-ruin-fragment round-03 style)',
    clips: [{ id: 'static', frames: 1, fps: 12, static: true, loop: false, frameOrder: [0], directions }] });
}
writeFileSync(path('library.json'), JSON.stringify({ version: 1, cellSize: 128, objects }, null, 1) + '\n');
console.log(`published ${objects.length} objects`);
