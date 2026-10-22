from PIL import Image,ImageChops
from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;B=O.parents[1];P=B/'candidates/round-03'
rep={'standalone':{},'joins':{},'consumerReplay':{},'crossSectionRawPixelChecks':{}}
for d in 'NESW':
 native=Image.open(P/f'native-static-{d}.png').convert('RGBA');pub=Image.open(P/f'published-static-{d}.png').convert('RGBA');atlas=Image.open(P/f'atlases/static-{d}.png').convert('RGBA');own=Image.open(O/f'replay/native-static-{d}.png').convert('RGBA')
 rep['standalone'][d]={'nativeSize':native.size,'publishedSize':pub.size,'atlasSize':atlas.size,'wholeBOXMatches':ImageChops.difference(native.resize((384,704),Image.Resampling.BOX),pub).getbbox() is None,'atlasMatchesWholeFrame':ImageChops.difference(pub,atlas).getbbox() is None,'independentNativePixelsEqual':ImageChops.difference(native,own).getbbox() is None,'nativeAlphaBounds':native.getbbox(),'publishedAlphaBounds':pub.getbbox()}
 a=Image.open(P/f'published-native-joined-{d}.png').convert('RGBA');b=Image.open(P/f'independent-published-joined-{d}.png').convert('RGBA');diff=ImageChops.difference(a,b);h=[diff.getchannel(i).histogram() for i in range(4)];opaqueMissing=sum(1 for x,y in zip(a.getchannel('A').getdata(),b.getchannel('A').getdata()) if x==255 and y<250)
 rep['joins'][d]={'size':a.size,'maxRGBAResidual':[e[1] for e in diff.getextrema()],'meanRGBAAbsoluteResidual':[sum(i*n for i,n in enumerate(q))/(a.width*a.height) for q in h],'nativeOpaqueIndependentAlphaBelow250':opaqueMissing,'ownJoinedReplay':'pending' if not (O/f'native-joins-replay/native-joined-{d}.png').exists() else ImageChops.difference(Image.open(O/f'native-joins-replay/native-joined-{d}.png').convert('RGBA'),Image.open(P/f'native-joined-{d}.png').convert('RGBA')).getbbox() is None}
 for q in (O/'consumer-replay').glob('*'+d+'-phase0.61-gray.png'):
  orig=P/'consumer'/q.name;rep['consumerReplay'][q.name]={'pixelEqual':ImageChops.difference(Image.open(q).convert('RGBA'),Image.open(orig).convert('RGBA')).getbbox() is None,'size':Image.open(q).size}
rows=json.loads((P/'side-alpha-cross-sections.json').read_text())['samples'];checked=0;errors=[];ground=[]
for row in rows:
 a=Image.open(P/f"published-native-joined-{row['direction']}.png").convert('RGBA');b=Image.open(P/f"independent-published-joined-{row['direction']}.png").convert('RGBA')
 for x in row['crossSection']:
  pixel=tuple(x['pixel']);aa=list(a.getpixel(pixel));bb=list(b.getpixel(pixel));checked+=1
  if aa!=x['nativeRGBA'] or bb!=x['independentRGBA'] or [bb[i]-aa[i] for i in range(4)]!=x['residualRGBA']:errors.append([row['direction'],row['port'],row['kind'],pixel])
 if 'ground' in row['kind']:ground.append({'direction':row['direction'],'port':row['port'],'alphaPairs':[(x['nativeRGBA'][3],x['independentRGBA'][3]) for x in row['crossSection']]})
rep['crossSectionRawPixelChecks']={'samplesChecked':checked,'mismatches':errors,'groundRows':ground}
(O/'pixel-verification.json').write_text(json.dumps(rep,indent=2)+'\n');print('PIXEL_VERIFICATION',json.dumps({k:v for k,v in rep.items() if k!='crossSectionRawPixelChecks'},indent=2))
