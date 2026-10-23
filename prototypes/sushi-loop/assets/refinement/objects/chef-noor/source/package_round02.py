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
# Every active frame has a registered source/canonical pair on each background.
oldfolder=BASE/'candidates/round-01';phase_new={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'candidate-phases.json').read_text())};phase_old={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'source-phases.json').read_text())};paired=[]
for clip in ['hold','load']:
 for direction in DIRECTIONS:
  for bg,col in BG.items():
   sheet=Image.new('RGB',(2304,704),col);dr=ImageDraw.Draw(sheet)
   for i in range(12):
    for version,folder in enumerate([oldfolder,OUT]):
     p=folder/'frames'/(clip+'-'+direction)/(f'{i:03d}.png');x=i%6*384+version*192;y=i//6*352;sheet.paste(composite(rgba(p).resize((192,320),Image.Resampling.LANCZOS),col),(x,y+28));dr.text((x+4,y+5),f'{clip} {direction} {i:02d} '+('source' if version==0 else 'canonical'),font=font(13),fill='#e8e8df' if bg=='dark' else '#28323b')
   p=OUT/'contact-sheets'/f'{clip}-{direction}-source-canonical-{bg}.png';sheet.save(p);previews[p.stem]=rel(p);paired.append({'clip':clip,'direction':direction,'background':bg,'path':rel(p),'frames':list(range(12)),'logicalFrameSize':[192,320],'sourceFolder':'candidates/round-01/frames','candidateFolder':'candidates/round-02/frames','method':'Every full registered source/native canvas at0.5scale. No food fitting/crop/raster correction.'})
# Full native contact/face/palm views at extrema, with a separate diagnostic copy.
for direction in DIRECTIONS:
 sheet=Image.new('RGB',(2304,1376),BG['light']);dr=ImageDraw.Draw(sheet)
 for ci,clip in enumerate(['hold','load']):
  for fi,i in enumerate([0,5,11]):
   for version,folder in enumerate([oldfolder,OUT]):
    im=rgba(folder/'frames'/(clip+'-'+direction)/(f'{i:03d}.png'));x=fi*768+version*384;y=ci*688;sheet.paste(composite(im,BG['light']),(x,y+28));dr.text((x+6,y+5),f'{clip} {direction} f{i:02d} '+('approved source' if version==0 else 'canonical native'),font=font(16),fill='#29333b')
 p=OUT/f'{direction}-native-contact-extrema.png';sheet.save(p);previews[p.stem]=rel(p)
# Actual phone-scale pixels: logical128px cell ->32px on screen, full character frame48x80.
(OUT/'phone').mkdir(exist_ok=True)
for direction in DIRECTIONS:
 phone=Image.new('RGB',(390,844),BG['light']);dr=ImageDraw.Draw(phone);dr.text((12,10),f'Noor {direction} · phone32px cell',font=font(17),fill='#23313d');dr.text((12,33),'Source | canonical · full frames48×80 · no fitting',font=font(11),fill='#23313d')
 for ci,clip in enumerate(['hold','load']):
  for i in range(12):
   x=51+i%3*96;y=52+(ci*4+i//3)*96;dr.text((x+2,y+2),f'{clip} {i:02d}',font=font(10),fill='#23313d')
   for version,folder in enumerate([oldfolder,OUT]):
    im=rgba(folder/'frames'/(clip+'-'+direction)/(f'{i:03d}.png')).resize((48,80),Image.Resampling.LANCZOS);phone.paste(composite(im,BG['light']),(x+version*48,y+16))
 p=OUT/'phone'/f'all24-source-canonical-{direction}.png';phone.save(p);previews['phone-'+direction]=rel(p)
# Original serving-belt registration: same logical roots,128px pitch and actual native load frames.
(OUT/'serving-contexts').mkdir(exist_ok=True);belt_source=oldfolder/'context-dependencies/belt-straight-e-running-S.png';belt_copy=OUT/'resources/belt-straight-e-running-S.png';shutil.copyfile(belt_source,belt_copy);belt=rgba(belt_copy).crop((0,0,384,704)).resize((192,352),Image.Resampling.LANCZOS);contexts=[];phone_context=Image.new('RGB',(390,844),BG['light']);pd=ImageDraw.Draw(phone_context);pd.text((12,9),'Original serving context · phone32px cell',font=font(16),fill='#23313d')
for di,direction in enumerate(DIRECTIONS):
 delta={'N':(0,-128),'E':(128,0),'S':(0,128),'W':(-128,0)}[direction];root=(256,360);br=(root[0]+delta[0],root[1]+delta[1])
 for version,folder in enumerate([oldfolder,OUT]):
  name='source' if version==0 else 'canonical';temp=OUT/'serving-contexts'/('_'+name+'-'+direction);temp.mkdir(exist_ok=True);preview=None
  for i in range(12):
   chef=rgba(folder/'frames'/('load-'+direction)/(f'{i:03d}.png')).resize((192,320),Image.Resampling.LANCZOS);im=Image.new('RGBA',(512,640),BG['light'])
   for x in range(0,513,128):ImageDraw.Draw(im).line([(x,0),(x,640)],fill='#ded8cc')
   for y in range(-24,641,128):ImageDraw.Draw(im).line([(0,y),(512,y)],fill='#ded8cc')
   def putchef():im.alpha_composite(chef,(root[0]-96,root[1]-248))
   def putbelt():im.alpha_composite(belt,(br[0]-96,br[1]-248))
   if direction=='S':putchef();putbelt()
   else:putbelt();putchef()
   draw=ImageDraw.Draw(im);draw.text((10,8),f'{name} load {direction} f{i:02d} · original128px cell pitch',font=font(16),fill='#24313c');draw.text((10,610),'Source action ends held; no new release or beltLoad path.',font=font(14),fill='#24313c');im.convert('RGB').save(temp/f'{i:03d}.png')
   if i in [0,5,11]:im.convert('RGB').save(OUT/'serving-contexts'/f'{name}-load-{direction}-{i:02d}.png')
   if i==5:preview=im.convert('RGB')
  vp=OUT/'serving-contexts'/f'{name}-load-{direction}.mp4';subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(temp/'%03d.png'),'-frames:v','12','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(vp)],check=True);shutil.rmtree(temp);previews[vp.stem]=rel(vp);contexts.append({'kind':name,'direction':direction,'path':rel(vp),'fps':12,'frames':12,'loop':False,'logicalChefRoot':root,'logicalBeltRoot':br,'cellPitch':128,'sourceBeltSHA256':sha(belt_copy)})
  phone_context.paste(preview.resize((128,160),Image.Resampling.LANCZOS),(38+version*186,55+di*194));pd.text((38+version*186,36+di*194),direction+' · '+name,font=font(13),fill='#24313c')
p=OUT/'phone/original-serving-context.png';phone_context.save(p);previews['phone-serving-context']=rel(p)
# Native records retain actual approved camera/rig/body; only source and food sidecars advance.
recipe=json.loads((P/'recipe-round02.json').read_text());nr=OUT/'native-records';source={'project':'source/round-02.blend','sha256':sha(P/'round-02.blend'),'approvedPhysicalSourceSHA256':recipe['approvedSourceSHA256'],'scene':recipe['scene'],'collection':recipe['collection'],'root':recipe['root'],'armature':recipe['armature'],'recipe':'source/recipe-round02.json','capture':'candidates/round-02/candidate-phases.json'}
for key,oldname,newname in [('camera','camera.json','camera.json'),('assetRecord','assetRecord.json','assetRecord.json'),('rig','rig.json','rig.json')]:
 oldpath=oldfolder/'records'/oldname;r=json.loads(oldpath.read_text());r.update(sourceCaptureScale=2,captureScale=2,sourceScale=2,sourceProject=source['project'],sourceSHA256=source['sha256'],status='canonical-food candidate pending independent review',nativeSource=source,priorApprovedRecord={'path':rel(oldpath),'sha256':sha(oldpath)})
 if key=='assetRecord':r['scale']=2;r['canonicalFood']={'path':'source/dependencies-round02/dish-salmon.png','sha256':recipe['food']['sha256'],'size':[731,505],'mapping':recipe['semanticFoodMapping'],'representation':'exact packed2D canonicalRGBA, unchanged original all-ray emission/holder law'}
 if key=='rig':r['actionImplementation']='source/native_actions_round02.py';r['contactEvidence']='candidates/round-02/semantic-support-all96.json';r['physicalInvariance']='candidates/round-02/phase-parity.json'
 write(nr/newname,r)
shutil.copyfile(P/'dependencies-round02/dish-salmon.png',OUT/'resources/dish-salmon.png')
# Actual12fps viewer, including48x80 phone playback CSS and preserved loop policy.
source_videos=OUT/'resources/source-playbacks';source_videos.mkdir(exist_ok=True);cards=[];phonecards=[]
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();loop=' loop' if v['loop'] else '';cards.append(f'<figure><figcaption>{v["clip"]} {v["direction"]} ·12fps · {"loop" if v["loop"] else "ends held"}</figcaption><video src="{url}" controls muted playsinline{loop}></video></figure>')
 if v['clip'] in ['hold','load']:
  name=v['clip']+'-'+v['direction']+'.mp4';shutil.copyfile(oldfolder/'playback'/name,source_videos/name);phonecards.append(f'<figure><figcaption>{v["clip"]} {v["direction"]}: source | canonical</figcaption><video class="phone" src="resources/source-playbacks/{name}" controls muted playsinline{loop}></video><video class="phone" src="{url}" controls muted playsinline{loop}></video></figure>')
html='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Noor canonical food round02</title><style>body{margin:16px;font:14px system-ui;background:#eee9de;color:#24313c}h1{font-size:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}figure{margin:0;padding:8px;background:#f6f2e9;border-radius:8px}figcaption{font-size:12px;min-height:28px}video{width:192px;height:320px;background:#ccc}video.phone{display:inline-block;width:48px;height:80px}button{font:inherit;padding:8px;margin:5px}img{max-width:100%;height:auto}</style><h1>Noor · canonical food round02</h1><p>Exact approved native body/knife/rig/actions/light/camera. Only packed canonical731×505RGBA and one frozen quad/fullUV map changed. All192native384×640 frames,16 clips at12fps. Original load is nonloop and ends held. Food is separate2D with the original all-ray Emission1 shader.</p><button onclick="document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})">Play from frame00</button><button onclick="document.querySelectorAll('video').forEach(v=>v.pause())">Pause</button><main>'''+''.join(cards)+'''</main><h2>Actual phone scale ·32px cell</h2><p>Each complete registered character frame is48×80screenpx. Source and canonical use the same scale; no food fitting.</p><main>'''+''.join(phonecards)+'''</main><h2>Phone serving context</h2><img width="390" height="844" src="phone/original-serving-context.png"><h2>Full source/canonical contact evidence</h2>'''
for pth in sorted(previews.values()):
 if 'source-canonical' in pth:html+=f'<a href="{Path(pth).relative_to("candidates/round-02")}">{Path(pth).name}</a><br>'
(OUT/'playback.html').write_text(html);previews['playback-index']=rel(OUT/'playback.html')
for name in ['fresh-native-radiance-controls.png','native-replay-calibration.json','radiance-residual-analysis.json','hidden-state-render-parity.json','semantic-support-all96.json','phase-parity.json','parity-validation.json','resource-and-shader-closure.json']:
 previews[Path(name).stem]=rel(OUT/name)
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'frames':192,'allInsideFrame':True,'atlasRectanglesEqualRawNativePixels':True,'originalAtlasSize':[2304,1280],'columns':6,'rows':2,'frameRecords':alpha})
write(OUT/'playback-validation.json',{'ok':True,'count':16,'clips':videos})
write(OUT/'contact-sheet-validation.json',{'ok':True,'singleFrameSheets':sheets,'pairedSourceCanonicalSheets':paired,'phoneSheets':{d:rel(OUT/'phone'/f'all24-source-canonical-{d}.png') for d in DIRECTIONS},'phonePolicy':{'screen':[390,844],'cellPitch':32,'logicalCellPitch':128,'completeCharacterFrame':[48,80],'fullCanvasScaleFromNative2':0.125,'noFit':True},'contexts':contexts})
parity=json.loads((OUT/'parity-validation.json').read_text());closure=json.loads((OUT/'resource-and-shader-closure.json').read_text());replay=json.loads((OUT/'native-replay-calibration.json').read_text());semantic=json.loads((P/'support-reference-round02.json').read_text());hidden=json.loads((OUT/'hidden-state-render-parity.json').read_text());primary=semantic['references'][1]
aggregate={'asset':'chef-noor','round':'round-02','status':'Complete canonical-food dependency closure; independent visual verdict pending','ok':parity['ok'] and closure['ok'] and replay['controlsComplete'] and abs(primary['widthDeltaLogicalPixels'])<1e-5 and max(abs(x) for x in primary['bottomDeltaLogicalCameraBasis'])<1e-5,'brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':recipe['briefSHA256'],'source':'source/round-02.blend','sourceSHA256':source['sha256'],'approvedPhysicalSourceSHA256':recipe['approvedSourceSHA256'],'renderCount':192,'atlasCount':16,'playbackCount':16,'fps':12,'rawNativeFrameRecords':raw,'nativeFrameManifest':'candidates/round-02/candidate-phases.json','renderManifest':'candidate-phases.json','parity':'candidates/round-02/parity-validation.json','phaseParity':'candidates/round-02/phase-parity.json','semanticSupport':'candidates/round-02/semantic-support-all96.json','imageAlphaSemantics':'source/support-reference-round02.json','nativeReplayCalibration':'candidates/round-02/native-replay-calibration.json','radianceResiduals':'candidates/round-02/radiance-residual-analysis.json','hiddenStateRGB':{'maxRGB':hidden['maxRGBDifference'],'maxAlpha':hidden['maxAlphaDifference'],'manifest':'candidates/round-02/hidden-state-render-parity.json'},'resourceClosure':'candidates/round-02/resource-and-shader-closure.json','alphaAndAtlasValidation':'candidates/round-02/alpha-and-atlas-validation.json','playbackValidation':'candidates/round-02/playback-validation.json','contactSheetValidation':'candidates/round-02/contact-sheet-validation.json','camera':json.loads((nr/'camera.json').read_text()),'notes':['All78 protected physical objects match across192 phases; all original full coordinate/normal/pose buffers and static body/knife/rest/actions/material/light/camera are invariant.','Only exact packed canonical binding and fixed source-specific quad/fullUV changed. Actual own sin/cos/yaw/ray drivers, visibility and original load behavior remain.','Hidden food matrices remain dormant; authored actions/driver targets and actual visibility are checked.','Changed Emission1 food can alter body radiance. Same-input repeats and restored-source-food counterfactual controls are reported separately; no blanket hold/load RGB identity rule.','No new Noor runtime variants. All earlier source/round01 evidence unchanged. Numeric checks do not self-approve visual outcomes.']};write(OUT/'complete-validation.json',aggregate)
resources={p.name:rel(p) for p in P.glob('*round02*') if p.is_file() and p.suffix in ['.py','.json']};resources.update({'canonical-salmon':rel(P/'dependencies-round02/dish-salmon.png'),'source-control-food':rel(P/'dependencies-round02/source-control-dish-salmon.png'),'exact-native-project':'source/round-02.blend'})
delivery={'schemaVersion':1,'asset':'chef-noor','assetId':'chef-noor','capture':{'frame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'sourceScale':2,'fps':12,'elevationDegrees':35,'pixelAspect':[1,1]},'round':'round-02','brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':recipe['briefSHA256'],'pipeline':'native-3d-with-explicit-canonical2D-food','status':'candidate-ready-for-original-independent-judge','project':'source/round-02.blend','recipe':'source/recipe-round02.json','recipeScript':'source/build_round02.py','validation':'candidates/round-02/complete-validation.json','heroes':{d:rel(frame('hold',d,0)) for d in DIRECTIONS},'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'assetRecord.json'),'rig':rel(nr/'rig.json')},'resources':resources,'representation':{'bodyAndKnife':'exact approved native3D body/knife/rig/actions/materials/light/camera','food':'exact packed canonical731x505RGBA, fullUV and frozen constant localquad; explicitly2D on original native holder/ray/yaw law'},'notes':['Round01 reviewed artifacts remain immutable. No Git/production/brief/review edits.','Coordinator seals this numbered delivery against frozen versioned v3 brief. Original independent judge supplies final verdict.','192 native frames,16 exact original-layout atlases,16 actual12fps clips; original visibility/end/loop policy preserved.']};write(BASE/'delivery-round02.json',delivery);write(OUT/'delivery-round02.json',delivery);print('PACKED_ROUND02',len(raw),len(atlases),len(videos),len(previews),aggregate['ok'])
