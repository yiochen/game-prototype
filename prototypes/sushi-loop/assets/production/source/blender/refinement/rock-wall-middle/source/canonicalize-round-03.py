"""Copy untouched native render bytes from reopening the final saved project.
Run render-only replay first, then this helper, publication and measurements.
"""
from pathlib import Path
from shutil import copyfile
from PIL import Image
import json,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for d in 'NESW':
 src=O/'replay'/f'native-static-{d}.png';dst=O/f'native-static-{d}.png';copyfile(src,dst)
 rows.append({'direction':d,'nativeRenderSource':str(src.relative_to(B)),'publishedNativeCapture':str(dst.relative_to(B)),'sha256':sha(dst),'size':list(Image.open(dst).size)})
(B/'source/round-03-capture-provenance.json').write_text(json.dumps({'project':'source/round-03.blend','projectSHA256':sha(B/'source/round-03.blend'),'method':'Canonical captures are untouched native files from render-only reopen/replay of exact final saved project; copied byte-for-byte. No authoring code, paint, warp or pixel repair.','reason':'Native creation state and save/load round differently at a few 8-bit edge pixels. Canonicalizing from saved-project renders binds captures to the portable source.','frames':rows},indent=2))
