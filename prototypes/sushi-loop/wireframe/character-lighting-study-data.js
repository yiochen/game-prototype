// Isolated native Blender light experiment; no production sprite substitution.
const manifests = import.meta.glob('../assets/character-lighting-study/manifest.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/character-lighting-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
const environmentManifests = import.meta.glob('../assets/environment-lighting-study/manifest.json', { eager: true, import: 'default' });
const environmentImages = {
  ...import.meta.glob('../assets/environment-lighting-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' }),
  ...import.meta.glob('../assets/environment-lighting-study/frames/**/*.png', { eager: true, query: '?url', import: 'default' }),
};
const refinementManifests = import.meta.glob('../assets/faceted-material-refinement/manifest.json', { eager: true, import: 'default' });
const refinementImages = {
  ...import.meta.glob('../assets/faceted-material-refinement/sprites/**/*.png', { eager: true, query: '?url', import: 'default' }),
  ...import.meta.glob('../assets/faceted-material-refinement/frames/**/*.png', { eager: true, query: '?url', import: 'default' }),
};
export const lightingStudy = Object.values(manifests)[0] || { version: 1, character: { id: 'chef-noor', name: 'Noor' }, cellSize: 128, frame: [192, 320], root: [96, 248], captureScale: 4, directions: ['N', 'E', 'S', 'W'], variants: [] };
export const lightingVariants = lightingStudy.variants || [];
const environmentStudy = Object.values(environmentManifests)[0] || { subjects: [] };
const refinementStudy = Object.values(refinementManifests)[0];
const activeEnvironmentStudy = refinementStudy || environmentStudy;
const environmentRoot = refinementStudy ? 'faceted-material-refinement' : 'environment-lighting-study';
export const lightingSubjects = [
  { ...lightingStudy, id: lightingStudy.character?.id || 'chef-noor', name: 'Noor', description: 'Faceted is the chosen lighting treatment. The selected C125 anatomy, ordinary 35° character camera and green-hat surface comparison stay fixed.', selectedLighting: 'faceted', projection: 'character-orthographic', footprint: [1, 1], detailCrop: lightingStudy.hatCrop, detailLabel: 'Hat detail', studyRoot: 'character-lighting-study' },
  ...(activeEnvironmentStudy.subjects || []).map(subject => ({ ...subject, selectedLighting: subject.selectedLighting || activeEnvironmentStudy.selectedLighting || 'faceted', source: activeEnvironmentStudy.source, studyRoot: environmentRoot })),
];
export function lightingReviewVariants(subject) {
  const variants = subject.variants || [];
  return subject.reviewVariantIds?.length ? subject.reviewVariantIds.map(id => variants.find(variant => variant.id === id)).filter(Boolean) : variants;
}
const safePath = path => typeof path === 'string' && path && !path.startsWith('/') && !path.includes('\\') && !path.split('/').includes('..') ? path : null;
export function lightingImage(path, subject) {
  const safe = safePath(path);
  const root = subject?.studyRoot || 'character-lighting-study';
  const sourceImages = root === 'faceted-material-refinement' ? refinementImages : root === 'environment-lighting-study' ? environmentImages : images;
  return safe ? sourceImages[`../assets/${root}/${safe}`] || null : null;
}
export function lightingCapture(variant, direction) {
  const capture = variant.captures?.[direction];
  return typeof capture === 'string' ? { image: capture } : capture || null;
}
export function lightingSource(path, subject) {
  const safe = safePath(path);
  const root = subject?.studyRoot || 'character-lighting-study';
  return safe ? `https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/${root}/${safe.split('/').map(encodeURIComponent).join('/')}` : null;
}
