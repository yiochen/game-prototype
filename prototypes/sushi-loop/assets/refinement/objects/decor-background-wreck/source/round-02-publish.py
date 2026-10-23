"""Uniform complete-canvas native4x->published2x only; atlas bytes are aliases."""
from pathlib import Path
from PIL import Image,ImageChops
import hashlib,json,shutil,sys
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-02'
proof=[];sheet=Image.new('RGBA',(384*4,704),(128,128,128,255))
for i,d in enumerate('NESW'):
 n=O/'native/static'/d/'000.png';im=Image.open(n).convert('RGBA');assert im.size==(768,1408)
 pub=im.resize((384,704),Image.Resampling.LANCZOS)
 f=O/'frames/static'/d/'000.png';f.parent.mkdir(parents=True,exist_ok=True);pub.save(f)
 a=O/'atlases'/f'static-{d}.png';a.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,a)
 z=P/'round-02-resources/consumer/sprites/decor-background-wreck'/f'static-{d}.png';z.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,z)
 sheet.alpha_composite(pub,(i*384,0))
 proof.append({'direction':d,'native':str(n.relative_to(B)),'nativeSHA256':hashlib.sha256(n.read_bytes()).hexdigest(),'nativeSize':[768,1408],'published':str(f.relative_to(B)),'publishedSHA256':hashlib.sha256(f.read_bytes()).hexdigest(),'publishedSize':[384,704],'atlas':str(a.relative_to(B)),'atlasSHA256':hashlib.sha256(a.read_bytes()).hexdigest(),'rect':[0,0,384,704],'nativeAlphaBounds':im.getchannel('A').getbbox(),'publishedAlphaBounds':pub.getchannel('A').getbbox(),'wholeCanvasLANCZOS':True,'cropFitWarpNudgeRecolorAlphaRGBRepair':False})
sheet.convert('RGB').save(O/'four-view-sheet.png')
(O/'publication-proof.json').write_text(json.dumps({'asset':'decor-background-wreck','method':'Pillow wholecanvas RGBA LANCZOS768x1408->384x704, no additional pixel operation; original singleframe atlas byte-copy','python':sys.version,'pillow':Image.__version__,'records':proof},indent=2)+'\n')
print('PUBLICATION COMPLETE',[(x['direction'],x['publishedAlphaBounds']) for x in proof])
