// #28 r7: the game's one scene transition, used for every scene switch.
// An iris closes onto what the player tapped, like the harpoon strike's focus circle: navy outside and
// a cream rim on the edge. While it is shut a small loading beat plays (the salvage chunk bobbing over
// rising bubbles), the next scene is built, and the iris reopens on the new scene's point of interest.
// Input is blocked throughout. Reduced motion uses a short fade through navy instead.

const NAVY = '#0f2433', RIM = '#fff1d3';

function overlay(root, loaderIcon) {
  const el = document.createElement('div');
  el.className = 'iris';
  el.innerHTML = `<svg class="iris-svg" aria-hidden="true"><defs><mask id="iris-hole"><rect width="100%" height="100%" fill="#fff"/><circle class="hole" fill="#000"/></mask></defs>
    <rect width="100%" height="100%" fill="${NAVY}" mask="url(#iris-hole)"/><circle class="rim" fill="none" stroke="${RIM}" stroke-width="5"/></svg>
    <div class="iris-loader" role="status" aria-live="polite"><span class="bubbles"><i></i><i></i><i></i></span><img src="${loaderIcon}" alt=""><span class="sr-only">Loading</span></div>`;
  root.append(el);
  return el;
}

const ease = k => k < .5 ? 4 * k * k * k : 1 - (-2 * k + 2) ** 3 / 2;
function iris(el, at, from, to, ms) {
  const [hole, rim] = el.querySelectorAll('.hole, .rim');
  for (const c of [hole, rim]) { c.setAttribute('cx', at.x); c.setAttribute('cy', at.y); c.setAttribute('r', Math.max(0, from)); }
  return new Promise(done => {
    const start = performance.now();
    const step = now => {
      const k = Math.min(1, (now - start) / ms), r = from + (to - from) * ease(k);
      hole.setAttribute('r', Math.max(0, r)); rim.setAttribute('r', Math.max(0, r)); rim.style.opacity = r < 2 ? 0 : 1;
      if (k < 1) requestAnimationFrame(step); else done();
    };
    requestAnimationFrame(step);
    setTimeout(() => { hole.setAttribute('r', Math.max(0, to)); done(); }, ms + 120); // throttled-frame fallback
  });
}

/**
 * Switch scenes inside `root` (the phone frame).
 * @param from  point (root px) the iris closes on: the tapped hut, doorway, submarine…
 * @param to    point to reopen on in the new scene (defaults to the centre)
 * @param swap  builds the next scene while the screen is shut (may be async)
 */
export async function sceneTransition(root, {from, to, swap, loaderIcon, reduced = false, minLoadMs = 450}) {
  if (root.querySelector('.iris')) return; // one transition at a time; repeated taps do nothing
  const el = overlay(root, loaderIcon);
  const {width: W, height: H} = root.getBoundingClientRect();
  const cover = p => Math.hypot(Math.max(p.x, W - p.x), Math.max(p.y, H - p.y)) + 8;
  from ??= {x: W / 2, y: H / 2};
  if (reduced) {
    el.classList.add('fade');
    await el.animate([{opacity: 0}, {opacity: 1}], {duration: 150, fill: 'forwards'}).finished;
    await swap?.();
    await el.animate([{opacity: 1}, {opacity: 0}], {duration: 150, fill: 'forwards'}).finished;
    el.remove();
    return;
  }
  await iris(el, from, cover(from), 0, 420);
  el.classList.add('loading');
  const started = performance.now();
  await swap?.();
  const at = typeof to === 'function' ? to() : to;
  await new Promise(r => setTimeout(r, Math.max(0, minLoadMs - (performance.now() - started))));
  el.classList.remove('loading');
  const open = at ?? {x: W / 2, y: H / 2};
  await iris(el, open, 0, cover(open), 460);
  el.remove();
}
