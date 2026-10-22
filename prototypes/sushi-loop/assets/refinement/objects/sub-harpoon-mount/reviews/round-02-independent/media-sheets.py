from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
R=Path(__file__).parent;E=R.parents[1];C=E/'candidates/round-02';out=R/'sheets';out.mkdir(exist_ok=True)
colors={'light':(245,240,230),'gray':(156,167,172),'dark':(28,39,50)};entries=[];atlas=[];full=[]
for d in 'NESW':
 media=[('idle',1,C/'published'/f'idle-{d}'/'000.png')]+[('active',i+1,C/'published'/f'active-{d}'/f'{i:03}.png') for i in range(12)]
 for tone,bg in colors.items():
  sh=Image.new('RGB',(7*192,2*372),bg);dr=ImageDraw.Draw(sh)
  for i,(clip,f,p) in enumerate(media):
   im=Image.open(p).convert('RGBA');im=im.resize((192,352),Image.Resampling.BOX);xy=(i%7*192,i//7*372);sh.paste(im,xy,im);dr.text((xy[0]+3,xy[1]+353),f'{d} {clip} {f}',fill='white' if tone=='dark' else 'black')
  dst=out/f'logical-all13-{d}-{tone}.png';sh.save(dst);entries.append({'sheet':str(dst.relative_to(R)),'members':[str(x[2].relative_to(C)) for x in media],'method':'Full registered192x352 logical frames; no fitting. Published2x complete frame -> BOXlogical1x, only neutral background compositing.'})
 # Native inspected at original resolution through a common transparent-padding crop, no fitting.
 paths=[C/'native'/f'{c}-{d}'/f'{f-1:03}.png' for c,f,_ in media];images=[Image.open(p).convert('RGBA') for p in paths];bs=[im.getchannel('A').getbbox() for im in images];box=(min(b[0] for b in bs)-4,min(b[1] for b in bs)-4,max(b[2] for b in bs)+4,max(b[3] for b in bs)+4);w=box[2]-box[0];h=box[3]-box[1]
 sh=Image.new('RGB',(7*w,2*(h+20)),colors['gray']);dr=ImageDraw.Draw(sh)
 for i,im in enumerate(images):
  im=im.crop(box);xy=(i%7*w,i//7*(h+20));sh.paste(im,xy,im);dr.text((xy[0]+2,xy[1]+h),f'{d} {media[i][0]} {media[i][1]}',fill='black')
 dst=out/f'native-all13-{d}.png';sh.save(dst);entries.append({'sheet':str(dst.relative_to(R)),'members':[str(p.relative_to(C)) for p in paths],'commonCrop':box,'method':'Native4x crop of common transparent padding only, retained native pixel dimensions for detail inspection; all original complete dimensions/alpha bounds checked separately.'})
 for clip,count in [('idle',1),('active',12)]:
  at=Image.open(C/'atlases'/f'{clip}-{d}.png').convert('RGBA')
  for f in range(count):
   p=C/'published'/f'{clip}-{d}'/f'{f:03}.png';im=Image.open(p).convert('RGBA');rect=((f%6)*384,(f//6)*704,(f%6+1)*384,(f//6+1)*704) if count>1 else (0,0,384,704);native=Image.open(C/'native'/f'{clip}-{d}'/f'{f:03}.png').convert('RGBA');box=im.getchannel('A').getbbox();full.append({'published':str(p.relative_to(C)),'size':im.size,'alphaBounds':box,'canvasClear':box[0]>0 and box[1]>0 and box[2]<384 and box[3]<704,'wholeBOXNativeToPublishedExact':native.resize(im.size,Image.Resampling.BOX).tobytes()==im.tobytes()});atlas.append({'atlas':f'atlases/{clip}-{d}.png','frame':f,'exactPublishedRGBA':at.crop(rect).tobytes()==im.tobytes()})
for tone,bg in colors.items():
 sh=Image.new('RGB',(13*48,4*108),bg);dr=ImageDraw.Draw(sh)
 for y,d in enumerate('NESW'):
  for x,(clip,f) in enumerate([('idle',1)]+[('active',i+1) for i in range(12)]):
   im=Image.open(C/'published'/f'{clip}-{d}'/f'{f-1:03}.png').convert('RGBA').resize((48,88),Image.Resampling.LANCZOS);xy=(x*48,y*108);sh.paste(im,xy,im);dr.text((xy[0]+1,xy[1]+88),f'{d}{x}',fill='white' if tone=='dark' else 'black')
 sh.save(out/f'phone32-all52-{tone}.png')
# Native mounted views: source full-frame BOX to logical whole frame; all52 phases and all4 facings.
for d in 'NESW':
 sh=Image.new('RGB',(7*320,2*408),colors['gray']);dr=ImageDraw.Draw(sh);members=[]
 for i,(clip,f) in enumerate([('idle',1)]+[('active',n+1) for n in range(12)]):
  p=C/'mounted'/f'{clip}-{d}'/f'{f-1:03}.png';im=Image.open(p).convert('RGBA').resize((320,384),Image.Resampling.BOX);xy=(i%7*320,i//7*408);sh.paste(im,xy,im);dr.text((xy[0]+1,xy[1]+385),f'{d} {clip} {f}; static main / other gear provisional',fill='black');members.append(str(p.relative_to(C)))
 dst=out/f'mounted-all13-{d}.png';sh.save(dst);entries.append({'sheet':str(dst.relative_to(R)),'members':members,'method':'Whole native mounted frame640x768 -> logical320x384; context static/provisional.'})
(R/'media-coverage.json').write_text(json.dumps({'pathBase':'candidate paths relative to candidates/round-02; sheet paths relative to reviews/round-02-independent','sheetMembers':entries,'fullFrameChecks':full,'atlasChecks':atlas},indent=2)+'\n')
print('FULL',len(full),'BOX',all(x['wholeBOXNativeToPublishedExact'] for x in full),'atlas',all(x['exactPublishedRGBA'] for x in atlas),'sheets',len(entries))
