import sys
sys.dont_write_bytecode=True
import json,hashlib,os,platform,subprocess,datetime
from pathlib import Path
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(B/n).write_text(json.dumps(d,indent=2)+'\n')
# Final audit corrections preserve actually used prior review media and drivers.
p=B/'source-replay-visual-observations.json';d=json.loads(p.read_text());d['sheetLimit']='Final policy/use-size sheets were widened and actually re-inspected. Fixed registered crop includes all4 whole alpha silhouettes. Original inspectedv0 sheets, drivers, logs and findings remain saved. Crops/scaling are review media only; native PNGs remain untouched.';d['supersededInspectedMedia']=['evidence/source-replay-policy-sheet-v0.png','evidence/source-replay-use-size-sheet-v0.png'];save(p.name,d)
p=B/'assembly-evidence-plan.json';d=json.loads(p.read_text());lookup={0:'S',1:'E',2:'N',3:'W'}
for contexts in d['all4AuthoredPositions'].values():
 for rows in contexts.values():
  for row in rows:row['catalogPlacementAtEndGridRoot3.5_3.5']['direction']=lookup[round(row['angle']/(3.141592653589793/2))%4]
save(p.name,d)
versions={'blender':{'executable':'/opt/homebrew/bin/blender','sha256':sha(Path('/opt/homebrew/bin/blender')),'version':'5.2.2 LTS','buildHash':'d13f752e3b9c','mode':'--background --factory-startup; no live UI/MCP Blender'},'python':{'executable':sys.executable,'version':sys.version,'sha256':sha(Path(sys.executable)),'Pillow':'12.3.0','dontWriteBytecode':sys.dont_write_bytecode},'nodeVersionReadOnly':(B/'logs/node-version.txt').read_text().strip(),'browserStatus':'No browser launched in preparation. FullChromium channelchromium and default bundled shell are specified for future exact-candidate evidence, with actual versions/argv/DPR/viewport required at execution. No prior browser version represented as a new run.','usedModules':{'Blender':['bpy','mathutils','bpy_extras.object_utils'],'PythonStandardLibrary':['sys','json','math','pathlib','hashlib','shutil','datetime','importlib.util','types','collections','platform','subprocess','os'],'external':['Pillow12.3.0'],'frozenCaptureClosure':['resources/capture/capture_worker.py','resources/capture/capture_runtime.py','resources/capture/catalog_style.py','resources/capture/catalog_faceted.py']},'sourceRecipeReadOnly':True,'noFrozenBytecode':True,'executedScope':'Measure original and canonical, eight untouched-source native control renders, Pillow comparisons/sheets, criteria/contract/evidence planning, exact dependency copies. No candidate construction, browser matrix, approval, Git, production, device or native UI.'}
save('toolchain.json',versions)
# Original observations were immutable before canonical reads.
assert (B/'initial.sha256').read_text().split()[0]==sha(B/'initial.json')
assert sha(B/'resources/b1765262bfa897ad-sushi-loop-world-library.blend')=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert sha(B/'resources/canonical/reef-middle-round-02.blend')=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
files=[p for p in B.rglob('*') if p.is_file() and p.name not in ['manifest.json','manifest.sha256']]
assert all(p.stat().st_size<100_000_000 for p in files)
assert not any(p.suffix in ['.pyc','.pyo'] for p in files)
save('seal-validation.json',{'checks':{'originalInitialSealMatches':True,'originalNativeSourceIdentity':True,'canonicalExactSourceIdentity':True,'allFilesBelow100MB':True,'noPycOrPyo':True,'onlyOwnReviewsEdited':True,'noCandidateConstructedOrApproved':True},'fileSizeMaximumBeforeThisValidation':max(p.stat().st_size for p in files),'observationOrder':'Own original/target/family/style and activated original collection first → initial.json SHA saved → canonical source/contract/review and technical analysis.','scope':'Preparation immutable handoff for root freeze; no approval.'})
files=[p for p in B.rglob('*') if p.is_file() and p.name not in ['manifest.json','manifest.sha256']]
entries=[{'path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]
manifest={'schemaVersion':1,'asset':'reef-end','stage':'preparation-v1 independent judge handoff; STOP for root reconciliation/freeze','createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(B),'scope':'Hash-bound exact own observations, actual source/canonical measurements, bounded original-source replay, proposedcriteria/rootcontract, native/consumer evidenceplan, exact used drivers/logs/minimal saved inputclosure. No construction or candidate/family/production approval.','files':entries,'fileCount':len(entries),'totalBytes':sum(e['bytes'] for e in entries),'maximumFileBytes':max(e['bytes'] for e in entries)}
save('manifest.json',manifest)
(B/'manifest.sha256').write_text(sha(B/'manifest.json')+'  manifest.json\n')
for p in B.rglob('*'):
 if p.is_file():p.chmod(0o444)
print(json.dumps({'manifestSHA256':sha(B/'manifest.json'),'files':len(entries),'totalBytes':manifest['totalBytes'],'maximumFileBytes':manifest['maximumFileBytes'],'handoff':str(B/'handoff.json'),'status':'SEALED; STOP before rootfreeze/fresh editor'}))
