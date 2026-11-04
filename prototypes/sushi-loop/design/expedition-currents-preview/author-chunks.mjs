// Issue #22: author the feature chunks in the map-designer format, straight
// into the game's chunk folder (the review page reads them from there too).
//
//   node prototypes/sushi-loop/design/expedition-currents-preview/author-chunks.mjs
//
// Rows use the route characters plus feature marks: B boost, P portal
// (both open water). `currents` lists lateral fields as inclusive cell
// rectangles with a direction (+1 east, -1 west). Features and currents go
// into their own designer layers, which route.js ignores, so these chunks
// validate and join exactly like ordinary chunks.
import { writeFileSync } from 'node:fs';
import { chunkToMap, validateChunk, mulberry32 } from '../../assets/expedition/route/route.js';

const chunks = {
  'current-crossing': {
    kind: 'current', currents: [{ x0: 1, x1: 9, y0: 9, y1: 12, dir: 1 }, { x0: 1, x1: 9, y0: 2, y1: 5, dir: -1 }],
    rows: [
      '####...####',
      '###c....###',
      '##........#',
      '#c........#',
      '#.$.......#',
      '#.$.......#',
      '##.......m#',
      '###k...####',
      '###....c###',
      '#.........#',
      '#.......$.#',
      '#k.......$#',
      '##........#',
      '###.....###',
      '####...####',
      '####...####',
    ],
  },
  'portal-basin': {
    kind: 'portal', currents: [],
    rows: [
      '####...####',
      '###c...m###',
      '##k......##',
      '#c.......##',
      '#..P.....c#',
      '#.,......##',
      '##c...$..##',
      '###.....###',
      '##...$...##',
      '##m.....###',
      '###.....###',
      '####...####',
      '####...####',
    ],
  },
  'boost-run': {
    kind: 'boost', currents: [],
    rows: [
      '####...####',
      '####...####',
      '###c..$k###',
      '###..$.####',
      '##c.$..m###',
      '##...c..###',
      '###.....###',
      '###k.$.c###',
      '####...####',
      '###....####',
      '###.$..m###',
      '##m....####',
      '##..$...k##',
      '###.....###',
      '###..$..###',
      '###..B..###',
      '####...####',
      '####...####',
    ],
  },
};
// The second crossing mirrors the first so a run can meet both bands in either order.
const mirror = (row) => [...row].reverse().join('');
chunks['current-crossing-mirror'] = {
  kind: 'current', rows: chunks['current-crossing'].rows.map(mirror),
  currents: chunks['current-crossing'].currents.map((c) => ({ x0: 10 - c.x1, x1: 10 - c.x0, y0: c.y0, y1: c.y1, dir: -c.dir })),
};

let failed = false;
for (const [id, c] of Object.entries(chunks)) {
  const plain = c.rows.map((r) => r.replace(/[BP]/g, '.'));
  const problems = validateChunk({ id, kind: c.kind, rows: plain });
  console.log(id, problems.length ? problems : 'ok');
  failed ||= problems.length > 0;
  const doc = chunkToMap({ name: id, kind: c.kind, source: 'issue #22 review', rows: plain });
  doc.layers.push({ id: 'currents', collidable: false }, { id: 'features', collidable: false });
  for (const f of c.currents) for (let y = f.y0; y <= f.y1; y++) for (let x = f.x0; x <= f.x1; x++) {
    if (plain[y][x] === '#' || 'kcm'.includes(plain[y][x])) continue;
    doc.placements.push({ id: `currents:${x}:${y}`, layer: 'currents', object: f.dir > 0 ? 'current-east' : 'current-west', x, y, direction: f.dir > 0 ? 'E' : 'W', footprint: [1, 1] });
  }
  c.rows.forEach((row, y) => [...row].forEach((ch, x) => {
    if (ch === 'B') doc.placements.push({ id: `features:${x}:${y}`, layer: 'features', object: 'boost', x, y, direction: 'S', footprint: [1, 1] });
    if (ch === 'P') doc.placements.push({ id: `features:${x}:${y}`, layer: 'features', object: 'portal-ring', x, y, direction: 'S', footprint: [1, 1] });
  }));
  writeFileSync(new URL(`../../godot/content/expedition/chunks/${id}.json`, import.meta.url), JSON.stringify(doc, null, 1) + '\n');
}
process.exitCode = failed ? 1 : 0;
