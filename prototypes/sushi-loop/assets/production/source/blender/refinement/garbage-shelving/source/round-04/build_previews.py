"""Preview-only exact-frame assembly. Never edits native render pixels, transforms only complete frames uniformly."""
from pathlib import Path
import json,hashlib,shutil,subprocess,math
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/round-04';PRE=OUT/'previews';PRE.mkdir(exist_ok=True);RES=HERE/'resources/context'
DIRS=['S','E','N','W'];BGS={'light':(235,231,219),'gray':(118,118,118),'dark':(27,34,41)};SIZES={'native':(896,1344),'logical':(448,672),'half':(224,336),'consumer55-4x':(770,1155)}
FONT=ImageFont.load_default(size=18);SMALL=ImageFont.load_default(size=12)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def native(c,d,i=0):return Image.open(OUT/'frames'/f'{c}-{d}'/f'{i:03d}.png').convert('RGBA')
def bgim(im,bg):
 p=Image.new('RGBA',im.size,(*bg,255));p.alpha_composite(im);return p.convert('RGB')
def label(draw,xy,s,font=FONT,color=(235,235,230)):draw.text(xy,s,fill=color,font=font)
raw=[];atlases=[]
for c,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in DIRS:
  cols,rows=(1,1) if c=='idle' else (6,2);a=Image.new('RGBA',(896*cols,1344*rows));rects=[]
  for i in range(n):
   p=OUT/'frames'/f'{c}-{d}'/f'{i:03d}.png';im=Image.open(p);assert im.mode=='RGBA' and im.size==(896,1344);pos=(i%cols*896,i//cols*1344);a.paste(im,pos);rects.append([*pos,896,1344]);raw.append({'clip':c,'direction':d,'index':i,'path':str(p.relative_to(OBJ)),'sha256':sha(p)})
  folder=OUT/'atlases';folder.mkdir(exist_ok=True);p=folder/f'{c}-{d}.png';a.save(p)
  for i,r in enumerate(rects):assert a.crop((r[0],r[1],r[0]+r[2],r[1]+r[3])).tobytes()==native(c,d,i).tobytes()
  atlases.append({'clip':c,'direction':d,'path':str(p.relative_to(OBJ)),'sha256':sha(p),'columns':cols,'rows':rows,'size':list(a.size),'rects':rects,'fps':12,'loop':c=='highlighted','frameOrder':list(range(n))})
dump(OUT/'raw-frame-records.json',raw);dump(OUT/'atlas-records.json',atlases)
# Complete registered frame sheets at native, logical, half and 4x exact consumer55 display scale.
for sizeName,size in SIZES.items():
 for bn,bg in BGS.items():
  w,h=size;sheet=Image.new('RGB',(w*4,h+40),bg);dr=ImageDraw.Draw(sheet)
  for i,d in enumerate(DIRS):sheet.paste(bgim(native('idle',d).resize(size,Image.Resampling.LANCZOS),bg),(i*w,40));label(dr,(i*w+8,8),f'{d} | {sizeName}',color=(50,50,50) if bn=='light' else (230,230,230))
  sheet.save(PRE/f'four-view-{sizeName}-{bn}.png')
  for c in ['highlighted','clearance']:
   for d in DIRS:
    sheet=Image.new('RGB',(w*6,h*2+56),bg);dr=ImageDraw.Draw(sheet);label(dr,(8,8),f'{c}-{d} | all12 | {sizeName} | fixed whole frames',color=(50,50,50) if bn=='light' else (235,235,235))
    for i in range(12):sheet.paste(bgim(native(c,d,i).resize(size,Image.Resampling.LANCZOS),bg),((i%6)*w,56+(i//6)*h))
    sheet.save(PRE/f'{c}-{d}-{sizeName}-{bn}-all12.png')
# Fixed-source/context resources are byte copies. Floor-cream is displayed by its exact published tile.
floor=Image.open(RES/'floor-cream.png').convert('RGBA');chef=Image.open(RES/'chef-lena-idle-S.png').convert('RGBA').crop((0,0,384,640))
contextManifest={'method':'Complete registered-frame alpha compositing at exact sourceScale2; no alpha fitting or recoloring','floor':{'path':str((RES/'floor-cream.png').relative_to(OBJ)),'sha256':sha(RES/'floor-cream.png'),'tileNative':[256,256]},'chefReference':{'path':str((RES/'chef-lena-idle-S.png').relative_to(OBJ)),'sha256':sha(RES/'chef-lena-idle-S.png'),'nativeFrame':[384,640],'root':[192,496],'atlasRect':[0,0,384,640],'clip':'idle','index':0,'direction':'S'},'humanCatalog':{'gridSize':[5,3],'placements':[{'object':'garbage-shelving','x':0,'y':0,'rootCell':[1,1]},{'object':'chef-lena','x':3,'y':0}]},'excludedFloors':[],'contexts':[]}
for name in ['floor-cream','floor-blue-wave','floor-checker']:
 p=RES/f'{name}.png';contextManifest['excludedFloors'].append({'path':str(p.relative_to(OBJ)),'sha256':sha(p),'designUnmodified':True})
# Context canvas retains every whole input frame; margins accommodate its authored transparent padding.
def floorcanvas(gridw,gridh):
 margin=(360,600);im=Image.new('RGBA',(gridw*256+720,gridh*256+850),BGS['dark']+(255,))
 for y in range(gridh):
  for x in range(gridw):im.alpha_composite(floor,(margin[0]+x*256,margin[1]+y*256))
 return im,margin
def place(im,fr,anchor,root):im.alpha_composite(fr,(int(root[0]-anchor[0]),int(root[1]-anchor[1])))
def maskdraw(im,origin,xy,span=(2,2),outline=True):
 # Grid x/y are authored cell coordinates; rootCell1,1 is at mask center.
 dr=ImageDraw.Draw(im);x=origin[0]+xy[0]*256;y=origin[1]+xy[1]*256
 if outline:
  dr.rectangle((x,y,x+span[0]*256,y+span[1]*256),outline=(40,190,220,255),width=4);dr.line((x+256,y,x+256,y+512),fill=(40,190,220,180),width=2);dr.line((x,y+256,x+512,y+256),fill=(40,190,220,180),width=2)
 root=(x+256,y+256);dr.line((root[0]-12,root[1],root[0]+12,root[1]),fill=(245,65,80),width=3);dr.line((root[0],root[1]-12,root[0],root[1]+12),fill=(245,65,80),width=3)
for d in DIRS:
 im,origin=floorcanvas(5,3);r=(origin[0]+256,origin[1]+256);place(im,native('idle',d),(448,896),r);place(im,chef,(192,496),(origin[0]+3*256+128,origin[1]+128))
 p=PRE/f'human-context-{d}.png';im.convert('RGB').save(p);ann=im.copy();maskdraw(ann,origin,(0,0));label(ImageDraw.Draw(ann),(20,20),f'{d}: literal5x3 catalog | garbage0,0 rootCell1,1 | chef3,0');ann.convert('RGB').save(PRE/f'human-context-{d}-mask-root.png');contextManifest['contexts'].append({'type':'human','direction':d,'path':str(p.relative_to(OBJ)),'nativeCell':256,'garbageRoot':r,'chefRoot':[origin[0]+896,origin[1]+128]})
 # Actual consumer55pxcell by one uniform resize from native256pxcell, CSS displayed natural resulting size.
 im.resize((int(im.width*55/256),int(im.height*55/256)),Image.Resampling.LANCZOS).convert('RGB').save(PRE/f'human-context-{d}-consumer55.png')
 # Four whole assemblies at two-cell centers; separate one-cell-gap row.
 im,origin=floorcanvas(6,7)
 placements=[(0,0),(2,0),(0,2),(2,2),(0,5),(3,5)]
 for x,y in placements:place(im,native('idle',d),(448,896),(origin[0]+(x+1)*256,origin[1]+(y+1)*256))
 p=PRE/f'repeated-{d}.png';im.convert('RGB').save(p);ann=im.copy()
 for x,y in placements:maskdraw(ann,origin,(x,y))
 label(ImageDraw.Draw(ann),(20,20),f'{d}:2x2 assembly centers2cells | gaprow centers3cells');ann.convert('RGB').save(PRE/f'repeated-{d}-mask-root.png');im.resize((int(im.width*55/256),int(im.height*55/256)),Image.Resampling.LANCZOS).convert('RGB').save(PRE/f'repeated-{d}-consumer55.png');contextManifest['contexts'].append({'type':'repeated','direction':d,'path':str(p.relative_to(OBJ)),'nativeCell':256,'placements':placements,'oneCellGapRow':True})
 # Floor reveal uses the same floor pixel bytes composited below transparent frames.
 folder=PRE/'floor-reveal'/d;folder.mkdir(parents=True,exist_ok=True);video=folder/'video-frames';video.mkdir(exist_ok=True)
 base,origin=floorcanvas(4,4);r=(origin[0]+512,origin[1]+512)
 before=base.copy();place(before,native('idle',d),(448,896),r);before.convert('RGB').save(folder/'idle.png')
 for i in range(12):
  im=base.copy();place(im,native('clearance',d,i),(448,896),r);im.convert('RGB').save(folder/f'clearance-{i:03d}.png');im.convert('RGB').save(video/f'{i:03d}.png')
 # Terminal fragment hold and truly separate after-consumer-removal state.
 im.convert('RGB').save(folder/'terminal-fragments.png');base.convert('RGB').save(folder/'after-consumer-removal.png');ann=before.copy();maskdraw(ann,(origin[0]+256,origin[1]+256),(0,0));ann.convert('RGB').save(folder/'support-mask-outline.png')
 for i in range(12,36):Image.open(video/'011.png').save(video/f'{i:03d}.png')
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','12','-i',str(video/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','12',str(folder/'clearance-one-shot-finalhold.mp4')],check=True)
 contextManifest['contexts'].append({'type':'floorReveal','direction':d,'folder':str(folder.relative_to(OBJ)),'root':r,'cleanFloorSeparateFromTerminal':True,'sourceFloorSHA256':sha(RES/'floor-cream.png')})
# Transient neighboring-assembly overlap is separate from stationary occupancy.
for d in DIRS:
 folder=PRE/'repeated-clearance'/d;folder.mkdir(parents=True,exist_ok=True)
 base,origin=floorcanvas(5,5)
 for i in range(12):
  im=base.copy()
  for x,y in [(0,0),(2,0),(0,2),(2,2)]:place(im,native('clearance',d,i),(448,896),(origin[0]+(x+1)*256,origin[1]+(y+1)*256))
  im.convert('RGB').save(folder/f'{i:03d}.png')
 # Encode the entire native context without stretching or fitting; native width/height are even.
 for i in range(12,36):Image.open(folder/'011.png').save(folder/f'{i:03d}.png')
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','12','-i',str(folder/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','12',str(folder/'clearance-2x2-overlap.mp4')],check=True)
 contextManifest['contexts'].append({'type':'repeatedTransientClearance','direction':d,'folder':str(folder.relative_to(OBJ)),'fixedCentersTwoCells':True,'transientOverlapExpectedFromOriginalScatter':True})
# All eight actual12fps moving streams, with synchronized original comparison, logical plus half and exact CSS55pxcell.
# HTML uses elapsed time*12 to update complete-frame image bitmaps; source native captures are immutable read-only.
original=OBJ/'reviews/source-audit/native-original'
resources=PRE/'original-comparison';resources.mkdir(exist_ok=True)
for c,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in DIRS:
  fol=resources/f'{c}-{d}';fol.mkdir(exist_ok=True)
  for i in range(n):shutil.copyfile(original/f'{c}-{d}'/f'{i:03d}.png',fol/f'{i:03d}.png')
html='''<!doctype html><meta charset="utf-8"><title>garbage-shelving native12fps comparison</title><style>body{background:#1b2229;color:#ece7db;font:14px system-ui;margin:20px}button,select{font:inherit;margin:4px}section{margin:22px 0;border-top:1px solid #52606a;padding:12px;overflow:auto}.views{display:flex;gap:8px;align-items:flex-end}figure{margin:0}figcaption{padding:5px}.stage{display:flex;align-items:flex-end;gap:5px}canvas{background:#767676}input{width:220px}header{position:sticky;top:0;background:#1b2229;padding:10px;z-index:2}</style><header><b>Native12fps: source/candidate synchronized whole-frame comparison.</b><br>Highlighted plays at least3wraps; clearance runs once and holds opaque terminal fragments. Restart is explicit. Camera and registration never fit. Consumer uses exactly55CSSpx per cell.<br><button id="restart">Restart all</button><button id="toggle">Pause/play</button><select id="bg"><option value="#767676">Middle gray</option><option value="#ebe7db">Light</option><option value="#1b2229">Dark</option></select></header><main></main><script>const dirs=['S','E','N','W'],clips=['highlighted','clearance'];let start=performance.now(),pause=false,frozen=0;const groups=[];const bg=document.querySelector('#bg');function make(c,d){let sec=document.createElement('section');sec.innerHTML=`<h3>${c}-${d} ·12fps ${c==='highlighted'?'loop;3wraps minimum':'one shot with final hold'}</h3><button class="restart">Restart this</button><input type="range" min="0" max="11" step="1" value="0"><span></span><div class="views"></div>`;document.querySelector('main').append(sec);let g={c,d,start:performance.now(),images:[[],[]],canvases:[],manual:null};for(let j=0;j<2;j++){for(let i=0;i<12;i++){let im=new Image;im.src=j===0?`original-comparison/${c}-${d}/${String(i).padStart(3,'0')}.png`:`../frames/${c}-${d}/${String(i).padStart(3,'0')}.png`;g.images[j].push(im)}}for(let [name,w,h] of [['Logical',448,672],['Half',224,336],['Consumer55pxcell',192.5,288.75]]){let f=document.createElement('figure');f.innerHTML=`<figcaption>${name}: original | candidate</figcaption><div class="stage"></div>`;for(let j=0;j<2;j++){let cv=document.createElement('canvas');cv.width=896;cv.height=1344;cv.style.width=w+'px';cv.style.height=h+'px';f.lastChild.append(cv);g.canvases.push([cv,j])}sec.querySelector('.views').append(f)}g.sec=sec;sec.querySelector('.restart').onclick=()=>{g.start=performance.now();g.manual=null};sec.querySelector('input').oninput=e=>g.manual=Number(e.target.value);groups.push(g)}for(let c of clips)for(let d of dirs)make(c,d);document.querySelector('#restart').onclick=()=>groups.forEach(g=>{g.start=performance.now();g.manual=null});document.querySelector('#toggle').onclick=()=>{pause=!pause;if(pause)frozen=performance.now();else{let dt=performance.now()-frozen;groups.forEach(g=>g.start+=dt)}};function tick(now){for(let g of groups){let raw=Math.floor(((pause?frozen:now)-g.start)*12/1000),i=g.manual??(g.c==='highlighted'?raw%12:Math.min(11,raw));g.sec.querySelector('span').textContent=` frame${i+1}/12 · ${g.c==='highlighted'?'wrap'+Math.floor(raw/12):raw>11?'terminal fragments held':''}`;g.sec.querySelector('input').value=i;for(let[cv,j]of g.canvases){let ct=cv.getContext('2d');ct.fillStyle=bg.value;ct.fillRect(0,0,896,1344);if(g.images[j][i]?.complete)ct.drawImage(g.images[j][i],0,0)}}requestAnimationFrame(tick)}requestAnimationFrame(tick);</script>'''
(PRE/'playback.html').write_text(html)
# Render short12fps encoded per-facing stream side by side at half logical size on all3backgrounds.
for c in ['highlighted','clearance']:
 for d in DIRS:
  folder=PRE/'moving-frames'/f'{c}-{d}';folder.mkdir(parents=True,exist_ok=True);count=48 if c=='highlighted' else 36
  for j in range(count):
   i=j%12 if c=='highlighted' else min(j,11);pair=Image.new('RGB',(224*2*3,336),BGS['dark'])
   for bn,bg in enumerate(BGS.values()):
    for q,im in enumerate([Image.open(resources/f'{c}-{d}'/f'{i:03d}.png').convert('RGBA'),native(c,d,i)]):pair.paste(bgim(im.resize((224,336),Image.Resampling.LANCZOS),bg),((bn*2+q)*224,0))
   pair.save(folder/f'{j:03d}.png')
  p=PRE/f'{c}-{d}-12fps.mp4';subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','12','-i',str(folder/'%03d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','12',str(p)],check=True)
# Browser-oriented index keeps all native/context previews discoverable.
(PRE/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>garbage-shelving round04 evidence</title><style>body{background:#1b2229;color:#eee;font:16px system-ui}img{max-width:95vw}a{color:#8ddcff}details{padding:10px}</style><h1>Garbage shelving round04 native evidence</h1><p><a href="playback.html">Eight synchronized12fps streams, logical/half/exact55pxcell</a></p>'+''.join(f'<details><summary>{p.name}</summary><a href="{p.name}">Full image</a><br><img loading="lazy" src="{p.name}"></details>' for p in sorted(PRE.glob('*.png')))+''.join(f'<h2>{c}-{d}:12fps, source|candidate, light/gray/dark</h2><video controls muted playsinline src="{c}-{d}-12fps.mp4"></video>' for c in ['highlighted','clearance'] for d in DIRS))
dump(OUT/'context-manifest.json',contextManifest)
# Raster mechanical checks; an approval is outside this script's role.
checks=[]
for r in raw:
 im=Image.open(OBJ/r['path']);bb=im.getchannel('A').getbbox();checks.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'alphaBBox':list(bb) if bb else None,'borderPixels':min(bb[0],bb[1],896-bb[2],1344-bb[3]) if bb else None,'nonzeroAlphaPixels':sum(x>0 for x in im.getchannel('A').getdata())})
closures=[]
for d in DIRS:
 a=native('highlighted',d);b=Image.open(OUT/'closure'/f'highlighted-{d}-013.png');diff=ImageChops.difference(a,b);closures.append({'direction':d,'RGBAExact':a.tobytes()==b.tobytes(),'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'maxRGBA':diff.getextrema()})
dump(OUT/'raster-audit.json',{'nativeCount':len(raw),'atlasCount':len(atlases),'atlasPixelIdentityToFullFrames':True,'phases':checks,'minimumNativeBorder':min(c['borderPixels'] for c in checks),'closure':closures,'consumerScale':'CSS exact55pxcell; bitmap consumer55-4x uses uniform770x1155 then display25percent; near-integer context snapshots preserve one global scale','backgrounds':BGS,'noSubjectFitting':True})
print('PREVIEWS_DONE',OUT,flush=True)
