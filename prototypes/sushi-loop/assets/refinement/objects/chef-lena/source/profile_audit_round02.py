from pathlib import Path
from PIL import Image,ImageDraw
import json,math,hashlib,collections
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-02';OLD=O/'candidates/round-01';BG={'light':'#EFEBE1','gray':'#7C7C7C','dark':'#191D24'}
new=json.loads((C/'native-frames.json').read_text());old=json.loads((OLD/'native-frames.json').read_text());old={(x['clip'],x['direction'],x['index']):x for x in old};recipe=json.loads((P/'recipe-round02.json').read_text());cam=recipe['camera'];origin=cam['root'];ux=cam['unitX'];ud=cam['unitDepth'];uz=cam['unitHeight']
def mouthbox(row):
 b=row['geometry']['chef_lena__R01_gentle_smile']['bounds'];ps=[]
 for x in b[0]:
  for y in b[1]:
   for z in b[2]:ps.append((origin[0]+ux[0]*x-ud[0]*y+uz[0]*z,origin[1]+ux[1]*x-ud[1]*y+uz[1]*z))
 return [math.floor(min(x[0] for x in ps))-3,math.floor(min(x[1] for x in ps))-3,math.ceil(max(x[0] for x in ps))+3,math.ceil(max(x[1] for x in ps))+3]
def components(im,roi):
 w,h=im.size;data=list(im.get_flattened_data());a=bytearray(1 if p[3]>128 else 0 for p in data);found=[]
 for n in range(w*h):
  if not a[n]:continue
  stack=[n];a[n]=0;xs=[];ys=[];dark=0
  while stack:
   k=stack.pop();x=k%w;y=k//w;xs.append(x);ys.append(y);dark+=max(data[k][:3])<100
   for q in ([k-1] if x>0 else [])+([k+1] if x+1<w else [])+([k-w] if y>0 else [])+([k+w] if y+1<h else []):
    if a[q]:a[q]=0;stack.append(q)
  bbox=[min(xs),min(ys),max(xs)+1,max(ys)+1];bw=bbox[2]-bbox[0];bh=bbox[3]-bbox[1]
  intersects=bbox[0]<roi[2] and bbox[2]>roi[0] and bbox[1]<roi[3] and bbox[3]>roi[1]
  if intersects and len(xs)>=5 and bw<=12 and bh<=26 and dark/len(xs)>.6:found.append({'bbox':bbox,'pixels':len(xs),'darkFraction':dark/len(xs)})
 return found
rows=[]
for r in new:
 if r['direction'] not in ['E','W']:continue
 oldr=old[r['clip'],r['direction'],r['index']];b1=mouthbox(r);b0=mouthbox(oldr);roi=[min(b0[0],b1[0]),min(b0[1],b1[1]),max(b0[2],b1[2]),max(b0[3],b1[3])];before=components(Image.open(O/oldr['path']).convert('RGBA'),roi);after=components(Image.open(O/r['path']).convert('RGBA'),roi);rows.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'roi':roi,'beforeDetachedDarkComponents':before,'afterDetachedDarkComponents':after})
report={'method':'4-connected alpha>128/255 (visible coverage; faint antialias bridges ignored) components; local projected native mouth envelope, component5+pixels,width<=12,height<=26,60%pixelsRGB<100. Body/plate main components are excluded by scale. Diagnostic only; independent visual judgment required.','profileFrames':len(rows),'beforeAffectedFrames':sum(bool(r['beforeDetachedDarkComponents']) for r in rows),'afterAffectedFrames':sum(bool(r['afterDetachedDarkComponents']) for r in rows),'frames':rows};(C/'profile-alpha-audit.json').write_text(json.dumps(report,indent=2))
# Native fixed-crop evidence, no fitting or painting. Clip×profile×extrema captured on all backgrounds.
lookup={(r['clip'],r['direction'],r['index']):r for r in new}
for bg,color in BG.items():
 sheet=Image.new('RGB',(1056,1760),color);dr=ImageDraw.Draw(sheet)
 for ci,clip in enumerate(['idle','work','hold','load']):
  for di,direction in enumerate(['E','W']):
   for fi,frame in enumerate([0,5,11]):
    r=lookup[clip,direction,frame];br=mouthbox(r);# Fixed profile region from judge enlarged for full expressive facial edge.
    rect=(250,315,294,415) if direction=='E' else (90,315,134,415)
    im=Image.open(O/r['path']).convert('RGBA').crop(rect);bgim=Image.new('RGBA',im.size,color);bgim.alpha_composite(im);tile=bgim.convert('RGB').resize((176,400),Image.Resampling.NEAREST);x=di*528+fi*176;y=ci*440;sheet.paste(tile,(x,y+28));dr.text((x+3,y+5),f'{clip} {direction} {frame:02d}',fill='#EDE9DD' if bg=='dark' else '#263342')
 sheet.save(C/('profile-all-actions-'+bg+'.png'))
comp=Image.new('RGB',(704,440),BG['light']);dr=ImageDraw.Draw(comp)
for col,(roundname,base,direction,rect) in enumerate([('round01',OLD,'E',(250,315,294,415)),('round02',C,'E',(250,315,294,415)),('round01',OLD,'W',(90,315,134,415)),('round02',C,'W',(90,315,134,415))]):
 im=Image.open(base/'frames'/('idle-'+direction)/'000.png').convert('RGBA').crop(rect);b=Image.new('RGBA',im.size,BG['light']);b.alpha_composite(im);comp.paste(b.convert('RGB').resize((176,400),Image.Resampling.NEAREST),(col*176,28));dr.text((col*176+4,6),roundname+' idle '+direction,fill='#263342')
comp.save(C/'profile-smile-comparison.png');print('PROFILE AUDIT',report['profileFrames'],report['beforeAffectedFrames'],report['afterAffectedFrames'])
