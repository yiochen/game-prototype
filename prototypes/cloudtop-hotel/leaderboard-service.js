import { createHash } from 'node:crypto';
import { cleanName, compareScores, replayRun, scoreOf, SCORE_VERSION } from './score-rules.js';

// Independent from Netlify so validation and simultaneous writes can be tested.
export async function handleLeaderboard(request, store) {
  const respond = (body, status = 200) => Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
  if (request.method === 'GET') return respond({ entries: (await store.get('top', { type: 'json' })) ?? [], version: SCORE_VERSION });
  if (request.method !== 'POST') return respond({ error: 'Method not allowed.' }, 405);
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return respond({ error: 'Please submit from the game.' }, 403);
  if (!request.headers.get('content-type')?.startsWith('application/json')) return respond({ error: 'Send a game record.' }, 415);
  const bytes = await request.arrayBuffer();
  if (bytes.byteLength > 12000) return respond({ error: 'This game record is too large.' }, 413);
  let entry;
  try {
    const body = JSON.parse(new TextDecoder().decode(bytes));
    if (!body || typeof body !== 'object') throw new Error('Invalid game record.');
    if (body.version !== SCORE_VERSION) throw new Error('Please refresh the game before submitting.');
    const name = cleanName(body.name), state = replayRun(body.seed, body.moves);
    // Identical runs occupy one place, even if re-submitted or renamed.
    const id = createHash('sha256').update(JSON.stringify([SCORE_VERSION, body.seed, body.moves.map(([index, suit]) => [index, suit ?? null])])).digest('hex').slice(0,32);
    entry = { id, name, seed: body.seed, ...scoreOf(state), createdAt: new Date().toISOString() };
  } catch (error) { return respond({ error: error instanceof SyntaxError ? 'Invalid game record.' : error.message }, 400); }
  for (let attempt = 0; attempt < 5; attempt++) {
    const current = await store.getWithMetadata('top', { type: 'json' });
    const entries = current?.data ?? [];
    const existing = entries.find(row => row.id === entry.id);
    if (existing) return respond({ entry: existing, rank: entries.indexOf(existing) + 1, entries });
    const next = [...entries, entry].sort(compareScores).slice(0,100);
    const rank = next.findIndex(row => row.id === entry.id) + 1;
    if (!rank) return respond({ entry, rank: null, entries });
    const result = await store.setJSON('top', next, current ? { onlyIfMatch: current.etag } : { onlyIfNew: true });
    if (result.modified) return respond({ entry, rank, entries: next }, 201);
  }
  return respond({ error: 'The guestbook is busy. Please try signing again.' }, 503);
}
