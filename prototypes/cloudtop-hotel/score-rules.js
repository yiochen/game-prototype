import { createGame, pick, advanceDeal, beginRoof, finishRoof, segments } from './engine.js';

// Bump this when balance or deterministic replay rules change.
export const SCORE_VERSION = 'paper-v3';
export function replayRun(seed, moves, complete = true) {
  if (typeof seed !== 'string' || !/^[a-zA-Z0-9_-]{1,64}$/.test(seed) || !Array.isArray(moves) || moves.length > 100) throw new Error('Invalid guestbook record.');
  const state = createGame(seed);
  for (const move of moves) {
    if (!Array.isArray(move) || move.length < 1 || move.length > 2 || !Number.isInteger(move[0]) || (move[1] != null && !['bunny', 'frog', 'cat'].includes(move[1]))) throw new Error('Invalid card choice.');
    if (move[1] != null && state.offer[move[0]]?.type !== 'choice') throw new Error('Only Room Choice accepts a guest type.');
    if (!pick(state, move[0], move[1]) || !advanceDeal(state)) throw new Error('This run contains a card that could not be bought.');
  }
  if (complete && (!beginRoof(state) || !finishRoof(state))) throw new Error('Finish your hotel before signing the guestbook.');
  return state;
}
export function scoreOf(state) {
  return { floors: state.links.length, neighborhoods: segments(state).length, coins: state.cash };
}
export function compareScores(a, b) {
  return b.floors - a.floors || b.neighborhoods - a.neighborhoods || b.coins - a.coins || a.createdAt.localeCompare(b.createdAt) || a.id.localeCompare(b.id);
}
export function cleanName(value) {
  if (typeof value !== 'string') throw new Error('Add your innkeeper name.');
  const name = value.normalize('NFKC').trim().replace(/\s+/g, ' ');
  if (!/^[\p{L}\p{N} ._'’-]{1,20}$/u.test(name)) throw new Error('Use 1–20 letters, numbers, spaces, or simple punctuation.');
  return name;
}
