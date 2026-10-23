import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'resources/tools/python'))
from PIL import Image,ImageDraw,ImageChops,ImageStat
import pathlib,json
out=pathlib.Path(__file__).resolve().parent;rep=out/'source-replay'
def opened(p):return Image.open(p).convert('RGBA')
def put(im,xy,canvas,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,xy)
canvas=Image.new('RGBA',(800,400),'#e7e5dd');draw=ImageDraw.Draw(canvas)
for j,d in enumerate('NESW'):
 put(opened(rep/f'idle-{d}-01.png'),(j*200+4,28),canvas,(192,352));draw.text((j*200+8,8),f'Original native {d}',fill='#333333')
canvas.save(out/'original-native-all4-logical.png')
canvas=Image.new('RGBA',(800,950),'#324653');draw=ImageDraw.Draw(canvas)
for j,d in enumerate('NESW'):
 for i,f in enumerate([1,4,7,10]):
  # Same fixed crop for all frames; no fit/warp. Crop of native4x projected frame.
  im=opened(rep/f'active-{d}-{f:02}.png').crop((160,680,608,1160)).resize((179,192),Image.Resampling.LANCZOS)
  xy=(j*200+10,i*232+30);put(im,xy,canvas);draw.text((j*200+8,i*232+8),f'{d} active frame {f}',fill='white')
canvas.save(out/'original-active-phases-all4-detail.png')
orig=opened(out/'resources/experiment/inputs/original.png');replay=opened(rep/'idle-S-01.png').resize(orig.size,Image.Resampling.LANCZOS)
diff=ImageChops.difference(orig,replay);stat=ImageStat.Stat(diff)
canvas=Image.new('RGBA',(800,750),'#aaa79c');draw=ImageDraw.Draw(canvas);put(orig,(8,32),canvas);put(replay,(408,32),canvas);draw.text((8,8),'Frozen exported original 2x',fill='#222222');draw.text((408,8),'Native source replay 4x -> 2x',fill='#222222');canvas.save(out/'source-replay-parity.png')
(out/'source-replay/parity.json').write_text(json.dumps({'mode':'4x registered native capture, whole-frame Lanczos to existing 2x','rgbaMeanAbsoluteDifference':stat.mean,'rgbaExtrema':stat.extrema,'note':'Bounded visual source reproduction; exact original exported bytes retained separately. Replay sampling not a candidate approval.'},indent=2))
print(stat.mean,stat.extrema)
# Bounded old-source mounted diagnostic: same frozen main capture, one static pose.
canvas=Image.new('RGBA',(1280,430),'#bbc6c8');draw=ImageDraw.Draw(canvas)
for j,d in enumerate('NESW'):
 im=opened(out/'mounted-source-diagnostic'/f'old-source-mounted-{d}.png').resize((320,384),Image.Resampling.LANCZOS)
 put(im,(j*320,35),canvas);draw.text((j*320+8,8),f'{d}: OLD source, WRONG mount',fill='#222222')
canvas.save(out/'old-source-mounted-all4-diagnostic.png')
# Existing immutable exported atlases: all48 active cells and a logical-size loop.
canvas=Image.new('RGBA',(936,1280),'#d4dbdc');draw=ImageDraw.Draw(canvas);loops=[]
for di,d in enumerate('NESW'):
 atlas=opened(out/'resources/consumer/sprites/sub-hull-panels'/f'active-{d}.png')
 for fi in range(12):
  cell=atlas.crop(((fi%6)*384,(fi//6)*704,(fi%6+1)*384,(fi//6+1)*704))
  crop=cell.crop((86,336,302,584)).resize((130,149),Image.Resampling.LANCZOS)
  x=(fi%6)*156+8;y=di*320+(fi//6)*160+20;put(crop,(x,y),canvas);draw.text((x,y-16),f'{d} f{fi+1:02}',fill='#222222')
canvas.save(out/'original-exported-active-all48.png')
for fi in range(12):
 frame=Image.new('RGBA',(768,382),'#c6cece');draw=ImageDraw.Draw(frame)
 for di,d in enumerate('NESW'):
  atlas=opened(out/'resources/consumer/sprites/sub-hull-panels'/f'active-{d}.png');cell=atlas.crop(((fi%6)*384,(fi//6)*704,(fi%6+1)*384,(fi//6+1)*704)).resize((192,352),Image.Resampling.LANCZOS);put(cell,(di*192,24),frame);draw.text((di*192+6,6),f'{d}: f{fi+1:02}/12',fill='#222222')
 loops.append(frame)
loops[0].save(out/'original-exported-active-all4.apng',save_all=True,append_images=loops[1:],duration=1000/12,loop=0,format='PNG')
