from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,subprocess,shutil,math
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-03';ROOT=BASE.parents[3];PROD=ROOT/'assets/production'
# Resolve from local object directory rather than machine current working directory.
PROD=BASE.parents[2]/'production'
BG={'light':'#EFEBE1','gray':'#7C7C7C','dark':'#191D24'};CLIPS=['idle','work','hold','load'];DIRS=['N','E','S','W']
for n in ['atlases','sheets','playback','backgrounds','contexts']: (OUT/n).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(p):return Image.open(p).convert('RGBA')
def logical(im):return im.resize((192,320),Image.Resampling.LANCZOS)
def flat(im,bg):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
def text(draw,pos,s,bg):draw.text(pos,s,fill='#1D2430' if bg!='dark' else '#EDE9DD')
rows=json.loads((OUT/'native-frames.json').read_text());lookup={(r['clip'],r['direction'],r['index']):r for r in rows};evidence=[];atlases=[];videos=[];alpha=[]
for clip in CLIPS:
 for d in DIRS:
  raw=[rgba(BASE/lookup[(clip,d,i)]['path']) for i in range(12)]
  atlas=Image.new('RGBA',(2304,1280))
  mapping=[]
  for i,im in enumerate(raw):
   assert im.size==(384,640);r=lookup[(clip,d,i)];assert sha(BASE/r['path'])==r['sha256'];atlas.paste(im,((i%6)*384,(i//6)*640));mapping.append({'index':i,'nativeFrame':r['path'],'sha256':r['sha256'],'rect':[(i%6)*384,(i//6)*640,384,640]})
   box=im.getchannel('A').getbbox();alpha.append({'clip':clip,'direction':d,'index':i,'bbox':box,'touchesFrameEdge':bool(box and (box[0]==0 or box[1]==0 or box[2]==384 or box[3]==640))})
  path=OUT/'atlases'/f'{clip}-{d}.png';atlas.save(path);atlases.append({'clip':clip,'direction':d,'path':str(path.relative_to(BASE)),'sha256':sha(path),'columns':6,'rows':2,'frame':[384,640],'atlasSize':[2304,1280],'frames':mapping})
  for bg,color in BG.items():
   sheet=Image.new('RGB',(1152,688),color);dr=ImageDraw.Draw(sheet)
   for i,im in enumerate(raw):
    x=(i%6)*192;y=(i//6)*344;text(dr,(x+6,y+5),f'{clip} {d} · {i:02d} · 12fps',bg);sheet.paste(flat(logical(im),color),(x,y+24))
   path=OUT/'sheets'/f'{clip}-{d}-{bg}.png';sheet.save(path);evidence.append({'kind':'all-frame-sheet','clip':clip,'direction':d,'background':bg,'path':str(path.relative_to(BASE)),'sha256':sha(path),'mapping':mapping,'nativeFullFrameSize':[384,640],'displayFullFrameSize':[192,320]})
  # Native-source2RGBA frames composited over one shared gray background, exact12fps MP4.
  temp=OUT/'playback'/f'_{clip}-{d}';temp.mkdir(exist_ok=True)
  for i,im in enumerate(raw):flat(logical(im),BG['gray']).save(temp/f'{i:03d}.png')
  video=OUT/'playback'/f'{clip}-{d}.mp4';subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(temp/'%03d.png'),'-frames:v','12','-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_read_frames,width,height,duration','-of','json',str(video)]))
  assert probe['streams'][0]['r_frame_rate']=='12/1' and int(probe['streams'][0]['nb_read_frames'])==12
  videos.append({'id':clip+'-'+d,'clip':clip,'direction':d,'path':str(video.relative_to(BASE)),'sha256':sha(video),'fps':12,'frames':12,'durationSeconds':1,'loop':clip!='load','probe':probe});shutil.rmtree(temp)
# All facings/statics on every background, full native frame retained.
for bg,color in BG.items():
 sheet=Image.new('RGB',(1536,1380),color);dr=ImageDraw.Draw(sheet)
 for row,clip in enumerate(CLIPS):
  for col,d in enumerate(DIRS):
   im=rgba(BASE/lookup[(clip,d,5)]['path']);x=col*384;y=row*345;text(dr,(x+8,y+4),f'{clip} {d} frame05',bg);sheet.paste(flat(im,color).resize((192,320),Image.Resampling.LANCZOS),(x+96,y+24))
 path=OUT/'backgrounds'/f'all-states-facings-{bg}.png';sheet.save(path);evidence.append({'kind':'all-states-facings-background','background':bg,'path':str(path.relative_to(BASE)),'sha256':sha(path)})
 # Enlarged exact-source edge inspection: actual384x640 frames, including hold/load extremum.
 sheet=Image.new('RGB',(1536,1328),color);dr=ImageDraw.Draw(sheet)
 for row,clip in enumerate(['idle','load']):
  for col,d in enumerate(DIRS):
   im=rgba(BASE/lookup[(clip,d,5)]['path']);x=col*384;y=row*664;text(dr,(x+8,y+4),f'{clip} {d} native384x640 frame05',bg);sheet.paste(flat(im,color),(x,y+24))
 path=OUT/'backgrounds'/f'enlarged-edges-{bg}.png';sheet.save(path);evidence.append({'kind':'enlarged-alpha-edges','background':bg,'path':str(path.relative_to(BASE)),'sha256':sha(path)})
# Four views full source384x640, single shared capture scale.
four=Image.new('RGBA',(1536,664),BG['light']);dr=ImageDraw.Draw(four)
for col,d in enumerate(DIRS):dr.text((col*384+12,5),f'idle {d} · same native camera/root',fill='#293442');four.alpha_composite(rgba(BASE/lookup[('idle',d,0)]['path']),(col*384,24))
four.convert('RGB').save(OUT/'four-view-sheet.png')
# Repeated sprites preserve one-cell pitch128 logical at common root; no silhouette refitting.
rep=Image.new('RGBA',(768,520),BG['light']);dr=ImageDraw.Draw(rep)
for gridy in range(2):
 for gridx,d in enumerate(DIRS):
  root=(192+gridx*128,248+gridy*128);dr.line([(root[0]-64,root[1]),(root[0]+64,root[1])],fill='#DBD3C1');rep.alpha_composite(logical(rgba(BASE/lookup[('idle',d,0)]['path'])),(root[0]-96,root[1]-248))
rep.convert('RGB').save(OUT/'repeated.png')
# Registered source belt context. This is a faithful native RGBA composite, never a replacement render.
lib=json.loads((PROD/'library.json').read_text());records={a['id']:a for a in lib['objects']};belt=records['belt-straight-e'];dish=records['dish-salmon'];dep=OUT/'context-dependencies';dep.mkdir(parents=True,exist_ok=True)
ctxdeps=[]
def copydep(rel,name):
 src=BASE/'candidates/round-02/context-dependencies'/name
 if name.startswith('original-load-'):src=BASE/'candidates/round-02/atlases'/('load-'+name.split('-')[-1])
 elif name.startswith('original-work-'):src=BASE/'candidates/round-02/atlases'/('work-'+name.split('-')[-1])
 elif name=='dish-salmon-2d-static-S.png':src=PROD/rel
 elif not src.exists():src=PROD/rel
 dst=dep/name;shutil.copy2(src,dst);ctxdeps.append({'path':str(dst.relative_to(BASE)),'sourceProductionPath':str(src),'sha256':sha(dst)});return dst
beltpath=copydep(belt['clips'][0]['directions']['S']['image'],'belt-straight-e-running-S.png');beltim=rgba(beltpath).crop((0,0,384,704)).resize((192,352),Image.Resampling.LANCZOS)
dishpath=copydep(dish['clips'][0]['directions']['S']['image'],'dish-salmon-2d-static-S.png');dishim=logical(rgba(dishpath));ctx=[]
for d in DIRS:
 origpath=copydep('sprites/chef-lena/load-'+d+'.png','original-load-'+d+'.png');origatlas=rgba(origpath)
 workorig=copydep('sprites/chef-lena/work-'+d+'.png','original-work-'+d+'.png')
 delta={'N':(0,-128),'E':(128,0),'S':(0,128),'W':(-128,0)}[d];cr=(256,360);br=(cr[0]+delta[0],cr[1]+delta[1])
 for kind in ['source','candidate']:
  temp=OUT/'contexts'/('_'+kind+'-'+d);temp.mkdir(exist_ok=True)
  frames=[]
  for i in range(12):
   chef=logical(origatlas.crop(((i%6)*384,(i//6)*640,(i%6+1)*384,(i//6+1)*640))) if kind=='source' else logical(rgba(BASE/lookup[('load',d,i)]['path']))
   im=Image.new('RGBA',(512,640),BG['light']);dr=ImageDraw.Draw(im);dr.text((10,8),f'{kind} · load {d} · frame{i:02d} · roots at128px cell pitch',fill='#293442')
   for x in range(0,513,128):dr.line([(x,0),(x,640)],fill='#E2DCCF')
   for y in range(-24,641,128):dr.line([(0,y),(512,y)],fill='#E2DCCF')
   def putbelt():im.alpha_composite(beltim,(br[0]-96,br[1]-248))
   def putchef():im.alpha_composite(chef,(cr[0]-96,cr[1]-248))
   if d=='S':putchef();putbelt()
   else:putbelt();putchef()
   # Root/contact markers are outside delivered sprite pixels and labeled only in preview.
   dr=ImageDraw.Draw(im);dr.ellipse((cr[0]-3,cr[1]-3,cr[0]+3,cr[1]+3),outline='#334D68',width=1);dr.ellipse((br[0]-3,br[1]-3,br[0]+3,br[1]+3),outline='#AD5B34',width=1)
   dr.text((10,612),'Source native load ends holding; game transfers ownership after clip.',fill='#293442');im=im.convert('RGB');im.save(temp/f'{i:03d}.png');frames.append(im)
  video=OUT/'contexts'/f'{kind}-load-{d}.mp4';subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(temp/'%03d.png'),'-frames:v','12','-c:v','libx264','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
  for i in [0,5,11]:frames[i].save(OUT/'contexts'/f'{kind}-load-{d}-{i:02d}.png')
  ctx.append({'kind':kind,'direction':d,'path':str(video.relative_to(BASE)),'sha256':sha(video),'fps':12,'loop':False,'chefRoot':cr,'beltRoot':br,'cellPitch':128,'sourceConsistentLimitation':'Native load clip ends with dish still held; gameplay changes owner after last unique frame. No new beltLoad transform exists in source.'});shutil.rmtree(temp)
 # Following gameplay ownership transfer, show same chef work frame0 and separate original2D dish on belt support offset.
 chef=logical(rgba(BASE/lookup[('work',d,0)]['path']));im=Image.new('RGBA',(512,640),BG['light']);dr=ImageDraw.Draw(im);dr.text((10,8),f'Game next-state illustration · {d} · original support offset',fill='#293442')
 if d=='S':im.alpha_composite(chef,(cr[0]-96,cr[1]-248));im.alpha_composite(beltim,(br[0]-96,br[1]-248))
 else:im.alpha_composite(beltim,(br[0]-96,br[1]-248));im.alpha_composite(chef,(cr[0]-96,cr[1]-248))
 im.alpha_composite(dishim,(br[0]-96,round(br[1]-248-57.3440234375)));dr=ImageDraw.Draw(im);dr.text((10,612),'Illustration only: native work frame0 + separate2D belt dish.',fill='#293442');im.convert('RGB').save(OUT/'contexts'/f'game-transfer-{d}.png')
# Original/target/current common full-frame reference for inspection, never fitted.
comp=Image.new('RGB',(1152,664),BG['light']);dr=ImageDraw.Draw(comp)
for i,(title,path) in enumerate([('Original',BASE/'inputs/original.png'),('Fixed ImageGen target (aesthetic)',BASE/'inputs/target.png'),('Native round03',BASE/lookup[('idle','S',0)]['path'])]):
 im=rgba(path).resize((384,640),Image.Resampling.LANCZOS);comp.paste(flat(im,BG['light']),(i*384,24));dr.text((i*384+8,5),title,fill='#293442')
comp.save(OUT/'comparison.png')
# A simple playable evidence index. Nonloop load clips do not auto-repeat.
html='''<!doctype html><meta charset="utf-8"><title>Lena round03 native playback</title><style>body{margin:24px;background:#ece8dd;color:#263342;font:14px system-ui}h1{font-size:24px}.grid{display:grid;grid-template-columns:repeat(4,192px);gap:16px}figure{margin:0}video{display:block;width:192px;height:320px;background:#7c7c7c}button,select{font:inherit;margin:4px;padding:8px}.context video{width:256px;height:320px}.context{display:grid;grid-template-columns:repeat(4,256px);gap:16px}a{color:#224e79}details{margin:16px 0}img{max-width:100%}</style><h1>Lena · round03 · native12fps</h1><p>All16 clips use12 native frames at12fps. Idle/work/hold loop. Load stops at its original last frame. Full frames remain registered192×320; no fitting or pixel repaint.</p><button onclick="document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})">Play all from start</button><button onclick="document.querySelectorAll('video').forEach(v=>v.pause())">Pause all</button><div class="grid">'''
for v in videos:
 html+=f'<figure><figcaption>{v["id"]} ·12fps ·{"loop" if v["loop"] else "ends held"}</figcaption><video controls muted playsinline preload="auto" {"loop" if v["loop"] else ""} data-id="{v["id"]}" src="playback/{v["id"]}.mp4"></video></figure>'
html+='</div><h2>Source-consistent serving belt context · original128px pitch</h2><p>Native load action is unchanged. Source also finishes with the dish held; the game then transfers dish ownership. Source and candidate contexts are shown together. No separate authoritative beltLoad transform exists.</p><div class="context">'
for kind in ['source','candidate']:
 for d in DIRS:html+=f'<figure><figcaption>{kind} load {d}</figcaption><video controls muted playsinline preload="auto" src="contexts/{kind}-load-{d}.mp4"></video></figure>'
html+='</div><details><summary>Four native facings</summary><img src="four-view-sheet.png"></details><details><summary>Fixed reference comparison</summary><img src="comparison.png"></details><details><summary>Light/gray/dark evidence</summary>'
for bg in BG:html+=f'<a href="backgrounds/enlarged-edges-{bg}.png">{bg} enlarged edges</a> · <a href="backgrounds/all-states-facings-{bg}.png">{bg} states/facings</a><br>'
html+='</details><details><summary>Every frame on each background</summary>'
for e in evidence:
 if e['kind']=='all-frame-sheet':html+=f'<a href="{Path(e["path"]).relative_to("candidates/round-03")}">{e["clip"]}-{e["direction"]}-{e["background"]}</a> · '
html+='</details>'
(OUT/'playback.html').write_text(html)
(OUT/'atlas-manifest.json').write_text(json.dumps(atlases,indent=2));(OUT/'preview-manifest.json').write_text(json.dumps({'previews':evidence,'videos':videos,'contexts':ctx,'contextDependencies':ctxdeps,'alpha':alpha,'previewPolicy':'Composites use unchanged nativeRGBA, uniform logical scale and registered source roots. Text/backgrounds/root marks are preview-only.'},indent=2))
v=json.loads((OUT/'validation.json').read_text());v['atlasCount']=len(atlases);v['allAtlasFramesPixelExact']=all(rgba(OUT/'atlases'/f'{c}-{d}.png').crop(((i%6)*384,(i//6)*640,(i%6+1)*384,(i//6+1)*640)).tobytes()==rgba(BASE/lookup[(c,d,i)]['path']).tobytes() for c in CLIPS for d in DIRS for i in range(12));v['alphaClippedFrames']=[x for x in alpha if x['touchesFrameEdge']];v['videoCount']=len(videos);v['allVideosExact12fps12Frames']=True;v['backgroundSheets']=48;v['previewManifest']='preview-manifest.json';v['atlasManifest']='atlas-manifest.json';v['sourceConsistentBeltContext']='Source and candidate use original128px catalog pitch; original load action ends holding; gameplay then transfers ownership. No separate authoritative beltLoad transform exists.';v['ok']=v['ok'] and v['allAtlasFramesPixelExact'] and not v['alphaClippedFrames'];(OUT/'validation.json').write_text(json.dumps(v,indent=2))
print(json.dumps({'atlases':len(atlases),'videos':len(videos),'backgroundSheets':48,'clipped':len(v['alphaClippedFrames']),'ok':v['ok']}))
