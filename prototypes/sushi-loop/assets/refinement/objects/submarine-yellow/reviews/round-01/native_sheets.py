from pathlib import Path
from PIL import Image,ImageDraw
import json
H=Path(__file__).resolve().parent;C=H/'resources/candidates/round-01';O=H/'visual/native';O.mkdir(exist_ok=True);j=json.loads((H/'pixel-audit.json').read_text());mapping=[]
for clip in ['idle','travel','impact','protection','dock-charging','dock-ready','upgraded-idle','upgraded-travel','upgraded-impact','upgraded-protection','upgraded-dock-charging','upgraded-dock-ready']:
 for pair in [('N','E'),('S','W')]:
  sheet=Image.new('RGB',(2016,1456),(135,143,151));dr=ImageDraw.Draw(sheet);cells=[]
  for di,d in enumerate(pair):
   for i in range(12):
    p=C/f'frames/{clip}-{d}/{i:03}.png';im=Image.open(p).convert('RGBA').crop((152,372,488,716));color=[(245,241,232),(160,168,176),(35,42,50)][i%3];bg=Image.new('RGBA',im.size,color+(255,));bg.alpha_composite(im);x=i%6*336;y=(di*2+i//6)*364;sheet.paste(bg.convert('RGB'),(x,y+20));dr.text((x+3,y+3),f'{clip} {d} {i:02} native1:1',fill='white');cells.append({'source':str(p.relative_to(H/'resources')),'column':i%6,'row':di*2+i//6,'background':color})
  p=O/(clip+'-'+''.join(pair)+'.png');sheet.save(p);mapping.append({'sheet':str(p.relative_to(H)),'cropNative':[152,372,488,716],'noRescale':True,'frames':cells})
# Independent native replay contact sheet, full native1:1 artwork crop.
rs=json.loads((H/'native-checks/independent-renders.json').read_text());sheet=Image.new('RGB',(1344,1092),(160,168,176));dr=ImageDraw.Draw(sheet)
for k,q in enumerate(rs['renders']):
 im=Image.open(H/q['path']).convert('RGBA').crop((152,372,488,716));bg=Image.new('RGBA',im.size,(160,168,176,255));bg.alpha_composite(im);x=(k//3)*336;y=(k%3)*364;sheet.paste(bg.convert('RGB'),(x,y+20));dr.text((x+3,y+3),q['clip']+' '+q['direction']+' '+str(q['frame']),fill='white')
sheet.save(H/'visual/independent-native-replays.png');(H/'native-sheet-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');print('native1:1 sheets',len(mapping),'frames',sum(len(x['frames']) for x in mapping))
