const BASE_PARTS = {
  reactor: { name: 'Reactor', rotatable: true, color: '#ffad38', ink: '#a4531d', mark: 'CORE', description: 'The heart of your machine. Sends 8 energy in the direction it faces through empty space.', tip: 'Rotate to change its output. Keep at least one gun connected.', ports: 'One directional output', lesson: 'Power starts here.' },
  mirror: { name: 'Mirror', rotatable: true, color: '#55c7bf', ink: '#177f83', mark: 'TURN', description: 'Reflects a beam by 90°. Empty cells between parts are fine.', tip: 'Tap to flip the diagonal. Look at the beam to see where it goes.', ports: 'Reflects either side', lesson: 'Give your beam a new direction.' },
  amplifier: { name: 'Amplifier', color: '#f7c94e', ink: '#b58128', mark: '×1.5', description: 'Accepts beams from any side, multiplies their energy by 1.5, and sends them straight onward.', tip: 'Amplify before a split to strengthen both branches. No rotation needed.', ports: 'Any side → straight through', lesson: 'A little more punch.' },
  splitter: { name: 'Splitter', color: '#b79be8', ink: '#7251a6', mark: 'SPLIT', description: 'Accepts a beam from any side and splits it left and right relative to its incoming direction. Each branch gets half the energy.', tip: 'Send the branches into guns, or use mirrors to route them farther. No rotation needed.', ports: 'Any side → two perpendicular beams', lesson: 'One beam. Two possibilities.' },
  lens: { name: 'Lens', color: '#81bfee', ink: '#3d7dae', mark: 'PIERCE', description: 'Accepts beams from any side and passes them straight through. Makes shots pierce armor and strike a second enemy behind their target.', tip: 'Add it to a branch before the gun. No rotation needed.', ports: 'Any side → straight through', lesson: 'Go right through them.' },
  pulse: { name: 'Pulse gun', color: '#efa2ca', ink: '#a75288', mark: 'PULSE', description: 'Accepts energy from all four sides and stores 36 energy, then fires a 54-damage pulse. Stronger beams charge it faster. A lens adds armor piercing and extra targets.', tip: 'A full gun waits for an enemy. Disconnection holds charge; reconnect to fire. Returning it to the hold clears charge. A spare starts in your hold.', ports: 'Inputs on all four sides · terminal', lesson: 'Store energy. Release a heavy pulse.' },
  gun: { name: 'Laser gun', color: '#7bd6bc', ink: '#318d78', mark: 'LASER', description: 'Accepts beams from all four sides and turns their energy into a continuous laser at the nearest enemy. Small hits add up over time; the tile shows damage per second before armor.', tip: 'Every powered gun tracks independently. More energy means more damage per second.', ports: 'Inputs on all four sides', lesson: 'Your machine reaches the world.' },
};

const upgrade = (base, name, mark, description, tier = 2) => ({ ...BASE_PARTS[base], base, name, mark, description, tier, ports: base === 'splitter' ? 'Any side → three beams' : BASE_PARTS[base].ports, lesson: 'More capability. Still one square.', tip: 'Forged parts still occupy one square. ' + (BASE_PARTS[base].rotatable ? 'Tap to rotate.' : 'Works from any side.') });
export const PARTS = Object.freeze({
  ...BASE_PARTS,
  reactor2: upgrade('reactor', 'Fusion core', '12', 'Emits 12 energy: 50% more power for the entire circuit.'),
  mirror2: upgrade('mirror', 'Prism mirror', '×1.25', 'Turns a beam 90° and multiplies its energy by 1.25.'),
  amplifier2: upgrade('amplifier', 'Overcharger', '×2.4', 'Multiplies energy by 2.4 in a single square.'),
  splitter2: upgrade('splitter', 'Trident', '½ × 3', 'Splits forward, left and right. Each branch retains half the incoming power.'),
  splitter3: upgrade('splitter', 'Duplicator', '1 × 3', 'Splits forward, left and right with full incoming power on every branch.', 3),
  lens2: upgrade('lens', 'Rail lens', 'PIERCE 3', 'Adds 25% power and piercing shots that hit up to three enemies.'),
  gun2: upgrade('gun', 'Heavy laser', '×1.6', 'Turns incoming energy into a continuous laser with 1.6 times the normal damage per second.'),
  prism2: upgrade('lens', 'Prism overcharger', '×2.8 ◆', 'Multiplies energy by 2.8 and adds two-target piercing in one square.', 3),
  prism: upgrade('lens', 'Piercing amplifier', '×1.75 ◆', 'Multiplies energy by 1.75 and adds piercing in one square.'),
});

// Only reactors and mirrors have a meaningful orientation.
export function partIcon(type) {
  const paths = {
    reactor: '<circle cx="32" cy="34" r="18" fill="#fce6a3"/><circle cx="32" cy="34" r="10" fill="#fff9d9"/><path d="M32 17V3m-6 6 6-6 6 6"/><path d="M32 55v5M4 34h7M53 34h7"/>',
    mirror: '<path d="M13 49 49 13" stroke="#183c4c" stroke-width="13"/><path d="M13 46 46 13" stroke="#ecfcf5" stroke-width="8"/><path d="m15 17 7 7m20 19 7 7" stroke="#e7fffa" stroke-width="2"/>',
    amplifier: '<path d="M32 3v7M32 54v7M3 32h7M54 32h7" stroke="#fff4bf"/><circle cx="32" cy="32" r="17" fill="#fff4bf"/><path d="M32 23v18M23 32h18" stroke="#b58128" stroke-width="6"/>',
    splitter: '<path d="M32 5v54M5 32h54" stroke="#efffff" stroke-width="6"/><path d="m25 12 7-7 7 7M25 52l7 7 7-7M12 25l-7 7 7 7m40-14 7 7-7 7" stroke="#efffff"/><path d="m32 22 10 10-10 10-10-10z" fill="#7251a6" stroke="#efffff"/>',
    lens: '<path d="M32 3v7M32 54v7M3 32h7M54 32h7" stroke="#c2f8ff"/><circle cx="32" cy="32" r="18" fill="#c2f8ff"/><circle cx="32" cy="32" r="12" fill="#54c6ec" stroke="none"/><path d="m27 24-3 8" stroke="white" stroke-width="4"/>',
    pulse: '<path d="M4 32h7m42 0h7M32 3v7m0 44v7" stroke="#fff0fa"/><path d="M21 8h22v17H21z" fill="#fce6f4"/><path d="M14 25h36v27H14z" fill="#793b76"/><circle cx="32" cy="36" r="13" fill="#fff1bf"/><circle cx="32" cy="36" r="7" fill="#f7a6dc"/><path d="M12 55h40" stroke="#fff0fa" stroke-width="6"/>',
    gun: '<path d="M32 2v5M32 59v3M2 32h8M54 32h8" stroke="#efffff" stroke-width="4"/><path d="M24 9h16v26H24z" fill="#d1ebe6"/><path d="M22 9h20v8H22z" fill="#e9fbf3"/><path d="M18 33h28v18H18z" fill="#267a82"/><path d="M15 49h34v9H15z" fill="#e3f3d9"/>',
    reactor2: '<path d="M32 15V2m-7 7 7-7 7 7" stroke="#fff8cf" stroke-width="5"/><path d="m32 15 19 11v22L32 59 13 48V26z" fill="#c37124"/><circle cx="32" cy="37" r="14" fill="#ffe6a0"/><path d="m35 23-12 16h9l-3 12 13-18h-10z" fill="#fffef0" stroke-width="2"/><path d="M4 32h5m46 0h5M7 47l5-2m40 0 5 2" stroke="#fff8cf"/>',
    mirror2: '<path d="m10 49 4-17 25-25 18 18-25 25-17 4z" fill="#175c72"/><path d="m17 42 24-25 8 8-25 25z" fill="#d3ffff"/><path d="m17 42 7 8 17-33z" fill="#7cebd9" stroke-width="2"/><path d="M8 12v10M3 17h10M49 45v12m-6-6h12" stroke="#fff9d9" stroke-width="3"/>',
    amplifier2: '<path d="M32 3v7M32 54v7M3 32h7M54 32h7" stroke="#fff8cf"/><path d="m32 9 20 12v22L32 55 12 43V21z" fill="#fff0aa"/><path d="m21 29 11-11 11 11m-22 15 11-11 11 11" stroke="#ac6522" stroke-width="7"/>',
    splitter2: '<path d="M32 58V8M32 40 10 18m22 22 22-22" stroke="#efffff" stroke-width="7"/><path d="m24 15 8-8 8 8M10 29V17h12m20 0h12v12" stroke="#efffff" stroke-width="5"/><circle cx="32" cy="42" r="7" fill="#7251a6" stroke="#fff1b0"/>',
    splitter3: '<path d="M32 58V9M32 41 9 18m23 23 23-23" stroke="#fff1a0" stroke-width="9"/><path d="m25 16 7-8 7 8M9 29V17h12m22 0h12v12" stroke="#fff1a0" stroke-width="5"/><path d="m32 30 12 12-12 12-12-12z" fill="#7543a1" stroke="#fff8cf"/><path d="M28 39h8m-8 6h8" stroke="#fff8cf" stroke-width="3"/>',
    lens2: '<path d="M32 3v58" stroke="#efffff" stroke-width="6"/><path d="M8 20h48M8 32h48M8 44h48" stroke="#193e4d" stroke-width="10"/><path d="M8 20h48M8 32h48M8 44h48" stroke="#b8f4ff" stroke-width="5"/><path d="m25 10 7-7 7 7m-14 44 7 7 7-7" stroke="#efffff"/>',
    gun2: '<path d="M14 8h14v30H14zm22 0h14v30H36z" fill="#d7fcdf"/><path d="M12 8h18v8H12zm22 0h18v8H34z" fill="#fff5c4"/><path d="M12 35h40v19H12z" fill="#267a82"/><path d="M10 53h44v7H10z" fill="#fff5c4"/><path d="m26 41 6 7 6-7" stroke="#a8f4cb" stroke-width="4"/>',
    prism: '<path d="M32 3v9m0 40v9M3 32h9m40 0h9" stroke="#efffff"/><path d="m32 9 21 23-21 23-21-23z" fill="#c1f6ff"/><path d="m32 9 7 23-7 23-7-23z" fill="#57b4ee" stroke-width="2"/><circle cx="47" cy="46" r="11" fill="#ffe08a"/><path d="M47 40v12m-6-6h12" stroke="#8d6928" stroke-width="3"/>',
    prism2: '<path d="M32 2v8m0 46v6M2 32h6m48 0h6" stroke="#fff5c4"/><path d="m23 10 15 22-15 22L8 32z" fill="#8ce3f4"/><path d="m41 10 15 22-15 22-15-22z" fill="#e1faff"/><path d="m32 19-10 15h9l-3 13 15-19H32l4-9z" fill="#ffe291" stroke="#a27738" stroke-width="2.5"/><path d="M8 5v8M4 9h8m43 40v10m-5-5h10" stroke="#fff6c4" stroke-width="3"/>',
  };
  return `<svg viewBox="0 0 64 64" fill="none" stroke="#193e4d" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[type] || paths[PARTS[type]?.base] || ''}</svg>`;
}

export function tileMarkup(type, rotation = 0) {
  const part = PARTS[type];
  return `<span class="part-art part-${type}" style="--part:${part.color};--part-shadow:${part.ink}"><span class="part-symbol" style="transform:rotate(${part.rotatable ? rotation * 90 : 0}deg)">${partIcon(type)}</span><i></i><i></i>${part.tier ? `<b class="tier-badge">${part.tier === 3 ? 'III' : 'II'}</b>` : ''}</span>`;
}
