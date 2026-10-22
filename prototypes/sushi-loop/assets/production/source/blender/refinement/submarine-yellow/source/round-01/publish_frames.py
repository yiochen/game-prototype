"""Lossless atlas placement and rational 12fps APNG. Never changes raw pixels."""
import json,hashlib,struct,zlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
H=Path(__file__).resolve().parent;B=H.parents[1];O=B/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def chunks(p):
 b=p.read_bytes();i=8;out=[]
 while i<len(b):
  n=struct.unpack('>I',b[i:i+4])[0];out.append((b[i+4:i+8],b[i+8:i+8+n]));i+=12+n
 return out
def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
def apng(paths,out,loop):
 parts=[chunks(p) for p in paths];header=next(d for t,d in parts[0] if t==b'IHDR');w,h=struct.unpack('>II',header[:8]);data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'acTL',struct.pack('>II',len(paths),0 if loop else 1));seq=0
 for k,ps in enumerate(parts):
  data+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,w,h,0,0,1,12,0,0));seq+=1
  for t,d in ps:
   if t!=b'IDAT':continue
   if k==0:data+=chunk(b'IDAT',d)
   else:data+=chunk(b'fdAT',struct.pack('>I',seq)+d);seq+=1
 data+=chunk(b'IEND',b'');out.write_bytes(data)
 im=Image.open(out);assert im.n_frames==12
 for k,p in enumerate(paths):im.seek(k);assert im.convert('RGBA').tobytes()==Image.open(p).convert('RGBA').tobytes(),(out,k)
 return {'frames':12,'delayNumerator':1,'delayDenominator':12,'fps':12,'numPlays':0 if loop else 1,'decodedAllFramesExactRawRGBA':True,'dispose':'none','blend':'SOURCE fullcanvas'}
allcaps=[]
for d in 'NESW':allcaps+=json.loads((O/('captures-'+d+'.json')).read_text())['captures']
runtime=[r for r in allcaps if r['kind']=='runtime'];assert len(runtime)==576
clips=list(dict.fromkeys(r['clip'] for r in runtime));atlases=[];playbacks=[];raw=[]
(O/'atlases').mkdir(exist_ok=True);(O/'playbacks').mkdir(exist_ok=True);(O/'sheets').mkdir(exist_ok=True)
for clip in clips:
 sheet=Image.new('RGBA',(3840,1536),(0,0,0,0));diag=Image.new('RGBA',(960,1536),(0,0,0,0))
 for row,d in enumerate('NESW'):
  rr=sorted([r for r in runtime if r['clip']==clip and r['direction']==d],key=lambda r:r['index']);paths=[B/r['path'] for r in rr];atlas=Image.new('RGBA',(3840,1536),(0,0,0,0));rects=[]
  for k,(r,p) in enumerate(zip(rr,paths)):
   im=Image.open(p).convert('RGBA');assert im.size==(640,768);x=k%6*640;y=k//6*768;atlas.paste(im,(x,y));rects.append([x,y,640,768]);sheet.paste(im.resize((320,384),Image.Resampling.LANCZOS),(k*320,row*384));raw.append({k:r[k] for k in ['clip','direction','index','path','sha256','size']})
  p=O/'atlases'/(clip+'-'+d+'.png');atlas.save(p)
  for k,rect in enumerate(rects):x,y,w,h=rect;assert Image.open(p).convert('RGBA').crop((x,y,x+w,y+h)).tobytes()==Image.open(paths[k]).convert('RGBA').tobytes()
  atlases.append({'clip':clip,'direction':d,'path':str(p.relative_to(B)),'sha256':sha(p),'columns':6,'rows':2,'size':[3840,1536],'rects':rects,'everyCellExactRawRGBA':True})
  p=O/'playbacks'/(clip+'-'+d+'.png');proof=apng(paths,p,not clip.endswith('impact'));playbacks.append({'clip':clip,'direction':d,'path':str(p.relative_to(B)),'sha256':sha(p),**proof})
  for k,kind in enumerate(['runtime-first','meaningful-half','closure-or-terminal']):
   pp=paths[0] if k==0 else O/'diagnostics'/(clip+'-'+d+'-'+kind+'.png');diag.paste(Image.open(pp).convert('RGBA').resize((320,384),Image.Resampling.LANCZOS),(k*320,row*384))
 sheet.save(O/'sheets'/(clip+'-all48-logical.png'));diag.save(O/'sheets'/(clip+'-first-half-end-logical.png'))
four=Image.new('RGBA',(1280,768),(0,0,0,0))
for y,clip in enumerate(['dock-ready','upgraded-dock-ready']):
 for x,d in enumerate('NESW'):four.paste(Image.open(O/'frames'/(clip+'-'+d)/'000.png').resize((320,384),Image.Resampling.LANCZOS),(x*320,y*384))
four.save(O/'four-view-sheet.png')
save(O/'publication-ledger.json',{'sourceSHA256':sha(H/'project.blend'),'rawFrames':raw,'atlases':atlases,'playbacks':playbacks,'allRuntimeFrames':576,'atlasCount':48,'playbackCount':48,'captureRecords':allcaps,'pixelPolicy':'Selected directnative2x frames authoritative. Atlases pure lossless wholeRGBA cell placement; APNG exact rawRGBA frames at rational1/12s. Contact sheets are wholeframe ordinary Lanczos1/2 display previews only, not delivered atlas pixels. No source fit, alpha repair, recolor or perview adjustment.'})
print('PUBLISHED',len(raw),len(atlases),len(playbacks))
