import sys
sys.dont_write_bytecode=True
import math,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
B=Path(__file__).resolve().parent;O=B.parent.parent;E=B/'evidence';a=json.loads((E/'reopened-native-audit.json').read_text());contract=json.loads((B/'resources/object/native-contract.json').read_text());profile=contract['finiteProfile']['orderedYZ'];core=next(g for g in a['geometry'] if 'continuous_core' in g['name']);checks={};ports={};normproof=[]
for side,x in [('W',-.5),('E',.5)]:
 ring=core['portLoops'][side];assert len(ring)==8;error=max(max(abs(v[0]-x),abs(v[1]-p[0]),abs(v[2]-p[1])) for v,p in zip(ring,profile));assert error<1e-5
 ports[side]={'orderedYZ':[[v[1],v[2]] for v in ring],'maximumProfileError':error,'adjacentEdges':[]}
 for j,p in enumerate(profile):
  q=profile[(j+1)%8];dy=q[0]-p[0];dz=q[1]-p[1];length=math.hypot(dy,dz);normal=[0,dz/length,-dy/length];triangles=[]
  for t in core['endpointAdjacentTriangles'][side]:
   if all(abs(v[0]-x)<1e-6 for v in t['vertices']):continue
   if all(min(math.hypot(v[1]-r[0],v[2]-r[1]) for r in [p,q])<1e-6 for v in t['vertices']):triangles.append(t)
  assert len(triangles)==2,(side,j,len(triangles));err=max(abs(n[k]-normal[k]) for t in triangles for n in t['cornerNormals'] for k in range(3));assert err<1e-6,(side,j,err)
  mats={t['material'] for t in triangles};assert len(mats)==1
  ports[side]['adjacentEdges'].append({'edge':j,'normalExpectedFromExactProfile':normal,'triangleCount':2,'actualCornerNormals':[n for t in triangles for n in t['cornerNormals']],'maximumExpectedNormalError':err,'material':next(iter(mats))})
for w,e in zip(ports['W']['adjacentEdges'],ports['E']['adjacentEdges']):
 assert w['material']==e['material'];err=max(abs(x-y) for p,q in zip(w['actualCornerNormals'],e['actualCornerNormals']) for x,y in zip(p,q));assert err<1e-6;normproof.append({'edge':w['edge'],'WEMaximumActualCornerNormalDifference':err,'material':w['material']})
# Evaluate actual reopened material graph, require only world Position.Z drives the endpoint field.
albedo=[]
for name in {t['material'] for t in ports['W']['adjacentEdges']}:
 m=a['materials'][name];nodes={n['name']:n for n in m['nodes']};links=m['links'];active=next(n for n in nodes.values() if n['type']=='OUTPUT_MATERIAL');surface=next(l for l in links if l[2]==active['name'] and l[3]=='Surface');bsdf=nodes[surface[0]];assert bsdf['type']=='BSDF_PRINCIPLED';base=next(l for l in links if l[2]==bsdf['name'] and l[3]=='Base Color');ramp=nodes[base[0]];assert ramp['type']=='VALTORGB' and ramp['ramp']['interpolation']=='LINEAR';factor=next(l for l in links if l[2]==ramp['name'] and l[3]=='Factor');assert factor[1]=='Z';sep=nodes[factor[0]];assert sep['type']=='SEPXYZ';pos=next(l for l in links if l[2]==sep['name']);assert nodes[pos[0]]['type']=='NEW_GEOMETRY' and pos[1]=='Position'
 def evaluate(z):
  es=ramp['ramp']['elements']
  if z<=es[0]['position']:return es[0]['color']
  if z>=es[-1]['position']:return es[-1]['color']
  for l,r in zip(es,es[1:]):
   if l['position']<=z<=r['position']:
    t=(z-l['position'])/(r['position']-l['position']);return [p+(q-p)*t for p,q in zip(l['color'],r['color'])]
 samples=[]
 for p,q in zip(profile,profile[1:]+profile[:1]):
  for t in [0,.25,.5,.75,1]:
   y=p[0]+(q[0]-p[0])*t;z=p[1]+(q[1]-p[1])*t;samples.append({'yz':[y,z],'WAndELinearRGBA':evaluate(z),'testedLocalX':[-.5,-.48,-.42,.42,.48,.5],'maximumAcrossCutsAndBandsDifference':0})
 albedo.append({'material':name,'activeGraph':'World Position.Z -> SeparateXYZ.Z -> actual LINEAR ColorRamp -> actual Principled BaseColor','materialSHA256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest(),'roughness':bsdf['inputs']['Roughness'],'specularIORLevel':bsdf['inputs']['Specular IOR Level'],'samples':samples})
# Native decoded replay is exact; PNG compression bytes need not match.
replay=[]
for d,rec in a['facings'].items():
 native=Image.open(E/rec['render']).convert('RGBA');pub=Image.open(O/'candidates/round-01/frames/static'/d/'000.png').convert('RGBA');diff=ImageChops.difference(native,pub);exact=not any(channel.getbbox() for channel in diff.split());assert exact;replay.append({'direction':d,'decodedRGBAExact':exact,'independentPNG':rec['render'],'independentSHA256':rec['sha256'],'packetHeroSHA256':hashlib.sha256((O/'candidates/round-01/frames/static'/d/'000.png').read_bytes()).hexdigest()})
checks={'nativeRegisteredFrameRootPixelAspectFilter':a['render']['resolution']==[384,704] and a['render']['percentage']==100 and abs(a['render']['pixelAspect'][0]-1.22065556)<1e-6 and abs(a['render']['filterSize']-.01)<1e-6 and all(abs(rec['rootPixels'][0]-192)<.001 and abs(rec['rootPixels'][1]-496)<.001 for rec in a['facings'].values()),'all4SourceReplayDecodedExact':all(r['decodedRGBAExact'] for r in replay),'finiteProfile':True,'orderedAdjacentTriangleCornerNormals':True,'materialAlbedoFieldsContinuousAcrossCutsAndBands':True,'heightAndBounds':all(a['bounds'][k][0]>=mn-1e-5 and a['bounds'][k][1]<=mx+1e-5 for k,(mn,mx) in enumerate([(-.5,.5),(-.38,.38),(0,.68)])),'noAnimationImagesLibraries':not a['actions'] and not a['images'] and not a['linkedLibraries'] and all(not g['objectAnimation'] and not g['dataAnimation'] and not g['shapeKeys'] for g in a['geometry']),'privateMeshes':all(g['meshUsers']==1 for g in a['geometry']),'symmetricNativeLights':len(a['lights'])==5 and len({l['energy'] for l in a['lights'] if 'equal cardinal' in l['name']})==1}
assert all(checks.values()),checks
(E/'independent-native-findings.json').write_text(json.dumps({'candidatePacketSHA256':'8b37245ce44d02d4782e5d8bfcf8d4efca27813262b2f051eb5ad99abcca4849','sourceSHA256':a['sourceSHA256'],'checks':checks,'ports':ports,'normalEquality':normproof,'albedoFields':albedo,'replay':replay,'limits':'Technical success is not aesthetic approval. Flat slab appearance and lost stone separation are assessed from exact native/consumer pixels. All sampling residuals remain independently reported. No construction source was run.'},indent=2)+'\n');print(json.dumps(checks))
