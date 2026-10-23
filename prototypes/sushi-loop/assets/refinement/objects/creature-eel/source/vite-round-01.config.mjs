import {defineConfig} from 'vite';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const source=path.dirname(fileURLToPath(import.meta.url));
export default defineConfig({cacheDir:path.join(source,'temporary-vite-cache'),server:{host:'127.0.0.1',port:5167,strictPort:true}});
