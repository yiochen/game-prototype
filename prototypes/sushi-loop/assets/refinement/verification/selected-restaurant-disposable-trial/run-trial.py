from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
PROTO=ROOT/'prototypes/sushi-loop'; GAME=PROTO/'godot'; OUT=PROTO/'assets/refinement/verification/selected-restaurant-disposable-trial'
OUT.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 result={}
 for relative in ['catalog','ui/editor-goods','feedback-variants','chef-variants','recipe-variants']:
  for p in (GAME/'assets'/relative).rglob('*'):
   if p.is_file() and p.suffix in ['.png','.json']:result[p.relative_to(GAME).as_posix()]=digest(p)
 return result
before=snapshot()
baseline=json.loads((PROTO/'assets/refinement/backups/godot-before-warm-soft/snapshot.json').read_text())
assert before==baseline['files'],'Actual game differs from saved pre-cutover sprite baseline'
library=json.loads((PROTO/'assets/production/library.json').read_text());objects={x['id']:x for x in library['objects']}
sys.path.insert(0,str(GAME/'tools'))
from catalog_contract import SELECTION,verify_catalog
missing=[a for a in SELECTION if a not in ['floor-cream','floor-blue-wave'] and not objects[a].get('refinement')]
assert not missing,('Await remaining selected native approvals',missing)
source_sha=digest(PROTO/'assets/production/library.json');results=[]
(OUT/'actual-game-before.json').write_text(json.dumps(before,indent=2)+'\n')
def run(name,args):
 print('Running '+name,flush=True)
 with (OUT/(name+'.log')).open('w')as log:
  proc=subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 results.append({'name':name,'exitCode':proc.returncode,'log':name+'.log','logSHA256':digest(OUT/(name+'.log'))})
 (OUT/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
 assert proc.returncode==0,(name,OUT/(name+'.log'))
 print('Passed '+name,flush=True)
with tempfile.TemporaryDirectory(prefix='sushi-approved-restaurant-trial-')as tmp:
 proto=Path(tmp)/'prototypes/sushi-loop';proto.mkdir(parents=True);game=proto/'godot'
 ignored=shutil.ignore_patterns('.godot','.local','build','android','review','__pycache__','*.keystore','*.jks','export_credentials.cfg')
 shutil.copytree(GAME,game,ignore=ignored)
 run('00-source-snapshot',['/bin/cp','-cR',str(PROTO/'assets'),str(proto/'assets')])
 for relative in ['catalog','ui/editor-goods','feedback-variants','chef-variants','recipe-variants']:
  shutil.rmtree(game/'assets'/relative)
 tools=game/'tools';py=sys.executable
 run('01-catalog',[py,str(tools/'sync_catalog.py')]);verify_catalog(PROTO/'assets/production',game/'assets/catalog')
 run('02-goods',[py,str(tools/'pack_refined_goods.py'),'--output',str(game/'assets/ui/editor-goods')])
 run('03-feedback',[py,str(tools/'sync_refined_feedback.py'),'--output',str(game/'assets/feedback-variants')])
 for kind in ['chef','recipe']:run('04-'+kind,[py,str(tools/'sync_refined_actor_variants.py'),'--kind',kind,'--output',str(game/'assets'/f'{kind}-variants')])
 for module in ['editor_goods','feedback_variants','chef_variants','recipe_variants']:
  run('04-verify-'+module,[py,str(tools/f'verify_{module}.py')])
 run('05-phone-native',[py,str(tools/'test_native.py'),'--godot','/opt/homebrew/bin/godot','--size','390x844','--timeout','240'])
 for label,size in [('phone','390x844'),('landscape','1120x720')]:
  for scene in ['starter','editor']:
   target=OUT/f'{label}-{scene}'
   run(f'06-{label}-{scene}',[py,str(tools/'test_native.py'),'--godot','/opt/homebrew/bin/godot','--size',size,'--timeout','240','--visible','--script',f'tests/capture_{scene}.gd','--output',str(target)])
after=snapshot();assert before==after,'Actual game runtime payloads changed during disposable trial'
receipt={'scope':'Early selected-restaurant trial only; full catalog/final actual Godot cutover remains pending','sourceLibrarySHA256':source_sha,'selectedObjects':len(SELECTION),'selectedWarmRefinements':len(SELECTION)-2,'excludedRestaurantFloors':['floor-cream','floor-blue-wave'],'results':results,'actualGamePayloadsUnchanged':True,'actualGamePayloadCount':len(before),'actualGamePayloadSnapshot':before,'isolation':'Outer disposable Godot copy with independent APFS copy-on-write source snapshot; test runner creates another disposable project and unique save identity; real game payloads and saves are untouched.'}
(OUT/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');shutil.copyfile(__file__,OUT/'run-trial.py')
print(json.dumps({k:v for k,v in receipt.items()if k!='actualGamePayloadSnapshot'}))
