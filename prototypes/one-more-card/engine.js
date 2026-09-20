import { BALANCE } from './balance.js';
export { BALANCE };
export const suitInfo = id => BALANCE.suits.find(s => s.id === id);
const sum = values => values.reduce((a, b) => a + b, 0);
export const chain = state => state.links.length;
export const finished = state => state.phase === 'complete';
export const baseCards = (state, suit) => state.history.filter(e => e.family === 'base' && (!suit || e.suit === suit));
// A segment is a maximal consecutive run of one suit, regardless of purchase.
// Its stable ID is the first link's ID. Inserting links never renumbers targets.
export function segments(state, suit = null) {
  const runs = [];
  state.links.forEach((link, index) => {
    const previous = runs.at(-1);
    if (previous?.suit === link.suit) { previous.length++; previous.end = index + 1; }
    else runs.push({ id: link.id, suit: link.suit, start: index, end: index + 1, length: 1 });
  });
  return suit ? runs.filter(run => run.suit === suit) : runs;
}
export const longestSegment = state => segments(state).reduce((best, run) => !best || run.length > best.length ? run : best, null);
export const overgrowLinks = state => {
  const run = longestSegment(state), config = BALANCE.growth.overgrow;
  return run ? Math.min(config.maximum, Math.max(config.minimum, Math.floor(run.length / config.linksPerBonus))) : 0;
};
export const recallLinks = (state, suit) => sum(segments(state, suit).map(run => Math.min(run.length, BALANCE.growth.recall.linksPerSegmentCap))) * BALANCE.growth.recall.multiplier;
export const vaultSuit = state => state.links.at(-1)?.suit ?? BALANCE.wealth.vault.openingSuit;
export const upgradeKey = card => card.type === 'suit' ? `suit:${card.suit}` : card.type;
export const upgradeValue = (state, type, suit) => {
  const level = state.upgrades[type === 'suit' ? `suit:${suit}` : type] ?? 0;
  return level ? BALANCE.reactor[type].values[level - 1] : 0;
};
export const mysteryOutcomes = (state, level = state.upgrades.stabilizer ?? 0) => level ? BALANCE.reactor.stabilizer.outcomesByLevel[level - 1] : BALANCE.base.mystery.outcomes;
export const outcomePercent = (outcome, outcomes) => Number((100 * outcome.weight / sum(outcomes.map(o => o.weight))).toFixed(2));
export const mysteryOddsText = (state, level = state.upgrades.stabilizer ?? 0, bonus = 0) => {
  const outcomes = mysteryOutcomes(state, level);
  return outcomes.map(o => `${o.links + bonus}: ${outcomePercent(o, outcomes)}%`).join(', ');
};
export const baseBonus = (state, card) => upgradeValue(state, 'suit', card.suit) + (card.type === 'mystery' ? 0 : upgradeValue(state, 'assembler'));
export function weightedPick(items, roll) {
  const total = sum(items.map(item => item.weight));
  if (!items.length || total <= 0) throw new Error('Empty weighted pool');
  let point = roll * total;
  for (const item of items) { point -= item.weight; if (point < 0) return item; }
  return items.at(-1);
}
function seedNumber(seed) {
  let hash = 2166136261;
  for (const char of String(seed)) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
  return (hash >>> 0) || 1;
}
function random(state, key = 'rng') {
  let x = state[key]; x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
  state[key] = x >>> 0;
  return state[key] / 4294967296;
}
function card(family, type, suit = null, level = null) {
  const config = BALANCE[family][type];
  return { id: [family, type, suit, level].filter(v => v !== null).join(':'), family, type, suit, level,
    price: level ? config.prices[level - 1] : config.price,
    name: `${suit ? `${suitInfo(suit).name} ` : ''}${config.name}${level ? ` ${level}` : ''}` };
}
// Only the next level is eligible. Growth requires an existing target.
export function eligibleCards(state) {
  const pool = [];
  for (const type of Object.keys(BALANCE.base)) for (const suit of BALANCE.suits) pool.push(card('base', type, suit.id));
  for (const type of Object.keys(BALANCE.growth)) {
    if (type === 'overgrow') { if (segments(state).length) pool.push(card('growth', type)); }
    else for (const suit of BALANCE.suits) if (segments(state, suit.id).length) pool.push(card('growth', type, suit.id));
  }
  for (const type of Object.keys(BALANCE.reactor)) {
    for (const suit of type === 'suit' ? BALANCE.suits.map(s => s.id) : [null]) {
      const next = (state.upgrades[type === 'suit' ? `suit:${suit}` : type] ?? 0) + 1;
      if (next <= BALANCE.reactor[type].prices.length) pool.push(card('reactor', type, suit, next));
    }
  }
  if (Math.floor((state.cash - BALANCE.wealth.vault.price) / BALANCE.wealth.vault.cashPerLink) > 0) pool.push(card('wealth', 'vault'));
  if (!state.rebateRemaining) pool.push(card('wealth', 'rebate'));
  return pool;
}
// Family, then type, then suit. New tiers never increase a family's weight.
function draw(state, pool) {
  const families = Object.entries(BALANCE.families).filter(([id]) => pool.some(c => c.family === id)).map(([id, weight]) => ({ id, weight }));
  const family = weightedPick(families, random(state)).id;
  const types = Object.entries(BALANCE[family]).filter(([id]) => pool.some(c => c.family === family && c.type === id)).map(([id, config]) => ({ id, weight: config.weight }));
  const type = weightedPick(types, random(state)).id;
  const variants = pool.filter(c => c.family === family && c.type === type);
  return variants[Math.floor(random(state) * variants.length)];
}
function deal(state) {
  const pool = eligibleCards(state);
  const affordable = pool.filter(c => c.price <= state.cash);
  if (!affordable.length) { state.offer = []; state.phase = 'complete'; return; }
  let remaining = [...pool];
  state.offer = Array.from({ length: BALANCE.offerSize }, () => {
    const chosen = draw(state, remaining);
    remaining = remaining.filter(c => c.id !== chosen.id);
    return chosen;
  });
  // Prevent a random unaffordable draw from ending a viable run.
  if (!state.offer.some(c => c.price <= state.cash)) {
    state.offer[0] = affordable.reduce((a, b) => a.price <= b.price ? a : b);
  }
  state.deals++;
  state.phase = 'picking';
}
export function createGame(seed = 'build-an-engine') {
  const state = { seed: String(seed), rng: seedNumber(seed), prizeRng: seedNumber(`${seed}:prizes`),
    cash: BALANCE.startingCash, spent: 0, refunded: 0, history: [], links: [], nextLinkId: 0, upgrades: {}, rebateRemaining: 0,
    offer: [], deals: 0, phase: 'picking', lastEffect: null };
  deal(state); return state;
}
export function canBuy(state, offer) {
  if (state.phase !== 'picking' || !offer || offer.price > state.cash || !eligibleCards(state).some(c => c.id === offer.id)) return false;
  return true;
}
export function preview(state, offer) {
  const config = BALANCE[offer.family][offer.type];
  const refund = offer.family === 'base' && state.rebateRemaining ? Math.min(BALANCE.wealth.rebate.refund, offer.price - 1) : 0;
  const cashAfter = state.cash - offer.price + refund;
  let headline, detail;
  if (offer.family === 'base') {
    const bonus = baseBonus(state, offer);
    if (offer.type === 'mystery') {
      headline = mysteryOutcomes(state).map(o => o.links + bonus).join(' / ');
      detail = `Mystery odds — ${mysteryOddsText(state, undefined, bonus)}. One draw.`;
    } else { headline = `+${config.links + bonus}`; detail = `${config.links} fixed${bonus ? ` + ${bonus} from upgrades` : ''} links in this suit.`; }
  } else if (offer.family === 'growth') {
    const matches = segments(state, offer.suit);
    if (offer.type === 'recall') { headline = `+${recallLinks(state, offer.suit)}`; detail = `Append ${suitInfo(offer.suit).name} links: up to ${config.linksPerSegmentCap} per existing ${suitInfo(offer.suit).name} segment ×${config.multiplier}.`; }
    if (offer.type === 'polish') { headline = `+${matches.length * config.linksPerSegment}`; detail = `Insert ${config.linksPerSegment} link(s) into each ${suitInfo(offer.suit).name} segment. Short segments become stronger for Recall.`; }
    if (offer.type === 'overgrow') { const run = longestSegment(state); headline = `+${overgrowLinks(state)}`; detail = `Automatically extend the longest segment: ${suitInfo(run.suit).name} ${run.length} → ${run.length + overgrowLinks(state)}. +1 per ${config.linksPerBonus} links, minimum ${config.minimum}, cap ${config.maximum}. Earliest wins ties.`; }
  } else if (offer.family === 'reactor') {
    if (offer.type === 'stabilizer') {
      const outcomes = mysteryOutcomes(state, offer.level), top = outcomes.at(-1);
      headline = `${outcomePercent(top, outcomes)}%`;
      detail = `Future Mystery odds — ${mysteryOddsText(state, offer.level)}. Replaces the old odds.`;
    } else {
      const before = upgradeValue(state, offer.type, offer.suit), after = config.values[offer.level - 1];
      headline = `${before} → ${after}`;
      detail = `Future ${offer.type === 'suit' ? suitInfo(offer.suit).name : 'Fixed'} base cards gain +${after}. Replaces the old level.`;
    }
  } else if (offer.type === 'vault') { headline = `+${Math.floor(cashAfter / config.cashPerLink)}`; detail = `One ${suitInfo(vaultSuit(state)).name} link per $${config.cashPerLink} left after paying. Extends the tail suit.`; }
  else { headline = `$${config.refund} × ${config.purchases}`; detail = `Refund on your next ${config.purchases} base purchases. Cannot stack.`; }
  return { headline, detail, cashAfter, refund };
}
export function pick(state, index) {
  if (!Number.isInteger(index) || index < 0 || index >= state.offer.length) return false;
  const offer = state.offer[index];
  if (!canBuy(state, offer)) return false;
  const config = BALANCE[offer.family][offer.type];
  const before = chain(state);
  const entry = { ...offer, cardId: offer.id, id: state.history.length, links: 0 };
  state.cash -= offer.price; state.spent += offer.price;
  const affected = [], addedIds = [];
  const emit = (suit, count, at = state.links.length) => {
    const links = Array.from({ length: count }, () => ({ id: state.nextLinkId++, suit, source: entry.id }));
    addedIds.push(...links.map(link => link.id));
    state.links.splice(at, 0, ...links);
  };
  let message = '';
  if (offer.family === 'base') {
    let value;
    if (offer.type === 'mystery') {
      entry.result = weightedPick(mysteryOutcomes(state), random(state, 'prizeRng')).links;
      value = entry.result + baseBonus(state, offer);
      message = `Rolled ${entry.result}${baseBonus(state, offer) ? ` + ${baseBonus(state, offer)} from upgrades` : ''}.`;
    } else value = config.links + baseBonus(state, offer);
    emit(offer.suit, value);
    if (state.rebateRemaining) {
      // A base purchase always consumes at least $1, even after tuning prices.
      entry.refund = Math.min(BALANCE.wealth.rebate.refund, offer.price - 1);
      state.cash += entry.refund; state.refunded += entry.refund; state.rebateRemaining--;
      message += ` $${entry.refund} refunded; ${state.rebateRemaining} rebates left.`;
    }
  } else if (offer.family === 'growth') {
    const targets = offer.type === 'overgrow' ? [longestSegment(state)] : segments(state, offer.suit);
    for (const run of targets) affected.push(...state.links.slice(run.start, run.end).map(link => link.id));
    if (offer.type === 'recall') {
      const count = recallLinks(state, offer.suit); // Snapshot before emitting; never recursively activates.
      emit(offer.suit, count);
      message = `${targets.length} ${suitInfo(offer.suit).name} segment(s) paid up to ${config.linksPerSegmentCap} each.`;
    } else {
      // Insert from the end so earlier run boundaries keep their indices.
      const amount = offer.type === 'polish' ? config.linksPerSegment : overgrowLinks(state);
      for (const run of [...targets].reverse()) emit(run.suit, amount, run.end);
      message = offer.type === 'overgrow' ? `Longest segment: ${suitInfo(targets[0].suit).name} ${targets[0].length} → ${targets[0].length + amount}.` : `Extended ${targets.length} segment(s) in place. Recall counts up to ${BALANCE.growth.recall.linksPerSegmentCap} per segment.`;
    }
  } else if (offer.family === 'reactor') {
    state.upgrades[upgradeKey(offer)] = offer.level;
    message = `${offer.name} installed. ${preview(state, offer).detail}`;
  } else if (offer.type === 'vault') {
    const suit = vaultSuit(state);
    emit(suit, Math.floor(state.cash / config.cashPerLink));
    message = `${suitInfo(suit).name} links extend the tail suit.`;
  } else { state.rebateRemaining = config.purchases; message = `Next ${config.purchases} base purchases each refund up to $${config.refund}.`; }
  entry.links = chain(state) - before;
  state.history.push(entry);
  state.lastEffect = { added: entry.links, entryId: entry.id, affected, addedIds, message: message.trim() };
  state.offer = []; state.phase = 'resolving';
  return true;
}
export function advanceDeal(state) {
  if (state.phase !== 'resolving') return false;
  deal(state); return true;
}
