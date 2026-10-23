import json,pathlib,collections
import numpy as np
from PIL import Image,ImageDraw
B=pathlib.Path(__file__).parents[2];O=pathlib.Path(__file__).parent;P=B/'candidates/round-03';r=json.loads((O/'integrity-pixels.json').read_text());stats={};worst=['hold-E-07.png','hold-W-09.png','load-E-04.png','load-W-05.png'];sheet=Image.new('RGB',(4*384,4*400),(105,110,116));draw=ImageDraw.Draw(sheet)
for d in ['N','E','S','W']:
 rows=[x for x in r['pixelRecords']if x['frame'].split('-')[0]in['hold','load']and '-'+d+'-'in x['frame']];hist=collections.Counter();logical=0;large=0;alpha=0
 for x in rows:
  im=Image.open(P/'frames'/x['frame']).convert('RGBA');old=Image.open(B/f"candidates/{x['baseline']}/frames"/x['frame']).convert('RGBA');de=np.abs(np.array(im,dtype=np.int16)-np.array(old,dtype=np.int16));hist.update(dict(zip(*np.unique(de[de>0],return_counts=True))));large+=int(np.any(de>4,axis=2).sum());alpha+=int((de[:,:,3]>0).sum())
  for bg in [(242,237,226),(105,110,116),(29,37,45)]:
   a=Image.alpha_composite(Image.new('RGBA',im.size,(*bg,255)),im).resize((192,320),Image.Resampling.LANCZOS);b=Image.alpha_composite(Image.new('RGBA',im.size,(*bg,255)),old).resize((192,320),Image.Resampling.LANCZOS);logical=max(logical,int(np.abs(np.array(a,dtype=np.int16)-np.array(b,dtype=np.int16)).max()))
 stats[d]={'nonzeroComponentErrorHistogram':{str(k):int(v)for k,v in sorted(hist.items())},'nativePixelsWithAnyChannelOver4Across24Frames':large,'nativeAlphaChangedPixelsAcross24Frames':alpha,'maxLogicalCompositeError':logical}
for row,n in enumerate(worst):
 new=Image.open(P/'frames'/n).convert('RGBA');old=Image.open(B/'candidates/round-01/frames'/n).convert('RGBA');box=(70,155,330,545)
 for i,(label,im)in enumerate([('round01',old),('round03',new)]):
  bg=Image.new('RGBA',im.size,(105,110,116,255));rgb=Image.alpha_composite(bg,im).convert('RGB').crop(box);sheet.paste(rgb,(i*384,row*400+10));draw.text((i*384,row*400),n+' '+label,fill='white')
 de=np.abs(np.array(new,dtype=np.int16)-np.array(old,dtype=np.int16));mask=np.any(de>0,axis=2);heat=np.minimum(np.max(de,axis=2)*28,255).astype('uint8');diag=np.zeros((*heat.shape,3),dtype='uint8');diag[:,:,0]=heat;diag[:,:,1]=mask.astype('uint8')*30
 sheet.paste(Image.fromarray(diag).crop(box),(768,row*400+10));draw.text((768,row*400),'28x channel error diagnostic',fill='white')
 # True logical-size composite, placed without upscaling.
 bg=Image.new('RGBA',new.size,(29,37,45,255));thumb=Image.alpha_composite(bg,new).resize((192,320),Image.Resampling.LANCZOS).convert('RGB');sheet.paste(thumb,(1152,row*400+10));draw.text((1152,row*400),'round03 logical192x320',fill='white')
sheet.save(O/'pixel-difference-diagnostic.png');(O/'pixel-materiality.json').write_text(json.dumps({'quantifiedComparisons':stats,'diagnosticOnly':'Amplified error panel is analytical, not a candidate render. Source captures remain untouched.','recaptureParity':[{**x,'decodedRGBAEqual':Image.open(O/x['path']).convert('RGBA').tobytes()==Image.open(P/x['candidateFrame']).convert('RGBA').tobytes()}for x in json.loads((O/'recaptures.json').read_text())['renders']]},indent=2)+'\n');print(json.dumps(stats,indent=2))
