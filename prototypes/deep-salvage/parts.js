export const PARTS = Object.freeze({
  reactor: { name: 'Reactor', color: '#ffad38', ink: '#a4531d', mark: 'CORE', description: 'The heart of your machine. Sends 8 energy upward through empty space.', tip: 'Rotate to change its output. Keep at least one gun connected.', ports: 'One output', lesson: 'Power starts here.' },
  mirror: { name: 'Mirror', color: '#55c7bf', ink: '#177f83', mark: 'TURN', description: 'Reflects a beam by 90°. Empty cells between parts are fine.', tip: 'Tap to flip the diagonal. Look at the beam to see where it goes.', ports: 'Reflects either side', lesson: 'Give your beam a new direction.' },
  amplifier: { name: 'Amplifier', color: '#f7c94e', ink: '#b58128', mark: '×1.5', description: 'Multiplies incoming energy by 1.5. More energy means harder-hitting shots.', tip: 'Amplify before a split to strengthen both branches.', ports: 'Bottom → top', lesson: 'A little more punch.' },
  splitter: { name: 'Splitter', color: '#b79be8', ink: '#7251a6', mark: 'SPLIT', description: 'Splits one beam into two. Each branch gets half the incoming energy.', tip: 'Place mirrors beside it to turn the branches toward two guns.', ports: 'Bottom → left + right', lesson: 'One beam. Two possibilities.' },
  lens: { name: 'Lens', color: '#81bfee', ink: '#3d7dae', mark: 'PIERCE', description: 'Makes shots pierce armor and strike a second enemy behind their target.', tip: 'Add it to a branch before the gun. Watch for the blue piercing shots.', ports: 'Bottom → top', lesson: 'Go right through them.' },
  gun: { name: 'Gun', color: '#7bd6bc', ink: '#318d78', mark: 'FIRE', description: 'Turns beam energy into automatic shots at the nearest enemy.', tip: 'Every powered gun fires independently. The inlet must face the beam.', ports: 'One input', lesson: 'Your machine reaches the world.' },
});

// Icons use a common 64-unit square and point upward before rotation.
export function partIcon(type) {
  const paths = {
    reactor: '<circle cx="32" cy="32" r="18" fill="#fce6a3"/><circle cx="32" cy="32" r="10" fill="#fff9d9"/><path d="M32 4v7M32 53v7M4 32h7M53 32h7"/>',
    mirror: '<path d="M13 49 49 13" stroke="#183c4c" stroke-width="13"/><path d="M13 46 46 13" stroke="#ecfcf5" stroke-width="8"/><path d="m15 17 7 7m20 19 7 7" stroke="#e7fffa" stroke-width="2"/>',
    amplifier: '<path d="m17 34 15-15 15 15M17 48l15-15 15 15" fill="none" stroke="#fff4bf" stroke-width="8"/><path d="M32 5v7M32 55v5"/>',
    splitter: '<path d="M32 59V32M32 32H6M32 32h26" fill="none" stroke="#efffff" stroke-width="9"/><path d="m13 24-8 8 8 8m38-16 8 8-8 8" fill="none" stroke="#efffff" stroke-width="4"/>',
    lens: '<ellipse cx="32" cy="32" rx="14" ry="22" fill="#c2f8ff"/><ellipse cx="32" cy="32" rx="8" ry="17" fill="#54c6ec" stroke="none"/><path d="m29 21-3 10" stroke="white" stroke-width="3"/><path d="M32 3v6M32 55v6"/>',
    gun: '<path d="M24 9h16v26H24z" fill="#d1ebe6"/><path d="M22 9h20v8H22z" fill="#e9fbf3"/><path d="M18 33h28v18H18z" fill="#267a82"/><path d="M15 49h34v9H15z" fill="#e3f3d9"/><path d="M32 59v4"/>',
  };
  return `<svg viewBox="0 0 64 64" fill="none" stroke="#193e4d" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[type] || ''}</svg>`;
}

export function tileMarkup(type, rotation = 0) {
  const part = PARTS[type];
  return `<span class="part-art part-${type}" style="--part:${part.color};--part-shadow:${part.ink}"><span class="part-symbol" style="transform:rotate(${rotation * 90}deg)">${partIcon(type)}</span><i></i><i></i></span>`;
}
