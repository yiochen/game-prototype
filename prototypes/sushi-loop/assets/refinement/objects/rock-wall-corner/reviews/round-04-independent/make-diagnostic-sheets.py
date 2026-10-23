from PIL import Image,ImageDraw,ImageChops
from pathlib import Path
import numpy as np,json
O=Path(__file__).resolve().parent;P=O.parents[1]/'candidates/round-04'
can=Image.new('RGB',(800,500),'#dfe3e6');dr=ImageDraw.Draw(can)
for i,(d,box,lab) in enumerate([('S',(135,330,320,525),'S repeated crease striations'),('W',(64,330,249,525),'W repeated crease striations')]):
 im=Image.open(P/f'published-static-{d}.png').convert('RGBA').crop(box);bg=Image.new('RGBA',im.size,'#dfe3e6');bg.alpha_composite(im);bg=bg.convert('RGB').resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=10 if i==0 else 410;can.paste(bg,(x,80));dr.text((x,12),lab,fill='black');dr.text((x,35),'published coordinates '+str(box),fill='black');dr.text((x,56),'2x nearest diagnostic crop; asset unchanged',fill='black')
can.save(O/'crease-striation-crops.png')
result={};sheet=Image.new('RGB',(4*344,206),'#90959c');dr=ImageDraw.Draw(sheet)
for j,d in enumerate('NESW'):
 aa=Image.open(P/f'published-native-joined-{d}.png').convert('RGBA');bb=Image.open(P/f'independent-published-joined-{d}.png').convert('RGBA');a=np.asarray(aa).astype(int);b=np.asarray(bb).astype(int);diff=np.abs(a-b);mask=(a[:,:,3]>=250)&(b[:,:,3]>=250);rgb=diff[:,:,:3].max(axis=2);m=int(rgb[mask].max());ys,xs=np.where(mask&(rgb==m));x,y=int(xs[0]),int(ys[0]);result[d]={'maxRGBResidualWhenBothAlphaAtLeast250':m,'worstPixelXY':[x,y],'nativeRGBA':a[y,x].tolist(),'independentRGBA':b[y,x].tolist(),'pixelsAboveRGB16BothOpaque':int((mask&(rgb>16)).sum()),'allAlphaNative254IndependentBelow250':int(((a[:,:,3]>=254)&(b[:,:,3]<250)).sum())}
 for k,(name,im) in enumerate([('native',aa),('independent',bb)]):
  cr=im.crop((x-28,y-28,x+28,y+28));bg=Image.new('RGBA',cr.size,'#90959c');bg.alpha_composite(cr);sheet.paste(bg.convert('RGB').resize((168,168),Image.Resampling.NEAREST),(j*344+k*172,32));dr.text((j*344+k*172+3,8),d+' '+name+' RGBdelta'+str(m),fill='black')
(O/'opaque-residual-analysis.json').write_text(json.dumps(result,indent=2)+'\n');sheet.save(O/'opaque-residual-worst-crops.png')
# Verify the labelled submitted standalone and native/independent all4 sheets use the actual image bytes.
checks={}
colors={'light':(244,244,244,255),'gray':(144,149,156,255),'dark':(23,33,44,255)}
for bg,c in colors.items():
 for d,i in zip('NESW',range(4)):
  def flat(im):
   x=Image.new('RGBA',im.size,c);x.alpha_composite(im);return x.convert('RGB')
  expected=flat(Image.open(P/f'published-static-{d}.png').convert('RGBA'));actual=Image.open(P/f'previews/standalone-all4-{bg}.png').crop((i*384,28,i*384+384,28+704));checks[f'standalone/{bg}/{d}']=ImageChops.difference(expected,actual).getbbox() is None
  for kind,filename in [('native',f'native-joined-{d}.png'),('independent',f'independent-published-joined-{d}.png')]:
   expected=flat(Image.open(P/filename).convert('RGBA').resize((448,608),Image.Resampling.BOX));actual=Image.open(P/f'previews/{kind}-joins-all4-{bg}.png').crop((i*448,30,i*448+448,30+608));checks[f'{kind}/{bg}/{d}']=ImageChops.difference(expected,actual).getbbox() is None
(O/'sheet-pixel-verification.json').write_text(json.dumps(checks,indent=2)+'\n');print('VERIFIED_SHEET_CELLS',len(checks),all(checks.values()))
