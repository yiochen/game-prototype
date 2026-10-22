import {build} from 'esbuild';
import path from 'node:path';
const p=path.dirname(new URL(import.meta.url).pathname);
await build({entryPoints:[path.join(p,'consumer-entry.js')],outfile:path.join(p,'consumer-bundle.js'),bundle:true,format:'esm',platform:'browser',target:'es2022',logLevel:'warning'});
