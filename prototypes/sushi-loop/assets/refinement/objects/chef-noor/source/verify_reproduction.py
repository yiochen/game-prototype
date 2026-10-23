from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-01';d=json.loads((C/'reproduction-manifest.json').read_text());raw=json.loads((C/'native-frames.json').read_text());lookup={(r['clip'],r['direction'],r['index']):r for r in raw};out=[]
for r in d['frames']:
 q=lookup[r['clip'],r['direction'],r['index']];a=Image.open(O/q['path']).convert('RGBA');b=Image.open(O/r['path']).convert('RGBA');diff=ImageChops.difference(a,b);out.append({**r,'nativeFrame':q['path'],'maxRGBA':[x[1] for x in diff.getextrema()],'differentPixels':sum(any(x) for x in diff.getdata())})
d['comparisons']=out;d['sourceMatchesRawExport']=d['sourceSHA256']==json.loads((C/'validation.json').read_text())['sourceSHA256'];d['alphaIdentical']=all(r['maxRGBA'][3]==0 for r in out);d['max8bitRGBDifference']=max(max(r['maxRGBA'][:3]) for r in out);(C/'reproduction-manifest.json').write_text(json.dumps(d,indent=2));v=json.loads((C/'validation.json').read_text());v['reproduction']='reproduction-manifest.json';v['reproductionComparison']={k:d[k] for k in ['sourceMatchesRawExport','alphaIdentical','max8bitRGBDifference']};v['ok']=v['ok'] and d['sourceMatchesRawExport'] and d['alphaIdentical'] and d['max8bitRGBDifference']<=2;(C/'validation.json').write_text(json.dumps(v,indent=2));print('REPRODUCTION',v['reproductionComparison'])
