import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
const base=fileURLToPath(new URL('../..',import.meta.url));
export default defineConfig({root:base,cacheDir:base+'/candidates/round-01/browser/cache',server:{host:'127.0.0.1',port:5517,strictPort:true,fs:{allow:[base]}}});
