import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,shutil
out=pathlib.Path(__file__).resolve().parent;ex=out.parents[1];packet=ex/'candidates/round-01/packet.json';p=json.loads(packet.read_text());root=next(x for x in ex.parents if (x/'prototypes.json').is_file());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(packet)=='f811ac32a84bc59ea572a773963a5df54015b5d2a45cc5297cfd8408f8120473'
files={}
for section in ['files','candidateRenders','previews']:
 for name,r in p[section].items():
  f=(packet.parent/r['path']).resolve();assert f.is_relative_to(root),(name,f)
  actual=sha(f);assert actual==r['sha256'],(name,f,actual,r['sha256']);files[str(f)]={'sha256':actual,'bytes':f.stat().st_size,'entries':files.get(str(f),{}).get('entries',[])+[section+':'+name]}
res=out/'resources';res.mkdir(exist_ok=True)
selected={'brief.json':'brief.json','inputs/root-native-contract.json':'root-native-contract.json','inputs/target.png':'target.png','inputs/original.png':'original.png','inputs/source-camera.json':'original-camera.json','source/round-01.blend':'candidate.blend','source/round-01-neutral.blend':'neutral.blend','source/resources/frozen-main-v1/project.blend':'frozen-main.blend','source/consumer-demo.js':'consumer/consumer-demo.js','source/consumer-demo.html':'consumer/consumer-demo.html','source/consumer-demo.jsx':'consumer/consumer-demo.jsx','source/consumer-objects.json':'consumer/consumer-objects.json','source/check-consumer.mjs':'consumer/supplied-check-consumer.mjs','source/resources/consumer/sprite-layout.js':'consumer/sprite-layout.js','source/resources/consumer/world-sprite-raster.js':'consumer/world-sprite-raster.js'}
for a,b in selected.items():
 dst=res/b;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ex/a,dst)
for name in ['geometry-audit.json','action-audit.json','publication-manifest.json','native-render-manifest.json','validation.json','settings.json','publication-validation.json']:
 shutil.copy2(ex/'candidates/round-01'/name,res/name)
shutil.copy2(packet,res/'packet.json')
shutil.copy2(root/'AGENTS.md',res/'root-AGENTS.md');shutil.copy2(root/'prototypes/sushi-loop/AGENTS.md',res/'sushi-AGENTS.md')
shutil.copy2(ex/'reviews/preparation-v1/resources/instructions/refine-3d-model-SKILL.md',res/'refine-3d-model-SKILL.md')
shutil.copy2(root/'prototypes/sushi-loop/assets/refinement/preparation/sub-hull-panels/judge-round-01-dispatch.txt',res/'dispatch.txt')
for name in ['PIL']:
 shutil.copytree(ex/'reviews/preparation-v1/resources/tools/python'/name,res/'python'/name,dirs_exist_ok=True)
(out/'packet-verification.json').write_text(json.dumps({'packetSHA256':sha(packet),'verifiedEntries':sum(len(p[s]) for s in ['files','candidateRenders','previews']),'verifiedUniqueFiles':len(files),'files':files,'snapshotMap':selected},indent=2))
print('PACKET_VERIFIED',len(files),sum(len(p[s]) for s in ['files','candidateRenders','previews']))
