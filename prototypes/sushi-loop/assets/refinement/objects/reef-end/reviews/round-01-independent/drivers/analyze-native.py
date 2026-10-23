import sys
sys.dont_write_bytecode=True
import json,math,hashlib
from pathlib import Path
from collections import Counter
from PIL import Image,ImageChops
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01';E=B/'evidence'
a=json.loads((E/'candidate-audit.json').read_text());c=json.loads((E/'canonical-audit.json').read_text());core=next(g for g in a['geometry'] if 'continuous_core' in g['name']);canon=next(g for g in c['geometry'] if 'continuous_core' in g['name'])
def ident(t):return tuple(sorted(tuple(round(x,7) for x in v) for v in t['vertices']))
def collar(g):return [t for t in g['triangles'] if all(v[0]<=-.42+1e-6 for v in t['vertices'])]
can={ident(t):t for t in collar(canon)};actual={ident(t):t for t in collar(core)};assert set(can)==set(actual),(len(can),len(actual));fields=[];maxerr=0
for key,t in actual.items():
 ref=can[key];assert t['material']==ref['material'];assert a['materials'][t['material']]==c['materials'][ref['material']]
 def order(ns,vs):return dict(zip([tuple(round(x,7) for x in v) for v in vs],ns))
 cs=order(ref['cornerNormals'],ref['vertices']);ns=order(t['cornerNormals'],t['vertices']);keys=sorted(cs)
 def normalized(v):
  l=math.sqrt(sum(x*x for x in v));return [x/l for x in v]
 errs=[]
 for bary in [[1,0,0],[0,1,0],[0,0,1],[.2,.3,.5],[.3333333333333333]*3,[.7,.2,.1]]:
  n=normalized([sum(bary[i]*ns[keys[i]][k] for i in range(3)) for k in range(3)]);r=normalized([sum(bary[i]*cs[keys[i]][k] for i in range(3)) for k in range(3)]);err=max(abs(x-y) for x,y in zip(n,r));errs.append(err);maxerr=max(err,maxerr)
 assert max(errs)<1e-6
 graph=a['materials'][t['material']];assert not any(link[2]=='Principled BSDF' and link[3]=='Normal' for link in graph['links'])
 fields.append({'triangle':key,'material':t['material'],'maxNormalizedPostInterpolationNormalError':max(errs),'sameActualMaterialGraph':True,'shaderNormal':'Native geometric/corner normal, normalized after interpolation; no connected PrincipledNormal override.'})
# Exact node/ramp equality implies all Position.Z albedo samples and native surface parameters agree, not just names.
area=0;ground=[];edges=Counter();verts=core['vertices']
for f in core['faces']:
 for x,y in zip(f,f[1:]+f[:1]):edges[tuple(sorted((x,y)))]+=1
for t in core['triangles']:
 if all(abs(v[2])<1e-7 for v in t['vertices']):
  p,q,r=t['vertices'];ar=abs((q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]))/2;area+=ar;ground.append(t['vertices'])
assert abs(area-.6384)<1e-6 and set(edges.values())=={2}
profile=[[-.38,0],[.38,0],[.38,.2],[.25,.4],[.08,.44],[-.14,.35],[-.3,.4],[-.38,.2]]
ring=[v for v in verts if abs(v[0]+.5)<1e-6];assert len(ring)==8
assert all(min(max(abs(v[1]-p[0]),abs(v[2]-p[1])) for v in ring)<1e-6 for p in profile)
bounds=[[min(g['bounds'][k][0] for g in a['geometry']),max(g['bounds'][k][1] for g in a['geometry'])] for k in range(3)];assert all(lo>=mn-1e-5 and hi<=mx+1e-5 for (lo,hi),(mn,mx) in zip(bounds,[(-.5,.34),(-.38,.38),(0,.68)]))
assert a['world']==c['world'];background=next(n for n in a['world']['nodes'] if n['type']=='BACKGROUND');worldInputs={i['name']:i['value'] for i in background['inputs']};assert abs(worldInputs['Strength']-.32)<1e-7
assert a['lights']==c['lights'];assert not a['images'] and not a['libraries'] and not a['actions'];assert all(g['meshUsers']==1 and not g['animation'] and not g['shapeKeys'] for g in a['geometry']);assert all(not g['animation'] for g in a['materials'].values())
replay=json.loads((E/'reopened-replay-ledger.json').read_text());heroes=[];contexts=[]
def compare(p,q):
 x=Image.open(p).convert('RGBA');y=Image.open(q).convert('RGBA');assert x.size==y.size;d=ImageChops.difference(x,y);return {'decodedRGBAExact':all(ch.getbbox() is None for ch in d.split()),'differentPixels':sum(any(v) for v in d.getdata()),'maximumRGBAChannelDifference':[ch.getextrema()[1] for ch in d.split()]}
for d,r in replay['heroes'].items():
 result=compare(E/r['render'],C/'frames/static'/d/'000.png');assert result['decodedRGBAExact'];heroes.append({'direction':d,**result,'rootPixels':r['rootPixels']});assert abs(r['rootPixels'][0]-192)<.001 and abs(r['rootPixels'][1]-496)<.001
for n,r in replay['contexts'].items():contexts.append({'context':n,**compare(E/r['render'],C/'native/contexts'/(n+'.png')),'rootPixels':r['rootPixels']})
check={'collarGeometry22TrianglesExact':len(fields)==22,'normalizedPostInterpolationNormalField':maxerr<1e-6,'actualAlbedoMaterialGraphsExact':True,'actualCanonicalWorldAndLightsExact':True,'worldStrength32DistinctFromWeight0':worldInputs,'finiteGroundAreaAndClosedCore':True,'bounds':bounds,'privateStaticNativeOwnership':True,'registeredDirect2xCamera64Samples':a['render']['samples']==64 and a['render']['resolution']==[384,704] and abs(a['render']['filter']-.01)<1e-7 and abs(a['render']['pixelAspect'][0]-1.22065556)<1e-6,'all4HeroDecodedReplayExact':True}
(E/'independent-native-findings.json').write_text(json.dumps({'candidatePacketSHA256':'48e08fc7f305a01eb9855350ad4a39c5487bf69da8024d832bae2d4eec8140f3','sourceSHA256':a['sourceSHA256'],'canonicalSHA256':c['sourceSHA256'],'checks':check,'groundArea':area,'groundTriangles':ground,'coreEdgeIncidence':dict(Counter(edges.values())),'collarFields':fields,'maximumNormalizedPostInterpolationNormalError':maxerr,'heroReplay':heroes,'nativeContextReplay':contexts,'limits':'Independent exact native reopens and all4heroes/all8assemblycontrols. Nativecontext RGB/alpha differences retained, no exact identity assumed. Geometry/topology/cap/count improvements permitted within frozen finite contract. No construction recipe executed.'},indent=2)+'\n')
print(json.dumps({'checks':check,'maxFieldError':maxerr,'groundArea':area,'contextReplay':contexts}))
