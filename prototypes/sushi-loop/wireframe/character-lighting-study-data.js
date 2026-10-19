// Isolated native Blender light experiment; no production sprite substitution.
const manifests = import.meta.glob('../assets/character-lighting-study/manifest.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/character-lighting-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
export const lightingStudy = Object.values(manifests)[0] || { version: 1, character: { id: 'chef-noor', name: 'Noor' }, cellSize: 128, frame: [192, 320], root: [96, 248], captureScale: 4, directions: ['N', 'E', 'S', 'W'], variants: [] };
export const lightingVariants = lightingStudy.variants || [];
const safePath = path => typeof path === 'string' && path && !path.startsWith('/') && !path.includes('\\') && !path.split('/').includes('..') ? path : null;
export function lightingImage(path) {
  const safe = safePath(path);
  return safe ? images[`../assets/character-lighting-study/${safe}`] || null : null;
}
export function lightingCapture(variant, direction) {
  const capture = variant.captures?.[direction];
  return typeof capture === 'string' ? { image: capture } : capture || null;
}
export function lightingSource(path) {
  const safe = safePath(path);
  return safe ? `https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/character-lighting-study/${safe.split('/').map(encodeURIComponent).join('/')}` : null;
}
