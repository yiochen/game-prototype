"""Read-only old-byte integrity and registered headwear alpha-slot measurement.
This records pixel evidence, not an editor visual verdict.
"""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round02'
packetpath=OBJ/'candidates/round01/packet.json';packet=json.loads(packetpath.read_text())
records=[*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]
seen={}
for r in records:
 p=(packetpath.parent/r['path']).resolve();actual=hashlib.sha256(p.read_bytes()).hexdigest()
 assert actual==r['sha256'],('Round01 bound bytes changed',p)
 seen[str(p)]=actual
def slots(path):
 alpha=Image.open(path).getchannel('A').crop((70,180,315,360)).point(lambda a:255 if a>=64 else 0)
 padded=Image.new('L',(alpha.width+2,alpha.height+2),0);padded.paste(alpha,(1,1));ImageDraw.floodfill(padded,(0,0),128,thresh=0)
 return padded.histogram()[0]
rows=[]
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   sub=Path('raw-frames')/(clip+'-'+d)/(str(i).zfill(3)+'.png')
   old=slots(OBJ/'candidates/round01'/sub);new=slots(OUT/sub)
   rows.append({'clip':clip,'direction':d,'index':i,'round01EnclosedTransparentPixels':old,'round02EnclosedTransparentPixels':new})
report={'round01PacketSHA256':hashlib.sha256(packetpath.read_bytes()).hexdigest(),'oldBoundFilesUnchanged':True,'uniqueOldFilesVerified':len(seen),'alphaSlotMethod':'Fixed native headwear ROI[70,180,315,360], alpha threshold64; flood transparent pixels from padded exterior and count enclosed transparent pixels. Raw native PNGs only, no pixel changes. Visual integration remains the independent judge decision.','roi':[70,180,315,360],'samples':192,'round01MaximumEnclosedTransparentPixels':max(r['round01EnclosedTransparentPixels'] for r in rows),'round02MaximumEnclosedTransparentPixels':max(r['round02EnclosedTransparentPixels'] for r in rows),'round01TotalEnclosedTransparentPixels':sum(r['round01EnclosedTransparentPixels'] for r in rows),'round02TotalEnclosedTransparentPixels':sum(r['round02EnclosedTransparentPixels'] for r in rows),'frames':rows}
assert report['round02MaximumEnclosedTransparentPixels']==0,report['round02MaximumEnclosedTransparentPixels']
(OUT/'headband-alpha-integrity-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='frames'}))
