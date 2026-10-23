from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil,numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Canonical frames are byte copies from reopening the final saved project at a relocated path.
for d in 'NESW':
 shutil.copyfile(O/'replay'/f'native-static-{d}.png',O/f'native-static-{d}.png')
 im=Image.open(O/f'native-static-{d}.png').convert('RGBA');im.resize((384,704),Image.Resampling.BOX).save(O/f'raw-static-{d}.png');shutil.copyfile(O/f'raw-static-{d}.png',O/f'atlas-static-{d}.png')
 Image.open(O/f'connected-native-{d}.png').convert('RGBA').resize((896,1216),Image.Resampling.BOX).save(O/f'connected-published-{d}.png')
for name,bg in {'light':'#f5f2e9','gray':'#808080','dark':'#182231'}.items():
 sh=Image.new('RGB',(920,430),bg);dr=ImageDraw.Draw(sh)
 for i,d in enumerate('NESW'):
  im=Image.open(O/f'raw-static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);sh.paste(im,(230*i+19,40),im);dr.text((230*i+16,12),d+' logical 128 / phone32',fill='white' if name=='dark' else '#243c52');ph=im.resize((48,88),Image.Resampling.BOX);sh.paste(ph,(230*i+178,330),ph)
 sh.save(O/f'four-view-{name}.png')
# Exact native root matrices and projection retained separately from publication measurements.
a=json.loads((O/'native-audit.json').read_text());camera=json.loads((B/'inputs/source-camera.json').read_text());camera['captureScale']=2;camera['nativeCaptureScale']=4;camera['nativeFrame']=[768,1408];camera['publishedFrame']=[384,704];camera['camera']['worldMatrix']=a['camera']['worldMatrix'];camera['camera']['projectionMatrix']=a['camera']['projectionMatrix'];camera['calibration']={k:[v/2 for v in vs] for k,vs in a['camera']['calibration'].items()};camera['nativeMeasurements']=a['camera'];camera['publicationSampling']='Uniform whole-canvas BOX reduction native4 to published2';camera['artStyle']={'revision':'soft-cobalt-rock-edge-round01','source':'round-01-settings.json','noPerViewTreatment':True};(B/'source/published-camera.json').write_text(json.dumps(camera,indent=2))
asset=json.loads((B/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['sourceScale']=2;asset['nativeCaptureScale']=4;asset['nativeFrame']=[768,1408];asset['publishedFrame']=[384,704];asset['measuredPhysicalBounds']=a['bounds'];asset['height']=1.17;asset['nominalHeight']=1.17;asset['artStyle']=camera['artStyle'];(B/'source/published-assetRecord.json').write_text(json.dumps(asset,indent=2))
rig=json.loads((B/'inputs/source-rig.json').read_text());rig['groundRootObject']=a['root'];rig['status']='four static native facings, no animation';(B/'source/rig.json').write_text(json.dumps(rig,indent=2))
provenance={'project':'source/round-01.blend','projectSHA256':sha(B/'source/round-01.blend'),'relocatedSHA256':sha(B/'source/relocated/round-01.blend'),'captureMethod':'Canonical exact native captures copied from render-only reopening of final saved .blend from relocated path. No authoring script used during canonical capture.','publication':'Pillow BOX whole-frame 50% reduction only','frames':[{ 'direction':d,'nativeSHA256':sha(O/f'native-static-{d}.png'),'publishedSHA256':sha(O/f'raw-static-{d}.png')} for d in 'NESW']}
(O/'capture-provenance.json').write_text(json.dumps(provenance,indent=2))
print('PACKAGED',O)
