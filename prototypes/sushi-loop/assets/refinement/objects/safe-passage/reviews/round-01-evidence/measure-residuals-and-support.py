from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json
H=Path(__file__).resolve().parent;C=H.parent.parent/'candidates/round-01';rs=[]
for d in 'NESW':
 for i in range(12):
  a=Image.open(H/'native'/d/f'{i:03}.png').convert('RGBA');b=Image.open(C/'native/ambient'/d/f'{i:03}.png').convert('RGBA');p=a.resize((384,704),Image.Resampling.LANCZOS);q=Image.open(C/'frames/ambient'/d/f'{i:03}.png').convert('RGBA');variants={}
  for size,x,y in [('native',a,b),('published',p,q)]:
   composites={}
   for color in ['#eeeeee','#777777','#121820']:
    bg=Image.new('RGBA',x.size,color);xx=Image.alpha_composite(bg,x).convert('RGB');yy=Image.alpha_composite(bg,y).convert('RGB');diff=ImageChops.difference(xx,yy)
    composites[color]={'maxAbsoluteRGB':[z[1] for z in diff.getextrema()],'meanAbsoluteRGB':ImageStat.Stat(diff).mean,'differingRGBPixels':sum(v!=w for v,w in zip(xx.getdata(),yy.getdata()))}
   variants[size]=composites
  diffs=[(x,y) for x,y in zip(a.getdata(),b.getdata()) if x!=y]
  rs.append({'direction':d,'index':i,'alphaExact':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'nativeDifferingPixels':len(diffs),'nativeAlphaRangeOfDifferingPixels':[min(x[3] for x,y in diffs),max(x[3] for x,y in diffs)] if diffs else None,'composites':variants})
(H/'native-recapture-composited-residuals.json').write_text(json.dumps({'records':rs,'interpretation':'Actual independently rerendered source RGB repeatability differences at very few pixels measured separately on three backgrounds. Submitted art remains unchanged. Fullframe native/publication/source checks and visual defect review remain independently required.'},indent=2)+'\n')
records=json.loads((H/'native-replay.json').read_text())['captureRecords'];supports=[]
def area(vs):
 ps=sorted(set((p[0],p[1]) for p in vs))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 a=[];b=[]
 for p in ps:
  while len(a)>1 and cross(a[-2],a[-1],p)<=0:a.pop()
  a.append(p)
 for p in reversed(ps):
  while len(b)>1 and cross(b[-2],b[-1],p)<=0:b.pop()
  b.append(p)
 ps=a[:-1]+b[:-1];return abs(sum(p[0]*ps[(i+1)%len(ps)][1]-ps[(i+1)%len(ps)][0]*p[1] for i,p in enumerate(ps)))/2 if len(ps)>2 else 0
for rr in records:
 for o in rr['geometry']['objects']:
  if o['role']=='stable_stone':supports.append({'direction':rr['direction'],'index':rr['index'],'object':o['object'],'evaluatedZ0CrossSectionConvexHullArea':area(o['groundIntersections'])})
(H/'finite-support-independent.json').write_text(json.dumps({'records':supports,'allFinitePositiveArea':all(x['evaluatedZ0CrossSectionConvexHullArea']>0 for x in supports),'source':'independent enabled evaluated mesh edge intersections, worldgroundz0/canonicalXY; no oldhullshape/area law inferred'},indent=2)+'\n')
print(json.dumps({'maxDisplayedNativeRGBDifference':max(max(z['maxAbsoluteRGB']) for r in rs for z in r['composites']['native'].values()),'maxDisplayedPublishedRGBDifference':max(max(z['maxAbsoluteRGB']) for r in rs for z in r['composites']['published'].values()),'finiteSupportAreas':len(supports),'minimumSupportArea':min(s['evaluatedZ0CrossSectionConvexHullArea'] for s in supports)}))
