import './style.css';
import { ART, SHEETS, spriteArt } from './assets.js';
import { mountWorld } from './world.js';
import { mountScenery } from './scenery.js';
import { createCardFlight } from './card-flight.js';
import { paperAudio } from './audio.js';
import { BALANCE, createGame, segments, longestSegment, preview, pick, advanceDeal, choiceSuits, suitInfo, mysteryOddsText, mysteryOutcomes, outcomePercent, finished } from './engine.js';

const $ = id => document.getElementById(id);
const node = (tag, className = '', text = '') => { const n = document.createElement(tag); n.className = className; n.textContent = text; return n; };
const img = (key, className = '', alt = '') => {
  const { sheet, frame } = spriteArt(key), { columns, rows } = SHEETS[sheet];
  const holder = node('span', `sprite-art ${className}`), image = node('img');
  holder.dataset.sheet = sheet; holder.dataset.frame = frame;
  holder.style.setProperty('--cols', columns); holder.style.setProperty('--rows', rows);
  holder.style.setProperty('--col', frame % columns); holder.style.setProperty('--row', Math.floor(frame / columns));
  image.src = ART[sheet]; image.alt = alt; holder.append(image); return holder;
};
const randomSeed = () => Math.random().toString(36).slice(2, 9);
$('coin-art').append(img('coin'));
document.querySelector('.dock-label').src = ART['dock-paper'];
document.documentElement.style.setProperty('--tray-art', `url("${ART['cardboard-tray']}")`);
const human = text => text.replaceAll('Foundation', 'Neighborhood Streak').replaceAll('Attunement', 'Type Lock').replaceAll('Reactor', 'Room Pattern').replaceAll('Assembler', 'Master Fold').replaceAll('Mystery', 'Surprise Parcel').replaceAll('Stabilizer', 'Lucky Bell').replaceAll('Recall', 'Balloon Call').replace(/\bsuit\b/g, 'room type').replace(/\bsuited\b/g, 'typed').replace(/\blinks?\b/g, m => m === 'links' ? 'floors' : 'floor').replace(/\bsegments?\b/g, m => m === 'segments' ? 'neighborhoods' : 'neighborhood');
let state = createGame(new URL(location.href).searchParams.get('seed') || randomSeed());
let scene, resolvingBefore = null, pendingPurchase = null, epoch = 0, choiceIndex = null, menuReturn = null;
const flight = createCardFlight();
const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reduced = motionQuery.matches;
const scenery = mountScenery(document.querySelector('.sky-backdrop'), !reduced);
const world = mountWorld($('world'));
const audio = paperAudio();
let loading = true;

function setSeed() { const url = new URL(location.href); url.searchParams.set('seed', state.seed); history.replaceState(null, '', url); }
function title(card) { return card.type === 'single' ? `${suitInfo(card.suit).name} Room` : card.type === 'triple' ? `${suitInfo(card.suit).name} Pack` : card.name; }
function presentation(card, view = state, chosen) {
  const effect = preview(view, card, chosen), c = BALANCE[card.family][card.type];
  let headline = effect.headline, detail;
  if (card.type === 'choice') detail = view.attunement ? `${suitInfo(view.attunement.suit).name} only during Type Lock.` : 'Choose your guest type.';
  else if (card.sequence) detail = '3 rooms, in this order.';
  else if (card.type === 'mystery') { headline = effect.headline.replaceAll(' / ', '/'); detail = `Odds ${mysteryOutcomes(view).map(o => outcomePercent(o, mysteryOutcomes(view))).join('/')}%.`; }
  else if (card.family === 'base') detail = 'Fresh rooms, ready to unfold.';
  else if (card.type === 'recall') detail = `One room per ${suitInfo(card.suit).name} balloon.`;
  else if (card.type === 'overgrow') { const source = longestSegment(view); detail = `Copy ${suitInfo(source.suit).name} ×${source.length}. Add at the top.`; }
  else if (card.type === 'foundation') detail = 'Same type. A growing bonus.';
  else if (card.type === 'attunement') detail = `${c.shops} shops. Only ${suitInfo(card.suit).name} types.`;
  else if (card.type === 'rebate') { headline = `${c.refund} × ${c.purchases}`; detail = `Coins back on next ${c.purchases} room buys.`; }
  else if (card.type === 'vault') detail = `A room per ${c.cashPerLink} coins left.`;
  else if (card.type === 'stabilizer') detail = 'Better odds of 8 rooms.';
  else detail = card.type === 'suit' ? `More ${suitInfo(card.suit).name} rooms on future builds.` : 'More rooms in future fixed packs.';
  return { ...effect, headline, detail, fullDetail: human(effect.detail) };
}
function art(card) {
  const holder = node('div', `card-art art-${card.type}`); holder.setAttribute('aria-hidden', 'true'); holder.dataset.illustration = card.type + (card.suit ? '-' + card.suit : card.sequence ? '-' + card.sequence.join('-') : '');
  if (card.sequence) card.sequence.forEach((type, i) => { if (i) holder.append(node('span', 'art-arrow', '›')); holder.append(img(`resident-${type}-0`, 'mosaic-guest')); });
  else if (card.type === 'single') holder.append(img(`resident-${card.suit}-0`, 'art-room'));
  else if (card.type === 'triple') for (let i = 0; i < 3; i++) holder.append(img(`resident-${card.suit}-0`, `pack-room pack-${i}`));
  else if (card.type === 'recall') holder.append(img(`balloon-${card.suit}`, 'call-balloon'), img(`resident-${card.suit}-0`, 'call-room'));
  else if (card.type === 'suit') holder.append(img(`pattern-${card.suit}`));
  else if (card.type === 'attunement') holder.append(img(`lock-${card.suit}`));
  else holder.append(img(`power-${card.type}`));
  return holder;
}
function showEffect(card, view) {
  const p = presentation(card, view);
  scene?.inspect(null); $('effect-title').textContent = title(card); $('effect-art').replaceChildren(art(card));
  $('effect-value').textContent = p.headline + (card.family === 'base' || card.family === 'growth' || card.type === 'vault' ? ' floors' : '');
  $('effect-detail').textContent = p.fullDetail;
  $('effect-extra').textContent = card.type === 'suit' ? 'Applies to future matching room cards, including Surprise Parcel. Mosaic keeps its exact pattern.' : card.type === 'assembler' ? 'Applies to One Room, Prefab Pack and Room Choice. Mosaic and Surprise Parcel keep their own rules.' : card.type === 'rebate' ? p.detail : card.sequence ? 'Read left to right. These rooms are added from bottom to top.' : '';
  $('effect-extra').hidden = !$('effect-extra').textContent;
  $('effect-cost').replaceChildren(img('coin'), node('span', '', `${card.price} coins${card.price > state.cash ? ' · Not enough coins' : ''}`));
  $('effect-dialog').showModal();
}
function renderDock(view) {
  const runs = segments(view);
  $('dock').replaceChildren(...BALANCE.suits.map(type => {
    const count = runs.filter(r => r.suit === type.id).length;
    const dock = node('div', `dock-chip ${type.id}`); dock.dataset.suit = type.id;
    dock.setAttribute('aria-label', `${type.name}: ${count} neighborhood balloons`);
    dock.append(img(`balloon-${type.id}`), node('span', 'dock-name', type.name), node('strong', 'dock-count', count)); return dock;
  }));
}
function renderWorkshop(view) {
  const list = [];
  for (const [key, level] of Object.entries(view.upgrades)) {
    const [type, suit] = key.split(':'), config = BALANCE.reactor[type];
    const line = node('div', 'workshop-item'); line.append(img(suit ? `resident-${suit}-0` : 'charm'));
    const copy = node('div'); copy.append(node('strong', '', `${suit ? suitInfo(suit).name + ' ' : ''}${config.name} · level ${level}`));
    copy.append(node('p', '', type === 'stabilizer' ? `Surprise odds: ${mysteryOddsText(view)}` : `+${config.values[level - 1]} on matching future room cards.`)); line.append(copy); list.push(line);
  }
  if (view.rebateRemaining) list.push(node('p', 'workshop-item', `Coupon Book · ${view.rebateRemaining} refunds of ${BALANCE.wealth.rebate.refund} coins left`));
  const active = [];
  if (view.foundation) active.push(`Streak ${view.foundation.suit ? suitInfo(view.foundation.suit).name : 'ready'} · next +${view.foundation.bonus + BALANCE.strategy.foundation.bonusStep}`);
  if (view.attunement) active.push(`${suitInfo(view.attunement.suit).name} lock · ${view.attunement.remaining} ${view.attunement.remaining === 1 ? 'shop' : 'shops'}`);
  for (const text of active) list.push(node('p', 'workshop-item', text));
  $('installed').replaceChildren(...(list.length ? list : [node('p', 'empty-workshop', 'Your workshop is waiting. Collect tools and techniques to make every coin go further.')]));
  $('upgrade-count').textContent = list.length;
  $('strategy-status').replaceChildren(...active.map(text => node('span', 'strategy-chip', text))); $('strategy-status').hidden = !active.length;
}
function renderOffers(view) {
  const offers = state.phase === 'resolving' ? resolvingBefore.offer : state.offer;
  $('offers').replaceChildren(...offers.map((card, i) => {
    const p = presentation(card, view), slot = node('div', 'offer-slot'), button = node('button', `offer-card ${card.family} ${card.suit ?? 'mixed'}`);
    if (pendingPurchase?.index === i || (state.phase === 'resolving' && state.history.at(-1)?.cardId === card.id)) slot.classList.add('card-used');
    button.dataset.offerIndex = i; button.dataset.cardId = card.id; button.dataset.type = card.type;
    button.disabled = loading || !!pendingPurchase || state.phase !== 'picking' || card.price > state.cash;
    button.setAttribute('aria-label', `Buy ${title(card)} for ${card.price} coins. ${p.headline}. ${p.fullDetail}`);
    const top = node('div', 'card-top'), price = node('span', 'price'); price.append(img('coin'), node('span', '', card.price)); top.append(price);
    button.append(top, art(card), node('strong', 'card-title', title(card)));
    const value = node('div', 'card-value'); value.append(node('strong', 'card-effect', p.headline));
    if (card.family === 'base' || card.family === 'growth' || card.type === 'vault') value.append(node('span', '', 'floors'));
    button.append(value);
    let pointerStart = null, canceled = false;
    button.addEventListener('pointerdown', event => { if (button.disabled) return; pointerStart = { x: event.clientX, y: event.clientY }; canceled = false; scene?.inspect(card); $('preview').textContent = p.fullDetail; });
    button.addEventListener('pointerup', event => { canceled = pointerStart && Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y) > 10; });
    button.addEventListener('pointercancel', () => { canceled = true; scene?.inspect(null); });
    button.addEventListener('mouseenter', () => { if (!button.disabled) { scene?.inspect(card); $('preview').textContent = p.fullDetail; } });
    button.addEventListener('focus', () => { if (!button.disabled) { scene?.inspect(card); $('preview').textContent = p.fullDetail; } });
    for (const event of ['mouseleave', 'blur']) button.addEventListener(event, () => { scene?.inspect(null); $('preview').textContent = ''; });
    button.addEventListener('click', () => { if (!canceled) select(i); canceled = false; });
    const help = node('button', 'card-help', '?'); help.dataset.offerHelp = i;
    help.setAttribute('aria-label', `About ${title(card)}`); help.setAttribute('aria-haspopup', 'dialog'); help.setAttribute('aria-controls', 'effect-dialog');
    help.disabled = loading || !!pendingPurchase || state.phase !== 'picking';
    help.addEventListener('click', () => showEffect(card, view));
    slot.append(button, help); return slot;
  }));
}
function render() {
  const view = resolvingBefore ?? state, done = finished(state);
  $('height').textContent = view.links.length; $('coins').textContent = state.cash;
  renderDock(view); renderWorkshop(view); renderOffers(view);
  $('reveal-now').hidden = state.phase !== 'resolving' && !pendingPurchase;
  $('offers').hidden = done; $('tray').hidden = done; $('ending').hidden = !done;
  $('overview').disabled = !view.links.length; $('seed-label').textContent = `Guestbook ${state.seed}`;
  $('world').dataset.state = pendingPurchase ? 'launching' : state.phase; document.querySelector('.hotel-app').classList.toggle('complete', done);
  $('floor-record').replaceChildren(...view.links.map((floor, i) => { const li = node('li', '', `Floor ${i + 1}: ${suitInfo(floor.suit).name}`); li.dataset.floorId = floor.id; li.dataset.type = floor.suit; return li; }));
  if (done) {
    $('ending-title').textContent = `${state.links.length} floors`;
    $('ending-detail').textContent = `${segments(state).length} neighborhoods · ${state.cash} coins saved`;
    $('status').textContent = 'Your guests have arrived. Welcome home.';
  } else if (state.phase === 'resolving') $('status').textContent = state.history.at(-1).type === 'mystery' ? 'Unwrapping your surprise…' : 'Your delivery is unfolding…';
  $('motion-toggle').setAttribute('aria-pressed', String(reduced)); document.documentElement.classList.toggle('reduced-motion', reduced);
}
function select(index) {
  if (loading || pendingPurchase || state.phase !== 'picking' || document.querySelector('dialog[open]')) return;
  const card = state.offer[index]; if (!card || card.price > state.cash) return;
  if (card.type !== 'choice') { commit(index); return; }
  choiceIndex = index;
  $('room-choices').replaceChildren(...choiceSuits(state).map(type => {
    const p = presentation(card, state, type), button = node('button', `room-choice ${type}`); button.dataset.suit = type;
    const copy = node('span'); copy.append(node('strong', '', `${suitInfo(type).name} room`), node('small', '', `${p.headline} floors · ${card.price} coins${p.endsFoundation ? ' · Ends your streak' : p.foundationBonus ? ` · Streak +${p.foundationBonus}` : ''}`));
    button.append(img(`resident-${type}-1`), copy, node('span', '', '→'));
    button.addEventListener('click', () => { const selected = choiceIndex; $('choice-dialog').close(); commit(selected, type); }); return button;
  }));
  $('choice-dialog').showModal();
}
function commit(index, selectedType) {
  if (pendingPurchase || state.phase !== 'picking') return;
  const token = ++epoch;
  const apply = () => { if (token !== epoch) return; pendingPurchase = null; applyPurchase(index, selectedType, token); };
  if (reduced) { apply(); return; }
  pendingPurchase = { index, selectedType };
  const source = document.querySelector(`#offers [data-offer-index="${index}"]`);
  scene?.inspect(null);
  flight.play(source, { onBurst: () => { audio.fold(); apply(); } });
  render(); $('status').textContent = 'Opening your card…';
  // The original node was cloned for flight before rendering disabled offers.
  document.querySelector(`#offers [data-offer-index="${index}"]`)?.classList.add('card-flight-source');
}
function applyPurchase(index, selectedType, token) {
  const before = structuredClone(state);
  if (!pick(state, index, selectedType)) return;
  resolvingBefore = before; render();
  const complete = () => {
    if (token !== epoch || state.phase !== 'resolving') return;
    const entry = state.history.at(-1);
    advanceDeal(state); resolvingBefore = null;
    $('status').textContent = entry.links ? `+${entry.links} ${entry.links === 1 ? 'floor' : 'floors'}. ${entry.type === 'mosaic' ? 'A new patchwork of neighbors.' : 'Make room for possibility.'}` : `${entry.name} is ready for you.`;
    render(); scene.setState(state); $('overview').textContent = scene.whole ? 'Back to the top' : 'Whole hotel'; $('preview').textContent = '';
    if (!reduced) { $('height').animate([{ transform: 'translateY(-2px)' }, { transform: 'translateY(0)' }], { duration: 180 }); }
  };
  let lastFloor = before.links.length;
  if (reduced) { audio.fold(); complete(); }
  else scene.animate(before, structuredClone(state), { onFrame: count => { $('height').textContent = count; if (count > lastFloor) { audio.fold(); lastFloor = count; } }, onComplete: complete });
}
function restart(seed) {
  ++epoch; flight.cancel(); pendingPurchase = null; menuReturn = null; for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  resolvingBefore = null; choiceIndex = null; state = createGame(seed); setSeed();
  $('status').textContent = 'Choose one card. A new delivery follows.'; $('preview').textContent = '';
  $('overview').textContent = 'Whole hotel'; render(); scene?.reset(state);
}
function balanceTable() {
  const rows = [];
  for (const [type, c] of Object.entries(BALANCE.base)) rows.push([c.name, c.price, type === 'mosaic' ? 'Exact printed sequence: trio, sandwich, or pair at either end. No upgrade extras.' : type === 'mystery' ? c.outcomes.map(o => `${o.links} floors (${outcomePercent(o, c.outcomes)}%)`).join(' / ') : `${c.links} floor(s)${type === 'choice' ? ' of your chosen type' : ' of the printed type'}, plus applicable bonuses.`]);
  const call = BALANCE.growth.recall, copy = BALANCE.growth.overgrow;
  rows.push([call.name, call.price, `${call.linksPerSegment} matching floor per matching neighborhood.`], [copy.name, copy.price, `Largest neighborhood: 1 floor per ${copy.linksPerBonus} existing floors, rounded down. Minimum ${copy.minimum}, maximum ${copy.maximum}; earliest wins ties.`]);
  for (const [type, c] of Object.entries(BALANCE.reactor)) rows.push([c.name, c.prices.join(' / '), type === 'stabilizer' ? c.outcomesByLevel.map((_, i) => `Level ${i + 1}: ${mysteryOddsText(state, i + 1)}`).join('; ') : `+${c.values.join(' / +')} floors on future ${type === 'suit' ? 'matching room cards (excludes Mosaic)' : 'One Room, Prefab Pack and Room Choice'}. Levels replace each other.`]);
  const reserve = BALANCE.wealth.vault, coupon = BALANCE.wealth.rebate, streak = BALANCE.strategy.foundation, lock = BALANCE.strategy.attunement;
  rows.push([reserve.name, reserve.price, `1 room per ${reserve.cashPerLink} coins remaining after payment, using the top type (${suitInfo(reserve.openingSuit).name} on an empty hotel).`], [coupon.name, coupon.price, `${coupon.refund} coins back on the next ${coupon.purchases} room buys, including Mosaic. No refresh while active.`], [streak.name, streak.price, `Start at +${streak.bonusStep}; add ${streak.bonusStep} to the bonus per matching typed purchase. Typed powers count. A new type or Mosaic ends it; untyped cards pause it.`], [lock.name, lock.price, `100% matching typed offers for ${lock.shops} shops. Every purchase consumes a shop. No refresh while active.`]);
  $('balance-table').replaceChildren(...rows.map(row => { const tr = node('tr'); for (const value of row) tr.append(node('td', '', value)); return tr; }));
}
$('sound-toggle').addEventListener('click', () => { const enabled = audio.toggle(); $('sound-toggle').textContent = enabled ? 'Sound on' : 'Sound off'; $('sound-toggle').setAttribute('aria-pressed', String(enabled)); });
$('menu-open').addEventListener('click', () => { scene?.inspect(null); $('menu-dialog').showModal(); });
$('resume').addEventListener('click', () => $('menu-dialog').close());
for (const [button, dialog] of [['rules-open', 'rules-dialog'], ['workshop-open', 'workshop-dialog']]) {
  $(button).addEventListener('click', () => { menuReturn = button; $('menu-dialog').close(); $(dialog).showModal(); });
  $(dialog).addEventListener('close', () => { if (menuReturn !== button) return; menuReturn = null; $('menu-dialog').showModal(); $(button).focus(); });
}
$('menu-dialog').addEventListener('close', () => { if (!menuReturn && !document.querySelector('dialog[open]')) $('menu-open').focus(); });
$('choice-dialog').addEventListener('close', () => { choiceIndex = null; });
$('reveal-now').addEventListener('click', () => { flight.finish(); scene?.skip(); $('menu-dialog').close(); });
$('overview').addEventListener('click', () => { $('overview').textContent = scene.toggleOverview() ? 'Back to the top' : 'Whole hotel'; $('menu-dialog').close(); });
$('replay').addEventListener('click', () => restart(state.seed));
$('new-game').addEventListener('click', () => restart(randomSeed()));
function applyMotion(value) { reduced = value; scenery.setMotion(!reduced); document.documentElement.classList.toggle('reduced-motion', reduced); if (scene) scene.motion = !reduced; if (reduced) flight.finish(); if (scene) { if (reduced) { scene.skip(); scene.tower.y = 0; } scene.draw(); } $('motion-toggle').setAttribute('aria-pressed', String(reduced)); }
$('motion-toggle').addEventListener('click', () => applyMotion(!reduced)); motionQuery.addEventListener('change', e => applyMotion(e.matches));
document.addEventListener('keydown', event => { if (!event.repeat && !event.ctrlKey && !event.metaKey && !event.altKey && /^[123]$/.test(event.key) && !document.querySelector('dialog[open]')) { event.preventDefault(); select(Number(event.key) - 1); } });
setSeed(); balanceTable(); render();
world.ready.then(readyScene => { scene = readyScene; scene.motion = !reduced; loading = false; render(); scene.setState(state); $('world').dataset.ready = 'true'; });
if (import.meta.hot) import.meta.hot.dispose(() => { flight.destroy(); scenery.destroy(); world.destroy(); audio.destroy(); });
