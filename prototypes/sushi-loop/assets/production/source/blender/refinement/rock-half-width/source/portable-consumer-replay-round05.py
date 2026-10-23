"""Replay exact consumer in isolated staging using only retained module/helper bytes."""
import pathlib,json,hashlib,shutil,tempfile,subprocess,os
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
main=json.loads((O/'consumer/record.json').read_text());base=pathlib.Path(tempfile.mkdtemp(prefix='rock-half-width-round05-portable-')).resolve();Q=base/'prototypes/sushi-loop/assets/refinement/objects/rock-half-width';Q.mkdir(parents=True)
inputs=['source/capture-consumer-round05.mjs','source/consumer-round05.html','inputs/root-preparation-reconciliation-v1.json','inputs/catalog-object.json']+[f'candidates/round-05/atlases/static-{d}.png' for d in 'NESW']+['source/round-01-resources/'+n for n in ['sprite-layout.js','world-sprite-raster.js']]
inputs+=list(dict.fromkeys(q['path'] for q in main['actualLoadedNodeDependencyClosure']))
inputs.append(main['playwrightVersionPackage']['path']);copied=[]
for n in dict.fromkeys(inputs):
 src=P/n;dest=Q/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);assert sha(src)==sha(dest);copied.append({'path':n,'sha256':sha(src)})
for n in ['sprite-layout.js','world-sprite-raster.js']:
 dest=Q.parents[3]/'wireframe'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(P/'source/round-01-resources'/n,dest)
node=shutil.which('node');assert node;node_record=next(q for q in main['executables'] if pathlib.Path(q['path']).resolve()==pathlib.Path(node).resolve());assert sha(pathlib.Path(node))==node_record['sha256']
env=dict(os.environ,NODE_PATH=str(Q/'source/round-01-resources/node-loaded'),PYTHONDONTWRITEBYTECODE='1',DEBUG='pw:browser')
log=Q/'portable-consumer.log'
with log.open('w') as stream:subprocess.run([node,str(Q/'source/capture-consumer-round05.mjs')],cwd=Q,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
x=json.loads((Q/'candidates/round-05/consumer/record.json').read_text());assert len(x['runs'])==8 and all(not q['errors'] for q in x['runs']);snapshots={q['path']:q['sha256'] for q in main['actualLoadedNodeDependencyClosure']}
for q in x['actualLoadedNodeDependencyClosure']:
 assert pathlib.Path(q['originalPath']).is_relative_to(Q/'source/round-01-resources/node-loaded'),'Unexpected external module resolution'
 assert q['path'] in snapshots and q['sha256']==snapshots[q['path']]
main_runs={(r['id'],r['case']['id']):r for r in main['runs']};aliases=[];canvas_matches=0
for r in x['runs']:
 m=main_runs[(r['id'],r['case']['id'])];assert r['launchOptions']==m['launchOptions'] and r['case']==m['case'] and r['viewport']==m['viewport'] and r['DPR']==m['DPR'] and r['browserVersion']==m['browserVersion']
 a=Q/r['screenshot'];b=P/m['screenshot'];assert sha(a)==sha(b),'Portable screenshot differs';aliases.append({'portableRelativePath':r['screenshot'],'retainedPath':m['screenshot'],'sha256':sha(b)})
 for u,v in zip(r['records'],m['records']):
  assert u['nativeCanvasSHA256']==v['nativeCanvasSHA256'] and sha(Q/'candidates/round-05/consumer'/u['nativeCanvasFile'])==v['nativeCanvasSHA256'];canvas_matches+=1
  aliases.append({'portableRelativePath':'candidates/round-05/consumer/'+u['nativeCanvasFile'],'retainedPath':'candidates/round-05/consumer/'+v['nativeCanvasFile'],'sha256':v['nativeCanvasSHA256']})
assert {q['sha256'] for q in x['executables']}=={q['sha256'] for q in main['executables']}
assert x['playwrightVersionPackage']['sha256']==main['playwrightVersionPackage']['sha256']
D=O/'diagnostics';D.mkdir(exist_ok=True);shutil.copy2(log,D/'portable-consumer.log');shutil.copy2(Q/'candidates/round-05/consumer/record.json',D/'portable-consumer-record.json')
write(O/'portable-consumer-replay.json',{'scope':'Actual isolated consumer replay from only retained module/helper/input/atlas bytes, using exact external executables; no aesthetic approval. No duplicate replay PNGs frozen: exact byte aliases below retain every replay image.','privateStagingRoot':str(Q),'allPackagesResolvedFromRetainedSnapshots':True,'loadedModuleCount':len(x['actualLoadedNodeDependencyClosure']),'copiedInputs':copied,'prescribedRuns':8,'pageErrors':[],'exactScreenshotPNGMatches':8,'nativeCanvasRecordMatches':canvas_matches,'imageAliases':aliases,'actualRecord':'candidates/round-05/diagnostics/portable-consumer-record.json','actualLog':'candidates/round-05/diagnostics/portable-consumer.log','externalExecutableHashesMatchPrimaryCapture':True})
print(json.dumps({'privateStagingRoot':str(Q),'runs':8,'screenshotsByteExact':8,'nativeCanvasRecordsByteExact':canvas_matches,'loadedPrivateModules':len(x['actualLoadedNodeDependencyClosure'])}))
