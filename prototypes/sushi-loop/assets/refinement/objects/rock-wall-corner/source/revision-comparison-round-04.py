from pathlib import Path
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';P=O/'previews';P.mkdir(exist_ok=True)
views=[('N','backing patch',(64,230,200,430)),('E','mirrored backing',(184,230,320,430)),('S','exterior transition',(64,450,320,610)),('W','exterior transition',(64,450,320,610))]
sheet=Image.new('RGB',(4*560,470),(225,229,232));dr=ImageDraw.Draw(sheet)
for i,(d,label,box) in enumerate(views):
 for j,rd in enumerate(['round-03','round-04']):
  im=Image.open(B/f'candidates/{rd}/published-static-{d}.png').convert('RGBA');cr=im.crop(box);cr.thumbnail((264,400),Image.Resampling.NEAREST);bg=Image.new('RGBA',cr.size,(144,149,156,255));bg.alpha_composite(cr);sheet.paste(bg.convert('RGB'),(i*560+j*280+8,52));dr.text((i*560+j*280+8,10),f'{d} {rd}',fill='black');dr.text((i*560+8,30),f'{label} - same registered crop',fill='black')
sheet.save(P/'reviewed-round03-versus-round04.png')
