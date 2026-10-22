"""Whole-frame exact packing and labeled review evidence for frozen native food v3."""
from pathlib import Path
import json,hashlib,subprocess,shutil,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-02';DIRS=['N','E','S','W']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return Path(p).relative_to(BASE).as_posix()
def font(n):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
 except OSError:return ImageFont.load_default()
def rgba(p):return Image.open(p).convert('RGBA')
def bg(im,color):
 b=Image.new('RGBA',im.size,color);b.alpha_composite(im);return b.convert('RGB')
def movie(pattern,path,count,fps=12):
 subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate',str(fps),'-i',str(pattern),'-f','lavfi','-i',f'color=c=0xd1d0c7:s=384x640:r={fps}:d={count/fps}','-filter_complex','[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[v]','-map','[v]','-frames:v',str(count),'-r',str(fps),'-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',str(path)],check=True)
 s=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,nb_frames,width,height,duration','-of','json',str(path)]))['streams'][0]
 assert s['r_frame_rate']==f'{fps}/1' and int(s['nb_frames'])==count;return s
allpreviews={};videos=[];bundles=[]
for runtime in [False,True]:
 folder=OUT/'runtimeVariants' if runtime else OUT;val=json.loads((folder/'validation.json').read_text());rows=json.loads((folder/'native-frames.json').read_text());clips=['hold-cucumber','load-cucumber'] if runtime else ['idle','work','hold','load'];atlases=[]
 for sub in ['atlases','contact-sheets','playbacks','native-records']: (folder/sub).mkdir(exist_ok=True)
 for clip in clips:
  for direction in DIRS:
   seq=[r for r in rows if r['clip']==clip and r['direction']==direction];seq.sort(key=lambda r:r['index']);assert len(seq)==12
   atlas=Image.new('RGBA',(2304,1280));sheet=Image.new('RGB',(1152,704),'#e5e2d8');draw=ImageDraw.Draw(sheet);rects=[]
   for i,r in enumerate(seq):
    im=rgba(BASE/r['path']);assert im.size==(384,640) and sha(BASE/r['path'])==r['sha256'];x=i%6*384;y=i//6*640;atlas.paste(im,(x,y));rects.append([x,y,384,640]);sx=i%6*192;sy=i//6*352
    sheet.paste(bg(im.resize((192,320),Image.Resampling.LANCZOS),'#e5e2d8'),(sx,sy+28));draw.text((sx+6,sy+4),f'{clip} {direction} · {i:02d}',font=font(14),fill='#20343c')
   path=folder/'atlases'/f'{clip}-{direction}.png';atlas.save(path,compress_level=9);reread=rgba(path)
   for i,r in enumerate(seq):x,y,w,h=rects[i];assert reread.crop((x,y,x+w,y+h)).tobytes()==rgba(BASE/r['path']).tobytes()
   atlases.append({'clip':clip,'direction':direction,'path':rel(path),'sha256':sha(path),'columns':6,'rows':2,'size':[2304,1280],'rects':rects,'frameOrder':list(range(12)),'fps':12,'loop':not clip.startswith('load')})
   sp=folder/'contact-sheets'/f'{clip}-{direction}.png';sheet.save(sp);allpreviews[f'all-frames-{clip}-{direction}']=rel(sp)
   vp=folder/'playbacks'/f'{clip}-{direction}.mp4';info=movie(folder/'frames'/f'{clip}-{direction}'/'%03d.png',vp,12);videos.append({'clip':clip,'direction':direction,'path':rel(vp),'sha256':sha(vp),'fps':12,'frames':12,'loop':not clip.startswith('load'),'ffprobe':info});allpreviews[f'{clip}-{direction}']=rel(vp)
  # Head/hand/food boundary context at native2x enlargement, every N phase plus visible front/side examples.
  boundary=Image.new('RGB',(1536,768),'#e5e2d8');dr=ImageDraw.Draw(boundary)
  cases=[(d,i) for d in ['N','E','S','W'] for i in [0,5,11]]
  for j,(d,i) in enumerate(cases):
   r=next(r for r in rows if r['clip']==clip and r['direction']==d and r['index']==i);im=rgba(BASE/r['path']).crop((64,280,320,520));x=j%6*256;y=j//6*384
   boundary.paste(bg(im,'#e5e2d8'),(x,y+28));dr.text((x+5,y+4),f'{clip} {d} f{i:02d} · native crop',font=font(13),fill='#20343c')
  bp=folder/f'{clip}-boundary-context.png';boundary.save(bp);allpreviews[f'{clip}-boundary-context']=rel(bp)
  overview=Image.new('RGB',(1152,704),'#e5e2d8');dr=ImageDraw.Draw(overview)
  for di,d in enumerate(DIRS):
   for i in range(12):
    r=next(r for r in rows if r['clip']==clip and r['direction']==d and r['index']==i);im=rgba(BASE/r['path']).resize((96,160),Image.Resampling.LANCZOS);overview.paste(bg(im,'#e5e2d8'),(i*96,di*176+16));dr.text((i*96+3,di*176),f'{d} {i:02d}',font=font(11),fill='#20343c')
  op=folder/'contact-sheets'/f'{clip}-all48.png';overview.save(op);allpreviews[f'overview-{clip}']=rel(op)
 # Multiple backgrounds at intended size; hold/load and all facings receive equal evidence.
 bgs=Image.new('RGB',(1536,1014),'#e5e2d8');dr=ImageDraw.Draw(bgs)
 visibleclips=['hold-cucumber','load-cucumber'] if runtime else ['hold','load']
 for bi,color in enumerate(['#f5f4ed','#8c9292','#263238']):
  dr.rectangle((0,bi*338,1536,bi*338+18),fill=color)
  for ci,clip in enumerate(visibleclips):
   for di,d in enumerate(DIRS):
    r=next(r for r in rows if r['clip']==clip and r['direction']==d and r['index']==5);im=rgba(BASE/r['path']).resize((192,320),Image.Resampling.LANCZOS);x=(ci*4+di)*192;bgs.paste(bg(im,color),(x,bi*338+18));dr.text((x+4,bi*338+2),f'{clip} {d}',font=font(11),fill='#20343c' if bi<2 else '#f0f0e6')
 bgs.save(folder/'background-sheet.png');allpreviews['runtime-backgrounds' if runtime else 'background-sheet']=rel(folder/'background-sheet.png')
 cont=json.loads((folder/'continuous-law-validation.json').read_text());turn=cont['turnFrames'];assert len(turn)==27
 tv=folder/'playbacks'/'semantic-turn.mp4';movie(folder/'turn-frames'/'%03d.png',tv,27);allpreviews['runtime-semantic-turn' if runtime else 'semantic-turn']=rel(tv)
 tsh=Image.new('RGB',(1152,1056),'#e5e2d8');dr=ImageDraw.Draw(tsh)
 for j,r in enumerate(turn):
  im=rgba(BASE/r['path']).resize((128,214),Image.Resampling.LANCZOS);x=j%9*128;y=j//9*352;tsh.paste(bg(im,'#e5e2d8'),(x,y+24));dr.text((x+3,y+3),f'{r["angleDegrees"]:g}°',font=font(14),fill='#20343c')
 tp=folder/'semantic-turn-sheet.png';tsh.save(tp);allpreviews['runtime-turn-sheet' if runtime else 'turn-sheet']=rel(tp)
 camera=val['camera'];nr=folder/'native-records';old=BASE/'candidates/round-01/native-records'
 if not old.exists():old=P/'round-02-resources/approved-native-records'
 camera_record=json.loads((old/'camera.json').read_text());camera_record['camera']['worldMatrix']=camera['worldMatrix'];camera_record['camera']['projectionMatrix']=camera['projectionMatrix'];camera_record['captureScale']=2;camera_record['nativeCaptureScale']=2;camera_record['nativeResolution']=[384,640];camera_record['publicationSampling']='Identity whole-canvas native2 to published2; rawFrames are exact atlas-cell pixels.';write(nr/'camera.json',camera_record)
 shutil.copyfile(old/'asset.json',nr/'asset.json');shutil.copyfile(P/('runtime-rig-round02.json' if runtime else 'rig-round02.json'),nr/'rig.json')
 write(folder/'atlas-validation.json',{'ok':True,'nativeFrames':len(rows),'publishedFrames':len(rows),'nativeResolution':[384,640],'publishedResolution':[384,640],'nativeCaptureScale':2,'publishedSourceScale':2,'wholeCanvasSampling':'Identity','allAtlasRectanglesEqualPublishedRawFrames':True,'atlases':len(atlases)})
 bundles.append({'runtime':runtime,'folder':folder,'rows':rows,'atlases':atlases,'validation':val,'nativeRecords':{k:rel(nr/f) for k,f in [('camera','camera.json'),('assetRecord','asset.json'),('rig','rig.json')]}})
sheet=Image.new('RGB',(1536,680),'#e5e2d8');dr=ImageDraw.Draw(sheet)
for di,d in enumerate(DIRS):
 r=next(r for r in bundles[0]['rows'] if r['clip']=='hold' and r['direction']==d and r['index']==5);sheet.paste(bg(rgba(BASE/r['path']),'#e5e2d8'),(di*384,32));dr.text((di*384+12,6),f'Hold {d} · native384×640',font=font(18),fill='#20343c')
sheet.save(OUT/'four-view-sheet.png');allpreviews['four-view-sheet']=rel(OUT/'four-view-sheet.png')
repeat=sheet.resize((768,340),Image.Resampling.LANCZOS);repeat.save(OUT/'repeated.png');allpreviews['repeated']=rel(OUT/'repeated.png')
cards=[]
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-02').as_posix();cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} ·12fps · {"loop" if v["loop"] else "stops frame11"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{" loop" if v["loop"] else ""}></video></figure>')
(OUT/'playback.html').write_text('''<!doctype html><meta charset="utf-8"><title>Omar canonical food v3 round02</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20343c;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px}figure{margin:0;background:#f7f4e9;padding:10px;border-radius:8px}figcaption{font-size:12px;min-height:28px}video{width:192px;height:320px}button{font:inherit;padding:9px 16px;margin:8px}</style><h1>Omar · canonical food v3 · round02</h1><p>All288 native frames, shown at logical192×320. Each shipping video contains12 frames at12fps. Native capture and published scales are both2; exact full-canvas RGBA pixels occupy every atlas cell.</p><button id="play">Play all</button><button id="pause">Pause all</button><main>'''+''.join(cards)+'''</main><script>const vs=[...document.querySelectorAll('video')];document.querySelector('#play').onclick=()=>vs.forEach(v=>{v.currentTime=0;v.play()});document.querySelector('#pause').onclick=()=>vs.forEach(v=>v.pause());</script>''');allpreviews['playback-index']=rel(OUT/'playback.html')
write(OUT/'playback-validation.json',{'ok':True,'videos':videos,'shippingPlaybacks':24,'looping':16,'nonLooping':8})
summary={'ok':all(b['validation']['ok'] for b in bundles),'asset':'chef-omar','round':'round-02','catalogNativeFrames':192,'runtimeNativeFrames':96,'totalNativeFrames':288,'catalogPublishedFrames':192,'runtimePublishedFrames':96,'catalogAtlases':16,'runtimeAtlases':8,'shippingPlaybacks':24,'nativeCaptureScale':2,'publishedScale':2,'mainValidation':'candidates/round-02/validation.json','runtimeValidation':'candidates/round-02/runtimeVariants/validation.json','bodyFrozen':all(b['validation']['allNonFoodStaticSemanticsEqual'] for b in bundles),'shippingMaximum':{k:max(b['validation']['maximum'][k] for b in bundles) for k in bundles[0]['validation']['maximum']},'continuousLaw':{'dMinWorld':.4,'law':'d(f)=d0-(d0-dMin)*max(0,-f)^2','cameraRayOnly':True},'pendingEvidence':['portable replay and RGB diagnostics finalization']};write(OUT/'complete-validation.json',summary)
runtime=bundles[1];main=bundles[0]
delivery={'schemaVersion':1,'asset':'chef-omar','round':'round-02','brief':'brief-v3-held-food-occlusion.json','project':'source/round-02.blend','recipe':'source/recipe-round02.json','recipeScript':'source/build_food_round02.py','validation':'candidates/round-02/complete-validation.json','heroes':{d:next(r['path'] for r in main['rows'] if r['clip']=='hold' and r['direction']==d and r['index']==0) for d in DIRS},'rawFrames':[{k:r[k] for k in ['clip','direction','index','path','width','height','sha256']} for r in main['rows']],'nativeRawFrames':[{k:r[k] for k in ['clip','direction','index','path','width','height','sha256']} for r in main['rows']],'atlases':main['atlases'],'previews':allpreviews,'nativeRecords':main['nativeRecords'],'nativeCaptureScale':2,'publishedSourceScale':2,'publicationSampling':'Identity full canvas384x640native2 to384x640published2; every atlas rectangle is byte-for-byte RGBA equal to raw frame.','runtimeVariants':{'project':'source/runtime-round-02.blend','recipe':'source/runtime-recipe-round02.json','validation':'candidates/round-02/runtimeVariants/validation.json','rawFrames':[{k:r[k] for k in ['clip','direction','index','path','width','height','sha256']} for r in runtime['rows']],'atlases':runtime['atlases'],'nativeRecords':runtime['nativeRecords'],'manifest':'candidates/round-02/runtimeVariants/runtime-manifest.json'},'resources':{},'status':'Candidate evidence assembly; independent review pending'}
write(runtime['folder']/'runtime-manifest.json',delivery['runtimeVariants']);write(BASE/'delivery-round-02-held-food-v3.json',delivery);print('PACKED288/24 atlases/24 shipping videos',flush=True)
