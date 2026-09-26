// Presentation only: altitude depends on constructed floors, never the camera.
export const SKY_STAGES = [
  { floor: 0, name: 'Cloud Gardens', color: '#398ecb' },
  { floor: 25, name: 'Cloud Sea', color: '#2c78bc' },
  { floor: 50, name: 'First Starlight', color: '#245ba6' },
  { floor: 75, name: 'Blue Twilight', color: '#233f87' },
  { floor: 100, name: 'Moonlit Heights', color: '#18265f' },
  { floor: 125, name: 'Constellation Skies', color: '#111a43' },
  { floor: 150, name: 'Celestial Summit', color: '#0b1230' },
];
export function ramp(from, to, height) {
  const t = Math.max(0, Math.min(1, (height - from) / (to - from)));
  return t * t * (3 - 2 * t);
}
export function skyAtHeight(value) {
  const height = Number.isFinite(value) ? Math.max(0, value) : 0;
  const index = Math.min(SKY_STAGES.length - 1, Math.floor(height / 25));
  const stage = SKY_STAGES[index], next = SKY_STAGES[Math.min(index + 1, SKY_STAGES.length - 1)];
  const t = ramp(stage.floor, stage.floor + 25, height);
  const rgb = color => color.match(/[\da-f]{2}/g).map(channel => parseInt(channel, 16));
  const start = rgb(stage.color), end = rgb(next.color);
  const color = '#' + start.map((channel, i) => Math.round(channel + (end[i] - channel) * t).toString(16).padStart(2, '0')).join('');
  return {
    height, stage, color,
    islandOpacity: 1 - ramp(12, 48, height),
    islandDrop: 48 * ramp(0, 48, height),
    islandScale: 1 - .46 * ramp(0, 48, height),
    // Leave the whole cloud layer below the hotel before the night-sky stages.
    cloudDrop: 65 * ramp(0, 75, height),
    cloudOpacity: 1 - ramp(20, 75, height),
    night: ramp(45, 125, height),
    seaOpacity: ramp(10, 25, height) * (1 - ramp(35, 75, height)),
    ribbonOpacity: .36 * ramp(115, 135, height),
  };
}
