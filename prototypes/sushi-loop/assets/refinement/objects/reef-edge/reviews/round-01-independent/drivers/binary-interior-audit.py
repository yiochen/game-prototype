import sys
sys.dont_write_bytecode=True
from pathlib import Path
import math,json
from PIL import Image,ImageDraw,ImageFilter
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01';G=json.loads((B/'resources/context-geometry.json').read_text());out=[]
def audit_set(report,root,packet):
 for r in report['records']:
  if r.get('kind','primary')!='primary':continue
  d=r['d'];size=r['size'];z=size/128;a={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d];rp=r['rootPhase'];pp=r['panPhase'];folder=root/r['id'];images=[Image.open(folder/(name+'.png')).convert('RGBA') for name in ['native','independent']];w,h=images[0].size
  mask=Image.new('L',(w,h));draw=ImageDraw.Draw(mask);join=Image.new('L',(w,h));jd=ImageDraw.Draw(join)
  for key,x in [('middle',-1),('edge',0),('middle',1)]:
   g=G['assets'][key];vs=[(round(12+(352+(x*math.cos(a)+v[0]*math.cos(a)-v[1]*math.sin(a))*128+rp)*z+pp,9),round(12+(560-(x*math.sin(a)+v[0]*math.sin(a)+v[1]*math.cos(a))*128-v[2]*89.6+rp)*z+pp,9)) for v in g['vertices']]
   for t in g['triangles']:
    poly=[vs[i] for i in t];draw.polygon(poly,fill=255)
    if all(abs(g['vertices'][i][0])>=.42-1e-6 for i in t):jd.polygon(poly,fill=255)
  # Binary triangle union avoids GPU source-over antialias holes on internal
  # triangulation/cell boundaries. Conservative erosion removes outer coverage.
  mask=mask.filter(ImageFilter.MinFilter(7 if size==128 else 3));mp=mask.load();jp=join.load();aps=[im.getchannel('A').load() for im in images];samples=joins=0;loss=[0,0];joinloss=[0,0];minimum=[255,255]
  for y in range(h):
   for x in range(w):
    if mp[x,y]!=255:continue
    samples+=1;isjoin=jp[x,y]==255
    if isjoin:joins+=1
    for i,ap in enumerate(aps):
     minimum[i]=min(minimum[i],ap[x,y])
     if ap[x,y]<255:loss[i]+=1;joinloss[i]+=int(isjoin)
  out.append({'source':'packet' if packet else 'independent','backend':report['backend'],'case':r['id'],'interiorSamples':samples,'joinSamples':joins,'minimumAlpha':minimum,'interiorLoss':loss,'joinLoss':joinloss})
for backend in ['full-chromium','headless-shell']:
 audit_set(json.loads((C/'consumer'/(backend+'-results.json')).read_text()),C/'consumer'/backend,True)
 audit_set(json.loads((B/'evidence/consumer'/(backend+'-report.json')).read_text()),B/'evidence/consumer'/backend,False)
result={'method':'Independent conservative binary union of actual projected native core triangles; rounded only to1e-9 display pixels, no source/runtime changes; erosion3pixels at cell128 and1pixel at32. Includes internal triangle boundaries and both actual joined finite interfaces. Alpha mask does not derive from candidate image alpha. Raw GPU source-over-mask observations remain retained.','cases':len(out),'maximumInteriorLoss':max(max(r['interiorLoss']) for r in out),'maximumJoinLoss':max(max(r['joinLoss']) for r in out),'minimumAlpha':min(min(r['minimumAlpha']) for r in out),'minimumInteriorSamples':min(r['interiorSamples'] for r in out),'minimumJoinSamples':min(r['joinSamples'] for r in out),'records':out}
(B/'evidence/binary-interior-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','method']}))
