from pathlib import Path
from PIL import Image,ImageDraw
import json
B=Path(__file__).resolve().parents[2];out=B/'evidence';sheet=Image.new('RGB',(800,560),(216,225,227));d=ImageDraw.Draw(sheet);data=[]
for row,f in enumerate('NS'):
 im=Image.open(out/f'native-join-{f}-published.png').convert('RGBA');crop=im.crop((48,560,848,820));bg=Image.new('RGBA',crop.size,(122,137,148,255));bg.alpha_composite(crop);sheet.paste(bg.convert('RGB'),(0,row*280+20));d.text((5,row*280+4),f'{f} actual native repeated body / lossless source crop, ports at x320 and576',fill=(15,25,35));data.append({'direction':f,'source':f'native-join-{f}-published.png','crop':[48,560,848,820],'portOriginalX':[320,576],'method':'Lossless crop for inspection only; complete source frames retained; not modified art.'})
sheet.save(out/'collar-tone-context.png');(out/'collar-tone-context.json').write_text(json.dumps(data,indent=2)+'\n')
