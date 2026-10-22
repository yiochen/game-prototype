from pathlib import Path
import json,hashlib,shutil,datetime
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');OBJ=ROOT/'prototypes/sushi-loop/assets/refinement/objects/dock-entry';PACK=OBJ/'candidates/round-07/packet.json';OUT=OBJ/'reviews/round07-independent';RET=OUT/'resources/repo';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads(PACK.read_text());assert H(PACK)=='5e4a1c313176fc0e0474474a0fbc800b3ddd321d9c4076e71da39620a617ba70'
refs={};fail=[];claims=[]
for group in ['files','candidateRenders','previews']:
 for role,v in p[group].items():
  q=(PACK.parent/v['path']).resolve();got=H(q);claims.append({'group':group,'role':role,'originalPath':str(q),'declaredSHA256':v['sha256'],'actualSHA256':got})
  if got!=v['sha256']:fail.append(role)
  refs[q]=q
extra=[PACK,OBJ/'delivery-v4.json',OBJ/'brief-v4-human-reference.json',OBJ/'reviews/initial.json',OBJ/'reviews/proposedcriteria.json',ROOT/'prototypes/sushi-loop/wireframe/sprite-layout.js',ROOT/'prototypes/sushi-loop/wireframe/world-sprite-raster.js',ROOT/'prototypes/sushi-loop/assets/production/library.json',ROOT/'prototypes/sushi-loop/assets/refinement/preparation/MUTABLE-REVIEW-INPUTS.md',ROOT/'prototypes/sushi-loop/assets/refinement/preparation/dock-entry/judge-round-07-dispatch.txt']
for q in extra:
 if q.exists():refs[q]=q
retained=[]
for q in refs:
 assert q.stat().st_size<100_000_000,q
 rel=q.relative_to(ROOT);dest=RET/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,dest);retained.append({'originalPath':str(q),'retainedPath':str(dest.relative_to(OUT)),'sha256':H(dest),'sizeBytes':dest.stat().st_size})
skill=Path('/Users/yiouchen/.codex/skills/refine-3d-model');skfiles=[skill/'SKILL.md',skill/'scripts/candidate_packet.py',skill/'references/blender-techniques.md']
for q in skfiles:
 dest=OUT/'resources/skill'/q.relative_to(skill);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,dest);retained.append({'originalPath':str(q),'retainedPath':str(dest.relative_to(OUT)),'sha256':H(dest),'sizeBytes':dest.stat().st_size})
r={'candidatePacketSHA256':H(PACK),'createdUTC':datetime.datetime.now(datetime.UTC).isoformat(),'files':{x['retainedPath']:x['sha256'] for x in retained},'provenance':retained,'packetClaims':claims,'mismatchedPacketClaims':fail,'allInputsRetainedUnder100MBEach':True};(OUT/'input-snapshot-manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Retained',len(retained),'files;',round(sum(x['sizeBytes'] for x in retained)/1e6,1),'MB; packet claim mismatches',len(fail));print(fail)
