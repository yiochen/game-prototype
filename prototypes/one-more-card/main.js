import './style.css';
import { BALANCE, createGame, chain, finished, segments, vaultSuit, suitInfo, longestSegment, mysteryOutcomes, outcomePercent, mysteryOddsText, preview, pick, advanceDeal, choiceSuits, sequenceText } from './engine.js';
const $ = id => document.getElementById(id);
const el = (tag, className = '', text = '') => { const node = document.createElement(tag); node.className = className; node.textContent = text; return node; };
const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const makeSeed = () => Math.random().toString(36).slice(2, 9);
let state = createGame(new URL(location.href).searchParams.get('seed') || makeSeed());
let timer, previous = null, flashing = [], choosingIndex = null;
let collectionMode = 'chain', collectionPage = 0;
const pageSize = () => collectionMode === 'engine' && innerHeight <= 560 && innerWidth <= 619 ? 1 : innerHeight < 700 ? 3 : 6;
function paginate(nodes, page, size) {
  const pages = Math.max(1, Math.ceil(nodes.length / size));
  page = Math.min(Math.max(0, page), pages - 1);
  nodes.forEach((node, i) => { node.hidden = i < page * size || i >= (page + 1) * size; });
  return { page, pages };
}
function renderCollectionPages() {
  const engine = collectionMode === 'engine';
  $('hand').hidden = engine; $('installed').hidden = !engine;
  $('show-chain').setAttribute('aria-selected', String(!engine)); $('show-engine').setAttribute('aria-selected', String(engine));
  $('collection-pager').hidden = !engine;
  $('segment-summary').hidden = engine;
  if (!engine) { fitSequence(); return; }
  const { page, pages } = paginate([...$('installed').children], collectionPage, pageSize());
  collectionPage = page;
  $('collection-page').textContent = `${page + 1} / ${pages}`;
  $('collection-prev').disabled = page === 0; $('collection-next').disabled = page === pages - 1;
}
function rememberSeed() {
  const url = new URL(location.href); url.searchParams.set('seed', state.seed); history.replaceState(null, '', url);
}
function suitMark(suit) { return suit ? `${suitInfo(suit).symbol} ${suitInfo(suit).name}` : ''; }
function fitSequence() {
  const hand = $('hand');
  if (hand.hidden) return;
  const links = [...hand.querySelectorAll('.sequence-link')];
  if (!links.length) return;
  const width = hand.clientWidth - 12, height = hand.clientHeight - 12;
  let size = 28, gap = 3;
  while (size > 1 && Math.floor(width / (size + gap)) * Math.floor(height / (size + gap)) < links.length) { size--; gap = size < 12 ? 1 : 3; }
  const columns = Math.max(1, Math.floor(width / (size + gap)));
  hand.style.setProperty('--link-size', `${size}px`);
  hand.style.setProperty('--link-gap', `${gap}px`);
  hand.style.setProperty('--columns', columns);
  links.forEach((link, i) => link.classList.toggle('row-end', i % columns === columns - 1 || i === links.length - 1));
}
function renderChain(view) {
  const hand = $('hand'); hand.replaceChildren();
  const runs = segments(view);
  $('segment-summary').replaceChildren(...BALANCE.suits.map(suit => {
    const count = runs.filter(run => run.suit === suit.id).length;
    const label = el('span', '', `${suit.symbol} ${count} ${count === 1 ? 'segment' : 'segments'}`);
    label.style.color = suit.color; return label;
  }));
  if (!view.links.length) { hand.append(el('p', 'empty', 'Build a sequence. Switch suits to create new segments.')); return; }
  let runIndex = 0;
  for (const [index, link] of view.links.entries()) {
    while (index >= runs[runIndex].end) runIndex++;
    const suit = suitInfo(link.suit);
    const node = el('span', `link sequence-link${flashing.includes(link.id) ? ' activating' : ''}`, suit.symbol);
    node.style.setProperty('--suit', suit.color);
    node.dataset.linkId = link.id; node.dataset.suit = link.suit; node.dataset.segmentId = runs[runIndex].id;
    node.title = `Link ${index + 1} · ${suit.name} · segment ${runIndex + 1} (${runs[runIndex].length} links)`;
    node.setAttribute('role', 'img'); node.setAttribute('aria-label', node.title);
    hand.append(node);
  }
}
function renderInstalled(view) {
  const nodes = Object.entries(view.upgrades).map(([key, level]) => {
    const [type, suit] = key.split(':');
    const config = BALANCE.reactor[type];
    const value = config.values?.[level - 1];
    const outcomes = type === 'stabilizer' ? mysteryOutcomes(view) : null;
    return el('span', 'upgrade-chip', `${suit ? suitMark(suit) + ' ' : ''}${config.name} Lv${level} · ${type === 'stabilizer' ? `${outcomes.at(-1).links} links: ${outcomePercent(outcomes.at(-1), outcomes)}%` : `+${value}`}`);
  });
  if (view.rebateRemaining) nodes.push(el('span', 'upgrade-chip wealth', `Rebate · $${BALANCE.wealth.rebate.refund} × ${view.rebateRemaining} left`));
  const active = [];
  if (view.foundation) active.push(`Foundation ${view.foundation.suit ? suitMark(view.foundation.suit) : 'ready'} · next +${view.foundation.bonus + BALANCE.strategy.foundation.bonusStep}`);
  if (view.attunement) active.push(`${suitMark(view.attunement.suit)} Attunement · ${view.attunement.remaining} ${view.attunement.remaining === 1 ? 'shop' : 'shops'} left`);
  for (const text of active) nodes.push(el('span', 'upgrade-chip strategy', text));
  $('active-effects').textContent = active.join(' / ');
  $('active-effects').hidden = !active.length;
  $('installed').replaceChildren(...nodes);
  $('show-engine').textContent = `Engine${nodes.length ? ` · ${nodes.length}` : ''}`;
  if (!nodes.length) $('installed').append(el('span', 'muted', 'No installed upgrades yet.'));
}
function shortDetail(offer, effect) {
  const c = BALANCE[offer.family][offer.type];
  if (offer.type === 'choice') return state.attunement ? `${suitInfo(state.attunement.suit).name} only during Attunement.` : 'Choose Sun, Moon or Wave.';
  if (offer.sequence) return `${offer.sequence.length} links, in order.`;
  if (offer.family === 'strategy') return offer.type === 'foundation' ? 'Keep buying one suit.' : `Next ${c.shops} shops: ${suitInfo(offer.suit).name} only.`;
  if (offer.family === 'base') return offer.type === 'mystery' ? `Odds ${mysteryOutcomes(state).map(o => outcomePercent(o, mysteryOutcomes(state))).join('/')}%.` : 'Append links of this suit.';
  if (offer.family === 'reactor') return offer.type === 'stabilizer' ? `Chance of ${mysteryOutcomes(state, offer.level).at(-1).links} on future Mysteries.` : `Future ${offer.suit ? suitInfo(offer.suit).name : 'Fixed'} bases +${c.values[offer.level - 1]}.`;
  if (offer.type === 'recall') return `Append ${c.linksPerSegment} per ${suitInfo(offer.suit).name} segment.`;
  if (offer.type === 'overgrow') { const run = longestSegment(state); return `Longest: ${suitInfo(run.suit).name} ${run.length}. Append ${effect.headline.slice(1)} at end.`; }
  return offer.type === 'vault' ? `${suitInfo(vaultSuit(state)).name} links: 1 / $${c.cashPerLink} left.` : `Refunds on next ${c.purchases} base buys.`;
}
function render() {
  const view = previous ?? state;
  const resolving = state.phase === 'resolving';
  const done = finished(state);
  $('score').textContent = chain(view);
  $('cash').textContent = `$${state.cash}`;
  $('score-label').textContent = done ? 'CHAIN COMPLETE' : 'CHAIN LENGTH';
  $('spent').textContent = `$${state.spent} spent · $${state.refunded} refunded`;
  $('formula').textContent = done ? 'Every link saved' : 'Build, improve, reuse.';
  $('card-count').textContent = `${segments(view).length} segments · ${view.history.length} buys`;
  renderChain(view); renderInstalled(view); renderCollectionPages();
  $('status').textContent = resolving ? state.history.at(-1).type === 'mystery' ? 'Rolling your Mystery…' : 'Applying your purchase…' : done ? 'Run complete. Replay this seed or try a fresh shop.' : 'Buy one; the other offers are replaced.';
  $('reveal').hidden = resolving || !state.lastEffect;
  $('status').hidden = !resolving && !!state.lastEffect;
  $('reveal').title = state.lastEffect?.message ?? '';
  $('reveal').textContent = state.lastEffect ? `+${state.lastEffect.added} links${state.lastEffect.message ? ` · ${state.lastEffect.message}` : ''}` : '';
  $('finish-reaction').hidden = !resolving;
  $('deal-count').textContent = done ? '' : `Offer ${state.deals}`;
  $('deal-heading').textContent = done ? 'Run complete' : 'Buy one';
  $('offer').hidden = done || resolving;
  $('offer').dataset.stage = resolving ? 'resolving' : 'ready';
  $('offer').replaceChildren(...state.offer.map((offer, index) => {
    const effect = preview(state, offer);
    const button = el('button', `offer-card ${offer.family}`);
    button.title = effect.detail;
    button.dataset.offerIndex = index; button.dataset.cardId = offer.id; button.dataset.family = offer.family; button.dataset.price = offer.price;
    button.disabled = offer.price > state.cash;
    button.setAttribute('aria-label', `Buy ${offer.name} for $${offer.price}. ${effect.headline}. ${effect.detail}${offer.price > state.cash ? ' Cannot afford.' : ''}`);
    const top = el('div', 'card-top'); top.append(el('span', 'family', offer.family), el('strong', 'price', `$${offer.price}`));
    button.append(top, el('span', 'card-name', `${offer.suit ? suitInfo(offer.suit).symbol + ' ' : ''}${offer.name}`));
    if (!offer.sequence) button.append(el('strong', 'effect', offer.type === 'mystery' ? effect.headline.replaceAll(' / ', '/') : effect.headline));
    if (offer.sequence) {
      const pattern = el('span', 'effect mosaic-sequence'); pattern.setAttribute('aria-label', sequenceText(offer));
      offer.sequence.forEach((suit, i) => {
        if (i) pattern.append(el('span', 'sequence-arrow', '›'));
        const symbol = el('span', 'mosaic-suit', suitInfo(suit).symbol); symbol.title = suitInfo(suit).name; pattern.append(symbol);
      });
      button.append(pattern);
    }
    button.append(el('span', 'effect-detail', shortDetail(offer, effect)));
    if (effect.foundationBonus || effect.endsFoundation) button.append(el('span', 'foundation-note', effect.endsFoundation ? 'Ends Foundation' : `Foundation +${effect.foundationBonus}`));
    button.append(el('span', 'card-footer', offer.price > state.cash ? `Need $${offer.price - state.cash} more` : `$${effect.cashAfter} left${effect.refund ? ` · $${effect.refund} refund` : ''}`));
    button.addEventListener('click', () => selectOffer(index));
    return button;
  }));
  $('finished').hidden = !done;
  $('finished').textContent = `${chain(state)} links · $${state.cash} left`;
  $('seed').textContent = `Seed: ${state.seed}`;
}
function selectOffer(index) {
  const offer = state.offer[index];
  if (state.phase !== 'picking' || !offer || offer.price > state.cash) return;
  if (offer.type === 'choice') {
    choosingIndex = index;
    $('choice-description').textContent = `Choose a suit for ${offer.name} · $${offer.price}. Pay when you choose.`;
    $('suit-choices').replaceChildren(...choiceSuits(state).map(suit => {
      const effect = preview(state, offer, suit);
      const button = el('button', 'suit-choice', `${suitMark(suit)} · ${effect.headline} links${effect.foundationBonus ? ` · Foundation +${effect.foundationBonus}` : ''}${effect.endsFoundation ? ' · Ends Foundation' : ''}`);
      button.dataset.suit = suit; button.title = effect.detail;
      button.addEventListener('click', () => {
        const selected = choosingIndex;
        $('choice-dialog').close();
        purchase(selected, suit);
      });
      return button;
    }));
    $('choice-dialog').showModal();
    return;
  }
  purchase(index);
}
function purchase(index, selectedSuit) {
  const snapshot = structuredClone(state);
  if (!pick(state, index, selectedSuit)) return;
  clearTimeout(timer);
  flashing = [];
  previous = snapshot;
  if (reducedMotion()) { finishReveal(); return; }
  render();
  timer = setTimeout(finishReveal, state.history.at(-1).type === 'mystery' ? 650 : 280);
}
function finishReveal() {
  if (state.phase !== 'resolving') return;
  clearTimeout(timer); previous = null;
  flashing = [...state.lastEffect.addedIds, ...state.lastEffect.affected];
  advanceDeal(state); render();
  if (!reducedMotion()) $('score').animate([{ transform: 'scale(1.09)' }, { transform: 'scale(1)' }], { duration: 220 });
  timer = setTimeout(() => { flashing = []; document.querySelectorAll('.activating').forEach(n => n.classList.remove('activating')); }, 500);
}
function restart(seed) { $('choice-dialog').close(); choosingIndex = null; clearTimeout(timer); previous = null; flashing = []; collectionMode = 'chain'; collectionPage = 0; state = createGame(seed); rememberSeed(); render(); }
$('choice-dialog').addEventListener('close', () => { choosingIndex = null; });
$('rules-open').addEventListener('click', () => $('rules-dialog').showModal());
for (const mode of ['chain', 'engine']) $('show-' + mode).addEventListener('click', () => { collectionMode = mode; collectionPage = 0; render(); });
for (const [id, delta] of [['collection-prev', -1], ['collection-next', 1]]) $(id).addEventListener('click', () => { collectionPage += delta; renderCollectionPages(); });
window.addEventListener('resize', () => { renderCollectionPages(); });
$('finish-reaction').addEventListener('click', finishReveal);
$('restart').addEventListener('click', () => restart(makeSeed()));
$('replay').addEventListener('click', () => restart(state.seed));
document.addEventListener('keydown', event => {
  if ($('rules-dialog').open || $('choice-dialog').open) return;
  if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  if (/^[123]$/.test(event.key)) { event.preventDefault(); selectOffer(Number(event.key) - 1); }
});
// The visible balance reference is generated from the same source as gameplay.
function renderBalance() {
  const tbody = $('balance-body');
  const row = (name, cost, effect) => { const tr = el('tr'); for (const text of [name, cost, effect]) tr.append(el('td', '', text)); tbody.append(tr); };
  for (const [type, c] of Object.entries(BALANCE.base)) row(c.name + (type === 'choice' ? ' · choose suit' : type === 'mosaic' ? ' · varied sequences' : ' · each suit'), `$${c.price}`, type === 'mystery' ? c.outcomes.map(o => `${o.links} links (${outcomePercent(o, c.outcomes)}%)`).join(', ') : type === 'mosaic' ? '3 links: all different, sandwich, or pair first/last. Exact printed order; no upgrade bonuses.' : `${c.links} fixed link(s)`);
  for (const [type, c] of Object.entries(BALANCE.growth)) row(c.name, `$${c.price}`, type === 'recall' ? `Append ${c.linksPerSegment} link(s) per matching segment, regardless of length` : `Append the longest segment's suit at the end: +1 per ${c.linksPerBonus} links (min ${c.minimum}, cap ${c.maximum})`);
  for (const [type, c] of Object.entries(BALANCE.reactor)) row(`${c.name}${type === 'suit' ? ' · each suit' : ''} Lv1/2/3`, c.prices.map(p => `$${p}`).join(' / '), type === 'stabilizer' ? c.outcomesByLevel.map((_, i) => `Lv${i + 1}: ${mysteryOddsText(state, i + 1)}`).join('; ') : `+${c.values.join(' / +')} future links`);
  row('Foundation', `$${BALANCE.strategy.foundation.price}`, `Start at +${BALANCE.strategy.foundation.bonusStep}, then increase by ${BALANCE.strategy.foundation.bonusStep} for each matching suited purchase. Switching suits or Mosaic ends it. Suitless purchases pause it.`);
  row('Attunement · each suit', `$${BALANCE.strategy.attunement.price}`, `Next ${BALANCE.strategy.attunement.shops} shops: 100% of suited offers match. Choice is locked; Mosaic pauses. Cannot refresh while active.`);
  const v = BALANCE.wealth.vault, r = BALANCE.wealth.rebate;
  row(v.name, `$${v.price}`, `1 link per $${v.cashPerLink} remaining after payment`);
  row(r.name, `$${r.price}`, `$${r.refund} refund on next ${r.purchases} base purchases`);
  $('weights').textContent = `Family weights: ${Object.entries(BALANCE.families).map(([k, v]) => `${k} ${v}`).join(' · ')}. Within Base: ${Object.values(BALANCE.base).map(c => `${c.name} ${c.weight}`).join(' · ')}. Within Growth: ${Object.values(BALANCE.growth).map(c => `${c.name} ${c.weight}`).join(' · ')}. Within Reactor: ${Object.values(BALANCE.reactor).map(c => `${c.name} ${c.weight}`).join(' · ')}. Within Wealth: ${Object.values(BALANCE.wealth).map(c => `${c.name} ${c.weight}`).join(' · ')}. Within Strategy: ${Object.values(BALANCE.strategy).map(c => `${c.name} ${c.weight}`).join(' · ')}. Eligible suits are equally likely unless Attunement is active.`;
  $('budget-rule').textContent = `Start with $${BALANCE.startingCash}. Choose one of ${BALANCE.offerSize} offers. Only links count. Foundation can add bonus links to suited power purchases.`;
}
rememberSeed(); renderBalance(); render();
new ResizeObserver(fitSequence).observe($('hand'));
