// node check.mjs — fair parrotfish lines per reef chunk under balance.json, and route validation of each chunk.
import fs from 'node:fs';
import { validateChunk } from '../../assets/expedition/route/route.js';
import { REEF_CHUNKS, fairLines, reefRows } from './reef.js';
const rules = JSON.parse(fs.readFileSync(new URL('./balance.json', import.meta.url)));
for (const c of REEF_CHUNKS) {
  const [a, b] = reefRows(c.rows);
  const routeRows = c.rows.map((r) => r.replaceAll('b', '.'));
  const problems = validateChunk({ ...c, rows: routeRows, kind: 'creature', creature: 'boulderhead-parrotfish', attackRows: [a, b] });
  const { fair, rejected } = fairLines(c, rules);
  console.log(`${c.id.padEnd(14)} ${fair.length} fair, ${rejected.length} rejected${problems.length ? ' · route: ' + problems.join('; ') : ''}`);
}
