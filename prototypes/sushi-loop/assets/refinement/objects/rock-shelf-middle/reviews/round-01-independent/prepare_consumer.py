import pathlib,sys,json,hashlib,shutil
sys.dont_write_bytecode=True
B=pathlib.Path(__file__).parent;sys.path.insert(0,str(B/'resources/python-library'))
from PIL import Image,ImageChops
E=B/'evidence';C=B.parent.parent/'candidates/round-01';comparison={}
for d in 'NESW':
 native=Image.open(E/f'reopened-{d}-4x.png').convert('RGBA');sealed=Image.open(C/f'native-{d}-4x.png').convert('RGBA');published=Image.open(C/f'static-{d}.png').convert('RGBA');reduced=native.resize((384,704),Image.Resampling.BOX);diff=ImageChops.difference(native,sealed);pdiff=ImageChops.difference(reduced,published)
 comparison[d]={'nativeMaxRGBA':[e[1] for e in diff.getextrema()],'nativeChangedPixels':sum(any(p) for p in diff.getdata()),'publishedMaxRGBA':[e[1] for e in pdiff.getextrema()],'publishedChangedPixels':sum(any(p) for p in pdiff.getdata()),'sealedBOXPublishesExactly':all(pair[1]==0 for pair in ImageChops.difference(sealed.resize((384,704),Image.Resampling.BOX),published).getextrema())}
 strip=Image.open(E/f'reopened-strip-{d}-4x.png').convert('RGBA');strip.resize((896,1216),Image.Resampling.BOX).save(E/f'joined-{d}-2x.png');sdiff=ImageChops.difference(strip,Image.open(C/f'native-strip-{d}-4x.png').convert('RGBA'));comparison[d]['stripNativeMaxRGBA']=[e[1] for e in sdiff.getextrema()];comparison[d]['stripChangedPixels']=sum(any(p) for p in sdiff.getdata())
 dest=B/'resources/published';dest.mkdir(exist_ok=True);shutil.copyfile(C/f'static-{d}.png',dest/f'static-{d}.png')
(E/'independent-replay-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
print(json.dumps(comparison,indent=2))
