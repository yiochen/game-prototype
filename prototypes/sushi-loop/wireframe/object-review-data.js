// Vite fingerprints every actual export. Queued objects never fall back to concept crops.
const libraries = import.meta.glob('../assets/production/library.json', { eager: true, import: 'default' });
const images = import.meta.glob('../assets/production/sprites/**/*.png', { eager: true, query: '?url', import: 'default' });
export const spriteLibrary = libraries['../assets/production/library.json'] || { version: 1, cellSize: 128, objects: [] };
export const libraryObjects = spriteLibrary.objects || [];
export const finalAssetsApproved = spriteLibrary.approval?.finalAssets === 'approved';
export const productionArtStatus = finalAssetsApproved ? 'Approved production art · Faceted lighting · matte wood · muted clay rails' : 'Art direction approved · native Faceted rollout in progress';
export function imageUrl(path) {
  if (!path || path.includes('..')) return null;
  const relative = path.replace(/^\/?(?:assets\/production\/)?/, '');
  return images[`../assets/production/${relative}`] || null;
}
export function objectStoryId(object) { return `object-${object.id}`; }
export const objectReviewStories = [
  {
    id: 'object-library', group: 'asset-review', title: 'Production object library · #33', scene: 'object-review',
    reviewBranch: 'codex/sushi-loop-33-art-catalog',
    description: 'Inspect the registered native and 2D sprites. Every object has a separate review page with cardinal facings, square-grid repetition, interaction scale comparisons and all animation clips.',
    elements: [
      { name: 'Production status', behavior: 'Only real registered exports appear as object sprites. Queued work stays explicitly labeled. Review pages are stable deep links and keep their own Comments context.', motion: 'Presentation time only. No service or expedition simulation runs here.' },
    ],
    notes: [productionArtStatus, 'The catalog is a browser review surface; the game target remains Godot Android.'],
  },
  ...libraryObjects.map(object => ({
    id: objectStoryId(object), group: 'asset-review', title: `${object.name} · ${object.family}`, scene: 'object-review', objectId: object.id,
    reviewBranch: 'codex/sushi-loop-33-art-catalog',
    description: `Review ${object.name} at the registered cell scale. Compare the declared facings, repeated copies and related objects, then play or scrub every exported state.`,
    elements: [
      { name: 'Fixed grid and ground root', behavior: 'Sprite bounds, ground root and cell pitch come from the production manifest. No silhouette fitting, per-pose resizing or turning a single image in CSS. Overlays show the root and declared footprint.', motion: 'The camera and scale stay fixed within each view. Zoom changes the complete scene uniformly.' },
      { name: 'All clips and directions', behavior: 'Each state is shown N/E/S/W side by side. Missing exports stay labeled; static directions remain static. Pause and scrub inspect the exact exported frames.', motion: 'Single-facing signs remain player-facing. 2D effects use their authored flat artwork. 12 fps sprite timing. Reduced-motion preferences start playback paused. Hidden tabs pause presentation time.' },
      { name: 'Interaction scale', behavior: 'Related assets share one cell size. Seated and supported objects use recorded placement/attachments. Decks render before food and characters.', motion: 'Manually staged visual comparison only, with no gameplay rules or economy.' },
    ],
    notes: ['Use Comments for this specific object; the URL retains the object identity.', productionArtStatus],
  })),
];
