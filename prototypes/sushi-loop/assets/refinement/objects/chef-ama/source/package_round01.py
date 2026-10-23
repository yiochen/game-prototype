"""Pack exact native pixels, original atlas rectangles and clearly labeled review contexts."""
from pathlib import Path
import json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01';DIRECTIONS=['N','E','S','W'];CLIPS=['idle','work','hold','load']
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
for i,(path,label) in enumerate([(BASE/'inputs/original.png','Original · same registration'),(frame('idle','S',0),'Round01 · native render')]):comparison.paste(composite(rgba(path),BG['light']),(i*384,34));dr.text((i*384+10,8),label,font=font(19),fill='#28323b')
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
# Contact contexts retain native pixels; colored markers are explicitly review overlays.
cal=json.loads((P/'recipe-round01.json').read_text())['camera']
def project(v):return tuple(cal['root'][i]+cal['unitX'][i]*v[0]-cal['unitDepth'][i]*v[1]+cal['unitHeight'][i]*v[2] for i in range(2))
cts={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'evaluated-contacts.json').read_text())}
for c in ['work','hold','load']:
 context=Image.new('RGB',(1536,2016),BG['light']);dr=ImageDraw.Draw(context)
 for ri,f in enumerate([0,5,11]):
  for di,d in enumerate(DIRECTIONS):
   im=composite(rgba(frame(c,d,f)),BG['light']);ct=cts[c,d,f];draw=ImageDraw.Draw(im)
   def dot(v,color,r=5):
    x,y=project(v);draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=2)
   for v in ct['palms'].values():dot(v,'#0873d2')
   for foot in ct['feet'].values():dot([(v[0]+v[1])*.5 for v in foot['bounds']],'#148c39')
   surf=ct['actualSurfaceContacts']
   if any('__image_plane' in name and not prop['hide'] for name,prop in ct['props'].items()):dot(surf['dish2DInsert']['alphaRectangleBottomWorldMidpoint'],'#e77312',6)
   if c=='work':
    g=surf['knifeGrip']['handleToRightPalmSurface'];dot(g['pointA'],'#b23aba');dot(g['nearestPointB'],'#b23aba',7)
   context.paste(im,(di*384,ri*672+32));dr.text((di*384+8,ri*672+7),f'{c} {d} f{f:02d} · native surface markers',font=font(16),fill='#28323b')
 path=OUT/(c+'-contact-context.png');context.save(path);previews[c+'-contact-context']=rel(path)
# Records describe actual refined source and captureScale2; preserve source attribution separately.
recipe=json.loads((P/'recipe-round01.json').read_text());nr=OUT/'native-records';source={'project':'source/round-01.blend','sha256':sha(P/'round-01.blend'),'scene':recipe['scene'],'collection':recipe['collection'],'root':recipe['root'],'armature':recipe['armature'],'recipe':'source/recipe-round01.json','recipeSHA256':sha(P/'recipe-round01.json'),'capture':'candidates/round-01/native-frames.json','captureSHA256':sha(OUT/'native-frames.json'),'nativeRepresentation':'chef and knife are native mesh/material/rig; held salmon remains separately identified original packed2D insert'}
scam=json.loads((BASE/'inputs/source-camera.json').read_text());camera={'schemaVersion':2,'projection':'character-orthographic','frame':[192,320],'nativeFrame':[384,640],'anchor':[96,248],'cellSize':128,'captureScale':2,'sourceScale':2,'fps':12,'axes':scam['axes'],'camera':{'type':'orthographic','worldMatrix':cal['worldMatrix'],'projectionMatrix':cal['projectionMatrix'],'orthoScale':cal['orthoScale'],'shift':cal['shift'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{**{k:cal[k] for k in ['root','unitX','unitDepth','unitHeight']},'units':'actual native scale2 pixels'},'source':source,'originalRecord':{'path':'inputs/source-camera.json','sha256':sha(BASE/'inputs/source-camera.json'),'historicalCaptureScale':4},'artStyle':{'revision':'warm-soft-native-round01','oneMaterialLightConfigurationForAllFrames':True,'lightingSymmetry':4,'noDirectionalGroundShadow':True,'renderer':recipe['renderer']}}
write(nr/'camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['captureScale']=2;asset['source']=source;asset['artStyle']={'revision':'warm-soft-native-round01','goldenWrapIvoryCoatGreenTieApron':True,'lightingSymmetry':4,'noGroundShadow':True,'renderer':recipe['renderer']};asset['originalRecord']={'path':'inputs/source-assetRecord.json','sha256':sha(BASE/'inputs/source-assetRecord.json')};asset['actualEvaluatedContactEvidence']='candidates/round-01/evaluated-contacts.json';write(nr/'asset.json',asset)
rig=json.loads((P/'rig-round01.json').read_text());rig['source']='source/native_actions_round01.py';rig['refinedSceneSource']=source;rig['actualEvaluatedContactEvidence']='candidates/round-01/evaluated-contacts.json';rig['originalRecord']={'path':'inputs/source-rig.json','sha256':sha(BASE/'inputs/source-rig.json')};rig['captureScale']=2;write(nr/'rig.json',rig)
for path in (P/'dependencies-round01').glob('*'):shutil.copyfile(path,OUT/'resources'/path.name)
# All16 actual12fps playbacks with original loop policy.
cards=[]
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-01').as_posix();loop=' loop' if v['loop'] else ''
 cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} · 12fps · {"loop" if v["loop"] else "stops after frame11"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{loop}></video></figure>')
html='''<!doctype html><meta charset="utf-8"><title>Ama round01 native animation evidence</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20323a;margin:24px}h1{font-size:25px}p{max-width:900px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}figure{margin:0;padding:10px;background:#f5f3eb;border-radius:8px}figcaption{font-size:12px;min-height:32px}video{display:block;width:192px;height:320px}button{font:inherit;margin:8px;padding:8px 14px}</style><h1>Ama round01 · native animation evidence</h1><p>All16 original clip/facing combinations,192 native frames. Each video contains twelve native384×640 frames at12fps and shows logical192×320. Idle/work/hold loop; load stops at frame11. The salmon dish is the exact original packed2D source insert with original native attachment and depth drivers. Background composites and colored surface markers are review evidence; delivered PNG frames and atlas rectangles retain exact native pixels.</p><button id="play">Play all from frame00</button><button id="pause">Pause all</button><button id="end">Show load endings</button><main>'''+''.join(cards)+'''</main><script>const videos=[...document.querySelectorAll('video')];document.querySelector('#play').onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector('#pause').onclick=()=>videos.forEach(v=>v.pause());document.querySelector('#end').onclick=()=>videos.filter(v=>!v.loop).forEach(v=>{v.pause();v.currentTime=11/12});</script>'''
(OUT/'playback.html').write_text(html);previews['playback-index']=rel(OUT/'playback.html')
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'frames':192,'allFramesInsideFixedCanvas':True,'atlasRectanglesEqualRawNativePixels':True,'originalColumns':6,'originalRows':2,'originalAtlasSize':[2304,1280],'frameRecords':alpha})
write(OUT/'playback-validation.json',{'ok':True,'count':16,'playbacks':videos})
write(OUT/'contact-sheet-validation.json',{'ok':True,'sheets':sheets,'nativeFrames':192,'eachFrameShownOnThreeBackgrounds':True})
main=json.loads((OUT/'validation.json').read_text());env=json.loads((OUT/'envelope-validation.json').read_text());nativeaudit=json.loads((OUT/'native-topology-phase-audit.json').read_text())
aggregate={**main,'status':'Complete native candidate; independent visual verdict pending','ok':main['ok'] and env['ok'] and nativeaudit['ok'],'renderCount':192,'atlasCount':16,'playbackCount':16,'rawNativeFrameRecords':raw,'playbacks':videos,'nativeTopologyPhaseAudit':'candidates/round-01/native-topology-phase-audit.json','nativePhaseManifest':'candidates/round-01/native-phase-manifest.json','nativeValidation':'candidates/round-01/validation.json','envelopeValidation':'candidates/round-01/envelope-validation.json','alphaAndAtlasValidation':'candidates/round-01/alpha-and-atlas-validation.json','playbackValidation':'candidates/round-01/playback-validation.json','contactSheetValidation':'candidates/round-01/contact-sheet-validation.json','envelopeSummary':{k:v for k,v in env.items() if k!='frames'}}
write(OUT/'complete-validation.json',aggregate)
resources={path.name:rel(path) for path in P.glob('*') if path.is_file() and path.suffix in ['.blend','.py','.json']}
resources.update({'source2D-dish-salmon':rel(P/'dependencies-round01/dish-salmon.png')})
delivery={'schemaVersion':1,'asset':'chef-ama','round':'round-01','pipeline':'native-3d','status':'candidate-ready-for-independent-review','project':'source/round-01.blend','recipe':'source/recipe-round01.json','recipeScript':'source/build_round01.py','validation':'candidates/round-01/complete-validation.json','heroes':{d:rel(frame('idle',d,0)) for d in DIRECTIONS},'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'representation':{'chef':'editable native Blender mesh/material/rig','knife':'native3D','heldSalmonDish':'separate exact original packed2D dependency with original attachment, yaw cancellation, camera depth and visibility actions'},'notes':['Original192 native frames,16 clip/facing atlases in original6x2 layouts and timing; true S0/E90/N180/W-90.','No native raster paintover, target card, perview correction, recoloring or camera fitting. Review composites are labeled.','Coordinator seals immutable bytes; fresh independent judge owns verdict.']}
write(BASE/'delivery.json',delivery)
print('PACKED',len(raw),'native frames',len(atlases),'atlases',len(videos),'actual clips',flush=True)
