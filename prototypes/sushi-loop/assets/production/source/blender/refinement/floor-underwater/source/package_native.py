"""Whole-frame approved reduction, lossless packing, technical metrics and previews."""
import sys,json,math,hashlib,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];C=P/'candidates/round-01';D=C/'previews';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def arr(im):return np.asarray(im).astype(float)
def measure(a,b):
 q=np.abs(a.astype(float)-b.astype(float));return {'maxAbs':float(q.max()),'meanAbs':float(q.mean()),'rmse':float(np.sqrt((q*q).mean()))}
def apng(frames,path):
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=83,loop=0,disposal=0,blend=0)
 b=path.read_bytes();out=b[:8];i=8
 while i<len(b):
  n=struct.unpack('>I',b[i:i+4])[0];typ=b[i+4:i+8];d=b[i+8:i+8+n]
  if typ==b'fcTL':d=d[:20]+struct.pack('>HH',1,12)+d[24:]
  out+=struct.pack('>I',len(d))+typ+d+struct.pack('>I',zlib.crc32(typ+d)&0xffffffff);i+=n+12
 path.write_bytes(out)
report={'publication':'Exact full RGBA512→256 LANCZOS, no fitting/crop/alpha/RGB repair. Native3x3 full1536→768 LANCZOS; independent3x3 consists of nine unchanged256 frames.','coverage':[],'closure':{},'temporal':{},'nativeIndependentComparison':[],'nativeShaderProbes':[]}
for direction in 'NESW':
 atlas=Image.new('RGBA',(1536,512));frames=[];patches=[];native_logical=[];independent_logical=[]
 for i in range(13):
  raw=Image.open(C/'native/scroll'/direction/('%03d.png'%i)).convert('RGBA');pub=raw.resize((256,256),Image.Resampling.LANCZOS);dest=C/'frames/scroll'/direction/('%03d.png'%i);dest.parent.mkdir(parents=True,exist_ok=True);pub.save(dest)
  nr=Image.open(C/'native-patch'/direction/('%03d.png'%i)).convert('RGBA');n=nr.resize((768,768),Image.Resampling.LANCZOS);npth=C/'published-native-patch'/direction/('%03d.png'%i);npth.parent.mkdir(parents=True,exist_ok=True);n.save(npth)
  indep=Image.new('RGBA',(768,768));
  for y in range(3):
   for x in range(3):indep.paste(pub,(x*256,y*256))
  ipth=C/'independent-patch'/direction/('%03d.png'%i);ipth.parent.mkdir(parents=True,exist_ok=True);indep.save(ipth)
  if i<12:
   frames.append(pub);patches.append(indep.resize((384,384),Image.Resampling.LANCZOS));native_logical.append(n.resize((384,384),Image.Resampling.LANCZOS));independent_logical.append(indep.resize((384,384),Image.Resampling.LANCZOS));atlas.paste(pub,(i%6*256,i//6*256))
   report['coverage'].append({'direction':direction,'phase':i,'rawAlphaMin':raw.getchannel('A').getextrema()[0],'publishedAlphaMin':pub.getchannel('A').getextrema()[0],'nativePatchAlphaMin':nr.getchannel('A').getextrema()[0],'independentAlphaMin':indep.getchannel('A').getextrema()[0]})
   a=np.asarray(n);b=np.asarray(indep);mask=np.zeros((768,768),bool)
   for k in [256,512]:mask[:,k-3:k+3]=True;mask[k-3:k+3,:]=True
   corner=np.zeros((768,768),bool)
   for y in [256,512]:
    for x in [256,512]:corner[y-4:y+4,x-4:x+4]=True
   report['nativeIndependentComparison'].append({'direction':direction,'phase':i,'fullRGB':measure(a[:,:,:3],b[:,:,:3]),'joinBandRGB':measure(a[mask,:3],b[mask,:3]),'sharedCornerRGB':measure(a[corner,:3],b[corner,:3])})
 (C/'atlases').mkdir(exist_ok=True);atlas.save(C/'atlases'/('scroll-'+direction+'.png'))
 report['closure'][direction]={kind:measure(np.asarray(Image.open(C/folder/direction/'000.png')),np.asarray(Image.open(C/folder/direction/'012.png'))) for kind,folder in [('raw','native/scroll'),('published','frames/scroll'),('nativePatch','native-patch'),('independent','independent-patch')]}
 report['temporal'][direction]={'uniquePublishedDecoded':len(set(im.tobytes() for im in frames)),'steps':[measure(np.asarray(frames[i])[:,:,:3],np.asarray(frames[(i+1)%12])[:,:,:3]) for i in range(12)]}
 apng(frames,D/('scroll-'+direction+'.apng'));apng(patches,D/('repeated-'+direction+'.apng'))
 for label,imgs in [('native',native_logical),('independent',independent_logical)]:
  sheet=Image.new('RGBA',(1152,1600),(245,245,240,255));dr=ImageDraw.Draw(sheet)
  for i,im in enumerate(imgs):x=i%3*384;y=i//3*400;sheet.paste(im,(x,y+16));dr.text((x+4,y+2),direction+' '+label+' phase '+str(i),fill=(35,42,48))
  sheet.save(D/(label+'-all-phases-'+direction+'.png'))
 # Published original-size atlas is the twelve-phase visual sheet, no extra resampling.
 atlas.save(D/('published-all-phases-'+direction+'.png'))
sheet=Image.new('RGBA',(1024,280),(245,245,240,255));draw=ImageDraw.Draw(sheet)
repeat=Image.new('RGBA',(1536,404),(245,245,240,255));rd=ImageDraw.Draw(repeat)
for j,d in enumerate('NESW'):
 sheet.paste(Image.open(C/'frames/scroll'/d/'000.png'),(j*256,24));draw.text((j*256+4,5),d+' published256 / root128,128',fill=(35,42,48))
 repeat.paste(Image.open(C/'independent-patch'/d/'000.png').resize((384,384),Image.Resampling.LANCZOS),(j*384,20));rd.text((j*384+4,4),d+' repeated logical128 per cell',fill=(35,42,48))
sheet.save(D/'four-view-sheet.png');repeat.save(D/'repeated-sheet.png')
# Actual GPU shader strips: exact values and matched finite-difference gradient stencils on both edges/corners.
for r in json.loads((C/'probe-records.json').read_text())['views']:
 a=np.asarray(Image.open(P/r['path']))[::-1].astype(int);pairs=[]
 for base,axis in [(0,'X'),(6,'Y')]:
  pairs.append({'axis':axis,'edgeValueMaxRGB':int(np.max(abs(a[base,:,:3]-a[base+1,:,:3]))),'minusHMaxRGB':int(np.max(abs(a[base+2,:,:3]-a[base+3,:,:3]))),'plusHMaxRGB':int(np.max(abs(a[base+4,:,:3]-a[base+5,:,:3]))),'finiteGradientNumeratorMaxRGB':int(np.max(abs((a[base+4,:,:3]-a[base+2,:,:3])-(a[base+5,:,:3]-a[base+3,:,:3])))),'cornerEndpointRGBMax':int(np.max(abs(a[base,0,:3]-a[base,-1,:3])))})
 report['nativeShaderProbes'].append({'frame':r['frame'],'path':r['path'],'pairs':pairs,'alphaMin':int(a[:,:,3].min())})
write(C/'pixel-technical-report.json',report)
# Truthful publication metadata keeps the raw4x camera measurement separately.
cam=json.loads((C/'native-camera.json').read_text());pub=json.loads(json.dumps(cam));pub['captureScale']=2;pub['nativeFrame']=[256,256];pub['calibration']={k:[v/2 for v in values] for k,values in cam['calibration'].items()};pub['nativeMeasurement']={'path':'candidates/round-01/native-camera.json','sha256':sha(C/'native-camera.json'),'captureScale':4,'frame':[512,512]};pub['normalization']='Metadata unit conversion4x→2x matches the approved whole512→256 LANCZOS. Camera matrix/projection/shift/aspect unchanged; no fitting or recapture at2x.';write(C/'published-camera.json',pub)
asset={'id':'floor-underwater','projection':'top-down-oblique-square-grid','frame':[128,128],'anchor':[64,64],'scale':2,'nativeCaptureScale':4,'footprint':[1,1],'height':.004,'directions':list('NESW'),'clips':{'scroll':{'frames':12,'fps':12,'loop':True,'nativeFirst':1,'nativeLastUnique':12,'closingFrame':13}},'sockets':{},'artStyle':{'revision':'warm-soft-native-water-round-01','nativeEditable':True,'lighting':'Optical emission field; no preferred horizontal light or cast shadow'}};write(C/'assetRecord.json',asset)
rig={'asset':'floor-underwater','groundRootObject':'floor-underwater__root','collection':'Floor Underwater Native Round01 scene collection','rootTransform':'identity ground origin; native facing rotation S0/E90/N180/W-90','clips':asset['clips'],'animation':{'owner':'Warm soft periodic aqua caustics node tree','channel':'Global one-second loop phase output.default_value','driver':'((frame - 1) % 12) / 12','spatialUV':'Exact local unit square(0,0)→(1,1); smooth integer-period trigonometric torus; same phase in every duplicate tile'},'sockets':{}};write(C/'rig.json',rig)
print(json.dumps({'frames':len(report['coverage']),'minimumAllAlpha':min(r[k] for r in report['coverage'] for k in ['rawAlphaMin','publishedAlphaMin','nativePatchAlphaMin','independentAlphaMin']),'closureMax':max(r['maxAbs'] for d in report['closure'].values() for r in d.values()),'probePairMax':max(x[k] for r in report['nativeShaderProbes'] for x in r['pairs'] for k in ['edgeValueMaxRGB','minusHMaxRGB','plusHMaxRGB','finiteGradientNumeratorMaxRGB','cornerEndpointRGBMax'])}))
