from pathlib import Path
import json,hashlib,shutil,sys,platform,subprocess
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;EXP=BASE.parent.parent;C=EXP/'candidates/round-01';ROOT=EXP.parents[5]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=json.loads((C/'packet.json').read_text());assert sha(C/'packet.json')=='8ab76a23ece8a8c73b861915e0c64036d27f876ff4124bcba967d838df4f2c35'
rows=[];unique={}
for group in ['files','candidateRenders','previews']:
 for key,v in packet[group].items():
  p=(C/v['path']).resolve();actual=sha(p);assert actual==v['sha256'],str(p)
  rows.append({'group':group,'key':key,'path':v['path'],'sha256':actual,'absolute':str(p)})
  unique[str(p)]=actual
assert sha(EXP/'source/round-01.blend')=='83765bce799260ef1cc016d02d28861b6a6c79ec883a0731a0800fab4f410657'
assert sha(EXP/'brief.json')=='3767a153d1c1066be52a6f051128ab836fc9a6622802f14aac0f0717de2b88d4'
assert sha(EXP/'inputs/root-native-contract.json')=='da2a0f73cbd5af158cd21dda9ad5428b92328268c6b0d11e7651a9ba37a88fa3'
r=BASE/'resources';r.mkdir(parents=True,exist_ok=True)
items={
 'source/candidate.blend':EXP/'source/round-01.blend','source/canonical.blend':EXP/'inputs/approved-shelf-middle-v1/project.blend',
 'packet.json':C/'packet.json','brief.json':EXP/'brief.json','root-native-contract.json':EXP/'inputs/root-native-contract.json',
 'judge.txt':EXP/'prompts/judge.txt','REVIEW-COVERAGE.txt':EXP.parent.parent/'preparation/REVIEW-COVERAGE.txt',
 'refine-3d-model-SKILL.md':Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),
 'target.png':EXP/'inputs/target.png','original.png':EXP/'inputs/original.png','style.png':EXP.parent.parent/'style/warm-soft-reference.png',
 'acceptance_contract.py':EXP.parent.parent/'tools/acceptance_contract.py',
 'browser/original-harness.html':EXP/'source/consumer-round-01.html',
 'browser/consumer/world-sprite-raster.js':ROOT/'prototypes/sushi-loop/wireframe/world-sprite-raster.js',
 'browser/consumer/sprite-layout.js':ROOT/'prototypes/sushi-loop/wireframe/sprite-layout.js',
 'browser/consumer/react-unused-stub.js':EXP/'source/round-01-resources/consumer/react-unused-stub.js',
 'browser/catalog-object.json':EXP/'inputs/catalog-object.json'}
# Canonical bundle paths are discovered from its manifest when not flat.
if not items['source/canonical.blend'].exists():
 items['source/canonical.blend']=next((EXP/'inputs/approved-shelf-middle-v1').rglob('round-03.blend'))
retained=[]
for rel,p in items.items():
 assert p.exists(),str(p)
 q=r/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 retained.append({'path':rel,'source':str(p),'sha256':sha(q)})
assert sha(r/'source/canonical.blend')=='3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422'
assert sha(r/'browser/consumer/world-sprite-raster.js')=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
assert sha(r/'browser/consumer/sprite-layout.js')=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
html=(r/'browser/original-harness.html').read_text().replace('./round-01-resources/consumer/','./consumer/').replace('./round-01-resources/catalog-object.json','./catalog-object.json').replace("base='../candidates/round-01/'","base='/candidates/round-01/'")
(r/'browser/harness.html').write_text(html)
(BASE/'packet-hash-verification.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'records':rows,'uniqueFiles':len(unique),'recordCount':len(rows),'allVerified':True,'aliases':{'repeated':'fullChrome-background-gray','samePath':packet['previews']['repeated']['path']==packet['previews']['fullChrome-background-gray']['path']}},indent=2)+'\n')
(BASE/'retained-inputs.json').write_text(json.dumps(retained,indent=2)+'\n')
cmd=['node','-p',"JSON.stringify({version:process.version,execPath:process.execPath,playwright:require.resolve('playwright')})"]
node=json.loads(subprocess.check_output(cmd,text=True,cwd=ROOT));blender=Path('/opt/homebrew/bin/blender')
env={'python':sys.version,'pythonExecutable':sys.executable,'pillowRuntime':'specified bundled Python; imported only by later evidence driver','blenderExecutable':str(blender),'blenderSHA256':sha(blender),'blenderVersion':subprocess.check_output([str(blender),'--version'],text=True).splitlines()[0],'node':node,'nodeSHA256':sha(Path(node['execPath'])),'bytecodeWrites':False}
(BASE/'environment-before-execution.json').write_text(json.dumps(env,indent=2)+'\n')
print(json.dumps({'allPacketRecordsVerified':len(rows),'uniqueFiles':len(unique),'retainedInputs':len(retained),'node':node},indent=2))
