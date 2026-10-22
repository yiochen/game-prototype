from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).parent;C=R.parents[1]/'candidates/round-02'
for d in 'EW':
 pics=[C/'native'/f'idle-{d}'/'000.png']+[C/'native'/f'active-{d}'/f'{i:03}.png' for i in range(12)];ims=[Image.open(p).convert('RGBA') for p in pics];bs=[im.getchannel('A').getbbox() for im in ims];box=(min(x[0] for x in bs)-4,min(x[1] for x in bs)-4,max(x[2] for x in bs)+4,max(x[3] for x in bs)+4);w=box[2]-box[0];h=box[3]-box[1];sheet=Image.new('RGB',(3*w,5*(h+20)),(156,167,172));dr=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  xy=(i%3*w,i//3*(h+20));im=im.crop(box);sheet.paste(im,xy,im);dr.text((xy[0]+2,xy[1]+h),f'{d} idle' if i==0 else f'{d} active{i}',fill='black')
 sheet.save(R/'sheets'/f'native-detail-all13-{d}.png')
