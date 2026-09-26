import { BALANCE } from './balance.js';
export { BALANCE };
export const suitInfo = id => BALANCE.suits.find(s => s.id === id);
const sum = values => values.reduce((a, b) => a + b, 0);
export const chain = state => state.links.length;
export const finished = state => state.phase === 'complete';
export const baseCards = (state, suit) => state.history.filter(e => e.family === 'base' && (!suit || e.suit === suit));
// A segment is a maximal consecutive run of one suit, regardless of purchase.
// Its stable ID is the first link's ID. New links only append to the chain.
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
export const recallLinks = (state, suit) => segments(state, suit).length * BALANCE.growth.recall.linksPerSegment;
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
export const baseBonus = (state, card) => card.type === 'mosaic' ? 0 : upgradeValue(state, 'suit', card.suit) + (card.type === 'mystery' ? 0 : upgradeValue(state, 'assembler'));
export const choiceSuits = state => state.attunement ? [state.attunement.suit] : BALANCE.suits.map(s => s.id);
export function foundationEffect(state, offer) {
  if (!state.foundation) return { bonus: 0, ends: false };
  if (offer.sequence || (offer.suit && state.foundation.suit && offer.suit !== state.foundation.suit)) return { bonus: 0, ends: true };
  return { bonus: offer.suit ? state.foundation.bonus + BALANCE.strategy.foundation.bonusStep : 0, ends: false };
}
// Streaks follow the purchased type, never the generated bonus rooms.
export function paradeEffect(state, offer) {
  if (!state.parade) return { bonus: 0, ends: false };
  // Every Mosaic advances once, even if its first/last guest matches the last
  // purchase. Its last printed guest anchors the bonus and next typed purchase.
  const suit = offer.sequence?.at(-1) ?? offer.suit;
  if (!offer.sequence && suit && suit === state.parade.suit) return { bonus: 0, ends: true };
  return { bonus: suit ? state.parade.bonus + BALANCE.strategy.parade.bonusStep : 0, ends: false, suit };
}
export const frenzyActive = state => !!(state.foundation || state.parade) && ['picking', 'resolving'].includes(state.phase);
export const sequenceText = offer => offer.sequence.map(suit => suitInfo(suit).name).join(' → ');
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
function mosaicCards() {
  const variants = [];
  for (const pattern of BALANCE.base.mosaic.patterns) {
    const count = new Set(pattern.slots).size;
    function fill(suits) {
      if (suits.length < count) {
        for (const suit of BALANCE.suits) if (!suits.includes(suit.id)) fill([...suits, suit.id]);
        return;
      }
      const sequence = pattern.slots.map(slot => suits[slot]);
      variants.push({ ...card('base', 'mosaic'), id: `base:mosaic:${sequence.join(':')}`, name: `Mosaic ${pattern.name}`, pattern: pattern.id, sequence });
    }
    fill([]);
  }
  return variants;
}
// Only the next level is eligible. Growth requires an existing target.
export function eligibleCards(state) {
  const pool = [];
  for (const type of Object.keys(BALANCE.base)) {
    if (type === 'mosaic') pool.push(...mosaicCards());
    else if (type === 'choice') pool.push(card('base', type));
    else for (const suit of BALANCE.suits) pool.push(card('base', type, suit.id));
  }
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
  if (!state.foundation && !state.parade) pool.push(card('strategy', 'foundation'), card('strategy', 'parade'));
  if (!state.attunement) for (const suit of BALANCE.suits) pool.push(card('strategy', 'attunement', suit.id));
  return state.attunement ? pool.filter(c => !c.sequence && (!c.suit || c.suit === state.attunement.suit)) : pool;
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
  if (!affordable.length) {
    state.offer = [{ id: 'finale:roof', family: 'finale', type: 'roof', price: 0, name: 'Roof' }];
    state.phase = 'roof-ready';
    return;
  }
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
  const state = { seed: String(seed), rng: seedNumber(seed), prizeRng: seedNumber(`${seed}:prizes`), paradeRng: seedNumber(`${seed}:parade`),
    cash: BALANCE.startingCash, spent: 0, refunded: 0, history: [], links: [], nextLinkId: 0, upgrades: {}, rebateRemaining: 0,
    foundation: null, parade: null, attunement: null, offer: [], deals: 0, phase: 'picking', lastEffect: null };
  deal(state); return state;
}
export function canBuy(state, offer) {
  if (state.phase !== 'picking' || !offer || offer.price > state.cash || !eligibleCards(state).some(c => c.id === offer.id)) return false;
  return true;
}
export function preview(state, offer, selectedSuit) {
  if (offer.type === 'choice' && !selectedSuit) {
    const choices = choiceSuits(state).map(suit => ({ suit, ...preview(state, offer, suit) }));
    const values = choices.map(c => Number(c.headline.slice(1)));
    return { ...choices[0], headline: Math.min(...values) === Math.max(...values) ? `+${values[0]}` : `+${Math.min(...values)}–${Math.max(...values)}`, detail: 'Choose a suit before paying. Room and streak bonuses use your choice.' + (state.parade ? ' Guest Parade bonus rooms use a random different type.' : ''), choices, foundationBonus: 0, endsFoundation: false, paradeBonus: 0, endsParade: false };
  }
  if (offer.type === 'choice') offer = { ...offer, suit: selectedSuit };
  const foundation = foundationEffect(state, offer), parade = paradeEffect(state, offer);
  const config = BALANCE[offer.family][offer.type];
  const refund = offer.family === 'base' && state.rebateRemaining ? Math.min(BALANCE.wealth.rebate.refund, offer.price - 1) : 0;
  const cashAfter = state.cash - offer.price + refund;
  let headline, detail;
  if (offer.family === 'base') {
    const bonus = baseBonus(state, offer);
    if (offer.type === 'mosaic') {
      headline = `+${offer.sequence.length}`; detail = `Append in order: ${sequenceText(offer)}. Exact pattern; no Reactor or Assembler bonus.`;
    } else if (offer.type === 'mystery') {
      headline = mysteryOutcomes(state).map(o => o.links + bonus).join(' / ');
      detail = `Mystery odds — ${mysteryOddsText(state, undefined, bonus)}. One draw.`;
    } else { headline = `+${config.links + bonus}`; detail = `${config.links} fixed${bonus ? ` + ${bonus} from upgrades` : ''} links in this suit.`; }
  } else if (offer.family === 'growth') {
    if (offer.type === 'recall') { headline = `+${recallLinks(state, offer.suit)}`; detail = `Append ${config.linksPerSegment} ${suitInfo(offer.suit).name} link(s) per existing matching segment, regardless of its length.`; }
    if (offer.type === 'overgrow') { const run = longestSegment(state); headline = `+${overgrowLinks(state)}`; detail = `Append ${overgrowLinks(state)} ${suitInfo(run.suit).name} links at the end, based on the longest segment (${run.length} links). +1 per ${config.linksPerBonus} links, minimum ${config.minimum}, cap ${config.maximum}. Earliest wins ties.`; }
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
  } else if (offer.family === 'strategy') {
    headline = config.bonusStep ? `+${config.bonusStep}…` : '100%';
    detail = offer.type === 'parade' ? 'Next typed purchase earns +1 bonus room. Change the purchased type to earn +2, +3… bonus rooms. Each bonus batch uses one random type different from the purchase (equal chances). Every Mosaic pattern also advances once, using its final printed guest as the type to change from next. Its bonus differs from that final guest. Repeating a single purchased type ends the parade; untyped powers pause it. One streak at a time.' : offer.type === 'foundation' ? 'Next suited purchase starts a streak. Matching purchases append a growing bonus; switching suits or buying Mosaic ends it. Suitless purchases pause it.' : `Next ${config.shops} shops: all suited offers are ${suitInfo(offer.suit).name}. Choice 1 is locked to this suit; Mosaic pauses. Every purchase uses one shop.`;
  } else if (offer.type === 'vault') { headline = `+${Math.floor(cashAfter / config.cashPerLink)}`; detail = `One ${suitInfo(vaultSuit(state)).name} link per $${config.cashPerLink} left after paying. Extends the tail suit.`; }
  else { headline = `$${config.refund} × ${config.purchases}`; detail = `Refund on your next ${config.purchases} base purchases. Cannot stack.`; }
  if (foundation.bonus) {
    if (offer.family === 'base' && offer.type === 'mystery') headline = mysteryOutcomes(state).map(o => o.links + baseBonus(state, offer) + foundation.bonus).join(' / ');
    else if (headline.startsWith('+')) headline = `+${Number(headline.slice(1)) + foundation.bonus}`;
    detail += ` Foundation appends +${foundation.bonus} ${suitInfo(offer.suit).name} links.`;
  }
  if (foundation.ends) detail += ' Ends Foundation.';
  if (parade.bonus) {
    if (offer.family === 'base' && offer.type === 'mystery') headline = mysteryOutcomes(state).map(o => o.links + baseBonus(state, offer) + parade.bonus).join(' / ');
    else if (headline.startsWith('+')) headline = `+${Number(headline.slice(1)) + parade.bonus}`;
    const types = BALANCE.suits.filter(s => s.id !== parade.suit).map(s => s.name).join(' or ');
    detail += ` Guest Parade appends +${parade.bonus} bonus rooms: all ${types}, chosen randomly with equal chances. Your next typed purchase must differ from ${suitInfo(parade.suit).name}; any Mosaic continues.`;
  }
  if (parade.ends) detail += ' Ends Guest Parade.';
  else if (state.parade && !parade.bonus && offer.type !== 'choice') detail += ' Pauses Guest Parade.';
  return { headline, detail, cashAfter, refund, foundationBonus: foundation.bonus, endsFoundation: foundation.ends, paradeBonus: parade.bonus, endsParade: parade.ends };
}
export function pick(state, index, selectedSuit) {
  if (!Number.isInteger(index) || index < 0 || index >= state.offer.length) return false;
  let offer = state.offer[index];
  if (!canBuy(state, offer)) return false;
  if (offer.type === 'choice') {
    if (!choiceSuits(state).includes(selectedSuit)) return false;
    offer = { ...offer, suit: selectedSuit };
  }
  const foundation = foundationEffect(state, offer), parade = paradeEffect(state, offer);
  // The purchase creating Attunement does not consume its first shop.
  if (state.attunement && --state.attunement.remaining === 0) state.attunement = null;
  const config = BALANCE[offer.family][offer.type];
  const before = chain(state);
  const entry = { ...offer, cardId: offer.id, id: state.history.length, links: 0 };
  state.cash -= offer.price; state.spent += offer.price;
  const affected = [], addedIds = [];
  const emit = (suit, count) => {
    const links = Array.from({ length: count }, () => ({ id: state.nextLinkId++, suit, source: entry.id }));
    addedIds.push(...links.map(link => link.id));
    state.links.push(...links);
  };
  let message = '';
  if (offer.family === 'base') {
    let value;
    if (offer.type === 'mystery') {
      entry.result = weightedPick(mysteryOutcomes(state), random(state, 'prizeRng')).links;
      value = entry.result + baseBonus(state, offer);
      message = `Rolled ${entry.result}${baseBonus(state, offer) ? ` + ${baseBonus(state, offer)} from upgrades` : ''}.`;
    } else if (offer.type !== 'mosaic') value = config.links + baseBonus(state, offer);
    if (offer.type === 'mosaic') {
      for (const suit of offer.sequence) emit(suit, 1);
      message = `Appended ${sequenceText(offer)}.`;
    } else emit(offer.suit, value);
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
      message = `${targets.length} ${suitInfo(offer.suit).name} segment(s) × ${config.linksPerSegment} = ${count} appended links.`;
    } else {
      const run = targets[0], amount = overgrowLinks(state);
      emit(run.suit, amount);
      message = `Longest segment: ${suitInfo(run.suit).name} ${run.length}. Appended ${amount} ${suitInfo(run.suit).name} links at the end.`;
    }
  } else if (offer.family === 'reactor') {
    state.upgrades[upgradeKey(offer)] = offer.level;
    message = `${offer.name} installed. ${preview(state, offer).detail}`;
  } else if (offer.family === 'strategy') {
    if (offer.type === 'foundation') {
      state.foundation = { suit: null, bonus: 0 };
      message = 'Foundation ready. Next suited purchase starts at +1.';
    } else if (offer.type === 'parade') {
      state.parade = { suit: null, bonus: 0 };
      message = 'Guest Parade ready. Change guest type to grow the bonus.';
    } else {
      state.attunement = { suit: offer.suit, remaining: config.shops };
      message = `${suitInfo(offer.suit).name} Attunement: ${config.shops} shops locked.`;
    }
  } else if (offer.type === 'vault') {
    const suit = vaultSuit(state);
    emit(suit, Math.floor(state.cash / config.cashPerLink));
    message = `${suitInfo(suit).name} links extend the tail suit.`;
  } else { state.rebateRemaining = config.purchases; message = `Next ${config.purchases} base purchases each refund up to $${config.refund}.`; }
  if (foundation.ends) {
    state.foundation = null;
    message += ' Foundation ended.';
  } else if (foundation.bonus) {
    emit(offer.suit, foundation.bonus);
    state.foundation = { suit: offer.suit, bonus: foundation.bonus };
    entry.foundationBonus = foundation.bonus;
    message += ` Foundation +${foundation.bonus} ${suitInfo(offer.suit).name}.`;
  }
  if (parade.ends) {
    state.parade = null;
    message += ' Guest Parade ended.';
  } else if (parade.bonus) {
    const types = BALANCE.suits.filter(s => s.id !== parade.suit);
    const bonusSuit = types[Math.floor(random(state, 'paradeRng') * types.length)].id;
    emit(bonusSuit, parade.bonus);
    state.parade = { suit: parade.suit, bonus: parade.bonus };
    entry.paradeBonus = parade.bonus;
    entry.paradeSuit = bonusSuit;
    message += ` Guest Parade +${parade.bonus} ${suitInfo(bonusSuit).name} rooms.`;
  }
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
// The free finishing card is separate from purchases: it cannot spend money,
// advance the deck, or trigger upgrades and streaks while the roof is landing.
export function beginRoof(state) {
  if (state.phase !== 'roof-ready') return false;
  state.offer = [];
  state.phase = 'roofing';
  return true;
}
export function finishRoof(state) {
  if (state.phase !== 'roofing') return false;
  state.phase = 'complete';
  return true;
}
