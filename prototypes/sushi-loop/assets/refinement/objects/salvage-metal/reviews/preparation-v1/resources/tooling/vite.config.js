import { defineConfig } from 'vite';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const catalog = JSON.parse(readFileSync(new URL('./prototypes.json', import.meta.url), 'utf8'));
const input = { index: fileURLToPath(new URL('./index.html', import.meta.url)) };
for (const { slug } of catalog) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || input[slug]) throw new Error(`Invalid or duplicate prototype slug: ${slug}`);
  input[slug] = fileURLToPath(new URL(`./prototypes/${slug}/index.html`, import.meta.url));
}
export default defineConfig({ base: './', build: { rollupOptions: { input } } });
