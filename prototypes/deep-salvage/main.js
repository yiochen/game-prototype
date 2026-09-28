import './style.css';
import { BALANCE as B, PART_RULES, MAPS, ENEMY_INFO, mapFor } from './balance.js';
import { PARTS, tileMarkup } from './parts.js';
import { RECIPES } from './recipes.js';
import { ART } from './artwork.js';
import { createState, startDive, tick, traceCircuit, rebuild, rotatePart, movePart, sourcePart, spawnDrop, forgeMatches, forgeRecipe, canAddToForge } from './engine.js';
import { createWorld } from './world.js';

const $ = selector => document.querySelector(selector);
const knownKey = 'deep-salvage:discoveries:v1';
function loadKnown() { try { const value = JSON.parse(localStorage.getItem(knownKey) || '[]'); return Array.isArray(value) ? value : []; } catch { return []; } }
function saveKnown() { try { localStorage.setItem(knownKey, JSON.stringify([...state.discovered])); } catch { /* Private browsing can disable persistence. */ } }
let state = createState(loadKnown()), selection = null, gesture = null, modalKind = null, revision = -1, toastTimer;
let restoreFocus = null, selectedMap = 'city', holdPage = 0, holdOrder = [];
const HOLD_SLOTS = 5;
const gameRoot = $('#game'), modal = $('#modal'), cells = $('#cells'), board = $('#board'), storage = $('#storage');
const buttons = Array.from({ length: B.gridSize ** 2 }, (_, index) => {
  const button = document.createElement('button'); button.className = 'cell empty'; button.dataset.index = index;
  button.setAttribute('aria-label', `Empty cell, row ${Math.floor(index / B.gridSize) + 1}, column ${index % B.gridSize + 1}`);
  cells.append(button); return button;
});
const lootElements = new Map();

function toast(message) {
  $('#toast').textContent = message; $('#toast').classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#toast').classList.remove('show'), 2300);
}

function renderBeams(circuit = state.circuit, preview = false) {
  const lines = circuit.segments.map(s => {
    const attrs = `x1="${s.x1 * 100}" y1="${s.y1 * 100}" x2="${s.x2 * 100}" y2="${s.y2 * 100}"`;
    const width = Math.min(22, 2 + s.power * .65);
    const color = s.piercing ? '#618eff' : s.power > B.reactorPower ? '#e6a52d' : '#34b9a5';
    return `<line class="beam" data-power="${s.power}" data-piercing="${s.piercing}" style="stroke:${preview ? '#efab46' : color};stroke-width:${width};opacity:${s.power < B.reactorPower ? .6 : 1}" ${attrs}/><line class="beam-core" style="stroke-width:${Math.max(1.2, width * .25)}" ${attrs}/><line class="beam-flow${s.piercing ? ' piercing-flow' : ''}" ${attrs}/>`;
  }).join('');
  $('#beam-lines').innerHTML = lines;
  $('#beam-glow').innerHTML = circuit.segments.map(s => `<line class="beam-glow" style="stroke:${s.piercing ? '#729cff' : s.power > B.reactorPower ? '#ffd365' : '#57f4d3'};stroke-width:${5 + Math.sqrt(s.power) * 3}" x1="${s.x1 * 100}" y1="${s.y1 * 100}" x2="${s.x2 * 100}" y2="${s.y2 * 100}"/>`).join('');
}

function renderForge() {
  const job = state.forge.job, recipe = forgeRecipe(state);
  document.querySelectorAll('.forge-slot').forEach((button, index) => {
    const part = state.forge.slots[index], locked = !!job?.indices.includes(index);
    if (button.dataset.type !== (part?.type || '')) { button.innerHTML = part ? tileMarkup(part.type) : '+'; button.dataset.type = part?.type || ''; }
    button.disabled = locked;
    button.classList.toggle('working', locked);
    button.classList.toggle('waiting-cash', !job && !!recipe && state.cash < recipe.cost && recipe.ingredients.includes(part?.type));
    button.style.setProperty('--progress', locked ? `${100 * (1 - job.remaining / job.seconds)}%` : '0%');
    button.setAttribute('aria-label', locked ? `${PARTS[part.type].name}, forging ${PARTS[job.output].name}, ${Math.ceil(job.remaining)} seconds remaining` : part ? `${PARTS[part.type].name} forge ingredient ${index + 1}, tap to return` : `Forge ingredient ${index + 1}`);
  });
  $('#forge').classList.toggle('working', !!job);
}

function renderLab() {
  for (const [index, button] of buttons.entries()) {
    const part = state.grid[index];
    button.removeAttribute('title');
    button.className = `cell ${part ? `has-part ${state.circuit.active.has(index) ? 'active' : 'inactive'}` : 'empty'}${state.circuit.blocked.includes(index) ? ' blocked' : ''}`;
    button.innerHTML = part ? `${tileMarkup(part.type, part.rotation)}${PART_RULES[part.type].capacity ? '<span class="charge-meter"><i></i></span>' : ''}` : '';
    button.classList.toggle('forge-match', !!part && forgeMatches(state).has(part.type));
    const label = part ? `${PARTS[part.type].name}, ${PARTS[part.type].rotatable ? `${part.rotation * 90} degrees, tap to rotate` : 'accepts beams from any side'}` : 'Empty cell';
    button.setAttribute('aria-label', `${label}, row ${Math.floor(index / B.gridSize) + 1}, column ${index % B.gridSize + 1}`);
    button.setAttribute('aria-keyshortcuts', part && !PARTS[part.type].rotatable ? 'Delete' : 'Enter Space Delete');
  }
  renderBeams();
  const parts = Object.entries(state.inventory).filter(([, count]) => count > 0);
  for (const [type] of parts) if (!holdOrder.includes(type)) holdOrder.push(type);
  const pageCount = Math.max(1, Math.ceil(holdOrder.length / HOLD_SLOTS));
  holdPage = Math.min(holdPage, pageCount - 1);
  const visible = holdOrder.slice(holdPage * HOLD_SLOTS, (holdPage + 1) * HOLD_SLOTS);
  $('#stacks').innerHTML = Array.from({ length: HOLD_SLOTS }, (_, index) => {
    const type = visible[index], count = state.inventory[type] || 0;
    if (!count) return '<button class="stack empty-slot" aria-label="Empty parts slot" disabled></button>';
    return `<button class="stack${selection === type ? ' selected' : ''}${forgeMatches(state).has(type) ? ' forge-match' : ''}" data-type="${type}" aria-label="${PARTS[type].name} stack, ${count} available">${tileMarkup(type)}<span class="count">${count}</span></button>`;
  }).join('');
  $('#hold-prev').disabled = holdPage === 0;
  $('#hold-next').disabled = holdPage === pageCount - 1;
  $('#stacks').setAttribute('aria-label', `Stored parts, page ${holdPage + 1} of ${pageCount}`);
  if (selection && !state.inventory[selection]) selection = null;
  renderForge();
  revision = state.revision;
}

function renderFrame() {
  if (revision !== state.revision) renderLab();
  renderForge();
  for (const [index, button] of buttons.entries()) {
    const part = state.grid[index];
    if (!part || !PART_RULES[part.type].capacity) continue;
    const rule = PART_RULES[part.type];
    const percent = Math.floor((part.charge || 0) / rule.capacity * 100);
    button.querySelector('.charge-meter i').style.width = `${percent}%`;
    button.classList.toggle('charged', percent === 100);
    button.title = `${PARTS[part.type].name}: ${percent}% charged · ${rule.restore ? `+${rule.restore} ${rule.resource}` : `${B.pulseDamage} damage per pulse`}`;
    button.setAttribute('aria-label', `${PARTS[part.type].name}, ${percent}% charged, ${state.circuit.active.has(index) ? 'powered' : 'disconnected'}, row ${Math.floor(index / B.gridSize) + 1}, column ${index % B.gridSize + 1}`);
  }
  $('#cash-label').textContent = state.cash;
  $('#shield-fill').style.width = `${state.shield / B.shield * 100}%`;
  $('.shield-track').setAttribute('aria-label', `Shield ${Math.ceil(state.shield)} of ${B.shield}`);
  $('.hull-badge').classList.toggle('taking-damage', state.submarine.hitFlash > 0);
  $('#hull-label').textContent = Math.ceil(state.hull);
  if (state.notices.length) toast(state.notices.shift());
  $('#hull-fill').style.width = `${state.hull}%`;
  $('#hull-fill').style.background = state.hull < 35 ? '#f18d80' : '#83d4b0';
  $('#wave-label').innerHTML = `${String(state.wave + 1).padStart(2, '0')} <span>/ ${String(mapFor(state).waves.length).padStart(2, '0')}</span>`;
  $('#location-label').textContent = mapFor(state).waves[state.wave].name.toUpperCase();
  $('.depth').textContent = `${mapFor(state).depth + state.wave * 120} m ↓`;
  $('#world').dataset.map = state.mapId;
  $('#kill-label').textContent = `${state.salvaged} recovered`;
  const notice = state.rest > 0 ? `⏱ ${Math.ceil(state.rest)}s` : '';
  if ($('#wave-notice').innerHTML !== notice) $('#wave-notice').innerHTML = notice;
  $('#world-hint').textContent = gesture?.dragging ? 'ENGINEERING · TIME SLOWED' : !state.circuit.guns.length ? 'NO POWERED GUNS · CHECK THE LAB' : 'TAP SCRAP TO SALVAGE';
  const existing = new Set();
  for (const drop of state.drops) {
    existing.add(drop.id);
    let button = lootElements.get(drop.id);
    if (!button) {
      button = document.createElement('button'); button.className = 'loot'; button.dataset.id = drop.id;
      button.innerHTML = `${tileMarkup(drop.type)}<span class="loot-meter"><i></i></span>`;
      button.setAttribute('aria-label', `Salvage ${PARTS[drop.type].name}`);
      $('#loot-layer').append(button); lootElements.set(drop.id, button);
    }
    button.style.left = `${drop.x * 100}%`; button.style.top = `${drop.y * 100}%`;
    button.classList.toggle('expiring', drop.life < B.lootFlash);
    button.classList.toggle('held', state.heldDrop === drop.id);
    button.classList.toggle('forge-match', forgeMatches(state).has(drop.type));
    button.querySelector('.loot-meter i').style.width = `${drop.life / B.lootLife * 100}%`;
  }
  for (const [id, button] of lootElements) if (!existing.has(id)) { button.remove(); lootElements.delete(id); }
}

function selectStack(type) {
  selection = selection === type ? null : type;
  renderLab();
  buttons.forEach((button, i) => button.classList.toggle('valid', !!selection && !state.grid[i]));
}

function sourceFromElement(element) {
  const ingredient = element.closest('.forge-slot'); if (ingredient && state.forge.slots[ingredient.dataset.slot] && !state.forge.job?.indices.includes(Number(ingredient.dataset.slot))) return { kind: 'forge', index: Number(ingredient.dataset.slot) };
  const drop = element.closest('.loot'); if (drop) return { kind: 'drop', id: Number(drop.dataset.id) };
  const cell = element.closest('.cell'); if (cell && state.grid[cell.dataset.index]) return { kind: 'grid', index: Number(cell.dataset.index) };
  const stack = element.closest('.stack'); if (stack) return { kind: 'storage', type: stack.dataset.type };
  return null;
}

function destinationAt(x, y) {
  const target = document.elementFromPoint(x, y);
  const cell = target?.closest('.cell');
  if (cell) return { kind: 'grid', index: Number(cell.dataset.index) };
  const slot = target?.closest('.forge-slot');
  if (slot) return { kind: 'forge', index: Number(slot.dataset.slot) };
  if (target?.closest('#forge')) return { kind: 'forge' };
  if (target?.closest('#storage')) return { kind: 'storage' };
  return null;
}

function positionPreviewAndFindTarget(x, y) {
  const preview = $('#drag-ghost');
  preview.style.left = `${x}px`; preview.style.top = `${y}px`;
  // The visible tile is lifted above the pointer. Use its actual rendered center
  // for both highlighting and placement, including any CSS sizing/offset changes.
  const rect = preview.getBoundingClientRect();
  return destinationAt(rect.x + rect.width / 2, rect.y + rect.height / 2);
}

function clearGesture() {
  if (gesture && gameRoot.hasPointerCapture(gesture.pointerId)) gameRoot.releasePointerCapture(gesture.pointerId);
  gesture = null; state.heldDrop = null; $('#drag-ghost').hidden = true; storage.classList.remove('drop-target'); $('#forge').classList.remove('invalid'); $('#forge').classList.remove('drop-target');
  renderLab();
}

function previewDestination(target) {
  buttons.forEach((button, index) => {
    button.classList.toggle('valid', !state.grid[index]);
    button.classList.remove('target', 'invalid');
    button.classList.toggle('drag-source', gesture?.source.kind === 'grid' && gesture.source.index === index);
  });
  storage.classList.toggle('drop-target', target?.kind === 'storage');
  const forgeTarget = target?.kind === 'forge', forgeValid = forgeTarget && canAddToForge(state, gesture.part.type, target.index);
  $('#forge').classList.toggle('invalid', !!forgeTarget && !forgeValid);
  $('#forge').classList.toggle('drop-target', !!forgeValid);
  if (target?.kind === 'grid') {
    const valid = !state.grid[target.index]; buttons[target.index].classList.add(valid ? 'target' : 'invalid');
    if (valid) {
      const grid = state.grid.map(part => part ? { ...part } : null);
      if (gesture.source.kind === 'grid') grid[gesture.source.index] = null;
      grid[target.index] = { ...gesture.part };
      renderBeams(traceCircuit(grid), true); return;
    }
  }
  renderBeams();
}

gameRoot.addEventListener('pointerdown', event => {
  if (modal.open || gesture || event.button !== 0 || ['won', 'lost'].includes(state.status)) return;
  const source = sourceFromElement(event.target); if (!source) return;
  const part = sourcePart(state, source); if (!part) return;
  event.preventDefault();
  event.target.closest('button')?.focus({ preventScroll: true });
  gesture = { source, part: { ...part }, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, dragging: false, targetKey: '' };
  if (source.kind === 'drop') state.heldDrop = source.id;
  gameRoot.setPointerCapture(event.pointerId);
});
gameRoot.addEventListener('pointermove', event => {
  if (!gesture || event.pointerId !== gesture.pointerId) return;
  if (!gesture.dragging && Math.hypot(event.clientX - gesture.startX, event.clientY - gesture.startY) > 7) {
    gesture.dragging = true; selection = null;
    $('#drag-ghost').innerHTML = tileMarkup(gesture.part.type, gesture.part.rotation); $('#drag-ghost').hidden = false;
  }
  if (!gesture.dragging) return;
  event.preventDefault();
  const target = positionPreviewAndFindTarget(event.clientX, event.clientY), key = JSON.stringify(target);
  if (key !== gesture.targetKey) { gesture.targetKey = key; previewDestination(target); }
});
gameRoot.addEventListener('pointerup', event => {
  if (!gesture || event.pointerId !== gesture.pointerId) return;
  const current = gesture;
  if (current.dragging) {
    const target = positionPreviewAndFindTarget(event.clientX, event.clientY);
    const moved = target && movePart(state, current.source, target);
    if (!moved) toast('Cannot place here');
  } else if (current.source.kind === 'forge') {
    movePart(state, current.source, { kind: 'storage' });
  } else if (current.source.kind === 'grid') {
    rotatePart(state, current.source.index);
  } else if (current.source.kind === 'drop') {
    movePart(state, current.source, { kind: 'storage' });
  } else { selection = selection === current.part.type ? null : current.part.type; }
  clearGesture();
  if (selection) buttons.forEach((button, i) => button.classList.toggle('valid', !state.grid[i]));
  renderFrame(); checkDiscoveries();
});
gameRoot.addEventListener('pointercancel', clearGesture);
gameRoot.addEventListener('lostpointercapture', () => { if (gesture) clearGesture(); });

gameRoot.addEventListener('click', event => {
  if (modal.open || ['won', 'lost'].includes(state.status)) return;
  const slot = event.target.closest('.forge-slot');
  if (slot && !state.forge.slots[slot.dataset.slot] && selection) {
    if (movePart(state, { kind: 'storage', type: selection }, { kind: 'forge', index: Number(slot.dataset.slot) })) { selection = null; renderLab(); }
    return;
  }
  const cell = event.target.closest('.cell');
  if (cell) {
    const index = Number(cell.dataset.index);
    if (!state.grid[index] && selection) {
      if (movePart(state, { kind: 'storage', type: selection }, { kind: 'grid', index })) { selection = null; renderLab(); }
    } else if (event.detail === 0) { rotatePart(state, index); renderLab(); }
  }
  if (event.detail === 0) {
    const ingredient = event.target.closest('.forge-slot');
    if (ingredient && state.forge.slots[ingredient.dataset.slot]) { movePart(state, { kind: 'forge', index: Number(ingredient.dataset.slot) }, { kind: 'storage' }); renderLab(); }
    const stack = event.target.closest('.stack'); if (stack) selectStack(stack.dataset.type);
    const drop = event.target.closest('.loot');
    if (drop) { movePart(state, { kind: 'drop', id: Number(drop.dataset.id) }, { kind: 'storage' }); renderFrame(); checkDiscoveries(); }
  }
});
cells.addEventListener('keydown', event => {
  const cell = event.target.closest('.cell'); if (!cell || modal.open) return;
  const index = Number(cell.dataset.index);
  if (['Delete', 'Backspace'].includes(event.key)) {
    event.preventDefault(); if (movePart(state, { kind: 'grid', index }, { kind: 'storage' })) { renderLab(); toast('Part returned to hold'); }
  }
  const offsets = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -B.gridSize, ArrowDown: B.gridSize };
  if (event.key in offsets) { event.preventDefault(); buttons[Math.max(0, Math.min(B.gridSize ** 2 - 1, index + offsets[event.key]))].focus(); }
});

function openModal(kind, content) {
  if (gesture) clearGesture();
  restoreFocus = modal.open ? restoreFocus : document.activeElement;
  modalKind = kind; state.paused = true; gameRoot.classList.add('is-paused');
  $('#modal-content').innerHTML = content;
  if (!modal.open) modal.showModal();
  $('#modal-content').scrollTop = 0;
  modal.scrollTop = 0;
  modal.querySelector('button')?.focus({ preventScroll: true });
}

function closeModal() {
  modalKind = null; modal.close(); state.paused = false; gameRoot.classList.remove('is-paused');
  if (restoreFocus?.isConnected) restoreFocus.focus({ preventScroll: true });
  checkDiscoveries();
}

function showWelcome() {
  selectedMap = state.mapId;
  openModal('welcome', `<div class="welcome-art"><img src="data:image/svg+xml;charset=utf-8,${encodeURIComponent(ART.submarine)}" alt="A little yellow submarine"></div><p class="modal-eyebrow">A LITTLE MACHINE. A BIG OCEAN.</p><h2 id="modal-title">Deep Salvage<span class="title-dot">.</span></h2><p class="modal-copy">The city sank. Your ingenuity didn't.<br>Keep your submarine alive with whatever you find.</p><p class="modal-copy">Tap fallen parts to salvage. Drag parts into the lab or forge. Rotate reactors and mirrors; every recipe is in the guide.</p><fieldset class="route-picker"><legend>Choose your route</legend>${Object.entries(MAPS).map(([id, map]) => `<button type="button" class="route-card" data-map="${id}" aria-pressed="${id === selectedMap}"><strong>${map.name}</strong><small>${map.difficulty} · 3 waves</small><span>${map.description}</span></button>`).join('')}</fieldset><p class="modal-copy">Shield and Medic terminals charge from beams to restore protection and hull. One of each and an extra reactor are in your hold. Starting a route begins a fresh dive.</p><div class="modal-actions"><button class="primary" data-action="start">Let's dive →</button>${state.status !== 'ready' ? '<button class="secondary" data-action="close">Back to current dive</button>' : ''}</div>`);
}

function showPause() {
  openModal('pause', `<p class="modal-eyebrow">TAKE A BREATH</p><h2 id="modal-title">Holding depth.</h2><p class="modal-copy">Your submarine and salvage are safe while paused.</p><div class="modal-actions"><button class="primary" data-action="close">Keep going →</button><button class="secondary" data-action="guide">Parts guide</button><button class="secondary" data-action="restart">Start a new dive</button><button class="secondary" data-action="routes">Choose another route</button></div>`);
}

function showGuide() {
  openModal('guide', `<p class="modal-eyebrow">THE ENGINEER'S FIELD NOTES</p><h2 id="modal-title">Recipes & parts.</h2><h3>All forge recipes</h3><p class="modal-copy">The right column automatically forges any affordable recipe whose ingredients are present. Cash is deducted when it starts. Unrelated parts stay in place; any part can be added to an empty slot, even during another job. Glowing progress marks locked ingredients. Tap other ingredients to recover them. No recipe is a subset of another. The timer pauses with the dive.</p><div class="recipe-list">${RECIPES.map(r => `<article class="recipe-row"><div class="recipe-ingredients">${[...new Set(r.ingredients)].map(type => `<span>${r.ingredients.filter(t => t === type).length} × ${PARTS[type].name}</span>`).join(' + ')}</div><strong>→ ${PARTS[r.output].name}</strong><p>${PARTS[r.output].description}</p><small>${r.cost}¢ · ${r.seconds}s · ${r.ingredients.length} ingredients</small></article>`).join('')}</div><h3>Parts manual</h3><p class="modal-copy">The 6 × 6 lab fills the left side; the right column is the forge and the bottom row is storage. Its arrows page through fixed stacks without scrolling. All parts fit one square. Beams travel freely through empty cells. Only reactors and mirrors need rotation. Other parts work from any side. Thicker gold beams carry more power; thin beams carry less. Blue dashed beams pierce armor. Laser guns beam continuously for steady damage. Pink pulse guns store energy; their bars show charge. At 100% they fire a 54-damage pulse. Amplifiers speed up charging; lenses add piercing to either weapon. Shield and Medic terminals restore protection and hull when charged. They hold a full charge at full health; amplifiers speed them up, but lenses do not multiply repairs. Charged parts retain energy on the grid and clear it in storage. Your hold includes all three terminal types and a spare reactor.</p><div class="guide-list">${Object.entries(PARTS).map(([type, part]) => `<article class="guide-row"><div class="guide-tile">${tileMarkup(type)}</div><div><h3>${part.name}${state.discovered.has(type) ? '' : '<small>NOT FOUND YET</small>'}</h3><p>${part.description} ${part.tip}</p><p class="ports">${part.ports}</p></div></article>`).join('')}</div><h3>Enemy field guide</h3><div class="enemy-guide">${Object.entries(ENEMY_INFO).map(([type, info]) => `<article class="enemy-row"><img src="data:image/svg+xml;charset=utf-8,${encodeURIComponent(ART[type])}" alt=""><div><h4>${info.name}</h4><p>${info.tactic}</p><small>${B.enemies[type].hp} HP · ${B.enemies[type].armor} armor · ${B.enemies[type].damage} damage${B.enemies[type].shield ? ` · ${B.enemies[type].shield} shield` : ''}</small></div></article>`).join('')}</div><h3>Route atlas</h3>${Object.values(MAPS).map(map => `<p class="modal-copy"><strong>${map.name} · ${map.difficulty}</strong><br>${map.description}</p>`).join('')}<div class="guide-close"><button class="primary" data-action="close">Back to the dive →</button></div>`);
}

function checkDiscoveries() {
  if (modal.open || gesture || !state.discoveries.length) return;
  const type = state.discoveries.shift(), part = PARTS[type]; saveKnown();
  openModal('discovery', `<div class="big-part">${tileMarkup(type)}</div><p class="modal-eyebrow">NEW PART DISCOVERED</p><h2 id="modal-title">${part.name}<span class="title-dot">.</span></h2><span class="modal-tag">1 × 1 TILE · ${part.ports.toUpperCase()}</span><p class="modal-copy"><strong>${part.lesson}</strong><br>${part.description}</p><div class="discovery-flow">${type === 'splitter' ? '↖ ← ◇ → ↗' : '↑ ◇ ↑'}</div><p class="modal-copy">${part.tip}</p><div class="modal-actions"><button class="primary" data-action="close">Got it. Let's build →</button></div>`);
}

function showEnd() {
  const won = state.status === 'won';
  openModal('end', `<p class="modal-eyebrow">${won ? 'THE BEACON IS IN SIGHT' : 'THE OCEAN GOT THIS ONE'}</p><h2 id="modal-title">${won ? 'Still in one piece.' : 'A brave little dive.'}</h2><p class="modal-copy">${won ? 'A heap of scrap, a working machine, and a way home. Nicely engineered.' : 'Forge your spare amplifiers early. Add a lens to cut through armored enemies, then strengthen your branches.'}</p><div class="stats"><div><strong>${state.kills}</strong><span>DRONES SUNK</span></div><div><strong>${state.salvaged}</strong><span>PARTS SAVED</span></div><div><strong>${Math.ceil(state.hull)}</strong><span>HULL LEFT</span></div></div><div class="modal-actions"><button class="primary" data-action="restart">Another dive →</button><button class="secondary" data-action="guide">Study the parts</button><button class="secondary" data-action="routes">Choose another route</button></div>`);
}

function restart(mapId = state.mapId) {
  selection = null; holdPage = 0; holdOrder = []; saveKnown(); state = createState(loadKnown(), mapId); revision = -1;
  modal.close(); modalKind = null; gameRoot.classList.remove('is-paused');
  startDive(state); renderFrame();
}

$('#modal-content').addEventListener('click', event => {
  const mapId = event.target.closest('[data-map]')?.dataset.map;
  if (mapId && MAPS[mapId]) { selectedMap = mapId; modal.querySelectorAll('[data-map]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.map === mapId))); }
  const action = event.target.closest('[data-action]')?.dataset.action;
  if (action === 'start') { restart(selectedMap); }
  if (action === 'close') {
    if (state.status === 'won' || state.status === 'lost') showEnd(); else closeModal();
  }
  if (action === 'restart') restart();
  if (action === 'guide') showGuide();
  if (action === 'routes') showWelcome();
});
modal.addEventListener('cancel', event => {
  event.preventDefault();
  if ((modalKind === 'welcome' && state.status === 'ready') || modalKind === 'end') return;
  if (state.status === 'won' || state.status === 'lost') showEnd(); else closeModal();
});
for (const [id, direction] of [['hold-prev', -1], ['hold-next', 1]]) {
  $(`#${id}`).addEventListener('click', () => { holdPage = Math.max(0, holdPage + direction); selection = null; renderLab(); });
}
$('#pause').addEventListener('click', showPause);
$('#manual').addEventListener('click', showGuide);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !modal.open) { event.preventDefault(); if (gesture) clearGesture(); else showPause(); }
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden && state.status === 'running') { if (gesture) clearGesture(); if (!modal.open) showPause(); }
});
window.addEventListener('blur', () => { if (gesture) clearGesture(); });

renderFrame(); showWelcome();
const world = createWorld($('#phaser-world'), () => state, dt => {
  tick(state, dt * (gesture?.dragging ? B.dragSpeed : 1));
  renderFrame();
  if (['won', 'lost'].includes(state.status) && !modal.open) showEnd();
  else checkDiscoveries();
});

// Explicit opt-in deterministic test harness; absent from ordinary play.
if (new URLSearchParams(location.search).has('test')) {
  window.__deepSalvage = {
    snapshot: () => JSON.parse(JSON.stringify({ ...state, discovered: [...state.discovered], circuit: { ...state.circuit, active: [...state.circuit.active] } })),
    drop: (type, x = 0.65, y = B.floor) => { const drop = spawnDrop(state, type, x, y); drop.landed = true; renderFrame(); return drop.id; },
    advance: seconds => { tick(state, seconds); renderFrame(); if (['won', 'lost'].includes(state.status) && !modal.open) showEnd(); },
    setVitals: (hull, shield) => { state.hull = Math.max(0, Math.min(B.hull, hull)); state.shield = Math.max(0, Math.min(B.shield, shield)); state.shieldCooldown = B.shieldDelay; renderFrame(); },
    setCash: cash => { state.cash = Math.max(0, cash); renderFrame(); },
    setEnemies: enemies => { state.enemies = enemies; },
    setSpawnDelay: seconds => { state.spawnIn = Math.max(0, seconds); },
    setGrid: grid => { state.grid = grid; rebuild(state); renderLab(); },
  };
}
window.addEventListener('pagehide', event => { if (!event.persisted) world.destroy(); });
