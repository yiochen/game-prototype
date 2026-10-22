import {build} from 'esbuild';import {writeFileSync} from 'node:fs';
const result=await build({entryPoints:[new URL('browser-entry.js',import.meta.url).pathname],outfile:new URL('browser-bundle.js',import.meta.url).pathname,bundle:true,format:'esm',platform:'browser',metafile:true,minify:false});
writeFileSync(new URL('browser-build-meta.json',import.meta.url),JSON.stringify({esbuild:(await import('esbuild')).version,metafile:result.metafile},null,2)+'\n');
