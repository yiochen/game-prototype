// node check.mjs — which ordinary chunks stay fair under the ink settings in balance.json.
import fs from 'node:fs';
import { analyzeLibrary, chunkFromMap } from '../../assets/expedition/route/route.js';
import { analyzeSight, judge } from './sight.js';
const rules = JSON.parse(fs.readFileSync(new URL('./balance.json', import.meta.url)));
const dir = new URL('../../godot/content/expedition/chunks/', import.meta.url).pathname;
const docs = fs.readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => chunkFromMap(JSON.parse(fs.readFileSync(dir + f)), f.slice(0, -5)));
const { chunks } = analyzeLibrary(docs);
for (const c of chunks.filter((c) => ['normal', 'fork', 'rest'].includes(c.kind))) {
  const r = analyzeSight(c.rows, rules), j = judge(r, rules.ink);
  console.log(`${c.kind.padEnd(6)} ${j.fair ? 'fair' : 'NO  '} ${c.id.padEnd(28)} d${c.difficulty?.toFixed?.(1) ?? '?'} needs ${r.needRows.toFixed(1)} rows, ${r.forks.length} forks${j.fair ? '' : ' · ' + j.problems.slice(0, 2).join('; ')}`);
}
