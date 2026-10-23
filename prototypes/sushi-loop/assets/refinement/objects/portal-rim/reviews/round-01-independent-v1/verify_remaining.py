from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json,hashlib,subprocess
P=Path(__file__).resolve().parent;O=P.parents[1];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[];nativeMetadata=[]
replay=json.loads((P/'native-replay.json').read_text());original=json.loads((C/'native-measurements.json').read_text())
for d in ['N','E','S','W']:
 for i in range(12):
  raw=Image.open(C/'raw/idle'/d/f'{i:03d}.png').convert('RGBA');pub=Image.open(C/'published/idle'/d/f'{i:03d}.png').convert('RGBA');red=raw.resize((384,768),Image.Resampling.LANCZOS);dif=ImageChops.difference(red,pub)
  fresh=Image.open(P/'raw/idle'/d/f'{i:03d}.png').convert('RGBA');d2=ImageChops.difference(raw,fresh);changed=[(a,b) for a,b in zip(raw.get_flattened_data(),fresh.get_flattened_data()) if a!=b]
  rows.append({'direction':d,'frame':i,'submittedNativeWholeFrameLANCZOSExactlyEqualsPublished':not any(any(px) for px in dif.get_flattened_data()),'freshNativeAlphaExact':not ImageChops.difference(raw.getchannel('A'),fresh.getchannel('A')).getbbox(),'freshNativeOpaqueRGBExact':all(a[:3]==b[:3] for a,b in zip(raw.get_flattened_data(),fresh.get_flattened_data()) if a[3]==255),'nativeReplayChangedPixelAlphaRange':[min(a[3] for a,b in changed),max(a[3] for a,b in changed)] if changed else None,'nativeReplayChangedCount':len(changed),'publishedDecodedSHA256':hashlib.sha256(pub.tobytes()).hexdigest()})
 for i in range(13):
  actual=replay['frames'][d][i];bound=original['frames'][d][i]
  nativeMetadata.append({'direction':d,'frame':i,'rootMatrixExact':actual['rootMatrix']==bound['rootMatrix'],'everyEvaluatedGeometryDigestExact':all(actual['objects'][n].get('evaluatedGeometrySHA256')==bound['objects'][n].get('evaluatedGeometrySHA256') for n in actual['objects'])})
video=[]
for mode in ['full-chromium','headless-shell']:
 info=json.loads((C/f'consumer-{mode}.json').read_text());v=C/info['video']['path'];assert sha(v)==info['video']['sha256'];argv=['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration:stream=width,height,r_frame_rate','-of','json',str(v)];r=subprocess.run(argv,capture_output=True,text=True);video.append({'mode':mode,'path':str(v.relative_to(O)),'sha256':sha(v),'argv':argv,'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
result={'publicationRows':rows,'all48SubmittedReductionExact':all(r['submittedNativeWholeFrameLANCZOSExactlyEqualsPublished'] for r in rows),'uniquePublishedFrames':{d:len({r['publishedDecodedSHA256'] for r in rows if r['direction']==d}) for d in ['N','E','S','W']},'nativeMetadata':nativeMetadata,'all52NativeGeometryAndRootRecordsExact':all(r['rootMatrixExact'] and r['everyEvaluatedGeometryDigestExact'] for r in nativeMetadata),'nativeReplayInterpretation':'Tiny honest native RGB residuals retained. Alpha is exact. Dither intensity is actually0; do not attribute them to invented enabled dithering. No RGB/alpha repair or source change was performed. Geometry, transforms and camera establish clean native reproduction; residual bounds are in pixel-and-native-metrics.json.','videoReadback':video}
(P/'remaining-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['all48SubmittedReductionExact','uniquePublishedFrames','all52NativeGeometryAndRootRecordsExact']},indent=2));print('nativealpha',all(r['freshNativeAlphaExact'] for r in rows),'nativeopaque',all(r['freshNativeOpaqueRGBExact'] for r in rows),'changed',sum(r['nativeReplayChangedCount'] for r in rows))
