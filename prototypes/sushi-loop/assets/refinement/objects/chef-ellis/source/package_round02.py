"""Copy untouched RGBA native pixels into original atlases; separate labeled review composites."""
from pathlib import Path
import json,hashlib,subprocess,shutil,math
from PIL import Image,ImageDraw,ImageFont,ImageChops
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-02';DS=['N','E','S','W'];CS=['idle','work','hold','load']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def comp(im,bg):b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
def font(s):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',s)
 except OSError:return ImageFont.load_default()
def fp(c,d,i):return OUT/'frames'/(c+'-'+d)/(f'{i:03d}.png')
for n in ['atlases','playbacks','contact-sheets','native-records','resources']: (OUT/n).mkdir(exist_ok=True)
raw=[];atlases=[];pre={};vid=[];alphas=[];pixelhashes={}
backgrounds={'light':'#f5f4ed','gray':'#9a9e9b','dark':'#263238'}
for c in CS:
 for d in DS:
  ims=[];atlas=Image.new('RGBA',(2304,1280));sheets={k:Image.new('RGB',(1152,704),v) for k,v in backgrounds.items()}
  for i in range(12):
   path=fp(c,d,i);im=rgba(path);assert im.size==(384,640);ims.append(im);x=i%6*384;y=i//6*640;atlas.paste(im,(x,y));bbox=im.getchannel('A').getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<640
   row={'clip':c,'direction':d,'index':i,'path':rel(path),'sha256':sha(path)};raw.append(row);alphas.append({**row,'alphaBounds':bbox,'clipped':False});pixelhashes[(c,d,i)]=hashlib.sha256(im.tobytes()).hexdigest()
   for name,bg in backgrounds.items():
    ss=sheets[name];ss.paste(comp(im.resize((192,320),Image.Resampling.LANCZOS),bg),(i%6*192,i//6*352+30));ImageDraw.Draw(ss).text((i%6*192+7,i//6*352+7),f'{c} {d} · {i:02}',font=font(16),fill='#edf0e8' if name=='dark' else '#26343a')
  path=OUT/'atlases'/(c+'-'+d+'.png');atlas.save(path,compress_level=9);check=rgba(path);rects=[]
  for i,im in enumerate(ims):
   x=i%6*384;y=i//6*640;assert check.crop((x,y,x+384,y+640)).tobytes()==im.tobytes();rects.append([x,y,384,640])
  atlases.append({'clip':c,'direction':d,'path':rel(path),'sha256':sha(path),'columns':6,'rows':2,'size':[2304,1280],'rects':rects,'fps':12,'loop':c!='load','frameOrder':list(range(12))})
  for name,ss in sheets.items():path=OUT/'contact-sheets'/(c+'-'+d+'-'+name+'.png');ss.save(path);pre['all-frames-'+c+'-'+d+'-'+name]=rel(path)
  path=OUT/'playbacks'/(c+'-'+d+'.mp4')
  subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','12','-i',str(OUT/'frames'/(c+'-'+d)/'%03d.png'),'-f','lavfi','-i','color=c=0x9a9e9b:s=384x640:r=12:d=1','-filter_complex','[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[v]','-map','[v]','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',str(path)],check=True)
  data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams'][0];assert data['r_frame_rate']=='12/1' and int(data['nb_frames'])==12 and float(data['duration'])==1
  vid.append({'clip':c,'direction':d,'path':rel(path),'sha256':sha(path),'frames':12,'fps':12,'durationSeconds':1,'loop':c!='load','ffprobe':data});pre[c+'-'+d]=rel(path)
 # All48 overview shows source frame ordering/facing labels.
 ss=Image.new('RGB',(1152,704),backgrounds['gray']);dr=ImageDraw.Draw(ss)
 for di,d in enumerate(DS):
  for i in range(12):ss.paste(comp(rgba(fp(c,d,i)).resize((96,160),Image.Resampling.LANCZOS),backgrounds['gray']),(i*96,di*176+16));dr.text((i*96+3,di*176),f'{d} {i:02}',font=font(12),fill='#26343a')
 path=OUT/'contact-sheets'/(c+'-all48.png');ss.save(path);pre['overview-'+c]=rel(path)
for name,width,height,scale,coords in [('four-view-sheet',1536,680,1,[(i*384,34) for i in range(4)]),('repeated',768,640,.5,[(i%4*192,i//4*320) for i in range(8)])]:
 ss=Image.new('RGB',(width,height),'#e5e2d8');dr=ImageDraw.Draw(ss)
 for i,xy in enumerate(coords):
  d=DS[i%4];im=rgba(fp('idle',d,0 if i<4 else 6));im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);ss.paste(comp(im,'#e5e2d8'),xy)
  if name=='four-view-sheet':dr.text((xy[0]+12,8),d+' · native384×640',font=font(20),fill='#26343a')
 path=OUT/(name+'.png');ss.save(path);pre[name]=rel(path)
ss=Image.new('RGB',(768,1014));dr=ImageDraw.Draw(ss)
for bi,(name,bg) in enumerate(backgrounds.items()):
 dr.rectangle((0,bi*338,768,(bi+1)*338),fill=bg)
 for di,d in enumerate(DS):ss.paste(comp(rgba(fp('idle',d,0)).resize((192,320),Image.Resampling.LANCZOS),bg),(di*192,bi*338+18));dr.text((di*192+8,bi*338+1),d,font=font(14),fill='#edf0e8' if name=='dark' else '#26343a')
ss.save(OUT/'background-sheet.png');pre['background-sheet']=rel(OUT/'background-sheet.png')
ss=Image.new('RGB',(768,678),'#e5e2d8');dr=ImageDraw.Draw(ss)
for i,(path,label) in enumerate([(BASE/'inputs/original.png','Original · fixed registration'),(fp('idle','S',0),'Round02 · native render')]):ss.paste(comp(rgba(path),'#e5e2d8'),(i*384,34));dr.text((i*384+12,8),label,font=font(20),fill='#26343a')
ss.save(OUT/'comparison.png');pre['comparison']=rel(OUT/'comparison.png')
closure=[]
for row in json.loads((OUT/'closure-renders.json').read_text()):
 c=row['clip'];d=row['direction'];a=rgba(BASE/row['path']);b=rgba(fp(c,d,0));diff=ImageChops.difference(a,b);ext=diff.getextrema();mx=max(x[1] for x in ext);assert mx==0,(c,d,mx)
 ss=Image.new('RGB',(576,352),backgrounds['gray']);dr=ImageDraw.Draw(ss)
 for i,(im,label) in enumerate([(rgba(fp(c,d,11)),'last unique11'),(a,'closure key13'),(b,'first00')]):ss.paste(comp(im.resize((192,320),Image.Resampling.LANCZOS),backgrounds['gray']),(i*192,30));dr.text((i*192+5,7),label,font=font(15),fill='#26343a')
 path=OUT/'closures'/(c+'-'+d+'-boundary.png');ss.save(path);pre['closure-'+c+'-'+d]=rel(path);closure.append({**row,'maxRGBAChannelDifferenceToFirst':mx,'sourceClosingKey':13,'renderedAsCatalogFrame':False})
source=json.loads((OUT/'source-integrity.json').read_text());current=json.loads((OUT/'reopened-integrity.json').read_text());assert source['actions']==current['actions'];assert source['rest']==current['rest'];assert source['salmonPlane']==current['salmonPlane'];assert not current['libraries'];assert abs(current['heightDeltaFromNominal'])<1e-6
sourcePacked={x['packedSHA256'] for x in source['images'] if x['packed']};currentPacked={x['packedSHA256'] for x in current['images'] if x['packed']};assert sourcePacked==currentPacked
rows=json.loads((OUT/'native-frames.json').read_text());assert len(rows)==192
bounds=[[min(r['nativeBounds'][i][0] for r in rows),max(r['nativeBounds'][i][1] for r in rows)] for i in range(3)];assert max(abs(v) for dim in bounds[:2] for v in dim)<=.500001,bounds
for r in rows:assert abs(r['rootPixel'][0]-192)<.002 and abs(r['rootPixel'][1]-496)<.002
contacts=json.loads((OUT/'evaluated-contacts.json').read_text());dishErr=max(max(abs(c['dishToPalmMidpointVector'][i]-(.0225 if i==2 else 0)) for i in range(3)) for c in contacts)
vis={clip:{'dishHidden':sorted(set(v['hide'] for c in contacts if c['clip']==clip for n,v in c['props'].items() if '__image_plane' in n)),'knifeHidden':sorted(set(v['hide'] for c in contacts if c['clip']==clip for n,v in c['props'].items() if '__knife_' in n))} for clip in CS}
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'frames':alphas,'allNativeRectanglesPreserved':True});write(OUT/'playback-validation.json',{'ok':True,'playbacks':vid,'visibleLoopClosure':closure,'pixelDistinctSamples':{c+'-'+d:len({pixelhashes[(c,d,i)] for i in range(12)}) for c in CS for d in DS}})
recipe=json.loads((P/'recipe-round02.json').read_text());nr=OUT/'native-records';camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'captureScale':2,'fps':12,'cellSize':128,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':recipe['camera']['worldMatrix'],'projectionMatrix':recipe['camera']['projectionMatrix'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{k:recipe['camera'][k] for k in ['root','unitX','unitDepth','unitHeight']},'artStyle':{'lighting':'Warm soft symmetric overhead and four equal cardinal fills','nativeRefinement':'round-02'}};write(nr/'camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-round02','lightingSymmetry':4,'noGroundShadow':True,'sourceCameraRigActionsPreserved':True};write(nr/'asset.json',asset);shutil.copyfile(P/'rig-round02.json',nr/'rig.json')
for path in (P/'dependencies').glob('*'):shutil.copyfile(path,OUT/'resources'/path.name)
contexts=json.loads((OUT/'native-context-validation.json').read_text())
for i,r in enumerate(contexts['renders']):pre['native-context-'+str(i)]=r['path']
cards=[]
for v in vid:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();loop=' loop' if v['loop'] else '';cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} ·12fps · {"loop" if v["loop"] else "stops after12frames"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{loop}></video></figure>')
(OUT/'playback.html').write_text('<!doctype html><meta charset="utf-8"><title>Ellis round02 native playback</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20323a;margin:24px}main{display:grid;grid-template-columns:repeat(4,212px);gap:12px}figure{margin:0;padding:10px;background:#f5f3eb}video{display:block;width:192px;height:320px}button{font:inherit;margin:8px;padding:8px}</style><h1>Ellis round02 · native animation evidence</h1><p>All16 original clip/facing combinations, twelve384×640 native frames at12fps displayed at192×320. Idle/work/hold loop; load stops at its original ending frame. Video backgrounds are review composites. PNG frames and original-layout atlases contain unchanged native RGBA pixels.</p><button id="play">Play all from frame00</button><button id="pause">Pause all</button><main>'+''.join(cards)+'</main><script>const videos=[...document.querySelectorAll("video")];document.querySelector("#play").onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector("#pause").onclick=()=>videos.forEach(v=>v.pause());</script>');pre['playback-index']=rel(OUT/'playback.html')
validation=json.loads((OUT/'validation.json').read_text());assert validation['ok'];validation.update({'status':'Complete candidate evidence; independent judge verdict pending','rawNativeFrameRecords':raw,'catalogRenderCount':192,'originalLayoutAtlasCount':16,'playbackCount':16,'playbacks':vid,'alphaAndAtlasValidation':rel(OUT/'alpha-and-atlas-validation.json'),'closureValidation':closure,'physicalBodyBoundsAllFrames':bounds,'oneCellEnvelopePass':True,'nominalRestHeight':current['restBodyBounds'][2][1],'nominalHeightDifference':current['heightDeltaFromNominal'],'authoredHeightExcursionRetained':{'sourceMax':max(r['sourceBodyBounds'][2][1] for r in rows),'candidateMax':bounds[2][1]},'dishPalmMidpointPlusWorldZ0225MaxError':dishErr,'actualPropVisibility':vis,'actionContentsByteHashParity':True,'actionIntegrity':{'source':rel(OUT/'source-integrity.json'),'reopened':rel(OUT/'reopened-integrity.json')},'packedDependenciesParity':True,'nativeContexts':rel(OUT/'native-context-validation.json'),'allFramesSourceContactDeltaMax':{k:max(r['contactComparison'][k] for r in rows) for k in rows[0]['contactComparison']},'cameraRootCalibrationPass':True});write(OUT/'complete-validation.json',validation)
resources={path.name:rel(path) for path in P.glob('*') if path.is_file() and path.suffix in ['.blend','.py','.json']};resources['dish-salmon.png']=rel(P/'dependencies/dish-salmon.png')
delivery={'schemaVersion':1,'asset':'chef-ellis','round':'round-02','pipeline':'native-3d','status':'candidate-ready-for-independent-review','project':'source/round-02.blend','recipe':'source/recipe-round02.json','recipeScript':'source/build_round02.py','validation':rel(OUT/'complete-validation.json'),'heroes':{d:rel(fp('idle',d,0)) for d in DS},'rawFrames':raw,'atlases':atlases,'previews':pre,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'representation':{'actor':'native editable Blender meshes, materials and rig','knife':'native3D','heldDish':'separate original packed2D cutout with preserved UV, alpha, camera-ray bias, facing cancellation, attachment actions and visibility'},'notes':['Original16 catalog atlases and192 indexed native captures; original duplicated poses retained.','Physical body excludes the display-only2D salmon plane and separately audited native knife. No invented release/belt landing.','No raster repair or perview fitting. Background/comparison/contact sheets and videos are labeled review composites.','Independent judge owns visual verdict; coordinator seals exact bytes.']};write(BASE/'delivery.json',delivery)
print('PACKED',len(raw),len(atlases),len(vid),json.dumps({k:validation[k] for k in ['ok','physicalBodyBoundsAllFrames','nominalRestHeight','dishPalmMidpointPlusWorldZ0225MaxError']}),flush=True)
