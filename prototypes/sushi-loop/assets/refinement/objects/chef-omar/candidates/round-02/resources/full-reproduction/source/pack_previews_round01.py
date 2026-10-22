"""Pack untouched native RGBA frames; build explicitly labeled review composites/playbacks."""
from pathlib import Path
import json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01';DIRECTIONS=['N','E','S','W']
FONTPATH='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(s=18):
 try:return ImageFont.truetype(FONTPATH,s)
 except OSError:return ImageFont.load_default()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def composite(im,bg):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
def actorframe(folder,clip,d,i):return folder/'frames'/(clip+'-'+d)/(f'{i:03d}.png')
allvideo=[];allraw=[];allatlas=[];allalpha=[];allpreviews={}
def pack(folder,clips):
 folder.joinpath('atlases').mkdir(exist_ok=True);folder.joinpath('playbacks').mkdir(exist_ok=True);folder.joinpath('contact-sheets').mkdir(exist_ok=True)
 raw=[];atlases=[];preview={};alpha=[];video=[]
 for clip in clips:
  for direction in DIRECTIONS:
   ims=[];atlas=Image.new('RGBA',(2304,1280));sheet=Image.new('RGB',(1152,704),'#e5e2d8');draw=ImageDraw.Draw(sheet)
   for i in range(12):
    path=actorframe(folder,clip,direction,i);im=rgba(path);assert im.size==(384,640)
    ims.append(im);x=(i%6)*384;y=(i//6)*640;atlas.paste(im,(x,y))
    logical=im.resize((192,320),Image.Resampling.LANCZOS);sx=(i%6)*192;sy=(i//6)*352
    sheet.paste(composite(logical,'#e5e2d8'),(sx,sy+28));draw.text((sx+8,sy+5),f'{clip} {direction} · {i:02}',font=font(16),fill='#29363b')
    bbox=im.getchannel('A').getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<640,(clip,direction,i,bbox)
    row={'clip':clip,'direction':direction,'index':i,'path':rel(path),'sha256':sha(path)};raw.append(row)
    alpha.append({**row,'alphaBounds':bbox,'frame':[384,640],'clipped':False})
   atlaspath=folder/'atlases'/(clip+'-'+direction+'.png');atlas.save(atlaspath,compress_level=9)
   # Verify all twelve full RGBA rectangles equal the corresponding raw native pixels.
   reread=rgba(atlaspath);rects=[]
   for i,im in enumerate(ims):
    x=(i%6)*384;y=(i//6)*640;assert reread.crop((x,y,x+384,y+640)).tobytes()==im.tobytes();rects.append([x,y,384,640])
   atlases.append({'clip':clip,'direction':direction,'path':rel(atlaspath),'sha256':sha(atlaspath),'columns':6,'rows':2,'size':[2304,1280],'rects':rects,'fps':12,'loop':not clip.startswith('load'),'frameOrder':list(range(12))})
   sheetpath=folder/'contact-sheets'/(clip+'-'+direction+'.png');sheet.save(sheetpath);preview['all-frames-'+clip+'-'+direction]=rel(sheetpath)
   videopath=folder/'playbacks'/(clip+'-'+direction+'.mp4')
   subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','12','-i',str(folder/'frames'/(clip+'-'+direction)/'%03d.png'),'-f','lavfi','-i','color=c=0xd1d0c7:s=384x640:r=12:d=1','-filter_complex','[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[v]','-map','[v]','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',str(videopath)],check=True)
   data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration','-of','json',str(videopath)]))['streams'][0]
   assert data['r_frame_rate']=='12/1' and int(data['nb_frames'])==12 and float(data['duration'])==1
   video.append({'clip':clip,'direction':direction,'path':rel(videopath),'sha256':sha(videopath),'frames':12,'fps':12,'durationSeconds':1,'loop':not clip.startswith('load'),'ffprobe':data})
   preview[clip+'-'+direction]=rel(videopath)
  overview=Image.new('RGB',(1152,704),'#e5e2d8');draw=ImageDraw.Draw(overview)
  for di,d in enumerate(DIRECTIONS):
   for i in range(12):
    im=rgba(actorframe(folder,clip,d,i)).resize((96,160),Image.Resampling.LANCZOS);x=i*96;y=di*176
    overview.paste(composite(im,'#e5e2d8'),(x,y+16));draw.text((x+4,y),f'{d} {i:02}',font=font(12),fill='#29363b')
  path=folder/'contact-sheets'/(clip+'-all48.png');overview.save(path);preview['overview-'+clip]=rel(path)
 write(folder/'alpha-and-atlas-validation.json',{'ok':True,'frames':len(raw),'allFramesInsideFixedCanvas':True,'atlasRectanglesEqualRawNativePixels':True,'framesRecords':alpha})
 write(folder/'playback-validation.json',{'ok':True,'playbacks':video})
 allvideo.extend(video);allraw.extend(raw);allatlas.extend(atlases);allalpha.extend(alpha);allpreviews.update(preview)
 return raw,atlases,preview

catalograw,catalogatlases,catalogpreviews=pack(OUT,['idle','work','hold','load'])
runtimefolder=OUT/'runtimeVariants'
runtimeraw,runtimeatlases,runtimepreviews=pack(runtimefolder,['hold-cucumber','load-cucumber'])
# Unaltered four-facing hero frames and logical repeats against three backgrounds.
sheet=Image.new('RGB',(1536,680),'#e6e2d7');d=ImageDraw.Draw(sheet)
for i,direction in enumerate(DIRECTIONS):
 im=rgba(actorframe(OUT,'idle',direction,0));sheet.paste(composite(im,'#e6e2d7'),(i*384,34));d.text((i*384+18,8),f'{direction} · native384×640',font=font(19),fill='#26343a')
sheet.save(OUT/'four-view-sheet.png');allpreviews['four-view-sheet']=rel(OUT/'four-view-sheet.png')
backgrounds=['#f5f4ed','#8c9292','#263238'];bg=Image.new('RGB',(768,1014));d=ImageDraw.Draw(bg)
for bi,c in enumerate(backgrounds):
 d.rectangle((0,bi*338,768,bi*338+18),fill=c)
 for i,direction in enumerate(DIRECTIONS):
  im=rgba(actorframe(OUT,'idle',direction,0)).resize((192,320),Image.Resampling.LANCZOS)
  bg.paste(composite(im,c),(i*192,bi*338+18));d.text((i*192+8,bi*338+2),direction,font=font(14),fill='#1c2e34' if bi<2 else '#edf0e8')
bg.save(OUT/'background-sheet.png');allpreviews['background-sheet']=rel(OUT/'background-sheet.png')
repeat=Image.new('RGB',(768,640),'#e5e2d8')
for i in range(8):
 im=rgba(actorframe(OUT,'idle',DIRECTIONS[i%4],(i//4)*6)).resize((192,320),Image.Resampling.LANCZOS);repeat.paste(composite(im,'#e5e2d8'),((i%4)*192,(i//4)*320))
repeat.save(OUT/'repeated.png');allpreviews['repeated']=rel(OUT/'repeated.png')
comparison=Image.new('RGB',(768,678),'#e5e2d8');dr=ImageDraw.Draw(comparison)
for i,(path,label) in enumerate([(BASE/'inputs/original.png','Original · same registration'),(actorframe(OUT,'idle','S',0),'Round01 · native render')]):
 comparison.paste(composite(rgba(path),'#e5e2d8'),(i*384,34));dr.text((i*384+16,8),label,font=font(20),fill='#26343a')
comparison.save(OUT/'comparison.png');allpreviews['comparison']=rel(OUT/'comparison.png')
# Technical overlays are confined to labeled review contexts; native frames/atlases stay untouched.
cal=json.loads((P/'recipe-round01.json').read_text())['camera']
def project(v):return tuple(cal['root'][i]+cal['unitX'][i]*v[0]-cal['unitDepth'][i]*v[1]+cal['unitHeight'][i]*v[2] for i in range(2))
for folder in [OUT,runtimefolder]:
 ct={(r['clip'],r['direction'],r['index']):r for r in json.loads((folder/'evaluated-contacts.json').read_text())}
 for clip in (['work','hold','load'] if folder==OUT else ['hold-cucumber','load-cucumber']):
  context=Image.new('RGB',(1536,674),'#e5e2d8');dr=ImageDraw.Draw(context)
  for di,direction in enumerate(DIRECTIONS):
   im=composite(rgba(actorframe(folder,clip,direction,5)),'#e5e2d8');ctx=ct[(clip,direction,5)];draw=ImageDraw.Draw(im)
   def dot(v,c,r=5):
    x,y=project(v);draw.ellipse((x-r,y-r,x+r,y+r),outline=c,width=2)
   for v in ctx['palms'].values():dot(v,'#0873d2')
   for foot in ctx['feet'].values():
    b=foot['bounds'];dot([(v[0]+v[1])*.5 for v in b],'#148c39')
   for n,v in ctx['props'].items():
    if '__held_' in n and '__image_plane' not in n:dot([v['matrix'][i][3] for i in range(3)],'#e77312',7)
    if '__utensil' in n and clip=='work':dot([v['matrix'][i][3] for i in range(3)],'#b23aba',7)
   context.paste(im,(di*384,34));dr.text((di*384+10,8),f'{clip} {direction} f05 · contact markers',font=font(16),fill='#26343a')
  path=folder/(clip+'-contact-context.png');context.save(path);allpreviews[clip+'-contact-context']=rel(path)

# Native registration records next to exact output bytes.
nr=OUT/'native-records';nr.mkdir(exist_ok=True)
recipe=json.loads((P/'recipe-round01.json').read_text())
camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'captureScale':2,'fps':12,'cellSize':128,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':recipe['camera']['worldMatrix'],'projectionMatrix':recipe['camera']['projectionMatrix'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{k:recipe['camera'][k] for k in ['root','unitX','unitDepth','unitHeight']},'artStyle':{'lighting':'Warm soft common native symmetric overhead and four equal fills','nativeRefinement':'round-01'}}
write(nr/'camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-round01','lightingSymmetry':4,'noGroundShadow':True,'renderer':'Cycles Metal','sourceCameraAndRigPreserved':True};write(nr/'asset.json',asset)
shutil.copyfile(P/'rig-round01.json',nr/'rig.json')
rnr=runtimefolder/'native-records';rnr.mkdir(exist_ok=True);write(rnr/'camera.json',camera);shutil.copyfile(P/'runtime-rig-round01.json',rnr/'rig.json');write(rnr/'asset.json',json.loads((BASE/'inputs/runtime-variants/original-object.json').read_text()))
resources=OUT/'resources';resources.mkdir(exist_ok=True)
for path in (P/'dependencies').glob('*'):shutil.copyfile(path,resources/path.name)
# A single review surface gives every 12fps video its original loop behavior.
cards=[]
for v in allvideo:
 url=Path(v['path']).relative_to('candidates/round-01').as_posix();loop=' loop' if v['loop'] else ''
 cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} · 12fps · {"loop" if v["loop"] else "load ends after12frames"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{loop}></video></figure>')
html='''<!doctype html><meta charset="utf-8"><title>Omar round01 native animation evidence</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20323a;margin:24px}h1{font-size:25px}p{max-width:820px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}figure{margin:0;padding:10px;background:#f5f3eb;border-radius:8px}figcaption{font-size:12px;min-height:32px}video{display:block;width:192px;height:320px}button{font:inherit;margin:8px;padding:8px 14px}a{color:#076d76}</style><h1>Omar round01 · native animation evidence</h1><p>All24 original clip/facing combinations. Each video contains the twelve full native384×640 frames at12fps; the player shows logical192×320. Looping actions repeat; load actions stop on frame11. Backgrounds and contact markers are review composites only. The PNG frames and atlases are unchanged native RGBA renders.</p><button id="play">Play all from frame00</button><button id="pause">Pause all</button><button id="end">Show load endings</button><main>'''+''.join(cards)+'''</main><script>const videos=[...document.querySelectorAll('video')];document.querySelector('#play').onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector('#pause').onclick=()=>videos.forEach(v=>v.pause());document.querySelector('#end').onclick=()=>videos.filter(v=>!v.loop).forEach(v=>{v.pause();v.currentTime=11/12});</script>'''
(OUT/'playback.html').write_text(html);allpreviews['playback-index']=rel(OUT/'playback.html')
mainval=json.loads((OUT/'validation.json').read_text());runval=json.loads((runtimefolder/'validation.json').read_text())
aggregate={**mainval,'status':'Complete native catalog and runtime evidence; independent visual verdict pending','ok':mainval['ok'] and runval['ok'],'renderCount':288,'catalogRenderCount':192,'runtimeVariantRenderCount':96,'clipFacingCount':24,'catalogNativeValidation':'candidates/round-01/validation.json','runtimeNativeValidation':'candidates/round-01/runtimeVariants/validation.json','rawNativeFrameRecords':allraw,'originalLayoutAtlasCount':24,'catalogAtlasCount':16,'runtimeVariantAtlasCount':8,'playbackCount':24,'playbacks':allvideo,'alphaAndAtlasValidation':{'catalog':'candidates/round-01/alpha-and-atlas-validation.json','runtimeVariants':'candidates/round-01/runtimeVariants/alpha-and-atlas-validation.json'},'runtimeVariants':{'source':'source/runtime-round-01.blend','sourceSHA256':sha(P/'runtime-round-01.blend'),'recipe':'source/runtime-recipe-round01.json','actorMeshMaterialParity':json.loads((P/'runtime-recipe-round01.json').read_text())['actorMeshMaterialParity'],'validation':runval}}
write(OUT/'complete-validation.json',aggregate)
delivery={'schemaVersion':1,'asset':'chef-omar','round':'round-01','pipeline':'native-3d','status':'candidate-ready-for-independent-review','project':'source/round-01.blend','recipe':'source/recipe-round01.json','recipeScript':'source/build_round01.py','validation':'candidates/round-01/complete-validation.json','heroes':{d:rel(actorframe(OUT,'idle',d,0)) for d in DIRECTIONS},'rawFrames':catalograw,'atlases':catalogatlases,'previews':allpreviews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':{path.name:rel(path) for path in P.glob('*') if path.is_file() and path.suffix in ['.blend','.py','.json']},'runtimeVariants':{'project':'source/runtime-round-01.blend','recipe':'source/runtime-recipe-round01.json','recipeScript':'source/build_runtime_round01.py','validation':'candidates/round-01/runtimeVariants/validation.json','rawFrames':runtimeraw,'atlases':runtimeatlases,'previews':runtimepreviews,'nativeRecords':{'camera':rel(rnr/'camera.json'),'assetRecord':rel(rnr/'asset.json'),'rig':rel(rnr/'rig.json')},'resources':{'food':rel(resources/'dish-cucumber.png'),'runtimeSourceContacts':'source/runtime-source-contacts-round01.json','runtimeSourceRest':'source/runtime-source-rest-round01.json','runtimeSourceFood':'source/runtime-source-food-round01.json'}},'representation':{'actor':'editable native Blender mesh/materials/rig','knife':'native3D','salmonAndCucumberDishes':'separate original packed2D ImageGen dependencies with original native attachment and visibility behavior'},'notes':['No catalog clip IDs added. Original16 catalog atlases and eight separately declared supplemental runtime atlases.','No raster retouch, angle correction, recolor or perframe fitting. Review composites/video backgrounds are identified separately.','Coordinator seals exact bytes. Independent judge owns visual verdict.']}
write(BASE/'delivery.json',delivery)
print('PACKED',len(allraw),'nativeframes',len(allatlas),'atlases',len(allvideo),'playbacks',flush=True)
