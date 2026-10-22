from PIL import Image, ImageDraw
from pathlib import Path
import json, hashlib
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OBJ=BASE/'prototypes/sushi-loop/assets/refinement/objects/garbage-sofa';OUT=OBJ/'reviews'
cat=json.loads((OBJ/'inputs/catalog-object.json').read_text())
records=[];idles=[];playbacks={}
for clip in cat['clips']:
 for direction,desc in clip['directions'].items():
  p=BASE/'prototypes/sushi-loop/assets/production'/desc['image'];atlas=Image.open(p).convert('RGBA')
  frames=[]
  for index,rect in enumerate(desc['rects']):
   x,y,w,h=rect;im=atlas.crop((x,y,x+w,y+h));a=im.getchannel('A');hist=a.histogram()
   records.append({'clip':clip['id'],'direction':direction,'index':index,'atlas':str(p),'atlasSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'rect':rect,'rgbaSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'alphaBBox':a.getbbox(),'alphaArea':sum(hist[1:]),'alphaSum':sum(i*n for i,n in enumerate(hist)),'opaquePixels':hist[255],'partialAlphaPixels':sum(hist[1:255]),'rgbExtrema':im.getextrema()[:3]})
   frames.append(im)
  thumb=(224,288);header=24
  sheet=Image.new('RGB',(6*224,2*(288+header)),(128,128,128));d=ImageDraw.Draw(sheet)
  for i,im in enumerate(frames):
   im=im.resize(thumb,Image.Resampling.LANCZOS);x=(i%6)*224;y=(i//6)*(288+header)
   d.text((x+8,y+4),f'{clip["id"]}-{direction} / {i}',fill='white');sheet.paste(im,(x,y+header),im)
  if clip['id']=='idle':idles.append((direction,frames[0]))
  else:
   sheet.save(OUT/f'original-{clip["id"]}-{direction}-all-phases-phone.png')
   # 12 Hz HTML playback uses decoded, original full atlas and exact registered crop.
   playbacks[clip['id']+'-'+direction]={'url':str(p),'columns':desc['columns'],'frames':clip['frames'],'loop':clip['loop']}
idle_sheet=Image.new('RGB',(448*4,600),(128,128,128));d=ImageDraw.Draw(idle_sheet)
for i,(direction,im) in enumerate(idles):
 d.text((448*i+8,4),'idle-'+direction+' logical 448x576',fill='white');im=im.resize((448,576),Image.Resampling.LANCZOS);idle_sheet.paste(im,(448*i,24),im)
idle_sheet.save(OUT/'original-idle-four-facing-logical.png')
for name in ['original','target']:
 p=OBJ/'inputs'/f'{name}.png';im=Image.open(p).convert('RGBA')
 records.append({'input':name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size),'alphaBBox':im.getchannel('A').getbbox()})
 # Evidence only: backgrounds show source alpha and target halo, preserve whole framing.
 im.thumbnail((448,576),Image.Resampling.LANCZOS)
 sheet=Image.new('RGB',(im.width*3,im.height+24));d=ImageDraw.Draw(sheet)
 for i,(color,label) in enumerate([((238,238,238),'light'),((128,128,128),'gray'),((32,32,32),'dark')]):
  tile=Image.new('RGBA',im.size,color+(255,));tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(i*im.width,24));d.text((i*im.width+8,4),name+' / '+label,fill='white')
 sheet.save(OUT/f'{name}-three-backgrounds.png')
(OUT/'raster-audit-raw.json').write_text(json.dumps(records,indent=2)+'\n')
# Copy no source images: local evidence player references the frozen original atlas bytes.
html='''<!doctype html><meta charset="utf-8"><title>Original sofa temporal evidence</title><style>body{background:#777;color:#fff;font:14px system-ui}main{display:grid;grid-template-columns:repeat(4,224px);gap:8px}canvas{width:224px;height:288px;background:#aaa}button{font:inherit}</style><button id="restart">Replay all at 12 Hz</button><p>Original unedited atlases; registered full-frame crops. Highlighted loops; clearance holds final frame after 1 second.</p><main></main><script>const defs=DEFS;const entries=[];for(const [id,d]of Object.entries(defs)){const box=document.createElement('section');box.innerHTML='<b>'+id+'</b><br>';const canvas=document.createElement('canvas');canvas.width=896;canvas.height=1152;box.append(canvas);document.querySelector('main').append(box);const image=new Image();image.src='file://'+d.url;entries.push({id,d,canvas,image});}let start=performance.now();document.querySelector('button').onclick=()=>start=performance.now();function tick(now){for(const e of entries){let f=Math.floor((now-start)*12/1000);f=e.d.loop?f%e.d.frames:Math.min(f,e.d.frames-1);const c=e.canvas.getContext('2d');c.clearRect(0,0,896,1152);if(e.image.complete)c.drawImage(e.image,(f%e.d.columns)*896,Math.floor(f/e.d.columns)*1152,896,1152,0,0,896,1152);}requestAnimationFrame(tick)}requestAnimationFrame(tick);</script>'''.replace('DEFS',json.dumps(playbacks))
(OUT/'original-temporal-player.html').write_text(html)
print('Raster audit:',len([r for r in records if 'clip'in r]),'phases')
