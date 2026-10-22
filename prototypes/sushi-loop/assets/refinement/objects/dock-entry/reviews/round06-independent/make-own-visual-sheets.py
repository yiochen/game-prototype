from pathlib import Path
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;D=O/'diagnostics';D.mkdir(exist_ok=True);P=O/'browser-replay'
for bg in ['light','gray','dark']:
 sheet=Image.new('RGB',(1560,844),'#bbb')
 for i,f in enumerate('NESW'):sheet.paste(Image.open(P/f'viewport-390x844-{f}-{bg}.png').convert('RGB'),(390*i,0))
 sheet.save(D/f'portrait-all4-{bg}.png')
 sheet=Image.new('RGB',(1688,780),'#bbb')
 for i,f in enumerate('NESW'):sheet.paste(Image.open(P/f'viewport-844x390-{f}-{bg}.png').convert('RGB'),(844*(i%2),390*(i//2)))
 sheet.save(D/f'landscape-all4-{bg}.png')
# Keep actual phone screenshot scale; vertically crop four common quarter-phase contact areas to avoid distant empty deck.
for bg in ['light','gray','dark']:
 sheet=Image.new('RGB',(4*576,4*120),'#a7a7a7');dr=ImageDraw.Draw(sheet)
 for col,f in enumerate('NESW'):
  im=Image.open(P/f'pair-{f}-{bg}-phone.png').convert('RGB')
  # each pair row has label24+stage320 atzoom.5; retain lower or upper contact region at its actual size.
  for row in range(4):
   top=24+row*344;yy={'N':45,'S':230,'E':120,'W':120}[f];crop=im.crop((0,top+yy,576,top+yy+110));sheet.paste(crop,(col*576,row*120+10));dr.text((col*576,row*120),f+' phase'+str([0,.25,.5,.75][row]),fill='black')
 sheet.save(D/f'phone-contacts-all4-{bg}.png')
