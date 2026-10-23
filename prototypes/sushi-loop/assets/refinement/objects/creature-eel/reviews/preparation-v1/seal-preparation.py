from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent;O=P.parent.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
# Preserve the exact here-doc render-driver revisions used before the metadata iterator fix.
# Logical execution path is recorded; resources/drivers is an archival location, not a new execution root.
dr=P/'resources/drivers';dr.mkdir(exist_ok=True)
for filename in ['capture-source.py','diagnostic-euler.py']:
 s=(P/filename).read_text().replace('curves=list(N._fcurves(action))','curves=N._fcurves(action)')
 s=s.replace("if '--measure-only' in sys.argv:\n print('MEASURE_ONLY_FINISHED',flush=True);sys.exit()\n",'')
 (dr/(Path(filename).stem+'-rendered-v1.py')).write_text(s)
commands=json.loads((P/'commands.json').read_text());base='prototypes/sushi-loop/assets/refinement/objects/creature-eel/reviews/preparation-v1/';source=commands['sourceBlend']
for run in commands['runs']:
 if run.get('args','').startswith('blender'):
  run['exactCommand']='PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b '+source+' --python '+base+run['script']+(' -- --measure-only' if '--measure-only' in run['args'] else '')+' > '+base+run['log']+' 2>&1'
  if run['script'] in ['capture-source.py','diagnostic-euler.py'] and '--measure-only' not in run['args']:
   run['exactRenderDriverRevision']='resources/drivers/'+Path(run['script']).stem+'-rendered-v1.py';run['logicalExecutionLocation']=base+run['script']
 elif run.get('command'):run['exactCommand']='npm run dev -- --port 5163 > '+base+run['log']+' 2>&1'
 elif run.get('args','').startswith('node'):
  run['exactCommand']='node '+base+run['script']+' > '+base+run['log']+' 2>&1'
 elif run.get('args','').startswith('PILLOW_PYTHON'):
  run['exactCommand']=commands['environment']['pillowPython']+' '+base+run['script']+(' > '+base+run['log']+' 2>&1' if run.get('log') else '')
 elif run.get('args')=='python3 SCRIPT':run['exactCommand']='python3 '+base+run['script']
commands['executionNotes'].append('resources/drivers retains the exact original here-doc render revisions before the documented metadata-only iterator fix, archived under new paths. Current drivers add --measure-only and correct action-channel metadata only; both used versions are bound. No repeat rendering needed.')
put(P/'commands.json',commands)
records=json.loads((P/'capture-records.json').read_text())
put(P/'source-native-validation.json',{'asset':'creature-eel','scope':'source preparation only; no candidate validation/approval','sourceSHA256':records['sourceSHA256'],'camera':'native-camera.json','nativeFrame':records['nativeFrame'],'captureScale':records['nativeScale'],'captureRecords':[{'direction':r['direction'],'clip':r['clip'],'frame':r['frame'],'rootRotationZ':r['rootRotationZ'],'actualRootMatrix':r['actualRootMatrix'],'path':r['nativePath']} for r in records['records']],'nativeGeometryMeasurements':json.loads((P/'native-measurements.json').read_text())['views'],'honestResiduals':'replay-residual-summary.json'})
sourcePath=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')/source
expected='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert sha(sourcePath)==expected==sha(P/'resources/untouched-source.blend')
assert sha(P/'resources/instructions/dispatch.txt')=='8aa8907fdb09f1a020500b9f9e6a417f426ae7ba1043f1d7fc7a9bca6d0fa967'
paths=[P.parent/'initial.json',P.parent/'criteria.json']+[p for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ['manifest.json','seal.json']]
assert not any('__pycache__' in p.parts for p in paths)
assert all(p.stat().st_size<100_000_000 for p in paths)
files=[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]
put(P/'manifest.json',{'formatVersion':1,'asset':'creature-eel','scope':'fresh independent body-only preparation; no candidate/approval','pathBase':'object-root','sourceSHA256':expected,'files':files,'fileCount':len(files),'totalBytes':sum(f['bytes'] for f in files),'closure':'Only actual used/read inputs/modules, own exact scripts/commands/logs, own source studies/browser captures, independent criteria and proposed contract. Runtime/application trees are not copied.'})
manifest_sha=sha(P/'manifest.json')
put(P/'seal.json',{'asset':'creature-eel','stage':'preparation-v1','status':'sealed proposed evidence pending ROOT reconciliation/freeze','approval':False,'candidate':None,'manifest':{'path':'reviews/preparation-v1/manifest.json','sha256':manifest_sha},'sourceSHA256':expected,'independentCriteria':{'path':'reviews/criteria.json','sha256':sha(P.parent/'criteria.json')},'initial':{'path':'reviews/initial.json','sha256':sha(P.parent/'initial.json')},'proposedContract':{'path':'reviews/preparation-v1/root-native-contract.proposed.json','sha256':sha(P/'root-native-contract.proposed.json')},'proposedEvidencePlan':{'path':'reviews/preparation-v1/evidence-plan.proposed.json','sha256':sha(P/'evidence-plan.proposed.json')},'fileCount':len(files),'totalBytes':sum(f['bytes'] for f in files),'createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stop':'Preparation complete. Wait for ROOT reconciliation/freeze and a fresh editor. No candidate construction, effect work, production integration, publish, device or approval.'})
print(json.dumps({'manifestSHA256':manifest_sha,'sealSHA256':sha(P/'seal.json'),'files':len(files),'totalBytes':sum(f['bytes'] for f in files),'maxBytes':max(f['bytes'] for f in files)},indent=2))
