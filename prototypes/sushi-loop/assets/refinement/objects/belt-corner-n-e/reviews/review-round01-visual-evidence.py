from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
B=Path(__file__).resolve().parent.parent;C=B/'candidates/round-01';R=B/'reviews';report={}
# Verify displayed native contact-sheet panels against all exact packet raw frames.
report['contactPanelsMatchRawFrames']=True
for d in 'NESW':
 sheet=Image.open(C/f'previews/all-frames-{d}.png').convert('RGBA')
 for i in range(24):
  im=Image.open(C/f'frames/running-{d}-{i:02}.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);base=Image.new('RGBA',(192,352),'#ece9df');base.alpha_composite(im)
  panel=sheet.crop((i%6*192,i//6*374+20,(i%6+1)*192,i//6*374+372));report['contactPanelsMatchRawFrames'] &= panel.tobytes()==base.tobytes()
# GIF contact verifies animation previews include the same connected form at representative phases.
contact=Image.new('RGB',(5*230,4*320),'#ece9df');draw=ImageDraw.Draw(contact)
for j,d in enumerate('NESW'):
 g=Image.open(C/f'previews/running-{d}.gif')
 for col,frame in enumerate([0,6,12,18,23]):
  g.seek(frame);im=g.convert('RGBA');im.thumbnail((224,292),Image.Resampling.LANCZOS);contact.paste(im,(col*230,j*320+22),im);draw.text((col*230+5,j*320+3),f'{d} GIFframe {frame}',fill='#23323b')
contact.save(R/'round01-gif-contact.png')
# Independently recalculate actual browser/Godot joins using the declared conservative mask, and report fullRGB separately.
for dirname,receipt in [('consumer','cases.json'),('godot-consumer','render-record.json')]:
 cfg=json.loads((C/dirname/receipt).read_text());groups={}
 for e in cfg['evidence'] if dirname=='consumer' else cfg['captures']:
  k=e['case'] if dirname=='consumer' else f"{e['direction']}-{e['pitch']}-f{e['index']}-{e['background']}";groups.setdefault(k,{})[e['mode']]=e
 out={}
 for key,modes in groups.items():
  e=modes['independent'];pitch=str(e['pitch']);d=e['direction'];ims={}
  for m in ['independent','connected','unbroken']:
   f=f'{key}-{m}.png' if dirname=='consumer' else modes[m]['path'];ims[m]=np.array(Image.open(C/dirname/f).convert('RGBA')).astype(int)
  h,w=ims['independent'].shape[:2];mask=np.array(Image.open(C/f'residuals/join-mask-{d}.png').resize((w,h),Image.Resampling.BOX).filter(ImageFilter.MaxFilter(5)))>0
  for l,rr in [('independent','connected'),('connected','unbroken')]:
   diff=abs(ims[l]-ims[rr]);name=l+'Vs'+rr;row=out.setdefault(pitch,{}).setdefault(name,{'cases':0,'fullMaxRGBA':[0,0,0,0],'joinMaxRGBA':[0,0,0,0],'joinAlphaPixels':0,'joinRGBOver1Pixels':0});row['cases']+=1;row['fullMaxRGBA']=np.maximum(row['fullMaxRGBA'],diff.max(axis=(0,1))).tolist();row['joinMaxRGBA']=np.maximum(row['joinMaxRGBA'],diff[mask].max(axis=0)).tolist();row['joinAlphaPixels']+=int(np.count_nonzero(diff[:,:,3][mask]));row['joinRGBOver1Pixels']+=int(np.any(diff[:,:,:3]>1,axis=2)[mask].sum())
 report[dirname]=out
(R/'round01-consumer-independent-metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
