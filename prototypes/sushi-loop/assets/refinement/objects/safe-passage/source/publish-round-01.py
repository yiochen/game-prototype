"""Uniform whole-canvas publication and explicit native evidence checks, no art repairs."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json, hashlib, shutil, math
from PIL import Image, ImageDraw

BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,v):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def rec(p,**extra):return {'path':str(p.relative_to(BASE)),'sha256':sha(p),'bytes':p.stat().st_size,**extra}
def composite(im,bg):
 out=Image.new('RGBA',im.size,bg);out.alpha_composite(im);return out.convert('RGB')
native=json.loads((OUT/'native-validation.json').read_text());scene=json.loads((OUT/'native-scene-record.json').read_text());camera=json.loads((OUT/'native-camera.json').read_text())
frozen=json.loads((BASE/'reviews/preparation-v1/camera-measured.json').read_text())
def maxdelta(a,b):
 if isinstance(a,list):return max(maxdelta(x,y) for x,y in zip(a,b))
 return abs(a-b)
camera_errors={k:maxdelta(camera['camera'][k],frozen['camera'][k]) for k in ['worldMatrix','projectionMatrix','pixelAspect']}
assert max(camera_errors.values())<1e-6,camera_errors
assert len(native['captureRecords'])==48
frames=[];nativeframes=[];atlases=[];alphastats=[];maps=[]
durations=[83,83,84]*4
for direction in 'NESW':
 atlas=Image.new('RGBA',(2304,1408));ims=[];originals=[];rects=[]
 for index in range(12):
  p=OUT/f'native/ambient/{direction}/{index:03d}.png';im=Image.open(p).convert('RGBA');assert im.size==(768,1408)
  q=OUT/f'frames/ambient/{direction}/{index:03d}.png';q.parent.mkdir(parents=True,exist_ok=True)
  published=im.resize((384,704),Image.Resampling.LANCZOS);published.save(q)
  x=(index%6)*384;y=(index//6)*704;atlas.paste(published,(x,y));rects.append([x,y,384,704]);ims.append(published);originals.append(q)
  for label,img in [('native',im),('published',published)]:
   a=img.getchannel('A');edge=max(max(a.crop((0,0,img.width,1)).getdata()),max(a.crop((0,img.height-1,img.width,img.height)).getdata()),max(a.crop((0,0,1,img.height)).getdata()),max(a.crop((img.width-1,0,img.width,img.height)).getdata()))
   assert edge==0
   alphastats.append({'direction':direction,'index':index,'layer':label,'alphaBounds':a.getbbox(),'edgeAlphaMax':edge,'alphaRange':a.getextrema()})
  frames.append(rec(q,clip='ambient',direction=direction,index=index,frame=index,dimensions=[384,704]))
  nativeframes.append(rec(p,clip='ambient',direction=direction,index=index,frame=index,dimensions=[768,1408]))
 p=OUT/f'atlases/ambient-{direction}.png';p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p)
 atlases.append(rec(p,clip='ambient',direction=direction,size=[2304,1408],columns=6,rows=2,rects=rects))
 hero=OUT/f'heroes/{direction}.png';hero.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(originals[0],hero)
 preview=OUT/f'previews/ambient-{direction}.png';preview.parent.mkdir(parents=True,exist_ok=True)
 ims[0].save(preview,save_all=True,append_images=ims[1:],duration=durations,loop=0,disposal=0,blend=0)
 sheet=Image.new('RGB',(1152,752),'#eeeeee');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  x=(i%6)*192;y=(i//6)*376;logical=im.resize((192,352),Image.Resampling.LANCZOS)
  sheet.paste(composite(logical,'#eeeeee'),(x,y+24));d.text((x+5,y+6),f'{direction} {i:02d} · {i}/12s',fill='#111111')
  maps.append({'sheet':f'candidates/round-01/sheets/phase-{direction}.png','cell':[x,y+24,192,352],'direction':direction,'index':i,'source':frames[-12+i]['path'],'sourceSHA256':frames[-12+i]['sha256'],'wholeFrame':True})
 p=OUT/f'sheets/phase-{direction}.png';p.parent.mkdir(parents=True,exist_ok=True);sheet.save(p)

# Registered complete-frame four-facing/three-background hero sheet.
sheet=Image.new('RGB',(768,1152),'#eeeeee');d=ImageDraw.Draw(sheet)
for row,(name,bg) in enumerate([('light','#eeeeee'),('gray','#777777'),('dark','#121820')]):
 for col,direction in enumerate('NESW'):
  im=Image.open(OUT/f'heroes/{direction}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS)
  x=col*192;y=row*384;sheet.paste(composite(im,bg),(x,y+24));d.text((x+6,y+6),direction+' · '+name,fill='#111' if name=='light' else '#fff')
sheet.save(OUT/'previews/four-view-sheet.png')
motion=[]
for index in range(12):
 im=Image.new('RGBA',(768,376),'#eeeeee');draw=ImageDraw.Draw(im)
 for col,direction in enumerate('NESW'):
  frame=Image.open(OUT/f'frames/ambient/{direction}/{index:03d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS)
  im.alpha_composite(frame,(col*192,24));draw.text((col*192+6,6),f'{direction} {index:02d}',fill='#111')
 motion.append(im)
motion[0].save(OUT/'previews/motion.png',save_all=True,append_images=motion[1:],duration=durations,loop=0,disposal=0,blend=0)
# Explicit enlarged diagnostic region only; production frames above remain full registered canvases.
detail=Image.open(OUT/'native/ambient/S/000.png').convert('RGBA').crop((120,670,370,900)).resize((750,690),Image.Resampling.NEAREST)
composite(detail,'#777777').save(OUT/'sheets/enlarged-foliage-S-frame00.png')
write('phase-cell-map.json',{'cells':maps,'all48FullFramesShown':True,'presentationOnlySampling':'Uniform full registered published2x canvas to logical1x LANCZOS; no occupied-bounds fitting. Enlarged diagnostic crop is explicitly separate from delivered art.','enlargedDiagnostic':{'path':'candidates/round-01/sheets/enlarged-foliage-S-frame00.png','nativeSource':'candidates/round-01/native/ambient/S/000.png','nativeCrop':[120,670,250,230],'scale':3,'sampling':'NEAREST'},'APNGPreviews':{'durationMilliseconds':durations,'loop':True,'source':'all12 submitted published native frames; never consumed by drawImage as a runtime atlas'}})

budget={'min':[-.5,-.5,-.05],'max':[.5,.5,.53]};failures=[];allgm=[]
for r in native['captureRecords']:
 gm=r['geometry'];allgm.append(gm)
 for kind in ['rawAuthoredBoundsCanonicalS','evaluatedBoundsCanonicalS']:
  for j in range(3):
   if gm[kind]['min'][j]<budget['min'][j]-1e-5 or gm[kind]['max'][j]>budget['max'][j]+1e-5:failures.append([r['direction'],r['index'],kind,j])
 assert all(s['finiteContact'] for s in gm['stoneSupports'])
 assert all(a['pivotInsideStone'] and a['baseVertexAtPivot'] for a in gm['foliageAttachments'])
assert not failures,failures
stability={};closure={}
for direction in 'NESW':
 records=[r for r in native['captureRecords'] if r['direction']==direction]
 first=records[0]['geometry'];byname={o['object']:o for o in first['objects']}
 stable=[]
 for r in records:
  for o in r['geometry']['objects']:
   if o['role']!='attached_foliage':stable.append(maxdelta(o['matrixLocal'],byname[o['object']]['matrixLocal']))
 stability[direction]={'stableStoneAndGuideLocalMatrixDeltaMax':max(stable),'rootMatrixDeltaMax':max(maxdelta(r['rootMatrix'],records[0]['rootMatrix']) for r in records)}
 last=native['closureFrame13'][direction]['geometry']
 closure[direction]={'frame1GeometryFingerprint':first['geometryFingerprint'],'frame13GeometryFingerprint':last['geometryFingerprint'],'geometryExact':first['geometryFingerprint']==last['geometryFingerprint'],'maxObjectMatrixDelta':max(maxdelta(a['matrixWorld'],b['matrixWorld']) for a,b in zip(first['objects'],last['objects']))}
 assert closure[direction]['geometryExact'] and closure[direction]['maxObjectMatrixDelta']==0
 assert stability[direction]['stableStoneAndGuideLocalMatrixDeltaMax']==0
counts={direction:len({hashlib.sha256(Image.open(OUT/f'frames/ambient/{direction}/{i:03d}.png').tobytes()).hexdigest() for i in range(12)}) for direction in 'NESW'}
assert min(counts.values())>=6
aggregate={kind:{'min':[min(g[kind]['min'][i] for g in allgm) for i in range(3)],'max':[max(g[kind]['max'][i] for g in allgm) for i in range(3)]} for kind in ['rawAuthoredBoundsCanonicalS','evaluatedBoundsCanonicalS']}
checks={'cameraMatrixMaxErrorsVersusFrozen':camera_errors,'nativePublishedFrameCounts':[len(nativeframes),len(frames)],'allphaseCanonicalBudget':budget,'allphaseBounds':aggregate,'allphaseBudgetViolations':failures,'allphaseStoneFiniteZ0Contact':True,'allphaseLeafPivotInsideAssignedStone':True,'stability':stability,'loopClosure':closure,'publishedUniqueDecodedFrameCounts':counts,'existingMinimumUniqueFrames':6,'alphaFrames':alphastats,'sourceUnchangedAfterCapture':native['sourceUnchangedAfterCapture'],'publication':'One whole-canvas LANCZOS 768x1408 ->384x704; atlas exact original6x2 cells, no per-view/color/alpha processing.'}
write('native-checks.json',checks)
published=json.loads(json.dumps(camera));published['captureScale']=2
published['calibration']={k:[v/2 for v in value] for k,value in camera['calibration'].items()}
published['publication']={'nativeFrame':[768,1408],'nativeCaptureScale':4,'nativeRoot':camera['calibration']['root'],'publishedFrame':[384,704],'publishedSourceScale':2,'publishedRoot':[192,496],'sampling':'whole-canvas Pillow LANCZOS'}
write('published-camera.json',published)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'safe-passage-warm-soft-round-01','lighting':'150W broad warm overhead plus four equal45W cardinal soft fills, world strength.10','materials':'native blue/green height color ramps, broad bevels and closed thick leaves; Standard view without compositor contrast'}
write('assetRecord.json',asset)
rig={'assetId':'safe-passage','fps':12,'source':'build-round-01-v2.py','static':False,'clips':{'ambient':{'frames':12,'fps':12,'loop':True,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13,'actions':[{k:a[k] for k in ['ownerType','ownerName','action','slotIdentifier','keyframeCount']} for a in scene['actions']],'controlsByFrame':[{} for _ in range(12)],'geometryOwners':[],'shaderChannels':[]}},'armatures':[],'footprint':[1,1],'projection':'square-top-front-oblique','groundRootObject':'safe-passage__root','sockets':{},'actionCount':len(scene['actions']),'status':'native-actions-authored-pending-independent-visual-review','sourceFiles':{'build-round-01-v2.py':sha(BASE/'source/build-round-01-v2.py')},'loopClosure':closure,'notes':['Ten closed leaf meshes pivot inside stone supports; calm localEuler action channels.','Runtime12 phase slots exclude native closing13; no attachment ports or collision behavior added.','Historical raw native action baker is not represented as candidate recipe.']}
write('rig.json',rig)
write('publication-manifest.json',{'asset':'safe-passage','pathBase':'object experiment','rawFrames':frames,'nativeRawFrames':nativeframes,'atlases':atlases,'heroes':{d:f'candidates/round-01/heroes/{d}.png' for d in 'NESW'},'publication':checks['publication']})
print(json.dumps({'frames':len(frames),'native':len(nativeframes),'uniqueCounts':counts,'allphaseBounds':aggregate,'nativeChecks':'candidates/round-01/native-checks.json'}))
