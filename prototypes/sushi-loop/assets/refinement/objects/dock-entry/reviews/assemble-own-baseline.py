from pathlib import Path
from PIL import Image,ImageDraw
import math,json,hashlib
base=Path('prototypes/sushi-loop/assets');out=base/'refinement/objects/dock-entry/reviews';prod=base/'production';evid={'method':'Independent Pillow alpha_composite of exact published whole-frame assets at original registered roots;128logicalpx/world, common fixed640x640logical context canvas. Both painter orders are diagnostic; actual current consumer order is separately invoked and bound in own-consumer-order.json. Original catalog interaction is S.','assemblies':[]}
for f,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 floor=Image.open(prod/f'sprites/dock-floor/static-{f}.png').convert('RGBA');entry=Image.open(prod/f'sprites/dock-entry/static-{f}.png').convert('RGBA');fr=(640,640);er=(640+round(math.sin(a)*1.5*256),640+round(math.cos(a)*1.5*256));fp=(fr[0]-448,fr[1]-512);ep=(er[0]-192,er[1]-496)
 for order in ['entry-over-floor','floor-over-entry']:
  im=Image.new('RGBA',(1280,1280));items=[(floor,fp),(entry,ep)] if order=='entry-over-floor' else [(entry,ep),(floor,fp)]
  for sprite,p in items:im.alpha_composite(sprite,p)
  path=out/f'own-published-joined-{f}-{order}.png';im.save(path);evid['assemblies'].append({'path':path.name,'facing':f,'order':order,'floorRootNative':fr,'entryRootNative':er,'floorOriginNative':fp,'entryOriginNative':ep,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
sheet=Image.new('RGB',(4*390,3*390),(70,73,80));d=ImageDraw.Draw(sheet)
for col,f in enumerate('NESW'):
 for row,kind in enumerate(['native','entry-over-floor','floor-over-entry']):
  p=out/f'own-native-joined-{f}.png' if kind=='native' else out/f'own-published-joined-{f}-{kind}.png';im=Image.open(p).convert('RGBA').resize((360,360),Image.Resampling.LANCZOS);sheet.paste(im,(col*390+15,row*390+25),im);d.text((col*390+15,row*390+8),f+' '+kind,fill='white')
sheet.save(out/'own-joins-comparison.png');(out/'own-published-assembly-evidence.json').write_text(json.dumps(evid,indent=2)+'\n')
for kind in ['native','entry-over-floor','floor-over-entry']:
 p=out/'own-native-joined-S.png' if kind=='native' else out/f'own-published-joined-S-{kind}.png';im=Image.open(p).convert('RGBA');im.crop((480,920,800,1120)).resize((960,600),Image.Resampling.NEAREST).save(out/f'own-S-join-detail-{kind}.png')
sheet=Image.new('RGB',(832,1140),'white');d=ImageDraw.Draw(sheet)
for row,bg in enumerate(['#f2f0e6','#7b7b7b','#171b23']):
 for col,f in enumerate('NESW'):
  im=Image.open(out/f'own-native-entry-{f}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);panel=Image.new('RGBA',(208,380),bg);panel.alpha_composite(im,(8,22));sheet.paste(panel.convert('RGB'),(col*208,row*380));d.text((col*208+8,row*380+5),'Native '+f+' logical',fill='white' if row==2 else 'black')
sheet.save(out/'own-native-entry-backgrounds-logical.png')
