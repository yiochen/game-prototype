"""Verify copied actual browser pixels/renderer bindings; no rendering or pixel editing."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-06';P=B/'source/resources/paired-consumer-v3/floor-packet';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();repo=next(p for p in B.parents if (p/'prototypes.json').exists())
bind=read(O/'paired-consumer-binding.json');bad=[x['copy'] for x in bind['copies'] if sha(B/x['copy'])!=x['sha256']];assert not bad,bad
manifest=read(B/bind['finalManifest']['path']);assert sha(B/bind['finalManifest']['path'])==bind['finalManifest']['sha256'];assert not manifest['errors'];assert manifest['allActualIntermediateSmoothingDisabled'];assert set(manifest['rendererInputs'].values())=={bind['nativeRasterRendererSHA256']}
assert sha(repo/'prototypes/sushi-loop/wireframe/world-sprite-raster.js')==bind['nativeRasterRendererSHA256'];assert sha(repo/'prototypes/sushi-loop/wireframe/sprite-layout.js')==bind['placementRendererSHA256']
allcases=[c for r in manifest['records'] for c in r['cases']];assert all(c['actualIntermediateImageSmoothingEnabled'] is False for c in allcases)
for r in manifest['records']:assert sha(P/r['path'])==r['sha256']
metrics=read(B/bind['currentContactMetrics']['path']);records=[]
for m in metrics['measurements']:
 i=np.array(Image.open(P/m['independent']['path']).convert('RGBA'),dtype=np.float64);n=np.array(Image.open(P/m['native']['path']).convert('RGBA'),dtype=np.float64);x,y,w,h=m['contactStripNativeRect'];i=i[y:y+h,x:x+w];n=n[y:y+h,x:x+w];loss=n[:,:,3]-i[:,:,3];ip=i[:,:,:3]*i[:,:,3:]/255;np_=n[:,:,:3]*n[:,:,3:]/255;diff=np.abs(ip-np_);assert int(i[:,:,3].min())==255 and int(n[:,:,3].min())==255 and int(loss.max())==0
 assert abs(float(diff.max())-m['maxPremultipliedRGBDifference'])<1e-8
 backgrounds={}
 for name,color in [('light',[242,240,230]),('gray',[167,167,167]),('dark',[31,36,42])]:
  v=np.array(color);ci=ip+v*(1-i[:,:,3:]/255);cn=np_+v*(1-n[:,:,3:]/255);backgrounds[name]={'maxRGBDifference':float(np.abs(ci-cn).max()),'meanRGBDifference':float(np.abs(ci-cn).mean())}
 records.append({'direction':m['direction'],'phase':m['phaseLogical'],'contactStripNativeRect':m['contactStripNativeRect'],'independentMinAlpha':int(i[:,:,3].min()),'nativeMinAlpha':int(n[:,:,3].min()),'maxAlphaLoss':int(loss.max()),'pixelsLostAlpha':int((loss>0).sum()),'maxPremultipliedRGBDifference':float(diff.max()),'meanPremultipliedRGBDifference':float(diff.mean()),'compositedRGBComparisonOnBackgrounds':backgrounds})
assert len(records)==16 and len({(x['direction'],x['phase']) for x in records})==16
for d in 'NESW':assert (B/f'candidates/round-06/static-{d}.png').read_bytes()==(P/f'source/resources/browser-v3-native-sampling/paired-entry-{d}.png').read_bytes()
report={'method':'Independent hash/array verification of exact copied current browser PNGs and native contact strip, retaining companion originals. No new consumer wrapper or smoothing override. Background RGB comparison is analytical alpha compositing of exact raw browser outputs; actual browser light/gray/dark screenshots separately bound.','binding':'candidates/round-06/paired-consumer-binding.json','copiedResourcesVerified':len(bind['copies']),'screenshotCount':len(manifest['records']),'caseCount':len(allcases),'actualAllContextsFalseAfterPaint':True,'browserErrors':manifest['errors'],'liveSnapshotExecutedRendererSHA256':bind['nativeRasterRendererSHA256'],'livePlacementRendererSHA256':bind['placementRendererSHA256'],'all4EntryInputFramesExactOwnExportBytes':True,'nativeFilterSize':.5,'cases':records,'all16CoverageMatchesNative':True,'rgbScope':'Native depth pair and independent sprites are not RGB pixelidentical. Recorded RGB differences remain (S max47/mean~5.88). Coverage and color are reported separately; independent judge evaluates visible seam/readability.','preservedHistoricalFailure':'candidates/round-05/consumer-contact-metrics.json','scope':'No independent approval; root seals and original judge reviews.'}
(O/'consumer-verification.json').write_text(json.dumps(report,indent=2));print('CURRENT_CONSUMER_VERIFIED',len(bind['copies']),len(manifest['records']),len(records),max(x['maxAlphaLoss'] for x in records))
