import json,hashlib,shutil
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];O=P.parents[1];W=O.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
a=json.loads((O/'source/construction-acknowledgment-v2.json').read_text());out=[]
for x in a['priorByteProtection']+[{'path':p,'sha256':h}for p,h in a['frozenInputHashes'].items()]:
 assert sha(O/x['path'])==x['sha256'],x;out.append(x)
old=json.loads((O/'reviews/round-01-evidence-v1/supplemental-manifest.json').read_text())
for x in old['files']:assert sha(O/x['path'])==x['sha256'],x
for p,h in {'reviews/round-01-evidence-v1/post-review-seal.json':'ed0dd317f56a6b5fc749cb7a7c32f9553b2a3b68010af503ea0d9a346ed8d7ef'}.items():
 if (O/p).exists():assert sha(O/p)==h
m=json.loads((O/'candidates/round-02/consumer/inspection-report.json').read_text());maps=[]
for mode in m['playback']:
 for s in mode['sheets']:
  im=Image.open(O/s['path']);edges=sorted({x['sheetRect'][0]for x in s['cells']});cut=edges[6]
  for name,box in [('first6',(0,0,cut,im.height)),('last7',(cut,0,im.width,im.height))]:
   target=P/'inspection'/f"{mode['mode']}-{Path(s['path']).stem}-{name}.png";im.crop(box).save(target);maps.append({'source':s['path'],'sourceSHA256':sha(O/s['path']),'crop':list(box),'path':str(target.relative_to(O)),'exactPixels':'unscaled RGB source-sheet crop; every cell covered between the two halves'})
dump(P/'inspection/video-sheet-crop-map.json',maps)
dump(P/'resources/preservation-verification.json',{'protectedEditorPriorFiles':len(a['priorByteProtection']),'frozenInputs':len(a['frozenInputHashes']),'previousJudgeSupplementMembers':len(old['files']),'allHashesVerified':True,'verifiedFrozenAndPrior':out,'priorJudgeSupplementSHA256':sha(O/'reviews/round-01-evidence-v1/supplemental-manifest.json')})
print(json.dumps({'protectedPrior':len(a['priorByteProtection']),'frozenInputs':len(a['frozenInputHashes']),'priorJudgeMembers':len(old['files']),'unscaledVisualCrops':len(maps)}))
