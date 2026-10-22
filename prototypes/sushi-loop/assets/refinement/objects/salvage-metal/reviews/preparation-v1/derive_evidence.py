from pathlib import Path
import json,hashlib,math,shutil
from PIL import Image,ImageDraw,ImageChops
import numpy as np
P=Path(__file__).resolve().parent
C=json.loads((P/'resources/object/inputs/catalog-object.json').read_text());A=json.loads((P/'native/all432-native-measurements.json').read_text());R=A['captureRecords'];T=json.loads((P/'native/closure-and-hold-measurements.json').read_text());CAP=json.loads((P/'native/capture-records.json').read_text())['captureRecords'];out=P/'sheets';out.mkdir(exist_ok=True)
def save(name,value):(P/name).write_text(json.dumps(value,indent=2)+'\n')
def boundsunion(records,key):return {'min':[min(x[key]['min'][i] for x in records) for i in range(3)],'max':[max(x[key]['max'][i] for x in records) for i in range(3)]}
def transforms(x):return {o['name']:{k:o[k] for k in ['visible','location','rotation','scale','matrix']} for o in x['objects']}
def numericdelta(a,b):
 if isinstance(a,dict):return max([numericdelta(a[k],b[k]) for k in a] or [0])
 if isinstance(a,list):return max([numericdelta(x,y) for x,y in zip(a,b)] or [0])
 return abs(float(a)-float(b)) if isinstance(a,(int,float)) else int(a!=b)
summary=[]
for c in C['clips']:
 clip=c['id'];r=[x for x in R if x['clip']==clip];s=[x for x in r if x['direction']=='S'];t=[x for x in T if x['clip']==clip];start=t[0];end=t[2];active=[o['name'] for o in s[0]['objects'] if o['visible']]
 summary.append({'clip':clip,'frames':12,'fps':12,'loop':c['loop'],'allFacingRawUnion':boundsunion(r,'rawAuthoredBounds'),'allFacingEvaluatedUnion':boundsunion(r,'evaluatedBounds'),'SStartRaw':s[0]['rawAuthoredBounds'],'SStartEvaluated':s[0]['evaluatedBounds'],'SEndRaw':s[-1]['rawAuthoredBounds'],'activeMeshes':active,'closureOrHoldMaxTransformDelta':numericdelta(transforms(start if c['loop'] else t[1]),transforms(end)),'lateHoldMaxTransformDelta':None if c['loop'] else numericdelta(transforms(t[1]),transforms(t[3])),'firstLastUniqueTransformDelta':numericdelta(transforms(s[0]),transforms(s[-1]))})
save('source-summary.json',{'clips':summary,'all432Measured':len(R),'boundedRawRenders':len(CAP),'note':'Source measurements are evidence, not automatically final design locks. Raw transformed authored and evaluated bevel bounds remain separate. Matrices recorded only after enabling collection ancestry and owned objects then native cohort evaluation.'})
# Contact/bounds evidence uses native numeric geometry above; sheets uniformly resize complete frames only.
map=[]
canvas=Image.new('RGB',(4*192,3*376),(136,136,136));draw=ImageDraw.Draw(canvas)
for row,clip in enumerate(['shimmer','b-shimmer','c-shimmer']):
 for col,d in enumerate(['N','E','S','W']):
  rel=f'native/raw/{clip}/{d}/000.png';im=Image.open(P/rel).convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);x,y=col*192,row*376;bg=Image.new('RGBA',im.size,[(248,248,245,255),(136,136,136,255),(24,35,46,255)][(row+col)%3]);bg.alpha_composite(im);canvas.paste(bg.convert('RGB'),(x,y+24));draw.text((x+4,y+5),f'{clip} {d}',fill='black');draw.ellipse((x+93,y+24+245,x+99,y+24+251),outline='red');map.append({'sheet':'sheets/native-facing-sheet.png','rect':[x,y+24,192,352],'source':rel,'processing':'whole 768x1408 canvas uniformly reduced to192x352; background composite presentation only'})
canvas.save(out/'native-facing-sheet.png')
canvas=Image.new('RGB',(7*96,9*200),(200,200,200));draw=ImageDraw.Draw(canvas)
for row,c in enumerate(C['clips']):
 frames=[0,3,6,9,11,12]+([] if c['loop'] else [23])
 for col,f in enumerate(frames):
  rel=f'native/raw/{c["id"]}/S/{f:03d}.png';im=Image.open(P/rel).convert('RGBA').resize((96,176),Image.Resampling.LANCZOS);x,y=col*96,row*200;bg=Image.new('RGBA',im.size,(136,136,136,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB'),(x,y+24));draw.text((x+2,y+3),f'{c["id"]} {f}',fill='black');map.append({'sheet':'sheets/native-motion-sheet.png','rect':[x,y+24,96,176],'source':rel,'processing':'uniform complete-frame reduction to96x176, gray background presentation only'})
canvas.save(out/'native-motion-sheet.png');save('sheets/coverage-map.json',map)
# Compare actual untouched replay with full-frame sampled published originals, no cleanup/crop fitting.
residuals=[]
for r in CAP:
 if r['frameIndex']>=12:continue
 c=next(c for c in C['clips'] if c['id']==r['clip']);e=c['directions'][r['direction']];rect=e['rects'][r['frameIndex']];atlas=Image.open(P/'resources/consumer'/e['image']).convert('RGBA');pub=atlas.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));nat=Image.open(P/r['path']).convert('RGBA').resize(pub.size,Image.Resampling.LANCZOS);na=np.asarray(nat).astype(np.int16);pa=np.asarray(pub).astype(np.int16);delta=np.abs(na-pa);visible=np.maximum(na[:,:,3],pa[:,:,3])>0
 residuals.append({'clip':r['clip'],'direction':r['direction'],'frameIndex':r['frameIndex'],'nativePath':r['path'],'publishedAtlas':str(Path('resources/consumer')/e['image']),'publishedRect':rect,'sameDecodedRGBA':bool((delta==0).all()),'changedPixels':int((delta.max(2)>0).sum()),'maxRGBA':delta.max((0,1)).tolist(),'meanAbsRGBAWholeFrame':delta.mean((0,1)).tolist(),'meanAbsRGBAVisibleUnion':delta[visible].mean(0).tolist(),'nativeAlphaBounds':nat.getchannel('A').getbbox(),'publishedAlphaBounds':pub.getchannel('A').getbbox()})
save('replay-published-residuals.json',{'operation':'Uniform whole-frame native768x1408 to published384x704 LANCZOS, compare decoded RGBA against exact declared atlas rect. Atlas rect extraction is diagnostic only. Native render uses Blender5.2.2LTS/32 samples; byte and visible differences retained honestly.','records':residuals})
# Verify all source frames and states, atlas equality of shimmer/attract, exact snapshot origin.
source=[];aliases=[]
for c in C['clips']:
 for d,e in c['directions'].items():
  im=Image.open(P/'resources/consumer'/e['image']).convert('RGBA');hashes=[]
  for f,rect in enumerate(e['rects']):
   cell=im.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));hashes.append(hashlib.sha256(cell.tobytes()).hexdigest());source.append({'clip':c['id'],'direction':d,'frameIndex':f,'decodedSHA256':hashes[-1],'alphaBounds':cell.getchannel('A').getbbox()})
  if c['id'] in ['shimmer','b-shimmer','c-shimmer']:
   other=next(x for x in C['clips'] if x['id']==c['id'].replace('shimmer','attract'));otherim=Image.open(P/'resources/consumer'/other['directions'][d]['image']).convert('RGBA');aliases.append({'left':c['id'],'right':other['id'],'direction':d,'sameDecodedAtlas':im.tobytes()==otherim.tobytes()})
save('published-source-frame-audit.json',{'required432':source,'shimmerAttractDecodedAliases':aliases,'minimumUniqueDecodedFramesPerClipFacing':min(len(set(x['decodedSHA256'] for x in source if x['clip']==c['id'] and x['direction']==d)) for c in C['clips'] for d in ['N','E','S','W'])})
# Keep a concise inventory, retaining complete meaningful own-object records; discard unrelated global scene action_manifest text.
invpath=P/'native/untouched-inventory.json';inv=json.loads(invpath.read_text());inv['sceneProperties']={k:v for k,v in inv['sceneProperties'].items() if k in ['issue','source']};inv['inventoryNormalization']='derive_evidence.py retains own-object detail and scene identity; unrelated global asset/action enumeration removed from preparation packet.';invpath.write_text(json.dumps(inv,indent=2)+'\n')
print('summary',len(summary),'raw',len(CAP),'replay compared',len(residuals),'max visible mean',max(max(x['meanAbsRGBAVisibleUnion']) for x in residuals),'all source frames',len(source))
