from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import numpy as np,json,hashlib
OUT=Path(__file__).resolve().parent;BASE=OUT/'resources/experiment';C=BASE/'candidates/round-03'
report={'packetSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'views':{},'independentPairs':{},'browserRaw':{}}
def im(p):return Image.open(p).convert('RGBA')
def stats(a,b):
 x=np.array(a).astype(np.int16);y=np.array(b).astype(np.int16);delta=np.abs(x-y);opaque=(x[:,:,3]==255)&(y[:,:,3]==255)
 return {'exactRGBA':a.tobytes()==b.tobytes(),'maxRGBA':delta.reshape(-1,4).max(0).tolist(),'meanRGBA':delta.mean((0,1)).tolist(),'alphaUnder255WhereReferenceOpaque':int(((y[:,:,3]<255)&(x[:,:,3]==255)).sum()),'zeroAlphaWhereReferenceOpaque':int(((y[:,:,3]==0)&(x[:,:,3]==255)).sum()),'minimumAlphaWhereReferenceOpaque':int(y[:,:,3][x[:,:,3]==255].min()),'bothOpaqueRGBMaximum':delta[:,:,:3][opaque].max(0).tolist(),'bothOpaqueRGBMean':delta[:,:,:3][opaque].mean(0).tolist()}
vectors={'N':(-1,0),'E':(0,-1),'S':(1,0),'W':(0,1)}
browser=json.loads((OUT/'independent-consumer-report.json').read_text())
sheet=Image.new('RGB',(1280,504),'#808080');draw=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
 n=im(C/f'native-static-{d}.png');r=im(OUT/f'native-replay/native-{d}.png');b=n.resize((384,704),Image.Resampling.BOX)
 report['views'][d]={'savedSourceReplay':stats(n,r),'BOXPublication':stats(b,im(C/f'published/static-{d}.png')),'atlasEqual':b.tobytes()==im(C/f'atlases/static-{d}.png').tobytes(),'rawEqual':b.tobytes()==im(C/f'raw/static-{d}/000.png').tobytes()}
 j=im(OUT/f'native-joined-reproduction/joined-{d}.png');report['views'][d]['joinedNativeReplay']=stats(im(C/f'joined-native-{d}.png'),j)
 x,y=vectors[d];positions={'end':(320+x*128,640+y*128),'middle':(320-x*128,640-y*128)}
 order=sorted(['middle','end'],key=lambda k:positions[k][1])
 pair=Image.new('RGBA',(640,960))
 for k in order:
  src=im(C/f'atlases/static-{d}.png') if k=='end' else im(BASE/f'inputs/approved-middle/published-{d}.png');root=positions[k];pair.alpha_composite(src,(root[0]-192,root[1]-512))
 pair.save(OUT/f'independent-pair-{d}.png')
 native2=j.resize((640,960),Image.Resampling.BOX)
 report['independentPairs'][d]=stats(native2,pair)
 cell=next(c for c in browser['cases'] if c['d']==d and c['pitch']==128 and c['phase']==[.25,.5] and c['bg']=='#808080')
 plan=cell['result']['plan'];expected=Image.new('RGBA',(plan['width'],plan['height']))
 for sprite in cell['sprites']:
  k='end' if sprite['key'].startswith('rock-wall-end') else 'middle';src=im(C/f'atlases/static-{d}.png') if k=='end' else im(BASE/f'inputs/approved-middle/published-{d}.png')
  expected.alpha_composite(src,(round((sprite['x']-plan['x'])*plan['scale']),round((sprite['y']-plan['y'])*plan['scale'])))
 raw=im(OUT/f'consumer-reproduction/raw-native-{d}.png');report['browserRaw'][d]=stats(expected,raw)
 # Crop-independent physical seam diagnostics: identify alpha undercoverage points.
 a=np.array(native2);bpa=np.array(pair);ys,xs=np.where((a[:,:,3]==255)&(bpa[:,:,3]<255))
 report['independentPairs'][d]['undercoverageLocations']=[[int(x),int(y),int(bpa[y,x,3])] for x,y in zip(xs,ys)]
 tile=j.resize((320,480),Image.Resampling.BOX);sheet.paste(tile,(i*320,24),tile);draw.text((i*320+5,5),d+' independent native join',fill='white')
sheet.save(OUT/'independent-joined-sheet.png')
(OUT/'independent-pixel-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'exactNativeReplay':{d:r['savedSourceReplay']['exactRGBA'] for d,r in report['views'].items()},'exactPublication':{d:r['BOXPublication']['exactRGBA'] for d,r in report['views'].items()},'exactJoinedReplay':{d:r['joinedNativeReplay']['exactRGBA'] for d,r in report['views'].items()},'browserRaw':report['browserRaw'],'independentPairs':report['independentPairs']},indent=2))
