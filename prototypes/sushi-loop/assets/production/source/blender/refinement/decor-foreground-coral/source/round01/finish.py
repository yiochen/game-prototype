"""One exact full-frame publication reduction and atlas packing, metadata and visual previews.
Run with bundled Pillow Python after saved-source capture and browser capture.
"""
import json,hashlib,math,copy,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;O=S.parent.parent;C=O/'candidates/round-01';R=S/'resources'
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(O).as_posix()
cat=json.loads((R/'catalog-object.json').read_text())
def publish():
 records=[];atlases=[];reductions=[]
 for clip in cat['clips']:
  for d,entry in clip['directions'].items():
   atlas=Image.new('RGBA',tuple(entry['atlasSize']))
   for i,rect in enumerate(entry['rects']):
    raw=C/'native'/clip['id']/d/f'{i:03}.png';im=Image.open(raw).convert('RGBA');assert im.size==(768,1536)
    out=C/'frames'/clip['id']/d/f'{i:03}.png';out.parent.mkdir(parents=True,exist_ok=True);pub=im.resize((384,768),Image.Resampling.LANCZOS);pub.save(out)
    x,y,w,h=rect;assert pub.size==(w,h);atlas.paste(pub,(x,y));record={'clip':clip['id'],'direction':d,'index':i,'path':rel(out),'sha256':sha(out)};records.append(record)
    reductions.append({'native':rel(raw),'nativeSHA256':sha(raw),'published':rel(out),'publishedSHA256':sha(out),'nativeSize':list(im.size),'publishedSize':list(pub.size),'method':'Whole-frame Pillow LANCZOS exactly once; no alpha/RGB edit','alphaBBox':pub.getchannel('A').getbbox(),'nativeAlphaBBox':im.getchannel('A').getbbox(),'edgeAlphaMax':max(max(pub.getchannel('A').crop(b).getextrema()) for b in [(0,0,384,1),(0,767,384,768),(0,0,1,768),(383,0,384,768)])})
   p=C/'atlases'/f'{clip["id"]}-{d}.png';p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p);atlases.append({'clip':clip['id'],'direction':d,'path':rel(p),'sha256':sha(p),'columns':entry['columns'],'rows':entry['rows'],'size':entry['atlasSize'],'rects':entry['rects']})
 write(C/'publication.json',{'method':'Pillow complete-frame LANCZOS4xto2x; exact original atlas rects; no fitting, crop, warp, recolor, repair or per-facing adjustment.','pillowVersion':Image.__version__,'records':reductions,'atlases':atlases})
 write(C/'raw-records.json',records);write(C/'atlas-records.json',atlases)
 camera=json.loads((C/'native-camera.json').read_text());pubcamera=copy.deepcopy(camera);pubcamera['captureScale']=2;pubcamera['nativeRecord']='native-camera.json';pubcamera['nativeCaptureScale']=4;pubcamera['nativeFrame']=[768,1536];pubcamera['publication']='Exact whole-frame LANCZOS4xto2x';pubcamera['calibration']={k:[x/2 for x in v] for k,v in camera['calibration'].items()};pubcamera['artStyle']={'revision':'native-warm-soft-coral-round01','lighting':'120W overhead + four equal45W disk fills, neutral world.28; soft symmetric native Cycles; no ground plane','material':'Native vertex-color satin coral and matte cobalt/green, analytic shallow mesh pores; no raster texture'};write(C/'published-camera.json',pubcamera)
 native=json.loads((C/'native-validation.json').read_text());ar={'id':cat['id'],'projection':cat['projection'],'frame':cat['frameSize'],'anchor':cat['root'],'scale':2,'sourceCaptureScale':4,'clips':{c['id']:{k:c[k] for k in ['frames','fps','loop','static']} for c in cat['clips']},'footprint':[1,1],'height':1.45,'actualMeasuredSweptBounds':[[min(x['bounds'][0][i] for x in native['geometryMeasurements']) for i in range(3)],[max(x['bounds'][1][i] for x in native['geometryMeasurements']) for i in range(3)]],'collection':'Coral warm soft native','rootObject':'Coral ground root','sockets':{},'ports':{},'directions':list('NESW'),'artStyle':pubcamera['artStyle']};write(C/'assetRecord.json',ar)
 owners=[o for o in native['nativeScene']['objects'] if o.get('idleAction')];rig={'assetId':cat['id'],'fps':12,'source':'source/round01/reproduce.py','static':False,'groundRootObject':'Coral ground root','footprint':[1,1],'projection':'square-top-front-oblique','armatures':[],'sockets':{},'clips':{'idle':{'frames':12,'fps':12,'loop':True,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13,'actions':[{'ownerType':'Key','ownerName':o['name'],'action':o['idleAction'],'channels':['Rooted sway X.value','Rooted sway Y.value'],'keyframeCount':26} for o in owners]},'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'actions':[],'hold':'All shape key values zero; no animated transforms'}},'notes':['Two native shape keys on each tube; weights zero belowz.22, eased to tip; constant native color attributes follow mesh.','Rock/frond/button coral static. Native root rotates S0/E90/N180/W-90.','12 unique integerframes; frame13 same key values asframe1; static samples stablethrough13.']};write(C/'rig.json',rig)
 print('Published',len(records),'frames in',len(atlases),'original-layout atlases')

def sheet(rows,path,size,cols=4,bg='#7d8792',gap=12):
 w,h=size;res=Image.new('RGB',(cols*(w+gap)+gap,math.ceil(len(rows)/cols)*(h+30)+gap),bg);dr=ImageDraw.Draw(res);mapping=[]
 for i,(label,pathin) in enumerate(rows):
  im=Image.open(pathin).convert('RGBA');im=im.resize((w,h),Image.Resampling.LANCZOS);x=gap+i%cols*(w+gap);y=gap+i//cols*(h+30);dr.text((x,y),label,fill='white');res.paste(im,(x,y+18),im);mapping.append({'input':rel(pathin),'label':label,'rect':[x,y+18,w,h]})
 path.parent.mkdir(parents=True,exist_ok=True);res.save(path);return {'path':rel(path),'sha256':sha(path),'inputs':mapping,'method':'Display contact sheet of complete frames; no sprite processing'}
def stack_images(rows,path,cols=1,maxwidth=None):
 ims=[]
 for label,p in rows:
  im=Image.open(p).convert('RGB')
  if maxwidth and im.width>maxwidth:im=im.resize((maxwidth,round(im.height*maxwidth/im.width)),Image.Resampling.LANCZOS)
  ims.append((label,p,im))
 widths=[max((im.width for _,_,im in ims[i::cols]),default=0) for i in range(cols)];heights=[max(im.height for _,_,im in ims[i:i+cols])+26 for i in range(0,len(ims),cols)];res=Image.new('RGB',(sum(widths)+12*(cols+1),sum(heights)+12),'#394956');dr=ImageDraw.Draw(res);mapping=[];y=12
 for ri in range(math.ceil(len(ims)/cols)):
  x=12
  for ci in range(cols):
   idx=ri*cols+ci
   if idx>=len(ims):continue
   label,p,im=ims[idx];dr.text((x,y),label,fill='white');res.paste(im,(x,y+18));mapping.append({'input':rel(p),'label':label,'rect':[x,y+18,im.width,im.height]});x+=widths[ci]+12
  y+=heights[ri]
 path.parent.mkdir(parents=True,exist_ok=True);res.save(path);return {'path':rel(path),'sha256':sha(path),'inputs':mapping}

def previews():
 P=C/'previews';P.mkdir(exist_ok=True);mapping=[]
 mapping.append(sheet([(d,C/'frames/static'/d/'000.png') for d in 'NESW'],P/'four-view-sheet.png',(384,768)))
 mapping.append(sheet([(d,C/'native/static'/d/'000.png') for d in 'NESW'],P/'native-four-view.png',(768,1536)))
 nativeback=Image.new('RGB',(4*(768+12)+12,2*(1536+30)+12),'#394956');nd=ImageDraw.Draw(nativeback);nm=[]
 for row,(tone,bg) in enumerate([('light','#eee7d9'),('dark','#13202d')]):
  for col,d in enumerate('NESW'):
   p=C/'native/static'/d/'000.png';im=Image.open(p).convert('RGBA');x=12+col*780;y=12+row*1566;nd.rectangle((x,y+18,x+768,y+18+1536),fill=bg);nd.text((x,y),f'{d} native4x {tone}',fill='white');nativeback.paste(im,(x,y+18),im);nm.append({'input':rel(p),'label':d+' '+tone,'rect':[x,y+18,768,1536]})
 nativeback.save(P/'native-light-dark.png');mapping.append({'path':rel(P/'native-light-dark.png'),'sha256':sha(P/'native-light-dark.png'),'inputs':nm,'method':'Complete exact native4x frames on light/dark backgrounds; gray is separate native-four-view.'})

 rows=[(f'{d} idle{i:02}',C/'frames/idle'/d/f'{i:03}.png') for d in 'NESW' for i in range(12)]
 mapping.append(sheet(rows,P/'all-motion-phases.png',(192,384),cols=12))
 for d in 'NESW':
  frames=[Image.open(C/'native/idle'/d/f'{i:03}.png').convert('RGBA') for i in range(12)]
  frames[0].save(P/f'idle-{d}.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,lossless=True,loop=0)
  mapping.append({'path':rel(P/f'idle-{d}.webp'),'sha256':sha(P/f'idle-{d}.webp'),'inputs':[rel(C/'native/idle'/d/f'{i:03}.png') for i in range(12)],'method':'Lossless full-native-size RGBA WebP playback; exact52native source frames unchanged. Timing83,83,84ms repeats; one-second loop.'})
 if (C/'browser-ledger.json').exists():
  b=C/'browser';mapping.append(stack_images([(f'all4 · {tone} · cell{pitch}',b/f'views-{tone}-{pitch}.png') for tone in ['light','gray','dark'] for pitch in [128,32]],P/'consumer-sizes.png',cols=2))
  mapping.append(stack_images([(f'fractional47.3 · phase{phase}',b/f'views-fractional-gray-{phase}.png') for phase in [0,.25,.5,.75]],P/'fractional-phases.png',cols=2))
  mapping.append(stack_images([('Phone actual interaction',b/'context-phone.png'),('Landscape actual interaction',b/'context-landscape.png')],P/'actual-context.png',cols=2))
  mapping.append(stack_images([(f'Phone t={i}/12',b/f'context-390-{i:02}.png') for i in [0,3,6,9,12]]+[(f'Landscape t={i}/12',b/f'context-844-{i:02}.png') for i in [0,3,6,9,12]],P/'context-motion.png',cols=5))
  mapping.append(stack_images([(f'All4 phone frame{i}',b/f'temporal-{i:02}.png') for i in range(13)],P/'consumer-motion.png',cols=4))
 write(C/'preview-coverage-mapping.json',mapping);print('Preview mappings',len(mapping))

if __name__=='__main__':
 if '--publish' in sys.argv:publish()
 if '--previews' in sys.argv:previews()
