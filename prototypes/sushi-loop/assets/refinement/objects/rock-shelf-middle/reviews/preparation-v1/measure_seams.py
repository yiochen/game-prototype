import pathlib,json,sys,math
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).parent/'resources/python-library'))
from PIL import Image,ImageDraw,ImageChops,ImageStat
B=pathlib.Path(__file__).parent;E=B/'evidence';results={}
for label,prefix in [('historical','consumer'),('study-filter05-box','study-consumer')]:
 rows={}
 for d in 'NESW':
  a=Image.open(E/f'{prefix}-nativecanvas-independent-{d}.png').convert('RGBA');n=Image.open(E/f'{prefix}-nativecanvas-joined-{d}.png').convert('RGBA');mask=Image.new('L',a.size);dr=ImageDraw.Draw(mask)
  # Use actual fixed section projection on the common native grid (plan x=y=-.5, scale2).
  def pix(p):return tuple(round((v+.5)*2) for v in p)
  if d in 'NS':
   for x in (160,288):dr.rectangle((*pix((x-2,278)),*pix((x+2,435))),fill=255)
  else:
   profile=[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]
   for y in (312,440):
    pts=[pix((224-128*w,y-89.6*z)) for w,z in profile];dr.polygon(pts,fill=255);dr.line(pts+[pts[0]],fill=255,width=5)
  mask.save(E/f'{prefix}-cutface-mask-{d}.png')
  cases={}
  for mname,m in [('allNativeOpaque',None),('projectedCutface',mask)]:
   count=deficit=0;minimum=255;maxdef=0;sumdef=0;maxrgb=[0,0,0];sumrgb=[0,0,0];maxcomps={k:[0,0,0] for k in ['light','gray','dark']}
   samples=[]
   for y in range(a.height):
    for x in range(a.width):
     av=a.getpixel((x,y));nv=n.getpixel((x,y))
     if nv[3]!=255 or (m is not None and not m.getpixel((x,y))):continue
     count+=1;minimum=min(minimum,av[3]);delta=255-av[3];sumdef+=delta;maxdef=max(maxdef,delta)
     if delta:deficit+=1
     for c in range(3):v=abs(av[c]-nv[c]);maxrgb[c]=max(maxrgb[c],v);sumrgb[c]+=v
     for k,bg in [('light',(238,242,237)),('gray',(144,144,144)),('dark',(23,37,57))]:
      for c in range(3):
       comp=round(av[c]*av[3]/255+bg[c]*(1-av[3]/255));maxcomps[k][c]=max(maxcomps[k][c],abs(comp-nv[c]))
   cases[mname]={'nativeOpaquePixels':count,'assembledAlphaLess255Pixels':deficit,'minAssembledAlphaOnNativeOpaque':minimum,'maxAlphaDeficit':maxdef,'meanAlphaDeficit':sumdef/count if count else None,'maxStraightRGBDiff':maxrgb,'meanStraightRGBDiff':[v/count for v in sumrgb] if count else [],'maxCompositeRGBDiff':maxcomps}
  # Cross-join samples in native2x canvas: fixed row top/body for N/S; center-line for E/W.
  points={}
  if d in 'NS':
   for x in (160,288):
    for y in (300,360,410,425):points[f'x{x}y{y}']={'independent':[a.getpixel(pix((x+dx,y))) for dx in (-1,-.5,0,.5,1)],'nativeJoined':[n.getpixel(pix((x+dx,y))) for dx in (-1,-.5,0,.5,1)]}
  else:
   for y in (273.5,401.5):points[f'center-y{y}']={'independent':[a.getpixel(pix((224,y+dy))) for dy in (-1,-.5,0,.5,1)],'nativeJoined':[n.getpixel(pix((224,y+dy))) for dy in (-1,-.5,0,.5,1)]}
  rows[d]={'metrics':cases,'localRGBAAcrossJoins':points}
 results[label]=rows
(E/'seam-measurements.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:{d:v['metrics'] for d,v in ds.items()} for k,ds in results.items()},indent=2))
