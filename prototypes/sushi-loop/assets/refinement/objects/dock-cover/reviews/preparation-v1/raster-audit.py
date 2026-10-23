from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageChops,ImageStat
import numpy as np
B=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');O=B/'prototypes/sushi-loop/assets/refinement/objects/dock-cover';R=O/'reviews/preparation-v1';P=B/'prototypes/sushi-loop/assets/production'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bg(im,c):
 out=Image.new('RGBA',im.size,c);out.alpha_composite(im);return out.convert('RGB')
report={'method':'All96 actual native2x fullframe images; original-layout5x3 atlases assembled without pixel warps. Published original atlas fullframes compared separately; downsample previews are diagnostic only.','frames':[],'streams':[]}
for clip in ['covered','uncover']:
 for d in ['N','E','S','W']:
  ims=[];atlas=Image.new('RGBA',(7360,4224));source=Image.open(P/f'sprites/dock-cover/{clip}-{d}.png').convert('RGBA');sc=Image.new('RGB',(4*368,3*376),(160,160,160));nc=sc.copy()
  for i in range(12):
   f=R/f'native-frames/{clip}-{d}/{i:03d}.png';im=Image.open(f).convert('RGBA');assert im.size==(1472,1408);ims.append(im);atlas.alpha_composite(im,((i%5)*1472,(i//5)*1408));sp=source.crop(((i%5)*1472,(i//5)*1408,(i%5+1)*1472,(i//5+1)*1408))
   a=np.array(im);sa=np.array(sp);al=a[:,:,3];partial=(al>0)&(al<128)
   diff=ImageChops.difference(im,sp);stats=ImageStat.Stat(diff)
   report['frames'].append({'clip':clip,'direction':d,'index':i,'path':str(f.relative_to(O/'reviews')),'sha256':sha(f),'alphaBounds':im.getbbox(),'nonzeroAlphaPixels':int((al>0).sum()),'partialAlphaPixels':int(((al>0)&(al<255)).sum()),'partialRedIndicators':int((partial&(a[:,:,0]>100)&(a[:,:,1]<12)&(a[:,:,2]<12)).sum()),'publishedCropRGBAEqual':im.tobytes()==sp.tobytes(),'publishedCropMeanAbsRGBA':stats.mean,'publishedCropExtrema':stats.extrema})
   for sh,img in [(nc,im),(sc,sp)]:
    sm=bg(img,(167,167,167,255)).resize((368,352),Image.Resampling.LANCZOS);sh.paste(sm,((i%4)*368,(i//4)*376+24));ImageDraw.Draw(sh).text(((i%4)*368+8,(i//4)*376+5),f'{clip}-{d} f{i:02}',fill='white')
  dest=R/'native-atlases'/f'{clip}-{d}.png';dest.parent.mkdir(exist_ok=True);atlas.save(dest)
  nc.save(R/f'contact-native-{clip}-{d}.png');sc.save(R/f'contact-published-{clip}-{d}.png')
  for color,name in [((246,241,225,255),'light'),((35,38,44,255),'dark')]:
   sh=Image.new('RGB',(4*368,3*376),color[:3])
   for i,im in enumerate(ims):sh.paste(bg(im,color).resize((368,352),Image.Resampling.LANCZOS),((i%4)*368,(i//4)*376+24))
   sh.save(R/f'contact-native-{clip}-{d}-{name}.png')
  report['streams'].append({'id':f'{clip}-{d}','atlasPath':str(dest.relative_to(O/'reviews')),'atlasSHA256':sha(dest),'atlasDimensions':[7360,4224],'rects':[[i%5*1472,i//5*1408,1472,1408] for i in range(12)],'publishedAtlasPath':str((P/f'sprites/dock-cover/{clip}-{d}.png').relative_to(B)),'publishedAtlasSHA256':sha(P/f'sprites/dock-cover/{clip}-{d}.png'),'fps':12,'loop':clip=='covered','uncoverTerminalHeld':clip=='uncover'})
# Family source evidence, native fullframe across all4, downsampled unmodified.
for clip in ['covered','uncover']:
 for i in [0,5,11]:
  sh=Image.new('RGB',(4*368,376),(167,167,167))
  for j,d in enumerate(['N','E','S','W']):
   p=R/f'native-family/{clip}-{d}-{i:02d}.png'
   if p.exists():sh.paste(bg(Image.open(p),(167,167,167,255)).resize((368,352),Image.Resampling.LANCZOS),(j*368,24));ImageDraw.Draw(sh).text((j*368+8,5),f'{clip}-{d} f{i}',fill='white')
  sh.save(R/f'family-{clip}-{i:02d}-sheet.png')
(R/'raster-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print('96 fullframe raster records;8 exact-layout native audit atlases')
