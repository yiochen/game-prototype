from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib,math
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01';ROOT=P.parent;E=ROOT/'belt-corner-e-n';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();v=json.loads((O/'validation.json').read_text());native=json.loads((O/'native-continuity.json').read_text());src=json.loads((O/'source-contract.json').read_text());rots={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};r0=src['intrinsicRotationRadians'];raw=json.loads((O/'raw-frame-records.json').read_text());masks={}
# Perasset functional open ports determine native ROI geometry. No target/alpha fitting.
for d,r in rots.items():
 mm={}
 for name,p in v['ports']['S'].items():
  if name=='deck':continue
  px,py,pz=p['world'];nx,ny=round(px*2),round(py*2);tx,ty=-ny,nx;pts=[];im=Image.new('L',(896,1216));dr=ImageDraw.Draw(im)
  for cross in [-.48,.48]:
   for delta in [-.014,.014]:
    for z in [.505,.695]:
     x,y=nx*(.5+delta)+tx*cross,ny*(.5+delta)+ty*cross;xx=x*math.cos(r)-y*math.sin(r);yy=x*math.sin(r)+y*math.cos(r);pts.append((448+256*xx,752-256*yy-z*179.2))
  dr.rectangle((min(x for x,y in pts)-1,min(y for x,y in pts)-1,max(x for x,y in pts)+1,max(y for x,y in pts)+1),fill=255);mm[name]=im
 masks[d]=mm
loc=lambda a:None if not a.any() else [int(np.where(a)[1].min()),int(np.where(a)[0].min()),int(np.where(a)[1].max()),int(np.where(a)[0].max())]
def stat(a,b,mm):
 df=np.abs(a.astype(int)-b.astype(int));out={}
 for name,mask in [('full',np.ones(df.shape[:2],bool)),*mm.items()]:
  dd=df[mask];bad=np.any(df[:,:,:3]>1,axis=2)&mask;alpha=(df[:,:,3]>0)&mask;out[name]={'maxRGBA':dd.max(axis=0).tolist(),'alphaDifferentPixels':int(alpha.sum()),'RGBOver1Pixels':int(bad.sum()),'RGBOver1Bounds':loc(bad),'alphaDifferenceBounds':loc(alpha),'roiBounds':loc(mask)}
 return out
# Rotation/handedness equivalence is measured on actual registered pixels, never assumed.
if 'corner' in P.name:
 audit=json.loads((P/'source/resources/native-equivalence.json').read_text());U0=audit['deckUVEndpoints']['0']['vertexIndices'];localForward=audit['uvValues'][0][0]<.5;reference=ROOT/('belt-corner-n-e' if localForward else 'belt-corner-e-n')
else:reference=ROOT/('belt-start-n' if 'start' in P.name else 'belt-end-n')
rows=[]
if reference!=P and (reference/'candidates/round-01/frames').exists():
 refIntrinsic=0 if 'corner' in P.name else math.pi
 for d,r in rots.items():
  angle=r+r0-refIntrinsic;rd=min(rots,key=lambda k:abs(math.atan2(math.sin(rots[k]-angle),math.cos(rots[k]-angle))))
  for i in range(24):
   a=np.array(Image.open(O/'frames'/f'running-{d}-{i:02}.png'));b=np.array(Image.open(reference/'candidates/round-01/frames'/f'running-{rd}-{i:02}.png'));df=np.abs(a.astype(int)-b.astype(int));rows.append({'direction':d,'index':i,'referenceDirection':rd,'RGBAExactlyEqual':not df.any(),'maxRGBA':df.max(axis=(0,1)).tolist(),'differenceBounds':loc(np.any(df>0,axis=2))})
closure={d:Image.open(O/'frames'/f'running-{d}-00.png').tobytes()==Image.open(O/'closure'/f'running-{d}-24.png').tobytes() for d in rots}
closureStats={}
for d in rots:
 a=np.array(Image.open(O/'frames'/f'running-{d}-00.png'));b=np.array(Image.open(O/'closure'/f'running-{d}-24.png'));df=np.abs(a.astype(int)-b.astype(int));closureStats[d]={'maxRGBA':df.max(axis=(0,1)).tolist(),'differentPixels':int(np.any(df>0,axis=2).sum()),'RGBAOver1Pixels':int(np.any(df>1,axis=2).sum()),'alphaDifferentPixels':int((df[:,:,3]>0).sum()),'differenceBounds':loc(np.any(df>0,axis=2))}

common=O/'reused-coverage';common.mkdir(exist_ok=True);commonFiles=[]
for path in ['native-continuity.json','consumer-metrics.json','godot-consumer-metrics.json','portable-replay.json','consumer/motion.json']:
 original=E/'candidates/round-01'/path;dest=common/path.replace('/','-');dest.write_bytes(original.read_bytes());commonFiles.append({'sourceObject':'belt-corner-e-n','sourcePath':'candidates/round-01/'+path,'sourceSHA256':sha(original),'localCopy':dest.relative_to(P).as_posix(),'localCopySHA256':sha(dest)})
# Class reference sources/packets remain fixed. This candidate has no independent art judgment.
refPacket=reference/'candidates/round-01/packet.json';equiv={'method':'recipe-reuse','independentReview':False,'classReference':reference.name,'classReferencePacketSHA256':sha(refPacket) if refPacket.exists() else None,'intrinsicRadians':r0,'publishedPixelRotationCases':rows,'pixelEquivalenceAllExact':all(x['RGBAExactlyEqual'] for x in rows) if rows else None,'maximumRGBA':np.array([x['maxRGBA'] for x in rows]).max(axis=0).tolist() if rows else None,'closedTerminalClass':None if 'corner' in P.name else ('U0-closed-start' if 'start' in P.name else 'U1-closed-end'),'actualOwnEvidence':['validation.json','source-contract.json','native-continuity.json','consumer/cases.json'],'reusedCommonCoverage':commonFiles,'reusedCoverageMeaning':'Exact approved family material/camera/render transport and actual unchanged native compositor broad filtering/timing fixture. All own native frames/closure/registered mixed joins are actually exported/tested. Representative current SpriteScene probes are actual perasset. No duplicated consumer matrix is claimed.','savedSourceReopenProof':{'projectSHA256':sha(P/'source/round-01.blend'),'captureRecipeSHA256':sha(P/'source/capture-round01.py'),'nativeCapturedFrames':len(v['frames']),'mixedCapturedFrames':len(v['nativeAssemblies']),'images':v['dependencyClosure']['images'],'libraries':v['dependencyClosure']['libraries'],'meaning':'Capture script opens saved project without running authoring recipe; native frames, closure, independently assembled, connected and welded captures all come from those saved bytes. Native source inputs and executable build/capture are portable resources.'}}
(O/'recipe-equivalence.json').write_text(json.dumps(equiv,indent=2))
C=O/'consumer';cfg=json.loads((C/'cases.json').read_text());groups={}
for e in cfg['evidence']:groups.setdefault(e['case'],{})[e['mode']]=e
rr=[]
for key,group in groups.items():
 e=group['independent'];ims={mode:np.array(Image.open(C/f'{key}-{mode}.png').convert('RGBA')) for mode in ['independent','connected','unbroken']};h,w=ims['independent'].shape[:2];mm={name:np.array(im.resize((w,h),Image.Resampling.BOX).filter(ImageFilter.MaxFilter(5)))>0 for name,im in masks[e['direction']].items()};row={'case':key,'direction':e['direction'],'pitch':e['pitch'],**{f'{a}Vs{b.title()}':stat(ims[a],ims[b],mm) for a,b in [('independent','connected'),('independent','unbroken'),('connected','unbroken')]}};rr.append(row)
 (C/'residuals').mkdir(exist_ok=True);df=np.abs(ims['independent'].astype(int)-ims['unbroken'].astype(int)).astype('uint8');Image.fromarray(df).save(C/'residuals'/f'{key}-fullRGBA.png')
report={'cases':rr,'maximumJoinRGBA':np.array([s['maxRGBA'] for row in rr for name,s in row['independentVsUnbroken'].items() if name!='full']).max(axis=0).tolist(),'joinAlphaDifferentPixels':sum(s['alphaDifferentPixels'] for row in rr for name,s in row['independentVsUnbroken'].items() if name!='full'),'joinRGBOver1Pixels':sum(s['RGBOver1Pixels'] for row in rr for name,s in row['independentVsUnbroken'].items() if name!='full'),'method':'Actual current perasset SpriteScene captures, fullRGBA and separate functional-port ROI stats. Registered source planes, conservative2px filtering margin, exact residualmaps; no raster repair.'};(O/'consumer-metrics.json').write_text(json.dumps(report,indent=2))
checks={'method':'recipe-reuse','independentReview':False,'nativeRegistration':v['camera']==json.loads((P/'source/resources/family-settings.json').read_text())['capture'] if False else {'sameCameraWorldMatrix':v['camera']['worldMatrix']==json.loads((P/'source/resources/family-settings.json').read_text())['capture']['worldMatrix'],'sameProjectionMatrix':v['camera']['projectionMatrix']==json.loads((P/'source/resources/family-settings.json').read_text())['capture']['projectionMatrix'],'frame':v['camera']['frame'],'rootCalibration':v['camera']['calibration']['root']},'nativeFrameCount':len(raw),'closureExact':closure,'closurePixelResiduals':closureStats,'closureInterpretation':'Original authored -7integer-period key retained. Some native deck samples differ by1quantization level at frame25 versusframe1; exact counts/locations reported separately from phase/alpha failure. No source/raster correction for bitidentity.','originalDeckVerticesExactlyEqual':src['deckVerticesExactlyPreserved'],'originalUVExactlyEqual':src['deckUVExactlyPreserved'],'originalIntrinsicExactlyEqual':src['intrinsicRotationExactlyPreserved'],'originalPhaseExactlyEqual':src['originalStoredPhaseExactlyPreserved'],'allOpenFunctionalProfilesUncapped':all(not p['capPolygons'] for o in v['profiles'].values() for p in o.values()),'nativeContinuity':native['summary'],'actualCurrentConsumer':{'cases':cfg['cases'],'allReady':all(e['ready']=='true' for e in cfg['evidence']),'errors':cfg['errors'],'joinMaxRGBA':report['maximumJoinRGBA'],'joinAlphaDifferentPixels':report['joinAlphaDifferentPixels'],'joinRGBOver1Pixels':report['joinRGBOver1Pixels']},'measuredPhysicalBounds':v['measuredPhysicalBounds'],'nominalFunctionalHeight':.695,'nativeCapEnvelopeTop':None if 'corner' in P.name else .71939999,'resourceClosure':v['dependencyClosure'],'pixelRotationEquivalenceAllExact':equiv['pixelEquivalenceAllExact'],'pixelRotationMaximumRGBA':equiv['maximumRGBA']};(O/'technical-checks.json').write_text(json.dumps(checks,indent=2));print(P.name,json.dumps({'pixelEquivalent':equiv['pixelEquivalenceAllExact'],'pixelMax':equiv['maximumRGBA'],'nativeContinuity':native['summary'],'currentJoinMax':report['maximumJoinRGBA']}))
