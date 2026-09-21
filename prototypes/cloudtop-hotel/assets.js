// Vite packages the game's own SVG art; Phaser and the HUD share stable keys.
const files = import.meta.glob('./assets/*.svg', { eager: true, query: '?url&no-inline', import: 'default' });
export const ART = Object.fromEntries(Object.entries(files).map(([path, url]) => [path.split('/').at(-1).replace('.svg', ''), url]));
