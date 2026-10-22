import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent;C=O/'candidates/round-01';sys.path.insert(0,str(P/'resources/python-pillow'))
from PIL import Image,ImageDraw,ImageChops,ImageStat
out=P/'apng-decoded';out.mkdir(exist_ok=True)
packet=json.loads((C/'packet.json').read_text());report={'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'declaredRecords':[],'animations':[],'nativeImageSummary':[]}
for kind in ('candidateRenders','previews'):
 for name,r in packet[kind].items():
  f=C/r['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];im=Image.open(f)
  report['declaredRecords'].append({'kind':kind,'name':name,'path':r['path'],'sha256':r['sha256'],'size':list(im.size),'frames':getattr(im,'n_frames',1)})
  if f.suffix!='.apng':continue
  direction=name[-1];repeat=name.startswith('repeated-');cell=288 if repeat else 128
  sheet=Image.new('RGB',(4*(cell+12),3*(cell+40)),(238,238,238));draw=ImageDraw.Draw(sheet);frames=[]
  for i in range(im.n_frames):
   im.seek(i);frame=im.convert('RGBA');duration=im.info.get('duration');comparable=Image.open(C/('independent-patch' if repeat else 'frames/scroll')/direction/(str(i).zfill(3)+'.png')).convert('RGBA')
   if comparable.size!=frame.size:comparable=comparable.resize(frame.size,Image.Resampling.LANCZOS)
   delta=ImageChops.difference(frame,comparable)
   frames.append({'index':i,'durationMs':duration,'rgbaSHA256':hashlib.sha256(frame.tobytes()).hexdigest(),'referenceImage':str((C/('independent-patch' if repeat else 'frames/scroll')/direction/(str(i).zfill(3)+'.png')).relative_to(C)),'referenceDifferenceExtrema':delta.getextrema(),'referenceMeanAbs':ImageStat.Stat(delta).mean})
   thumb=frame.resize((cell,cell),Image.Resampling.LANCZOS).convert('RGB');x=i%4*(cell+12);y=i//4*(cell+40);sheet.paste(thumb,(x+4,y+28));draw.text((x+4,y+6),f'{name} phase{i} / {duration:.3f}ms',fill='black')
  target=out/(name+'.png');sheet.save(target)
  report['animations'].append({'path':r['path'],'sheet':str(target.relative_to(O)),'size':list(im.size),'frameCount':im.n_frames,'loop':im.info.get('loop'),'totalDurationMs':sum(f['durationMs'] for f in frames),'frames':frames})
for direction in 'NESW':
 for i in range(13):
  for kind in ('native/scroll','frames/scroll','native-patch','independent-patch'):
   f=C/kind/direction/(str(i).zfill(3)+'.png');im=Image.open(f).convert('RGBA');a=im.getchannel('A');hist=a.histogram();report['nativeImageSummary'].append({'path':str(f.relative_to(C)),'alphaRange':a.getextrema(),'nonOpaque':sum(hist[:-1]),'rgbaSHA256':hashlib.sha256(im.tobytes()).hexdigest()})
(P/'media-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'declared':len(report['declaredRecords']),'animations':[{'path':a['path'],'size':a['size'],'frames':a['frameCount'],'duration':a['totalDurationMs']} for a in report['animations']],'imageAudit':len(report['nativeImageSummary']),'opaqueFailures':sum(bool(f['nonOpaque']) for f in report['nativeImageSummary'])},indent=2))
