"""Whole-canvas publication, atlases and honest inspection sheets. Bundled Pillow."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json,math,shutil
H=Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-01';P=O/'previews';P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def framed(im,bg):
 b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
audit=json.loads((O/'native-audit.json').read_text());raw=[];native=[];atlas=[];closure=[]
for r in audit['records']:
 p=E/r['path'];im=Image.open(p).convert('RGBA')
 assert im.size==(768,1408)
 if r['closureOnly']:continue
 q=O/'frames'/r['clip']/r['direction']/f"{r['index']:03d}.png";q.parent.mkdir(parents=True,exist_ok=True);im.resize((384,704),Image.Resampling.BOX).save(q)
 raw.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'path':str(q.relative_to(E)),'size':[384,704],'sha256':sha(q)})
 native.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'path':r['path'],'size':[768,1408],'sha256':sha(p)})
for clip,n in [('idle',1),('active',12)]:
 for d in 'NESW':
  cols,rows=(1,1) if n==1 else (6,2);a=Image.new('RGBA',(384*cols,704*rows));rects=[]
  for i in range(n):
   im=Image.open(O/f'frames/{clip}/{d}/{i:03d}.png').convert('RGBA');x=i%cols*384;y=i//cols*704;a.paste(im,(x,y));rects.append([x,y,384,704])
  q=O/f'atlases/{clip}-{d}.png';q.parent.mkdir(exist_ok=True);a.save(q)
  atlas.append({'clip':clip,'direction':d,'path':str(q.relative_to(E)),'sha256':sha(q),'columns':cols,'rows':rows,'size':list(a.size),'rects':rects,'fps':12,'loop':clip=='active','frameOrder':list(range(n))})
for d in 'NESW':
 a=Image.open(O/f'native/active/{d}/000.png').convert('RGBA');b=Image.open(O/f'native/active/{d}/closure-013.png').convert('RGBA')
 closure.append({'direction':d,'nativeRGBAEqual':a.tobytes()==b.tobytes(),'publishedRGBAEqual':a.resize((384,704),Image.Resampling.BOX).tobytes()==b.resize((384,704),Image.Resampling.BOX).tobytes(),'nativeFrame1':f'candidates/round-01/native/active/{d}/000.png','nativeFrame13':f'candidates/round-01/native/active/{d}/closure-013.png','frame13ExcludedFromAtlas':True})
 # Logical sheets retain complete authored frames, never fit alpha bounds.
 sheet=Image.new('RGB',(192*6,352*2),'#9da9ae');frames=[]
 for i in range(12):
  im=Image.open(O/f'frames/active/{d}/{i:03d}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX)
  sheet.paste(im,(i%6*192,i//6*352),im);ImageDraw.Draw(sheet).text((i%6*192+6,i//6*352+6),f'{d} {i+1}/12',fill='#152d38');frames.append(framed(im,'#9da9ae'))
 sheet.save(P/f'active-phase-sheet-{d}.png')
 frames[0].save(P/f'active-{d}.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,loop=0,lossless=True)
for bg,name in [('#eef2f3','light'),('#9da9ae','gray'),('#162833','dark')]:
 for scale in [1,2]:
  w,h=192*scale,352*scale;im=Image.new('RGB',(w*4,h),bg)
  for i,d in enumerate('NESW'):
   a=Image.open(O/f'frames/idle/{d}/000.png').convert('RGBA').resize((w,h),Image.Resampling.BOX);im.paste(a,(i*w,0),a);ImageDraw.Draw(im).text((i*w+8,8),d,fill='#11252c' if name!='dark' else '#eef5f6')
  im.save(P/f'idle-all4-{name}-{scale}x.png')
allmotion=[]
for i in range(12):
 sheet=Image.new('RGB',(768,352),'#9da9ae')
 for j,d in enumerate('NESW'):
  im=Image.open(O/f'frames/active/{d}/{i:03d}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);sheet.paste(im,(j*192,0),im);ImageDraw.Draw(sheet).text((j*192+6,6),f'{d} · {i+1}/12',fill='#17323e')
 allmotion.append(sheet)
allmotion[0].save(P/'all4-logical-playback.webp',save_all=True,append_images=allmotion[1:],duration=[83,83,84]*4,loop=0,lossless=True)
# Repeated independent standalone sprites at exact logical registration.
repeated=Image.new('RGB',(768,704),'#d6e4e5')
for row in range(2):
 for j,d in enumerate('NESW'):
  im=Image.open(O/f'frames/idle/{d}/000.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);repeated.paste(im,(j*192,row*352),im)
repeated.save(P/'repeated.png')
settings=audit['settings'];camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':2,'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedFrame':[384,704],'fps':12,'camera':{**settings['camera'],'pixelAspect':settings['pixelAspect']},'calibration':{'root':[v/2 for v in settings['calibration']['root']],'unitX':[(v-r)/2 for v,r in zip(settings['calibration']['unitX'],settings['calibration']['root'])],'unitDepth':[(r-v)/2 for v,r in zip(settings['calibration']['unitY'],settings['calibration']['root'])],'unitHeight':[(v-r)/2 for v,r in zip(settings['calibration']['unitZ'],settings['calibration']['root'])]},'nativeCalibration':settings['calibration'],'publication':'Complete native4x768x1408 frame BOX to published2x384x704; no fitting/cropping/warping/alpha repair.','nativeValidation':'candidates/round-01/native-audit.json'}
asset=json.loads((E/'inputs/source-assetRecord.json').read_text());asset.update(scale=2,artStyle={'revision':'warm-soft-native-refinement','nativeRecipe':'source/round-01.py','lighting':'Symmetric broad overhead+four equal cardinal fills; transparent without ground geometry','publishedSampling':'whole-canvas BOX4x->2x'},physicalBoundsQualification='Nominal1x1/.55 metadata preserved; actual evaluated bounds recorded separately.')
rig={'assetId':'sub-collector-inlet','fps':12,'groundRootObject':'collector__root','footprint':[1,1],'height':.55,'clips':{'idle':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'pose':'neutral'},'active':{'frames':12,'fps':12,'loop':True,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13,'mechanics':'Native mouth sleeve/dark throat scaleZ pulse plus connected guard cage rotationX rocking. Three native owners, six saved actions; no new effect or mechanic.'}},'actions':audit['actions'],'source':'source/round-01.blend','neutralAdoption':'CanonicalS idle nativeframe1 at frozen positive uniform mount only; activeframe1 is not neutral.'}
for n,d in [('camera.json',camera),('assetRecord.json',asset),('rig.json',rig),('native-camera.json',settings),('publication-audit.json',{'rawFrames':raw,'nativeRawFrames':native,'atlases':atlas,'closure':closure,'sampling':'Pillow whole-canvas BOX only','runtimeCellCount':len(raw),'atlasCount':len(atlas),'fps':12,'webpPlayback':'12 frames per1000ms,83/83/84msquantization; actual consumer HTML uses exact floor(seconds*12).','allNativeFramesRGBAClosed':all(c['nativeRGBAEqual'] for c in closure)})]:write(O/n,d)
print(json.dumps({'runtimeCells':len(raw),'atlases':len(atlas),'closure':closure},indent=2))
