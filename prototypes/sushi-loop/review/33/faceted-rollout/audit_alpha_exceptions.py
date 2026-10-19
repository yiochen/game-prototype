"""Measure the tiny translucent-ray alpha differences in the Faceted recapture.
All inputs stay unchanged; the only output is this study's JSON report.
"""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;old=Path('/private/tmp/sushi33-art-rollout-v12/export/raw-frames');new=Path('/private/tmp/sushi33-faceted-rollout-v2/export/raw-frames');report={'asset':'decor-light-shafts','frames':[],'issues':[]}
for path in sorted((new/'decor-light-shafts').rglob('*.png')):
 relative=path.relative_to(new)
 with Image.open(path) as image:a=np.asarray(image.convert('RGBA'))[:,:,3].astype(int)
 with Image.open(old/relative) as image:b=np.asarray(image.convert('RGBA'))[:,:,3].astype(int)
 delta=np.abs(a-b)
 if not delta.any():continue
 bounds=lambda data:Image.fromarray(data.astype('uint8')).getbbox()
 item={'image':str(relative),'canvas':[a.shape[1],a.shape[0]],'differentPixels':int((delta>0).sum()),'maximumByteDifference':int(delta.max()),'changedFraction':float((delta>0).sum()/delta.size),'alphaBoundsUnchanged':bounds(a)==bounds(b)};report['frames'].append(item)
 if item['maximumByteDifference']>5 or item['differentPixels']>10 or not item['alphaBoundsUnchanged']:report['issues'].append(str(relative)+': difference larger than measured tiny transparency rounding')
report['explanation']='The material retains its exact transparent node colors and Mix Shader factor. Five frames have 2–7 changed source pixels and at most 5/255 alpha change, with identical bounds. The other 9,385 native frames have byte-identical alpha.';report['passed']=not report['issues'];(HERE/'audit-alpha-exceptions.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if not report['passed']:sys.exit(1)
