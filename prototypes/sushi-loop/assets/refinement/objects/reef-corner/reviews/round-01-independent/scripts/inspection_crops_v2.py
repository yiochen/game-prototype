from pathlib import Path
from PIL import Image,ImageDraw
import json,math
p=Path(__file__).resolve().parents[1];e=p/'evidence';ledger=json.loads((e/'independent-consumer-ledger.json').read_text());P=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)];angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def bounds(d,port):
 a=angles[d];points=[]
 for w,z in P:
  x,y=(-.5,w) if port=='W' else (-w,.5);points.append((225+128*(math.cos(a)*x-math.sin(a)*y),377-128*(math.sin(a)*x+math.cos(a)*y)-89.6*z))
 return (math.floor(min(x for x,y in points))-12,math.floor(min(y for x,y in points))-12,math.ceil(max(x for x,y in points))+13,math.ceil(max(y for x,y in points))+13)
for mode in ledger['modes']:
 for group,ds in [('NE',['N','E']),('SW',['S','W'])]:
  rows=[]
  for d in ds:
   for port in ['W','N']:
    box=bounds(d,port);ims=[]
    for ctrl in ['native','individual']:
     rec=next(x for x in mode['cases'] if x['settings']['direction']==d and x['settings']['size']==128 and x['settings']['phase']==1 and x['settings']['control']==ctrl and x['settings']['bg']==1);im=Image.open(p/rec['screenshot']['path']).convert('RGB').crop(box);ims.append(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST))
    rows.append((d,port,ims,max(im.height for im in ims)+30))
  sheet=Image.new('RGB',(650,sum(r[3] for r in rows)),'#e7e4db');draw=ImageDraw.Draw(sheet);y=0
  for d,port,ims,h in rows:
   for k,im in enumerate(ims):sheet.paste(im,(k*325,y+25));draw.text((k*325+4,y+5),f'{d}/{port} '+['native','individual'][k]+' actual128p1 / x2',fill='#183a51')
   y+=h
  sheet.save(e/f"local-joins-v2-{mode['name']}-{group}.png")
a=json.loads((e/'extent-diagnostic/ledger.json').read_text())
for mode in a['modes']:
 sheet=Image.new('RGB',(900,300),'#e7e4db');draw=ImageDraw.Draw(sheet)
 for i,control in enumerate(['native','individual','equal-extent-diagnostic']):
  rec=next(x for x in mode['cases'] if x['settings']['size']==128 and x['settings']['control']==control);im=Image.open(p/rec['screenshot']['path']).convert('RGB').crop((160,385,300,510)).resize((280,250),Image.Resampling.NEAREST);sheet.paste(im,(300*i,35));draw.text((300*i+4,8),mode['name']+' '+control,fill='#183a51')
 sheet.save(e/f'extent-diagnostic/{mode["name"]}-N-local-v2.png')
(e/'inspection-crop-provenance.json').write_text(json.dumps({'v2':'Display-only registered world-coordinate crops from raw actual CSS screenshots; native/individual side by side, each crop2xNEAREST. All4/2ports/backends covered without sheet-row overlap.','supersededInspectionHelpers':['local-joins-full-chromium.png','local-joins-headless-shell.png','extent-diagnostic/full-chromium-N-local.png','extent-diagnostic/headless-shell-N-local.png'],'reason':'Initial sheet fixed row heights truncated some tall port crops; initial N diagnostic crop used wrong vertical presentation window and was blank. Raw controls untouched. V2 fixes presentation only, not data, art, masks or browser output.','productionChanged':False},indent=2)+'\n')
print('V2 inspection-only crops saved; raw evidence unchanged.')
