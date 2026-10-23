from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];out=P/'baseline-diagnostics';out.mkdir(exist_ok=True)
res=json.loads((P/'consumer-baseline/results.json').read_text());case=next(r for r in res['cases']if r['mode']=='full-chromium' and r['id']=='logical128-integer');summ=[]
for i in range(0,len(case['nativeCanvases']),2):
 fa,fb=case['nativeCanvases'][i:i+2];a=Image.open(P/'consumer-baseline'/fa).convert('RGBA');b=Image.open(P/'consumer-baseline'/fb).convert('RGBA');x=np.array(a).astype(int);y=np.array(b).astype(int);d=abs(x-y);bg=np.array([128,128,128]);av=np.round(x[:,:,:3]*x[:,:,3:4]/255+bg*(1-x[:,:,3:4]/255)).astype(int);bv=np.round(y[:,:,:3]*y[:,:,3:4]/255+bg*(1-y[:,:,3:4]/255)).astype(int);vis=abs(av-bv);mask=(vis>20).any(2);ys,xs=np.nonzero(mask);name=fa.split('logical128-integer-')[1].replace('-independent.png','')
 info={'case':name,'fullMaxRGBA':d.reshape(-1,4).max(0).tolist(),'over20VisiblePixels':int(mask.sum()),'visibleOver20Bounds':None if not len(xs)else[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]}
 diff=np.zeros_like(x,dtype=np.uint8);diff[:,:,:3]=np.clip(vis*8,0,255);diff[:,:,3]=255
 sheet=Image.new('RGB',(a.width*3,a.height+24),(45,50,55));dr=ImageDraw.Draw(sheet)
 for j,(label,im)in enumerate([('individual current consumer',a),('actual native L control',b),('actual visible diff x8',Image.fromarray(diff))]):
  canvas=Image.new('RGB',im.size,(128,128,128));canvas.paste(im,mask=im.getchannel('A'));sheet.paste(canvas,(a.width*j,24));dr.text((a.width*j+4,4),label,fill='white')
 sheet.save(out/(name+'-comparison.png'));summ.append(info)
(out/'differences.json').write_text(json.dumps({'scope':'Original corner baseline only, no candidate judgment','fullFrameDifferenceSheets':summ,'interpretation':'RGB/alpha are honest fullframe comparisons. Bright sheet differences require independent localization; do not automatically classify a highRGB delta as broad finite-light. Candidate must be examined at both actual contacts regardless of global numerical equality.'},indent=2)+'\n')
print(json.dumps(summ,indent=2))
