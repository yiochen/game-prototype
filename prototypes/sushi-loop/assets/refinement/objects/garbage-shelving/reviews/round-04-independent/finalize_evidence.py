from pathlib import Path
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,hashlib,math
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');B=O/'candidates/round-04';OUT=O/'reviews/round-04-independent';A=json.loads((OUT/'native-independent-audit.json').read_text());P=json.loads((B/'packet.json').read_text());C=json.loads((OUT/'packet-raster-context-audit.json').read_text());OR=json.loads((O/'reviews/source-audit/native-audit.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def err(x,y):
 if isinstance(x,(list,tuple)):return max((err(a,b) for a,b in zip(x,y)),default=0)
 return abs(x-y)
rawrows=[]
for x in A['independentSampleRenders']:
 p=Path(x['path']);ep=B/'frames'/f"{x['clip']}-{x['direction']}"/f"{int(x['frame1'])-1:03d}.png";a=Image.open(p);b=Image.open(ep);di=ImageChops.difference(a,b);rawrows.append({'independentRender':str(p),'independentRenderSHA256':sha(p),'sealedFrame':str(ep),'sealedFrameSHA256':sha(ep),'pixelExact':a.tobytes()==b.tobytes(),'meanAbsoluteRGBA':ImageStat.Stat(di).mean})
provided=[]
for c,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in ['S','E','N','W']:
  for i in range(n):
   p=B/'reproduction/frames'/f'{c}-{d}'/f'{i:03d}.png';ep=B/'frames'/f'{c}-{d}'/f'{i:03d}.png';a=Image.open(p);b=Image.open(ep);di=ImageChops.difference(a,b);provided.append({'reproduction':str(p),'reproductionSHA256':sha(p),'sealedFrame':str(ep),'sealedFrameSHA256':sha(ep),'pixelExact':a.tobytes()==b.tobytes(),'meanAbsoluteRGBA':ImageStat.Stat(di).mean})
fail=[];ev={};src={(p['clip'],p['direction'],float(p['frame1'])):p for p in OR['phases']};primary={'location':0,'rotation':0,'scale':0,'matrix':0};supplied=json.loads((B/'candidate-phases.json').read_text())+json.loads((B/'candidate-inbetweens.json').read_text());sup={(p['clip'],p['direction'],float(p['frame1'])):p for p in supplied};ledgerError=0
for p in A['phases']:
 c,d,f=p['clip'],p['direction'],p['frame1'];lo,hi=([-1,-1,-.002],[1,1,1.6801]) if c=='idle' else ([-1.008,-1.008,-.009],[1.008,1.008,1.694]) if c=='highlighted' else ([-1.566082864,-1.555552869,-.002],[1.563991098,1.250407248,2.277417688])
 if any(p['rootLocalMin'][i]<lo[i]-1e-6 or p['rootLocalMax'][i]>hi[i]+1e-6 for i in range(3)):fail.append(['envelope',c,d,f])
 if err(p['rootLocation'],[0,0,0])>1e-6 or err(p['rootScale'],[1,1,1])>1e-6:fail.append(['root',c,d,f])
 if any(x['hiddenRender'] or x['hiddenViewport'] for x in p['objects']):fail.append(['visibility',c,d,f])
 same=sup[c,d,f];ledgerError=max(ledgerError,err(p['rootLocalMin'],same['rootLocalMin']),err(p['rootLocalMax'],same['rootLocalMax']))
 if (c,d,f) in src:
  orig={o['name']:o for o in src[c,d,f]['objects']}
  for o in p['objects']:
   old=orig[o['name']]
   for key,oldkey in [('location','location'),('rotation','rotationEuler'),('scale','scale'),('matrix','matrixWorld')]:primary[key]=max(primary[key],err(o[key],old[oldkey]))
for c in ['idle','highlighted','clearance']:
 pp=[p for p in A['phases'] if p['clip']==c];ev[c]={'allFourFacingRootLocalMin':[min(p['rootLocalMin'][i] for p in pp) for i in range(3)],'allFourFacingRootLocalMax':[max(p['rootLocalMax'][i] for p in pp) for i in range(3)],'samples':len(pp)}
expected={('old_upright_-0.88_-0.36'):[-.91,-.36],('old_upright_-0.88_0.36'):[-.91,.36],('old_upright_0.88_-0.36'):[.85,-.36],('old_upright_0.88_0.36'):[.85,.36]};support=[]
for c in A['contacts']:
 k=c['owner'].split('__')[-1];e=expected.get(k);delta=max(abs(c['lowBandCentroid'][i]-e[i]) for i in range(2)) if e else None;pas=abs(c['minimumZ'])<=.002 and (delta is None or delta<=.03);support.append({'owner':c['owner'],'minimumZ':c['minimumZ'],'sourceSupportStationXY':e,'lowBandCentroid':c['lowBandCentroid'],'stationXYMaximumError':delta,'pass':pas})
 if not pas:fail.append(['support',k])
camOriginal=OR['cameraRecord896']['camera'];camerr=err(A['camera']['matrix'],camOriginal['worldMatrix']);projerr=err(A['camera']['projection'],camOriginal['projectionMatrix']);fixedcam=max(err(p['cameraMatrix'],A['camera']['matrix']) for p in A['phases']);closure=[]
for d in ['S','E','N','W']:
 p0=next(p for p in A['phases'] if p['clip']=='highlighted' and p['direction']==d and p['frame1']==1);p13=next(p for p in A['phases'] if p['clip']=='highlighted' and p['direction']==d and p['frame1']==13);closure.append({'direction':d,'maximumMatrixError':max(err(x['matrix'],y['matrix']) for x,y in zip(p0['objects'],p13['objects']))})
sh=Image.new('RGB',(896,1424),(118,118,118));dr=ImageDraw.Draw(sh)
for row,(c,f) in enumerate([('idle',1),('highlighted',4),('clearance',6),('clearance',12)]):
 for j,d in enumerate(['S','E','N','W']):
  p=OUT/'native-rerender'/f'{c}-{d}-{f:02d}.png';im=Image.open(p).convert('RGBA').resize((224,336),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,(118,118,118,255));bg.alpha_composite(im);sh.paste(bg.convert('RGB'),(j*224,row*356+20));dr.text((j*224+4,row*356+3),f'fresh native {c} {d} f{f}',fill='white')
sh.save(OUT/'independent-rerender-samples.png')
report={'packetSHA256':sha(B/'packet.json'),'briefSHA256':sha(O/'brief.json'),'candidateProjectSHA256':sha(O/'source/round-04/round-04.blend'),'deliverySnapshotSHA256':sha(B/'delivery.snapshot.json'),'failures':fail,'nativePhaseCount':len(A['phases']),'envelopes':ev,'source54ActionCohortsAllExact':all(x['exactSourceCurveKeys'] for x in A['actionChecks']),'sourcePrimaryCarrierMaximumErrors':primary,'providedPhaseLedgerBoundsMaximumDifference':ledgerError,'cameraMatrixError':camerr,'cameraProjectionError':projerr,'cameraMatrixVariationAll380Samples':fixedcam,'closure':closure,'contacts':support,'mainBodyIdleWidth':next(p for p in A['phases'] if p['clip']=='idle' and p['direction']=='S')['rootLocalMax'][0]-next(p for p in A['phases'] if p['clip']=='idle' and p['direction']=='S')['rootLocalMin'][0],'minimumRasterBorder':C['minimumBorder'],'independentNativeRerenderSampleCount':len(rawrows),'independentNativeRerenderMaximumMeanRGBA':max(max(x['meanAbsoluteRGBA']) for x in rawrows),'independentNativeRerenderComparisons':rawrows,'providedFullNativeReproductionFrameCount':len(provided),'providedReproductionMaximumMeanRGBA':max(max(x['meanAbsoluteRGBA']) for x in provided),'providedReproductionComparisons':provided,'bitIdentityLimit':'Exact source/packet/resource integrity is verified. Pixel comparison evidence is specific to saved inputs/outputs, not a universal renderer byte/pixel identity guarantee.','currentSavedSourceDependencies':{'libraries':A['libraries'],'sampledImages':[x for x in A['images'] if x['name']!='Render Result'],'note':'Earlier submitted native-audit/validation retain a pre-save original-library bookkeeping entry; the actual sealed saved source loaded independently has no linked library or sampled image. The bound immutable original-library resource is additionally present and hash-valid.'},'sourceIntegrityUnchanged':{'original':sha(O/'source/round-04/resources/original-library.blend'),'target':sha(O/'inputs/target.png'),'criteria':sha(O/'reviews/proposedcriteria.json'),'sourceContract':sha(O/'reviews/source-contract-proposal.json')}}
(OUT/'technical-summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['failures','nativePhaseCount','envelopes','source54ActionCohortsAllExact','sourcePrimaryCarrierMaximumErrors','providedPhaseLedgerBoundsMaximumDifference','cameraMatrixError','cameraProjectionError','cameraMatrixVariationAll380Samples','closure','mainBodyIdleWidth','minimumRasterBorder','independentNativeRerenderMaximumMeanRGBA','providedReproductionMaximumMeanRGBA']},indent=2))
