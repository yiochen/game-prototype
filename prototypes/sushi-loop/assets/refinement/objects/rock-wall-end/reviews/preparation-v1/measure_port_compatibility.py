from pathlib import Path
import json,math
OUT=Path(__file__).resolve().parent
d=json.loads((OUT/'canonical-port-samples.json').read_text())['samples']
reports={}
for reversed in [False,True]:
 rows=[]
 for a in d['E']:
  b=min(d['W'],key=lambda b:(a['y']-(-b['y'] if reversed else b['y']))**2+(a['z']-b['z'])**2)
  dist=math.hypot(a['y']-(-b['y'] if reversed else b['y']),a['z']-b['z'])
  col=max(abs(x-y) for x,y in zip(a['colorLinearRGBA'][:3],b['colorLinearRGBA'][:3]))
  an=a['meanCornerNormal'];bn=b['meanCornerNormal'];bn=[-bn[0],-bn[1],bn[2]] if reversed else bn
  nd=math.sqrt(sum((x-y)**2 for x,y in zip(an,bn)))
  rows.append({'y':a['y'],'z':a['z'],'profileDelta':dist,'linearColorMaximumChannelDelta':col,'meanCornerNormalDelta':nd})
 reports['reversed-middle' if reversed else 'authored-same-facing']={'sampleCount':len(rows),'maxProfileDelta':max(r['profileDelta'] for r in rows),'maxLinearColorChannelDelta':max(r['linearColorMaximumChannelDelta'] for r in rows),'maxMeanCornerNormalDelta':max(r['meanCornerNormalDelta'] for r in rows),'worstColor':max(rows,key=lambda r:r['linearColorMaximumChannelDelta']),'samples':rows}
(OUT/'port-compatibility-measurements.json').write_text(json.dumps({'meaning':'Canonical middle E-to-W versus E-to-mirrored-W after180-degree rotation. No end candidate is present.','measurements':reports},indent=2)+'\n')
