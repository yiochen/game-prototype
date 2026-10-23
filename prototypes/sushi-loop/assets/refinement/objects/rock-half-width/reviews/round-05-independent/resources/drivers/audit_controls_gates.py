from pathlib import Path
from PIL import Image
import json,hashlib,shutil,subprocess,sys
B=Path(__file__).resolve().parents[2];obj=B.parents[1];repo=obj.parents[5];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=obj/'candidates/round-05';R=B/'resources';delivery=json.loads((obj/'delivery/round-05.json').read_text());catalog=json.loads((R/'catalog-object.json').read_text())
records=[]
for item in delivery['atlases']:
 d=item['direction'];im=Image.open(obj/item['path']).convert('RGBA');hero=Image.open(C/f'frames/static/{d}/000.png').convert('RGBA');original=next(c for c in catalog['clips'] if c['id']==item['clip'])['directions'][d]
 assert item['columns']==original['columns'] and item['rows']==original['rows'] and item['rects']==original['rects'] and item['size']==original['atlasSize'];x,y,w,h=item['rects'][0];assert im.size==tuple(original['atlasSize']);assert im.crop((x,y,x+w,y+h)).tobytes()==hero.tobytes()
 records.append({'path':item['path'],'sha256':sha(obj/item['path']),'direction':d,'rects':item['rects'],'originalAtlasLayoutUnchanged':True,'exactHeroPixels':True})
camera=json.loads((C/'published-camera.json').read_text());assert camera['frame']==catalog['frameSize'] and camera['anchor']==catalog['root'] and camera['captureScale']==catalog['sourceScale'] and camera['fps']==12
helpers=[]
for name in ['sprite-layout.js','world-sprite-raster.js']:
 p=R/'consumer'/name;q=repo/'prototypes/sushi-loop/wireframe'/name;assert p.read_bytes()==q.read_bytes();helpers.append({'name':name,'frozenSHA256':sha(p),'currentSHA256':sha(q)})
checks=[]
for source,args,name in [(Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),['verify','--packet',str(C/'packet.json')],'integrity'),(repo/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py',['rock-half-width','--round','round-05'],'directions')]:
 dest=R/'instructions'/source.name
 if not dest.exists():shutil.copy2(source,dest)
 else:assert dest.read_bytes()==source.read_bytes()
 cmd=[sys.executable,str(source)]+args;p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True);assert p.returncode==0,(name,p.stdout,p.stderr);checks.append({'gate':name,'sourceSHA256':sha(source),'command':cmd,'cwd':str(repo),'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
(B/'evidence/controls-and-gates.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'atlases':records,'publishedMetadataMatchesFrozenCatalog':True,'helpers':helpers,'unchangedGates':checks},indent=2)+'\n');print(json.dumps({'atlases':len(records),'integrity':checks[0]['exitCode'],'directions':checks[1]['exitCode']}))
