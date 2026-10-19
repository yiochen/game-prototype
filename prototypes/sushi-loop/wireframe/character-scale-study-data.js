// Each study image is a fixed-frame native Blender still. Production exports
// remain independent of this experiment.
const manifests = import.meta.glob('../assets/character-scale-study/study.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/character-scale-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
export const characterScaleStudy = Object.values(manifests)[0] || { schemaVersion: 1, cellSize: 128, sourceScale: 4, variants: [] };
export const characterVariants = characterScaleStudy.variants || [];
export const characterScales = ['100', '125', '150'].map(id => ({ id, factor: Number(id) / 100, ...characterScaleStudy.scales?.find(scale => String(scale.id) === id), label: `${id}%` }));
const relativePath = path => typeof path === 'string' && path && !path.startsWith('/') && !path.includes('\\') && !path.split('/').includes('..') ? path : null;
export function characterStudyImage(path) {
  const safe = relativePath(path);
  return safe ? images[`../assets/character-scale-study/${safe}`] || null : null;
}
export function characterStudySource(path) {
  const safe = relativePath(path);
  return safe ? `https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/character-scale-study/${safe.split('/').map(encodeURIComponent).join('/')}` : null;
}
const finiteArray = (value, length) => Array.isArray(value) && value.length === length && value.every(Number.isFinite);
export function characterStudyGeometry(variant) {
  const cell = characterScaleStudy.cellSize || 128;
  const frameSize = variant.frameSize || characterScaleStudy.frameSize;
  const root = variant.root || characterScaleStudy.root;
  if (!finiteArray(frameSize, 2) || frameSize.some(value => value <= 0) || !finiteArray(root, 2)) return null;
  return { cell, frameSize, root, bounds: [-root[0], -root[1], ...frameSize] };
}
export function characterScaleMeasurement(variant, scale) {
  return variant.scales?.[scale.id] || null;
}
