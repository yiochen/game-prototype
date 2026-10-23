import sys,pathlib
sys.dont_write_bytecode=True
out=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(out/'resources/python'))
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,math
ex=out.parents[1];c=ex/'candidates/round-01';pub=json.loads((c/'publication-manifest.json').read_text());opened=lambda p:Image.open(p).convert('RGBA');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];native_index={(r['clip'],r['direction'],r['index']):r for r in pub['nativeRawFrames']};runtime_index={(r['clip'],r['direction'],r['index']):r for r in pub['rawFrames']}
for key,r in runtime_index.items():
 raw=opened(ex/r['path']);native=opened(ex/native_index[key]['path']);assert native.size==(768,1408) and raw.size==(384,704);assert native.resize(raw.size,Image.Resampling.BOX).tobytes()==raw.tobytes();bbox=raw.getchannel('A').getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<704
 checks.append({'clip':key[0],'direction':key[1],'index':key[2],'wholeBOXExact':True,'alphaBounds':bbox,'nativeSHA256':sha(ex/native_index[key]['path']),'publishedSHA256':sha(ex/r['path'])})
for typ,index in [('atlases',runtime_index),('nativeAtlases',native_index)]:
 for r in pub[typ]:
  im=opened(ex/r['path']);assert tuple(r['size'])==im.size
  for i,rect in enumerate(r['rects']):
   x,y,w,h=rect;assert im.crop((x,y,x+w,y+h)).tobytes()==opened(ex/index[(r['clip'],r['direction'],i)]['path']).tobytes()
  assert r['frames']==(1 if r['clip']=='idle' else 12)
# Fixed native crop: same window across all views/frames, no fitting.
crop=(80,600,688,1320);sheet=Image.new('RGBA',(1216,1480),'#A8ADAE');draw=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
 im=opened(ex/native_index[('idle',d,0)]['path']).crop(crop);x=(i%2)*608;y=(i//2)*740+20;sheet.alpha_composite(im,(x,y));draw.text((x+8,y-16),f'{d} native4x fixed crop',fill='#202020')
sheet.save(out/'native-idle-detail.png');sheets=[{'path':'native-idle-detail.png','sourceFrames':[native_index[('idle',d,0)]['path'] for d in 'NESW'],'fixedNativeCrop':crop}]
for d in 'NESW':
 sheet=Image.new('RGBA',(1824,760),'#A8ADAE');draw=ImageDraw.Draw(sheet)
 for i in range(12):
  im=opened(ex/native_index[('active',d,i)]['path']).crop(crop).resize((304,360),Image.Resampling.BOX);x=i%6*304;y=i//6*380+20;sheet.alpha_composite(im,(x,y));draw.text((x+8,y-16),f'{d} active {i+1}/12',fill='#202020')
 path=f'active-{d}-detail-all12.png';sheet.save(out/path);sheets.append({'path':path,'sourceFrames':[native_index[('active',d,i)]['path'] for i in range(12)],'fixedNativeCrop':crop,'cropDisplayScale':.5})
# Whole screenshot sheets, each screenshot retained in entirety at uniform thumbnail scale.
consumer=json.loads((c/'consumer/check.json').read_text());screenshot_records=[]
for view in consumer['views']:
 states=view['states'];thumb_width=220 if view['name']=='phone' else 240
 for start in [0,7]:
  group=states[start:start+7];thumbs=[]
  for r in group:
   p=ex/r['path'];assert sha(p)==r['sha256'];im=opened(p);size=(thumb_width,round(im.height*thumb_width/im.width));thumbs.append((r,im.resize(size,Image.Resampling.LANCZOS)))
  height=max(im.height for r,im in thumbs);sheet=Image.new('RGBA',(thumb_width*4,(height+22)*2),'#888888');draw=ImageDraw.Draw(sheet)
  for i,(r,im) in enumerate(thumbs):
   x=i%4*thumb_width;y=i//4*(height+22)+22;sheet.alpha_composite(im,(x,y));draw.text((x+4,y-18),f'{view["name"]} {view["background"]} {r["clip"]}{r["frameIndex"]+1}',fill='white')
  path=f'consumer-{view["name"]}-{view["background"]}-part-{start//7+1}.png';sheet.save(out/path);sheets.append({'path':path,'wholeScreenshots':[r for r,im in thumbs],'thumbnailWidth':thumb_width,'crop':False})
 screenshot_records+=states
loops=[]
for d in 'NESW':
 p=c/'previews'/f'active-{d}.apng';im=Image.open(p);assert im.n_frames==12
 durations=[]
 for i in range(12):im.seek(i);durations.append(im.info.get('duration'))
 loops.append({'path':str(p.relative_to(ex)),'sha256':sha(p),'frames':im.n_frames,'durationsMs':durations,'totalMs':sum(durations)})
(out/'pixel-audit.json').write_text(json.dumps({'publishedFrameChecks':checks,'all52NativeToPublishedWholeBOXExact':True,'all16NativeAndPublishedAtlasesExact':True,'allPublishedCellsInsideCanvas':True,'publishedActiveUniquePixels':{d:len({opened(ex/runtime_index[('active',d,i)]['path']).tobytes() for i in range(12)}) for d in 'NESW'},'loops':loops,'wholeScreenshotCount':len(screenshot_records),'sheets':sheets},indent=2))
print('PIXEL_AUDIT',len(checks),len(screenshot_records),len(sheets))
