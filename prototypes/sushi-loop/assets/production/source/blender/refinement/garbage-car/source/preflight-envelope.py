from pathlib import Path
import json
s=Path(__file__).with_name('capture-existing-round01.py').read_text();exec(s[:s.index('frames=[]')],globals())
rows=[]
for clip,n in [('idle',1),('highlighted',13),('clearance',12)]:
 for f in range(1,n+1):
  apply(clip,f,'S');rows.append({'clip':clip,'frame':f,'geometry':geometry()})
b=json.loads((P/'brief.json').read_text());src=b['constraints']['measuredNativeContract']['nativeContract']['animation']['clearance']['transientSourceSBoundsAllPhases'];trans=[[v-.02 for v in src[0]],[v+.02 for v in src[1]]];idle=[[-1.51,-1,-.015],[1.5,1,1.32]];errors=[]
for row in rows:
 env=trans if row['clip']=='clearance' else idle;bd=row['geometry']['bounds'];over=max([env[0][i]-bd[0][i] for i in range(3)]+[bd[1][i]-env[1][i] for i in range(3)]+[0])
 if over>2e-6:errors.append([row['clip'],row['frame'],over,bd])
(OUT/'preflight-envelope.json').write_text(json.dumps({'errors':errors,'frames':rows},indent=2));print('PREFLIGHT ENVELOPE ERRORS',errors)
