"""Verify baked compositor output against sRGB contrast and the original native pixels."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(sys.argv[1]);base=Path(sys.argv[2]);p=json.loads((root/'proof.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(root/p['nativeProject'])==p['nativeProjectSHA256'];assert sha(root/'source/create_native135.py')==p['sourceHash'];assert sha(base/'source/create_and_capture.py')==p['coreSourceSHA256']
assert len(p['captures'])==16
report={'nativeProjectSHA256':p['nativeProjectSHA256'],'contrastFactor':1.35,'capturePairs':[]}
for c in p['captures']:
 arrays={}
 for grade,data in c['images'].items():
  path=root/data['image'];assert sha(path)==data['sha256'];arrays[grade]=np.asarray(Image.open(path).convert('RGBA'));assert arrays[grade].shape==(3072,768,4)
 a=arrays['original'];b=arrays['native135'];original=np.asarray(Image.open(base/f"sprites/{c['profile']}/{c['id']}/{c['facing']}.png").convert('RGBA'))
 assert np.array_equal(a,original),(c['id'],c['facing'],'baseline pixels differ')
 assert np.array_equal(a[:,:,3],b[:,:,3]),(c['id'],c['facing'],'alpha changed')
 expected=np.clip((a[:,:,:3].astype(float)/255-.5)*1.35+.5,0,1)*255;mask=a[:,:,3]>250;error=np.abs(b[:,:,:3].astype(float)-expected)[mask]
 assert error.mean()<.6 and error.max()<1.5,(c['id'],c['facing'],error.mean(),error.max())
 report['capturePairs'].append({'id':c['id'],'facing':c['facing'],'maxAlphaDifference':0,'originalSourcePixelMatch':True,'meanOpaqueRGBError':float(error.mean()),'maxOpaqueRGBError':float(error.max())})
(root/'color-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: 16 native pairs; identical source/control pixels and alpha; RGB matches 135% within 8-bit rounding.')
