import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json, hashlib
from PIL import Image,ImageChops,ImageDraw
B=Path(__file__).resolve().parent;O=B.parent.parent;E=B/'evidence';P=O/'candidates/round-02'
report=json.loads((E/'independent-ground-and-strip-audit.json').read_text());records=[]
for item in report['strips']:
 a=Image.open(E/item['path']).convert('RGBA');b=Image.open(P/'native'/('three-joined-'+item['direction']+'.png')).convert('RGBA');assert a.size==b.size
 d=ImageChops.difference(a,b);ds=list(d.getdata());mx=[max(p[k] for p in ds) for k in range(4)];changed=sum(any(p) for p in ds)
 records.append({'direction':item['direction'],'dimensions':list(a.size),'differentDecodedPixels':changed,'maxRGBAChannelDelta':mx,'alphaExact':mx[3]==0,'savedSourceNativePath':item['path'],'packetNativePath':'native/three-joined-'+item['direction']+'.png'})
# Retain residuals truthfully rather than requiring/replacing exact native-strip pixels.
out={'sourceSHA256':report['sourceSHA256'],'ground':{k:v for k,v in report['finiteGround'].items() if k!='triangles'},'allMaterialObjectWorldAnimationAbsent':True,'nativeStrips':records,'heroVersusStripReplayDistinction':'All4 heroes decodedRGBA exact. The independent strip replay deltas are separately recorded here; no output is repaired. Actual consumer replay used exact submitted packet PNGs.','scope':'Saved native source only, no construction run or .blend save.'}
(E/'independent-support-and-strip-findings.json').write_text(json.dumps(out,indent=2)+'\n')
# Real replay pixels at the fractional consumer case also declared by the packet.
sheet=Image.new('RGB',(1536,768),'#eeede6');draw=ImageDraw.Draw(sheet);mapped=[]
for row,backend in enumerate(['full-chrome-155','shell-153']):
 data=json.loads((E/(backend+'-report.json')).read_text())
 for col,direction in enumerate(['N','E','S','W']):
  rec=next(r for r in data['records'] if r['direction']==direction and r['zoom']==1 and r['rootPhaseLogical']==.25 and r['panPhaseOutput']==.75)
  for side,kind in enumerate(['independent','native-actual']):
   image=Image.open(E/rec['images'][kind]).convert('RGBA');box=(40,220,432,456) if direction in ['N','S'] else (160,220,312,512)
   crop=image.crop(box);crop.thumbnail((188,338),Image.Resampling.LANCZOS) if crop.width>188 else None
   # Presentation thumbnail is uniform only; exact input paths/rectangles remain bound.
   x=col*384+side*192;y=row*384+38;bg=Image.new('RGBA',crop.size,'#7f888d');bg.alpha_composite(crop);sheet.paste(bg.convert('RGB'),(x,y))
   draw.text((x,row*384+5),backend+' '+direction,fill='#243946');draw.text((x,row*384+20),kind,fill='#243946')
   mapped.append({'input':rec['images'][kind],'sourceRectangle':list(box),'displayDimensions':list(crop.size)})
sheet.save(E/'own-actual-fractional-replay-sheet.png')
(E/'own-actual-fractional-replay-sheet.json').write_text(json.dumps({'rootPhaseLogical':.25,'panPhaseOutput':.75,'comparisonOnlyDiagnosticsOmitted':True,'inputs':mapped},indent=2)+'\n')
print(json.dumps(out))
