from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];r=json.loads((P/'original-native-inspection-v4.json').read_text());vs=[v for o in r['objects']for v in o['vertices']];pts=sorted(set(tuple(v[:2])for v in vs));cross=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);lo=[];hi=[]
for v in pts:
 while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
 lo.append(v)
for v in reversed(pts):
 while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
 hi.append(v)
hull=lo[:-1]+hi[:-1]
(P/'raw-authoring-envelope.json').write_text(json.dumps({'source':'Own enabled raw authored mesh vertices with evaluated object transforms, before four hardware bevel modifiers','sourceNativeEvidence':'reviews/preparation-v1/original-native-inspection-v4.json','rawXYConvexHullCCW':hull,'rawBounds':r['bounds'],'evaluatedXYHull':'reviews/preparation-v1/original-native-audit.json finiteXYConvexHullCCW','meaning':'Raw13point authoring hull deliberately retains native authored budget before hardware bevel trims. Evaluated11point hull is evidence, not a further lock. No perpart/3Dhull/oldcounts restriction.'},indent=2)+'\n')
print('RAW authoring hull',len(hull))
