from pathlib import Path
import json,hashlib,shutil,sys,subprocess,tempfile
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-03';AT=OUT/'atlases';AT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=[];atlases=[];alpha={}
for d in 'NESW':
 p=OUT/f'native-static-{d}.png';im=Image.open(p).convert('RGBA');assert im.size==(768,1280)
 # One exact registered uniform whole-canvas downsample. No fitting, grading or edge paint.
 pub=im.resize((384,640),Image.Resampling.LANCZOS);pub.save(OUT/f'static-{d}.png');shutil.copy2(OUT/f'static-{d}.png',AT/f'static-{d}.png')
 alpha[d]={'nativeBounds':im.getbbox(),'publishedBounds':pub.getbbox(),'nativeFrameSize':list(im.size),'publishedFrameSize':list(pub.size),'clipping':bool(im.getbbox() and (im.getbbox()[0]<=0 or im.getbbox()[1]<=0 or im.getbbox()[2]>=768 or im.getbbox()[3]>=1280)),'nativeRGBAsha256':hashlib.sha256(im.tobytes()).hexdigest(),'publishedRGBAsha256':hashlib.sha256(pub.tobytes()).hexdigest()}
 raw.append({'clip':'static','direction':d,'index':0,'nativeFrame':1,'path':f'candidates/round-03/native-static-{d}.png','sha256':sha(p),'size':[768,1280]})
 atlases.append({'clip':'static','sourceClipId':'static','direction':d,'path':f'candidates/round-03/atlases/static-{d}.png','sha256':sha(AT/f'static-{d}.png'),'columns':1,'rows':1,'size':[384,640],'rects':[[0,0,384,640]]})
# Proportionate exact-registered all-facing sheets at logical and enlarged scales.
for name,scale,bgs in [('four-view-sheet',2,['#ece9e1']),('logical-four-view-sheet',1,['#808080']),('backgrounds',1,['#f4f1e9','#808080','#202c37']),('enlarged-backgrounds',2,['#f4f1e9','#202c37'])]:
 w,h=192*scale,320*scale;sheet=Image.new('RGB',(w*4,(h+24)*len(bgs)))
 draw=ImageDraw.Draw(sheet)
 for row,bg in enumerate(bgs):
  y=row*(h+24);draw.rectangle((0,y,w*4,y+h+24),fill=bg)
  for j,d in enumerate('NESW'):
   im=Image.open(OUT/f'static-{d}.png').convert('RGBA');im=im if scale==2 else im.resize((192,320),Image.Resampling.LANCZOS)
   sheet.paste(im,(j*w,y+24),im);draw.text((j*w+8,y+7),d,fill='#111111' if bg!='#202c37' else '#eeeeee')
 sheet.save(OUT/f'{name}.png')
# A modest independent sprite repetition: four facings at the declared 128px tile pitch.
placements=[('N',0,0),('E',1,0),('S',0,1),('W',1,1)]
canvas=Image.new('RGBA',(448,560),'#dce4df');draw=ImageDraw.Draw(canvas)
for y in range(3):draw.line((32,248+y*128,416,248+y*128),fill='#a9b5b0')
for x in range(4):draw.line((32+x*128,248,32+x*128,504),fill='#a9b5b0')
for d,x,y in placements:
 im=Image.open(OUT/f'static-{d}.png').resize((192,320),Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,(32+x*128,32+y*128))
canvas.convert('RGB').save(OUT/'repeated.png')
# Relocate only source + replay to prove the scene has no dependency on its original paths.
if '--skip-replay' not in sys.argv:
 with tempfile.TemporaryDirectory(prefix='column-native-relocated-') as td:
  tmp=Path(td);src=tmp/'source';src.mkdir();shutil.copy2(BASE/'source/round-03.blend',src/'round-03.blend');shutil.copy2(BASE/'source/replay-round-03.py',src/'replay-round-03.py')
  log=OUT/'portable-replay.log'
  with log.open('w') as f:subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b',str(src/'round-03.blend'),'--python',str(src/'replay-round-03.py'),'--',str(tmp/'renders')],check=True,stdout=f,stderr=subprocess.STDOUT)
  replay={}
  for d in 'NESW':
   p=tmp/f'renders/native-static-{d}.png';q=OUT/f'native-static-{d}.png';a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA')
   replay[d]={'exactPNG':sha(p)==sha(q),'exactRGBA':a.tobytes()==b.tobytes(),'replaySHA256':sha(p),'sourceSHA256':sha(q)}
  (OUT/'portable-replay.json').write_text(json.dumps({'relocated':True,'copiedFiles':['source/round-03.blend','source/replay-round-03.py'],'blendSHA256':sha(BASE/'source/round-03.blend'),'replayScriptSHA256':sha(BASE/'source/replay-round-03.py'),'views':replay,'allFourExactRGBA':all(v['exactRGBA'] for v in replay.values()),'allFourExactPNG':all(v['exactPNG'] for v in replay.values())},indent=2)+'\n')
validation=json.loads((OUT/'source-audit.json').read_text());validation['alpha']=alpha;validation['publishedSampling']={'method':'Pillow LANCZOS','nativeResolution':[768,1280],'publishedResolution':[384,640],'uniformWholeCanvasScale':.5,'alphaFitting':False,'recolor':False};validation['sourceBackupSHA256']=sha(BASE/'source/original-backup.blend');validation['portableReplay']='candidates/round-03/portable-replay.json';validation['checks']['noNativeClipping']=not any(v['clipping'] for v in alpha.values())
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'asset':'column-broken','round':3,'status':'candidate-ready-for-independent-review','pipeline':'native-3d','project':'source/round-03.blend','recipe':'source/round-03-recipe.py','validation':'candidates/round-03/validation.json','heroes':{d:f'candidates/round-03/static-{d}.png' for d in 'NESW'},'rawFrames':raw,'atlases':atlases,'previews':{k:f'candidates/round-03/{k}.png' for k in ['four-view-sheet','logical-four-view-sheet','backgrounds','enlarged-backgrounds','repeated']},'nativeRecords':{'camera':'source/round-03-camera.json','assetRecord':'source/round-03-assetRecord.json','rig':'source/round-03-rig.json'},'nativeProject':{'scene':validation['scene'],'collection':'S33_PROP_column-broken','root':'column-broken__root','frame':1,'selfContained':True,'externalResources':[],'staticFacingsDegrees':{'N':180,'E':90,'S':0,'W':-90}},'replay':{'script':'source/replay-round-03.py','command':'blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output-directory','verification':'candidates/round-03/portable-replay.json'},'evidence':{'sourceAudit':'candidates/round-03/source-audit.json','initialIndependentObservations':'source/initial-observations.json','packagingRecipe':'source/package-round-03.py','auditRecipe':'source/audit-round-03.py'},'remainingDifferences':['Simpler continuous shaft contour and stone weathering than the ImageGen target.','Symmetric native lighting yields different turning-plane highlights from the target illustration.'],'resources':[]}
(OUT/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');(BASE/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');print('PACKAGED',OUT)
