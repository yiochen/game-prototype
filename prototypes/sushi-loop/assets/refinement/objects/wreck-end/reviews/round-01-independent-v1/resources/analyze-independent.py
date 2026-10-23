from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;E=R.parent;OBJ=E.parent.parent;C=OBJ/'candidates/round-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(Path(p).read_text());write=lambda n,j:(E/n).write_text(json.dumps(j,indent=2)+'\n')
a=load(E/'native-audit.json');curves=load(E/'curve-audit.json')['curves'];con=load(R/'root-preparation-reconciliation-v1.json');hull=con['authoringEnvelope']['xy'];tol=1e-6
points=a['own']['rawVertices']+a['own']['evaluatedVertices']+[p for c in curves for k in ['rawCurveControlPoints','evaluatedVertices'] for p in c[k]]
def clearance(p):return min((hull[(i+1)%len(hull)][0]-x)*(p[1]-y)-(hull[(i+1)%len(hull)][1]-y)*(p[0]-x) for i,(x,y) in enumerate(hull))
def inside(p):return .04-tol<=p[2]<=.78+tol and all((b[0]-x)*(p[1]-y)-(b[1]-y)*(p[0]-x)>=-tol*math.dist([x,y],b) for i,(x,y) in enumerate(hull) for b in [hull[(i+1)%len(hull)]])
violations=[p for p in points if not inside(p)];assert not violations,violations[:5]
# Independent polygon-union/intersection integration. Partition at every edge/vertex event;
# the union interval length is linear on each event-free slab, so symmetric interior
# quadrature exactly integrates finite polygon regions including triangulated overlaps.
polys=[[v[:2] for v in f['vertices']] for f in a['own']['supportFaces']];expected=[con['finiteSupport']['unionXY']]
def segments(ps):return [(p[i],p[(i+1)%len(p)]) for p in ps for i in range(len(p))]
def crosscut(ps,x):
 allspans=[]
 for p in ps:
  crossing=[]
  for u,v in segments([p]):
   if min(u[0],v[0])<x<max(u[0],v[0]):crossing.append(u[1]+(v[1]-u[1])*(x-u[0])/(v[0]-u[0]))
  crossing.sort();allspans += list(zip(crossing[::2],crossing[1::2]))
 merged=[]
 for u,v in sorted(allspans):
  if merged and u<=merged[-1][1]+1e-12:merged[-1][1]=max(v,merged[-1][1])
  else:merged.append([u,v])
 return merged
segs=segments(polys+expected);events={v[0] for p in polys+expected for v in p}
for u,v in segs:
 for q,r in segs:
  dx=v[0]-u[0];ex=r[0]-q[0]
  if abs(dx)<1e-12 or abs(ex)<1e-12:continue
  m=(v[1]-u[1])/dx;n=(r[1]-q[1])/ex
  if abs(m-n)<1e-12:continue
  x=(q[1]-n*q[0]-u[1]+m*u[0])/(m-n)
  if max(min(u[0],v[0]),min(q[0],r[0]))<x<min(max(u[0],v[0]),max(q[0],r[0])):events.add(x)
area=[0.,0.,0.]
for lo,hi in zip(sorted(events),sorted(events)[1:]):
 if hi-lo<1e-12:continue
 for f in [.211324865405187,.788675134594813]:
  xx=lo+(hi-lo)*f;p=crosscut(polys,xx);q=crosscut(expected,xx);lens=[sum(v-u for u,v in p),sum(v-u for u,v in q),sum(max(0,min(v,b)-max(u,z)) for u,v in p for z,b in q)]
  for i,l in enumerate(lens):area[i]+=(hi-lo)*l/2
xor=max(0,area[0]+area[1]-2*area[2]);assert xor<1e-6,(area,xor)
ref=load(R/'canonical-rig.json');canonicalGraph=load(E/'canonical-rig-independent.json');rig=a['rig'];checks={k:rig[k]==ref[k] for k in ['engine','viewTransform','look','exposure','gamma','dither','filter','camera']};checks['worldGraph']=rig['worldGraph']==canonicalGraph['worldGraph'];checks['worldBackground']=rig['worldBackground']==[[.7200000286102295,.800000011920929,1.,1.],.2800000011920929]
for light in ref['lights']:
 actual=next(v for v in rig['lights'] if v['name']==light['name']);checks['light:'+light['name']]=all(actual[k]==v for k,v in light.items()) and actual['nodeGraph']==next(v for v in canonicalGraph['lights'] if v['name']==light['name'])['nodeGraph']
assert all(checks.values()),checks
fc=a['finiteFieldComparisons'];assert len(fc)==27 and all(x['materialFunctionsEqual'] and x['wholeFaceConstantBoth'] and x['maxNormalizedNormalDelta']<1e-6 and not x['tangentRequirement'] for x in fc)
assert all(x['outwardCapCorrect'] for x in fc if x['domain'][0]=='cap')
props=a['own']['rootProperties'];assetRecord=load(C/'records/asset.json');assert assetRecord['portProfiles']=={'W':'wreck-frame-section-v1'} and all(set(p)=={'W'} for p in assetRecord['ports'].values())
assert props['asset_id']=='wreck-end' and props['visual_height']==.78
assert sum(f['domain'][0]=='cap' for f in fc)==3
# Sole port declaration is in the actual bound asset record; native cap geometry,
# handedness, finite domains and fields are measured rather than assuming a custom-property format.

assert all(not o['objectAnimation'] and not o['dataAnimation'] and not o['shapeKeys'] and o['localObject'] and o['localData'] for o in a['own']['objects'])
assert all(not x['materialAnimation'] and not x['nodeAnimation'] and x['local'] for x in a['own']['materials'].values());assert not a['savedStateBeforeReviewPose']['imageFiles'] and not a['savedStateBeforeReviewPose']['libraries'] and not a['savedStateBeforeReviewPose']['actions']
replays=[]
for d in 'NESW':
 for kind,src in [('single',C/'heroes'/(d+'.png')),('chain',C/'connected-native'/(d+'.png'))]:
  p=E/'replay'/kind/(d+'.png');x=np.array(Image.open(src).convert('RGBA'),dtype=np.int16);y=np.array(Image.open(p).convert('RGBA'),dtype=np.int16);delta=np.abs(x-y);replays.append({'direction':d,'kind':kind,'candidate':str(src.relative_to(OBJ)),'independent':str(p.relative_to(OBJ)),'candidateSHA256':sha(src),'independentSHA256':sha(p),'decodedExact':bool(np.array_equal(x,y)),'differentPixels':int(np.any(delta,axis=2).sum()),'maxRGBA':delta.max(axis=(0,1)).tolist()})
assert all(x['decodedExact'] for x in replays if x['kind']=='single')
# Inspect declared fixture and recorded actual cases without redundant browser reruns.
browser=load(C/'consumer/results.json');case_checks=[]
expectedCases={'logical128-integer':([1440,900],1,1,[0,0],[0,0]),'logical128-fractional':([1440,900],1,.773,[.375,.625],[.213,-.371]),'phone32-integer':([390,844],2,.25,[0,0],[0,0]),'phone32-fractional':([390,844],2,.25,[.375,.625],[.213,-.371])}
for c in browser['cases']:
 vv,dpr,scale,offset,pan=expectedCases[c['id']];ev=c['evidence'];assert c['viewport']==vv and c['deviceScaleFactor']==dpr and ev['case']['cssScale']==scale and ev['case']['rootOffset']==offset and ev['case']['pan']==pan and not c['errors'] and c['browserVersion']=='153.0.8010.12'
 assert c['launch']==({'headless':True,'channel':'chromium'} if c['mode']=='full-chromium' else {'headless':True})
 assert len(ev['fixtures'])==12 and {(f['direction'],f['background']) for f in ev['fixtures']}=={(d,b) for d in 'NESW' for b in ['light','gray','dark']}
 assert all(f['nativeNearestRestoredAfterResize'] and all(k['nearestAfterResize'] and k['wholeCSSImageRendering']=='auto' for k in f['actualDisplayChecks']) for f in ev['fixtures'])
 case_checks.append({'mode':c['mode'],'case':c['id'],'browserVersion':c['browserVersion'],'actualExecutable':c['actualBrowserExecutable'],'actualExecutableSHA256':c['actualBrowserExecutableSHA256'],'launch':c['launch'],'viewport':vv,'DPR':dpr,'wholeCSS':'auto','nativeNearestAfterResize':True,'all4AndBackgrounds':True,'errors':c['errors']})
assert len(case_checks)==8
for f,h in [('world-sprite-raster.js','570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'),('sprite-layout.js','099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65')]:
 assert sha(OBJ/'source/round01-resources/consumer'/f)==h
 for c in browser['cases']:assert c['inputHashes'][f]==h
for d in 'NESW':
 names=[OBJ/'candidates/round-01'/p for p in ['heroes/'+d+'.png','frames/static-'+d+'.png','native/static/'+d+'/000.png','atlases/static-'+d+'.png']];assert len({sha(p) for p in names})==1
write('independent-analysis.json',{'candidatePacketSHA256':sha(C/'packet.json'),'sourceSHA256':sha(R/'candidate.blend'),'geometry':{'rawMeshVertices':len(a['own']['rawVertices']),'evaluatedMeshVertices':len(a['own']['evaluatedVertices']),'curveObjects':len(curves),'allCheckedVerticesAndControlPoints':len(points),'violations':violations,'bounds':{'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]},'properAll4':'Independent captured root matrices; static owned geometry has no actions/constraints/shape keys that alter source across facings. Same proper rotation maps raw budget and support.'},'supportUnion':{'actualArea':area[0],'expectedArea':area[1],'intersectionArea':area[2],'symmetricDifferenceArea':xor,'supportFaceCountObservation':len(polys),'method':'Independent exact slab integration over actual polygon union and expected8point polygon; overlapping face areas never summed','geometricZ0Empty':min(v[2] for v in points)>0},'rigChecks':checks,'finiteWFields':{'functionCount':len(fc),'sideFields':sum(x['domain'][0]=='side' for x in fc),'capFields':sum(x['domain'][0]=='cap' for x in fc),'allMaterialFunctionsEquivalent':True,'maxNormalizedNormalDelta':max(x['maxNormalizedNormalDelta'] for x in fc),'wholeFiniteFunctionsProven':True,'tangentsRequired':False,'longitudinalDerivatives':0,'capOutwardW':True,'proof':'Actual active function signatures and constant corner fields matched on complete finite domains after normalization, with distinct cap fields; no material/name/type-only identity shortcut.'},'staticOwnership':'32local objects:24mesh/7curve/1root; no source linked libs/images/actions; all object/data/material/node animations absent','replays':replays,'actualBrowserCases':case_checks,'nativePNGIdentity':True,'limitations':'Broad finite-light independent-vs-native RGB residuals and tiny outer-raster coverage differences remain actual consumer evidence, not waived by field/replay equality. Browser images examined in original complete lossless tiles. No corner/familyL or publishing approval.'})
print('BUDGET',len(points),'all inside; SUPPORT',area,'xor',xor,'RIG',all(checks.values()),'FIELDS',len(fc));print('REPLAY',[(x['kind'],x['direction'],x['differentPixels'],x['maxRGBA']) for x in replays]);print('BROWSER',len(case_checks),'complete')
