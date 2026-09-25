import paperSheet from './assets/ui/origami-paper.webp';

const SURFACES = 'button,.hanging-sign,.guestbook-paper,.score-form,.leaderboard-row,.rank-portrait,.welcome-seal,dialog,.ending,.stat,.strategy-chip,.deck-card,#purchase-feedback,.signature-line';
const PRIMARY = '.primary-button,#resume,#effect-buy,#ending-board,#ending-new';

export function dressPaper(root = document) {
  const items = [...root.querySelectorAll(SURFACES)];
  if (root.matches?.(SURFACES)) items.unshift(root);
  for (const el of items) {
    if (el.closest('.paper-fold-rig')) continue;
    // Semantic variants stay in CSS; one real nine-slice source is shared.
    if (!el.hasAttribute('data-paper')) el.dataset.paper = el.matches(PRIMARY) ? 'plum' : 'ivory';
  }
}

// Each leaf contains a clipped half of the *same complete nine-slice panel*.
// Only the leaf rotates. Corners retain their size, and text is never squashed.
export function createPaperUI(isReduced) {
  document.documentElement.style.setProperty('--origami-sheet', `url("${paperSheet}")`);
  const active = new Map();
  let sheetReady = false;
  const pending = new Map();
  const ready = new Image(); ready.src = paperSheet;
  const loaded = ready.decode().catch(() => {}).then(() => { sheetReady = true; });
  function settle(el) {
    pending.delete(el);
    const run = active.get(el); if (!run) return;
    active.delete(el);
    for (const animation of run.animations) { animation.onfinish = null; animation.cancel(); }
    run.rig.remove(); delete el.dataset.folding;
  }
  function clear(root = document) { for (const el of new Set([...active.keys(),...pending.keys()])) if (root === document || root === el || root.contains(el)) settle(el); }
  function unfold(el, { delay = 0, duration = 570, axis = 'x' } = {}) {
    dressPaper(el); settle(el);
    if (isReduced() || !el.isConnected || !el.getClientRects().length || el.closest('[hidden]')) return;
    if (!sheetReady) {
      const ticket = {}; pending.set(el,ticket);
      loaded.then(() => { if (pending.get(el) === ticket) unfold(el,{delay,duration,axis}); });
      return;
    }
    const rig = document.createElement('span'); rig.className = 'paper-fold-rig'; rig.dataset.axis = axis; rig.setAttribute('aria-hidden','true'); rig.inert = true;
    for (const side of ['first','second']) {
      const leaf = document.createElement('span'); leaf.className = `paper-fold-leaf ${side}`;
      const skin = document.createElement('span'); skin.className = 'paper-fold-skin'; leaf.append(skin); rig.append(leaf);
    }
    const children = [...el.children]; const ink = getComputedStyle(el).color;
    const run = { rig, animations: [] }; active.set(el,run); el.dataset.folding = axis; el.append(rig);
    const animate = (target, frames, options) => { const a = target.animate(frames,{fill:'both',...options}); run.animations.push(a); return a; };
    const rotation = axis === 'x' ? 'rotateY' : 'rotateX';
    for (const [i,leaf] of [...rig.children].entries()) {
      const sign = i ? -1 : 1;
      animate(leaf,[
        {transform:`${rotation}(${sign*88}deg)`,filter:'brightness(.68)',opacity:0},
        {transform:`${rotation}(${sign*65}deg)`,filter:'brightness(.82)',opacity:1,offset:.18},
        {transform:`${rotation}(${-sign*3}deg)`,filter:'brightness(1.02)',opacity:1,offset:.82},
        {transform:`${rotation}(0deg)`,filter:'brightness(1)',opacity:1},
      ],{duration,delay:delay+i*45,easing:'cubic-bezier(.2,.7,.25,1)'});
    }
    // Direct text nodes (simple buttons) and child elements have the same reveal.
    animate(el,[{color:'transparent'},{color:ink}],{duration:150,delay:delay+duration*.42});
    for (const child of children) animate(child,[{opacity:0,translate:'0 3px'},{opacity:1,translate:'0 0'}],{duration:180,delay:delay+duration*.42,easing:'ease-out'});
    const clock = animate(rig,[{opacity:1},{opacity:1}],{duration:duration+46,delay});
    clock.onfinish = () => settle(el);
  }
  function dialogOpen(dialog) {
    dressPaper(dialog);
    unfold(dialog,{duration:480,axis:'y'});
    dialog.querySelectorAll('button').forEach((button,i)=>unfold(button,{delay:220+Math.min(i,6)*30,duration:290}));
  }
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'childList') {
        for (const child of record.addedNodes) if (child.nodeType === 1 && !child.matches('.paper-fold-rig') && !child.closest('.paper-fold-rig')) dressPaper(child);
      } else if (record.target.matches('dialog')) {
        if (record.target.open) dialogOpen(record.target); else clear(record.target);
      } else if (record.target.id === 'ending' && !record.target.hidden) unfold(record.target,{axis:'y',duration:480});
    }
    for (const el of active.keys()) if (!el.isConnected || el.closest('[hidden]')) settle(el);
  });
  dressPaper(); observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['open','hidden']});
  document.addEventListener('visibilitychange', pause);
  function pause() { if (document.hidden) clear(); }
  return { unfold, clear, settle, dress: dressPaper, ready: loaded, destroy(){observer.disconnect();document.removeEventListener('visibilitychange',pause);clear();} };
}
