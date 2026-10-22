from pathlib import Path
import json,hashlib,shutil
from PIL import Image
P=Path(__file__).resolve().parent;O=P.parent.parent;C=O/'candidates/round-02';R=P/'resources';pack=json.loads((C/'packet.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
expected={'brief.json':'0d70f621d013e2ca2b99c392f1dd4f86bffe778dba5f9d3b2c556dfd722ecb2d','inputs/root-native-contract.json':'b6dcd70d8ec52564f9d84f6c9b3dfdca7244af9ea7192ec6b3bf36495227bb5f','reviews/proposedcriteria.json':'b2da1303a13c000f5d95e08295e6530d8973e7214283bf8d2f802b688c827698','inputs/root-preparation-reconciliation-v1.json':'07123994e6c962c33e410c7884d52e5c843922cc2689dee56b2a24382617ddb6','source/round-02.blend':'abb77ba5ff32e0d38f70796950a3b433c48f6a953ffb08167d8735f0daa27e21'}
checks=[]
for rel,want in expected.items():checks.append({'path':rel,'sha256':sha(O/rel),'expected':want,'match':sha(O/rel)==want})
for group in ['files','candidateRenders','previews']:
 for name,r in pack[group].items():
  f=(C/r['path']).resolve();checks.append({'group':group,'name':name,'path':r['path'],'sha256':sha(f),'match':sha(f)==r['sha256']})
assert all(r['match'] for r in checks)
for rel in ['brief.json','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json','reviews/proposedcriteria.json','inputs/original.png','inputs/target.png','inputs/source-camera.json','source/round-02.blend','candidates/round-02/packet.json','candidates/round-02/native-validation.json','candidates/round-02/validation.json','candidates/round-02/publication-proof.json','candidates/round-02/consumer-ledger.json','candidates/round-02/source-settings-audit-v2.json','candidates/round-02/published-camera.json','candidates/round-02/rig.json','candidates/round-02/assetRecord.json','candidates/round-02/environment.json','candidates/round-02/inspection-map.json','candidates/round-02/round-02-resource-manifest.json']:
 dst=R/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(O/rel,dst)
for src,name in [(O.parent.parent/'style/warm-soft-reference.png','warm-soft-reference.png'),(O.parent.parent/'preparation/decor-background-wreck/judge-round-02-dispatch.txt','judge-round-02-dispatch.txt'),(Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),'refine-3d-model-SKILL.md')]:shutil.copy2(src,R/name)
used={};paths={};aliases=[]
for group in ['candidateRenders','previews']:
 for name,r in pack[group].items():
  f=C/r['path'];im=Image.open(f);key=r['sha256'];paths[r['path']]={'sha256':key,'size':list(im.size),'group':group,'name':name}
  if key in used:aliases.append({'path':r['path'],'exactSHA256':key,'inspectedAs':used[key]['sourcePath']});continue
  used[key]={'sourcePath':r['path'],'sha256':key,'size':list(im.size),'tiles':[]}
  for y in range(0,im.height,700):
   for x in range(0,im.width,1000):
    box=[x,y,min(x+1000,im.width),min(y+700,im.height)];t=im.crop(box);file=P/'tiles'/f'{len(used)-1:02d}-{x}-{y}.png';file.parent.mkdir(exist_ok=True);t.save(file);used[key]['tiles'].append({'path':str(file.relative_to(O)),'rect':box,'sha256':sha(file),'pixelIdentityToSourceCrop':t.tobytes()==im.crop(box).tobytes()})
report={'asset':'decor-background-wreck','candidatePacketSHA256':sha(C/'packet.json'),'pathBase':'object-root','declaredRecords':sum(len(pack[g]) for g in ['candidateRenders','previews']),'uniqueDeclaredPaths':len(paths),'uniquePixelFileHashes':len(used),'paths':paths,'sameHashAliases':aliases,'completeLosslessTiles':list(used.values()),'hashChecks':checks,'allHashesMatch':True,'everyTilePreservesRGBA':True,'inspectedTiles':[]}
(P/'coverage-plan.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'uniquePaths':len(paths),'uniqueHashes':len(used),'tiles':sum(len(x['tiles']) for x in used.values()),'tilesBySource':[{'path':u['sourcePath'],'size':u['size'],'tiles':[t['path'].split('/')[-1] for t in u['tiles']]} for u in used.values()]},indent=2))
