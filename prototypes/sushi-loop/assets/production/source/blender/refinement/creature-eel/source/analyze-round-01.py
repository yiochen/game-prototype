import sys
sys.dont_write_bytecode=True
import json,hashlib,re
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent;E=P.parent;C=E/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
measure=json.loads((C/'native-measurements.json').read_text());capture=json.loads((C/'capture-records.json').read_text());publication=json.loads((C/'publication.json').read_text());browser=json.loads((C/'browser-records.json').read_text())
rows=[r for rs in measure['views'].values() for r in rs]
assert len(rows)==528 and len(capture['records'])==542 and len(publication['rawFrames'])==528
assert len(browser)==2
facings={f:next(r for r in capture['records'] if r['direction']==f) for f in ['N','E','S','W']}
validation={'asset':'creature-eel','round':1,'stage':'native technical evidence; pending independent visual review','project':'source/round-01.blend','projectSHA256':sha(P/'round-01.blend'),'camera':'candidates/round-01/native-camera.json',
 'views':{f:{'direction':f,'rootRotationZ':r['rootRotationZ'],'actualRootMatrix':r['actualRootMatrix']} for f,r in facings.items()},
 'captureRecords':capture['records'],'nativeGeometryMeasurements':measure['views'],
 'nativeFrame':[1792,2048],'publishedFrame':[896,1024],'logicalFrame':[448,512],'logicalRoot':[224,352],'nativeCaptureScale':4,'sourceScale':2,
 'checks':{'all528PosesFinite':all(r['finite'] for r in rows),'all528InsideFrozenClearance':all(r['withinCanonicalBudget'] for r in rows),'all528ProjectedInsideFrame':all(r['projectedInsideFrame'] for r in rows),'all12MeshesClosedManifold':all(o['nonManifoldEdges']==0 for o in measure['ownership']),'rootNeverTranslated':all(max(abs(x) for x in r['rootLocation'])<1e-8 for r in rows),'maxHeadAttachmentResidual':max(r['headAttachmentVertexResidual'] for r in rows),'all528NativeAlphaEdgesClear':all(r['edgeAlphaMax']==0 for r in publication['alphaAudit'])},
 'canonicalSEnvelope':[[min(r['canonicalSEvaluatedBounds'][0][i] for r in measure['views']['S']) for i in range(3)],[max(r['canonicalSEvaluatedBounds'][1][i] for r in measure['views']['S']) for i in range(3)]],
 'loopClosuresAndTerminalHolds':measure['closures'],'ownership':measure['ownership'],
 'limits':['Closed topology/finite points and coherent weights do not by themselves prove absence of every self intersection or visual crease. Actual candidate pixels and allphase native sheets require independent judge inspection.','No game logic, full gameplay tether, device, production integration or deployment was changed. Current consumer fixture is bounded presentation evidence.','Published frames are whole-canvas LANCZOS reductions. Native and published antialiasing differ naturally; no RGB/alpha repair performed.']}
save(C/'native-validation.json',validation)
controlPixels=[]
for clip,r in measure['closures'].items():
 base=C/'native'/clip/'S'/('000.png' if r['loop'] else '011.png')
 for frame in ([13] if r['loop'] else [13,24]):
  other=C/'controls'/clip/'S'/f'{frame-1:03}.png';a=np.array(Image.open(base).convert('RGBA'));b=np.array(Image.open(other).convert('RGBA'));diff=np.abs(a.astype(np.int16)-b.astype(np.int16));visible=(a[:,:,3]>0)|(b[:,:,3]>0);opaque=(a[:,:,3]==255)&(b[:,:,3]==255)
  controlPixels.append({'clip':clip,'comparison':'native1to13' if r['loop'] else f'native12to{frame}','base':str(base.relative_to(E)),'control':str(other.relative_to(E)),'baseSHA256':sha(base),'controlSHA256':sha(other),'maxChannelDelta':int(diff.max()),'visibleMeanAbsoluteDelta':float(diff[visible].mean()),'opaqueMeanAbsoluteDelta':float(diff[opaque].mean()),'visiblePixelsOver5':int((diff.max(axis=2)[visible]>5).sum()),'visiblePixels':int(visible.sum()),'interpretation':'Same evaluated pose controls; actual native renderer residual retained. Published loop wraps use the actual12phase atlas; one-shot hold reuses final published cell.'})
save(C/'native-control-pixel-residuals.json',{'records':controlPixels,'limits':'Native pose equality is established separately by evaluated vertex/bone controls. Pixel residuals are measured; hashes do not replace visible transition review.'})

comparisons=[]
for mode in ['all','logical','phone','attachments','repeated','playback-wave','playback-turn','playback-reaction']:
 a=C/'browser/chromium'/f'{mode}.png';b=C/'browser/shell'/f'{mode}.png';ia=np.array(Image.open(a).convert('RGBA'));ib=np.array(Image.open(b).convert('RGBA'));assert ia.shape==ib.shape
 delta=np.abs(ia.astype(np.int16)-ib.astype(np.int16));diff=delta.max(axis=2)
 comparisons.append({'mode':mode,'chromiumPath':str(a.relative_to(E)),'shellPath':str(b.relative_to(E)),'chromiumSHA256':sha(a),'shellSHA256':sha(b),'dimensions':[ia.shape[1],ia.shape[0]],'maxChannelDelta':int(delta.max()),'meanAbsoluteChannelDelta':float(delta.mean()),'pixelsDifferent':int((diff>0).sum()),'pixelsDeltaOver5':int((diff>5).sum()),'totalPixels':int(diff.size),'interpretation':'Actual browser raster/configuration residual; static representatives use exact same phase. No blanket aesthetic waiver.'})
launchlog=(P/'capture-consumer-round-01.log').read_text()
executions=[line.strip() for line in launchlog.splitlines() if '<launching>' in line]
save(C/'browser-comparison.json',{'comparisons':comparisons,'actualExecutableLaunchCommands':executions,'launchLog':'source/capture-consumer-round-01.log','notes':['Both actual supported Playwright launch modes; actual version, CDP metadata, launch options, DPR, viewport and errors in browser-records.json.','Full actual rAF2.2s playback for three compact panels spans all11rules and all4facings. Recorded videos are real viewport playback; phase witnesses read actual composed canvas pixels, no APNG default-frame inference.','Video compression and browser raster residuals remain visible evidence; no exact cross-mode alias claim.']})

motion=[];boundaryPixels=[]
for mode in browser:
 for p in mode['playback']:
  timelines=p['timeline'];by={}
  for row in timelines:
   for f in row['frames']:by.setdefault((f['clip'],f['facing']),[]).append((row['seconds'],f['frame'],f['loop']))
  for (clip,facing),vals in by.items():
   seen=sorted(set(v[1] for v in vals));wraps=sum(a[1]==11 and b[1]==0 for a,b in zip(vals,vals[1:]));late=[v[1] for v in vals if v[0]>=1.1]
   witnesses=[w for w in p['phaseWitnesses'] if w['clip']==clip and w['facing']==facing]
   hashes={w['visiblePositionRGBAFNV32'] for w in witnesses}
   motion.append({'mode':mode['id'],'panel':p['panel'],'clip':clip,'facing':facing,'phasesObserved':seen,'RAFCount':len(vals),'actualElapsed':p['actualElapsed'],'observed11to0Wraps':wraps,'terminalLatePhases':sorted(set(late)) if not vals[0][2] else None,'distinctActualCanvasPixelDigests':len(hashes),'loop':vals[0][2]})
   selected=[w for row in p['boundaryWitness'] for w in row['digests'] if w['clip']==clip and w['facing']==facing and ((row['seconds'] in [0,1,2]) if vals[0][2] else row['seconds']>=11/12)]
   digests={w['visiblePositionRGBAFNV32'] for w in selected};assert len(digests)==1,(mode['id'],clip,facing,digests)
   boundaryPixels.append({'mode':mode['id'],'panel':p['panel'],'clip':clip,'facing':facing,'kind':'loop0at0_1_2seconds' if vals[0][2] else 'heldTerminal11at11_12andLater','samples':len(selected),'actualCanvasDigestsEqual':len(digests)==1})
  assert not mode['errors'],mode['errors']
save(C/'motion-witness-summary.json',{'records':motion,'actualCanvasBoundaryPixelChecks':boundaryPixels,'cadence':'Requested phase=floor(elapsedSeconds*12+1e-7) using unchanged spriteFrame; actual RAF times/phase order/boundary12to1/hold digests retained in browser-records.','limits':'Every native phase is retained and mapped separately. rAF cadence is browser sampling; missed phase slots, if any, are explicitly listed, not inferred from video sparse frames.'})
assert all(r['phasesObserved']==list(range(12)) for r in motion),motion
assert all(r['observed11to0Wraps']>=1 if r['loop'] else r['terminalLatePhases']==[11] for r in motion)
print('VALIDATED_NATIVE',len(rows),'BROWSER_MOTION',len(motion),'MODE_RESIDUALS',[(r['mode'],r['maxChannelDelta'],r['pixelsDifferent']) for r in comparisons],flush=True)
