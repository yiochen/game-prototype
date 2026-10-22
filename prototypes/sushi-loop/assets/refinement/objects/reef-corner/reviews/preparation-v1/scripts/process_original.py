from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,sys,PIL
p=Path(__file__).resolve().parents[1];out=p/'evidence/original-replay'
canvas=Image.new('RGBA',(4*384,704),(96,101,110,255))
rows=[]
for i,f in enumerate(['N','E','S','W']):
    n=Image.open(out/f'native4x-{f}.png').convert('RGBA');im=n.resize((384,704),Image.Resampling.LANCZOS);im.save(out/f'published2x-{f}.png');canvas.alpha_composite(im,(384*i,0));ImageDraw.Draw(canvas).text((384*i+8,8),f,fill='white')
    rows.append({'facing':f,'nativeAlphaBounds':n.getchannel('A').getbbox(),'publishedAlphaBounds':im.getchannel('A').getbbox()})
canvas.save(p/'evidence/original-replay-sheet.png')
src=Image.open(p/'resources/object/original.png').convert('RGBA');rep=Image.open(out/'published2x-S.png').convert('RGBA')
a=list(src.getdata());b=list(rep.getdata());d=[tuple(abs(x-y) for x,y in zip(x1,y1)) for x1,y1 in zip(a,b)]
(p/'evidence/original-replay-comparison.json').write_text(json.dumps({'sourceSnapshot':str(src.size),'replaySize':str(rep.size),'differentDecodedPixels':sum(any(x) for x in d),'maxChannels':[max(x[c] for x in d) for c in range(4)],'note':'Historical current-Blender replay retained without normalization; exact equality is diagnostic, not art or seam approval.','frames':rows,'python':sys.version,'Pillow':PIL.__version__},indent=2)+'\n')
