from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,math
RES=Path(__file__).resolve().parent;REV=RES.parent;OBJ=RES.parents[2];CAND=OBJ/'candidates/round-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();packet=json.loads((CAND/'packet.json').read_text());checks=[]
assert sha(CAND/'packet.json')=='84ba81e113279c5777e9cd5a1ce682dd05755bb6bf5175fe60f7fe0443d12c49'
for group in ['files','candidateRenders','previews']:
 for key,item in packet[group].items():
  p=(CAND/item['path']).resolve();assert sha(p)==item['sha256'],str(p);checks.append({'group':group,'key':key,'path':str(p),'sha256':item['sha256']})
aliases=[]
for a in json.loads((RES/'aliases.json').read_text())['aliases']:
 p=OBJ/a['alias'];q=OBJ/a['retainedInspectionSource'];assert sha(p)==sha(q)==a['sha256'];aliases.append(a)
identity=[];replay=[]
def compare(a,b):
 aa=Image.open(a).convert('RGBA');bb=Image.open(b).convert('RGBA');assert aa.size==bb.size;diff=ImageChops.difference(aa,bb);return {'decodedEqual':aa.tobytes()==bb.tobytes(),'maxRGBA':[e[1] for e in diff.getextrema()],'differentPixels':sum(any(p) for p in diff.get_flattened_data())}
for d in 'NESW':
 paths=[CAND/f'frames/static/{d}/000.png',CAND/f'native/static/{d}/000.png',CAND/f'atlases/static-{d}.png'];assert len({sha(p) for p in paths})==1;identity.append({'direction':d,'nativePublishedAtlasPNGBytesIdentical':True,'sha256':sha(paths[0])});r=compare(REV/f'recapture/{d}/000.png',paths[0]);assert r['decodedEqual'];replay.append({'direction':d,**r})
actual=json.loads((REV/'candidate-native-audit.json').read_text());canonical=json.loads((RES/'canonical-native-audit.json').read_text());contract=json.loads((RES/'root-native-contract.json').read_text());rec=json.loads((RES/'reconciliation.json').read_text());extras=json.loads((REV/'native-extras.json').read_text());assert actual['sourceSHA256']==sha(RES/'native/candidate.blend')=='a7f8357632d42d3f5113f7ee3b423634bdd834e0d3cbfb9a058ea513767a1498'
norm=lambda x:json.loads(json.dumps(x).replace('wreck-edge__','wreck-middle__'))
assert norm(actual['caps'])==canonical['caps']
assert norm(actual['canonicalCollarFields'])==canonical['canonicalCollarFields'];assert len(actual['canonicalCollarFields'])==48 and all(f['constantAfterInterpolation'] for f in actual['canonicalCollarFields'])
materials={m['name']:m['tree'] for m in canonical['materials']}
for m in actual['materials']:assert m['tree']==materials[m['name']]
assert actual['lights']==canonical['lights'] and actual['world']==canonical['world'] and actual['camera']==canonical['camera']
assert not actual['ownedActions'] and not actual['armatures'] and not actual['externalLibraries'] and not actual['ownedImageNodes']
assert not extras['images'] and not extras['actions'] and not extras['armatures'];assert all(not p['outsideObjectUsers'] and not p['images'] and not p['animation'] for p in extras['privateMaterials'])
assert extras['render']=={'engine':'BLENDER_EEVEE','viewTransform':'Standard','look':'None','exposure':0.0,'gamma':1.0,'dither':0.0,'percentage':100,'transparent':True,'PNG':['PNG','RGBA','8'],'useCompositing':True,'compositorGroup':None}
polygon=rec['authoringEnvelope']['xy'];zmin,zmax=rec['authoringEnvelope']['z'];worst=0
for v in actual['evaluatedVertices']:
 assert zmin-1e-6<=v[2]<=zmax+1e-6
 for a,b in zip(polygon,polygon[1:]+polygon[:1]):
  cross=(b[0]-a[0])*(v[1]-a[1])-(b[1]-a[1])*(v[0]-a[0]);violation=-cross/math.hypot(b[0]-a[0],b[1]-a[1]);worst=max(worst,violation);assert violation<=1e-6
assert abs(actual['support']['z']-.04)<1e-6 and abs(actual['support']['totalArea']-.36)<1e-6 and not actual['support']['geometricZ0Intersection']
for t in actual['support']['facesAtZ04']:
 for v in t['vertices']:assert abs(v[0])<=.500001 and abs(v[1])<=.180001 and abs(v[2]-.04)<1e-6
captures=json.loads((REV/'own-capture-records.json').read_text())
for r in captures:
 assert r['nativeFrame']==[384,704] and abs(r['filter']-.01)<1e-7 and r['ortho']==1.5 and r['pixelAspect']==[1.2206555604934692,1.0]
 assert abs(r['calibration']['root'][0]-192)<.001 and abs(r['calibration']['root'][1]-496)<.001
 assert abs(r['calibration']['unitX'][0]-256)<.001 and abs(r['calibration']['unitDepth'][1]-256)<.001 and abs(r['calibration']['unitHeight'][1]+179.2)<.001
 assert actual['render']['frame']==1 and actual['render']['fps']==12 and actual['render']['range']==[1,1]
mixed=[]
for r in json.loads((REV/'mixed-recapture-records.json').read_text()):
 d=r['direction'];forbidden=False;expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]
 for key,localx in [('edge',0),('middleMinus1',-1),('middlePlus1',1)]:
  mat=r['roots'][key];assert abs(mat[0][3]-math.cos(expected)*localx)<1e-6 and abs(mat[1][3]-math.sin(expected)*localx)<1e-6
  assert abs(math.atan2(mat[1][0],mat[0][0])-expected)<1e-5 or d=='N' and abs(math.atan2(mat[1][0],mat[0][0])+math.pi)<1e-5
 delta=compare(REV/f'mixed-recapture/{d}.png',CAND/f'mixed-native/{d}.png');mixed.append({'direction':d,**delta,'actualProperUnitPitchRoots':True})
 # Renderer precision may differ; retain honestly, never repair or turn into a visual waiver.
 assert max(delta['maxRGBA'])<=1 and delta['maxRGBA'][3]==0
browser=json.loads((CAND/'consumer/results.json').read_text());assert len(browser['cases'])==8
nativeCross=[];cssCross=[];modeRecords=[]
helperHashes={'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
for name,h in helperHashes.items():assert sha(OBJ/'source/consumer'/name)==h
for row in browser['cases']:
 assert not row['errors'] and row['browserVersion']=='153.0.8010.12'
 expectedLaunch={'headless':True,'channel':'chromium'} if row['mode']=='full-chromium' else {'headless':True};assert row['launch']==expectedLaunch
 assert ('Google Chrome for Testing' in row['actualBrowserExecutable']) if row['mode']=='full-chromium' else ('chrome-headless-shell' in row['actualBrowserExecutable'])
 assert row['viewport']==([390,844] if row['id'].startswith('phone') else [1440,900]);assert row['deviceScaleFactor']==(2 if row['id'].startswith('phone') else 1)
 for name,digest in row['inputHashes'].items():
  if name in ['fixture.html','fixture.mjs','fixture.bundle.js','world-sprite-raster.js','sprite-layout.js']:p=OBJ/'source/consumer'/name
  else:
   d,label=name.split('-',1);p=(CAND/'atlases'/f'static-{d}.png') if label=='original' else ((OBJ/'source/round01-resources'/f'approved-{d}.png') if label=='middle' else CAND/'mixed-native'/f'{d}.png')
  assert sha(p)==digest
 assert len(row['evidence']['fixtures'])==12
 for f in row['evidence']['fixtures']:
  d=f['direction'];assert f['plan']['scale']==2;assert f['background'] in ['light','gray','dark'];assert len(f['orderedPlacements'])==3
  sign=-1 if d in ['N','W'] else 1;vertical=d in ['E','W'];offset=row['evidence']['case']['rootOffset'];assert offset==([.375,.625] if row['id'].endswith('fractional') else [0,0])
  for place in f['orderedPlacements']:
   local=int(place['id'].split('local')[1]);assert place['direction']==d and place['offset']==offset
   assert place['x']==(0 if vertical else local*sign)-.5 and place['y']==(-local*sign if vertical else 0)-.5
  assert row['evidence']['case']['pan']==([.213,-.371] if row['id'].endswith('fractional') else [0,0])
 modeRecords.append({k:row[k] for k in ['mode','id','browserVersion','actualBrowserExecutable','launch','viewport','deviceScaleFactor','errors']})
for case in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 rows=[r for r in browser['cases'] if r['id']==case]
 for d in 'NESW':
  for kind in ['independent','native-control']:
   paths=[CAND/'consumer'/(r['mode']+'-'+case+'-'+d+'-'+kind+'.png') for r in rows];result=compare(*paths);assert result['decodedEqual'];nativeCross.append({'case':case,'direction':d,'kind':kind,**result})
 paths=[CAND/'consumer'/r['cssScreenshot'] for r in rows];cssCross.append({'case':case,**compare(*paths)})
out={'candidatePacketSHA256':sha(CAND/'packet.json'),'allExactPacketDescriptorsVerified':checks,'uniqueBoundFiles':len(set(r['path'] for r in checks)),'byteIdenticalAliases':aliases,'nativePublishedAtlasIdentity':identity,'ownSavedSourceHeroReplay':replay,'ownMixedSavedSourceReplay':mixed,'finiteNative':{'evaluatedBounds':actual['bounds'],'maximumFiniteRawXYViolation':worst,'raw7PointPrismZ':rec['authoringEnvelope']['z'],'supportArea':actual['support']['totalArea'],'noZ0':True,'all6CapsAnd48ActualFiniteSideFieldsMatchApprovedCanonical':True,'fullActualMaterialGraphsEqual':True,'actualCameraLightsWorldEqual':True,'privateStaticResources':True},'browserAudit':{'cases':modeRecords,'helpers':helperHashes,'allInputHashesAndTrueRootPlacementsVerified':True,'nativeCrossMode':nativeCross,'actualCSSCrossMode':cssCross},'limits':'Exact technical checks support actual pixels, never waive a visible local join defect. Whole image identity is not claimed for connected-native/consumer finite-light/exterior raster precision or CSS mode differences.'}
(REV/'independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'boundFiles':out['uniqueBoundFiles'],'capsAndFields':True,'heroRecaptures':replay,'mixedRecaptures':mixed,'CSS':cssCross},indent=2))
