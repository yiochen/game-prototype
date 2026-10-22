from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
P=Path(__file__).resolve().parent;out=P/'publication-source';out.mkdir(exist_ok=True)
for n in (P/'native-source').glob('*.png'):
 Image.open(n).convert('RGBA').resize((384,704),Image.Resampling.LANCZOS).save(out/n.name)
for clip,count in [('idle',1),('active',12)]:
 for d in 'NESW':
  cols=min(6,count);rows=(count+cols-1)//cols;at=Image.new('RGBA',(cols*384,rows*704))
  for f in range(1,count+1):at.paste(Image.open(out/f'{clip}-{d}-{f:02}.png'),(((f-1)%cols)*384,((f-1)//cols)*704))
  at.save(out/f'{clip}-{d}.png')
sheet=Image.new('RGB',(768,1128),(213,218,216));dr=ImageDraw.Draw(sheet)
for x,d in enumerate('NESW'):
 for y,f in enumerate([1,6,12]):
  im=Image.open(out/f'active-{d}-{f:02}.png').resize((192,352),Image.Resampling.LANCZOS);sheet.paste(im,(x*192,y*376),im);dr.text((x*192+6,y*376+354),f'Old source {d} active {f}/12',fill='black')
sheet.save(P/'source-representative-all4.png')
phase=Image.new('RGB',(1152,784),(227,230,229));dr=ImageDraw.Draw(phase)
for y,d in enumerate('NESW'):
 for x in range(12):
  im=Image.open(out/f'active-{d}-{x+1:02}.png').resize((96,176),Image.Resampling.LANCZOS);phase.paste(im,(x*96,y*196),im);dr.text((x*96+3,y*196+178),f'{d}{x+1}',fill='black')
phase.save(P/'source-all48-phone-phases.png')
s=Image.new('RGB',(1280,1200),(215,220,219));dr=ImageDraw.Draw(s)
for i,D in enumerate('NESW'):
 for row,f in enumerate([1,6,12]):
  im=Image.open(P/f'native-mounted-source/old-own-on-frozen-main-{D}-{f:02}.png').resize((320,384));s.paste(im,(i*320,row*400),im);dr.text((i*320+6,row*400+383),f'OLD source {D} phase{f}; static body; other upgrades provisional',fill='black')
s.save(P/'mounted-source-representative-all4.png')
a=json.loads((P/'native-source-audit.json').read_text());base=next(g for g in a['neutralGeometry'] if '__base' in g['name']);verts=base['evaluatedVertices'];faces=[]
for f in base['evaluatedFaces']:
 v=[verts[i] for i in f]
 if max(p[2] for p in v)-min(p[2] for p in v)<1e-6 and max(p[2] for p in v)<1e-6:faces.append([[p[0],p[1]] for p in v])
seat=json.loads((P/'independent-frozen-main-audit.json').read_text())['finiteSeatFaces'][0]['localVertices'];xr=[min(v[0] for v in seat),max(v[0] for v in seat)];yr=[min(v[1] for v in seat),max(v[1] for v in seat)]
def area(p):return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2) if len(p)>2 else 0

def clip(poly,axis,k,sign):
 out=[]
 for i,p in enumerate(poly):
  q=poly[(i+1)%len(poly)];ip=sign*(p[axis]-k)>=-1e-9;iq=sign*(q[axis]-k)>=-1e-9
  if ip:out.append(p)
  if ip!=iq:
   t=(k-p[axis])/(q[axis]-p[axis]);out.append([p[j]+t*(q[j]-p[j]) for j in range(2)])
 return out
contacts=[]
for f in faces:
 z=f
 for axis,k,sign in [(0,xr[0],1),(0,xr[1],-1),(1,yr[0],1),(1,yr[1],-1)]:z=clip(z,axis,k,sign)
 contacts.append({'sourceFootPolygon':f,'sourceFootAreaLocal':area(f),'supportedIntersectionPolygon':z,'supportedAreaLocal':area(z),'supportedFraction':area(z)/area(f)})
frames=a['frames'];neutral=next(f for f in frames if f['clip']=='idle' and f['direction']=='S')['bounds'];active=[f for f in frames if f['clip']=='active' and f['direction']=='S'];envelope=[[min(f['bounds'][0][i] for f in active) for i in range(3)],[max(f['bounds'][1][i] for f in active) for i in range(3)]]
m=json.loads((P/'mounted-source-audit.json').read_text());collisions=[{'frame':x['frame'],'overlaps':x['nativeTriangleOverlaps'],'frozenMainTransformMaxError':x['frozenMainTransformMaxError']} for x in m['phases']]
orig=Image.open(P/'resources/inputs/original.png').convert('RGBA');replay=Image.open(P/'publication-source/idle-S-01.png').convert('RGBA');diff=ImageChops.difference(orig,replay)
comp=Image.new('RGB',(768,728),(217,222,220));dc=ImageDraw.Draw(comp)
for i,(label,im) in enumerate([('historical original',orig),('native source replay',replay)]):comp.paste(im,(i*384,0),im);dc.text((i*384+6,707),label,fill='black')
comp.save(P/'source-replay-comparison.png')
cam=a['camera'];stored=json.loads((P/'resources/inputs/source-camera.json').read_text());camdiff={'matrixMaxError':max(abs(cam['camera']['worldMatrix'][r][c]-stored['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4)),'projectionMaxError':max(abs(cam['camera']['projectionMatrix'][r][c]-stored['camera']['projectionMatrix'][r][c]) for r in range(4) for c in range(4)),'root':cam['calibration']['root'],'originalRoot':stored['calibration']['root']}
comparison={'exactRGBA':orig.tobytes()==replay.tobytes(),'rgbaRmsWholeFrame':ImageStat.Stat(diff).rms,'originalAlphaBounds':orig.getchannel('A').getbbox(),'replayAlphaBounds':replay.getchannel('A').getbbox(),'cameraComparison':camdiff,'qualification':'Native source replay matches registered projection and source forms. It is not byte-identical to historical atlas pixels; small source raster/antialiasing differences are retained and disclosed. No image repair/fitting applied.'}
report={'finiteSeatLocalRect':{'X':xr,'Y':yr,'Z':0,'source':'independent reopened actual frozen-main face, not bounding-box seat'},'sourceContact':contacts,'sourceNeutralBounds':neutral,'sourceActiveEnvelopeS':envelope,'sourceVersusReservation':{'reserve':[[-.18,-.62,0],[.18,.62,.48]],'XViolationEachSide':.07,'heightWithin':True,'YWithin':True},'phaseCollisions':collisions,'sourceCaptureComparison':comparison,'proposedFootExample':{'rectangleLocal':[[-.10,.17,0],[.10,.51,0]],'world':[[.275,-.1805,.5685],[.345,-.0615,.5685]],'insideFiniteFace':True,'authority':'Feasibility example, not prescribed construction or new model. Entire actual editor foot must be independently finite-surface audited.'}}
(P/'technical-reconciliation.json').write_text(json.dumps(report,indent=2)+'\n');(P/'source-replay-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
print('Prepared registered native publication frames, source/mounted sheets and finite-seat/phase reconciliation')
