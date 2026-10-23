"""Publish exact full native canvases, create review sheets, and replay relocated saved source.
Run using a Python with Pillow: python source/package-round-01.py
"""
from pathlib import Path
import json,hashlib,shutil,subprocess,tempfile
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01';AT=OUT/'atlases';AT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=[];native=[];atlases=[];alpha={}
for d in 'NESW':
 p=OUT/f'native-static-{d}.png';im=Image.open(p).convert('RGBA');assert im.size==(768,1408)
 pub=im.resize((384,704),Image.Resampling.LANCZOS);q=OUT/f'static-{d}.png';pub.save(q);shutil.copy2(q,AT/f'static-{d}.png')
 raw.append({'clip':'static','sourceClipId':'idle','direction':d,'index':0,'path':f'candidates/round-01/static-{d}.png','size':[384,704],'sha256':sha(q)})
 native.append({'clip':'static','sourceClipId':'idle','direction':d,'index':0,'nativeFrame':1,'path':f'candidates/round-01/native-static-{d}.png','size':[768,1408],'nativeCaptureScale':4,'sha256':sha(p)})
 atlases.append({'clip':'static','sourceClipId':'idle','direction':d,'path':f'candidates/round-01/atlases/static-{d}.png','size':[384,704],'columns':1,'rows':1,'rects':[[0,0,384,704]],'frames':1,'fps':12,'static':True,'loop':False,'frameOrder':[0],'sha256':sha(AT/f'static-{d}.png')})
 b=im.getbbox();alpha[d]={'nativeBounds':b,'publishedBounds':pub.getbbox(),'clipping':b[0]<=0 or b[1]<=0 or b[2]>=768 or b[3]>=1408,'nativeRGBAsha256':hashlib.sha256(im.tobytes()).hexdigest(),'publishedRGBAsha256':hashlib.sha256(pub.tobytes()).hexdigest()}
for name,scale,bgs in [('four-view-sheet',2,['#eee8dd']),('logical-four-view-sheet',1,['#808080']),('backgrounds',1,['#f4f1e9','#808080','#202c37']),('enlarged-backgrounds',2,['#f4f1e9','#808080','#202c37'])]:
 w,h=192*scale,352*scale;sheet=Image.new('RGB',(w*4,(h+24)*len(bgs)));draw=ImageDraw.Draw(sheet)
 for row,bg in enumerate(bgs):
  y=row*(h+24);draw.rectangle((0,y,w*4,y+h+24),fill=bg)
  for j,d in enumerate('NESW'):
   im=Image.open(OUT/f'static-{d}.png').convert('RGBA');im=im if scale==2 else im.resize((192,352),Image.Resampling.LANCZOS)
   sheet.paste(im,(j*w,y+24),im);draw.text((j*w+8,y+7),d,fill='#111111' if bg!='#202c37' else '#eeeeee')
 sheet.save(OUT/f'{name}.png')
# Logical-size source/candidate/target comparison. Target retains its own imagegen geometry; it is never registered as a source sprite.
can=Image.new('RGB',(192*6,380),'#e7e4dd');draw=ImageDraw.Draw(can)
for j,(label,p) in enumerate([('Original source',BASE/'inputs/original.png')]+[(f'Native {d}',OUT/f'static-{d}.png') for d in 'NESW']+[('Style target',BASE/'inputs/target.png')]):
 im=Image.open(p).convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);can.paste(im,(j*192,28),im);draw.text((j*192+8,8),label,fill='#17232b')
can.save(OUT/'comparison-logical.png')
# Independent copies at the locked logical tile pitch, no per-view fitting.
canvas=Image.new('RGBA',(576,608),'#dce4df');draw=ImageDraw.Draw(canvas)
for y in range(3):draw.line((64,248+y*128,512,248+y*128),fill='#a9b5b0')
for x in range(4):draw.line((64+x*128,248,64+x*128,536),fill='#a9b5b0')
for d,x,y in [('N',0,0),('E',1,0),('S',0,1),('W',1,1)]:
 im=Image.open(OUT/f'static-{d}.png').resize((192,352),Image.Resampling.LANCZOS);canvas.alpha_composite(im,(64+x*128,32+y*128))
canvas.convert('RGB').save(OUT/'repeated.png')
with tempfile.TemporaryDirectory(prefix='starfish-native-relocated-') as td:
 tmp=Path(td);src=tmp/'source';src.mkdir();shutil.copy2(BASE/'source/round-01.blend',src/'round-01.blend');shutil.copy2(BASE/'source/replay-round-01.py',src/'replay-round-01.py')
 with (OUT/'portable-replay.log').open('w') as f:subprocess.run(['blender','-b',str(src/'round-01.blend'),'--python',str(src/'replay-round-01.py'),'--',str(tmp/'renders')],check=True,stdout=f,stderr=subprocess.STDOUT)
 replay={}
 # Preserve actual replay files and source's measured replay records, not only booleans.
 replaydir=OUT/'replay';replaydir.mkdir(exist_ok=True)
 for d in 'NESW':
  p=tmp/f'renders/native-static-{d}.png';q=OUT/f'native-static-{d}.png';a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');pub=a.resize((384,704),Image.Resampling.LANCZOS)
  shutil.copy2(p,replaydir/p.name);pubpath=replaydir/f'published-static-{d}.png';pub.save(pubpath)
  replay[d]={'exactPNG':sha(p)==sha(q),'exactRGBA':a.tobytes()==b.tobytes(),'exactPublishedRGBA':pub.tobytes()==Image.open(OUT/f'static-{d}.png').convert('RGBA').tobytes(),'exactPublishedPNG':sha(pubpath)==sha(OUT/f'static-{d}.png'),'publishedReplayPath':f'candidates/round-01/replay/published-static-{d}.png','replaySHA256':sha(p),'sourceSHA256':sha(q),'path':f'candidates/round-01/replay/{p.name}'}
 shutil.copy2(tmp/'renders/native-capture.json',replaydir/'native-capture.json')
 (OUT/'portable-replay.json').write_text(json.dumps({'relocated':True,'copiedFiles':['source/round-01.blend','source/replay-round-01.py'],'blendSHA256':sha(BASE/'source/round-01.blend'),'replayScriptSHA256':sha(BASE/'source/replay-round-01.py'),'views':replay,'allFourExactRGBA':all(v['exactRGBA'] for v in replay.values()),'allFourExactPNG':all(v['exactPNG'] for v in replay.values()),'PNGMetadataNote':'Blender writes source path,Date and render timing metadata. Native replay pixel buffers are exact; metadata is retained honestly rather than stripped.','allFourExactPublishedRGBA':all(v['exactPublishedRGBA'] for v in replay.values())},indent=2)+'\n')
validation=json.loads((OUT/'source-audit.json').read_text());validation['alpha']=alpha;validation['publishedSampling']={'method':'Pillow LANCZOS','nativeCaptureScale':4,'publishedSourceScale':2,'nativeResolution':[768,1408],'publishedResolution':[384,704],'uniformWholeCanvasScale':.5,'alphaFitting':False,'recolor':False};validation['originalSourceSHA256']=sha(BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend');validation['originalBackupSHA256']=sha(BASE/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend');validation['portableReplay']='candidates/round-01/portable-replay.json';validation['checks']['noNativeClipping']=not any(v['clipping'] for v in alpha.values());validation['checks']['allFourPortableReplaysExact']=all(v['exactRGBA'] and v['exactPublishedRGBA'] for v in replay.values())
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'asset':'decor-starfish','round':1,'status':'candidate-ready-for-independent-review','pipeline':'native-3d','project':'source/round-01.blend','recipeScript':'source/round-01-recipe.py','recipe':'source/round-01-settings.json','validation':'candidates/round-01/validation.json','heroes':{d:f'candidates/round-01/static-{d}.png' for d in 'NESW'},'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'previews':{k:f'candidates/round-01/{k}.png' for k in ['four-view-sheet','logical-four-view-sheet','backgrounds','enlarged-backgrounds','comparison-logical','repeated']},'nativeRecords':{'camera':'source/round-01-published-camera.json','assetRecord':'source/round-01-published-assetRecord.json','rig':'source/round-01-rig.json'},'nativeOriginalRecords':{'camera':'source/round-01-native-camera.json','assetRecord':'source/round-01-native-assetRecord.json','sourceCamera':'inputs/source-camera.json','sourceAssetRecord':'inputs/source-assetRecord.json','sourceRig':'inputs/source-rig.json'},'nativeProject':{'scene':validation['scene'],'collection':validation['collection'],'root':validation['rootObject'],'frame':1,'selfContained':True,'externalResources':[],'staticFacingsDegrees':{'N':180,'E':90,'S':0,'W':-90},'nativeResolution':[768,1408],'nativeCaptureScale':4,'publishedResolution':[384,704],'publishedSourceScale':2,'logicalFrame':[192,352],'logicalRoot':[96,248]},'replay':{'script':'source/replay-round-01.py','command':'blender -b source/round-01.blend --python source/replay-round-01.py -- /absolute/output-directory','verification':'candidates/round-01/portable-replay.json'},'evidence':{'sourceAudit':'candidates/round-01/source-audit.json','initialIndependentObservations':'source/initial-observations.json','packagingRecipe':'source/package-round-01.py','auditRecipe':'source/audit-round-01.py'},'remainingDifferences':['Native symmetric lighting and smooth cream nodules differ from the illustrated highlight shapes and faceted nodules.','Rounded five-arm contour and sparse cream detail preserve the low scenery scale.'],'resources':[]}
(BASE/'source/round-01-settings.json').write_text(json.dumps({'render':validation['camera']['render'],'publicationSampling':validation['publishedSampling'],'build':'blender -b --python source/round-01-recipe.py','closedSceneReplay':delivery['replay'],'buildInputs':['source/round-01-recipe.py','inputs/source-camera.json','source/replay-round-01.py'],'sourceClosure':'saved blend has native geometry/materials/camera/light only; no external image/library dependencies'},indent=2)+'\n')
(OUT/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');print('PACKAGED',OUT)
