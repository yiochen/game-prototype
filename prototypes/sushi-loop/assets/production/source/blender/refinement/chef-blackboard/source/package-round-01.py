"""Uniform capture downsample, original-layout atlas assembly and evidence.
This does not paint/change source-rendered art. Native 768x1408 ->384x704 LANCZOS.
Requires Pillow and only bound local input resources plus candidate native frames.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,hashlib,math,copy
P=Path(__file__).resolve().parent;O=P.parent;C=O/'candidates/round-01';R=P/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(O))
def save(im,path):path.parent.mkdir(parents=True,exist_ok=True);im.save(path);return path
font=ImageFont.load_default(size=14)
small=ImageFont.load_default(size=12)
native=json.loads((C/'native-validation.json').read_text());orig=json.loads((P/'source-animation-bounds.json').read_text());catalog=json.loads((R/'original-catalog.json').read_text())
raw=[];nativeCaptures=[];atlases=[];previews=[];by={}
for cl in catalog['clips']:
 clip=cl['id'];by[clip]=[];d=cl['directions']['S'];atlas=Image.new('RGBA',tuple(d['atlasSize']),(0,0,0,0))
 for i in range(cl['frames']):
  src=C/'raw'/(clip+'-S')/f'{i:03d}.png';im=Image.open(src).convert('RGBA');assert im.size==(768,1408)
  nativeCaptures.append({'clip':clip,'direction':'S','index':i,'path':rel(src),'size':list(im.size),'sha256':sha(src)})
  frame=im.resize((384,704),Image.Resampling.LANCZOS);out=save(frame,C/'frames'/f'{clip}-S-{i:03d}.png');by[clip].append(frame)
  raw.append({'clip':clip,'direction':'S','index':i,'path':rel(out),'size':[384,704],'sha256':sha(out)})
  r=d['rects'][i];assert r[2:]==[384,704];atlas.paste(frame,(r[0],r[1]))
 out=save(atlas,C/'atlases'/(clip+'-S.png'))
 for i,r in enumerate(d['rects']):
  crop=atlas.crop((r[0],r[1],r[0]+r[2],r[1]+r[3]));assert crop.tobytes()==by[clip][i].tobytes()
 atlases.append({'clip':clip,'sourceClipId':cl['sourceClipId'],'direction':'S','path':rel(out),'columns':d['columns'],'rows':d['rows'],'size':d['atlasSize'],'rects':d['rects'],'frameOrder':cl['frameOrder'],'fps':cl['fps'],'loop':cl['loop'],'static':cl['static'],'sha256':sha(out)})
hero=save(by['idle'][0],C/'hero-S.png')
def panel(frames,columns,size=(192,352),labels=None,background=(235,232,221,255),crop=None):
 n=len(frames);h=size[1]+24;im=Image.new('RGBA',(columns*size[0],math.ceil(n/columns)*h),background);draw=ImageDraw.Draw(im)
 for i,f in enumerate(frames):
  x=(i%columns)*size[0];y=(i//columns)*h
  if crop:f=f.crop(crop)
  f=f.resize(size,Image.Resampling.LANCZOS);im.alpha_composite(f,(x,y+24));draw.text((x+7,y+5),labels[i] if labels else str(i),fill='#303b43',font=small)
 return im

def preview(n,im,kind,**kw):
 out=save(im,C/(n+'.png'));previews.append({'id':n,'kind':kind,'path':rel(out),'size':list(im.size),'sha256':sha(out),**kw})
preview('four-view-sheet',panel([by['idle'][0]]*4,4,labels=['S · only registered view']*4),'generic-alias-repeated-single-S')
preview('idle-enlarged',panel([by['idle'][0]],1,size=(384,704),labels=['S idle · source scale2']),'registered-enlarged-idle')
preview('idle-logical',panel([by['idle'][0]],1,labels=['S idle · logical192×352']),'registered-logical-idle')
for clip in ['selected','recipe-change']:
 fs=by[clip];preview(clip+'-S',panel(fs,6,labels=[f'{clip} S {i:02d}' for i in range(12)]),'all-twelve-registered-logical-frames')
 # One fixed registration-space crop for every frame; this is visual evidence only.
 preview(clip+'-S-detail',panel(fs,6,size=(224,248),crop=(80,384,304,632),labels=[f'{i:02d}' for i in range(12)]),'all-twelve-unmodified-common-region-detail')
 anim=[f.resize((192,352),Image.Resampling.LANCZOS) for f in fs];out=C/(clip+'-S.webp');anim[0].save(out,save_all=True,append_images=anim[1:],lossless=True,duration=[83,83,84]*4,loop=0 if clip=='selected' else 1,method=6)
 previews.append({'id':clip+'-S-playback','kind':'12fps-logical-playback','path':rel(out),'size':[192,352],'frames':12,'fps':12,'loop':clip=='selected','sha256':sha(out)})
# Idle transparency on three neutral values, with real source alpha preserved.
bgs=Image.new('RGBA',(576,376));draw=ImageDraw.Draw(bgs)
for i,(col,label) in enumerate([('#f2eee4','light'),('#92999b','gray'),('#202c34','dark')]):
 tile=Image.new('RGBA',(192,376),col);tile.alpha_composite(by['idle'][0].resize((192,352),Image.Resampling.LANCZOS),(0,24));ImageDraw.Draw(tile).text((7,6),label,fill='white' if i else '#303b43',font=font);bgs.alpha_composite(tile,(192*i,0))
preview('transparency-backgrounds',bgs,'real-alpha-light-gray-dark')
# Comparison has constant registered sizes; no source or target fitting.
original=Image.open(R/'original.png').convert('RGBA');assert original.size==(384,704)
preview('source-candidate-logical',panel([original,by['idle'][0]],2,labels=['untouched source','native candidate']),'registered-original-candidate-comparison')
# Literal repeated player-facing instances at runtime cell pitch128.
repeat=Image.new('RGBA',(640,528),'#ece6d6');d=ImageDraw.Draw(repeat)
for i in range(4):d.line((64+i*128,176,64+i*128,488),fill='#c8bdab',width=1)
for i in range(3):d.line((64,232+i*128,576,232+i*128),fill='#c8bdab',width=1)
for x in [192,320,448]:repeat.alpha_composite(by['idle'][0].resize((192,352),Image.Resampling.LANCZOS),(x-96,344-248))
d.text((16,16),'Repeated S · registered roots one cell apart ·128 logical px/cell',fill='#303b43',font=small)
preview('repeated',repeat,'independent-runtime-alpha-composition',rootPitch=128)
# Catalog interaction: board foreground and chef share root; belt at y+1.
context=Image.new('RGBA',(640,784),'#e9e2d1');draw=ImageDraw.Draw(context);ctx={x['asset']:x for x in json.loads((R/'context-provenance.json').read_text())}
def sprite(canvas,aid,root_xy,factor=1):
 rec=ctx[aid];im=Image.open(O/rec['resource']).convert('RGBA');sz=tuple(round(v*factor/rec['sourceScale']) for v in im.size);im=im.resize(sz,Image.Resampling.LANCZOS);anchor=[round(v*factor) for v in rec['root']];canvas.alpha_composite(im,(round(root_xy[0]-anchor[0]),round(root_xy[1]-anchor[1])))
for y in range(4):
 for x in range(4):sprite(context,'floor-cream',(128+128*x,264+128*y))
base=(256,392);sprite(context,'chef-lena',base);sprite(context,'belt-straight-e',(base[0],base[1]+128));context.alpha_composite(by['idle'][0].resize((192,352),Image.Resampling.LANCZOS),(base[0]-96,base[1]-248))
draw=ImageDraw.Draw(context);draw.text((16,16),'Catalog interaction · chef+blank board share exact root',fill='#303b43',font=font);draw.text((16,38),'Original registered sprites;128 logical px/cell; foreground board',fill='#303b43',font=small)
preview('chef-cooccupancy',context,'catalog-independent-alpha-context',placements=[{'asset':'chef-lena','cell':[1,1],'rootLogical':list(base)},{'asset':'chef-blackboard','cell':[1,1],'rootLogical':list(base),'renderPass':'foreground'},{'asset':'belt-straight-e','cell':[1,2],'rootLogical':[base[0],base[1]+128]}])
# Optional runtime overlay demonstration is a separate preview, never baked art.
blank=by['idle'][0];demo=blank.copy();socket=native['nativeRecords'][0]['socket']['projectedRawPixels'];socket=[q/2 for q in socket]
sprite(demo,'dish-salmon',socket,factor=.56) #256 output px cell * .28 overlay scale
preview('blank-display-and-runtime-overlay',panel([blank,demo],2,size=(384,704),labels=['Exported blank native face','Preview-only runtime dish at unchanged socket']),'blank-export-versus-separate-runtime-overlay',socketAtlasPixels=socket,runtimeOverlayRule='Godot pitch*.28; dynamic dish sprite separately alpha-composited')
# Publication camera truth: registered logical frame/sourceScale2, native truth separate.
records=C/'records';records.mkdir(exist_ok=True)
cam=copy.deepcopy(json.loads((R/'registered-camera.json').read_text()));cam['captureScale']=2;cam['nativeCaptureScale']=4;cam['nativeCaptureFrame']=[768,1408];cam['publishedPixelFrame']=[384,704];cam['calibration']={k:[v/2 for v in vals] for k,vals in cam['calibration'].items()};cam['artStyle']={'revision':'warm-soft-native-chef-blackboard-round01','lighting':'Neutral surrounding world, centered overhead and four equal cardinal fills','preferredHorizontalLightDirection':False}
asset=copy.deepcopy(json.loads((O/'inputs/source-assetRecord.json').read_text())) if (O/'inputs/source-assetRecord.json').exists() else copy.deepcopy(json.loads((R/'asset-original.json').read_text()))
asset['scale']=2;asset['nativeCaptureScale']=4;asset['nativeCaptureFrame']=[768,1408];asset['artStyle']=cam['artStyle']
rig=copy.deepcopy(json.loads((R/'original-rig.json').read_text()));rig['refinement']={'originalActionCurvesAndSlotsUnchanged':True,'addedGeometryBinding':'Rounded caps parent to original posts; brass pegs parent to original rails','blend':'source/round-01.blend'}
for name,data in [('camera.json',cam),('assetRecord.json',asset),('rig.json',rig)]:
 (records/name).write_text(json.dumps(data,indent=2)+'\n')
# Compact measured comparison with source for every original pose.
assert len(orig['records'])==len(native['nativeRecords'])==25
faceDeltas=[];contactDeltas=[]
for old,new in zip(orig['records'],native['nativeRecords']):
 assert (old['clip'],old['frame'])==(new['clip'],new['frame'])
 faceDeltas.append(max(abs(old['faceMatrix'][i][j]-new['face']['matrix'][i][j]) for i in range(4) for j in range(4)))
 contactDeltas.append(new['bounds'][0][2]-old['bounds'][0][2])
assert max(faceDeltas)<1e-7 and max(map(abs,contactDeltas))<1e-7
assert all(x['bounds'][0][1]>=-.500001 and x['bounds'][1][1]<=-.269999 and x['bounds'][1][2]<=1.000001 for x in native['nativeRecords'])
unique={k:len({hashlib.sha256(f.tobytes()).hexdigest() for f in v}) for k,v in by.items()};assert unique['selected']>=6 and unique['recipe-change']>=6
v={'asset':'chef-blackboard','round':'round-01','fullNativeValidation':rel(C/'native-validation.json'),'nativeRecords':rel(C/'native-validation.json'),'nativeCaptureFrames':25,'publishedFrames':25,'uniformScaleDownsample':{'native':[768,1408],'published':[384,704],'method':'Pillow LANCZOS','axisScale':[.5,.5],'noArtRetouch':True},'publicationCamera':rel(records/'camera.json'),'frames':[{'clip':r['clip'],'frame':r['frame'],'direction':'S','rootMatrix':r['rootMatrix'],'cameraWorldMatrix':r['cameraWorldMatrix'],'cameraProjectionMatrix':r['cameraProjectionMatrix']} for r in native['nativeRecords']],'registeredCameraMaxDelta':native['registeredCameraMaxDelta'],'registeredProjectionMaxDelta':native['registeredProjectionMaxDelta'],'originalFacePerFrameMaxMatrixDelta':max(faceDeltas),'originalGroundContactPerFrameMaxDelta':max(map(abs,contactDeltas)),'animatedBoundsUnion':[[min(r['bounds'][0][axis] for r in native['nativeRecords']) for axis in range(3)],[max(r['bounds'][1][axis] for r in native['nativeRecords']) for axis in range(3)]],'display':{'blank':True,'socket':[0,-.434,.61],'frontPlaneY':-.4275,'outwardClearance':native['nativeRecords'][0]['socket']['facePlaneOutwardClearance'],'allFramesInsideFaceXZ':all(r['socket']['insideFaceXZ'] for r in native['nativeRecords']),'previewOnlyDynamicOverlay':rel(C/'blank-display-and-runtime-overlay.png')},'animation':{'fps':12,'uniquePublishedFrames':unique,'selectedLoop':native['selectedLoopClosure'],'recipeChangeLoop':False,'unchangedOriginal30Actions':True,'inheritedRecipeChangeGroundBob':'Original native recipe_change action moves all parts vertically by up to±.0089767. Its original ground contact extrema are preserved exactly; root is fixed.'},'dependencyClosure':native['dependencies'],'sourceIntegrity':{'originalLibrarySHA256':sha(P/'original-library.blend'),'declaredOriginalSHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'},'closedReplay':'candidates/round-01/closed-replay.json','noSelfApproval':True}
(C/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
(C/'atlas-manifest.json').write_text(json.dumps({'atlases':atlases,'rawFrames':raw,'nativeCaptures':nativeCaptures},indent=2)+'\n')
resources=[]
# Everything needed for portable source capture, assembly and the unchanged build source.
for p in sorted(P.rglob('*')):
 if p.is_file() and p.suffix!='.blend1':resources.append({'name':rel(p).replace('/','__'),'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size})
for p in [C/'native-validation.json',C/'closed-replay.json',C/'atlas-manifest.json',*sorted(records.glob('*.json'))]:
 resources.append({'name':rel(p).replace('/','__'),'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size})
delivery={'asset':'chef-blackboard','round':'round-01','status':'candidate-ready-for-independent-review','project':'source/round-01.blend','projectSHA256':sha(P/'round-01.blend'),'recipe':'source/round-01-recipe.json','recipeScript':'source/round-01-recipe.py','captureScript':'source/capture-round-01.py','supportingRecipes':['source/package-round-01.py'],'validation':rel(C/'validation.json'),'heroes':[{'direction':'S','path':rel(hero),'size':[384,704]}],'rawFrames':raw,'nativeCaptures':nativeCaptures,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(records/'camera.json'),'assetRecord':rel(records/'assetRecord.json'),'rig':rel(records/'rig.json')},'resources':resources,'notes':['Only S is registered; four-view-sheet repeats S as a generic preview alias.','All exported pixels come from the closed editable Blender project, uniformly downsampled; no paintover, imagegen raster substitute, fitted camera or per-frame fitting.','Native original-selected frame13 closure is excluded from the 12-frame runtime atlas.','Original action keys/slots, blank face plane and per-frame location, ground root and inherited recipe-change ground bob retained.','Root coordinator creates immutable packet and independent judge reviews exact bytes.']}
(O/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
print(json.dumps({'rawFrames':len(raw),'nativeCaptures':len(nativeCaptures),'atlases':len(atlases),'previews':len(previews),'unique':unique,'animatedBoundsUnion':v['animatedBoundsUnion'],'faceMaxDelta':max(faceDeltas)},indent=2))
