/* NEW reproduction wrapper, not part of the original historic browser driver. */
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const BASE=__dirname,REV=path.dirname(BASE),OUT=process.argv[2];if(!OUT||!path.isAbsolute(OUT))throw Error('Pass an absolute NEW output directory');if(fs.existsSync(OUT))throw Error('Output already exists; preserve all previous evidence');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const index=JSON.parse(fs.readFileSync(path.join(BASE,'original-execution-index.json'),'utf8'));
function copy(src,dst){fs.mkdirSync(path.dirname(dst),{recursive:true});fs.copyFileSync(src,dst);}
for(const record of index.files.filter(r=>r.originalPath.endsWith('.cjs'))){const src=path.join(REV,'..',record.originalPath);if(sha(src)!==record.sha256)throw Error('Changed original driver '+src);const relative=path.relative(REV,src);copy(src,path.join(OUT,relative));}
for(const name of ['world-sprite-raster.js','sprite-layout.js','host.html'])copy(path.join(REV,'preparation-v1/resources/consumer',name),path.join(OUT,'preparation-v1/resources/consumer',name));
copy(path.join(REV,'preparation-v1/resources/object/inputs/catalog-object.json'),path.join(OUT,'preparation-v1/resources/object/inputs/catalog-object.json'));
for(const folder of ['preparation-v1/evidence','preparation-v1/evidence/study-filter001','preparation-v2/evidence/study-filter05','preparation-v2/evidence/study-direct2x-filter001'])for(const d of ['N','E','S','W'])for(const name of ['single','three-joined']){const rel=`${folder}/packed/${name}-${d}/sheet.png`;copy(path.join(REV,rel),path.join(OUT,rel));}
let project=BASE;while(!fs.existsSync(path.join(project,'node_modules/@playwright/test'))) {const up=path.dirname(project);if(up===project)throw Error('Project Playwright installation not found');project=up;}
const env={...process.env,NODE_PATH:[path.join(project,'node_modules'),process.env.NODE_PATH].filter(Boolean).join(path.delimiter)};
for(const relative of ['preparation-v1/capture_consumer.cjs','preparation-v1/capture_consumer_study.cjs','preparation-v2/consumer_root_pan.cjs','preparation-v2/consumer_direct2x.cjs']){const file=path.join(OUT,relative);const r=cp.spawnSync(process.execPath,[file],{cwd:project,env,encoding:'utf8',maxBuffer:20*1024*1024});fs.writeFileSync(file+'.reproduction.log',String(r.stdout||'')+String(r.stderr||''));if(r.status!==0)throw Error('Reproduction failed: '+relative);}
console.log('Original exact drivers reproduced only into fresh output: '+OUT);
