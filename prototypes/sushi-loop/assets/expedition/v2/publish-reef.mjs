// Publish the #76 reef captures for the review page (not yet in library.json).
//
//   node prototypes/sushi-loop/assets/expedition/v2/publish-reef.mjs
//
// As publish.mjs, each 4x native frame is downsampled 2x as a whole canvas with Lanczos. Static pieces go to
// sprites/<id>/static-S.png. Each piece's crack and break frames (reef_break.py) go side by side, in
// pieces.json frame order, to sprites/reef-break/<id>.png: nine 384x1024 frames.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, existsSync } from 'node:fs';

const path = (p) => new URL(p, import.meta.url).pathname;
const ff = (...args) => execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args]);

const statics = JSON.parse(readFileSync(path('native/reef/pieces.json'), 'utf8'));
for (const id of Object.keys(statics.pieces)) {
  mkdirSync(path(`sprites/${id}`), { recursive: true });
  ff('-i', path(`native/reef/${id}/static-S.png`), '-vf', 'scale=384:1024:flags=lanczos,format=rgba', '-frames:v', '1', path(`sprites/${id}/static-S.png`));
}

const breaks = JSON.parse(readFileSync(path('native/reef-break/pieces.json'), 'utf8'));
mkdirSync(path('sprites/reef-break'), { recursive: true });
for (const id of Object.keys(breaks.pieces)) {
  const inputs = breaks.frames.flatMap((f) => {
    const src = path(`native/reef-break/${id}/${f}.png`);
    if (!existsSync(src)) throw new Error(`Missing capture ${src}`);
    return ['-i', src];
  });
  const n = breaks.frames.length;
  const graph = breaks.frames.map((_, i) => `[${i}]scale=384:1024:flags=lanczos,format=rgba[v${i}]`).join(';')
    + ';' + breaks.frames.map((_, i) => `[v${i}]`).join('') + `hstack=${n}`;
  ff(...inputs, '-filter_complex', graph, '-frames:v', '1', path(`sprites/reef-break/${id}.png`));
}
console.log(`published ${Object.keys(statics.pieces).length} static pieces and ${Object.keys(breaks.pieces).length} break sheets`);
