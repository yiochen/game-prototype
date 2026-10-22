import * as esbuild from './resources/tools/node_modules/esbuild/lib/main.js';
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const out=path.dirname(new URL(import.meta.url).pathname);
const result=await esbuild.build({entryPoints:[path.join(out,'consumer-demo.jsx')],bundle:true,format:'esm',platform:'browser',outfile:path.join(out,'consumer-demo.js'),metafile:true,define:{'process.env.NODE_ENV':'"production"'},minify:true,alias:{react:path.join(out,'resources/npm/react/index.js'),'react-dom':path.join(out,'resources/npm/react-dom/index.js'),'react-dom/client':path.join(out,'resources/npm/react-dom/client.js'),scheduler:path.join(out,'resources/npm/scheduler/index.js')}});
const inputs=Object.keys(result.metafile.inputs).map(p=>path.resolve(p));
fs.writeFileSync(path.join(out,'consumer-build-manifest.json'),JSON.stringify({node:process.version,esbuild:esbuild.version,inputs:inputs.map(p=>({path:path.relative(out,p),sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')})),scope:'Exact snapshotted real layout and native common-canvas hook, candidate atlas descriptors and static native assembled frozen-main fixture.'},null,2));
console.log('BUILT',inputs.length);
