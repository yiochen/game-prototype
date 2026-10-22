from PIL import Image,ImageDraw,ImageFont
import pathlib,json,hashlib,math,numpy as np
P=pathlib.Path(__file__).resolve().parents[1]; O=P/'candidates/round-01'
for n in ['atlases','previews','independent','residuals']: (O/n).mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
VALID=json.loads((O/'validation.json').read_text());SPECS=list(zip(VALID['assemblyContract']['canonicalOffsets'][1:], [math.radians(a) for a in VALID['assemblyContract']['familyRelativeRotations']]))
rots={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def frame(kind,d,i): return O/kind/f'running-{d}-{i:02}.png'
def atlas(kind,d):
 first=Image.open(frame(kind,d,0));w,h=first.size;im=Image.new('RGBA',(w*6,h*4))
 for i in range(24): im.paste(Image.open(frame(kind,d,i)),((i%6)*w,(i//6)*h))
 out=O/'atlases'/f'{kind}-{d}.png';im.save(out);return out
def mask(d):
 m=Image.new('L',(896,1216)); dr=ImageDraw.Draw(m);r=rots[d]
 for offset,angle in SPECS:
  nx,ny=offset[:2];tx,ty=-ny,nx;pts=[]
  for cross in [-.48,.48]:
   for delta in [-.014,.014]:
    for z in [.505,.695]:
     x,y=nx*(.5+delta)+tx*cross,ny*(.5+delta)+ty*cross;xx=x*math.cos(r)-y*math.sin(r);yy=x*math.sin(r)+y*math.cos(r);pts.append((448+256*xx,752-256*yy-z*179.2))
  dr.rectangle((min(p[0] for p in pts)-1,min(p[1] for p in pts)-1,max(p[0] for p in pts)+1,max(p[1] for p in pts)+1),fill=255)
 m.save(O/'residuals'/f'join-mask-{d}.png');return np.asarray(m)>0
def stat(a,b,m):
 diff=np.abs(a.astype(int)-b.astype(int)); loc=diff[m];bad=np.any(diff>1,axis=2)
 return {'fullMaxRGBA':diff.max(axis=(0,1)).tolist(),'joinMaxRGBA':loc.max(axis=0).tolist(),'fullDifferentAlphaPixels':int((diff[:,:,3]>0).sum()),'joinDifferentAlphaPixels':int((loc[:,3]>0).sum()),'joinRGBOver1Pixels':int(np.any(loc[:,:3]>1,axis=1).sum()),'fullRGBAOver1Bounds':None if not bad.any() else [int(np.where(bad)[1].min()),int(np.where(bad)[0].min()),int(np.where(bad)[1].max()),int(np.where(bad)[0].max())]}
metrics=[];raw=[];atlases=[]
for d,r in rots.items():
 for kind in ['frames','family-frames','connected','unbroken']: atlas(kind,d)
 m=mask(d)
 for i in range(25):
  # SpriteScene's back-to-front world depth order; alpha is composed on the native2x grid.
  modules=[(0,0,d,True)]
  for offset,a in SPECS:
   x,y=offset[:2]
   xx=round(x*math.cos(r)-y*math.sin(r));yy=round(x*math.sin(r)+y*math.cos(r)); rr=(r+a+math.pi)%(2*math.pi)-math.pi
   fd=min(rots,key=lambda k:abs((rots[k]-rr+math.pi)%(2*math.pi)-math.pi));modules.append((xx,yy,fd,False))
  im=Image.new('RGBA',(896,1216))
  for x,y,fd,isCorner in sorted(modules,key=lambda a:-a[1]):
   src=frame('frames',fd,i) if isCorner and i<24 else (frame('closure',fd,i) if isCorner else frame('family-frames',fd,i))
   im.alpha_composite(Image.open(src),(256+x*256,256-y*256))
  ip=frame('independent',d,i);im.save(ip)
  a=np.array(im);b=np.array(Image.open(frame('connected',d,i)));u=np.array(Image.open(frame('unbroken',d,i)))
  row={'direction':d,'index':i,'independentVsConnected':stat(a,b,m),'connectedVsUnbroken':stat(b,u,m),'independentVsUnbroken':stat(a,u,m)};metrics.append(row)
  for key,left,right in [('independent-vs-connected',a,b),('independent-vs-unbroken',a,u),('connected-vs-unbroken',b,u)]:
   dif=np.abs(left.astype(int)-right.astype(int)).astype('uint8');Image.fromarray(dif).save(O/'residuals'/f'fullRGBA-{key}-{d}-{i:02}.png')
  if i in [0,6,12,18,24]:
   dif=np.abs(a.astype(int)-b.astype(int));viz=np.zeros_like(a);viz[:,:,:3]=np.minimum(dif[:,:,:3]*24,255);viz[:,:,3]=np.where(np.any(dif>0,axis=2),255,0);Image.fromarray(viz.astype('uint8')).save(O/'residuals'/f'RGB-alpha-localized-{d}-{i:02}.png')
 for i in range(24):
  p=frame('frames',d,i);raw.append({'clip':'running','direction':d,'index':i,'path':p.relative_to(P).as_posix(),'width':384,'height':704,'sha256':sha(p)})
 p=O/'atlases'/f'frames-{d}.png';atlases.append({'clip':'running','direction':d,'path':p.relative_to(P).as_posix(),'width':2304,'height':2816,'columns':6,'rows':4,'rects':[[i%6*384,i//6*704,384,704] for i in range(24)],'sha256':sha(p)})
 # Full96 frame contact sheets retain registration; use2x published pixels at half scale.
 sheet=Image.new('RGBA',(192*6,374*4),'#ece9df');dr=ImageDraw.Draw(sheet)
 for i in range(24):
  thumb=Image.open(frame('frames',d,i)).resize((192,352),Image.Resampling.BOX);sheet.alpha_composite(thumb,((i%6)*192,(i//6)*374+20));dr.text(((i%6)*192+8,(i//6)*374+4),f'{d} frame{i+1:02}/24',fill='#23323b')
 sheet.save(O/'previews'/f'all-frames-{d}.png')
ims=[]
for i in range(24):
 im=Image.new('RGBA',(768,352),'#ece9df')
 for j,d in enumerate(rots):im.alpha_composite(Image.open(frame('frames',d,i)).resize((192,352),Image.Resampling.BOX),(192*j,0))
 ims.append(im)
ims[0].save(O/'previews/four-view-sheet.png');ims[0].save(O/'previews/running-all.gif',save_all=True,append_images=ims[1:],duration=[83,83,84]*8,loop=0,disposal=2)
for d in rots:
 im=[]
 for i in range(24):
  a=Image.new('RGBA',(448,608),'#ece9df');a.alpha_composite(Image.open(frame('connected',d,i)).resize((448,608),Image.Resampling.BOX));im.append(a)
 im[0].save(O/'previews'/f'running-{d}.gif',save_all=True,append_images=im[1:],duration=[83,83,84]*8,loop=0,disposal=2)
rep=Image.new('RGBA',(576,780),'#ece9df')
for j in range(9): rep.alpha_composite(Image.open(frame('frames','S',0)).resize((192,352),Image.Resampling.BOX),(j%3*128+32,j//3*128+20))
rep.save(O/'previews/repeated.png')
summary={k:{field:max(v[k][field] if isinstance(v[k][field],int) else max(v[k][field]) for v in metrics) for field in ['fullMaxRGBA','joinMaxRGBA','fullDifferentAlphaPixels','joinDifferentAlphaPixels','joinRGBOver1Pixels']} for k in ['independentVsConnected','connectedVsUnbroken','independentVsUnbroken']}
(O/'native-continuity.json').write_text(json.dumps({'schemaVersion':1,'cases':100,'nativeGrid':'2x published binary coverage; identical mathematical registered root/pitch; no raster repair','joinMasks':'residuals/join-mask-{direction}.png','summary':summary,'casesData':metrics,'closure':{d:{'RGBAEqual':np.array_equal(np.array(Image.open(frame('frames',d,0))),np.array(Image.open(frame('closure',d,24))))} for d in rots}},indent=2))
(O/'raw-frame-records.json').write_text(json.dumps(raw,indent=2));(O/'atlas-records.json').write_text(json.dumps(atlases,indent=2));print(json.dumps(summary,indent=2))
