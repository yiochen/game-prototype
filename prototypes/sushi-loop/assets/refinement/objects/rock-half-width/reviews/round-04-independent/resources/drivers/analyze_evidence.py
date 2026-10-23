from pathlib import Path
from PIL import Image,ImageChops,ImageOps,ImageDraw,ImageStat
import json,hashlib,sys,shutil
B=Path(__file__).resolve().parents[2];obj=B.parents[1];O=B/'evidence';C=obj/'candidates/round-04';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'savedSourceReplay':[],'wholeBOXPublication':[],'nativeJoinReplay':[],'consumerReplay':[],'nativeVsIndependent':[]}
for d in 'NESW':
 a=Image.open(O/f'replay-{d}.png').convert('RGBA');b=Image.open(C/f'native/static/{d}/000.png').convert('RGBA');report['savedSourceReplay'].append({'direction':d,'decodedRGBAEqual':a.size==b.size and a.tobytes()==b.tobytes(),'maxChannelDifference':max(v[1] for v in ImageChops.difference(a,b).getextrema())})
 p=a.resize((384,704),Image.Resampling.BOX);pub=Image.open(C/f'frames/static/{d}/000.png').convert('RGBA');report['wholeBOXPublication'].append({'direction':d,'decodedRGBAEqual':p.tobytes()==pub.tobytes(),'alphaBounds':pub.getchannel('A').getbbox(),'frameSize':pub.size})
 a=Image.open(O/f'native-join-{d}.png').convert('RGBA');b=Image.open(C/f'joins/native-{d}.png').convert('RGBA');report['nativeJoinReplay'].append({'direction':d,'decodedRGBAEqual':a.size==b.size and a.tobytes()==b.tobytes(),'maxChannelDifference':max(v[1] for v in ImageChops.difference(a,b).getextrema())});a.resize((896,1280),Image.Resampling.BOX).save(O/f'native-join-{d}-published.png')
own=json.loads((O/'consumer/record.json').read_text());provided=json.loads((C/'consumer/record.json').read_text());index={(r['id'],r['case']['id']):r for r in provided['runs']}
for r in own['runs']:
 p=index[(r['id'],r['case']['id'])]
 for a,b in zip(r['records'],p['records']):
  assert (a['direction'],a['background'],a['kind'])==(b['direction'],b['background'],b['kind']);aa=Image.open(O/'consumer'/a['canvasFile']).convert('RGBA');bb=Image.open(C/'consumer'/b['nativeCanvasFile']).convert('RGBA');report['consumerReplay'].append({'mode':r['id'],'case':r['case']['id'],'direction':a['direction'],'background':a['background'],'kind':a['kind'],'decodedRGBAEqual':aa.size==bb.size and aa.tobytes()==bb.tobytes(),'nativeSmoothing':a['smoothing'],'ownCanvas':a['canvasFile'],'providedCanvas':b['nativeCanvasFile']})
# Raw common canvas comparison has exact one-pixel guard, not content fitting.
for d in 'NESW':
 r=next(r for r in own['runs'] if r['id']=='full-chromium' and r['case']['id']=='logical128-integer');it=next(p for p in r['records'] if p['direction']==d and p['background']=='gray' and p['kind']=='repeat');ind=Image.open(O/'consumer'/it['canvasFile']).convert('RGBA');nat=ImageOps.expand(Image.open(O/f'native-join-{d}-published.png').convert('RGBA'),border=1,fill=(0,0,0,0));assert nat.size==ind.size
 vals=list(zip(nat.getdata(),ind.getdata()));alphaLoss=sum(a[3]==255 and b[3]<255 for a,b in vals);opaqueMax=max(max(abs(a[i]-b[i]) for i in range(3)) for a,b in vals if a[3]==255 and b[3]==255);report['nativeVsIndependent'].append({'direction':d,'nativeWithGuard':nat.size,'independentCanvas':ind.size,'nativeOpaqueButConsumerNotOpaque':alphaLoss,'maxOpaqueRGBDifference':opaqueMax,'allDecodedEqual':nat.tobytes()==ind.tobytes()})
# Diagnostic actual port locations: unambiguous E/W top collar positions vs the interior stone groove.
sheet=Image.new('RGB',(768,420),(214,222,225));dr=ImageDraw.Draw(sheet);samples=[]
for row,d in enumerate('EW'):
 im=Image.open(O/f'native-join-{d}-published.png').convert('RGBA')
 for col,(name,y) in enumerate([('port',473),('interior crown sample',550),('port',729)]):
  crop=im.crop((416,y-18,480,y+18)).resize((256,144),Image.Resampling.NEAREST);bg=Image.new('RGBA',crop.size,(122,137,148,255));bg.alpha_composite(crop);sheet.paste(bg.convert('RGB'),(col*256,row*210+30));dr.text((col*256+5,row*210+5),f'{d} {name} native y{y}',fill=(15,25,35));samples.append({'direction':d,'label':name,'center':[448,y],'pixelsAtCenter':[{'y':yy,'RGBA':im.getpixel((448,yy))} for yy in range(y-3,y+4)]})
sheet.save(O/'true-port-versus-interior-groove.png');report['portCoordinateDiagnostic']={'cameraProjection':'expanded published root(448,768), cell256px, height179.2px/unit. At x±.5,z.93, top crossings y473.344 and729.344. The middle sample is an interior crown sample, not a claimed port crossing.','samples':samples,'finding':'Actual true port samples are separated from the interior crown sample. Do not infer a port failure solely from an interior facet boundary.'}
# Complete actual-resolution desktop screenshot coverage via lossless vertical strips.
strips=[]
for mode in ['full-chromium','headless-shell']:
 for case in ['logical128-integer','logical128-fractional']:
  src=C/f'consumer/{mode}-{case}.png';im=Image.open(src);d=O/'desktop-strips'/f'{mode}-{case}';d.mkdir(parents=True,exist_ok=True)
  for i,y in enumerate(range(0,im.height,1600)):
   box=(0,y,im.width,min(y+1600,im.height));dst=d/f'{i}.png';im.crop(box).save(dst);strips.append({'candidatePath':str(src.relative_to(C)),'crop':box,'path':str(dst.relative_to(obj)),'noRescale':True})
report['desktopFullResolutionStrips']=strips
# Freeze only actual loaded Pillow files, no runtime application duplication.
closure=[]
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f and '/PIL/' in f:
  p=Path(f);d=B/'resources/python-loaded/PIL'/p.name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);closure.append({'path':str(d.relative_to(obj)),'sha256':sha(d),'originalPath':str(p)})
report['actualUsedPillowClosure']=closure;report['pillowVersion']=Image.__version__;report['python']=sys.version
(O/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'sourceReplayAllEqual':all(r['decodedRGBAEqual'] for r in report['savedSourceReplay']),'publishedAllEqual':all(r['decodedRGBAEqual'] for r in report['wholeBOXPublication']),'nativeJoinsAllEqual':all(r['decodedRGBAEqual'] for r in report['nativeJoinReplay']),'consumerCanvasComparisons':len(report['consumerReplay']),'consumerAllEqual':all(r['decodedRGBAEqual'] for r in report['consumerReplay']),'nativeVsIndependent':report['nativeVsIndependent']}))
