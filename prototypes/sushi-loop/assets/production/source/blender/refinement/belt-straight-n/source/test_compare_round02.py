from PIL import Image,ImageChops,ImageDraw
import numpy as np,pathlib,json
P=pathlib.Path(__file__).resolve().parents[1]/'candidates/round-02'
for d in ['N','E']:
 a=Image.open(P/('hero-'+d+'.png')).convert('RGBA');out=Image.new('RGBA',(896,1216));offsets=[(256,0),(256,256),(256,512)] if d=='N' else [(0,256),(256,256),(512,256)]
 for pos in offsets:out.alpha_composite(a,pos)
 out.save(P/('assembled-'+d+'-00.png'));native=Image.open(P/('native-'+d+'-00.png')).convert('RGBA');arr=np.array(native,dtype=float);b=np.array(out,dtype=float);mask=(arr[:,:,3]>0)|(b[:,:,3]>0);delta=abs(arr-b);alpha=delta[:,:,3];rgb=abs(arr[:,:,:3]*(arr[:,:,3:]/255)-b[:,:,:3]*(b[:,:,3:]/255))
 print(d,'alpha',float(alpha.max()),float(alpha[mask].mean()),'rgb premult',float(rgb.max()),float(rgb[mask].mean()))
 diff=np.zeros(arr.shape,dtype='uint8');diff[:,:,:3]=np.clip(rgb*4,0,255).astype('uint8');diff[:,:,3]=255;Image.fromarray(diff).save(P/('diff-'+d+'-00.png'))
 sheet=Image.new('RGB',(896*2,1216),(120,125,128));sheet.paste(native,(0,0),native);sheet.paste(out,(896,0),out);sheet.resize((896,608)).save(P/('pair-'+d+'-00.png'))
