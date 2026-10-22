from pathlib import Path
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';P=O/'previews';P.mkdir(exist_ok=True)
views=[('S',(135,330,320,525)),('W',(64,330,249,525))];sheet=Image.new('RGB',(4*390,450),(225,229,232));dr=ImageDraw.Draw(sheet)
for i,(d,box) in enumerate(views):
 for j,rd in enumerate(['round-04','round-05']):
  im=Image.open(B/f'candidates/{rd}/published-static-{d}.png').convert('RGBA');cr=im.crop(box).resize((370,390),Image.Resampling.NEAREST);back=Image.new('RGBA',cr.size,(144,149,156,255));back.alpha_composite(cr);sheet.paste(back.convert('RGB'),((i*2+j)*390+8,52));dr.text(((i*2+j)*390+8,10),f'{d} {rd}: actual published crop / 2x nearest',fill='black');dr.text(((i*2+j)*390+8,30),'Same registration; native captures unchanged by presentation',fill='black')
sheet.save(P/'reviewed-round04-versus-round05-creases.png')
