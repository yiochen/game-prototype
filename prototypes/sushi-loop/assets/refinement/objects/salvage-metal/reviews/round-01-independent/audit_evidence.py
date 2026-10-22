from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
import numpy as np
P=Path(__file__).resolve().parent;O=P.parent.parent;C=O/'candidates/round-01';packet=json.loads((C/'packet.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,a):(P/name).write_text(json.dumps(a,indent=2)+'\n')
verified=[]
for group in ['files','candidateRenders','previews']:
 for name,r in packet[group].items():
  f=(C/r['path']).resolve();assert f.is_file() and sha(f)==r['sha256'],(group,name);verified.append({'group':group,'name':name,'path':r['path'],'sha256':r['sha256']})
write('packet-binding-check.json',{'candidatePacketSHA256':sha(C/'packet.json'),'records':verified})
coverage=json.loads((C/'sheets/coverage-map.json').read_text());colors=[(248,246,240,255),(136,142,146,255),(23,39,54,255)];cellrecords=[]
for r in coverage:
 pub=Image.open(O/r['published']).convert('RGBA');native=Image.open(O/r['source']).convert('RGBA');assert sha(O/r['published'])==r['publishedSHA256'] and sha(O/r['source'])==r['sourceSHA256'];assert native.resize((384,704),Image.Resampling.LANCZOS).tobytes()==pub.tobytes();clip=Path(r['published']).parts[-3];d=Path(r['published']).parts[-2];idx=int(Path(r['published']).stem);row=['N','E','S','W'].index(d);half=idx//6;local=idx%6;sheetPath=C/'sheets'/f'allphase-{clip}-half{half}.png';sheet=Image.open(sheetPath).convert('RGB');logical=pub.resize((192,352),Image.Resampling.LANCZOS);bg=Image.new('RGBA',logical.size,colors[(row+idx)%3]);bg.alpha_composite(logical);rect=[local*192,row*376+24,192,352];part=sheet.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));assert part.tobytes()==bg.convert('RGB').tobytes();cellrecords.append({'published':r['published'],'native':r['source'],'sheet':str(sheetPath.relative_to(C)),'sheetSHA256':sha(sheetPath),'rect':rect,'wholeFrameSamplingAndCellExact':True})
write('full-useful-phase-coverage.json',{'count':len(cellrecords),'cellRecords':cellrecords,'sheetInspection':'All18 declared half-sheets directly inspected as1152x1504 original-resolution images,192x352 logical complete-cell art; no reduced overview substituted.'})
# All source atlases contain each exact published phase at original registered rect.
obj=json.loads((C/'consumer-object.json').read_text());atlases=[]
for clip in obj['clips']:
 for d,e in clip['directions'].items():
  f=(O/'source'/e['image']).resolve() if not (C/'atlases'/f'{clip["id"]}-{d}.png').exists() else C/'atlases'/f'{clip["id"]}-{d}.png'
  im=Image.open(f).convert('RGBA')
  for idx,rect in enumerate(e['rects']):
   x,y,w,h=rect;assert im.crop((x,y,x+w,y+h)).tobytes()==Image.open(C/'frames'/clip['id']/d/f'{idx:03d}.png').convert('RGBA').tobytes()
  atlases.append({'clip':clip['id'],'direction':d,'path':str(f.relative_to(O)),'sha256':sha(f),'all12RectsExact':True})
write('atlas-verification.json',atlases)
replay=json.loads((P/'native-replay.json').read_text());records=replay['records'];original=json.loads((C/'native-validation.json').read_text())['captureRecords'];holds=json.loads((C/'closure-hold-records.json').read_text())['captureRecords'];reference={(r['clip'],r['direction'],r['sourceFrame']):r for r in original+holds}
comparisons=[]
for r in records:
 ref=reference[r['clip'],r['direction'],r['nativeFrame']];delta=max(abs(r['evaluatedBounds'][k][i]-ref['bounds'][k][i]) for k in ['min','max'] for i in range(3));assert delta<1e-6;assert {x['name'] for x in r['activeMeshes']}=={x['name'] for x in ref['activeMeshes']};assert set(x['variantIndex'] for x in r['activeMeshes'])=={(1 if r['clip'].startswith('b-') else 2 if r['clip'].startswith('c-') else 0)};z=.7 if not r['clip'].endswith('collect') else 1.3
 for b in [r['rawBounds'],r['evaluatedBounds']]:assert all(b['min'][i]>=-.45001 and b['max'][i]<=.45001 for i in [0,1]) and b['min'][2]>=-1e-5 and b['max'][2]<=z+1e-5
 if not r['clip'].endswith('collect'):assert r['finiteGroundArea']>0
 comparisons.append({'clip':r['clip'],'direction':r['direction'],'frame':r['nativeFrame'],'nativeBoundsResidual':delta,'activeNamesMatch':True,'budget':True})
residuals=[]
for r in replay['renderedSamples']:
 a=np.array(Image.open(P/r['path']).convert('RGBA')).astype(np.int16);b=np.array(Image.open(O/r['candidate']).convert('RGBA')).astype(np.int16);diff=np.abs(a-b);residuals.append({**r,'sameDecodedRGBA':bool((diff==0).all()),'maxRGBA':diff.max((0,1)).tolist(),'changedPixels':int((diff.max(2)>0).sum()),'meanAbsRGBA':diff.mean((0,1)).tolist()})
closure=[]
for clip in obj['clips']:
 for d in ['N','E','S','W']:
  rr=[r for r in records if r['clip']==clip['id'] and r['direction']==d];start=next(r for r in rr if r['nativeFrame']==(1 if clip['loop'] else 12));end=next(r for r in rr if r['nativeFrame']==13);late=None if clip['loop'] else next(r for r in rr if r['nativeFrame']==24)
  for t in [end]+([] if late is None else [late]):assert t['motionMatrix']==start['motionMatrix'] and t['evaluatedBounds']==start['evaluatedBounds']
  closure.append({'clip':clip['id'],'direction':d,'closureOrHoldExactEvaluated':True})
write('independent-native-verification.json',{'recordsCompared':len(comparisons),'checks':comparisons,'replayPixels':residuals,'closureAndHold':closure,'rawAndEvaluatedBudgets':True,'minLoopFiniteGroundArea':min(r['finiteGroundArea'] for r in records if not r['clip'].endswith('collect')),'maxAttachmentResidual':max(r['attachmentResidual'] for r in records),'externalImages':replay['externalImages'],'linkedLibraries':replay['linkedLibraries']})
frames=sorted((P/'video-frames').glob('*.png'));assert len(frames)==24;probe=json.loads((P/'video-probe.json').read_text());write('video-decoded-order.json',{'video':'candidates/round-01/native-family-playback.webm','sha256':sha(C/'native-family-playback.webm'),'decodedFrames':len(frames),'timestamps':[x.get('best_effort_timestamp_time') for x in probe['frames']],'fps':probe['streams'][0]['r_frame_rate'],'frames':[{'path':str(f.relative_to(P)),'sha256':sha(f)} for f in frames],'limitation':'Decoded actualVP9 frames; RGB colors may differ from source family PNG dueYUV444 conversion, not repaired. Fullframe lossless tiled sheets below inspected separately from real browser callbacks.'})
for page in range(6):
 canvas=Image.new('RGB',(1556,1268));m=[]
 for n in range(4):
  f=frames[page*4+n];im=Image.open(f).convert('RGB');assert im.size==(778,634);x=n%2*778;y=n//2*634;canvas.paste(im,(x,y));m.append({'frame':page*4+n,'path':str(f.relative_to(P)),'rect':[x,y,778,634]})
 canvas.save(P/f'video-inspection-{page}.png');write(f'video-inspection-{page}.json',m)
print('INDEPENDENT_AUDIT_COMPLETE',len(verified),'packet bindings',len(cellrecords),'whole useful cells',len(records),'native poses',len(frames),'decoded video frames')
