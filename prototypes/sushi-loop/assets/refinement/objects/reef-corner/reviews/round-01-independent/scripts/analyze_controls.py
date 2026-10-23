from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,math,numpy as np,sys,PIL
p=Path(__file__).resolve().parents[1];obj=p.parents[1];run=obj/'candidates/round-01';e=p/'evidence'
def read(s):return json.loads((p/s).read_text())
def write(s,v):(p/s).write_text(json.dumps(v,indent=2)+'\n')
def rgba(f):return np.array(Image.open(f).convert('RGBA'))
def diff(a,b):
 d=np.abs(a.astype(int)-b.astype(int));return {'differentPixels':int(np.count_nonzero(np.any(d,axis=2))),'maxChannels':[int(d[:,:,j].max()) for j in range(4)],'changedExamples':[{'pixel':[int(x),int(y)],'submitted':a[y,x].tolist(),'replay':b[y,x].tolist()} for y,x in np.argwhere(np.any(d,axis=2))[:8]]}
comparisons=[]
for d in ['N','E','S','W']:
 for kind,f in [('hero',run/f'frames/static/{d}/000.png'),('two-port',run/f'native/two-port-{d}.png')]:
  comparisons.append({'kind':kind,'facing':d,**diff(rgba(f),rgba(e/'native'/f'{kind}-{d}.png'))})
write('evidence/independent-replay-comparison.json',comparisons)
ledger=read('evidence/independent-consumer-ledger.json');P=[(-.38,0),(.38,0),(.38,.2),(.25,.4),(.08,.44),(-.14,.35),(-.30,.4),(-.38,.2)]
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def proj(x,y,z,a):return (448+256*(math.cos(a)*x-math.sin(a)*y),752-256*(math.sin(a)*x+math.cos(a)*y)-179.2*z)
masks={};bounds={}
(e/'masks').mkdir(exist_ok=True)
for d,a in angles.items():
 native=Image.open(e/'native'/f'two-port-{d}.png').convert('RGBA');opaque=np.array(native.getchannel('A').filter(ImageFilter.MinFilter(3)))==255
 for port in ['W','N']:
  m=Image.new('L',(896,1216),0);draw=ImageDraw.Draw(m)
  def q(w,z,u):return proj(-.5+u,w,z,a) if port=='W' else proj(-w,.5+u,z,a)
  for j in range(8):
   v=P[j];w=P[(j+1)%8];draw.polygon([q(*v,-.03),q(*w,-.03),q(*w,.03),q(*v,.03)],fill=255)
  m=Image.fromarray((np.array(m).astype(bool)&opaque).astype('uint8')*255);m.save(e/'masks'/f'{d}-{port}.png');masks[(d,port)]=np.array(m)
  pts=[q(w,z,0) for w,z in P];bounds[(d,port)]=(int(min(x for x,y in pts)/2)-12,int(min(y for x,y in pts)/2)-12,int(max(x for x,y in pts)/2)+13,int(max(y for x,y in pts)/2)+13)
def find(mode,d,size,phase,control,bg):return next(x for x in mode['cases'] if x['settings']==dict(direction=d,size=size,phase=phase,root=.25 if phase==1 else .75,pan=.75 if phase==1 else .25,control=control,bg=bg,background=['#f2f0e8','#777b82','#17202b'][bg]))
rawreports=[];cssreports=[]
for mode in ledger['modes']:
 for d in angles:
  for phase in [1,3]:
   ind=find(mode,d,128,phase,'individual',0);nat=find(mode,d,128,phase,'native',0);rawind=rgba(p/ind['raw']['path']);rawnat=rgba(p/nat['raw']['path']);root=ind['settings']['root']
   for port in ['W','N']:
    m=Image.fromarray(masks[(d,port)]);rawmask=m.transform((rawnat.shape[1],rawnat.shape[0]),Image.Transform.AFFINE,(1,0,-1-root*2,0,1,-1-root*2),Image.Resampling.NEAREST)
    rawselect=(np.array(rawmask)==255)&(np.array(Image.fromarray(rawnat[:,:,3]).filter(ImageFilter.MinFilter(3)))==255);vals=np.abs(rawind[:,:,:3].astype(int)-rawnat[:,:,:3].astype(int))[rawselect]
    rawreports.append({'mode':mode['name'],'facing':d,'phase':phase,'port':port,'samples':int(rawselect.sum()),'individualInteriorAlphaLossPixels':int(np.count_nonzero(rawind[:,:,3][rawselect]<255)),'RGBMax':int(vals.max()) if len(vals) else None,'RGBMean':float(vals.mean()) if len(vals) else None,'scope':'same exact current raw raster, native combined vs independently rendered sprites; residuals retained'})
    for size in [128,32]:
     scale=size/128;H=round(608*scale);W=round(448*scale);offset=(root+ind['settings']['pan'])*scale;sel=np.zeros((H,W),bool)
     # Keep only complete output-pixel source footprints within finite native local opaque neighborhood.
     for yy in range(H):
      y0=math.floor((yy-offset)*2/scale+1e-8);y1=math.ceil((yy+1-offset)*2/scale-1e-8)
      if y0<0 or y1>1216:continue
      for xx in range(W):
       x0=math.floor((xx-offset)*2/scale+1e-8);x1=math.ceil((xx+1-offset)*2/scale-1e-8)
       if 0<=x0<x1<=896 and np.all(masks[(d,port)][y0:y1,x0:x1]==255):sel[yy,xx]=True
     images=[rgba(p/find(mode,d,size,phase,'individual',bg)['screenshot']['path']) for bg in range(3)];nativeimages=[rgba(p/find(mode,d,size,phase,'native',bg)['screenshot']['path']) for bg in range(3)]
     bgdiff=np.max(np.abs(images[0][:,:,:3].astype(int)-images[2][:,:,:3].astype(int)),axis=2);ndiff=np.max(np.abs(nativeimages[0][:,:,:3].astype(int)-nativeimages[2][:,:,:3].astype(int)),axis=2);rgb=np.abs(images[1][:,:,:3].astype(int)-nativeimages[1][:,:,:3].astype(int))[sel]
     cssreports.append({'mode':mode['name'],'facing':d,'phase':phase,'port':port,'cell':size,'root':root,'pan':ind['settings']['pan'],'samples':int(sel.sum()),'individualBackgroundDependentPixels':int(np.count_nonzero(bgdiff[sel])),'nativeBackgroundDependentPixels':int(np.count_nonzero(ndiff[sel])),'nativeIndividualRGBMax':int(rgb.max()) if len(rgb) else None,'css':find(mode,d,size,phase,'individual',1)['css']})
 # Actual128 CSS local strips, both controls, both ports, one representative fractional phase. Crop is inspection-only.
 sheet=Image.new('RGB',(650,8*190),'#e7e4db');draw=ImageDraw.Draw(sheet)
 for row,(d,port) in enumerate((d,p1) for d in ['N','E','S','W'] for p1 in ['W','N']):
  box=bounds[(d,port)];box=tuple(v+1 for v in box)
  for k,control in enumerate(['native','individual']):
   f=p/find(mode,d,128,1,control,1)['screenshot']['path'];im=Image.open(f).convert('RGB').crop(box);im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   sheet.paste(im,(k*325,row*190+22));draw.text((k*325+4,row*190+4),f'{d}/{port} {control} cell128 p1 x2',fill='#183a51')
 sheet.save(e/f"local-joins-{mode['name']}.png")
 # True intended-size all4phone on every background, native and individual, phase3.
 phone=Image.new('RGB',(1000,600),'#e7e4db');draw=ImageDraw.Draw(phone)
 for row,bg in enumerate(range(3)):
  for col,d in enumerate(['N','E','S','W']):
   for k,control in enumerate(['native','individual']):
    im=Image.open(p/find(mode,d,32,3,control,bg)['screenshot']['path']).convert('RGB');phone.paste(im,(250*col+112*k,200*row+25));draw.text((250*col+112*k,200*row+5),f'{d} {control[:3]}32',fill='#183a51')
 phone.save(e/f"phone-controls-{mode['name']}.png")
write('evidence/independent-local-measurements.json',{'method':'Independent exact finite8point two-port surface ribbons±.03, projected by registered camera. Native mask intersected with3x3opaque255 neighborhoods. CSS selection requires full output-pixel native footprint in that mask. Native and independent actual controls retain separate raw canvases and3background CSS screenshots, both backends.','nativeRaw':rawreports,'actualCSS':cssreports,'limits':'Masks omit outer silhouettes/nonopaque neighborhoods and disclose sample counts. RGB residuals are retained; no universal wholeimageidentity or numerical seam waiver. All192 independent CSS captures remain raw. No extent calibration/pixelrepair applied.'})
write('evidence/independent-toolchain.json',{'Python':sys.version,'Pillow':PIL.__version__,'NumPy':np.__version__,'browserVersions':[{'name':x['name'],'version':x['version'],'launch':x['launch'],'cases':len(x['cases']),'pageErrors':x['pageErrors']} for x in ledger['modes']],'helperSHA256':ledger['helpers'],'DPR':ledger['deviceScaleFactor'],'viewport':ledger['viewport']})
print(json.dumps({'replay':comparisons,'nativeRawMaxRGB':max(x['RGBMax'] or 0 for x in rawreports),'rawInteriorAlphaLoss':sum(x['individualInteriorAlphaLossPixels'] for x in rawreports),'CSSBackgroundDependentPixels':sum(x['individualBackgroundDependentPixels']+x['nativeBackgroundDependentPixels'] for x in cssreports),'CSSMaxNativeIndividualRGB':max(x['nativeIndividualRGBMax'] or 0 for x in cssreports),'CSSMinimumSamples':min(x['samples'] for x in cssreports)},indent=2))
