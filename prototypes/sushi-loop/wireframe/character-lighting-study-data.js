// Isolated native Blender light experiment; no production sprite substitution.
const manifests = import.meta.glob('../assets/character-lighting-study/manifest.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/character-lighting-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
const environmentManifests = import.meta.glob('../assets/environment-lighting-study/manifest.json', { eager: true, import: 'default' });
const environmentImages = {
  ...import.meta.glob('../assets/environment-lighting-study/sprites/**/*.png', { eager: true, query: '?url', import: 'default' }),
  ...import.meta.glob('../assets/environment-lighting-study/frames/**/*.png', { eager: true, query: '?url', import: 'default' }),
};
export const lightingStudy = Object.values(manifests)[0] || { version: 1, character: { id: 'chef-noor', name: 'Noor' }, cellSize: 128, frame: [192, 320], root: [96, 248], captureScale: 4, directions: ['N', 'E', 'S', 'W'], variants: [] };
export const lightingVariants = lightingStudy.variants || [];
const environmentStudy = Object.values(environmentManifests)[0] || { subjects: [] };
export const lightingSubjects = [
  { ...lightingStudy, id: lightingStudy.character?.id || 'chef-noor', name: 'Noor', description: 'Compare the green beret’s bright top and darker sides while keeping the face clear. The selected C125 anatomy and ordinary 35° character camera stay fixed.', projection: 'character-orthographic', footprint: [1, 1], detailCrop: lightingStudy.hatCrop, detailLabel: 'Hat detail', studyRoot: 'character-lighting-study' },
  ...(environmentStudy.subjects || []).map(subject => ({ ...subject, source: environmentStudy.source, studyRoot: 'environment-lighting-study' })),
];
const safePath = path => typeof path === 'string' && path && !path.startsWith('/') && !path.includes('\\') && !path.split('/').includes('..') ? path : null;
export function lightingImage(path, subject) {
  const safe = safePath(path);
  const root = subject?.studyRoot || 'character-lighting-study';
  return safe ? (root === 'environment-lighting-study' ? environmentImages : images)[`../assets/${root}/${safe}`] || null : null;
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
