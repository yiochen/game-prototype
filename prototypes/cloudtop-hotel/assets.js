// Keep generated sheets intact. Phaser frames and DOM clipping share this manifest.
const files = import.meta.glob(['./assets/sprites/*.webp', '!./assets/sprites/sky.webp'], { eager: true, query: '?url&no-inline', import: 'default' });
export const ART = Object.fromEntries(Object.entries(files).map(([path, url]) => [path.split('/').at(-1).replace('.webp', ''), url]));
// Uneven generated scenery bounds, with two pixels of alpha padding. Keeping
// source coordinates avoids resampling or clipping the tall paper waterfalls.
export const SCENERY = { width: 1536, height: 1024, frames: [
  [51, 41, 435, 542], [577, 68, 412, 513], [1087, 100, 385, 460],
  [24, 662, 494, 281], [573, 686, 396, 256], [1032, 646, 480, 302],
] };
export const SHEETS = {
  'rooms-bunny': { columns: 4, rows: 2 },
  'rooms-frog': { columns: 4, rows: 2 },
  'rooms-cat': { columns: 4, rows: 2 },
  actors: { columns: 4, rows: 4 },
  props: { columns: 4, rows: 2 },
  'card-powers': { columns: 4, rows: 2 },
  'card-types': { columns: 3, rows: 2 },
};
const types = ['bunny', 'frog', 'cat'];
const props = ['cloud', 'island', 'platform', 'roof', 'parcel', 'charm', 'coin', 'heart'];
export function spriteArt(key) {
  const power = ['choice', 'mystery', 'overgrow', 'assembler', 'stabilizer', 'vault', 'rebate', 'foundation'].indexOf(key.replace('power-', ''));
  if (key.startsWith('power-') && power >= 0) return { sheet: 'card-powers', frame: power };
  const typeCard = key.match(/^(pattern|lock)-(bunny|frog|cat)$/);
  if (typeCard) return { sheet: 'card-types', frame: types.indexOf(typeCard[2]) + (typeCard[1] === 'lock' ? 3 : 0) };
  if (props.includes(key)) return { sheet: 'props', frame: props.indexOf(key) };
  if (key === 'copycat') return { sheet: 'actors', frame: 0 };
  if (key.startsWith('balloon-')) return { sheet: 'actors', frame: (types.indexOf(key.slice(8)) + 1) * 4 };
  const match = key.match(/^(resident|box)-(bunny|frog|cat)(?:-(\d))?$/);
  if (match) return { sheet: `rooms-${match[2]}`, frame: match[1] === 'box' ? 0 : 3 + Math.min(4, Number(match[3] || 0)) };
  throw new Error(`Unknown hotel art: ${key}`);
}

// Frame metadata excludes transparent gutters and vines from the tile bounds,
// allowing complete facades to meet exactly without editing the source PNGs.
export function registerFrames(scene) {
  for (const [key, { columns, rows }] of Object.entries(SHEETS)) {
    const texture = scene.textures.get(key), source = texture.getSourceImage();
    const canvas = document.createElement('canvas'); canvas.width = source.width; canvas.height = source.height;
    const context = canvas.getContext('2d', { willReadFrequently: true }); context.drawImage(source, 0, 0);
    for (let frame = 0; frame < columns * rows; frame++) {
      let x = Math.round(frame % columns * source.width / columns), y = Math.round(Math.floor(frame / columns) * source.height / rows);
      let width = Math.round((frame % columns + 1) * source.width / columns) - x;
      let height = Math.round((Math.floor(frame / columns) + 1) * source.height / rows) - y;
      if ((key.startsWith('rooms-') && frame >= 3) || key === 'props') {
        const pixels = context.getImageData(x, y, width, height).data;
        const denseX = [], denseY = [];
        for (let cy = 0; cy < height; cy++) {
          let count = 0;
          for (let cx = 0; cx < width; cx++) if (pixels[(cy * width + cx) * 4 + 3] > 180) count++;
          if (count > width * (key === 'props' ? .035 : .55)) denseY.push(cy);
        }
        for (let cx = 0; cx < width; cx++) {
          let count = 0;
          for (let cy = 0; cy < height; cy++) if (pixels[(cy * width + cx) * 4 + 3] > 180) count++;
          if (count > height * (key === 'props' ? .035 : .55)) denseX.push(cx);
        }
        if (denseX.length && denseY.length) {
          x += denseX[0]; y += denseY[0]; width = denseX.at(-1) - denseX[0] + 1; height = denseY.at(-1) - denseY[0] + 1;
        }
      }
      texture.add(frame, 0, x, y, width, height);
    }
  }
}
