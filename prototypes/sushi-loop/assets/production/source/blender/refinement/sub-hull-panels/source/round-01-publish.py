"""Whole-frame native4x→published2x BOX publication and labeled evidence."""
from pathlib import Path
import json,hashlib,copy,math
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;OUT=EXP/'candidates/round-01';DIRECTIONS=['N','E','S','W']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return str(p.relative_to(EXP))
def frame(clip,d,i):return Image.open(OUT/'frames'/f'{clip}-{d}'/f'{i:03}.png').convert('RGBA')
def panel(image,bg):
    p=Image.new('RGBA',image.size,bg);p.alpha_composite(image);return p.convert('RGB')
def save_loop(images,p):
    # Each 3-frame group totals250ms; complete12frame runtime loop totals1000ms.
    durations=[83,83,84]*4 if len(images)==12 else [42,41,42,42,41,42]*4
    images[0].save(p,save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=0,blend=0)
native=json.loads((OUT/'native-render-manifest.json').read_text())['nativeCaptures'];published=[];atlases=[];natlases=[]
for r in native:
    p=EXP/r['path'];im=Image.open(p).convert('RGBA');assert im.size==(768,1408)
    q=OUT/'frames'/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03}.png';q.parent.mkdir(parents=True,exist_ok=True);im.resize((384,704),Image.Resampling.BOX).save(q)
    published.append({k:r[k] for k in ['clip','direction','index']}|{'path':rel(q),'size':[384,704],'sha256':sha(q)})
for clip,count,columns,rows,loop in [('idle',1,1,1,False),('active',12,6,2,True)]:
 for d in DIRECTIONS:
  for scale,folder,dest in [(2,'frames',atlases),(4,'native-frames',natlases)]:
   w,h=192*scale,352*scale;atlas=Image.new('RGBA',(w*columns,h*rows));rects=[]
   for i in range(count):
    r=[i%columns*w,i//columns*h,w,h];im=Image.open(OUT/folder/f'{clip}-{d}'/f'{i:03}.png');atlas.paste(im,(r[0],r[1]));rects.append(r)
   p=OUT/('atlases' if scale==2 else 'native-atlases')/f'{clip}-{d}.png';p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p)
   dest.append({'clip':clip,'direction':d,'path':rel(p),'sha256':sha(p),'columns':columns,'rows':rows,'size':list(atlas.size),'rects':rects,'fps':12,'loop':loop,'frameOrder':list(range(count)),'frames':count})
dump(OUT/'publication-manifest.json',{'sampling':'Entire unmodified native RGBA frame BOX resized768x1408→384x704. Lossless placement in original atlas layout. No alpha edits, fitting or sharpening.','nativeRawFrames':native,'rawFrames':published,'atlases':atlases,'nativeAtlases':natlases})
previews=OUT/'previews';previews.mkdir(exist_ok=True)
backgrounds={'light':'#F5F1E8','gray':'#A8ADAE','dark':'#253038'}
for bg,color in backgrounds.items():
 sheet=Image.new('RGB',(192*4,352+32),color);dr=ImageDraw.Draw(sheet)
 for n,d in enumerate(DIRECTIONS):
  im=frame('idle',d,0).resize((192,352),Image.Resampling.BOX);sheet.paste(panel(im,color),(n*192,32));dr.text((n*192+8,8),f'{d} · logical192×352',fill='#080D12' if bg!='dark' else '#FFFFFF')
 sheet.save(previews/f'four-view-logical-{bg}.png')
 mounted=Image.new('RGB',(320*4,416),color);dr=ImageDraw.Draw(mounted)
 for n,d in enumerate(DIRECTIONS):
  im=Image.open(OUT/'mounted'/f'neutral-{d}.png').convert('RGBA').resize((320,384),Image.Resampling.BOX);mounted.paste(panel(im,color),(n*320,32));dr.text((n*320+6,8),f'{d} · frozen body / provisional equipment',fill='#080D12' if bg!='dark' else '#FFFFFF')
 mounted.save(previews/f'mounted-four-view-{bg}.png')
 allphases=Image.new('RGB',(192*12,352*4+32),color);dr=ImageDraw.Draw(allphases)
 for row,d in enumerate(DIRECTIONS):
  for i in range(12):
   allphases.paste(panel(frame('active',d,i).resize((192,352),Image.Resampling.BOX),color),(i*192,32+row*352));dr.text((i*192+6,34+row*352),f'{d} / {i+1:02}',fill='#080D12' if bg!='dark' else '#FFFFFF')
 dr.text((8,8),'All48 active cells · same full logical192×352 registration · native12fps/1second',fill='#080D12' if bg!='dark' else '#FFFFFF');allphases.save(previews/f'active-all48-{bg}.png')
for d in DIRECTIONS:
 images=[frame('active',d,i) for i in range(12)];save_loop(images,previews/f'active-{d}.apng')
 dense=[]
 for i in range(12):
  dense.append(images[i]);dense.append(Image.open(OUT/'motion-evidence'/f'{d}-{i+1.5:04.1f}.png').convert('RGBA').resize((384,704),Image.Resampling.BOX))
 save_loop(dense,previews/f'active-halfphase-{d}.apng')
 # Byte compare closing native wholeframe13 with runtime nativeframe1.
 im1=Image.open(OUT/'native-frames'/f'active-{d}'/'000.png').convert('RGBA');im13=Image.open(OUT/'motion-evidence'/f'{d}-13.0.png').convert('RGBA')
 assert im1.tobytes()==im13.tobytes(),f'{d} frame13 differs'
all4=[]
for i in range(12):
 sheet=Image.new('RGBA',(384*4,704))
 for n,d in enumerate(DIRECTIONS):sheet.paste(frame('active',d,i),(n*384,0))
 all4.append(sheet)
save_loop(all4,previews/'active-all4.apng')
repeat=Image.new('RGBA',(448,608))
for row in range(3):
 for col in range(3):
  im=frame('idle','S',0).resize((192,352),Image.Resampling.BOX);repeat.alpha_composite(im,(col*128,row*128))
panel(repeat,backgrounds['gray']).save(previews/'repeated.png')
# Browser harness uses the exact snapshotted real renderer/registration and real
# input descriptors. Override only candidate atlas locations and native main fixture.
objects=json.loads((HERE/'resources/consumer/selected-objects.json').read_text())
for obj in objects:
 if obj['id']=='sub-hull-panels':
  for c in obj['clips']:
   for d,e in c['directions'].items():e['image']=f'../candidates/round-01/atlases/{c["id"]}-{d}.png'
 elif obj['id']=='submarine-yellow':
  obj['clips']=[{'id':'native-mounted-neutral','frames':1,'fps':12,'loop':False,'static':True,'directions':{d:{'image':f'../candidates/round-01/mounted/neutral-{d}.png','rects':[[0,0,640,768]],'columns':1,'rows':1,'atlasSize':[640,768]} for d in DIRECTIONS}}]
 else:
  for c in obj['clips']:
   for e in c['directions'].values():e['image']='./resources/consumer/'+e['image']
dump(HERE/'consumer-objects.json',objects)
dump(OUT/'publication-validation.json',{'nativeRuntimeCells':len(native),'publishedRuntimeCells':len(published),'publishedAtlases':len(atlases),'nativeAtlases':len(natlases),'frame13NativeWholeframePixelsIdenticalToFrame1All4':True,'everyPublishedPixelDerivedByWholeFrameBOX':True,'atlasCellsEqualPublishedWholeframes':True,'noRuntimeFrame13':True,'activeDistinctPixelFrames':{d:len({sha(EXP/r['path']) for r in published if r['direction']==d and r['clip']=='active'}) for d in DIRECTIONS}})
print('PUBLISHED',len(published),'ATLAS',len(atlases))
