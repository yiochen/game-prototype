// #28 r4: the Harpoon upgrade changes the harpoon that is fired, not the ship.
// Tier 1 is the approved native harpoon (godot/scripts/expedition/harpoon_art.gd) ported to SVG with the
// same geometry (u = cell / 55.7); tiers 2 and 3 extend it. Drawn pointing up, tip at the origin.
const INK = '#24364d';
export const harpoonTiers = [
  {length: 0.95, shaft: '#c9d4df', head: '#eef3f7', collar: '#e2553f', barbs: 1, rope: ['#6b4526', '#f3dcae', '#a77a4b']},
  {length: 1.08, shaft: '#c9d4df', head: '#eef3f7', collar: '#d9a43a', barbs: 2, rope: ['#7a2a22', '#e2553f', '#ffb3a3']},
  {length: 1.2, shaft: '#f1d27a', head: '#ffd552', collar: '#3cc6c0', barbs: 3, glow: '#6ff3ea', rope: ['#7a5418', '#ffd552', '#fff1b0']},
];

const pts = list => list.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ');

// SVG markup for one harpoon whose tip is at (0,0) and tail at (0, length·cell).
export function harpoonShape(tier, cell) {
  const t = harpoonTiers[tier - 1], u = cell / 55.7, L = cell * t.length;
  const line = (y0, y1, w, color) => `<line x1="0" y1="${y0}" x2="0" y2="${y1}" stroke="${color}" stroke-width="${w}" stroke-linecap="round"/>`;
  const head = (dy, s) => {
    const p = [[0, -3], [8, 14], [3, 12], [2.6, 16], [-2.6, 16], [-3, 12], [-8, 14]].map(([x, y]) => [x * u * s, (y * s + dy) * u]);
    return `<polygon points="${pts(p)}" fill="${t.head}" stroke="${INK}" stroke-width="${2.2 * u}" stroke-linejoin="round"/>`;
  };
  let out = '';
  if (t.glow) out += `<ellipse cx="0" cy="${L * 0.45}" rx="${10 * u}" ry="${L * 0.6}" fill="${t.glow}" opacity=".28"/>`;
  out += line(8 * u, L, 9.6 * u, INK) + line(8 * u, L, 5.2 * u, t.shaft);
  out += line(L - 13 * u, L - 6 * u, 12.8 * u, INK) + line(L - 13 * u, L - 6 * u, 8.4 * u, t.collar);
  if (t.glow) out += `<circle cx="0" cy="${L - 9.5 * u}" r="${3 * u}" fill="#fff" opacity=".85"/>`;
  // Extra barb pairs sit behind the head, each a little smaller (tier 2: two, tier 3: three).
  for (let i = t.barbs - 1; i >= 1; i--) out += head(i * 9, 1 - i * 0.12);
  out += head(0, t.glow ? 1.15 : 1);
  return out;
}

// A standalone icon (tip up, short coil of rope at the tail) for cards and the gallery.
export function harpoonIcon(tier) {
  const t = harpoonTiers[tier - 1], cell = 56, L = cell * t.length;
  const coil = `<path d="M0 ${L} q 9 6 0 11 q -9 5 0 10" fill="none" stroke="${t.rope[0]}" stroke-width="5" stroke-linecap="round"/><path d="M0 ${L} q 9 6 0 11 q -9 5 0 10" fill="none" stroke="${t.rope[1]}" stroke-width="2.8" stroke-linecap="round"/>`;
  return `<svg class="harpoon-icon" viewBox="-20 -8 40 ${L + 32}" aria-hidden="true">${coil}${harpoonShape(tier, cell)}</svg>`;
}

// Fire once from `nose` straight up `reach` px and reel back, drawn into an <svg> overlay whose user
// units are screen px. Returns a cancel function. Reduced motion shows a brief static extended pose.
export function fireHarpoon(svg, {nose, cell, tier, reach, reduced = false, onDone}) {
  const t = harpoonTiers[tier - 1], u = cell / 55.7, L = cell * t.length;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.innerHTML = `<path class="rope-shadow" fill="none" stroke="#05213f40" stroke-width="${7 * u}" stroke-linecap="round"/><path class="rope-out" fill="none" stroke="${t.rope[0]}" stroke-width="${5 * u}" stroke-linecap="round"/><path class="rope-in" fill="none" stroke="${t.rope[1]}" stroke-width="${2.8 * u}" stroke-linecap="round" stroke-dasharray="${2.2 * u} ${4.4 * u}"/><g class="trail"></g><g class="spear">${harpoonShape(tier, cell)}</g>`;
  svg.append(g);
  const [shadow, ropeOut, ropeIn] = g.querySelectorAll('path'), spear = g.querySelector('.spear'), trail = g.querySelector('.trail');
  const out = 0.32, hold = 0.18, back = 0.45, total = (out + hold + back) * 1000;
  let frame = 0, start = performance.now(), cancelled = false;
  const draw = now => {
    if (cancelled) return;
    const s = reduced ? out + hold / 2 : (now - start) / 1000;
    let k, slack;
    if (s < out) { k = 1 - (1 - s / out) ** 3; slack = 0.6; } else if (s < out + hold) { k = 1; slack = 0.15; } else { const r = Math.min(1, (s - out - hold) / back); k = 1 - r * r; slack = 0.9; }
    const tipY = nose.y - L - reach * k, tailY = tipY + L;
    spear.setAttribute('transform', `translate(${nose.x} ${tipY})`);
    const dist = Math.max(1, nose.y - tailY), sag = slack * Math.min(dist * 0.18, cell * 0.8) * Math.sin(now / 1000 * 9);
    const d = `M${nose.x} ${nose.y} Q${nose.x + sag + cell * 0.15 * slack} ${(nose.y + tailY) / 2} ${nose.x} ${tailY}`;
    shadow.setAttribute('d', d); shadow.setAttribute('transform', `translate(0 ${2.5 * u})`);
    ropeOut.setAttribute('d', d); ropeIn.setAttribute('d', d);
    ropeIn.setAttribute('stroke-dashoffset', String(-now / 1000 * 40 * u));
    ropeIn.setAttribute('stroke', t.rope[1]);
    if (t.glow && !reduced && s < out + hold && Math.random() < 0.5) {
      const spark = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      spark.setAttribute('cx', nose.x + (Math.random() - 0.5) * 8 * u); spark.setAttribute('cy', tailY + Math.random() * 10 * u);
      spark.setAttribute('r', 2.2 * u); spark.setAttribute('fill', t.glow);
      trail.append(spark);
      spark.animate([{opacity: 0.9, transform: 'scale(1)'}, {opacity: 0, transform: 'scale(.2)'}], {duration: 420}).onfinish = () => spark.remove();
    }
    if (reduced ? now - start < 600 : s * 1000 < total) frame = requestAnimationFrame(draw);
    else { g.remove(); onDone?.(); }
  };
  frame = requestAnimationFrame(draw);
  return () => { cancelled = true; cancelAnimationFrame(frame); g.remove(); };
}
