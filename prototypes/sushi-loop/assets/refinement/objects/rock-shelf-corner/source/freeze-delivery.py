"""Freeze an editor handoff. Root seals candidate packet and original judge reviews.
This manifest is evidence of identity, not aesthetic/technical self-approval.
"""
import sys,json,hashlib,platform,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates/round-01';D=EXP/'delivery/round-01';D.mkdir(parents=True,exist_ok=True)
if (D/'seal.json').exists():raise SystemExit('Immutable editor delivery already exists')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def record(p):return {'path':p.relative_to(EXP).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
brief=EXP/'brief-v2-native-normal-equivalence.json';contract=EXP/'inputs/root-native-contract-v2-rendered-normal-equivalence.json'
assert sha(brief)=='7c04c79d1634b3be2799b39e32709f3fa5982cc9299e54ab209901212f30c51f'
assert sha(contract)=='4c03fc7161a5730e1d52ee32d68ae9970187457ec59426b61c4f854a368824be'
assert sha(BASE/'dependencies/canonical-middle.blend')=='3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422'
validation=json.loads((OUT/'validation.json').read_text());assert validation['sourceSHA256']==sha(BASE/'round-01.blend')
assert validation['topology']['boundaryEdges']==validation['topology']['nonmanifoldEdges']==validation['topology']['zeroAreaFaces']==0
assert validation['briefSHA256']==sha(brief) and validation['contractSHA256']==sha(contract)
consumer=json.loads((OUT/'evidence/consumer/results.json').read_text());assert not consumer['pageErrors']
assert consumer['currentHelpers']=={'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
previews={'four-view-sheet':'four-view-native.png','repeated':'consumer-L-all4.png','single-use-sizes':'single-use-sizes.png','isolated-W':'consumer-W-all4.png','isolated-N':'consumer-N-all4.png','consumer-phases':'consumer-phases-all4.png','native-vs-consumer':'native-vs-consumer-all4.png','cap-field':'cap-field-sheet.png','collar-shader-normal-all-roots':'collar-shader-normal-all-roots.png','collar-shader-albedo-all-roots':'collar-shader-albedo-all-roots.png'}
sourcefiles=[p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts];resources=[record(p) for p in sorted(sourcefiles)]
delivery={'asset':'rock-shelf-corner','round':'round-01','status':'editor immutable handoff; root packet and original independent judge pending','brief':record(brief),'nativeContract':record(contract),'project':'source/round-01.blend','recipeScript':'source/reproduce.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':{d:f'candidates/round-01/frames/static/{d}/000.png' for d in 'NESW'},'previews':{name:'candidates/round-01/'+p for name,p in previews.items()},'rawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/frames/static/{d}/000.png'} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/native/static/{d}/000.png'} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-01/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW'],'resourcePathBase':'object root','resources':resources,'canonicalDependency':{'source':record(BASE/'dependencies/canonical-middle.blend'),'packet':record(EXP/'reviews/preparation-v1/resources/canonical/packet.json')},'publication':'Native4x 768x1408, filter.5, complete-frame BOX reduction to2x384x704. No warp, fit, overlap, per-view grade, RGB/alpha repair or runtime change.','normalImplementation':'Exact original native band triangles clipped to .025; preserve raw affine CORNER vector field; Object→World VECTOR; normalize after interpolation; clone canonical body material behavior. Geometric codec field reported separately. Cap behavior retained with N transverse=-localX.','consumer':{'browser':consumer['browser'],'dpr':consumer['devicePixelRatio'],'caseCount':len(consumer['cases']),'helpers':consumer['currentHelpers'],'evidence':'candidates/round-01/evidence/consumer/results.json'},'reviewLimit':'No self-approval, production promotion, family approval, Git or publication. Actual visual continuity remains original independent judge gate.'}
for p in delivery['heroes'].values():assert (EXP/p).is_file()
for p in delivery['previews'].values():assert (EXP/p).is_file()
dump(D/'delivery.json',delivery)
commands=[{'command':['/opt/homebrew/bin/blender','--background','--factory-startup','--python','source/'+p,*args],'log':'candidates/round-01/'+log} for p,log,args in [('build-round-01.py','build-capture.log',['--','capture']),('capture-evidence.py','capture-evidence.log',[]),('measure-collars.py','collar-fields.log',[]),('classify-normal-precision.py','normal-precision.log',[]),('capture-cap-fields.py','cap-fields.log',[]),('capture-collar-shader-controls.py','collar-shader-controls.log',[]),('audit-final-source.py','source-audit.log',[])]]
commands.extend([{'command':['/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','source/'+p],'log':'candidates/round-01/'+log} for p,log in [('publish-evidence.py','publication.log'),('finish-evidence.py','finish.log')]])
commands.append({'command':['node','source/capture-consumer.mjs'],'log':'candidates/round-01/consumer.log'})
dump(D/'commands.json',{'pathBase':'object root','commands':commands,'note':'Final captured scene/recipes and exact versioned brief are bound. Blender scripts are checked for Python traceback because Blender can exit0 on a Python error. Reproduction must occur in an unsealed private copy.'})
files=[p for root in [BASE,OUT,D] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['manifest.json','seal.json','packet.json']]
files.extend([brief,contract,EXP/'inputs/root-native-contract.json',EXP/'reviews/preparation-v1/resources/canonical/packet.json'])
records=[record(p) for p in sorted(set(files))]
assert all(r['bytes']<100_000_000 for r in records)
dump(D/'manifest.json',{'asset':'rock-shelf-corner','round':'round-01','pathBase':'object root','status':'immutable editor evidence identity; pending root candidate packet and original independent judge','projectSHA256':sha(BASE/'round-01.blend'),'briefSHA256':sha(brief),'contractSHA256':sha(contract),'files':records})
dump(D/'seal.json',{'asset':'rock-shelf-corner','round':'round-01','delivery':record(D/'delivery.json'),'manifest':record(D/'manifest.json'),'projectSHA256':sha(BASE/'round-01.blend'),'briefSHA256':sha(brief),'contractSHA256':sha(contract),'fileCount':len(records),'bytes':sum(r['bytes'] for r in records),'verdict':'not issued; root packet and original judge required'})
print(json.dumps({'delivery':str(D/'delivery.json'),'sourceSHA256':sha(BASE/'round-01.blend'),'manifestSHA256':sha(D/'manifest.json'),'files':len(records),'bytes':sum(r['bytes'] for r in records)},indent=2))
