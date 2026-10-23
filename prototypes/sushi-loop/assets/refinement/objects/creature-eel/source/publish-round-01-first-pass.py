"""Whole-canvas publication and lossless diagnostic sheets; no image repair."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,math
from PIL import Image,ImageDraw
import numpy as np
P=Path(__file__).resolve().parent;E=P.parent;C=E/'candidates/round-01';PRE=E/'reviews/preparation-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def savej(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return str(p.relative_to(E))
cat=json.loads((PRE/'resources/inputs/catalog-object.json').read_text());measure=json.loads((C/'native-measurements.json').read_text())
capture=json.loads((C/'capture-records.json').read_text());assert len(capture['records'])==542
assert capture['projectSHA256']==sha(P/'round-01.blend')
raw=[];native=[];atlases=[];coverage=[];alpha=[]
for clip in cat['clips']:
 for f in ['N','E','S','W']:
  frames=[];nat=[]
  for i in range(12):
   n=C/'native'/clip['id']/f/f'{i:03}.png';im=Image.open(n).convert('RGBA');assert im.size==(1792,2048)
   out=C/'published/frames'/clip['id']/f/f'{i:03}.png';out.parent.mkdir(parents=True,exist_ok=True)
   pub=im.resize((896,1024),Image.Resampling.LANCZOS);pub.save(out,compress_level=9)
   a=np.array(im.getchannel('A'));bb=im.getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<1792 and bb[3]<2048
   alpha.append({'path':rel(n),'alphaBBox':bb,'edgeAlphaMax':int(max(a[0].max(),a[-1].max(),a[:,0].max(),a[:,-1].max())),'opaquePixels':int((a==255).sum()),'visiblePixels':int((a>0).sum())})
   raw.append({'clip':clip['id'],'direction':f,'index':i,'path':rel(out),'dimensions':[896,1024],'sha256':sha(out)})
   native.append({'clip':clip['id'],'direction':f,'index':i,'path':rel(n),'dimensions':[1792,2048],'sha256':sha(n)})
   frames.append(pub);nat.append(im)
  atlas=Image.new('RGBA',(5376,2048))
  for i,im in enumerate(frames):atlas.paste(im,((i%6)*896,(i//6)*1024))
  out=C/'published'/clip['directions'][f]['image'];out.parent.mkdir(parents=True,exist_ok=True);atlas.save(out,compress_level=9)
  for i,im in enumerate(frames):assert atlas.crop(tuple([*(np.array(clip['directions'][f]['rects'][i][:2])),*(np.array(clip['directions'][f]['rects'][i][:2])+[896,1024])])).tobytes()==im.tobytes()
  atlases.append({'clip':clip['id'],'direction':f,'path':rel(out),'dimensions':[5376,2048],'columns':6,'rows':2,'frames':12,'fps':12,'loop':clip['loop'],'rects':clip['directions'][f]['rects'],'sha256':sha(out)})
  # Exact native RGBA pixels within ONE fixed union crop per clip/facing; no resampling.
  boxes=[im.getbbox() for im in nat];box=(max(0,min(b[0] for b in boxes)-12),max(0,min(b[1] for b in boxes)-12),min(1792,max(b[2] for b in boxes)+12),min(2048,max(b[3] for b in boxes)+12))
  w,h=box[2]-box[0],box[3]-box[1];label=28
  sheet=Image.new('RGBA',(w*3,(h+label)*4));draw=ImageDraw.Draw(sheet)
  cells=[]
  for i,im in enumerate(nat):
   x=(i%3)*w;y=(i//3)*(h+label)
   draw.rectangle((x,y,x+w,y+label),fill='#535963');draw.text((x+8,y+6),f'{clip["id"]} {f} phase {i+1:02}',fill='white')
   sheet.paste(im.crop(box),(x,y+label))
   cells.append({'path':rel(C/'native'/clip['id']/f/f'{i:03}.png'),'sha256':sha(C/'native'/clip['id']/f/f'{i:03}.png'),'sourceBox':list(box),'sheetBox':[x,y+label,x+w,y+label+h],'scale':1,'pixelCopy':'Exact native RGBA crop, complete useful alpha bounds included.'})
  out=C/'sheets'/f'{clip["id"]}-{f}-native.png';out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,compress_level=9)
  coverage.append({'sheet':rel(out),'sha256':sha(out),'dimensions':list(sheet.size),'cells':cells})
  # Small complete registration overview per animation, useful for timing/shape comparison.
  overview=Image.new('RGBA',(448*4,(512+24)*3),'#8e9196');d=ImageDraw.Draw(overview)
  for i,im in enumerate(frames):
   x=(i%4)*448;y=(i//4)*536;overview.alpha_composite(im.resize((448,512),Image.Resampling.LANCZOS),(x,y+24));d.text((x+8,y+5),f'{clip["id"]} {f} {i+1:02}',fill='white')
  out=C/'sheets'/f'{clip["id"]}-{f}-logical.png';overview.save(out,compress_level=9)

# Four registered views, kept on common complete canvases at logical scale.
four=Image.new('RGBA',(1792,552),'#8e9196');d=ImageDraw.Draw(four)
for j,f in enumerate(['N','E','S','W']):
 im=Image.open(C/'published/frames/normal'/f/'000.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS)
 four.alpha_composite(im,(j*448,30));d.text((j*448+8,8),f,fill='white')
four.save(C/'four-view-sheet.png',compress_level=9)
# Bind extrema and enlarged face/fin pixels without modifying any export.
extrema=[]
for axis in range(3):
 rows=measure['views']['S']
 extrema.extend([min(rows,key=lambda r:r['canonicalSEvaluatedBounds'][0][axis]),max(rows,key=lambda r:r['canonicalSEvaluatedBounds'][1][axis])])
seen=set();details=[]
for r in extrema+[next(r for r in measure['views'][f] if r['clip']=='normal' and r['frame']==1) for f in ['N','E','S','W']]:
 key=(r['clip'],r['direction'],r['frame'])
 if key in seen:continue
 seen.add(key);n=C/'native'/key[0]/key[1]/f'{key[2]-1:03}.png';im=Image.open(n).convert('RGBA');bb=im.getbbox()
 box=(max(0,bb[0]-16),max(0,bb[1]-16),min(1792,bb[2]+16),min(2048,bb[3]+16))
 out=C/'details'/f'{key[0]}-{key[1]}-{key[2]:02}.png';out.parent.mkdir(exist_ok=True);im.crop(box).save(out,compress_level=9)
 details.append({'path':rel(out),'sha256':sha(out),'sourcePath':rel(n),'sourceSHA256':sha(n),'sourceBox':list(box),'scale':1,'reason':'Allphase axis extremum or four-facing facial/fin detail.'})

resources=C/'resources';(resources/'consumer').mkdir(parents=True,exist_ok=True)
for name in ['sprite-layout.js','world-sprite-raster.js']:
 shutil.copyfile(PRE/'resources/consumer'/name,resources/'consumer'/name)
for name in ['source-camera.json','source-assetRecord.json','source-rig.json','catalog-object.json']:
 dest=resources/'original-records'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PRE/'resources/inputs'/name,dest)
camera=json.loads((C/'native-camera.json').read_text());pubcam=json.loads(json.dumps(camera));pubcam['captureScale']=2;pubcam['nativeCaptureScale']=4;pubcam['nativeFrame']=[1792,2048];pubcam['publishedFrame']=[896,1024]
pubcam['calibration']={k:[x/2 for x in v] for k,v in camera['calibration'].items()};pubcam['publication']='Whole1792x2048canvas LANCZOS896x1024; no occupied-bound fitting.'
asset=json.loads((PRE/'resources/inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['nativeCaptureScale']=4;asset['nativeFrame']=[1792,2048];asset['publishedFrame']=[896,1024];asset['artStyle']={'revision':'warm-soft-eel-round01','nativeLight':'160Woverhead+4x65Wcardinal+20Wunderside, world.18; invariant across facings','materials':'rounded native blue/yellow Principled; blue lower surfaces readable'}
rig=json.loads((PRE/'resources/inputs/source-rig.json').read_text());rig['source']='source/build-round-01.py';rig['status']='round01-native-repaired-needs-independent-review';rig['nativeRotationModes']={f'spine_{i}':'XYZ' for i in range(7)};rig['round01ActionAdjustment']='Caught arm rotation_euler X key values multiplied.80; all IDs/keys/order/holds retained.';rig['sourceFiles']={'build-round-01.py':sha(P/'build-round-01.py'),'round-01.blend':sha(P/'round-01.blend')}
savej(C/'nativeRecords/camera.json',pubcam);savej(C/'nativeRecords/assetRecord.json',asset);savej(C/'nativeRecords/rig.json',rig);savej(C/'nativeRecords/catalog-object.json',cat)
savej(C/'publication.json',{'asset':'creature-eel','projectSHA256':sha(P/'round-01.blend'),'method':'Pillow wholecanvas LANCZOS1792x2048to896x1024, no RGB/alpha repair; exact original6x2cells.','pillowVersion':Image.__version__,'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'alphaAudit':alpha})
savej(C/'visual-coverage-map.json',{'asset':'creature-eel','all528NativeUsefulPixelCoverage':coverage,'details':details,'fourViewSheet':{'path':rel(C/'four-view-sheet.png'),'sha256':sha(C/'four-view-sheet.png')},'limits':'Sheets are diagnostic crops/copies only; native and published exports retain full frozen canvases. Judge must inspect actual pixels; no selfapproval.'})
print('PUBLISHED',len(raw),'native',len(native),'atlases',len(atlases),'sheets',len(coverage),flush=True)
