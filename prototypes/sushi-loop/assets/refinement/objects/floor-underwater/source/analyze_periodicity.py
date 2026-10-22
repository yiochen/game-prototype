"""Independent double-precision evaluator of the persisted native math field.
Actual GPU material edge/gradient samples are separately bound in material-probes/.
"""
from pathlib import Path
import json,math,ast,hashlib
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];C=P/'candidates/round-01';tree=ast.parse((P/'source/reproduce.py').read_text());const={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['SEEDS','PALETTE']:const[n.targets[0].id]=ast.literal_eval(n.value)
TAU=math.tau
palette=[]
for k in ['deep','body','halo','caustic']:
 a=np.array([int(const['PALETTE'][k][i:i+2],16)/255 for i in [0,2,4]]);palette.append(np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4))
def field(u,v,phase):
 u,v=np.broadcast_arrays(np.asarray(u),np.asarray(v));t=TAU*phase
 U=u+.071*np.sin(TAU*(u+v)+.24*np.sin(t)+.8)+.026*np.sin(TAU*(2*v-u)+.18*np.cos(t))
 V=v+.064*np.sin(TAU*(v-u)+.22*np.cos(t)+1.7)+.026*np.sin(TAU*(2*u+v)+.17*np.sin(t))
 d=[]
 for i,(x,y) in enumerate(const['SEEDS']):
  sx=x+.009*np.sin(t+i*2.39996323);sy=y+.009*np.cos(t+i*1.819031)
  d.append(np.sqrt(np.maximum(2-np.cos(TAU*(U-sx))-np.cos(TAU*(V-sy)),0)))
 nearest=np.sort(d,axis=0)[:2];a,b=nearest;gap=b-a;core=np.exp(-(gap/(.027+.045*a))**2);halo=np.exp(-(gap/.16)**2)
 broad=np.sin(TAU*(2*u+v)+.15*np.sin(t));volume=np.clip(a*a*4.7+.02+.1*broad,0,1)
 c=palette[0]+volume[...,None]*(palette[1]-palette[0]);c=c+(halo*.34)[...,None]*(palette[2]-c);c=c+(core*.68)[...,None]*(palette[3]-c)
 return c
vs=np.linspace(0,1,1025);h=1e-5;rows=[]
for phase in [i/12 for i in range(13)]+[.5/12,6.5/12,11.5/12]:
 r={'phase':phase,'axes':{}}
 for axis in ['X','Y']:
  def f(c):return field(c,vs,phase) if axis=='X' else field(vs,c,phase)
  a=f(0);b=f(1);ga=(f(h)-f(-h))/(2*h);gb=(f(1+h)-f(1-h))/(2*h)
  r['axes'][axis]={'maxLinearRGBValueError':float(np.max(abs(a-b))),'maxLinearRGBFiniteGradientError':float(np.max(abs(ga-gb))),'maxLinearRGBStencilError':float(max(np.max(abs(f(h)-f(1+h))),np.max(abs(f(-h)-f(1-h)))))}
 corners=np.array([field(x,y,phase) for x,y in [(0,0),(0,1),(1,0),(1,1)]]);r['sharedCornerMaxLinearRGBError']=float(np.max(abs(corners-corners[0])));rows.append(r)
u,v=np.meshgrid(np.linspace(0,1,129),np.linspace(0,1,129));closure=float(np.max(abs(field(u,v,0)-field(u,v,1))))
inbet=[];strip=Image.new('RGBA',(1536,280),(245,245,240,255));dr=ImageDraw.Draw(strip)
for j,frame in enumerate([1,1.5,2,12,12.5,13]):
 if frame%1:im=Image.open(C/'inbetweens'/('frame-%04.1f.png'%frame)).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
 else:im=Image.open(C/'frames/scroll/S'/('%03d.png'%(int(frame)-1))).convert('RGBA')
 strip.paste(im,(j*256,24));dr.text((j*256+4,5),'Native frame '+str(frame),fill=(35,42,48))
strip.save(C/'previews/meaningful-inbetweens.png')
for frame in [1.5,7.5,12.5]:
 im=np.asarray(Image.open(C/'inbetweens'/('frame-%04.1f.png'%frame)).convert('RGBA')).astype(float);lo=int(frame)-1;hi=(lo+1)%12;a=np.asarray(Image.open(C/'native/scroll/S'/('%03d.png'%lo))).astype(float);b=np.asarray(Image.open(C/'native/scroll/S'/('%03d.png'%hi))).astype(float)
 inbet.append({'nativeFrame':frame,'meanAbsRGBFromPrevious':float(abs(im[:,:,:3]-a[:,:,:3]).mean()),'meanAbsRGBFromNext':float(abs(im[:,:,:3]-b[:,:,:3]).mean()),'meanAbsRGBFromLinearPixelBlend':float(abs(im[:,:,:3]-(a[:,:,:3]+b[:,:,:3])/2).mean()),'interpretation':'Captured by evaluating the native continuous shader at fractional scene frame; it differs from both neighboring captures and simple pixel blending.'})
report={'recipeSHA256':hashlib.sha256((P/'source/reproduce.py').read_bytes()).hexdigest(),'method':'Independent NumPy float64 transcription of the saved texture-free node graph;1025 samples per shared edge in16 phases (all12, closure,3 fractional). Native GPU probes independently test the actual persisted material and finite-gradient stencils at257 points.','analyticReason':'Both local UV axes enter only integer-period trigonometric functions plus periodic domain warp. Toroidal seed distances use cos(2π(U-seedX)),cos(2π(V-seedY)); translating either original UV axis by1 changes every trigonometric angle by an integer multiple of2π and leaves all distances,sorting,mixes and gradients invariant. Time appears only through periodic sin/cos of2πphase; frame13 equals frame1 exactly by the persisted phase driver. No branch switches the spatial/time boundary law.','allEdgeSamples':rows,'linearRGBTemporalClosureError':closure,'inbetweenCaptures':inbet,'limits':'Float64 analytic equality supports the intended field. Native GPU8-bit samples have independent rounding (observed at most1LSB), so do not claim byte-identical opposing raw pixel edges. Rendered pixel centers are half a pixel inside the finite surface; exact-edge equality is established by probes, not inferred from comparing ordinary first/last rows.'}
(C/'analytical-periodicity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'maxValueError':max(a['maxLinearRGBValueError'] for r in rows for a in r['axes'].values()),'maxGradientError':max(a['maxLinearRGBFiniteGradientError'] for r in rows for a in r['axes'].values()),'closure':closure,'inbetweens':inbet}))
