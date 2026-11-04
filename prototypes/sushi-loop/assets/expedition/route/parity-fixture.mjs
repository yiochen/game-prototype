// Reference output for the Godot route port.
//
//   node prototypes/sushi-loop/assets/expedition/route/parity-fixture.mjs [--check]
//
// godot/tests/expedition_route_tests.gd regenerates the same seeds with
// scripts/expedition/route.gd and must match this file exactly.
import { readFileSync, writeFileSync } from 'node:fs';
import { analyzeLibrary, assemble, composeScene, generate, hash, mulberry32 } from './route.js';
import { loadChunks } from './validate-chunks.mjs';

const OUT = new URL('../../../godot/tests/fixtures/expedition_route_parity.json', import.meta.url);
const pieces = JSON.parse(readFileSync(new URL('../../../godot/assets/expedition/pieces.json', import.meta.url), 'utf8'));
const rules = JSON.parse(readFileSync(new URL('../../../godot/content/expedition.json', import.meta.url), 'utf8'));
const v2 = Object.entries(pieces.objects).filter(([, o]) => ['rock', 'ruin', 'landmark', 'sealife-edge', 'sealife-floor'].includes(o.family)).map(([id, o]) => ({ id, ...o }));

export function fixture() {
  const { chunks } = analyzeLibrary(loadChunks());
  const rng = mulberry32(12345);
  return {
    primitives: { hash: [[0, 0, 0], [3, 17, 21], [10, 97700, 51], [-1, 5, 7]].map(([x, y, s]) => hash(x, y, s)), mulberry: Array.from({ length: 5 }, () => rng()) },
    library: chunks.map((c) => ({ id: c.id, difficulty: c.difficulty, next: c.next })),
    // Default-plan runs, plus the game's current plan (issue #22 feature slots).
    runs: [...[1, 2, 3, 7, 21, 99, 1234, 40000, 99999].map((seed) => [seed, null]), ...[1, 22, 777].map((seed) => [seed, rules.plan])].map(([seed, plan]) => {
      const sequence = generate(seed, chunks, plan ? { slots: plan } : {});
      const { rows, spans } = assemble(sequence);
      const scene = composeScene(rows, v2, seed);
      return { seed, ...(plan ? { plan } : {}), sequence: sequence.map((c) => c.id), spans, rows,
        objects: scene.objects.map((o) => [o.x, o.y, o.id, o.dir, o.w ?? 1]), beds: scene.beds.map((b) => b.sprite),
        seabed: scene.seabed.map((o) => [o.x, o.y, o.id, o.dir]), pickups: scene.pickups.map((p) => [p.x, p.y]),
        vents: scene.vents.map((v) => [v.x, v.y]), shafts: scene.shafts.map((s) => [s.x, s.y]), autopilot: scene.autopilot };
    }),
  };
}

const text = JSON.stringify(fixture()) + '\n';
if (process.argv.includes('--check')) {
  if (readFileSync(OUT, 'utf8') !== text) { console.error('parity fixture is stale'); process.exit(1); }
  console.log('parity fixture OK');
} else { writeFileSync(OUT, text); console.log('wrote', OUT.pathname); }
