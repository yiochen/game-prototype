// #28 r5: power-up visuals. Ported from the approved #22 drawing (design/expedition-currents-preview:
// drawBoost, drawShield, drawSwirl) to SVG. A power-up's look tier only changes colour (tierColors),
// and pickups/entrances the ship can use carry the shared lime "good, interactable" signal.
import {tierColors, signal} from './balance.js';

// Heater-shield outline centred at (0,0), half-width w, height h (same curves as drawBoost).
function shieldPath(w, h) {
  const top = -h * 0.82;
  return `M0 ${top + h * 0.08} Q${w * 0.5} ${top - h * 0.06} ${w} ${top + h * 0.06} C${w * 1.02} ${h * 0.25} ${w * 0.62} ${h * 0.72} 0 ${h * 0.98} C${-w * 0.62} ${h * 0.72} ${-w * 1.02} ${h * 0.25} ${-w} ${top + h * 0.06} Q${-w * 0.5} ${top - h * 0.06} 0 ${top + h * 0.08}Z`;
}

// The shield pickup emblem (navy rim, blue face, white inner rim, sheen), r = cell * 0.3.
export function shieldEmblem(r, id = 'e') {
  return `<defs><linearGradient id="face-${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8fe3ff"/><stop offset=".45" stop-color="#2f9be8"/><stop offset="1" stop-color="#1559b8"/></linearGradient><clipPath id="clip-${id}"><path d="${shieldPath(r * 0.76, r * 0.92)}"/></clipPath></defs>
    <path d="${shieldPath(r * 0.95, r * 1.15)}" fill="#0d3f78" stroke="#082a52" stroke-width="${r * 0.13}" stroke-linejoin="round"/>
    <path d="${shieldPath(r * 0.76, r * 0.92)}" fill="url(#face-${id})" stroke="#fff" stroke-opacity=".95" stroke-width="${r * 0.1}"/>
    <rect x="${-r * 1.2}" y="${-r * 1.4}" width="${r * 1.2}" height="${r * 2.8}" fill="#fff" opacity=".28" clip-path="url(#clip-${id})"/>
    <ellipse cx="${-r * 0.38}" cy="${-r * 0.45}" rx="${r * 0.12}" ry="${r * 0.07}" transform="rotate(-40 ${-r * 0.38} ${-r * 0.45})" fill="#fff" opacity=".9"/>`;
}

// Shield bubble around the hull: tinted fill, faint full ring and a bright rim that drains with `fraction`.
export function shieldBubble(r, color, fraction = 1) {
  const c = 2 * Math.PI * r;
  return `<circle r="${r}" fill="${color}" fill-opacity=".16" stroke="${color}" stroke-opacity=".4" stroke-width="${r * 0.05}"/>
    <circle r="${r * 0.82}" fill="none" stroke="${color}" stroke-opacity=".18" stroke-width="${r * 0.3}"/>
    <circle class="bubble-rim" r="${r}" fill="none" stroke="${color}" stroke-width="${r * 0.09}" stroke-linecap="round" stroke-dasharray="${c * fraction} ${c}" transform="rotate(-90)"/>`;
}

// Three-armed whirlpool inside the portal ring; arms take the passage tier colour.
export function swirl(r, color, spin = 0) {
  const arms = [0, 1, 2].map(arm => {
    const p = Array.from({length: 25}, (_, i) => { const u = i / 24, a = arm * (Math.PI * 2 / 3) + spin + u * 3.2, rr = r * (0.95 - u * 0.8); return `${(Math.cos(a) * rr).toFixed(2)},${(Math.sin(a) * rr).toFixed(2)}`; });
    return `<polyline points="${p.join(' ')}" fill="none" stroke="${color}" stroke-opacity=".85" stroke-width="${r * 0.11}" stroke-linecap="round"/>`;
  }).join('');
  return `<defs><radialGradient id="core"><stop offset="0" stop-color="#031a42" stop-opacity=".95"/><stop offset=".55" stop-color="#0c5c96" stop-opacity=".75"/><stop offset="1" stop-color="#5adcff" stop-opacity="0"/></radialGradient></defs><circle r="${r}" fill="url(#core)"/>${arms}`;
}

// The shared interaction signal: soft halo plus a keylined ring that pulses outward (CSS animates .pulse).
export function signalGlow(r, kind = 'good') {
  const c = signal[kind] ?? kind; // a signal name, or a raw colour for the glow comparison
  return `<circle r="${r * 1.2}" fill="${c}" opacity=".45" filter="url(#soft)"/>
    <circle r="${r}" fill="none" stroke="#0a3048" stroke-opacity=".5" stroke-width="${r * 0.12}"/><circle r="${r}" fill="none" stroke="${c}" stroke-width="${r * 0.07}"/>
    <g class="pulse"><circle r="${r}" fill="none" stroke="${c}" stroke-width="${r * 0.05}"/></g>`;
}
export const softFilter = '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>';

// Card / gallery icons (r6): one-colour neon line glyphs on a dark tile, coloured by the look tier.
// Original drawings: shield + clock (duration), portal vortex with a ride chevron (passage), shield + launch chevrons (start).
const GLYPHS = {
  shield: `<path d="M50 14 C62 20 72 21 82 20 C83 50 74 72 50 86 C26 72 17 50 18 20 C28 21 38 20 50 14Z"/>
    <circle cx="50" cy="50" r="15"/><path d="M50 41 V50 L57 55"/><path d="M41 28 h18" opacity=".6"/>`,
  passage: `<circle cx="50" cy="58" r="30"/>
    <g transform="rotate(0 50 58)"><path d="M50 58 Q50 42 66 40"/></g><g transform="rotate(120 50 58)"><path d="M50 58 Q50 42 66 40"/></g><g transform="rotate(240 50 58)"><path d="M50 58 Q50 42 66 40"/></g>
    <path d="M38 14 L50 4 L62 14" stroke-width="5"/>`,
  launch: `<path d="M50 10 C60 15 68 16 76 15 C77 39 70 56 50 67 C30 56 23 39 24 15 C32 16 40 15 50 10Z"/>
    <path d="M50 26 V48"/><path d="M41 35 L50 26 L59 35"/>
    <path d="M36 80 L50 70 L64 80"/><path d="M36 92 L50 82 L64 92" opacity=".6"/>`,
};
export function powerupIcon(id, tier) {
  const off = id === 'launch' && tier === 1;
  return `<span class="pu-glyph ${off ? 'off' : ''}" style="--c:${tierColors[tier - 1]}"><svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${GLYPHS[id]}</svg></span>`;
}
