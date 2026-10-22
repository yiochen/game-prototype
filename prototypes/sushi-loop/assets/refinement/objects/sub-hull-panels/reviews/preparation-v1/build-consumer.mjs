import * as esbuild from './resources/tools/node_modules/esbuild/lib/main.js';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const out=path.dirname(new URL(import.meta.url).pathname),root=path.resolve(out,'../../../../../../../../..');
const result=await esbuild.build({entryPoints:[path.join(out,'consumer-demo.jsx')],bundle:true,format:'esm',platform:'browser',outfile:path.join(out,'consumer-demo.js'),metafile:true,define:{'process.env.NODE_ENV':'"production"'},minify:true,alias:{'react':path.join(out,'resources/npm/react/index.js'),'react-dom':path.join(out,'resources/npm/react-dom/index.js'),'react-dom/client':path.join(out,'resources/npm/react-dom/client.js'),'scheduler':path.join(out,'resources/npm/scheduler/index.js')}});
const records=[];
for(const name of Object.keys(result.metafile.inputs)){
 const original=path.resolve(name);if(original.includes('/resources/npm/')){records.push({source:original,snapshot:path.relative(out,original),sha256:crypto.createHash('sha256').update(fs.readFileSync(original)).digest('hex'),bytes:fs.statSync(original).size});continue;}if(!original.includes('/node_modules/'))continue;
 const relative=original.split('/node_modules/')[1],snapshot=path.join(out,'resources/npm',relative);
 fs.mkdirSync(path.dirname(snapshot),{recursive:true});fs.copyFileSync(original,snapshot);records.push({source:original,snapshot:path.relative(out,snapshot),sha256:crypto.createHash('sha256').update(fs.readFileSync(snapshot)).digest('hex'),bytes:fs.statSync(snapshot).size});
}
fs.copyFileSync(path.resolve('prototypes/sushi-loop/wireframe/object-review.jsx'),path.join(out,'resources/consumer/object-review.jsx'));
for(const name of ['package.json','package-lock.json'])if(fs.existsSync(name))fs.copyFileSync(name,path.join(out,'resources/consumer',name));
fs.writeFileSync(path.join(out,'consumer-build-manifest.json'),JSON.stringify({esbuildVersion:esbuild.version,nodeVersion:process.version,dependencies:records,metafile:result.metafile,scope:'Snapshot hook/layout replay with original SpriteScene registration algorithm; custom preparation harness and static frozen main fixture. Production page controls/backdrop are outside this bounded check.'},null,2));
console.log('CONSUMER_BUILD',records.length);
