// Report on the expedition chunk folder (no build output; the game, review
// page and designer analyse chunks when they load them).
//
//   node prototypes/sushi-loop/assets/expedition/route/validate-chunks.mjs
//
// Exits non-zero when any chunk is invalid.
import { readdirSync, readFileSync } from 'node:fs';
import { analyzeLibrary, chunkFromMap } from './route.js';

export const CHUNK_DIR = new URL('../../../godot/content/expedition/chunks/', import.meta.url);

export function loadChunks(dir = CHUNK_DIR) {
  return readdirSync(dir).filter((f) => f.endsWith('.json')).sort()
    .map((f) => chunkFromMap(JSON.parse(readFileSync(new URL(f, dir), 'utf8')), f.slice(0, -5)));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { chunks, problems } = analyzeLibrary(loadChunks());
  for (const c of chunks) console.log(`${c.id.padEnd(26)} ${c.kind.padEnd(7)} d=${String(c.difficulty).padEnd(4)}${c.difficultyOverride != null ? '(set)' : '     '} rows=${String(c.rows.length).padEnd(3)} next=${c.next.length}`);
  for (const [id, list] of Object.entries(problems)) console.error(`INVALID ${id}: ${list.join('; ')}`);
  process.exit(Object.keys(problems).length ? 1 : 0);
}
