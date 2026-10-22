"""Pack exact native pixels, original atlas rectangles and clearly labeled review contexts."""
from pathlib import Path
import json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-02';DIRECTIONS=['N','E','S','W'];CLIPS=['idle','work','hold','load']
BG={'light':'#f3eee2','gray':'#858b8b','dark':'#202a31'}
def font(s=18):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',s)
 except OSError:return ImageFont.load_default()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def composite(im,bg):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
def frame(c,d,i):return OUT/'frames'/(c+'-'+d)/(f'{i:03d}.png')
raw=[];atlases=[];videos=[];previews={};alpha=[];sheets=[]
for folder in ['atlases','playbacks','contact-sheets','native-records','resources']: (OUT/folder).mkdir(exist_ok=True)
for clip in CLIPS:
 for direction in DIRECTIONS:
  ims=[];atlas=Image.new('RGBA',(2304,1280));sheet_by_bg={k:Image.new('RGB',(1152,704),col) for k,col in BG.items()};rects=[]
  for i in range(12):
   path=frame(clip,direction,i);im=rgba(path);assert im.size==(384,640);ims.append(im);x=i%6*384;y=i//6*640;atlas.paste(im,(x,y));rects.append([x,y,384,640])
   row={'clip':clip,'direction':direction,'index':i,'path':rel(path),'sha256':sha(path)};raw.append(row);bb=im.getchannel('A').getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<384 and bb[3]<640,(clip,direction,i,bb)
   alpha.append({**row,'alphaBounds':bb,'frame':[384,640],'clipped':False})
   logical=im.resize((192,320),Image.Resampling.LANCZOS)
   for bg,col in BG.items():
    sheet=sheet_by_bg[bg];sx=i%6*192;sy=i//6*352;sheet.paste(composite(logical,col),(sx,sy+28));ImageDraw.Draw(sheet).text((sx+5,sy+5),f'{clip} {direction} · {i:02d}',font=font(16),fill='#e8e8df' if bg=='dark' else '#28323b')
  atlaspath=OUT/'atlases'/(clip+'-'+direction+'.png');atlas.save(atlaspath,compress_level=9);check=rgba(atlaspath)
  for i,im in enumerate(ims):
   x,y,w,h=rects[i];assert check.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
  atlases.append({'clip':clip,'direction':direction,'path':rel(atlaspath),'sha256':sha(atlaspath),'hash':sha(atlaspath),'size':[2304,1280],'columns':6,'rows':2,'rects':rects,'fps':12,'loop':clip!='load','frameOrder':list(range(12))})
  for bg,sheet in sheet_by_bg.items():
   path=OUT/'contact-sheets'/(clip+'-'+direction+'-'+bg+'.png');sheet.save(path);previews['all-frames-'+clip+'-'+direction+'-'+bg]=rel(path)
   sheets.append({'clip':clip,'direction':direction,'background':bg,'path':rel(path),'sha256':sha(path),'frameIndices':list(range(12)),'logicalImageSize':[192,320],'method':'same full native canvas resized by exactly0.5 Lanczos; alpha composited only for labeled review context','sourceFrames':[r for r in raw[-12:]]})
  vp=OUT/'playbacks'/(clip+'-'+direction+'.mp4')
  subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','12','-i',str(frame(clip,direction,0).parent/'%03d.png'),'-f','lavfi','-i','color=c=0xd1d0c7:s=384x640:r=12:d=1','-filter_complex','[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[v]','-map','[v]','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',str(vp)],check=True)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration','-of','json',str(vp)]))['streams'][0]
  assert probe['r_frame_rate']=='12/1' and int(probe['nb_frames'])==12 and float(probe['duration'])==1
  videos.append({'clip':clip,'direction':direction,'path':rel(vp),'sha256':sha(vp),'frames':12,'fps':12,'durationSeconds':1,'loop':clip!='load','ffprobe':probe});previews[clip+'-'+direction]=rel(vp)
# Four-view native canvases and repeated logical use context.
sheet=Image.new('RGB',(1536,680),BG['light']);dr=ImageDraw.Draw(sheet)
for i,d in enumerate(DIRECTIONS):sheet.paste(composite(rgba(frame('idle',d,0)),BG['light']),(i*384,34));dr.text((i*384+12,8),d+' · native384×640',font=font(19),fill='#28323b')
sheet.save(OUT/'four-view-sheet.png');previews['four-view-sheet']=rel(OUT/'four-view-sheet.png')
repeat=Image.new('RGB',(768,640),BG['light'])
for i in range(8):repeat.paste(composite(rgba(frame('idle',DIRECTIONS[i%4],(i//4)*6)).resize((192,320),Image.Resampling.LANCZOS),BG['light']),((i%4)*192,(i//4)*320))
repeat.save(OUT/'repeated.png');previews['repeated']=rel(OUT/'repeated.png')
for bg,col in BG.items():
 sheet=Image.new('RGB',(768,1376),col);dr=ImageDraw.Draw(sheet)
 for ci,c in enumerate(CLIPS):
  for di,d in enumerate(DIRECTIONS):
   im=rgba(frame(c,d,0)).resize((192,320),Image.Resampling.LANCZOS);sheet.paste(composite(im,col),(di*192,ci*344+24));dr.text((di*192+6,ci*344+5),c+' '+d+' f00',font=font(15),fill='#e8e8df' if bg=='dark' else '#28323b')
 path=OUT/('background-'+bg+'.png');sheet.save(path);previews['background-'+bg]=rel(path)
# Same registered source/candidate comparison, no fitting.
comparison=Image.new('RGB',(768,678),BG['light']);dr=ImageDraw.Draw(comparison)
for i,(path,label) in enumerate([(BASE/'candidates/round-01/frames/hold-S/000.png','Approved source · same registration'),(frame('hold','S',0),'Canonical food · native render')]):comparison.paste(composite(rgba(path),BG['light']),(i*384,34));dr.text((i*384+10,8),label,font=font(19),fill='#28323b')
comparison.save(OUT/'comparison.png');previews['comparison']=rel(OUT/'comparison.png')
# Fixed enlarged edge/face and crown crops on all backgrounds, each state and both profiles.
for bg,col in BG.items():
 sheet=Image.new('RGB',(1152,1856),col);dr=ImageDraw.Draw(sheet)
 for ci,c in enumerate(CLIPS):
  for di,d in enumerate(['E','W']):
   for fi,f in enumerate([0,5,11]):
    rect=(242,310,302,420) if d=='E' else (82,310,142,420)
    im=composite(rgba(frame(c,d,f)).crop(rect),col).resize((192,352),Image.Resampling.NEAREST);x=di*576+fi*192;y=ci*464
    sheet.paste(im,(x,y+28));dr.text((x+5,y+6),f'{c} {d} f{f:02d} · fixed edge crop',font=font(12),fill='#e8e8df' if bg=='dark' else '#28323b')
 path=OUT/('profile-edges-'+bg+'.png');sheet.save(path);previews['profile-edges-'+bg]=rel(path)
# Old/new semantic contact context uses the same registered native canvas, never fitting the food.
oldfolder=BASE/'candidates/round-01';newph={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'candidate-phases.json').read_text())};oldph={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'source-phases.json').read_text())}
for c in ['hold','load']:
 for direction in DIRECTIONS:
  sheet=Image.new('RGB',(1152,352),BG['light']);draw=ImageDraw.Draw(sheet)
  for fi,i in enumerate([0,5,11]):
   for version,folder in enumerate([oldfolder,OUT]):
    path=folder/'frames'/(c+'-'+direction)/(f'{i:03d}.png');image=rgba(path).resize((192,320),Image.Resampling.LANCZOS);x=fi*384+version*192;sheet.paste(composite(image,BG['light']),(x,28));draw.text((x+5,7),f'{c} {direction} f{i:02d} · '+('source' if version==0 else 'canonical'),font=font(14),fill='#28323b')
  path=OUT/(f'{c}-{direction}-source-canonical-contact.png');sheet.save(path);previews[f'{c}-{direction}-source-canonical-contact']=rel(path)
# Every N active frame: actual tiny source/canonical rear crescent, fixed crop on3 backgrounds.
for bg,col in BG.items():
 sheet=Image.new('RGB',(1584,880),col);draw=ImageDraw.Draw(sheet)
 for ci,c in enumerate(['hold','load']):
  for i in range(12):
   cellx=i%6*264;celly=ci*440+(i//6)*220
   for version,folder in enumerate([oldfolder,OUT]):
    image=rgba(folder/'frames'/(c+'-N')/(f'{i:03d}.png')).crop((175,370,241,416));image=composite(image,col).resize((132,184),Image.Resampling.NEAREST);sheet.paste(image,(cellx+version*132,celly+28));draw.text((cellx+version*132+3,celly+5),f'{c} N {i:02d} '+('old' if version==0 else 'new'),font=font(12),fill='#e8e8df' if bg=='dark' else '#28323b')
 path=OUT/('all24-N-rear-crescent-'+bg+'.png');sheet.save(path);previews['all24-N-rear-crescent-'+bg]=rel(path)
# Meaningful profile/palm/plate/face crops across source and canonical extrema; fixed220x160 native crop.
for direction in DIRECTIONS:
 sheet=Image.new('RGB',(2640,1480),BG['light']);draw=ImageDraw.Draw(sheet)
 for ci,c in enumerate(['hold','load']):
  for fi,i in enumerate([0,5,11]):
   for version,folder in enumerate([oldfolder,OUT]):
    image=rgba(folder/'frames'/(c+'-'+direction)/(f'{i:03d}.png')).crop((80,325,300,485));image=composite(image,BG['light']).resize((440,320),Image.Resampling.NEAREST);x=fi*880+version*440;y=ci*740;sheet.paste(image,(x,y+34));draw.text((x+6,y+8),f'{c} {direction} f{i:02d} '+('approved source' if version==0 else 'canonical candidate'),font=font(17),fill='#28323b')
    r=(oldph if version==0 else newph)[c,direction,i];support=next(v for v in r['semanticSupport'] if v['cutoff']==128)
    marked=image.copy();md=ImageDraw.Draw(marked)
    for label,v in [('rim',support['projected'])]+[(k,p['projected']) for k,p in support['palmRelations'].items() if k!='midpoint']:
     xx=(v[0]-80)*2;yy=(v[1]-325)*2;color='#d97516' if label=='rim' else '#126bba'
     if 0<=xx<440 and 0<=yy<320:md.ellipse((xx-4,yy-4,xx+4,yy+4),outline=color,width=2);md.text((xx+6,yy-8),label,font=font(13),fill=color)
    sheet.paste(marked,(x,y+400));draw.text((x+6,y+375),'Diagnostic overlay · projected rim / palm centroids',font=font(14),fill='#28323b')
 path=OUT/(direction+'-plate-palm-face-context.png');sheet.save(path);previews[direction+'-plate-palm-face-context']=rel(path)
# Fresh replay/radiance diagnostics are evidence, not substitute native sprites.
for filename in ['fresh-body-face-radiance-comparison.png','native-replay-calibration.json','radiance-residual-analysis.json','image-alpha-semantic-audit.json','semantic-support-all96.json','parity-validation.json','phase-parity.json','resource-and-shader-closure.json']:
 previews[Path(filename).stem]=rel(OUT/filename)
recipe=json.loads((P/'recipe-round02.json').read_text());nr=OUT/'native-records';source={'project':'source/round-02.blend','sha256':sha(P/'round-02.blend'),'approvedPhysicalSourceSHA256':recipe['approvedSourceSHA256'],'scene':recipe['scene'],'collection':recipe['collection'],'root':recipe['root'],'armature':recipe['armature'],'recipe':'source/recipe-round02.json','recipeSHA256':sha(P/'recipe-round02.json'),'capture':'candidates/round-02/candidate-phases.json','captureSHA256':sha(OUT/'candidate-phases.json'),'nativeRepresentation':'exact approved physical chef/knife/rig; canonical packed2D731x505 salmon on original native holder with one global semantic food quad/fullUV'}
for filename in ['camera.json','asset.json','rig.json']:
 record=json.loads((oldfolder/'native-records'/filename).read_text());record['captureScale']=2;record['source']=source
 if filename=='camera.json':record['nativeFrame']=[384,640];record['sourceScale']=2;record['frameAudit']={'path':'candidates/round-02/candidate-phases.json','sha256':sha(OUT/'candidate-phases.json'),'frames':192,'rootRotationsDegrees':{'S':0,'E':90,'N':180,'W':-90},'oneSharedUnchangedCameraAndMaterials':True}
 if filename=='asset.json':record['scale']=2;record['canonicalFood']={'path':'source/dependencies-round02/dish-salmon.png','sha256':recipe['food']['sha256'],'size':[731,505],'semanticFoodMapping':recipe['semanticFoodMapping'],'representation':'exact approved2D artwork, unchanged all-ray source shader/holder law'}
 if filename=='rig.json':record['refinedSceneSource']=source;record['actionImplementation']='source/native_actions_round02.py';record['actualEvaluatedContactEvidence']='candidates/round-02/semantic-support-all96.json'
 record['priorApprovedRecord']={'path':'candidates/round-01/native-records/'+filename,'sha256':sha(oldfolder/'native-records'/filename)};write(nr/filename,record)
shutil.copyfile(P/'dependencies-round02/dish-salmon.png',OUT/'resources/dish-salmon.png')
cards=[]
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();loop=' loop' if v['loop'] else ''
 cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} ·12fps · {"loop" if v["loop"] else "nonloop, ends at11"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{loop}></video></figure>')
html='''<!doctype html><meta charset="utf-8"><title>Ama canonical salmon round02</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20323a;margin:24px}h1{font-size:25px}p{max-width:900px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}figure{margin:0;padding:10px;background:#f5f3eb;border-radius:8px}figcaption{font-size:12px;min-height:32px}video{display:block;width:192px;height:320px}button{font:inherit;margin:8px;padding:8px 14px}</style><h1>Ama · canonical salmon round02</h1><p>192 native384×640 frames at registered logical192×320. Exact approved body/knife/rig/actions/materials/light/camera; exact canonical731×505RGBA food, fullUV, one global semantic rim/occupied-width mapping. Food remains original camera-facing2D on original all-ray Emission1 holder/depth law. Idle/work/hold loop; load is nonloop. No native PNG pixels are retouched. Native diagnostics and source comparisons accompany the frames.</p><button id="play">Play from frame00</button><button id="pause">Pause all</button><button id="end">Show load endings</button><main>'''+''.join(cards)+'''</main><script>const videos=[...document.querySelectorAll('video')];document.querySelector('#play').onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector('#pause').onclick=()=>videos.forEach(v=>v.pause());document.querySelector('#end').onclick=()=>videos.filter(v=>!v.loop).forEach(v=>{v.pause();v.currentTime=11/12});</script>'''
(OUT/'playback.html').write_text(html);previews['playback-index']=rel(OUT/'playback.html')
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'frames':192,'allFramesInsideFixedCanvas':True,'atlasRectanglesEqualRawNativePixels':True,'originalColumns':6,'originalRows':2,'originalAtlasSize':[2304,1280],'frameRecords':alpha})
write(OUT/'playback-validation.json',{'ok':True,'count':16,'nativeInputFrameManifest':'candidates/round-02/candidate-phases.json','playbacks':videos})
write(OUT/'contact-sheet-validation.json',{'ok':True,'sheets':sheets,'nativeFrames':192,'eachFrameShownOnThreeBackgrounds':True})
parity=json.loads((OUT/'parity-validation.json').read_text());closure=json.loads((OUT/'resource-and-shader-closure.json').read_text());replay=json.loads((OUT/'native-replay-calibration.json').read_text());aa=json.loads((OUT/'image-alpha-semantic-audit.json').read_text())
aggregate={'asset':'chef-ama','round':'round-02','status':'Complete narrow canonical-food candidate; original independent judge verdict pending','ok':parity['ok'] and closure['ok'] and aa['ok'] and replay['controlsComplete'],'brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':recipe['briefSHA256'],'source':'source/round-02.blend','sourceSHA256':source['sha256'],'approvedPhysicalSourceSHA256':recipe['approvedSourceSHA256'],'renderCount':192,'atlasCount':16,'playbackCount':16,'rawNativeFrameRecords':raw,'playbacks':videos,'parity':'candidates/round-02/parity-validation.json','phaseParity':'candidates/round-02/phase-parity.json','semanticSupport':'candidates/round-02/semantic-support-all96.json','imageAlphaSemantics':'candidates/round-02/image-alpha-semantic-audit.json','nativeReplayCalibration':'candidates/round-02/native-replay-calibration.json','radianceResiduals':'candidates/round-02/radiance-residual-analysis.json','resourceClosure':'candidates/round-02/resource-and-shader-closure.json','alphaAndAtlasValidation':'candidates/round-02/alpha-and-atlas-validation.json','playbackValidation':'candidates/round-02/playback-validation.json','contactSheetValidation':'candidates/round-02/contact-sheet-validation.json','notes':['Every physical mesh/normal/pose/visibility is audited all192 phases; source/current shared frozen data stored once and indexed phase digests/maxima are compact.','Original all-ray Emission1 can change body radiance despite exact body input parity. Changed-input residuals and actual source/candidate native crops are separate from unchanged-input replay precision.','No universal GPU bound, outside-food RGB identity rule, body-light edits, ray-law exception or raster correction.','Numeric parity and forecasts do not establish visible approval. Same original judge must inspect required native views and playback.']}
write(OUT/'complete-validation.json',aggregate)
resources={path.name:rel(path) for path in P.glob('*round02*') if path.is_file()};resources['canonical-salmon']=rel(P/'dependencies-round02/dish-salmon.png');resources['exact-native-project']='source/round-02.blend'
delivery={'schemaVersion':1,'asset':'chef-ama','round':'round-02','brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':recipe['briefSHA256'],'pipeline':'native-3d-with-explicit-source2D-food','status':'candidate-ready-for-original-independent-judge','project':'source/round-02.blend','recipe':'source/recipe-round02.json','recipeScript':'source/build_round02.py','validation':'candidates/round-02/complete-validation.json','heroes':{d:rel(frame('idle',d,0)) for d in DIRECTIONS},'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'representation':{'chefAndKnife':'exact approved native physical meshes/materials/rig/actions','food':'exact canonical packed2D731x505RGBA, fullUV, one frozen global semantic mapping; original source XYZ/yaw/depth/visibility/shader/light unchanged'},'notes':['Prior round01, approved body/backup and reviewed artifacts remain immutable. No production or Git edits.','Coordinator seals this numbered delivery against the separate frozen v3 brief.','Actual full192 frames,16 matching original-layout atlases and16 actual12fps clips; load remains nonloop.']}
write(BASE/'delivery-round02.json',delivery);write(OUT/'delivery-round02.json',delivery)
print('PACKED_ROUND02',len(raw),len(atlases),len(videos),flush=True)
