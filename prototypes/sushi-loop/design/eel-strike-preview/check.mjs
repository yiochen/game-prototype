// node check.mjs — runs the #25 creature-chunk checks without a browser.
import fs from 'node:fs';
import { analyzeLibrary, chunkFromMap, compatible, validateChunk } from '../../assets/expedition/route/route.js';
import { analyzeCreatureChunk } from './fairness.js';
const rules = JSON.parse(fs.readFileSync(new URL('./balance.json', import.meta.url)));
const read = (dir) => fs.readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => ({ id: f.slice(0, -5), doc: JSON.parse(fs.readFileSync(`${dir}/${f}`)) }));
const { chunks: library } = analyzeLibrary(read(new URL('../../godot/content/expedition/chunks/', import.meta.url).pathname).map(({ id, doc }) => chunkFromMap(doc, id)));
const normals = library.filter((c) => c.kind === 'normal');
let failed = 0;
for (const { id, doc } of read(new URL('./chunks/', import.meta.url).pathname)) {
  const chunk = { ...chunkFromMap(doc, id), kind: 'normal', attack: doc.chunk.attack_rows };
  const route = validateChunk(chunk);
  const report = analyzeCreatureChunk(chunk, rules);
  const before = normals.filter((n) => compatible(n, chunk)).length, after = normals.filter((n) => compatible(chunk, n)).length;
  const expectRejected = doc.chunk.review_example === 'rejected';
  const ok = route.length === 0 && before > 2 && after > 2 && report.accepted !== expectRejected;
  if (!ok) failed++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${id}: route ${route.join('; ') || 'valid'}; follows ${before} / followed by ${after} normal chunks; ${report.strikes.length} strike rows, fair strips ${report.strikes.map((s) => s.fair.length).join(',')}; ${report.accepted ? 'accepted' : `rejected (${report.problems.join('; ')})`}${expectRejected ? ' [expected rejection]' : ''}`);
}
process.exit(failed ? 1 : 0);
