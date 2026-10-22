from PIL import Image,ImageFilter,ImageDraw
import pathlib,json,numpy as np,math
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
def stats(a,b,mask):
 diff=np.abs(a.astype(int)-b.astype(int));loc=diff[mask];bad=np.any(diff>1,axis=2)
 return {'fullMaxRGBA':diff.max(axis=(0,1)).tolist(),'joinMaxRGBA':loc.max(axis=0).tolist(),'joinDifferentAlphaPixels':int((loc[:,3]>0).sum()),'joinRGBOver1Pixels':int(np.any(loc[:,:3]>1,axis=1).sum()),'fullRGBAOver1Bounds':None if not bad.any() else [int(np.where(bad)[1].min()),int(np.where(bad)[0].min()),int(np.where(bad)[1].max()),int(np.where(bad)[0].max())]}
for dirname,receipt in [('consumer','cases.json'),('godot-consumer','render-record.json')]:
 C=O/dirname;cfg=json.loads((C/receipt).read_text());rows=[]
 if dirname=='consumer':
  groups={}
  for e in cfg['evidence']:groups.setdefault(e['case'],{})[e['mode']]=e
 else:
  groups={}
  for e in cfg['captures']:
   key=f"{e['direction']}-{e['pitch']}-f{e['index']}-{e['background']}";groups.setdefault(key,{})[e['mode']]=e
 for key,modes in groups.items():
  e=modes['independent'];d=e['direction'];pitch=e['pitch'];imgs={}
  for mode in ['independent','connected','unbroken']:
   file=C/(f'{key}-{mode}.png' if dirname=='consumer' else modes[mode]['path']);imgs[mode]=np.array(Image.open(file).convert('RGBA'))
  h,w=imgs['independent'].shape[:2];mask=Image.open(O/'residuals'/f'join-mask-{d}.png').resize((w,h),Image.Resampling.BOX).filter(ImageFilter.MaxFilter(5));mask=np.array(mask)>0
  rows.append({'case':key,'direction':d,'pitch':pitch,'independentVsConnected':stats(imgs['independent'],imgs['connected'],mask),'connectedVsUnbroken':stats(imgs['connected'],imgs['unbroken'],mask)})
 summary={}
 for pitch in [128,55,32]:
  rr=[r for r in rows if r['pitch']==pitch];summary[str(pitch)]={}
  for kind in ['independentVsConnected','connectedVsUnbroken']:
   summary[str(pitch)][kind]={'samples':len(rr),'fullMaxRGBA':np.array([r[kind]['fullMaxRGBA'] for r in rr]).max(axis=0).tolist(),'joinMaxRGBA':np.array([r[kind]['joinMaxRGBA'] for r in rr]).max(axis=0).tolist(),'joinDifferentAlphaPixels':sum(r[kind]['joinDifferentAlphaPixels'] for r in rr),'joinRGBOver1Pixels':sum(r[kind]['joinRGBOver1Pixels'] for r in rr)}
 result={'schemaVersion':1,'method':'Actual consumer PNG absolute RGBA residuals, source join masks uniformly mapped to output with2px conservative filter margin. Both fullRGB/alpha and joinRGB/alpha reported; no global-average waiver. Transparent Godot readback uses premultipliedRGB.','summaryByPitch':summary,'cases':rows};(O/f'{dirname}-metrics.json').write_text(json.dumps(result,indent=2));print(dirname,json.dumps(summary,indent=2))
