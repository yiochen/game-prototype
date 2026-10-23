"""Lossless native atlas packing and registered inspection contexts. Python+Pillow.
Does not alter raw captures. Derived previews preserve complete frame, declared roots,
and explicit integer scale factors. Atlas pixel crops are checked byte-for-pixel.
"""
import json,pathlib,hashlib,math,shutil
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parent;OBJ=P.parent;OUT=OBJ/'candidates/round-02';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
meta=json.loads((P/'resources/original-catalog-object.json').read_text());ledger=json.loads((OUT/'candidate-phases.json').read_text());raw=[];atlases=[];previews={};backgrounds={'light':(239,233,223,255),'gray':(128,128,128,255),'dark':(32,35,43,255)}
def rel(p):return str(p.relative_to(OBJ))
def composed(im,bg):
 o=Image.new('RGBA',im.size,bg);o.alpha_composite(im);return o
for e in ledger:
 p=OBJ/e['path'];im=Image.open(p).convert('RGBA');assert im.size==(896,1152)
 alpha=im.getchannel('A');bounds=alpha.getbbox();assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<896 and bounds[3]<1152
 raw.append({'clip':e['clip'],'direction':e['direction'],'index':e['frame']-1,'path':e['path'],'sha256':sha(p),'alphaBounds':list(bounds),'size':[896,1152]})
assert len(raw)==100
for clip in meta['clips']:
 for d in ['N','E','S','W']:
  spec=clip['directions'][d];atlas=Image.new('RGBA',tuple(spec['atlasSize']));records=sorted([r for r in raw if r['clip']==clip['id'] and r['direction']==d],key=lambda x:x['index'])
  for r,rect in zip(records,spec['rects']):
   im=Image.open(OBJ/r['path']).convert('RGBA');x,y,w,h=rect;assert (w,h)==im.size;atlas.paste(im,(x,y));assert atlas.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
  ap=OUT/'atlases'/(clip['id']+'-'+d+'.png');ap.parent.mkdir(exist_ok=True);atlas.save(ap)
  atlases.append({'clip':clip['id'],'direction':d,'path':rel(ap),'sha256':sha(ap),'columns':spec['columns'],'rows':spec['rows'],'size':spec['atlasSize'],'rects':spec['rects'],'fps':12,'loop':clip['loop'],'frameOrder':clip['frameOrder']})
# Every exact full native frame is embedded in fixed full-frame logical and half-logical canvases on all backgrounds.
for clip in meta['clips']:
 for d in ['N','E','S','W']:
  recs=sorted([r for r in raw if r['clip']==clip['id'] and r['direction']==d],key=lambda r:r['index'])
  for denom,label in [(2,'logical'),(4,'phone')]:
   w,h=896//denom,1152//denom;ncol=min(6,len(recs));nrow=math.ceil(len(recs)/ncol);panelh=h+22
   sheet=Image.new('RGBA',(w*ncol,panelh*nrow*3));draw=ImageDraw.Draw(sheet)
   for row,(bname,bg) in enumerate(backgrounds.items()):
    for n,r in enumerate(recs):
     x=(n%ncol)*w;y=(row*nrow+n//ncol)*panelh;im=Image.open(OBJ/r['path']).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);sheet.alpha_composite(composed(im,bg),(x,y+22));draw.text((x+6,y+5),f'{clip["id"]} {d} phase{n+1} {bname} {label}',fill='white')
   p=PRE/(clip['id']+'-'+d+'-'+label+'-three-backgrounds.png');sheet.save(p);previews[p.stem]=rel(p)
# Four-facing full native frame backgrounds; no crop, no fit.
for denom,label in [(1,'native'),(2,'logical'),(4,'phone')]:
 w,h=896//denom,1152//denom;sheet=Image.new('RGBA',(w*4,(h+22)*3));draw=ImageDraw.Draw(sheet)
 for row,(bname,bg) in enumerate(backgrounds.items()):
  for col,d in enumerate(['N','E','S','W']):
   p=OUT/'frames'/('idle-'+d)/'000.png';im=Image.open(p).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);sheet.alpha_composite(composed(im,bg),(col*w,row*(h+22)+22));draw.text((col*w+6,row*(h+22)+5),f'idle {d} {bname} {label} full frame',fill='white')
 p=PRE/('four-view-'+label+'.png');sheet.save(p);previews[p.stem]=rel(p)
# Context source pixels are retained exact. Grid tile is1cell=256nativepx, actor uses2x source scale.
context=json.loads((P/'resources/context-inputs.json').read_text());floor=Image.open(P/'resources/context-floor-cream.png').convert('RGBA');human=Image.open(P/'resources/context-chef-lena-S.png').convert('RGBA');assert floor.size==(256,256);assert human.size==(384,640)
def floor_canvas(size):
 out=Image.new('RGBA',size)
 for y in range(0,size[1],256):
  for x in range(0,size[0],256):out.paste(floor,(x,y))
 return out
def sprite_at(canvas,im,root,anchor):canvas.alpha_composite(im,(root[0]-anchor[0],root[1]-anchor[1]))
ctxrecords=[]
for d in ['N','E','S','W']:
 c=floor_canvas((1280,1280));sprite_at(c,Image.open(OUT/'frames'/('idle-'+d)/'000.png').convert('RGBA'),(512,768),(448,704));sprite_at(c,human,(1024,768),(192,496));p=PRE/('registered-floor-human-'+d+'-native.png');c.save(p);previews[p.stem]=rel(p);ctxrecords.append({'path':rel(p),'sourceScale':2,'cellNativePixels':256,'sofaRoot':[512,768],'sofaRawAnchor':[448,704],'humanRoot':[1024,768],'humanRawAnchor':[192,496],'sofaAndHumanSampling':'Identity native source pixels; no fitting, scaling, crop or regrade'})
 # Full context downsample at exactly one-half / one-quarter, never per-object fit.
 for denom,label in [(2,'logical'),(4,'phone')]:
  p=PRE/('registered-floor-human-'+d+'-'+label+'.png');c.resize((1280//denom,1280//denom),Image.Resampling.LANCZOS).save(p);previews[p.stem]=rel(p)
c=floor_canvas((1792,1536));placements=[('S',(512,768)),('N',(1280,1024))]
for d,r in placements:sprite_at(c,Image.open(OUT/'frames'/('idle-'+d)/'000.png').convert('RGBA'),r,(448,704))
sprite_at(c,human,(1280,512),(192,496));p=PRE/'repeated-fixed-root-native.png';c.save(p);previews[p.stem]=rel(p);ctxrecords.append({'path':rel(p),'cellNativePixels':256,'placements':[{'direction':d,'root':r,'anchor':[448,704]} for d,r in placements],'humanRoot':[1280,512],'humanRawAnchor':[192,496],'sampling':'Identity native RGBA compositing on unchanged floor tiles'})
# Native last frame is retained opaque. Removal is shown as a separately declared game-context state.
reveal=[]
for label,clip,index in [('assembled','idle',0),('clearance-middle','clearance',5),('clearance-native-terminal','clearance',11),('removed-surrounding-context',None,None)]:
 c=floor_canvas((1280,1280))
 if clip:sprite_at(c,Image.open(OUT/'frames'/(clip+'-S')/('%03d.png'%index)).convert('RGBA'),(512,768),(448,704))
 sprite_at(c,human,(1024,768),(192,496));p=PRE/('floor-reveal-'+label+'-native.png');c.save(p);previews[p.stem]=rel(p);reveal.append({'label':label,'path':rel(p),'clip':clip,'index':index,'root':[512,768],'separateRemovalContext':clip is None})
# Sheet at exact logical context size with external labels.
sheet=Image.new('RGBA',(2560,666),(35,38,44,255));draw=ImageDraw.Draw(sheet)
for i,r in enumerate(reveal):
 sheet.alpha_composite(Image.open(OBJ/r['path']).resize((640,640),Image.Resampling.LANCZOS),(i*640,26));draw.text((i*640+6,6),r['label'],fill='white')
p=PRE/'floor-reveal-logical.png';sheet.save(p);previews[p.stem]=rel(p)
write(OUT/'context-registration.json',{'inputs':context,'contexts':ctxrecords,'floorReveal':reveal,'excludedFloorIntegrity':[{**x,'unchanged':sha(x['path'])==x['sha256']} for x in context['excludedFloorIntegrity']]})
write(OUT/'raw-frame-manifest.json',raw);write(OUT/'atlas-manifest.json',atlases);write(OUT/'preview-manifest.json',previews)
# Actual12fps browser player. Each canvas receives the full native frame at an explicit scale.
frame_paths={clip['id']:{d:[str((pathlib.Path('..')/'frames'/(clip['id']+'-'+d)/('%03d.png'%i))) for i in range(clip['frames'])] for d in ['N','E','S','W']} for clip in meta['clips']}
html='''<!doctype html><meta charset="utf-8"><title>Garbage sofa native12fps inspection</title><style>body{background:#333944;color:#eee;font:14px system-ui;margin:16px}button,select{font:inherit}section{display:flex;gap:12px;margin:12px 0;overflow:auto}.view{flex:none}canvas{display:block;background:#808080}h2{font-size:16px}.small{max-width:1000px}#metrics{position:sticky;top:0;background:#181d28;padding:10px}</style><h1>Native sofa playback</h1><p class="small">100 full native896×1152 frames. Fixed root448,704; source scale2. Highlighted loops at12fps. Clearance plays once at12fps and holds its actual opaque final phase. Removed floor is a separate context shown in the saved floor-reveal previews.</p><label>Background <select id="bg"><option value="#808080">gray</option><option value="#efe9df">light</option><option value="#20232b">dark</option></select></label> <label>Full-frame size <select id="size"><option value="224">224×288 half-logical</option><option value="448">448×576 logical</option><option value="896">896×1152 native</option></select></label> <button id="replay">Replay</button> <button id="pause">Pause</button><div id="metrics" role="status">Loading all100 native frames…</div><main></main><script>const paths=FRAMEPATHS,dirs=['N','E','S','W'],images={},canvases={};let start=0,elapsed=0,paused=false,allDecoded=false,presentations=0,lastIndex=-1;const main=document.querySelector('main');for(const clip of ['highlighted','clearance']){let title=document.createElement('h2');title.textContent=clip;main.append(title);const section=document.createElement('section');main.append(section);canvases[clip]={};images[clip]={};for(const d of dirs){let view=document.createElement('div');view.className='view';view.append(document.createTextNode(d));let cv=document.createElement('canvas');cv.width=224;cv.height=288;view.append(cv);section.append(view);canvases[clip][d]=cv;images[clip][d]=paths[clip][d].map(path=>{let im=new Image();im.src=path;return im})}}const idle=dirs.flatMap(d=>paths.idle[d].map(path=>{let im=new Image();im.src=path;return im}));Promise.all([...idle,...Object.values(images).flatMap(x=>Object.values(x).flat())].map(im=>im.decode())).then(()=>{allDecoded=true;start=performance.now();requestAnimationFrame(tick)});function tick(now){if(!paused)elapsed=Math.max(0,now-start);const nativeTick=Math.floor(elapsed*12/1000),hi=nativeTick%12,cl=Math.min(11,nativeTick);if(nativeTick!==lastIndex){presentations++;lastIndex=nativeTick}for(const clip of ['highlighted','clearance'])for(const d of dirs){let cv=canvases[clip][d],ctx=cv.getContext('2d');ctx.fillStyle=document.querySelector('#bg').value;ctx.fillRect(0,0,cv.width,cv.height);ctx.drawImage(images[clip][d][clip==='highlighted'?hi:cl],0,0,cv.width,cv.height)}const state={allDecoded,decodedFrames:100,fps:12,elapsedMs:Math.round(elapsed),highlightedWraps:Math.floor(nativeTick/12),highlightedIndex:hi,clearanceIndex:cl,clearanceHoldingNativeFinal:nativeTick>=12,canvasWidth:canvases.highlighted.S.width,background:document.querySelector('#bg').value,presentations};window.playbackState=state;document.querySelector('#metrics').textContent=JSON.stringify(state);requestAnimationFrame(tick)}document.querySelector('#replay').onclick=()=>{start=performance.now();elapsed=0;paused=false;presentations=0;lastIndex=-1};document.querySelector('#pause').onclick=()=>{paused=!paused;if(!paused)start=performance.now()-elapsed};document.querySelector('#size').onchange=()=>{const w=+document.querySelector('#size').value;for(const group of Object.values(canvases))for(const cv of Object.values(group)){cv.width=w;cv.height=w*1152/896}};</script>'''.replace('FRAMEPATHS',json.dumps(frame_paths))
p=PRE/'temporal-player.html';p.write_text(html);previews['temporal-player']=rel(p);write(OUT/'preview-manifest.json',previews)
print('PACKED',len(raw),len(atlases),len(previews))
