from pathlib import Path
import json,math
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1]
a=json.loads((p/'evidence/native-measurements.json').read_text());tris=[[v[:2] for v in t] for t in a['groundLaw']['triangles']]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return [a[0]-b[0],a[1]-b[1]]
def point(seg,t):return [seg[0][j]+t*(seg[1][j]-seg[0][j]) for j in (0,1)]
def inside(q,t):
 s=[cross(sub(t[(i+1)%3],t[i]),sub(q,t[i])) for i in range(3)]
 return min(s)>=-1e-12 or max(s)<=1e-12
def union(q):return any(inside(q,t) for t in tris)
edges=[(t[i],t[(i+1)%3]) for t in tris for i in range(3)];boundary=[]
for a1,b1 in edges:
 r=sub(b1,a1);cuts=[0,1];rr=sum(x*x for x in r)
 for a2,b2 in edges:
  s=sub(b2,a2);den=cross(r,s);delta=sub(a2,a1)
  if abs(den)>1e-13:
   t=cross(delta,s)/den;u=cross(delta,r)/den
   if -1e-9<=t<=1+1e-9 and -1e-9<=u<=1+1e-9:cuts.append(max(0,min(1,t)))
  elif abs(cross(delta,r))<1e-12:
   for v in [a2,b2]:
    t=sum(sub(v,a1)[j]*r[j] for j in (0,1))/rr
    if -1e-9<=t<=1+1e-9:cuts.append(max(0,min(1,t)))
 cuts=sorted(set(round(v,12) for v in cuts))
 for l,h in zip(cuts,cuts[1:]):
  if h-l<1e-10:continue
  A=point((a1,b1),l);B=point((a1,b1),h);M=point((a1,b1),(l+h)/2);d=sub(B,A);L=math.hypot(*d);n=[-d[1]/L,d[0]/L];eps=1e-7
  left=union([M[j]+eps*n[j] for j in (0,1)]);right=union([M[j]-eps*n[j] for j in (0,1)])
  if left!=right:boundary.append((A,B) if left else (B,A))
key=lambda p:tuple(round(x,9) for x in p)
unique={(key(a),key(b)) for a,b in boundary};todo=set(unique);loops=[]
while todo:
 start,nextp=todo.pop();loop=[start,nextp]
 while loop[-1]!=start:
  options=[e for e in todo if e[0]==loop[-1]]
  if len(options)!=1:raise RuntimeError(('boundary ambiguity',loop[-1],options))
  e=options[0];todo.remove(e);loop.append(e[1])
 # remove collinear split points from outline only
 changed=True
 while changed:
  changed=False;v=loop[:-1]
  for i in range(len(v)):
   if abs(cross(sub(v[i],v[i-1]),sub(v[(i+1)%len(v)],v[i])))<1e-9:
    v.pop(i);loop=v+[v[0]];changed=True;break
 area=sum(cross(loop[i],loop[i+1]) for i in range(len(loop)-1))/2
 loops.append({'vertices':loop,'signedArea':area,'role':'outer' if area>0 else 'hole'})
result={'method':'Exact saved evaluated Z0 triangles; split all pairwise segment intersections, classify two-sided union coverage, discard interior overlap/fold edges, trace oriented outer/inner boundary. Numeric epsilon1e-7 normal offset/round1e-9 adjacency; raw float triangles retained.','triangleCount':len(tris),'boundaryLoops':loops,'unionArea':sum(x['signedArea'] for x in loops),'holes':[x for x in loops if x['role']=='hole'],'interiorTopology':'Two upward-facing Z0 bottom triangles and crossing source quad edges are accidental folded native construction, not contact requirements. Their internal edges, triangle orientation/count and overlap are not frozen. Clean interior reconstruction is permitted while preserving this finite exterior/contact set, true ports and clearance.','ambiguity':'No enclosed Z0 support hole is measured. The functional keep-clear regions are outside the finite outer outline; nominal support_cells[0,0] is not an opaque square. Interior construction may be remeshed and consistently oriented.','canonicalCollars':'Both0.08-width collars lie wholly within the outer footprint and are unaffected by source interior folds.'}
(p/'evidence/finite-support-outline.json').write_text(json.dumps(result,indent=2)+'\n')
im=Image.new('RGB',(760,780),'#f4f1e8');d=ImageDraw.Draw(im)
def px(v):return (380+v[0]*600,410-v[1]*600)
d.rectangle([px([-.5,.5]),px([.5,-.5])],outline='#aaa79e',width=2)
for t in tris:d.polygon([px(v) for v in t],fill='#b2d5e4',outline='#7c9dac',width=1)
for loop in loops:d.line([px(v) for v in loop['vertices']],fill='#214d71',width=4)
d.rectangle([px([-.5,.38]),px([-.42,-.38])],fill='#2b9c7b')
d.rectangle([px([-.38,.5]),px([.38,.42])],fill='#2b9c7b')
d.line([px([-.5,0]),px([0,0]),px([0,.5])],fill='#b06558',width=2)
for v,label in [([-.5,0],'W'),([0,.5],'N')]:
 q=px(v);d.ellipse((q[0]-5,q[1]-5,q[0]+5,q[1]+5),fill='#af4234');d.text((q[0]+10,q[1]-15),label,fill='#731e18')
d.text((20,18),'REEF-CORNER / S / actual finite Z0 support',fill='#16384d')
d.text((20,42),'Blue: evaluated triangle union; green: feasible unchanged canonical collars',fill='#16384d')
d.text((20,65),'Thin blue internal fold/overlap edges are measurement evidence, not modeling locks.',fill='#16384d')
d.text((20,735),'Square is nominal1-cell extent. Registered ports remain W(-.5,0), N(0,.5).',fill='#16384d')
im.save(p/'evidence/support-layout.png')
print(json.dumps(result,indent=2))
