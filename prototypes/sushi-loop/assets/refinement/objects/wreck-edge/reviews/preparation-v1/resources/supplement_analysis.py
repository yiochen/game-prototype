from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json
BASE=Path(__file__).resolve().parent.parent
sheet=Image.new('RGB',(1800,2070),(58,69,82));draw=ImageDraw.Draw(sheet);mapping=[];y=0
for d in 'NESW':
 im=Image.open(BASE/'baseline/mixed-native'/f'{d}.png').convert('RGBA');thumb=im.resize((im.width//2,im.height//2),Image.Resampling.LANCZOS);ph=im.resize((im.width//8,im.height//8),Image.Resampling.LANCZOS)
 for j,(label,bg) in enumerate([('light',(238,238,238)),('gray',(128,128,128)),('dark',(21,25,35))]):
  x=j*600+8;draw.text((x,y+4),d+' / '+label+' logical128 + phone32',fill='white')
  for view,off in [(thumb,0),(ph,thumb.width+10)]:
   dest=Image.new('RGB',view.size,bg);dest.paste(view,mask=view.getchannel('A'));sheet.paste(dest,(x+off,y+24))
  mapping.append({'source':'baseline/mixed-native/'+d+'.png','background':label,'logicalPanel':[x,y+24,thumb.width,thumb.height],'phonePanel':[x+thumb.width+10,y+24,ph.width,ph.height],'sourceCompleteFrame':True,'uniformScales':[.5,.125]})
 y+=thumb.height+38
sheet.save(BASE/'baseline/native-mixed-use-size-sheet-v2.png')
stats=[];refs=[]
for c in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 paths=[BASE/'consumer-baseline'/(m+'-'+c+'-css.png') for m in ['full-chromium','bundled-headless-shell']];ims=[Image.open(p).convert('RGBA') for p in paths];delta=ImageChops.difference(*ims);stats.append({'case':c,'sameSize':ims[0].size==ims[1].size,'maxRGBA':[e[1] for e in delta.getextrema()],'differentPixels':sum(any(p) for p in delta.get_flattened_data()),'interpretation':'Actual CSS mode residual retained; separate from shared native canvas equivalence and visible join bar.'})
for d in 'NESW':
 paths=[BASE/'consumer-baseline'/('full-chromium-logical128-integer-'+d+'-'+k+'.png') for k in ['independent','native-control']];ims=[Image.open(p).convert('RGBA') for p in paths];delta=ImageChops.difference(*ims);refs.append({'direction':d,'maxRGBA':[e[1] for e in delta.getextrema()],'differentPixels':sum(any(p) for p in delta.get_flattened_data()),'interpretation':'Raw independent source+middle baseline versus connected native; no pixel repair or color correction.'})
(BASE/'baseline-supplement.json').write_text(json.dumps({'sheet':'baseline/native-mixed-use-size-sheet-v2.png','mapping':mapping,'supersedes':'baseline/native-mixed-use-size-sheet.png has overlapping sheet rows and clipped phone panels; it grants no full-frame inspection coverage and is retained as an honest failed evidence layout. v2 only changes sheet layout; all underlying native captures remain unchanged.','consumerCSSCrossMode':stats,'consumerNativeVsControl':refs},indent=2)+'\n');print(json.dumps({'CSS':stats,'nativeControl':refs},indent=2))
