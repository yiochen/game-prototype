import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
const here=fileURLToPath(new URL('.',import.meta.url)),object=fileURLToPath(new URL('../../',import.meta.url));
export default defineConfig({root:object,cacheDir:here+'/browser-cache',server:{host:'127.0.0.1',port:5521,strictPort:true,fs:{allow:[object]}}});
