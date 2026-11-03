import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { analyzeLibrary, assemble, chunkFromMap, chunkToMap, composeScene, deadEnds, generate, reachable, seamWidth, shipProblems, validateChunk, COLUMNS, MIN_SEAM, runs } from '../assets/expedition/route/route.js';
import { loadChunks } from '../assets/expedition/route/validate-chunks.mjs';

const files = loadChunks();
const { chunks: library, problems } = analyzeLibrary(files);

test('every chunk file loads as a valid designer document', () => {
  assert.deepEqual(problems, {});
  assert.equal(library.length, files.length);
  for (const chunk of files) assert.deepEqual(chunkFromMap(chunkToMap(chunk), chunk.id).rows, chunk.rows, chunk.id);
});

test('an invalid chunk is reported and left out instead of breaking the run', () => {
  const broken = { id: 'broken', kind: 'normal', rows: Array(6).fill('###########') };
  const result = analyzeLibrary([...files, broken]);
  assert.ok(result.problems.broken);
  assert.ok(!result.chunks.some((c) => c.id === 'broken'));
});

test('an authored difficulty override replaces the computed score', () => {
  const [first] = files;
  const { chunks } = analyzeLibrary([{ ...first, difficultyOverride: 4.5 }]);
  assert.equal(chunks[0].difficulty, 4.5);
});
const v2 = JSON.parse(readFileSync(new URL('../assets/expedition/v2/library.json', import.meta.url), 'utf8')).objects;

test('every chunk is passable with no dead ends and reachable gold', () => {
  for (const chunk of library) assert.deepEqual(validateChunk(chunk), [], chunk.id);
});

test('library offers every slot kind, including forks with two lanes', () => {
  const kinds = new Set(library.map((c) => c.kind));
  for (const kind of ['launch', 'start', 'normal', 'rest', 'fork', 'finish']) assert.ok(kinds.has(kind), kind);
  for (const fork of library.filter((c) => c.kind === 'fork')) {
    assert.ok(fork.rows.some((row) => runs(row).length >= 2), `${fork.id} splits into lanes`);
  }
});

test('ship physics rejects one-cell diagonal steps that need instant steering', () => {
  const zigzag = ['####.######', '###.#######', '####.######', '###.#######', '####.######', '###.#######'];
  assert.ok(shipProblems(zigzag).includes('exit unreachable by the ship'));
  const straight = Array(6).fill('####..#####');
  assert.deepEqual(shipProblems(straight), []);
});

test('assembled routes fly end to end with the real hull, steering speed and no trap lanes', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const { rows } = assemble(generate(seed, library));
    const problems = shipProblems(rows).filter((p) => !p.startsWith('gold'));
    assert.deepEqual(problems, [], `seed ${seed}`);
  }
});

test('launch chunks keep the cruise lane clear and carry no gold', () => {
  const lane = Array(16).fill('##.......##');
  assert.deepEqual(validateChunk({ kind: 'launch', rows: lane }), []);
  assert.ok(validateChunk({ kind: 'launch', rows: ['##..$....##', ...lane.slice(1)] }).includes('launch chunks carry no gold'));
  assert.ok(validateChunk({ kind: 'launch', rows: ['##...#...##', ...lane.slice(1)] }).includes('launch chunks keep columns 4-6 open'));
});

test('dead-end detection rejects a pocket that cannot rise to the exit', () => {
  // Column 1 opens off the passage at row 3 but is capped by rock at row 0.
  const rows = ['####...####', '###.#...###', '###.#...###', '###.....###', '####...####'];
  assert.ok(deadEnds(rows).length > 0);
  assert.ok(validateChunk({ rows }).some((p) => p.startsWith('dead ends')));
});

test('same seed gives the same route; different seeds vary', () => {
  const a = generate(1234, library).map((c) => c.id);
  assert.deepEqual(generate(1234, library).map((c) => c.id), a);
  const distinct = new Set(Array.from({ length: 20 }, (_, i) => generate(i + 1, library).map((c) => c.id).join()));
  assert.ok(distinct.size > 10);
});

test('generated runs join only through wide seams and stay passable end to end', () => {
  for (let seed = 1; seed <= 200; seed++) {
    const sequence = generate(seed, library);
    assert.deepEqual(sequence.slice(0, 3).map((c) => c.kind), ['launch', 'launch', 'start']);
    assert.equal(sequence.at(-1).kind, 'finish');
    for (let i = 1; i < sequence.length; i++) {
      assert.ok(sequence[i - 1].next.includes(sequence[i].id), `seed ${seed}: ${sequence[i - 1].id} -> ${sequence[i].id}`);
      assert.ok(seamWidth(sequence[i].rows.at(-1), sequence[i - 1].rows[0]) >= MIN_SEAM);
    }
    const { rows } = assemble(sequence);
    assert.deepEqual(deadEnds(rows), [], `seed ${seed} dead ends`);
    const reach = reachable(rows);
    assert.ok([...rows[0]].some((ch, x) => ch !== '#' && reach.has(`${x},0`)), `seed ${seed} finish reachable`);
  }
});

test('difficulty rises from the opening toward the final stretch', () => {
  let early = 0, late = 0;
  for (let seed = 1; seed <= 100; seed++) {
    const normal = generate(seed, library).filter((c) => c.kind === 'normal');
    early += normal[0].difficulty; late += normal.at(-1).difficulty;
  }
  assert.ok(late > early, `late ${late} > early ${early}`);
});

test('scene composition keeps collision on rock cells and gold on water', () => {
  const { rows } = assemble(generate(7, library));
  const scene = composeScene(rows, v2, 7);
  assert.equal(scene.columns, COLUMNS);
  for (const { x, y } of scene.collision) assert.ok('#kcm'.includes(rows[y][x]));
  for (const p of scene.pickups) assert.equal(rows[Math.floor(p.y)][Math.floor(p.x)], '$');
  for (const o of scene.objects.filter((o) => o.w > 1)) {
    assert.ok('#kcm'.includes(rows[o.y][o.x]) && '#kcm'.includes(rows[o.y][o.x + o.w - 1]), 'landmark legs stand on rock');
    for (let x = o.x + 1; x < o.x + o.w - 1; x++) assert.ok(!'#kcm'.includes(rows[o.y][x]), 'landmark span stays open');
  }
});
