from pathlib import Path
from PIL import Image
import json,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-02'
def diff(a,b):
 d=np.abs(np.asarray(a).astype(np.int16)-np.asarray(b).astype(np.int16));return {'equal':not bool(d.any()),'maxAbs':int(d.max()),'meanAbs':float(d.mean()),'changedPixels':int(np.any(d,axis=2).sum())}
bgs={'light':(246,242,232,255),'gray':(112,118,128,255),'dark':(18,26,42,255)};out=[]
for size,scale in [('logical',1),('phone',.5)]:
 w,h=int(320*scale),int(448*scale)
 for bg,col in bgs.items():
  actual={};expected=[]
  for mode in ['full-chromium','headless-shell']:
   im=Image.open(C/'consumer'/mode/f'candidate-{size}-{bg}.png').convert('RGB');actual[mode]=[im.crop((j*w,k*(h+20)+20,(j+1)*w,k*(h+20)+20+h))for k in range(3)for j in range(4)]
  for clip in ['windup','active','recovery']:
   for d in ['N','E','S','W']:
    src=Image.open(C/'published'/clip/d/'005.png').convert('RGBA');guard=Image.new('RGBA',(642,898));guard.paste(src,(1,1));filtered=guard.resize((round(321*scale),round(449*scale)),Image.Resampling.BILINEAR);exp=Image.new('RGBA',(w,h),col);exp.alpha_composite(filtered,(round(-.5*scale),round(-.5*scale)));expected.append(exp.convert('RGB'))
  for mode in actual:
   out.append({'mode':mode,'scale':scale,'background':bg,'full12Cells':True,'crossmode':[diff(a,b)for a,b in zip(actual['full-chromium'],actual['headless-shell'])],'approximatePillowWholeGuardCanvasBilinearVsActualCSS':[diff(a,b)for a,b in zip(expected,actual[mode])],'interpretation':'Independent fullcell comparison excluding labels and phase marker. Native2x image occupies1px guard in642x898 commoncanvas; wholecanvas filtered once. PIL rounded placement approximates actual fractional CSS; differing kernels/rounding/premultiplication remain uncorrected. Actual12 screenshots directly inspected; no pixel-identical CSS claim.'})
result={'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'comparisons':out,'crossmodeMaxAbs':max(x['maxAbs']for r in out for x in r['crossmode']),'approximatePillowMaxAbs':max(x['maxAbs']for r in out for x in r['approximatePillowWholeGuardCanvasBilinearVsActualCSS'])};(P/'inspection/independent-static-consumer-residuals.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='comparisons'},indent=2))
