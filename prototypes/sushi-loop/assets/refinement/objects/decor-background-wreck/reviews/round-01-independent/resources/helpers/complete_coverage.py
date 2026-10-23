from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
P=Path(__file__).resolve().parent;O=P.parent.parent;C=O/'candidates/round-01';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();plan=json.loads((P/'coverage-plan.json').read_text())
tails=[]
for u in plan['completeLosslessTiles']:
 if u['sourcePath']=='four-view-sheet.png' or u['sourcePath'].startswith('native/'):
  for t in u['tiles']:
   if t['rect'][3]-t['rect'][1]<30:tails.append(t)
image=Image.new('RGBA',(1000,sum((t['rect'][3]-t['rect'][1])+22 for t in tails)), '#808080');draw=ImageDraw.Draw(image);maps=[];y=0
for t in tails:
 im=Image.open(O/t['path']).convert('RGBA');draw.text((0,y),Path(t['path']).name,fill='white');image.paste(im,(0,y+20));maps.append({'sourceTile':t['path'],'sheetRect':[0,y+20,im.width,y+20+im.height],'pixelsExact':image.crop((0,y+20,im.width,y+20+im.height)).tobytes()==im.tobytes()});y+=im.height+22
image.save(P/'lossless-tail-sheet.png');(P/'lossless-tail-sheet-map.json').write_text(json.dumps({'sheet':'reviews/round-01-independent/lossless-tail-sheet.png','sha256':sha(P/'lossless-tail-sheet.png'),'sourceTiles':maps},indent=2)+'\n')
# Independent publication and clean saved-source replay checks; source-source agreement is technical evidence only.
replay=[]
for d in 'NESW':
 a=Image.open(P/'replay'/f'{d}.png').convert('RGBA');b=Image.open(C/f'native/static/{d}/000.png').convert('RGBA');pub=Image.open(C/f'frames/static/{d}/000.png').convert('RGBA');reduced=a.resize((384,704),Image.Resampling.LANCZOS);referenceReduction=b.resize((384,704),Image.Resampling.LANCZOS);df=ImageChops.difference(a,b);replay.append({'direction':d,'replay':str((P/'replay'/f'{d}.png').relative_to(O)),'replaySHA256':sha(P/'replay'/f'{d}.png'),'submittedSHA256':sha(C/f'native/static/{d}/000.png'),'decodedNativeRGBAExact':a.tobytes()==b.tobytes(),'maxRGBAChannelDifference':max(e[1] for e in df.getextrema()),'savedSourceReplayReducedRGBAExactToPublished':reduced.tobytes()==pub.tobytes(),'submittedNativeWholeCanvasLANCZOSExactToPublished':referenceReduction.tobytes()==pub.tobytes(),'publishedAtlasAndConsumerExactBytes':(C/f'frames/static/{d}/000.png').read_bytes()==(C/f'atlases/static-{d}.png').read_bytes()==(O/f'source/round-01-resources/consumer/sprites/decor-background-wreck/static-{d}.png').read_bytes(),'nativeAlphaBounds':a.getchannel('A').getbbox(),'publishedAlphaBounds':pub.getchannel('A').getbbox()})
(P/'independent-replay-publication.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'replays':replay},indent=2)+'\n')
n=json.loads((P/'independent-native-audit.json').read_text());print(json.dumps({'source':n['savedSourceSHA256'],'rootBoundsRaw':n['restRawBounds'],'evaluated':n['restEvaluatedBounds'],'allManifold':all(x['nonManifoldEdges']==0 for x in n['topology']),'mesh':[{k:x[k] for k in ['object','boundaryEdges','nonManifoldEdges','zeroAreaFaces','groundIntersectionFaces']} for x in n['topology']],'nativeOwnedIntersections':n['nativeOwnedSurfaceIntersections'],'temporalStatic':not any(x['action'] or x['drivers'] or x['nla'] for x in n['staticOwners']),'holdsEqual':n['staticHoldGeometryMatrixVisibilityEqual'],'nativeReplays':replay},indent=2))
