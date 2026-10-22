from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json
OUT=Path(__file__).resolve().parent
prov=json.loads((OUT/'resources/approved-middle/round-03-capture-provenance.json').read_text())
expected={f['direction']:f['sha256'] for f in prov['frames']}
metrics={}
sheet=Image.new('RGB',(320*4,480+26),'#808080');draw=ImageDraw.Draw(sheet)
for i,f in enumerate('NESW'):
 p=OUT/f'canonical-baseline/middle-native-{f}.png';native=Image.open(p).convert('RGBA')
 pub=native.resize((384,704),Image.Resampling.BOX)
 old=Image.open(OUT/f'resources/approved-middle/published-{f}.png').convert('RGBA')
 metrics[f]={'nativeSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'expectedCanonicalNativeSHA256':expected[f],'exactNativeBytesReplay':hashlib.sha256(p.read_bytes()).hexdigest()==expected[f],'exactBOXPublishedRGBA':pub.tobytes()==old.tobytes(),'publishedDiff':ImageChops.difference(pub,old).getextrema()}
 canonical=Image.open(OUT/f'resources/approved-middle/canonical-native-{f}.png').convert('RGBA')
 metrics[f]['exactCanonicalNativeRGBAReplay']=canonical.tobytes()==native.tobytes()
 metrics[f]['nativeRGBADiff']=ImageChops.difference(canonical,native).getextrema()
 oldinfo=Image.open(OUT/f'resources/approved-middle/canonical-native-{f}.png').info
 newinfo=Image.open(p).info
 metrics[f]['differentPNGMetadataKeys']=[k for k in set(oldinfo)|set(newinfo) if oldinfo.get(k)!=newinfo.get(k)]
 join=Image.open(OUT/f'canonical-baseline/joined-native-{f}.png').convert('RGBA').resize((320,480),Image.Resampling.BOX)
 sheet.paste(join,(i*320,26),join);draw.text((i*320+8,8),f'{f}: canonical light / original end',fill='white')
sheet.save(OUT/'joined-native-all4-diagnostic.png')
(OUT/'canonical-replay-comparison.json').write_text(json.dumps(metrics,indent=2)+'\n')
# Useful measurements exclude unassociated RGB under zero alpha.
source=json.loads((OUT/'source-replay-comparison.json').read_text())
for f in 'NESW':
 a=Image.open(OUT/f'resources/source-catalog/static-{f}.png').convert('RGBA')
 b=Image.open(OUT/f'source-baseline/published-LANCZOS-{f}.png').convert('RGBA')
 ap=list(a.getdata());bp=list(b.getdata());both=[(x,y) for x,y in zip(ap,bp) if x[3]==255 and y[3]==255]
 source[f]['bothOpaquePixels']=len(both)
 source[f]['opaqueRGBMaximumDelta']=max(abs(x[k]-y[k]) for x,y in both for k in range(3))
 source[f]['opaqueRGBMeanAbsoluteDelta']=sum(abs(x[k]-y[k]) for x,y in both for k in range(3))/(3*len(both))
 source[f]['alphaMaximumDelta']=max(abs(x[3]-y[3]) for x,y in zip(ap,bp))
(OUT/'source-replay-comparison.json').write_text(json.dumps(source,indent=2)+'\n')
