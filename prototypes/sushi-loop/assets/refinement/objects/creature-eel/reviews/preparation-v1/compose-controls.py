from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
sheet=Image.new('RGB',(1792,1072),'#8e9196');draw=ImageDraw.Draw(sheet)
for row,(clip,facing,frames) in enumerate([('normal','S',[1,13]),('caught','E',[12,24])]):
 for n,branch in enumerate(['','diagnostic-euler']):
  for k,fr in enumerate(frames):
   col=n*2+k;im=Image.open(P/branch/'captures'/clip/facing/f'{fr:03}.png').convert('RGBA').resize((448,512),Image.Resampling.LANCZOS);sheet.paste(im,(448*col,row*536+24),im);draw.text((448*col+4,row*536+6),f"{branch or 'untouched'} {clip} {facing} frame {fr}",fill='white')
sheet.save(P/'closure-hold-controls.png')
