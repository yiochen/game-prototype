from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;B=H.parents[1];O=B/'candidates/stage1-v6';V5=B/'candidates/stage1-v5';DIRS=['N','E','S','W'];BGS=[('light',(245,246,248)),('gray',(112,117,124)),('dark',(30,34,40))]
def composite(im,bg,size):
 im=im.convert('RGBA').resize(size,Image.Resampling.NEAREST);out=Image.new('RGBA',size,(*bg,255));out.alpha_composite(im);return out.convert('RGB')
for clip in ['dock-ready','upgraded-dock-ready']:
 sheet=Image.new('RGB',(1280,1224),(41,46,51));d=ImageDraw.Draw(sheet)
 for row,(name,bg) in enumerate(BGS):
  for col,di in enumerate(DIRS):
   im=Image.open(O/(clip+'-'+di+'.png'));sheet.paste(composite(im,bg,(320,384)),(col*320,row*408+24));d.text((col*320+8,row*408+5),di+' | v6 '+name+' / '+('PROVISIONAL' if clip.startswith('upgraded') else 'BODY'),fill='white')
 sheet.save(O/(clip+'-logical-backgrounds.png'))
half=Image.new('RGB',(640,1296),(41,46,51));d=ImageDraw.Draw(half)
for vr,clip in enumerate(['dock-ready','upgraded-dock-ready']):
 for br,(name,bg) in enumerate(BGS):
  row=vr*3+br
  for col,di in enumerate(DIRS):
   im=Image.open(O/(clip+'-'+di+'.png'));half.paste(composite(im,bg,(160,192)),(col*160,row*216+24));d.text((col*160+5,row*216+5),di+' / '+name+' / '+('PROVISIONAL' if vr else 'BODY'),fill='white')
half.save(O/'representatives-half-logical-backgrounds.png')
compare=Image.new('RGB',(1280,816),(41,46,51));d=ImageDraw.Draw(compare)
for row,folder in enumerate([V5,O]):
 for col,di in enumerate(DIRS):
  compare.paste(composite(Image.open(folder/('dock-ready-'+di+'.png')),(41,46,51),(320,384)),(col*320,row*408+24));d.text((col*320+8,row*408+5),di+' | '+('v5' if row==0 else 'v6')+' / MATCHED REGISTERED LOGICAL FRAME',fill='white')
compare.save(O/'v5-v6-glass-logical-comparison.png')
family=Image.new('RGB',(1280,1536),(41,46,51));d=ImageDraw.Draw(family)
for i,di in enumerate(DIRS):
 im=Image.open(O/('family-PROVISIONAL-'+di+'.png'));family.paste(composite(im,(41,46,51),(640,768)),((i%2)*640,(i//2)*768));d.text(((i%2)*640+8,(i//2)*768+8),di+' | v6 NATIVE FAMILY / PROVISIONAL EQUIPMENT',fill='white')
family.save(O/'stage1-family-four-view.png')
