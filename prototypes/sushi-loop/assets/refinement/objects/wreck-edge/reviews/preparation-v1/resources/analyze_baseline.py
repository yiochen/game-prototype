from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib,math
RES=Path(__file__).resolve().parent;BASE=RES.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hull(pts):
 p=sorted(set(tuple(v[:2]) for v in pts));cross=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);lo=[];hi=[]
 for v in p:
  while len(lo)>1 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
  lo.append(v)
 for v in reversed(p):
  while len(hi)>1 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
original=json.loads((BASE/'original-native-audit.json').read_text());canon=json.loads((BASE/'canonical-native-audit.json').read_text());raw=json.loads((BASE/'original-native-inspection-v2.json').read_text());contract=json.loads((RES/'canonical/root-native-contract.json').read_text())
portChecks=[]
for side in ['W','E']:
 for c in original['caps'][side]:
  yz=sorted([v[1:] for v in c['vertices']]);match=[s for s in contract['finitePorts'][side]['sections'] if sorted([v[1:] for v in s['authoredRingVertices']])==yz];assert len(match)==1
  portChecks.append({'side':side,'source':c['object'],'canonicalSourceSection':match[0]['name'],'exactOrderedTransverseCoordinates':True,'sourceLoop':c['vertices'],'outwardNormal':c['outwardNormal']})
fields=canon['canonicalCollarFields'];assert len(fields)==48 and all(f['constantAfterInterpolation'] for f in fields)
def desc(f):return {'yz':sorted(set(tuple(v[1:]) for v in f['vertices'])),'normal':f['normalizedShaderInputCornerNormals'][0],'material':f['material']}
fieldChecks=[]
for ob in sorted(set(f['object'] for f in fields)):
 sides={s:sorted([desc(f) for f in fields if f['object']==ob and f['side']==s],key=lambda d:(d['yz'],d['normal'],d['material'])) for s in ['W','E']};assert sides['W']==sides['E'];fieldChecks.append({'object':ob,'facesPerSide':len(sides['W']),'completeFiniteWETreeFieldsAgree':True,'descriptors':sides['W']})
replay=Image.open(BASE/'baseline/historical-native4-S.png').convert('RGBA').resize((384,704),Image.Resampling.LANCZOS);replay.save(BASE/'baseline/historical-published2-S.png');snapshot=Image.open(RES/'inputs/original.png').convert('RGBA');diff=ImageChops.difference(replay,snapshot);stat={'historicalReduction':'whole-frame768x1408 to384x704 LANCZOS only; diagnostic source replay','sourceScale':4,'filterSize':1.5,'replayPath':'baseline/historical-published2-S.png','originalSnapshotSHA256':sha(RES/'inputs/original.png'),'decodedEqual':replay.tobytes()==snapshot.tobytes(),'maxRGBA':[b[1] for b in diff.getextrema()],'differentPixels':sum(any(p) for p in diff.getdata()),'boundsOfDifference':diff.getbbox()}
results=json.loads((BASE/'consumer-baseline/results.json').read_text());crossMode=[]
for case in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 rows=[x for x in results['cases'] if x['id']==case];assert len(rows)==2 and all(not r['errors'] for r in rows)
 for d in 'NESW':
  for kind in ['independent','native-control']:
   ps=[BASE/'consumer-baseline'/(r['mode']+'-'+case+'-'+d+'-'+kind+'.png') for r in rows];ims=[Image.open(p).convert('RGBA') for p in ps];delta=ImageChops.difference(*ims);crossMode.append({'case':case,'direction':d,'kind':kind,'decodedEqual':ims[0].tobytes()==ims[1].tobytes(),'maxRGBA':[b[1] for b in delta.getextrema()]})
sheet=Image.new('RGB',(1450,1500),(58,69,82));draw=ImageDraw.Draw(sheet);mapping=[]
for i,d in enumerate('NESW'):
 y=i*370;draw.text((10,y+4),d+' unchanged source + approved middle02; logical128 / phone32',fill='white');im=Image.open(BASE/'baseline/mixed-native'/f'{d}.png').convert('RGBA')
 for j,(name,bg) in enumerate([('light',(238,238,238)),('gray',(128,128,128)),('dark',(21,25,35))]):
  thumb=im.resize((im.width//2,im.height//2),Image.Resampling.LANCZOS);bgim=Image.new('RGB',thumb.size,bg);bgim.paste(thumb,mask=thumb.getchannel('A'));sheet.paste(bgim,(10+j*480,y+24));ph=im.resize((im.width//8,im.height//8),Image.Resampling.LANCZOS);pb=Image.new('RGB',ph.size,bg);pb.paste(ph,mask=ph.getchannel('A'));sheet.paste(pb,(10+j*480+thumb.width+8,y+24));mapping.append({'source':'baseline/mixed-native/'+d+'.png','panel':[10+j*480,y+24],'background':name,'uniformScale':[.5,.125]})
sheet.save(BASE/'baseline/native-mixed-use-size-sheet.png')
# Each screenshot remains unchanged; the sheet is a review overview of the whole
# CSS image at one uniform scale, with direct files retained for natural-size views.
css=Image.new('RGB',(1600,1880),(58,69,82));dc=ImageDraw.Draw(css);cssmap=[]
for i,row in enumerate(results['cases']):
 p=BASE/'consumer-baseline'/row['cssScreenshot'];im=Image.open(p).convert('RGB');scale=min(380/im.width,850/im.height);sz=(round(im.width*scale),round(im.height*scale));x=(i%4)*400;y=(i//4)*940;dc.text((x+5,y+5),row['mode']+' '+row['id'],fill='white');css.paste(im.resize(sz,Image.Resampling.LANCZOS),(x+5,y+30));cssmap.append({'source':'consumer-baseline/'+row['cssScreenshot'],'panel':[x+5,y+30],'sourceSize':list(im.size),'uniformScale':scale})
css.save(BASE/'consumer-baseline/css-overview.png')
out={'sourcePortMatches':portChecks,'canonicalFiniteFields':fieldChecks,'sourceSupport':original['support'],'sourceEvaluatedXYHull':original['finiteXYConvexHullCCW'],'proposedAuthoringBudget':{'xyPolygonCCW':hull([v for o in raw['objects'] for v in o.get('vertices',[])]),'z':[.04,.78],'tolerance':1e-6,'status':'proposal for root freeze; source raw XY convex hull plus catalog height, not source3D/perpart locks'},'historicalReplay':stat,'consumerCrossModeNativeCanvas':crossMode,'browserModes':[{'mode':r['mode'],'version':r['browserVersion'],'executable':r['actualBrowserExecutable'],'case':r['id'],'errors':r['errors']} for r in results['cases']],'sheetMappings':{'baseline/native-mixed-use-size-sheet.png':mapping,'consumer-baseline/css-overview.png':cssmap},'limits':'Baseline preserves actual source mismatch. This is no candidate or asset approval. Numeric fields do not waive visible defects.'}
(BASE/'baseline-analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'historical':stat,'budget':out['proposedAuthoringBudget'],'consumerCases':len(results['cases']),'nativeCrossModeEqual':all(c['decodedEqual'] for c in crossMode)},indent=2))
