import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
const own = fileURLToPath(new URL('.', import.meta.url));
export default defineConfig({ root: own, cacheDir: own + '/vite-cache', server: { host:'127.0.0.1', port:5473, strictPort:true, fs:{allow:[own]} } });
