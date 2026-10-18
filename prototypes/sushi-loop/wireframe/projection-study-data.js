// Experimental captures have their own manifest and runtime PNGs. Production
// library registrations and sprites are deliberately independent of this study.
const manifests = import.meta.glob('../assets/projection-study/study.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/projection-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
const manifest = Object.values(manifests)[0];
export const projectionStudy = manifest || { schemaVersion: 1, cellSize: 128, groups: [], ratios: [] };
export const projectionRatios = ['100', '70', '50', '40'].map(id => ({
  id,
  heightScale: Number(id) / 100,
  ...projectionStudy.ratios?.find(ratio => String(ratio.id) === id),
  label: `${id}%`,
}));
export const projectionGroups = (projectionStudy.groups || []).map(group => {
  const cell = projectionStudy.cellSize || 128;
  const ground = group.groundRoot || [0, 0];
  // Native gridOrigin is a logical-pixel point inside the capture canvas.
  // Convert it through the registered root before drawing a world-cell grid.
  const gridBounds = group.gridBounds || (group.gridOrigin && group.gridSize && group.root ? [
    (group.gridOrigin[0] - group.root[0]) / cell + ground[0],
    (group.gridOrigin[1] - group.root[1]) / cell + ground[1],
    ...group.gridSize,
  ] : undefined);
  return { ...group, gridBounds };
});
const finiteArray = (value, length) => Array.isArray(value) && value.length === length && value.every(Number.isFinite);
const relativePath = path => typeof path === 'string' && path && !path.startsWith('/') && !path.includes('\\') && !path.split('/').includes('..') ? path : null;
export function studyImageUrl(path) {
  const safe = relativePath(path);
  return safe ? images[`../assets/projection-study/${safe}`] || null : null;
}
export function studySourceUrl(path) {
  const safe = relativePath(path);
  return safe ? `https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/projection-study/${safe.split('/').map(encodeURIComponent).join('/')}` : null;
}
export function studyGeometry(group, reference = false) {
  const entry = reference ? { ...group, ...group.reference } : group;
  const { frameSize, root, gridBounds } = entry;
  const groundRoot = entry.groundRoot || [0, 0];
  const cell = projectionStudy.cellSize || 128;
  if (!finiteArray(frameSize, 2) || !frameSize.every(value => value > 0) || !finiteArray(root, 2) || !finiteArray(groundRoot, 2) || !finiteArray(gridBounds, 4) || gridBounds[2] <= 0 || gridBounds[3] <= 0) return null;
  const imageX = groundRoot[0] * cell - root[0], imageY = groundRoot[1] * cell - root[1];
  const minX = Math.min(gridBounds[0] * cell, imageX), minY = Math.min(gridBounds[1] * cell, imageY);
  const maxX = Math.max((gridBounds[0] + gridBounds[2]) * cell, imageX + frameSize[0]);
  const maxY = Math.max((gridBounds[1] + gridBounds[3]) * cell, imageY + frameSize[1]);
  return { cell, frameSize, root, groundRoot, gridBounds, imageX, imageY, bounds: [minX, minY, maxX - minX, maxY - minY] };
}
