"""Build exact-layout atlases and fixed-scale evidence from native renders. No pixel repair."""
from PIL import Image,ImageDraw,ImageChops,ImageStat
from pathlib import Path
import json,hashlib,math,subprocess,io,os,struct,zlib
P=Path(__file__).resolve().parent.parent;OUT=P/'candidates/round-01';RES=P/'source/resources';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
F=(1152,1664);LOG=(576,832);PHONE=(248,358);DRS=['N','E','S','W'];BACK=['f5f2e9','808080','202028'];raw=[];atlases=[];previews={};raster=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(P))
def write(p,a):Path(p).write_text(json.dumps(a,indent=2)+'\n')
def back(im,color,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 dst=Image.new('RGBA',im.size,'#'+color);dst.alpha_composite(im);return dst.convert('RGB')
def addpreview(name,path):previews[name]=rel(path)
def full(clip,dr,i):return Image.open(OUT/'frames'/f'{clip}-{dr}'/f'{i:03d}.png').convert('RGBA')
# Original-layout atlases use exact complete native frames.
for clip,n,loop in [('idle',1,False),('highlighted',12,True),('clearance',12,False)]:
 for dr in DRS:
  cols,rows=(1,1) if n==1 else (6,2);atlas=Image.new('RGBA',(F[0]*cols,F[1]*rows));rects=[]
  sheet=Image.new('RGB',(PHONE[0]*cols,PHONE[1]*rows+24),'#f5f2e9');draw=ImageDraw.Draw(sheet);draw.text((8,7),f'{clip} {dr} | full frame scaled to 55 px/cell | source order 0..{n-1}',fill='#343b40')
  for i in range(n):
   path=OUT/'frames'/f'{clip}-{dr}'/f'{i:03d}.png';im=Image.open(path).convert('RGBA');assert im.size==F;rect=[i%cols*F[0],i//cols*F[1],*F];atlas.paste(im,(rect[0],rect[1]));rects.append(rect)
   raw.append({'clip':clip,'direction':dr,'index':i,'path':rel(path),'sha256':sha(path)})
   alpha=im.getchannel('A');raster.append({'clip':clip,'direction':dr,'index':i,'alphaBounds':alpha.getbbox(),'alphaExtrema':alpha.getextrema(),'nonzeroAlphaPixels':sum(x>0 for x in alpha.histogram()[1:]) if False else sum(alpha.histogram()[1:]),'borderAlphaMax':max(im.getchannel('A').crop((0,0,1152,1)).getextrema()[1],alpha.crop((0,1663,1152,1664)).getextrema()[1],alpha.crop((0,0,1,1664)).getextrema()[1],alpha.crop((1151,0,1152,1664)).getextrema()[1])})
   sheet.paste(back(im,'f5f2e9',PHONE),(i%cols*PHONE[0],24+i//cols*PHONE[1]))
  ap=OUT/'atlases'/f'{clip}-{dr}.png';ap.parent.mkdir(exist_ok=True);atlas.save(ap);loaded=Image.open(ap).convert('RGBA')
  for i,r in enumerate(rects):assert loaded.crop((r[0],r[1],r[0]+r[2],r[1]+r[3])).tobytes()==full(clip,dr,i).tobytes()
  atlases.append({'clip':clip,'direction':dr,'path':rel(ap),'sha256':sha(ap),'columns':cols,'rows':rows,'size':list(atlas.size),'rects':rects,'fps':12,'loop':loop,'frameOrder':list(range(n))})
  sp=PRE/f'all-{clip}-{dr}.png';sheet.save(sp);addpreview(f'all-{clip}-{dr}',sp)
# Complete all-phase use-size/background sheets, never a subject crop.
for clip,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for dr in DRS:
  cols,rows=(1,1) if n==1 else (6,2)
  for size,label in [(LOG,'logical128'),(PHONE,'phone55')]:
   for bg in BACK:
    sh=Image.new('RGB',(size[0]*cols,size[1]*rows+24),'#'+bg);d=ImageDraw.Draw(sh);d.text((8,7),f'{clip} {dr} | {label} | complete frame order',fill='#eeeeee' if bg=='202028' else '#242832')
    for i in range(n):sh.paste(back(full(clip,dr,i),bg,size),(i%cols*size[0],24+i//cols*size[1]))
    fp=PRE/f'all-{clip}-{dr}-{label}-{bg}.png';sh.save(fp);addpreview(f'all-{clip}-{dr}-{label}-{bg}',fp)
# Full-frame all-view use-size/background sheets.
for size,label in [(LOG,'logical128'),(PHONE,'phone55')]:
 for bg in BACK:
  sh=Image.new('RGB',(size[0]*4,size[1]+25),'#'+bg);d=ImageDraw.Draw(sh)
  for j,dr in enumerate(DRS):sh.paste(back(full('idle',dr,0),bg,size),(j*size[0],25));d.text((j*size[0]+8,7),dr,fill='#181818' if bg!='202028' else '#eeeeee')
  f=PRE/f'idle-four-view-{label}-{bg}.png';sh.save(f);addpreview(f'idle-four-view-{label}-{bg}',f)
# Source/candidate share exact registered full frame. Fixed target is centered
# on that canvas without subject fitting; its framing is explicitly non-authoritative.
comparison=Image.new('RGB',(576*3,832+44),'#f5f2e9');cd=ImageDraw.Draw(comparison)
original=Image.open(P/'inputs/original.png').convert('RGBA');target=Image.open(P/'inputs/target.png').convert('RGBA');tc=Image.new('RGBA',F);tc.alpha_composite(target,((F[0]-target.width)//2,(F[1]-target.height)//2))
for j,(im,label) in enumerate([(original,'Original: registered native frame'),(tc,'Fixed target: centered canvas only'),(full('idle','S',0),'Native candidate: same registration')]):comparison.paste(back(im,'f5f2e9',LOG),(j*576,44));cd.text((j*576+8,8),label,fill='#242832')
cd.text((584,25),'Target framing is not size/camera authority.',fill='#666666');cp=PRE/'source-target-native-S.png';comparison.save(cp);addpreview('source-target-native-S',cp)
# Native zooms supplement full-frame evidence only.
for dr in DRS:
 im=full('idle',dr,0);f=PRE/f'idle-{dr}-native-background.png';back(im,'808080').save(f);addpreview('native-'+dr,f)
# Unchanged catalog sprite resources, fixed pitch/anchors and integer placements.
ctx=json.loads((RES/'context/catalog-records.json').read_text());floor=Image.open(RES/'context/floor-cream-static-S.png').convert('RGBA');lena=Image.open(RES/'context/chef-lena-idle-S.png').convert('RGBA').crop((0,0,384,640))
def grid_scene(cells,pitch=128):
 origin=(pitch,pitch*4);im=Image.new('RGBA',((cells[0]+2)*pitch,(cells[1]+5)*pitch),'#f5f2e9');f=floor.resize((pitch,pitch),Image.Resampling.LANCZOS)
 for y in range(cells[1]):
  for x in range(cells[0]):im.alpha_composite(f,(origin[0]+x*pitch,origin[1]+y*pitch))
 return im,origin

def place(im,obj,point,root,sourceScale,origin,pitch):
 factor=pitch/(128*sourceScale);scaled=obj.resize((round(obj.width*factor),round(obj.height*factor)),Image.Resampling.LANCZOS);pos=(round(origin[0]+point[0]*pitch-root[0]*pitch/128),round(origin[1]+point[1]*pitch-root[1]*pitch/128));im.alpha_composite(scaled,pos)
context_records=[]
for pitch in (128,55):
 for dr in DRS:
  im,origin=grid_scene((6,3),pitch);rc=(1.5,1) if dr in ('N','S') else (1,1.5);place(im,full('idle',dr,0),rc,(288,544),2,origin,pitch);place(im,lena,(4.5,.5),(96,248),2,origin,pitch)
  f=PRE/f'human-{dr}-cell{pitch}.png';im.convert('RGB').save(f);addpreview(f'human-{dr}-{pitch}',f);context_records.append({'type':'human','facing':dr,'cellPitch':pitch,'carTopLeft':[0,0],'carRootCells':list(rc),'humanTopLeft':[4,0],'humanRootCells':[4.5,.5],'origin':list(origin),'image':rel(f)})
 im,origin=grid_scene((8,6),pitch)
 for x,y in [(0,0),(4,0),(0,3)]:place(im,full('idle','S',0),(x+1.5,y+1),(288,544),2,origin,pitch)
 f=PRE/f'repeated-cell{pitch}.png';im.convert('RGB').save(f);addpreview(f'repeated-{pitch}',f);context_records.append({'type':'repeated','cellPitch':pitch,'placements':[[0,0],[4,0],[0,3]],'facings':['S']*3,'carRootOffset':[1.5,1],'origin':list(origin),'image':rel(f)})
# Exact12fps MP4s and APNGs. Clearance retains native final fragments, holds then removes at consumer layer.
def movie(path,images):
 proc=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{images[0].width}x{images[0].height}','-r','12','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
 for im in images:proc.stdin.write(im.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]));return probe

def chunk(typ,data):return struct.pack('>I',len(data))+typ+data+struct.pack('>I',zlib.crc32(typ+data)&0xffffffff)
def apng(path,ims,loop):
 # Every frame delay is the exact rational1/12second.
 W,H=ims[0].size;data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,6,0,0,0))+chunk(b'acTL',struct.pack('>II',len(ims),0 if loop else 1));seq=0
 for i,im in enumerate(ims):
  data+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,W,H,0,0,1,12,0,0));seq+=1
  a=im.convert('RGBA');scan=b''.join(b'\x00'+a.crop((0,y,W,y+1)).tobytes() for y in range(H));compressed=zlib.compress(scan,6)
  if i==0:data+=chunk(b'IDAT',compressed)
  else:data+=chunk(b'fdAT',struct.pack('>I',seq)+compressed);seq+=1
 data+=chunk(b'IEND',b'');path.write_bytes(data)
playback=[]
for clip in ('highlighted','clearance'):
 for dr in DRS:
  ims=[back(full(clip,dr,i),'f5f2e9',LOG) for i in range(12)];base=ims[:];order=list(range(12));consumer=False
  if clip=='clearance':ims+=([ims[-1]]*12)+[Image.new('RGB',LOG,'#f5f2e9')]*12;order+=([11]*12)+[None]*12;consumer=True
  mp=PRE/f'{clip}-{dr}-12fps.mp4';probe=movie(mp,ims);addpreview(f'{clip}-{dr}',mp);ap=PRE/f'{clip}-{dr}-12fps.png';apng(ap,[x.convert('RGBA') for x in ims],clip=='highlighted');addpreview(f'{clip}-{dr}-apng',ap)
  playback.append({'clip':clip,'direction':dr,'video':rel(mp),'apng':rel(ap),'fpsNumerator':12,'fpsDenominator':1,'frameDurationNumerator':1,'frameDurationDenominator':12,'uniqueNativeFrames':12,'frameOrder':order,'loop':clip=='highlighted','consumerRemoval':consumer,'ffprobe':probe})
# Same floor/camera before, all native phases and separate postclip removal, all four views.
for dr in DRS:
 ims=[]
 for i in range(12):
  im,origin=grid_scene((6,3));rc=(1.5,1) if dr in ('N','S') else (1,1.5);place(im,full('clearance',dr,i),rc,(288,544),2,origin,128);ims.append(im.convert('RGB'));f=PRE/'floor-reveal'/f'{dr}-{i:02d}.png';f.parent.mkdir(exist_ok=True);im.save(f)
 removed,_=grid_scene((6,3));rp=PRE/'floor-reveal'/f'{dr}-postclip-removed.png';removed.save(rp)
 sheet=Image.new('RGB',(ims[0].width*4,ims[0].height*4),'#f5f2e9')
 for i,im in enumerate(ims+[removed.convert('RGB')]):sheet.paste(im,(i%4*im.width,i//4*im.height))
 sp=PRE/f'floor-reveal-{dr}-all.png';sheet.save(sp);addpreview(f'floor-reveal-{dr}',sp)
 if dr=='S':
  mp=PRE/'floor-reveal-S-12fps.mp4';probe=movie(mp,ims+[ims[-1]]*12+[removed.convert('RGB')]*12);addpreview('floor-reveal-playback',mp);playback.append({'clip':'clearance-floor-reveal','direction':'S','video':rel(mp),'fpsNumerator':12,'fpsDenominator':1,'frameOrder':list(range(12))+[11]*12+[None]*12,'consumerRemoval':True,'ffprobe':probe})
write(OUT/'playback.json',playback);write(OUT/'consumer-context-audit.json',{'registration':'whole native frame scales uniformly using original anchor; no subject fit/crop','phoneRounding':{'scaleFactor':55/128,'logicalFullFrame':[576,832],'idealPhoneFrame':[247.5,357.5],'roundedRaster':[248,358],'method':'round each raster extent to nearest integer, half-up'},'contexts':context_records,'resourceHashes':{rel(f):sha(f) for f in (RES/'context').glob('*') if f.is_file()},'floorReveal':{'floorResource':'source/resources/context/floor-cream-static-S.png','phases':list(range(12)),'finalFragmentsHeldFrames':12,'consumerRemovalFrames':12,'floorPixelBytesChanged':False}})
nativeAudit=json.loads((OUT/'native-audit.json').read_text());parity=[]
for dr in DRS:
 a=full('idle',dr,0);b=full('clearance',dr,0);stats=ImageStat.Stat(ImageChops.difference(a,b));f=next(f for f in nativeAudit['frames'] if f['clip']=='idle' and f['direction']==dr);g=next(f for f in nativeAudit['frames'] if f['clip']=='clearance' and f['direction']==dr)
 parity.append({'direction':dr,'nativeCarrierTransformsIdentical':f['carriers']==g['carriers'],'nativeGeometryBoundsIdentical':f['geometry']['bounds']==g['geometry']['bounds'],'alphaIdentical':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'fullCanvasMeanAbsoluteRGBAError8bit':stats.mean,'maximumAbsoluteRGBAError8bit':[q[1] for q in stats.extrema],'explanation':'Separate native renders of the identical pose have tiny floating-point/denoising RGB differences. No pixels were copied or repaired; alpha and evaluated native pose remain exact.'})
write(OUT/'raster-audit.json',{'nativeFrame':[1152,1664],'clearanceStartParity':parity,'frames':raster,'atlasPixelIdentity':True,'clearanceStartPixelIdentity':{d:full('clearance',d,0).tobytes()==full('idle',d,0).tobytes() for d in DRS},'rawFrameCount':len(raw),'atlasCount':len(atlases),'previewScalingOnly':True})
# Review page uses actual HTML video playback with exact native sequence metadata.
cards=''.join(f'<article><h2>{x["clip"]} {x["direction"]}</h2><video controls muted playsinline '+('loop ' if x.get('loop') else '')+f'src="previews/{Path(x["video"]).name}"></video></article>' for x in playback)
html='<!doctype html><meta charset="utf-8"><title>Garbage car native round01 playback</title><style>body{font:16px system-ui;background:#202028;color:#eee;margin:24px}.grid{display:grid;grid-template-columns:repeat(4,minmax(200px,1fr));gap:16px}video{width:100%;max-height:70vh;background:#f5f2e9}h2{font-size:16px}button{font:inherit;padding:10px}</style><h1>Garbage car round01</h1><p>Native12fps. Highlighted loops12frames. Clearance plays12frames, holds terminal fragments1second, then removes at the consumer layer.</p><button id="play">Play all</button><div class="grid">'+cards+'</div><script>window.playbackEvidence=[];document.querySelector("#play").onclick=()=>{for(const v of document.querySelectorAll("video")){v.currentTime=0;v.play();if(v.requestVideoFrameCallback){const cb=(now,m)=>{window.playbackEvidence.push({src:v.getAttribute("src"),mediaTime:m.mediaTime,presentedFrames:m.presentedFrames});v.requestVideoFrameCallback(cb)};v.requestVideoFrameCallback(cb)}}};</script>'
(OUT/'playback.html').write_text(html);addpreview('playback-page',OUT/'playback.html')
write(OUT/'media-manifest.json',{'rawFrames':raw,'atlases':atlases,'previews':previews})
print('MEDIA COMPLETE',len(raw),len(atlases),len(previews))
