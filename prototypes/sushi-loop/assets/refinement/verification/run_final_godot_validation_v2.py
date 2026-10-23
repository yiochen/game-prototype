"""Validate the actual sprite cutover in disposable native sessions; no install."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
run=Path(__file__).resolve().parents[1]
repo=run.parents[3]
godot=run.parents[1]/'godot'
out=run/'verification/final-godot-cutover-v2'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=read(out/'payload-receipt.json')
assert receipt['status']=='payload-sync-and-import-checks-complete-full-scene-pending'
assert sha(run.parent/'production/library.json')==receipt['sourceLibrarySHA256']
assert all(sha(godot/name)==value for name,value in receipt['afterFiles'].items())
commands=[('engine',['node','--test',*map(str,sorted((repo/'prototypes/sushi-loop/tests').glob('*.test.js')))]),('build',['npm','run','build']),('browser',['npx','playwright','test',*[f'prototypes/sushi-loop/tests/{name}.spec.js' for name in ['art-catalog','world-showcase','world-sprite-raster','wireframe']]])]
python='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
native=[python,str(godot/'tools/test_native.py'),'--godot','/opt/homebrew/bin/godot']
commands.append(('native-suites',native))
for label,size in [('phone','390x844'),('landscape','1120x720')]:
 commands.append((f'native-app-{label}',native+['--script','tests/native_app_tests.gd','--visible','--size',size]))
 for scope in ['starter','editor']:
  commands.append((f'capture-{label}-{scope}',native+['--script',f'tests/capture_{scope}.gd','--visible','--size',size,'--output',str(out/f'{label}-{scope}')]))
if not args.apply:
 print(json.dumps({'status':'plan-only','commands':[(n,c[:4]) for n,c in commands],'mutated':False}));raise SystemExit(0)
logs=out/'validation';assert not logs.exists(),'Use a versioned continuation if a validation attempt already exists.'
logs.mkdir()
env=os.environ.copy();env['TEST_URL']='http://127.0.0.1:4179'
results=[]
for name,command in commands:
 process=subprocess.run(command,cwd=repo,env=env,capture_output=True,text=True)
 stdout=logs/f'{name}.stdout.txt';stderr=logs/f'{name}.stderr.txt'
 stdout.write_text(process.stdout);stderr.write_text(process.stderr)
 result={'name':name,'argv':command,'exitCode':process.returncode,'stdout':{'path':str(stdout.relative_to(run)),'sha256':sha(stdout)},'stderr':{'path':str(stderr.relative_to(run)),'sha256':sha(stderr)}}
 results.append(result);(logs/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps({'name':name,'exitCode':process.returncode}),flush=True)
 process.check_returncode()
assert all(sha(godot/name)==value for name,value in receipt['afterFiles'].items())
(logs/'result.json').write_text(json.dumps({'status':'automated-validation-passed-visual-review-and-package-pending','commands':results,'gamePayloadHashesUnchanged':True,'sceneCapturePaths':['phone-starter','phone-editor','landscape-starter','landscape-editor'],'scope':'Disposable unique save identities; no installation or production deploy.'},indent=2)+'\n')
print('Actual cutover automated checks passed; inspect native captures and package next.',flush=True)
