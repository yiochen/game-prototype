from pathlib import Path
import json,math
from PIL import Image,ImageDraw
import numpy as np
H=Path(__file__).resolve().parent;C=H/'resources/candidates/round-01';O=H/'visual/contexts';O.mkdir(parents=True,exist_ok=True);audit=json.loads((C/'consumer-audit.json').read_text());mapping=[]
for record in audit['screenshots']:
 p=H/'resources'/record['path'];im=Image.open(p).convert('RGB');cases=[q for q in audit['cases'] if q['background']==record['cases'][0]['background'] and q['display']==record['cases'][0]['display'] and q['fraction']==record['cases'][0]['fraction']];display=cases[0]['display'];k=2 if display=='native' else 1;cw=565*k;ch=cases[0]['plan']['height']/(1 if k==2 else 2);stepy=ch+36;board=Image.new('RGB',(4*254,4*278),(115,122,130));dr=ImageDraw.Draw(board);cells=[]
 for i,q in enumerate(cases):
  x=8+(i%4)*(cw+8);y=122+(i//4)*stepy;can=im.crop((round(x),round(y),round(x+cw),round(y+ch)));a=np.array(can);mask=(a[:,:,0]>200)&(a[:,:,1]<130)&(a[:,:,2]<120)&(a[:,:,0]>a[:,:,1]*1.5);yy,xx=np.where(mask);assert len(xx)>30,p;cx=(xx.min()+xx.max())/2;cy=(yy.min()+yy.max())/2+8*k;rect=(round(cx-125*k),round(cy-125*k),round(cx+125*k),round(cy+125*k));patch=can.crop(rect)
  if k==2:patch=patch.resize((250,250),Image.Resampling.LANCZOS)
  bx=i%4*254;by=i//4*278;board.paste(patch,(bx,by+24));dr.text((bx+2,by+2),q['mode']+' '+q['direction'],fill='white');cells.append({'mode':q['mode'],'direction':q['direction'],'originalCanvasScreenRect':[x,y,cw,ch],'bodyCropRelativeToCanvas':rect,'nativeOverviewReduction':k==2})
 out=O/p.name;board.save(out);mapping.append({'source':record['path'],'output':str(out.relative_to(H)),'cases':cells,'method':'Actual unmodified Chrome screenshot crops; red pod color only locates inspection crop. No asset or consumer changes. Native overview reduction2x; source original remains bound.'})
# Phone/landscape images, all16 at their true screen display size, packed for inspection.
layouts=json.loads((H/'context-layout.json').read_text())
for name in ['phone','landscape']:
 im=Image.open(C/'consumer'/f'{name}.png').convert('RGB');board=Image.new('RGB',(4*254,4*278),(115,122,130));dr=ImageDraw.Draw(board);cells=[]
 for i,q in enumerate(layouts[name]):
  r=q['rect'];can=im.crop((round(r['x']),round(r['y']),round(r['x']+r['width']),round(r['y']+r['height'])));a=np.array(can);mask=(a[:,:,0]>200)&(a[:,:,1]<130)&(a[:,:,2]<120)&(a[:,:,0]>a[:,:,1]*1.5);yy,xx=np.where(mask);cx=(xx.min()+xx.max())/2;cy=(yy.min()+yy.max())/2+8;rect=(round(cx-125),round(cy-125),round(cx+125),round(cy+125));patch=can.crop(rect);bx=i%4*254;by=i//4*278;board.paste(patch,(bx,by+24));dr.text((bx+2,by+2),q['label'].split(' offset')[0],fill='white');cells.append({'label':q['label'],'canvasScreenRect':r,'bodyCropRelativeToCanvas':rect})
 out=O/f'{name}-all16-use-size.png';board.save(out);mapping.append({'source':str((C/'consumer'/f'{name}.png').relative_to(H/'resources')),'output':str(out.relative_to(H)),'cases':cells,'method':'Packed actual CSS screenshot crops at original screen pixels; no resize.'})
(H/'context-crop-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
# Exact native-source replay pixel comparisons, no equality-forcing retry.
rs=json.loads((H/'native-checks/independent-renders.json').read_text());out=[]
for q in rs['renders']:
 target=C/('frames/'+q['clip']+'-'+q['direction']+'/000.png' if q['frame']==1 else 'diagnostics/'+q['clip']+'-'+q['direction']+'-meaningful-half.png');a=np.array(Image.open(H/q['path']).convert('RGBA')).astype(np.int16);b=np.array(Image.open(target).convert('RGBA')).astype(np.int16);dif=np.abs(a-b);out.append({**q,'selected':str(target.relative_to(H/'resources')),'maximumRGBAChannelDifference':int(dif.max()),'differentPixels':int(np.any(dif,axis=2).sum()),'alphaDifferentPixels':int((dif[:,:,3]>0).sum())})
(H/'independent-render-comparison.json').write_text(json.dumps({'method':'Single saved-source replay, original EEVEE settings. Selected frames authoritative; no source mutation/postprocess/retry.','renders':out},indent=2)+'\n');print('context boards',len(mapping),'renders',[(q['clip'],q['direction'],q['maximumRGBAChannelDifference'],q['differentPixels']) for q in out])
