"""Publish whole canvases and package evidence. Requires Pillow. No art edits."""
import json,hashlib,shutil,subprocess,tempfile,os
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent;OUT=BASE/'candidates/round-03';NATIVE=OUT/'native';PUB=OUT/'frames';ATLAS=OUT/'atlases';PREV=OUT/'previews';RES=HERE/'resources'
for p in [PUB,ATLAS,PREV,RES]:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(BASE))
def write(p,o):Path(p).write_text(json.dumps(o,indent=2)+'\n')
for n in ['source-camera.json','source-assetRecord.json','source-rig.json','catalog-object.json','original.png','target.png']:
 shutil.copyfile(BASE/'inputs'/n,RES/n)
shutil.copyfile(BASE/'brief.json',RES/'frozen-brief.json')
shutil.copyfile(BASE/'prompts/editor.txt',RES/'editor-prompt.txt')
shutil.copyfile(BASE.parent.parent/'style/warm-soft-reference.png',RES/'warm-soft-reference.png')
shutil.copyfile(BASE.parent.parent/'prompts/native-delivery-contract.md',RES/'native-delivery-contract.md')
report=json.loads((NATIVE/'capture-validation.json').read_text());raw=[];native=[];atlases=[];alphas={}
for d in 'NESW':
 np=NATIVE/f'static-{d}.png';im=Image.open(np).convert('RGBA');assert im.size==(768,1920)
 fp=PUB/f'static-{d}.png';im.resize((384,960),Image.Resampling.LANCZOS).save(fp)
 ap=ATLAS/f'static-{d}.png';shutil.copyfile(fp,ap)
 raw.append({'clip':'static','direction':d,'index':0,'path':rel(fp),'dimensions':[384,960],'sha256':sha(fp)})
 native.append({'clip':'static','direction':d,'index':0,'path':rel(np),'dimensions':[768,1920],'sha256':sha(np),'captureScale':4})
 atlases.append({'clip':'static','direction':d,'path':rel(ap),'dimensions':[384,960],'columns':1,'rows':1,'rects':[[0,0,384,960]],'frames':1,'fps':12,'loop':False,'static':True,'sha256':sha(ap)})
 for label,p in [('native',np),('published',fp)]:
  a=Image.open(p).getchannel('A');bb=a.getbbox();alphas[d+'-'+label]={'bounds':list(bb),'canvas':list(a.size),'borderTransparent':a.crop((0,0,a.width,1)).getbbox() is None and a.crop((0,a.height-1,a.width,a.height)).getbbox() is None and a.crop((0,0,1,a.height)).getbbox() is None and a.crop((a.width-1,0,a.width,a.height)).getbbox() is None,'partialAlphaPixels':sum(1 for v in a.getdata() if 0<v<255)}
# Display comparisons retain whole transparent canvas / same logical registration.
def sprite(d,scale=1):return Image.open(PUB/f'static-{d}.png').convert('RGBA').resize((192*scale,480*scale),Image.Resampling.LANCZOS)
def sheet(name,scale=1,bg=(224,228,226,255)):
 w,h=192*scale,480*scale;im=Image.new('RGBA',(w*4,h+24*scale),bg);dr=ImageDraw.Draw(im)
 for i,d in enumerate('NESW'):dr.text((i*w+10,5),d,fill='#263E43');im.alpha_composite(sprite(d,scale),(i*w,24*scale))
 im.convert('RGB').save(PREV/name)
sheet('four-view-sheet.png',2);sheet('logical-four-view-sheet.png')
for scale,label in [(1,'logical'),(2,'enlarged')]:
 w,h=192*scale,480*scale;im=Image.new('RGBA',(w*4,(h+24*scale)*3),(0,0,0,255));dr=ImageDraw.Draw(im)
 for row,bg in enumerate([(244,236,214,255),(170,179,180,255),(23,42,55,255)]):
  for i,d in enumerate('NESW'):
   x=i*w;y=row*(h+24*scale);im.paste(bg,(x,y,x+w,y+h+24*scale));im.alpha_composite(sprite(d,scale),(x,y+24*scale));dr.text((x+10,y+4),d,fill= '#24373A' if row<2 else '#FCF0D5')
 im.convert('RGB').save(PREV/f'backgrounds-{label}.png')
im=Image.new('RGBA',(192*3,504),(224,228,226,255));dr=ImageDraw.Draw(im)
for i,(title,p) in enumerate([('Original',BASE/'inputs/original.png'),('Fixed target',BASE/'inputs/target.png'),('Native S',PUB/'static-S.png')]):
 s=Image.open(p).convert('RGBA').resize((192,480),Image.Resampling.LANCZOS);im.alpha_composite(s,(i*192,24));dr.text((i*192+8,5),title,fill='#263E43')
im.convert('RGB').save(PREV/'comparison-logical.png')
# Native replay from a relocated copy with no source directory references.
REPLAY=OUT/'portable-replay';REPLAY.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ruin-closed-replay-') as t:
 t=Path(t);shutil.copyfile(HERE/'project.blend',t/'project.blend');shutil.copyfile(HERE/'capture.py',t/'capture.py')
 with (REPLAY/'render.log').open('w') as f:subprocess.run(['blender','-b',str(t/'project.blend'),'--python',str(t/'capture.py'),'--',str(REPLAY.resolve())],stdout=f,stderr=subprocess.STDOUT,check=True)
replays=[]
for d in 'NESW':
 a=NATIVE/f'static-{d}.png';b=REPLAY/f'static-{d}.png';replays.append({'direction':d,'originalSHA256':sha(a),'replaySHA256':sha(b),'bytesIdentical':a.read_bytes()==b.read_bytes()})
write(REPLAY/'verification.json',{'relocatedProjectOnlyAndCaptureScript':True,'projectSHA256':sha(HERE/'project.blend'),'scriptSHA256':sha(HERE/'capture.py'),'renders':replays,'allBytesIdentical':all(v['bytesIdentical'] for v in replays)})
# Actual records separate native4 from published2 and nominal from measured height.
cam=json.loads((NATIVE/'camera.json').read_text());pubcam=json.loads(json.dumps(cam));pubcam['captureScale']=2;pubcam['nativeCaptureScale']=4;pubcam['nativeResolution']=[768,1920];pubcam['publishedResolution']=[384,960];pubcam['publicationSampling']='whole-canvas uniform Lanczos2:1; no crop/fit';pubcam['calibration']={k:[x*.5 for x in v] for k,v in cam['calibration'].items()};write(HERE/'published-camera.json',pubcam)
a=json.loads((RES/'source-assetRecord.json').read_text());a['scale']=2;a['nativeCaptureScale']=4;a['nativeFrame']=[768,1920];a['sourceScale']=2;a['nominalHeight']=2.18;a['measuredNativeBounds']={k:report['undeformedGeometry'][k] for k in ['min','max','dimensions']};a['artStyle']={'revision':'warm-native-round03','lighting':'Soft centered110W overhead + four equal72W cardinal fills; neutral world0.16','roughness':'stone0.88-0.9, moss0.73-0.76','lowerTone':'native world-height .71..1 overZ0..1.8','compositor':'own-scene nativeRGBA passthrough'};write(HERE/'published-assetRecord.json',a)
rig=json.loads((RES/'source-rig.json').read_text());rig['groundRootObject']='decor-ruin-fragment__ground_root';rig['source']='native static editable rebuild';rig['status']='static-native-candidate';write(HERE/'published-rig.json',rig)
checks={'nativeRootCalibration':all(abs(a-b)<.01 for a,b in zip(cam['calibration']['root'],[384,1536])),'heightWithin2_18':report['undeformedGeometry']['max'][2]<=2.18001,'undeformedFootprintWithinCell':all(x>=-.50001 for x in report['undeformedGeometry']['min'][:2]) and all(x<=.50001 for x in report['undeformedGeometry']['max'][:2]),'groundAtZero':abs(report['undeformedGeometry']['min'][2])<.00001,'projectedSilhouetteUnder3Cells':all(v['geometry']['projectedSilhouetteCells']<=3 for v in report['views']),'noClipping':all(v['borderTransparent'] for v in alphas.values()),'noExternalImageOrLibraryDependencies':not report['resources']['libraries'] and not report['resources']['images'],'staticNoActionsOrArmatures':report['staticContract']['actions']==report['staticContract']['armatures']==0,'exactReplay':all(v['bytesIdentical'] for v in replays)}
brief=json.loads((BASE/'brief.json').read_text());source=(BASE/brief['source']['project']).resolve();backup=(BASE/brief['source']['backup']).resolve()
validation={'asset':'decor-ruin-fragment','round':3,'checks':checks,'allTechnicalChecksPass':all(checks.values()),'sourceIntegrity':{'projectSHA256':sha(source),'expectedProjectSHA256':brief['source']['projectSHA256'],'backupSHA256':sha(backup),'expectedBackupSHA256':brief['source']['backupSHA256']},'frozenBriefSHA256':sha(BASE/'brief.json'),'criteriaProposalSHA256':brief['qualityCriteria']['criteriaFileSHA256'],'camera':cam,'nativeCaptureValidation':rel(NATIVE/'capture-validation.json'),'alpha':alphas,'portableReplay':rel(REPLAY/'verification.json'),'visualApproval':'Independent judge pending'}
write(OUT/'validation.json',validation)
delivery={'asset':'decor-ruin-fragment','round':3,'status':'candidate-ready-for-independent-review','pipeline':'native-3d','project':rel(HERE/'project.blend'),'recipeScript':rel(HERE/'build.py'),'recipe':rel(HERE/'settings.json'),'validation':rel(OUT/'validation.json'),'heroes':{d:rel(PUB/f'static-{d}.png') for d in 'NESW'},'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'previews':{'four-view-sheet':rel(PREV/'four-view-sheet.png'),'logical-four-view-sheet':rel(PREV/'logical-four-view-sheet.png'),'backgrounds':rel(PREV/'backgrounds-logical.png'),'enlarged-backgrounds':rel(PREV/'backgrounds-enlarged.png'),'comparison-logical':rel(PREV/'comparison-logical.png'),'repeated':'candidates/round-03/consumer/phone-repeated.png','interaction':'candidates/round-03/consumer/phone-interaction.png','phone-four-facings':'candidates/round-03/consumer/phone-four-facings.png'},'nativeRecords':{'camera':rel(HERE/'published-camera.json'),'assetRecord':rel(HERE/'published-assetRecord.json'),'rig':rel(HERE/'published-rig.json')},'nativeOriginalRecords':{'camera':rel(NATIVE/'camera.json'),'sourceCamera':rel(RES/'source-camera.json'),'sourceAssetRecord':rel(RES/'source-assetRecord.json'),'sourceRig':rel(RES/'source-rig.json')},'nativeProject':{'scene':report['scene'] if 'scene' in report else cam['scene'],'collection':'decor-ruin-fragment','root':'decor-ruin-fragment__ground_root','frame':1,'selfContained':True,'externalResources':[],'nativeResolution':[768,1920],'nativeCaptureScale':4,'publishedResolution':[384,960],'publishedSourceScale':2,'logicalFrame':[192,480],'logicalRoot':[96,384],'staticFacingsDegrees':{'N':180,'E':90,'S':0,'W':-90},'footingCorrection':'Once in worldY belowZ.42, after root facing rotation, restored after render'},'replay':{'script':rel(HERE/'capture.py'),'command':'blender -b source/round-03/project.blend --python source/round-03/capture.py -- /absolute/output-directory','verification':rel(REPLAY/'verification.json')},'evidence':{'independentObservations':'source/initial-observations.json','packagingRecipe':rel(HERE/'package.py'),'consumerRecipe':'source/round-03/consumer.mjs','consumerEvidence':'candidates/round-03/consumer/evidence.json'},'resources':[]}
# Complete source/capture/evidence closure; consumer evidence files are bound by final handoff step.
resources=[]
for folder in [HERE,OUT]:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and p.name not in ['delivery.json','packet.json'] and p.suffix!='.blend1':resources.append({'name':rel(p),'path':rel(p),'sha256':sha(p)})
delivery['resources']=resources
write(OUT/'delivery.json',delivery)
print(json.dumps({'checks':checks,'project':delivery['project'],'delivery':rel(OUT/'delivery.json'),'measuredBounds':a['measuredNativeBounds'],'replay':replays},indent=2))
