from pathlib import Path
import json,math,hashlib
from PIL import Image,ImageChops,ImageDraw
P=Path(__file__).resolve().parents[1];RES=P/'resources';B=P/'baseline'
# Native evidence media remain unchanged. Sheets are inspection aids only.
def sheet(files,out,scale=1,bg=(128,128,128)):
 imgs=[]
 for label,p in files:
  im=Image.open(p).convert('RGBA');canvas=Image.new('RGB',im.size,bg);canvas.paste(im,mask=im.getchannel('A'))
  if scale!=1:canvas=canvas.resize(tuple(round(v*scale)for v in canvas.size),Image.Resampling.NEAREST)
  imgs.append((label,canvas))
 w=sum(i.width for _,i in imgs);h=max(i.height for _,i in imgs)+24;outim=Image.new('RGB',(w,h),(45,50,55));d=ImageDraw.Draw(outim);x=0
 for l,i in imgs:d.text((x+4,4),l,fill='white');outim.paste(i,(x,24));x+=i.width
 outim.save(out)
for kind in ['original-canonical-rig','middle-L','mixed-edge-L']:
 for scale,label in [(1,'native'),(.5,'logical128'),(.125,'phone32')]:sheet([(d,B/kind/(d+'.png'))for d in 'NESW'],B/(kind+'-'+label+'.png'),scale)
historical=Image.open(B/'historical-native4-S.png').convert('RGBA');reduced=historical.resize((384,704),Image.Resampling.LANCZOS);reduced.save(B/'historical-published2-S.png');original=Image.open(RES/'object/inputs/original.png').convert('RGBA')
def diff(a,b):
 import numpy as np
 x=np.array(a).astype(int);y=np.array(b).astype(int);d=abs(x-y);return {'sameSize':a.size==b.size,'decodedEqual':bool((d==0).all()),'maxRGBA':d.reshape(-1,4).max(0).tolist(),'differentPixels':int((d!=0).any(2).sum()),'alphaDifferentPixels':int((d[:,:,3]!=0).sum())}
replay=diff(reduced,original);(P/'source-replay-comparison.json').write_text(json.dumps({'historical4to2':'Full frame LANCZOS historical control only; new candidate uses exact identity direct2x','comparison':replay,'unrelatedSavedCamera':'Original saved library camera is presentation35/aspect1; own registered capture reconstructs55.0079798/aspect1.22065556; do not borrow saved presentation camera'},indent=2)+'\n');sheet([('original fixed',RES/'object/inputs/original.png'),('faithful historical replay',B/'historical-published2-S.png')],B/'source-replay-comparison.png')
# Original finite support boundary, not a square floor or convex-hull replacement.
a=json.loads((P/'original-native-audit.json').read_text());tris=a['support']['facesAtZ04'];edges={};positions={}
for t in tris:
 vs=t['vertices']
 for x,y in zip(vs,vs[1:]+vs[:1]):
  kx=tuple(round(v,8)for v in x);ky=tuple(round(v,8)for v in y);positions[kx]=x;positions[ky]=y;key=tuple(sorted([kx,ky]));edges[key]=edges.get(key,0)+1
boundary=[list(k)for k,n in edges.items() if n==1];graph={}
for x,y in boundary:graph.setdefault(tuple(x),[]).append(tuple(y));graph.setdefault(tuple(y),[]).append(tuple(x))
start=min(graph);loop=[start];prev=None;cur=start
while True:
 nxt=next(v for v in graph[cur] if v!=prev)
 if nxt==start:break
 loop.append(nxt);prev,cur=cur,nxt
area=sum(x[0]*y[1]-y[0]*x[1]for x,y in zip(loop,loop[1:]+loop[:1]))/2
if area<0:loop=loop[::-1];area=-area
(P/'finite-support-outline.json').write_text(json.dumps({'pathBase':'object-root','sourceAudit':'reviews/preparation-v1/original-native-audit.json','supportZ':a['support']['z'],'outlineCCW':loop,'area':area,'triangleArea':a['support']['totalArea'],'geometricZ0Intersection':False,'meaning':'Actual finite lowest lower-rail patch. Interior open bays and exterior cutouts are intentional. No fullsquare ground floor is inferred.','authoringBudgetProposal':{'finiteXYConvexHullCCW':a['finiteXYConvexHullCCW'],'zRange':[.04,.78],'tolerance':1e-6,'status':'proposed to root; no perpart boxes/3Dhull/oldcounts lock'}},indent=2)+'\n')
print('replay',replay,'support',area,len(loop))
