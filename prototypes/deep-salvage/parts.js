const BASE_PARTS = {
  reactor: { name: 'Reactor', rotatable: true, color: '#ffad38', ink: '#a4531d', mark: 'CORE', description: 'The heart of your machine. Sends 8 energy in the direction it faces through empty space.', tip: 'Rotate to change its output. Keep at least one gun connected.', ports: 'One directional output', lesson: 'Power starts here.' },
  mirror: { name: 'Mirror', rotatable: true, color: '#55c7bf', ink: '#177f83', mark: 'TURN', description: 'Reflects a beam by 90°. Empty cells between parts are fine.', tip: 'Tap to flip the diagonal. Look at the beam to see where it goes.', ports: 'Reflects either side', lesson: 'Give your beam a new direction.' },
  amplifier: { name: 'Amplifier', color: '#f7c94e', ink: '#b58128', mark: '×1.5', description: 'Accepts beams from any side, multiplies their energy by 1.5, and sends them straight onward.', tip: 'Amplify before a split to strengthen both branches. No rotation needed.', ports: 'Any side → straight through', lesson: 'A little more punch.' },
  splitter: { name: 'Splitter', color: '#b79be8', ink: '#7251a6', mark: 'SPLIT', description: 'Accepts a beam from any side and splits it left and right relative to its incoming direction. Each branch gets half the energy.', tip: 'Send the branches into guns, or use mirrors to route them farther. No rotation needed.', ports: 'Any side → two perpendicular beams', lesson: 'One beam. Two possibilities.' },
  lens: { name: 'Lens', color: '#81bfee', ink: '#3d7dae', mark: 'PIERCE', description: 'Accepts beams from any side and passes them straight through. Makes shots pierce armor and strike a second enemy behind their target.', tip: 'Add it to a branch before the gun. No rotation needed.', ports: 'Any side → straight through', lesson: 'Go right through them.' },
  gun: { name: 'Gun', color: '#7bd6bc', ink: '#318d78', mark: 'FIRE', description: 'Accepts beams from all four sides and turns their energy into automatic shots at the nearest enemy.', tip: 'Every powered gun fires independently. Rotation does not affect its inputs.', ports: 'Inputs on all four sides', lesson: 'Your machine reaches the world.' },
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
  gun2: upgrade('gun', 'Heavy gun', '×1.6', 'Deals 1.6 times the incoming beam power per shot.'),
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
    gun: '<path d="M32 2v5M32 59v3M2 32h8M54 32h8" stroke="#efffff" stroke-width="4"/><path d="M24 9h16v26H24z" fill="#d1ebe6"/><path d="M22 9h20v8H22z" fill="#e9fbf3"/><path d="M18 33h28v18H18z" fill="#267a82"/><path d="M15 49h34v9H15z" fill="#e3f3d9"/>',
  };
  return `<svg viewBox="0 0 64 64" fill="none" stroke="#193e4d" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[PARTS[type]?.base || type] || ''}</svg>`;
}

export function tileMarkup(type, rotation = 0) {
  const part = PARTS[type];
  return `<span class="part-art part-${type}" style="--part:${part.color};--part-shadow:${part.ink}"><span class="part-symbol" style="transform:rotate(${part.rotatable ? rotation * 90 : 0}deg)">${partIcon(type)}</span><i></i><i></i>${part.tier ? `<b class="tier-badge">${part.tier === 3 ? 'III' : 'II'}</b>` : ''}</span>`;
}
