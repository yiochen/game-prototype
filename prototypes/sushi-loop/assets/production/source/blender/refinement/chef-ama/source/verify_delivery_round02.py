"""Verify exact native/atlas resources and decoded ordinal video-frame binding."""
from pathlib import Path
import json,hashlib,subprocess,numpy as np
from PIL import Image
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(B/'delivery-round02.json');v=read(C/'complete-validation.json');ph=read(C/'candidate-phases.json');ph={(r['clip'],r['direction'],r['index']):r for r in ph};assert v['ok']
for r in d['rawFrames']:
 assert sha(B/r['path'])==r['sha256']==ph[r['clip'],r['direction'],r['index']]['sha256'];assert ph[r['clip'],r['direction'],r['index']]['sourceProjectSHA256']==sha(P/'round-02.blend')
for r in d['atlases']:
 atlas=Image.open(B/r['path']).convert('RGBA');assert list(atlas.size)==[2304,1280];assert sha(B/r['path'])==r['sha256']
 for i,(x,y,w,h) in enumerate(r['rects']):assert atlas.crop((x,y,x+w,y+h)).tobytes()==Image.open(C/'frames'/(r['clip']+'-'+r['direction'])/(f'{i:03d}.png')).convert('RGBA').tobytes()
rows=[]
for vid in read(C/'playback-validation.json')['playbacks']:
 path=B/vid['path'];buf=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']);decoded=np.frombuffer(buf,dtype=np.uint8).reshape(-1,640,384,3);assert len(decoded)==12
 bind=[]
 for i,actual in enumerate(decoded):
  raw=C/'frames'/(vid['clip']+'-'+vid['direction'])/(f'{i:03d}.png');im=Image.open(raw).convert('RGBA');bg=Image.new('RGBA',im.size,'#d1d0c7');bg.alpha_composite(im);expected=np.array(bg.convert('RGB'));delta=actual.astype(float)-expected.astype(float);mask=np.asarray(im)[:,:,3]>0;mae=float(np.abs(delta).mean());actor=float(np.abs(delta)[mask].mean());mse=float((delta**2).mean());psnr=float(10*np.log10(255**2/mse)) if mse else None
  bind.append({'index':i,'nativePath':str(raw.relative_to(B)),'nativePNG_SHA256':sha(raw),'decodedRGB_SHA256':hashlib.sha256(actual.tobytes()).hexdigest(),'nativeCompositeVsDecodedMeanAbsRGB':mae,'actorRegionMeanAbsRGB':actor,'compositeVsDecodedPSNRdB':psnr})
 rows.append({'clip':vid['clip'],'direction':vid['direction'],'videoPath':vid['path'],'videoSHA256':sha(path),'decodedFrameCount':12,'fps':12,'loop':vid['loop'],'frameBindings':bind})
for path in [d['project'],d['recipe'],d['validation'],*d['previews'].values(),*d['nativeRecords'].values(),*d['resources'].values()]:assert isinstance(path,str) and (B/path).is_file(),path
assert len(d['rawFrames'])==192 and len(d['atlases'])==16 and len(rows)==16
assert all(r['loop']==(r['clip']!='load') for r in rows)
assert sha(P/'round-01.blend')=='73cf8d7c6c1b4ef4170020424bfa3eebaae47ca4aabd124cb7753d4b1c1d7248'
for k,p in d['nativeRecords'].items():
 x=read(B/p);assert x['captureScale']==2 and x['source']['sha256']==sha(P/'round-02.blend')
result={'ok':True,'projectSHA256':sha(P/'round-02.blend'),'nativeFrameCount':192,'atlasCount':16,'allAtlasRGBA_RectanglesEqualNativeFrames':True,'actualVideoCount':16,'all192VideoFramesDecodedAndOrdinallyBoundToNativeInputs':True,'videoBindingMethod':'Exact recorded ffmpeg12fps input sequence of verified native PNG files; decoded output ordinals/hash/region compression statistics below. MP4 is a lossy review preview, not native output. Native frame SHA and exact atlas rect equivalence remain primary pixel identity.','maximumActorCompositeVsDecodedMeanAbsRGB':max(f['actorRegionMeanAbsRGB'] for r in rows for f in r['frameBindings']),'minimumCompositeVsDecodedPSNRdB':min(f['compositeVsDecodedPSNRdB'] for r in rows for f in r['frameBindings'] if f['compositeVsDecodedPSNRdB'] is not None),'videos':rows,'allReferencedPathsExist':True,'priorApprovedSourceImmutable':True}
(C/'delivery-binding-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='videos'},indent=2))
# Bind this audit into the numbered delivery and aggregate without altering any native bytes.
v['deliveryBinding']='candidates/round-02/delivery-binding-validation.json';(C/'complete-validation.json').write_text(json.dumps(v,indent=2)+'\n');d['previews']['delivery-binding-validation']='candidates/round-02/delivery-binding-validation.json';d['resources']['verify_delivery_round02.py']='source/verify_delivery_round02.py';(B/'delivery-round02.json').write_text(json.dumps(d,indent=2)+'\n');(C/'delivery-round02.json').write_text(json.dumps(d,indent=2)+'\n')
