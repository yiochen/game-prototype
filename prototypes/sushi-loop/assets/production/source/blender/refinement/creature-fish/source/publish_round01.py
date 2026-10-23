from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,copy,sys
P=Path(__file__).resolve().parent;E=P.parent;O=E/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def rec(p,**kw):return {**kw,'path':str(p.relative_to(E)),'dimensions':list(Image.open(p).size),'sha256':sha(p)}
C=json.loads((P/'round-01-resources/inputs/catalog-object-original.json').read_text());captures=json.loads((O/'native-capture-records.json').read_text());G=json.loads((O/'geometry-ledger.json').read_text());assert len(captures['captureRecords'])==528
raw=[];native=[];atlases=[];audits=[];coverage=[];colors={'light':'#f3f1e8','gray':'#858c92','dark':'#152338'}
for clip in C['clips']:
 ci=clip['id']
 for d,entry in clip['directions'].items():
  atlas=Image.new('RGBA',(5376,2048));frames=[]
  for i in range(12):
   n=O/'native'/ci/d/f'{i:03d}.png';im=Image.open(n).convert('RGBA');assert im.size==(1792,2048);pub=im.resize((896,1024),Image.Resampling.LANCZOS);q=O/'published'/ci/d/f'{i:03d}.png';q.parent.mkdir(parents=True,exist_ok=True);pub.save(q)
   x,y,w,h=entry['rects'][i];assert [w,h]==[896,1024];atlas.paste(pub,(x,y));native.append(rec(n,clip=ci,direction=d,index=i));raw.append(rec(q,clip=ci,direction=d,index=i));frames.append(pub)
   alpha=pub.getchannel('A');border=any(alpha.crop(box).getbbox() for box in [(0,0,896,1),(0,1023,896,1024),(0,0,1,1024),(895,0,896,1024)])
   assert not border,(ci,d,i,'border clipping')
   audits.append({'clip':ci,'direction':d,'index':i,'alphaBBox':alpha.getbbox(),'alphaBorderNonzero':border,'decodedRGBA_SHA256':hashlib.sha256(pub.tobytes()).hexdigest()})
  ap=O/'atlases'/f'{ci}-{d}.png';ap.parent.mkdir(parents=True,exist_ok=True);atlas.save(ap);entry['image']=str(ap.relative_to(O));atlases.append(rec(ap,clip=ci,direction=d,columns=6,rows=2,rects=entry['rects'],frameOrder=clip['frameOrder'],frames=12,fps=12,loop=clip['loop']))
  for i,f in enumerate(frames):
   x,y,w,h=entry['rects'][i];assert atlas.crop((x,y,x+w,y+h)).tobytes()==f.tobytes()
 # Lossless PNG review sheets, each cell is a uniform whole-frame reduction.
 for zoom,tag in [(1,'logical'),(.4,'phone')]:
  w,h=round(448*zoom),round(512*zoom);sheet=Image.new('RGB',(w*12,h*4+18*4),'#858c92');draw=ImageDraw.Draw(sheet);cells=[]
  for di,d in enumerate(['N','E','S','W']):
   for i in range(12):
    q=O/'published'/ci/d/f'{i:03d}.png';im=Image.open(q).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,colors[['light','gray','dark'][di%3]]);bg.alpha_composite(im);x=i*w;y=di*(h+18)+18;sheet.paste(bg.convert('RGB'),(x,y));draw.text((x+3,y-15),f'{ci} {d} {i}',fill='white');cells.append({'source':str(q.relative_to(E)),'sourceSHA256':sha(q),'clip':ci,'direction':d,'index':i,'cell':[x,y,w,h]})
  q=O/'sheets'/f'allphase-{ci}-{tag}.png';q.parent.mkdir(parents=True,exist_ok=True);sheet.save(q);coverage.append({'sheet':str(q.relative_to(E)),'sha256':sha(q),'wholeRegisteredFrame':True,'zoom':zoom,'cells':cells})
 # Representative true-logical fourview studies across all backgrounds.
 for bgname,bgcolor in colors.items():
  sheet=Image.new('RGB',(448*4,512*5+18*5),bgcolor);dr=ImageDraw.Draw(sheet)
  for fi,i in enumerate([0,3,6,9,11]):
   for di,d in enumerate(['N','E','S','W']):
    im=Image.open(O/'published'/ci/d/f'{i:03d}.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,bgcolor);bg.alpha_composite(im);x=di*448;y=fi*530+18;sheet.paste(bg.convert('RGB'),(x,y));dr.text((x+5,y-15),f'{ci} {d} f{i}',fill='black' if bgname=='light' else 'white')
  q=O/'previews'/f'{ci}-logical-{bgname}.png';q.parent.mkdir(parents=True,exist_ok=True);sheet.save(q)
# One compact hero; a separate face/fin crop is diagnostic only, never a delivered frame.
hero=Image.new('RGB',(448*4,512+20),'#858c92');dr=ImageDraw.Draw(hero)
for di,d in enumerate(['N','E','S','W']):
 im=Image.open(O/'published/normal'/d/'000.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,colors['gray']);bg.alpha_composite(im);hero.paste(bg.convert('RGB'),(448*di,20));dr.text((448*di+6,3),d,fill='white')
hero.save(O/'previews/four-view-sheet.png')
detail=Image.new('RGB',(600*4,600*4),'#858c92');dr=ImageDraw.Draw(detail)
for ci,clip in enumerate(['normal','hook','caught','escape']):
 for di,d in enumerate(['N','E','S','W']):
  rs=[r for r in G['views'] if r['clip']==clip and r['direction']==d];r=max(rs,key=lambda x:x['maxArmatureRelativeVertexDisplacementFromFrame1']);i=r['index'];im=Image.open(O/'published'/clip/d/f'{i:03d}.png').convert('RGBA');bb=im.getchannel('A').getbbox();crop=im.crop((bb[0]-12,bb[1]-12,bb[2]+12,bb[3]+12));crop.thumbnail((570,560),Image.Resampling.LANCZOS);bg=Image.new('RGBA',(600,600),colors['gray']);bg.alpha_composite(crop,((600-crop.width)//2,28));detail.paste(bg.convert('RGB'),(di*600,ci*600));dr.text((di*600+6,ci*600+6),f'DIAGNOSTIC CROP {clip} {d} f{i}',fill='white')
detail.save(O/'previews/extreme-face-fin-diagnostics.png')
C['status']='candidate-awaiting-independent-review';C['artStyle']={'revision':'warm-soft-native-round01','worldLighting':True,'lighting':'Centered overhead plus four equal cardinal broad disks, neutral warm white; no ground surface or directional cast shadow','roughness':.42,'specularIORLevel':.27};C['source']='editable native round01 body; source registry IDs/timing retained; Euler-compatible five-bone spine; .58 source bone rotation amplitude; geometry reconstructed'
dump('consumer-catalog.json',C);dump('publication-records.json',{'filter':'Pillow RGBA wholecanvas native1792x2048 to896x1024 LANCZOS once, no crop/fit/recolor/alpha/RGB repair','nativeRawFrames':native,'rawFrames':raw,'atlases':atlases,'sourceScale':2,'logicalFrame':[448,512],'logicalRoot':[224,352],'nativeCaptureScale':4,'nativeFrame':[1792,2048],'cameraSourceSHA256':sha(O/'native-camera.json')});dump('frame-audit.json',audits);dump('sheet-coverage.json',coverage)
camera=copy.deepcopy(captures['camera']);camera['nativeCaptureScale']=4;camera['captureScale']=2;camera['publication']='Uniform full native canvas LANCZOS0.5';camera['calibration']={k:[x*.5 for x in v] for k,v in camera['calibration'].items()};dump('published-camera.json',camera)
A=json.loads((P/'round-01-resources/inputs/assetRecord-original.json').read_text());A['scale']=2;A['artStyle']=C['artStyle'];dump('assetRecord.json',A)
rig=json.loads((P/'round-01-resources/inputs/rig-original.json').read_text());rig['source']='round01 source actions preserved under Euler-compatible pose modes; bone Euler curve amplitudes×0.58';rig['status']='candidate-native-actions-awaiting-independent-review';rig['notes']=['All eleven action IDs/timing/slots retained. Five deform bone modes XYZ. All required clips show evaluated armature-relative body response. See geometry-ledger.json.'];dump('rig.json',rig)
print('FISH_PUBLISHED',len(raw),len(native),len(atlases),flush=True)
