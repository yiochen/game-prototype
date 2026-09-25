import './style.css';
import './paper-hud.css';
import './card-table.css';
import './polish.css';
import { mountLobby } from './lobby.js';
import { createGuestbook } from './guestbook-storage.js';
import { replayRun } from './score-rules.js';
import { createFeedback } from './feedback.js';
import { ART, SHEETS, spriteArt } from './assets.js';
import { mountWorld } from './world.js';
import { mountScenery } from './scenery.js';
import { createCardFlight } from './card-flight.js';
import { paperAudio } from './audio.js';
import { BALANCE, createGame, segments, longestSegment, preview, baseBonus, pick, advanceDeal, beginRoof, finishRoof, choiceSuits, suitInfo, mysteryOddsText, mysteryOutcomes, outcomePercent, finished } from './engine.js';

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

document.documentElement.style.setProperty('--tray-art', `url("${ART['cardboard-tray']}")`);
document.documentElement.style.setProperty('--card-paper', `url("${ART['card-paper']}")`);
document.documentElement.style.setProperty('--hud-tab', `url("${ART['hud-tab']}")`);
const human = text => text.replaceAll('Foundation', 'Neighborhood Streak').replaceAll('Attunement', 'Type Lock').replaceAll('Reactor', 'Room Pattern').replaceAll('Assembler', 'Master Fold').replaceAll('Mystery', 'Surprise Parcel').replaceAll('Stabilizer', 'Lucky Bell').replaceAll('Recall', 'Balloon Call').replace(/\bsuit\b/g, 'room type').replace(/\bsuited\b/g, 'typed').replace(/\blinks?\b/g, m => m === 'links' ? 'floors' : 'floor').replace(/\bsegments?\b/g, m => m === 'segments' ? 'neighborhoods' : 'neighborhood');
const guestbook = createGuestbook();
let requestedSeed = new URL(location.href).searchParams.get('seed');
if (requestedSeed && !/^[a-zA-Z0-9_-]{1,64}$/.test(requestedSeed)) requestedSeed = null;
let run = guestbook.data.active || { id: crypto.randomUUID(), seed: requestedSeed || randomSeed(), moves: [] };
let state = guestbook.data.active ? replayRun(run.seed, run.moves, false) : createGame(run.seed), completedRecord = null;
let shell, sound = guestbook.data.sound;
let scene, resolvingBefore = null, pendingPurchase = null, epoch = 0, choiceIndex = null, menuReturn = null;
const flight = createCardFlight();
const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reduced = guestbook.data.reduced ?? motionQuery.matches;
const scenery = mountScenery(document.querySelector('.sky-backdrop'), !reduced);
const world = mountWorld($('world'));
const audio = paperAudio();
let loading = true, effectIndex = null;
const feedback = createFeedback(() => reduced);
function syncCamera() {
  for (const id of ['overview', 'camera-toggle']) {
    $(id).textContent = scene?.whole ? 'Back to the top' : 'Whole hotel';
    $(id).disabled = !state.links.length || !!pendingPurchase || ['resolving', 'roofing'].includes(state.phase);
  }
  $('camera-toggle').setAttribute('aria-pressed', String(!!scene?.whole));
}
function explainCounter(title, detail) {
  $('hud-title').textContent = title; $('hud-detail').textContent = detail; $('hud-dialog').showModal();
}

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
function showEffect(card, view, index) {
  effectIndex = index;
  const p = presentation(card, view);
  scene?.inspect(null); $('effect-title').textContent = title(card); $('effect-art').replaceChildren(art(card));
  $('effect-value').textContent = p.headline + (card.family === 'base' || card.family === 'growth' || card.type === 'vault' ? ' floors' : '');
  $('effect-detail').textContent = p.fullDetail;
  $('effect-extra').textContent = card.type === 'suit' ? 'Applies to future matching room cards, including Surprise Parcel. Mosaic keeps its exact pattern.' : card.type === 'assembler' ? 'Applies to One Room, Prefab Pack and Room Choice. Mosaic and Surprise Parcel keep their own rules.' : card.type === 'rebate' ? p.detail : card.sequence ? 'Read left to right. These rooms are added from bottom to top.' : '';
  $('effect-extra').hidden = !$('effect-extra').textContent;
  $('effect-cost').replaceChildren(img('coin'), node('span', '', `${card.price} coins${card.price > state.cash ? ' · Not enough coins' : ''}`));
  $('effect-buy').textContent = card.type === 'choice' ? `Choose a room · ${card.price} coins` : `Buy card · ${card.price} coins`;
  $('effect-buy').disabled = card.price > state.cash;
  $('effect-dialog').showModal();
}
function renderDock(view) {
  const runs = segments(view);
  for (const type of BALANCE.suits) {
    const count = runs.filter(r => r.suit === type.id).length;
    let dock = $('dock').querySelector(`[data-suit="${type.id}"]`);
    if (!dock) {
      dock = node('button', `dock-chip ${type.id}`); dock.dataset.suit = type.id;
      dock.setAttribute('aria-haspopup', 'dialog');
      const multiply = node('span', 'dock-multiply', '×'); multiply.setAttribute('aria-hidden', 'true');
      dock.append(img(`balloon-${type.id}`), node('span', 'dock-name', type.name), multiply, node('strong', 'dock-count', '0'));
      dock.addEventListener('click', () => explainCounter(`${type.name} balloons`, 'Each separate neighborhood of this guest type earns one reusable balloon. Balloon Call adds one room per matching balloon, without spending them.'));
      $('dock').append(dock);
    }
    const counter = dock.querySelector('.dock-count'), changed = Number(counter.textContent) !== count;
    dock.setAttribute('aria-label', `${type.name}: ${count} neighborhood balloons`);
    counter.textContent = count;
    if (changed) feedback.pulse(counter);
  }
}
function renderWorkshop(view) {
  const list = [], badges = [];
  for (const [key, level] of Object.entries(view.upgrades)) {
    const [type, suit] = key.split(':'), config = BALANCE.reactor[type];
    const badge = node('button', 'upgrade-badge'); badge.dataset.upgrade = key;
    badge.setAttribute('aria-label', `${suit ? suitInfo(suit).name + ' ' : ''}${config.name}, level ${level}. Open workshop`);
    badge.title = badge.getAttribute('aria-label'); badge.append(img(suit ? `pattern-${suit}` : `power-${type}`), node('span', '', String(level)));
    badge.addEventListener('click', () => { menuReturn = null; $('workshop-dialog').showModal(); }); badges.push(badge);
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
  $('upgrade-rack').replaceChildren(...badges); $('upgrade-rack').hidden = !badges.length;
  $('strategy-status').replaceChildren(...active.map(text => node('span', 'strategy-chip', text))); $('strategy-status').hidden = !active.length;
}
function renderOffers(view) {
  const roof = state.phase === 'roof-ready' || state.phase === 'roofing';
  $('offers').classList.toggle('roof-offer', roof);
  if (roof) { renderRoofOffer(); return; }
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
    help.addEventListener('click', () => showEffect(card, view, i));
    // Decorative cards suggest the pile underneath, not future dealt offers.
    for (let layer = 0; layer < 3; layer++) {
      const back = node('div', 'deck-card'); back.inert = true; back.setAttribute('aria-hidden', 'true');
      back.style.setProperty('--deck-layer', layer); back.append(img('parcel', 'deck-placeholder')); slot.append(back);
    }
    slot.append(button, help); return slot;
  }));
}
function renderRoofOffer() {
  if (state.phase === 'roofing') { $('offers').replaceChildren(); return; }
  const slot = node('div', 'offer-slot'), button = node('button', 'offer-card finale mixed');
  if (pendingPurchase) slot.classList.add('card-used');
  button.id = 'roof-card'; button.dataset.offerIndex = 0; button.dataset.type = 'roof'; button.dataset.cardId = 'finale:roof';
  button.disabled = loading || !!pendingPurchase;
  button.setAttribute('aria-label', 'Place the roof for free. Finish your hotel.');
  const top = node('div', 'card-top'), price = node('span', 'price'), picture = node('div', 'card-art art-roof'), value = node('div', 'card-value');
  price.append(img('coin'), node('span', '', '0')); top.append(price); picture.setAttribute('aria-hidden', 'true'); picture.append(img('roof'));
  value.append(node('strong', 'card-effect', 'FREE'));
  button.append(top, picture, node('strong', 'card-title', 'Roof'), value);
  button.addEventListener('click', () => select(0)); slot.append(button); $('offers').replaceChildren(slot);
}
function render() {
  const view = resolvingBefore ?? state, done = finished(state);
  $('height').textContent = view.links.length; $('coins').textContent = state.cash;
  renderDock(view); renderWorkshop(view); renderOffers(view);
  $('reveal-now').hidden = !['resolving', 'roofing'].includes(state.phase) && !pendingPurchase;
  $('offers').hidden = done; $('ending').hidden = !done;
  syncCamera(); $('seed-label').textContent = `Guestbook ${state.seed}`;
  $('world').dataset.state = pendingPurchase ? 'launching' : state.phase; document.querySelector('.hotel-app').classList.toggle('complete', done);
  $('floor-record').replaceChildren(...view.links.map((floor, i) => { const li = node('li', '', `Floor ${i + 1}: ${suitInfo(floor.suit).name}`); li.dataset.floorId = floor.id; li.dataset.type = floor.suit; return li; }));
  if (done) {
    $('ending-title').textContent = `${state.links.length} floors`;
    $('ending-detail').textContent = `${segments(state).length} neighborhoods · ${state.cash} ${state.cash === 1 ? 'coin' : 'coins'} saved`;
    $('status').textContent = 'Your guests have arrived. Welcome home.';
  } else if (state.phase === 'roof-ready') $('status').textContent = 'One last touch. Choose the free roof card to finish your hotel.';
  else if (state.phase === 'roofing') $('status').textContent = 'Your roof is landing…';
  else if (state.phase === 'resolving') $('status').textContent = state.history.at(-1).type === 'mystery' ? 'Unwrapping your surprise…' : 'Your delivery is unfolding…';
  $('motion-toggle').setAttribute('aria-pressed', String(reduced)); document.documentElement.classList.toggle('reduced-motion', reduced);
}
function select(index) {
  if (document.body.dataset.screen !== 'game' || loading || pendingPurchase || document.querySelector('dialog[open]')) return;
  if (state.phase === 'roof-ready') { if (index === 0) commitRoof(); return; }
  if (state.phase !== 'picking') return;
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
function commitRoof() {
  if (pendingPurchase || state.phase !== 'roof-ready') return;
  feedback.clear();
  const token = ++epoch;
  const drop = () => {
    if (token !== epoch) return;
    pendingPurchase = null;
    if (!beginRoof(state)) return;
    render();
    scene.dropRoof(state, { onComplete: () => {
      if (token !== epoch || !finishRoof(state)) return;
      const result = guestbook.finish(run, state); completedRecord = result.record;
      $('ending-save').textContent = result.saved ? 'Saved to Your hotels. Sign the guestbook to share your stay.' : 'Device storage is unavailable. Sign the guestbook to save your score online.';
      audio.finish(); render(); scene.setState(state); syncCamera();
    } });
  };
  if (reduced) { drop(); return; }
  pendingPurchase = { index: 0, roof: true };
  flight.play($('roof-card'), { onBurst: drop });
  render(); $('status').textContent = 'Opening your roof card…';
}
function commit(index, selectedType) {
  if (pendingPurchase || state.phase !== 'picking') return;
  const token = ++epoch;
  const apply = origin => { if (token !== epoch) return; pendingPurchase = null; applyPurchase(index, selectedType, token, origin); };
  if (reduced) { apply(); return; }
  pendingPurchase = { index, selectedType };
  const source = document.querySelector(`#offers [data-offer-index="${index}"]`);
  scene?.inspect(null);
  feedback.clear();
  flight.play(source, { onBurst: origin => { audio.fold(); apply(origin); } });
  render(); $('status').textContent = 'Opening your card…';
  // The original node was cloned for flight before rendering disabled offers.
  document.querySelector(`#offers [data-offer-index="${index}"]`)?.classList.add('card-flight-source');
}
function applyPurchase(index, selectedType, token, origin) {
  const before = structuredClone(state);
  if (!pick(state, index, selectedType)) return;
  run.moves.push([index, selectedType ?? null]); guestbook.saveActive(run);
  resolvingBefore = before; render();
  feedback.spend(state.history.at(-1).price, state.history.at(-1).refund);
  const complete = () => {
    if (token !== epoch || state.phase !== 'resolving') return;
    const entry = state.history.at(-1);
    advanceDeal(state); resolvingBefore = null;
    render(); scene.setState(state); syncCamera(); $('preview').textContent = '';
    feedback.pulse($('height')); feedback.deal();
    const parts = [];
    if (entry.links) {
      const bonus = entry.family === 'base' ? baseBonus(before, entry) : 0;
      parts.push(`+${entry.links} floors`);
      if (bonus) parts.push(`includes +${bonus} from upgrades`);
      if (entry.foundationBonus) parts.push(`Streak +${entry.foundationBonus}`);
      for (const badge of $('upgrade-rack').children) {
        if (bonus && (badge.dataset.upgrade === `suit:${entry.suit}` || (badge.dataset.upgrade === 'assembler' && entry.type !== 'mystery'))) feedback.pulse(badge);
      }
    } else {
      parts.push(`${title(entry)} ${entry.family === 'reactor' ? 'installed' : 'ready'}`);
      const badge = [...$('upgrade-rack').children].find(b => b.dataset.upgrade === (entry.type === 'suit' ? `suit:${entry.suit}` : entry.type)); feedback.pulse(badge);
    }
    if (before.foundation && !state.foundation) parts.push('Streak ended');
    if (before.attunement && !state.attunement) parts.push('Type Lock finished');
    $('status').textContent = parts.join(' · ');
    feedback.announce($('status').textContent);
  };
  let lastFloor = before.links.length;
  if (reduced) { audio.fold(); complete(); }
  else scene.animate(before, structuredClone(state), { origin, onFrame: count => { $('height').textContent = count; if (count > lastFloor) { audio.fold(); lastFloor = count; } }, onComplete: complete });
}
function restart(seed) {
  ++epoch; feedback.clear(); flight.cancel(); pendingPurchase = null; menuReturn = null; for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  resolvingBefore = null; choiceIndex = null; state = createGame(seed); setSeed();
  run = { id: crypto.randomUUID(), seed: state.seed, moves: [] }; completedRecord = null; guestbook.saveActive(run);
  $('status').textContent = 'Choose one card. A new delivery follows.'; $('preview').textContent = '';
  $('overview').textContent = 'Whole hotel'; render(); scene?.reset(state); syncCamera(); feedback.deal();
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
function toggleSound() { sound = audio.setEnabled(!sound); guestbook.preference('sound', sound); $('sound-toggle').textContent = sound ? 'Sound on' : 'Sound off'; $('sound-toggle').setAttribute('aria-pressed', String(sound)); shell?.preferences(sound, reduced); }
function restoreSound() { audio.setEnabled(sound); }
$('sound-toggle').addEventListener('click', toggleSound);
$('menu-open').addEventListener('click', () => { scene?.inspect(null); $('menu-dialog').showModal(); });
$('resume').addEventListener('click', () => $('menu-dialog').close());
for (const [button, dialog] of [['rules-open', 'rules-dialog'], ['workshop-open', 'workshop-dialog']]) {
  $(button).addEventListener('click', () => { menuReturn = button; $('menu-dialog').close(); $(dialog).showModal(); });
  $(dialog).addEventListener('close', () => { if (menuReturn !== button) return; menuReturn = null; $('menu-dialog').showModal(); $(button).focus(); });
}
$('menu-dialog').addEventListener('close', () => { if (!menuReturn && document.body.dataset.screen === 'game' && !document.querySelector('dialog[open]')) $('menu-open').focus(); });
$('choice-dialog').addEventListener('close', () => { choiceIndex = null; });
$('reveal-now').addEventListener('click', () => { flight.finish(); scene?.skip(); $('menu-dialog').close(); });
for (const id of ['overview', 'camera-toggle']) $(id).addEventListener('click', () => { scene.toggleOverview(); syncCamera(); $('menu-dialog').close(); });
$('effect-buy').addEventListener('click', () => { const index = effectIndex; $('effect-dialog').close(); select(index); });
$('height-info').addEventListener('click', () => explainCounter('Hotel floors', `Your hotel has ${state.links.length} floors. Each row of three windows is one floor. Spend your coins to build as high as you can.`));
function showLobby() {
  menuReturn = null; flight.finish(); scene?.skip(); feedback.clear();
  for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  shell.home({canResume: !finished(state)});
}
$('lobby-open').addEventListener('click', showLobby);
$('ending-board').addEventListener('click', () => shell.board(completedRecord));
$('ending-new').addEventListener('click', () => restart(randomSeed()));
$('ending-replay').addEventListener('click', () => restart(state.seed));
$('replay').addEventListener('click', () => restart(state.seed));
$('new-game').addEventListener('click', () => restart(randomSeed()));
function applyMotion(value) { reduced = value; if (reduced) feedback.clear(); scenery.setMotion(!reduced); document.documentElement.classList.toggle('reduced-motion', reduced); if (scene) scene.motion = !reduced; if (reduced) flight.finish(); if (scene) { if (reduced) { scene.skip(); scene.tower.y = 0; } scene.draw(); } $('motion-toggle').setAttribute('aria-pressed', String(reduced)); shell?.preferences(sound, reduced); }
function toggleMotion() { guestbook.preference('reduced', !reduced); applyMotion(!reduced); }
$('motion-toggle').addEventListener('click', toggleMotion); motionQuery.addEventListener('change', e => { guestbook.preference('reduced', null); applyMotion(e.matches); });
document.addEventListener('keydown', event => { if (document.body.dataset.screen === 'game' && !event.repeat && !event.ctrlKey && !event.metaKey && !event.altKey && /^[123]$/.test(event.key) && !document.querySelector('dialog[open]')) { event.preventDefault(); select(Number(event.key) - 1); } });
balanceTable(); render();
shell = mountLobby({img, guestbook, isReduced: () => reduced,
  onStart: () => { restoreSound(); restart(requestedSeed || randomSeed()); requestedSeed = null; },
  onResume: () => { restoreSound(); requestedSeed = null; setSeed(); render(); scene?.setState(state); },
  onRules: () => { menuReturn = null; $('rules-dialog').showModal(); },
  onSound: toggleSound, onMotion: toggleMotion,
});
$('sound-toggle').textContent = sound ? 'Sound on' : 'Sound off'; $('sound-toggle').setAttribute('aria-pressed', String(sound));
shell.preferences(sound, reduced); shell.home({canResume: !!guestbook.data.active});
world.ready.then(readyScene => { scene = readyScene; scene.motion = !reduced; loading = false; render(); scene.setState(state); $('world').dataset.ready = 'true'; });
if (import.meta.hot) import.meta.hot.dispose(() => { shell.destroy(); feedback.clear(); flight.destroy(); scenery.destroy(); world.destroy(); audio.destroy(); });
