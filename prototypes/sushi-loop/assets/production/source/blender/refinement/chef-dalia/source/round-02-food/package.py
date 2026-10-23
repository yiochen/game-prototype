"""Exact native frame packing and identified review-only composites/playbacks."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,subprocess,shutil
P=Path(__file__).parent;BASE=P.parent.parent;OUT=BASE/'candidates/round-02';PROD=BASE.parents[2]/'production'
CLIPS=['idle','work','hold','load'];DIRS=['N','E','S','W'];BG={'light':'#f3f0e7','gray':'#8a8d8b','dark':'#242c30'}
for n in ['atlases','sheets','playbacks','backgrounds','contexts','native-records','resources']:(OUT/n).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def logical(im):return im.resize((192,320),Image.Resampling.LANCZOS)
def flat(im,bg):
 a=Image.new('RGBA',im.size,bg);a.alpha_composite(im);return a.convert('RGB')
def font(n):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
 except OSError:return ImageFont.load_default()
def rawpath(c,d,i):return OUT/'frames'/f'{c}-{d}'/f'{i:03d}.png'
def video_encode(pattern,path,w=384,h=640):
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(pattern),'-frames:v','12','-r','12','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_read_frames,width,height,duration','-of','json',str(path)]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and int(probe['nb_read_frames'])==12 and float(probe['duration'])==1
 return probe
rows=json.loads((OUT/'candidate-phases.json').read_text())['frames'];assert len(rows)==192
lookup={(r['clip'],r['direction'],r['index']):r for r in rows};catalog=json.loads((P/'dependencies/original-catalog-object.json').read_text());clips={c['id']:c for c in catalog['clips']}
raw=[];atlases=[];videos=[];sheets=[];alpha=[];previews={};sheetchecks=[]
for clip in CLIPS:
 for direction in DIRS:
  ims=[rgba(rawpath(clip,direction,i)) for i in range(12)];record=clips[clip]['directions'][direction];assert record['atlasSize']==[2304,1280]
  atlas=Image.new('RGBA',record['atlasSize'])
  for i,im in enumerate(ims):
   p=rawpath(clip,direction,i);assert im.size==(384,640) and sha(p)==lookup[(clip,direction,i)]['sha256'];r=record['rects'][i];assert r[2:]==[384,640];atlas.paste(im,tuple(r[:2]));box=im.getchannel('A').getbbox();assert box and 0<box[0]<box[2]<384 and 0<box[1]<box[3]<640
   raw.append({'clip':clip,'direction':direction,'index':i,'path':rel(p),'sha256':sha(p)});alpha.append({'clip':clip,'direction':direction,'index':i,'alphaBounds':box,'clipped':False})
  path=OUT/'atlases'/f'{clip}-{direction}.png';atlas.save(path,compress_level=9)
  reread=rgba(path)
  for i,im in enumerate(ims):
   x,y,w,h=record['rects'][i];assert reread.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
  atlases.append({'clip':clip,'direction':direction,'path':rel(path),'sha256':sha(path),'columns':record['columns'],'rows':record['rows'],'size':record['atlasSize'],'atlasSize':record['atlasSize'],'rects':record['rects'],'frameOrder':list(range(12)),'fps':12,'loop':clips[clip]['loop']})
  for bg,color in BG.items():
   for display,scale in [('logical',1),('enlarged',2)]:
    fw,fh=192*scale,320*scale;head=24*scale;sheet=Image.new('RGB',(6*fw,2*(fh+head)),color);dr=ImageDraw.Draw(sheet)
    for i,im in enumerate(ims):
     x=i%6*fw;y=i//6*(fh+head);shown=logical(im) if scale==1 else im;shown=flat(shown,color);sheet.paste(shown,(x,y+head));dr.text((x+6*scale,y+4*scale),f'{clip} {direction} · {i:02} · 12fps',font=font(14*scale),fill='#243339' if bg!='dark' else '#f1ede0')
     assert sheet.crop((x,y+head,x+fw,y+head+fh)).tobytes()==shown.tobytes()
    path=OUT/'sheets'/f'{clip}-{direction}-{bg}-{display}.png';sheet.save(path);sheets.append({'clip':clip,'direction':direction,'background':bg,'display':display,'path':rel(path),'sha256':sha(path),'nativeFrameSize':[384,640],'displayFrameSize':[fw,fh],'pixelVerified':True});previews[f'all-frames-{clip}-{direction}-{bg}-{display}']=rel(path)
  temp=OUT/'playbacks'/f'_{clip}-{direction}';temp.mkdir(exist_ok=True)
  for i,im in enumerate(ims):flat(im,BG['gray']).save(temp/f'{i:03d}.png')
  path=OUT/'playbacks'/f'{clip}-{direction}.mp4';probe=video_encode(temp/'%03d.png',path);shutil.rmtree(temp)
  videos.append({'clip':clip,'direction':direction,'path':rel(path),'sha256':sha(path),'fps':12,'frames':12,'durationSeconds':1,'loop':clips[clip]['loop'],'ffprobe':probe});previews[f'{clip}-{direction}']=rel(path)
# Four registered native facings and all-state/background evidence.
four=Image.new('RGB',(1536,674),BG['light']);dr=ImageDraw.Draw(four)
for di,d in enumerate(DIRS):four.paste(flat(rgba(rawpath('idle',d,0)),BG['light']),(di*384,34));dr.text((di*384+14,8),f'{d} · native384×640',font=font(19),fill='#243339')
four.save(OUT/'four-view-sheet.png');previews['four-view-sheet']=rel(OUT/'four-view-sheet.png')
for bg,color in BG.items():
 sheet=Image.new('RGB',(768,1376),color);dr=ImageDraw.Draw(sheet)
 for ci,c in enumerate(CLIPS):
  for di,d in enumerate(DIRS):sheet.paste(flat(logical(rgba(rawpath(c,d,5))),color),(di*192,ci*344+24));dr.text((di*192+7,ci*344+5),f'{c} {d} frame05',font=font(14),fill='#243339' if bg!='dark' else '#f1ede0')
 path=OUT/'backgrounds'/f'all-states-facings-{bg}.png';sheet.save(path);previews[f'background-{bg}']=rel(path)
# Registered128px cell-pitch repeated context at logical scale.
repeat=Image.new('RGBA',(768,520),BG['light']);dr=ImageDraw.Draw(repeat)
for row in range(2):
 for col,d in enumerate(DIRS):
  rootpx=(192+col*128,248+row*128);dr.line([(rootpx[0]-64,rootpx[1]),(rootpx[0]+64,rootpx[1])],fill='#c8c3b8');repeat.alpha_composite(logical(rgba(rawpath('idle',d,0))),(rootpx[0]-96,rootpx[1]-248))
repeat.convert('RGB').save(OUT/'repeated.png');previews['repeated']=rel(OUT/'repeated.png')
comparison=Image.new('RGB',(768,674),BG['light']);dr=ImageDraw.Draw(comparison)
for i,(title,path) in enumerate([('Approved body · prior food',BASE/'candidates/round-01/frames/hold-S/000.png'),('Canonical food · same body',rawpath('hold','S',0))]):comparison.paste(flat(rgba(path),BG['light']),(i*384,34));dr.text((i*384+12,8),title,font=font(19),fill='#243339')
comparison.save(OUT/'comparison.png');previews['comparison']=rel(OUT/'comparison.png')
# Evaluated contact markers only on labeled review contexts.
native=json.loads((OUT/'native-validation.json').read_text());ct={(r['clip'],r['direction'],r['index']):r for r in rows}
cal=native['camera']
def project(v):return tuple(cal['root'][i]+cal['unitX'][i]*v[0]-cal['unitDepth'][i]*v[1]+cal['unitHeight'][i]*v[2] for i in range(2))
for clip in ['work','hold','load']:
 sheet=Image.new('RGB',(1536,674),BG['light']);dr=ImageDraw.Draw(sheet)
 for di,d in enumerate(DIRS):
  im=flat(rgba(rawpath(clip,d,5)),BG['light']);draw=ImageDraw.Draw(im);r=ct[(clip,d,5)]
  for s,v in r['palmCentroidsWorld'].items():
   x,y=project(v);draw.ellipse((x-5,y-5,x+5,y+5),outline='#0873d2',width=2)
  x,y=r['semanticSupportNative'];draw.ellipse((x-6,y-6,x+6,y+6),outline='#d15b22',width=2)
  sheet.paste(im,(di*384,34));dr.text((di*384+10,8),f'{clip} {d} f05 · palms / alpha128 support',font=font(15),fill='#243339')
 path=OUT/'contexts'/f'{clip}-contacts.png';sheet.save(path);previews[f'{clip}-contact-context']=rel(path)
# Original source/candidate serving contexts use the same registered roots and128px cell pitch.
contextdeps=[];contexts=[];dep=OUT/'resources/context';dep.mkdir(exist_ok=True)
def copy_context(src,name):
 dest=dep/name;shutil.copyfile(src,dest);contextdeps.append({'path':rel(dest),'sourcePath':str(src),'sha256':sha(dest)});return dest
beltpath=copy_context(PROD/'sprites/belt-straight-e/running-S.png','belt-straight-e-running-S.png')
# Resolve actual source belt record if naming differs, without inventing a crop.
lib=json.loads((PROD/'library.json').read_text());belt=next(a for a in lib['objects'] if a['id']=='belt-straight-e');beltrec=belt['clips'][0]['directions']['S'];assert (PROD/beltrec['image']).is_file()
if (PROD/beltrec['image']).resolve()!= (PROD/'sprites/belt-straight-e/running-S.png').resolve():beltpath=copy_context(PROD/beltrec['image'],'belt-context-source.png')
beltim=rgba(beltpath).crop((0,0,384,704)).resize((192,352),Image.Resampling.LANCZOS)
for d in DIRS:
 originalpath=copy_context(BASE/'candidates/round-01/atlases'/f'load-{d}.png',f'approved-body-load-{d}.png');original=rgba(originalpath)
 delta={'N':(0,-128),'E':(128,0),'S':(0,128),'W':(-128,0)}[d];cr=(256,360);br=(cr[0]+delta[0],cr[1]+delta[1])
 for kind in ['source','candidate']:
  temp=OUT/'contexts'/f'_{kind}-load-{d}';temp.mkdir(exist_ok=True)
  for i in range(12):
   x,y,w,h=clips['load']['directions'][d]['rects'][i];chef=logical(original.crop((x,y,x+w,y+h))) if kind=='source' else logical(rgba(rawpath('load',d,i)))
   im=Image.new('RGBA',(512,640),BG['light']);draw=ImageDraw.Draw(im)
   for x in range(0,513,128):draw.line([(x,0),(x,640)],fill='#ded8cc')
   for y in range(-24,641,128):draw.line([(0,y),(512,y)],fill='#ded8cc')
   def putbelt():im.alpha_composite(beltim,(br[0]-96,br[1]-248))
   def putchef():im.alpha_composite(chef,(cr[0]-96,cr[1]-248))
   if d=='S':putchef();putbelt()
   else:putbelt();putchef()
   draw=ImageDraw.Draw(im);draw.text((12,10),f'{kind} load {d} · frame{i:02d} ·128px cell pitch',font=font(17),fill='#243339');draw.text((12,611),'Original load returns holding. No release trajectory is authored.',font=font(14),fill='#243339')
   im=im.convert('RGB');im.save(temp/f'{i:03d}.png')
   if i in [0,5,11]:im.save(OUT/'contexts'/f'{kind}-load-{d}-{i:02d}.png')
  path=OUT/'contexts'/f'{kind}-load-{d}.mp4';probe=video_encode(temp/'%03d.png',path);shutil.rmtree(temp);contexts.append({'kind':kind,'clip':'load','direction':d,'path':rel(path),'sha256':sha(path),'fps':12,'frames':12,'loop':False,'chefRoot':cr,'beltRoot':br,'cellPitch':128,'probe':probe});previews[f'{kind}-load-{d}-context']=rel(path)
# Same-registration source/candidate work/hold/load extremum and phone-size contexts.
source_paths=[]
for clip in CLIPS:
 for d in DIRS:
  for i in range(12):source_paths.append(BASE/'candidates/round-01/frames'/f'{clip}-{d}'/f'{i:03d}.png')
for clip in ['work','hold','load']:
 for d in DIRS:
  sheet=Image.new('RGB',(1152,344),BG['light']);draw=ImageDraw.Draw(sheet)
  for j,(i,kind) in enumerate([(0,'source'),(0,'candidate'),(5,'source'),(5,'candidate'),(11,'source'),(11,'candidate')]):
   p=BASE/'candidates/round-01/frames'/f'{clip}-{d}'/f'{i:03d}.png' if kind=='source' else rawpath(clip,d,i);sheet.paste(flat(logical(rgba(p)),BG['light']),(j*192,24));draw.text((j*192+5,4),f'{kind} {clip}-{d} f{i:02}',font=font(13),fill='#243339')
  path=OUT/'contexts'/f'{clip}-{d}-registered-source-candidate.png';sheet.save(path);previews[f'{clip}-{d}-registered-context']=rel(path)
  phone=Image.new('RGB',(390,844),BG['light']);draw=ImageDraw.Draw(phone);draw.text((8,10),f'Dalia · {clip} {d} · logical192×320',font=font(17),fill='#243339');draw.text((8,37),'Approved prior food                 Canonical food',font=font(13),fill='#243339')
  for row,i in enumerate([5,11]):
   for col,kind in enumerate(['source','candidate']):
    p=BASE/'candidates/round-01/frames'/f'{clip}-{d}'/f'{i:03d}.png' if kind=='source' else rawpath(clip,d,i);phone.paste(flat(logical(rgba(p)),BG['light']),(3+col*192,72+row*344));draw.text((8+col*192,54+row*344),f'Frame{i:02} · same root/scale',font=font(12),fill='#243339')
  draw.text((8,789),'Full native frames at one common logical scale.',font=font(13),fill='#243339');draw.text((8,809),'Original body, camera, hands and timing preserved.',font=font(12),fill='#243339');path=OUT/'contexts'/f'{clip}-{d}-phone.png';phone.save(path);previews[f'{clip}-{d}-phone-context']=rel(path)
# Actual source-repeat and food-off comparisons are observations, never a universal noise budget.
import numpy as np
control=json.loads((OUT/'controls-record.json').read_text());cl={(r['kind'],r['clip'],r['direction'],r['index'],r['mode']):r for r in control['records']}
def pixelstats(pa,pb):
 a=np.asarray(rgba(pa),dtype=np.int16);b=np.asarray(rgba(pb),dtype=np.int16);v=np.abs(a-b);changed=np.any(v!=0,axis=2);return {'differentPixels':int(changed.sum()),'differentAlphaPixels':int((v[:,:,3]!=0).sum()),'maximumRGBAByteDifference':v.max(axis=(0,1)).tolist(),'meanAbsoluteRGBAByteDifference':v.mean(axis=(0,1)).tolist(),'decodedRGBAEqual':bool(not changed.any()),'PNGBytesEqual':sha(pa)==sha(pb)}
comparisons=[]
poses=[('hold','S',0),('hold','E',0),('hold','N',0),('hold','W',0),('load','S',5),('work','S',5)]
for c,d,i in poses:
 for mode in ['food-on-a','food-off']:
  a=cl['source',c,d,i,mode];b=cl['candidate',c,d,i,mode];comparisons.append({'comparison':'source-versus-canonical','clip':c,'direction':d,'index':i,'mode':mode,'a':a['path'],'b':b['path'],'stats':pixelstats(BASE/a['path'],BASE/b['path'])})
for kind in ['source','candidate']:
 a=cl[kind,'hold','S',0,'food-on-a'];b=cl[kind,'hold','S',0,'food-on-b'];comparisons.append({'comparison':'same-source-repeat','kind':kind,'clip':'hold','direction':'S','index':0,'a':a['path'],'b':b['path'],'stats':pixelstats(BASE/a['path'],BASE/b['path'])})
for c,d,i in poses:
 sheet=Image.new('RGB',(768,344),BG['gray']);dr=ImageDraw.Draw(sheet)
 for j,(kind,mode) in enumerate([('source','food-on-a'),('candidate','food-on-a'),('source','food-off'),('candidate','food-off')]):
  rr=cl[kind,c,d,i,mode];sheet.paste(flat(logical(rgba(BASE/rr['path'])),BG['gray']),(j*192,24));dr.text((j*192+4,4),f'{kind} · {mode}',font=font(12),fill='#172c32')
 path=OUT/'contexts'/f'{c}-{d}-{i:03d}-radiance-controls.png';sheet.save(path);previews[f'{c}-{d}-{i:03d}-radiance-controls']=rel(path)
all_differences=[]
for r in rows:
 src=BASE/'candidates/round-01/frames'/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03d}.png';all_differences.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'source':rel(src),'candidate':r['path'],'foodAuthoredVisible':r['clip'] in ['hold','load'],'stats':pixelstats(src,BASE/r['path'])})
write(OUT/'pixel-diagnostics.json',{'policy':'Strict native data equality is separate from decoded PNG comparisons. Same-source repeats are limited observations. Food-on changes may include canonical artwork, natural occlusion and transported radiance. Food-off controls isolate the unchanged approved body under the same capture configuration. No universal noise allowance or PNG identity claim.','controls':comparisons,'all192ApprovedSourceVersusCandidateComparisons':all_differences})
# Measured current native records. Historical original-bake fields stay identified as provenance.
native=json.loads((OUT/'native-validation.json').read_text());nr=OUT/'native-records';cam=native['camera'];record=json.loads((P/'dependencies/rig.json').read_text())
camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'captureScale':2,'sourceScale':2,'fps':12,'cellSize':128,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','nativeBlenderType':native['presentation']['camera']['data']['type'],'worldMatrix':cam['worldMatrix'],'projectionMatrix':cam['projectionMatrix'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{k:cam[k] for k in ['root','unitX','unitDepth','unitHeight']},'measuredNativePoints':{'origin':cam['root'],'unitX':[cam['root'][i]+cam['unitX'][i] for i in range(2)],'unitDepth':[cam['root'][i]+cam['unitDepth'][i] for i in range(2)],'unitHeight':[cam['root'][i]+cam['unitHeight'][i] for i in range(2)]},'approvedBodyCameraPreserved':True,'nativeValidation':'candidates/round-02/native-validation.json'};write(nr/'camera.json',camera)
asset=json.loads((BASE/'candidates/round-01/native-records/asset.json').read_text());asset['scale']=2;asset['sourceScale']=2;asset['foodDependency']={'representation':'Exact canonical packed2D billboard','sha256':native['canonicalFoodSHA256'],'fullUV':True,'aspect':[731,505],'displayWidthWorld':.3500000014901161,'displayHeightWorld':.24179206669289827,'globalDepthWorld':.6,'semanticSupport':'alpha128 pixel-center fixed source-specific fullUV mapping','approvedBodyUnchanged':True};write(nr/'asset.json',asset)
record['sourceScale']=2;record['captureScale']=2;record['source']='source/round-02-food/native_actions.py';record['originalBakeSourceFilesAreHistorical']=True;record['canonicalHeldFood']={**asset['foodDependency'],'phaseLedger':'candidates/round-02/candidate-phases.json','sourcePhaseLedger':'candidates/round-02/source-phases.json'};write(nr/'rig.json',record)
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'rawFrameCount':192,'atlasCount':16,'allRectanglesEqualNativePixels':True,'originalRectsPreserved':True,'allFrameSheetsPixelVerified':True,'sheetCount':len(sheets),'alpha':alpha})
write(OUT/'playback-validation.json',{'ok':True,'actual12fpsNativePlaybacks':videos,'servingContexts':contexts})
write(OUT/'preview-manifest.json',{'sheets':sheets,'nativeVideos':videos,'servingContextVideos':contexts,'contextDependencies':contextdeps,'policy':'All native PNG frames and atlases untouched. Backgrounds, labels, contact marks, phone sheets and registered source/belt assemblies are review-only composites.'})
html='''<!doctype html><meta charset="utf-8"><title>Dalia canonical food round02 evidence</title><style>body{font:14px system-ui;background:#ece8de;color:#243339;margin:24px}main{display:grid;grid-template-columns:repeat(4,192px);gap:16px}figure{margin:0}video{display:block;width:192px;height:320px;background:#8a8d8b}button{font:inherit;padding:8px;margin:8px}.contexts{display:grid;grid-template-columns:repeat(4,256px);gap:16px}.contexts video{width:256px;height:320px}img{max-width:100%}details{margin-top:20px}a{color:#075c65}</style><h1>Dalia · canonical held food · round02</h1><p>Exact approved native body, rig, materials, lights, camera and timing. The packed salmon image and fullUV/aspect quad use the frozen alpha128 support mapping and one unchanged source depth0.6. Each runtime clip retains12 indexed frames at12fps. Idle/work/hold loop; load returns holding and stops.</p><button onclick="document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})">Play all from frame00</button><button onclick="document.querySelectorAll('video').forEach(v=>v.pause())">Pause all</button><main>'''
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();loop=' loop' if v['loop'] else '';html+=f'<figure><figcaption>{v["clip"]}-{v["direction"]} ·12fps ·{"loop" if v["loop"] else "nonloop"}</figcaption><video muted controls playsinline preload="auto"{loop} src="{url}"></video></figure>'
html+='</main><h2>Registered source and canonical serving contexts</h2><p>Original128px cell pitch; the source load extends and returns holding. No new release or belt flight.</p><div class="contexts">'
for v in contexts:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();html+=f'<figure><figcaption>{v["kind"]} load {v["direction"]}</figcaption><video muted controls playsinline preload="auto" src="{url}"></video></figure>'
html+='</div><details><summary>Four native views and exact-registration comparison</summary><img src="four-view-sheet.png"><img src="comparison.png"></details><details><summary>All native frames at logical and enlarged size on light/gray/dark</summary>'
for ss in sheets:html+=f'<a href="{Path(ss["path"]).relative_to("candidates/round-02")}">{ss["clip"]}-{ss["direction"]}-{ss["background"]}-{ss["display"]}</a> · '
html+='</details><details><summary>Registered work/hold/load and phone contexts</summary>'
for name,path in previews.items():
 if 'registered-context' in name or 'phone-context' in name or 'radiance-controls' in name:html+=f'<a href="{Path(path).relative_to("candidates/round-02")}">{name}</a> · '
html+='</details>';(OUT/'playback.html').write_text(html);previews['playback-index']=rel(OUT/'playback.html')
preflight=json.loads((OUT/'mapping-preflight.json').read_text());complete={**native,'ok':native['ok'] and preflight['ok'],'status':'Complete food-only native delivery; independent visual verdict pending','atlasCount':16,'playbackCount':16,'allFramesSheetCount':96,'sourceCandidateServingPlaybackCount':8,'alphaAndAtlasValidation':'candidates/round-02/alpha-and-atlas-validation.json','playbackValidation':'candidates/round-02/playback-validation.json','previewManifest':'candidates/round-02/preview-manifest.json','mappingPreflight':'candidates/round-02/mapping-preflight.json','pixelDiagnostics':'candidates/round-02/pixel-diagnostics.json','controlsRecord':'candidates/round-02/controls-record.json','runtimeFramePolicy':'Twelve indexed frames perclip with actual source repeats preserved. No runtime variants.'};write(OUT/'complete-validation.json',complete)
resources={}
for path in (BASE/'source').rglob('*'):
 if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':resources['source:'+path.relative_to(BASE/'source').as_posix()]=rel(path)
for path in source_paths:resources['approved-body-render:'+path.relative_to(BASE/'candidates/round-01/frames').as_posix()]=rel(path)
for path in (BASE/'candidates/draft-before-bevel-fix').rglob('*'):
 if path.is_file() and '__pycache__' not in path.parts:resources['retained-prior-body-draft:'+path.relative_to(BASE/'candidates/draft-before-bevel-fix').as_posix()]=rel(path)
for path in OUT.rglob('*'):
 if path.is_file() and path.name not in ['packet.json','delivery.snapshot.json','editor-handoff-hashes.json'] and '__pycache__' not in path.parts:resources['round:'+path.relative_to(OUT).as_posix()]=rel(path)
delivery={'schemaVersion':1,'asset':'chef-dalia','round':'round-02','pipeline':'native-3d','status':'candidate-ready-for-independent-review','project':'source/round-02.blend','recipe':'source/round-02-food/recipe.json','recipeScript':'source/round-02-food/build.py','validation':'candidates/round-02/complete-validation.json','heroes':{d:rel(rawpath('idle',d,0)) for d in DIRS},'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'frozenBrief':'brief-v3-held-food-frozen.json','frozenBriefSHA256':'d500baed2708cdd42bf5830b8bf373dc9f589292d0c333d5e0e1f5341d005107','approvedBodySHA256':'6786550a8d05b9d4563c038cd4d3614ce7c189a5a1e40813e2f536ac67c2709c','canonicalFoodSHA256':'4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4','representation':{'bodyAndKnife':'Exact approved native3D','heldFood':'Exact canonical731×505 packed RGBA2D, fullUV, frozen source-specific plate support and unchanged globalD0.6'},'retainedFailedDrafts':{'attempt01':'source/round-02-food/attempts/attempt-01-import','attempt02':'source/round-02-food/attempts/attempt-02-presentation-serialization','attempt03Sources':'source/round-02-food/attempts/attempt-03-phase-evaluation','attempt03Captures':'candidates/round-02/attempt-03-phase-evaluation','priorBodyDraft':'candidates/draft-before-bevel-fix','attempt04Sources':'source/round-02-food/attempts/attempt-04-animated-visibility-controls','attempt04Controls':'candidates/round-02/attempt-04-animated-visibility-controls'},'notes':['Food-only followup; all95 approved physical meshes/weights,24actions,15materials, native rig and presentation strictly preserved.','Only exact canonical image and fullUV/aspect quad use the frozen single local vertex rebase. Source depth/yaw drivers untouched.','Diagnostic hidden-owner evaluation uses a stable owner list and temporary visibility-curve mute/tagging; authored visibility/mute states restored before every native capture.','Native frame pixels/atlases are never retouched, fitted, cropped or recolored. Labels/backgrounds/contexts are identified review composites.','No new runtime variant clips. No self-approval. Root seals the v3brief/versioned delivery; original judge reviews exact candidate bytes.']}
write(BASE/'delivery-round-02.json',delivery)
write(OUT/'editor-handoff-hashes.json',{'status':'Ready for final inspection/closure and coordinator sealing; no visual approval issued','projectSHA256':sha(BASE/'source/round-02.blend'),'deliverySHA256':sha(BASE/'delivery-round-02.json'),'validationSHA256':sha(OUT/'complete-validation.json'),'nativeFrames':192,'atlases':16,'native12fpsClips':16,'allFrameSheets':96,'sourceCandidateContextClips':8,'allActualResourcesDeclared':len(resources)})
print('PACKAGED_FOOD_ONLY',complete['ok'],len(raw),len(atlases),len(videos),len(sheets),len(resources),flush=True)
