from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,shutil
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';P=B/'candidates/round-07/packet.json';p=json.loads(P.read_text());H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
r={'candidatePacketSHA256':H(P),'standalone':[],'browserScreenshotComparisons':[],'consumerLedger':{},'nativeProfile':{},'physicalSummary':{},'priorIndependentSeamReplay':{}}
for d,v in p['candidateRenders'].items():
 a=P.parent/v['path'];b=O/f'native-replay/static-{d}.png';i=np.array(Image.open(a));j=np.array(Image.open(b));r['standalone'].append({'direction':d,'submittedSHA256':H(a),'replaySHA256':H(b),'pixelExact':bool(np.array_equal(i,j)),'maxChannelDifference':int(np.abs(i.astype(int)-j.astype(int)).max()),'frame':list(Image.open(a).size)})
R=O/'browser-replay';submitted=B/'source/resources/paired-consumer-v4/floor-packet/candidates/round-05/browser-v4-human-reference'
for f in sorted(R.glob('*.png')):
 s=submitted/f.name
 if not s.exists():continue
 a=np.array(Image.open(f));b=np.array(Image.open(s));d=np.abs(a.astype(int)-b.astype(int));r['browserScreenshotComparisons'].append({'file':f.name,'pixelExact':bool(np.array_equal(a,b)),'maxChannelDifference':int(d.max()),'meanChannelDifference':float(d.mean())})
# Actual browser raw canvas ledger: no smoothing, exact selected authored stand/walk cohort, geometrical support and unchanged elevation.
b=json.loads((R/'consumer-evidence.json').read_text());bad=[];combos=[];supports=[]
for row in b['rawCurrentCanvas']:
 c=row['actualCase'];d=c['direction'];id=c['caseId'];phase=c['phase'];combos.append((d,id,phase));se={v['object']:v for v in c['actualFrameSelection']};ac=se['customer-rosa'];actor=next(v for v in c['placements'] if v['object']=='customer-rosa');clip='walk' if id in ['terminal-tread','transfer'] else 'stand';index=6 if clip=='walk' else 11
 expectedSupport=None if id=='approach' else 'dock-entry-1' if id in ['first-tread','second-tread','terminal-tread'] else 'dock-floor-0'
 if (ac['clip'],ac['selectedFrame'],ac['root'],ac['frameSize'])!=(clip,index,[96,248],[192,320]):bad.append([d,id,phase,'actor-frame'])
 if se['submarine-yellow']['selectedFrame']!=11 or se['dock-cover']['selectedFrame']!=11:bad.append([d,id,phase,'companion-frame'])
 if actor.get('supportedBy')!=expectedSupport:bad.append([d,id,phase,'support'])
 if abs(actor['offset'][1]+c['human'][2]*89.6-phase)>1e-8 or abs(actor['offset'][0]-phase)>1e-8:bad.append([d,id,phase,'height-offset'])
 if c['actualIntermediateImageSmoothingEnabled'] is not False:bad.append([d,id,phase,'intermediate-smoothing'])
 supports.append({'direction':d,'id':id,'phase':phase,'clip':ac['clip'],'index':ac['selectedFrame'],'support':actor.get('supportedBy'),'sourceRootXYZ':c['human'],'actualOffset':actor['offset']})
r['consumerLedger']={'screenshotCount':len(b['records']),'rawRGBAcount':len(b['rawCurrentCanvas']),'uniqueFacingStancePhaseCases':len(set(combos)),'facings':sorted(set(x[0] for x in combos)),'phases':sorted(set(x[2] for x in combos)),'browserErrors':b['errors'],'allActualIntermediateSmoothingDisabled':b['allActualIntermediateSmoothingDisabled'],'actualFramesVerified':b['actualFramesVerified'],'rendererInputs':b['rendererInputs'],'independentLedgerFailures':bad,'actualSupports':supports}
n=json.loads((O/'own-native-audit.json').read_text());vertices=np.array([v for mesh in n['entryGeometry'] for v in mesh['verticesWorld']]);boundary=n['boundaryRays'];r['nativeProfile']={'entryEnvelope':[vertices.min(0).tolist(),vertices.max(0).tolist()],'meshCount':len(n['entryGeometry']),'zeroAreaFaces':sum(m['zeroAreaFaces'] for m in n['entryGeometry']),'boundaryCount':len(boundary),'allBoundarySamplesPresent':all(x['entry'] and x['floor'] for x in boundary),'maxBoundaryHeightMismatch':max(abs(x['entry']['point'][2]-x['floor']['point'][2]) for x in boundary),'maxBoundaryErrorFromPoint22':max(abs(v['point'][2]-.22) for x in boundary for v in [x['entry'],x['floor']]),'nativeSourcesUnchanged':n['nativeSourcesUnchanged'],'savedSettings':n['savedSettings'],'savedCalibration':n['savedCalibration']}
prs=[json.loads(f.read_text()) for f in sorted((O/'physical-records').glob('*.json'))];shoes=[s for a in prs for s in a['support']['shoes']];par=json.loads((O/'own-cohort-source-parity.json').read_text());r['physicalSummary']={'cases':len(prs),'maxFullShoePenetration':max(a['support']['maximumFullShoePenetration'] for a in prs),'minFlatSoleContactFraction':min(s['flatSoleContactFraction'] for s in shoes),'minContactArea':min(s['contactArea'] for s in shoes),'badPairCount':sum(len(a['badPairs']) for a in prs),'authoredScaleEveryCase':all(a['actualRootScale']==[1.25]*3 for a in prs),'maxCohortRigidRotationVertexDrift':max(a['cohortMaximumVertexDrift'] for a in prs),'allCohortMaterialsUnchanged':all(a['cohortMaterialsUnchanged'] for a in prs),'actualSourceSnapshotObjectsChecked':len(par['rows']),'maxActualSourceVertexError':max(a['maxWorldVertexError'] for a in par['rows']),'allActualSourceMaterialsExactlyEqual':all(a['materialChannelsExactlyEqual'] for a in par['rows']),'strictDigestCaveat':'Strict serialized vertex digests in own-physical-summary include float-rounding mismatches for some snapshots. Separate actual source evaluated-geometry/material parity establishes maximum error below 1e-5; byte-identical coordinate serialization is not claimed.'}
# Retain and recalculate original independent 16-case contact proof. All candidate source, art, raster and ordering bytes are unchanged in new07. The old human path is excluded from this reuse.
old=O.parent/'round06-independent';oldmanifest=json.loads((old/'supplemental-evidence-manifest.json').read_text());dest=O/'resources/prior-independent-seam';dest.mkdir(exist_ok=True);copies=[]
for f in sorted((old/'browser-replay').glob('*.png')):
 if not (f.name.startswith('native-') or f.name.startswith('independent-')):continue
 if '-phase' not in f.name:continue
 key=str(f.relative_to(old));assert H(f)==oldmanifest['files'][key];shutil.copyfile(f,dest/f.name);copies.append({'file':f.name,'priorManifestSHA256':oldmanifest['files'][key]})
assert len(copies)==32
oldB=old/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';dependencies=['source/round-06.blend','source/resources/paired-consumer-v3/floor-packet/source/resources/paired-entry/source/round-06.blend']
# Compare every original packet resource carried forward, including source/models and browser module closure.
oldpacket=json.loads((oldB/'candidates/round-06/packet.json').read_text());records=[]
def walk(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:records.append(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
for group in ['files','candidateRenders','previews']:
 for value in oldpacket[group].values():records.append(value)
matched=0
for v in records:
 a=(oldB/'candidates/round-06'/v['path']).resolve();rel=a.relative_to(oldB.parents[5]);new=(B.parents[5]/rel)
 assert a.exists() and new.exists() and H(a)==H(new)==v['sha256'];matched+=1
contacts=[];centers={'N':(288,352-192-.22*89.6),'S':(288,352+192-.22*89.6),'E':(480,352-.22*89.6),'W':(96,352-.22*89.6)}
for d in 'NESW':
 for phase in [0,.25,.5,.75]:
  a=np.array(Image.open(dest/f'native-{d}-phase{phase}.png').convert('RGBA'),dtype=float);b=np.array(Image.open(dest/f'independent-{d}-phase{phase}.png').convert('RGBA'),dtype=float);cx,cy=centers[d];cx=(cx+phase)*2;cy=(cy+phase)*2
  rect=[round(cx-.37*256),round(cy-4),round(.74*256),8] if d in 'NS' else [round(cx-4),round(cy-.37*256),8,round(.74*256)];x,y,w,h=rect;a=a[y:y+h,x:x+w];b=b[y:y+h,x:x+w];delta=np.abs(a[:,:,:3]*a[:,:,3:]/255-b[:,:,:3]*b[:,:,3:]/255)
  contacts.append({'direction':d,'phase':phase,'analyticCentralContactRectNative':rect,'nativeMinimumAlpha':int(a[:,:,3].min()),'independentMinimumAlpha':int(b[:,:,3].min()),'alphaLossPixels':int((a[:,:,3]>b[:,:,3]).sum()),'maxAlphaLoss':float((a[:,:,3]-b[:,:,3]).max()),'maxPremultipliedRGBDifference':float(delta.max()),'meanPremultipliedRGBDifference':float(delta.mean())})
r['priorIndependentSeamReplay']={'method':'Original independent32 rawnative/currentcanvasRGBA retained and their sealed SHA verified, then analytic common plane strip recalculated. This is seam-only evidence; old rejected human support/path never reused as passing. Exact original source/render/consumer resource hashes carried unchanged into07.','matchedOriginalPacketClaims':matched,'retainedRawFiles':copies,'contactCases':contacts}
(O/'verification-summary.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'standaloneExact':all(v['pixelExact'] for v in r['standalone']),'browserCompared':len(r['browserScreenshotComparisons']),'browserExact':sum(v['pixelExact'] for v in r['browserScreenshotComparisons']),'browserMaxChannel':max(v['maxChannelDifference'] for v in r['browserScreenshotComparisons']),'consumerLedgerFailures':bad,'physical':r['physicalSummary'],'boundaryMismatch':r['nativeProfile']['maxBoundaryHeightMismatch'],'retainedSeamCases':len(contacts),'seamMaxAlphaLoss':max(v['maxAlphaLoss'] for v in contacts)},indent=2))
