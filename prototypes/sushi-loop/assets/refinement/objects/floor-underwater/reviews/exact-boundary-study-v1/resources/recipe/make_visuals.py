import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'resources/python-pillow'))
from PIL import Image,ImageDraw,ImageChops,ImageStat
out=P/'comparison';out.mkdir(exist_ok=True)
variants=['original-filter-1p5','repair-filter-0p5'];numbers=[]
for direction in 'NESW':
 canvas=Image.new('RGB',(4*336,2*384),'#eee');draw=ImageDraw.Draw(canvas)
 for row,phase in enumerate((0,3)):
  for vi,variant in enumerate(variants):
   for ki,kind in enumerate(('native','independent')):
    col=vi*2+ki;f=P/variant/'consumer'/f'phone-{kind}-{direction}-{phase}-bg2.png';im=Image.open(f).convert('RGB');canvas.paste(im,(col*336+8,row*384+46));draw.text((col*336+8,row*384+8),f'{direction} phase {phase}: {variant}',fill='black');draw.text((col*336+8,row*384+24),kind+' / real phone / dark',fill='black')
 canvas.save(out/('phone-'+direction+'.png'))
 for phase in (0,3):
  name=direction+'-'+str(phase).zfill(3)+'.png';a=Image.open(P/variants[0]/'packed'/name).convert('RGBA');b=Image.open(P/variants[1]/'packed'/name).convert('RGBA');d=ImageChops.difference(a,b)
  numbers.append({'direction':direction,'phase':phase,'packedRGBAAbsMeanDifference':ImageStat.Stat(d).mean,'packedRGBAAbsDifferenceExtrema':d.getextrema(),'originalRightEdgeRGBA':{str(y):a.getpixel((255,y)) for y in (0,64,128,192,255)},'repairRightEdgeRGBA':{str(y):b.getpixel((255,y)) for y in (0,64,128,192,255)}})
(P/'rgb-comparison.json').write_text(json.dumps({'interpretation':'One common native filter change alters edge antialiasing. Geometry, palette/materials, lights, camera,512raw and full LANCZOS reduction unchanged. Existing dark grout dominates visible grid in both variants. Measured2/255 packed alpha leakage is separately established, not exaggerated as a dramatic phone seam.','samples':numbers},indent=2)+'\n')
