from pathlib import Path
import json,math,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;B=S.parent;O=B/'candidates/round-01';C=O/'consumer';D=O/'diagnostics';D.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else list(v))+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def array(p):return np.asarray(Image.open(p).convert('RGBA')).astype(int)
def diff(a,b,mask=None):
 a=array(a) if isinstance(a,Path) else a;b=array(b) if isinstance(b,Path) else b
 if a.shape!=b.shape:return {'sameSize':False,'sizeA':list(a.shape),'sizeB':list(b.shape)}
 d=abs(a-b);sel=np.ones(a.shape[:2],bool) if mask is None else mask
 return {'sameSize':True,'pixels':int(sel.sum()),'decodedEqual':not np.any(d[sel]),'maxRGBA':d[sel].max(0).tolist() if np.any(sel) else [0]*4,'differentPixels':int((d.any(2)&sel).sum()),'alphaDifferentPixels':int(((d[:,:,3]!=0)&sel).sum())}
def area(v):return abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(v,v[1:]+v[:1]))/2)
def simplify(v):
 v=[list(p) for p in v];changed=True
 while changed and len(v)>3:
  changed=False
  for i in range(len(v)):
   a=np.array(v[i])-v[i-1];b=np.array(v[(i+1)%len(v)])-v[i]
   if np.linalg.norm(np.cross(a,b))<1e-7:v.pop(i);changed=True;break
 return v
def hull(points):
 p=sorted(set(tuple(v) for v in points))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lo=[];hi=[]
 for v in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
  lo.append(v)
 for v in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
n=load(O/'native-validation.json');contract=load(S/'resources/root-preparation-reconciliation-v1.json');captures=load(O/'capture-records.json');checks=[]
for view in n['views']:
 d=view['direction'];view['decodedReplay']=diff(O/'frames/static'/d/'000.png',O/'replay'/('hero-'+d+'.png'))
 tris=n['nativeGeometryMeasurements'][d]['supportTriangles'];edges={};pos={};winds=[]
 for tri in tris:
  winds.append(np.cross(np.array(tri[1])-tri[0],np.array(tri[2])-tri[0])[2])
  for a,b in zip(tri,tri[1:]+tri[:1]):
   a=tuple(round(x,7) for x in a);b=tuple(round(x,7) for x in b);key=tuple(sorted([a,b]));edges[key]=edges.get(key,0)+1;pos[a]=a;pos[b]=b
 boundary=[e for e,c in edges.items() if c==1];graph={}
 for a,b in boundary:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
 assert all(len(v)==2 for v in graph.values())
 start=min(graph);loop=[start];prev=None;cur=start
 while True:
  nex=next(v for v in graph[cur] if v!=prev)
  if nex==start:break
  loop.append(nex);prev,cur=cur,nex
 assert len(loop)==len(graph)
 simple=simplify(loop);expected=contract['support']['outline'];maxdist=max(min(np.linalg.norm(np.array(p)-q) for q in expected) for p in simple)
 checks.append({'direction':d,'actualFiniteBoundary':simple,'sourceFiniteBoundary':expected,'boundaryHausdorffMax':float(maxdist),'boundaryVertices':len(simple),'singleSimpleBoundaryLoop':True,'boundaryAndTriangleArea':area(simple),'expectedArea':contract['support']['area'],'supportTrianglesSameWinding':all(x<0 for x in winds),'triangleAreaAbsoluteError':view['supportAreaAbsoluteError'],'finiteSupportEqualWithin1e-6':maxdist<1e-6 and abs(area(simple)-contract['support']['area'])<1e-6 and len(simple)==10 and all(x<0 for x in winds)})
fields=[]
for item in n['fullFiniteCollarFields']:
 fs=item['faces'];cap=next(f for f in fs if f['cap']);sv=simplify(cap['mappedCanonicalVertices']);out=cap['expectedEntirePatchNormal'];av=sum((np.cross(p,q) for p,q in zip(sv,sv[1:]+sv[:1])),np.zeros(3))/2
 # Actual cap bounds define the normative three finite sections; full collar sides tile their four rectangular boundaries.
 yz=[[p[1],p[2]] for p in sv];lo=np.min(yz,axis=0);hi=np.max(yz,axis=0);patches=[]
 for normal in [(0,0,-1),(0,1,0),(0,0,1),(0,-1,0)]:
  faces=[f for f in fs if tuple(f['expectedEntirePatchNormal'])==normal]
  surface=sum(np.linalg.norm(sum((np.cross(p,q) for p,q in zip(f['mappedCanonicalVertices'],f['mappedCanonicalVertices'][1:]+f['mappedCanonicalVertices'][:1])),np.zeros(3)))/2 for f in faces)
  expected=(hi[0]-lo[0] if normal[2] else hi[1]-lo[1])*.08
  patches.append({'normal':list(normal),'polygons':len(faces),'actualArea':float(surface),'expectedArea':float(expected),'areaError':float(abs(surface-expected)),'completeFiniteCoverage':abs(surface-expected)<1e-6})
 fields.append({'object':item['object'],'side':item['side'],'orderedFiniteCap':sv,'canonicalSectionBoundsYZ':[lo.tolist(),hi.tolist()],'outwardOrientedArea':float(np.dot(av,out)),'outwardWinding':float(np.dot(av,out))>0,'fullCollarPatches':patches,'maxEntireFieldNormalError':max(f['maxVectorError'] for f in fs),'activeCanonicalMaterialsIdentical':all(f['canonicalMaterialDatablockIdentical'] for f in fs),'surfaceLaw':'The source-owned rail material datablocks are the exact approved canonical material graphs; their active height-only albedo, roughness, alpha, specular and normal-chain inputs are shared with unchanged canonical meshes in this native project. Normal vectors are baked into the corner local basis, then Object-to-World NORMAL and Normalize are active. Zero anisotropy makes tangent unnecessary; collar longitudinal derivatives zero. All4 proper root rotations preserve this correspondence.'})
write(O/'finite-contract-proof.json',{'pathBase':'object-root','supportChecks':checks,'wholeFiniteCollarChecks':fields,'tolerance':1e-6,'limits':'Field coverage and finite support evidence do not waive any localized visible defect.'})
# Eight actual browser runs; compare native decoded canvases independently from wholeCSS screenshots.
results=load(C/'results.json');runs=results['cases'];cross=[];comparisons=[]
for ident in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 a=next(x for x in runs if x['id']==ident and x['mode']=='full-chromium');b=next(x for x in runs if x['id']==ident and x['mode']=='bundled-headless-shell')
 native=[{'name':p.split(ident+'-')[1],**diff(C/p,C/q)} for p,q in zip(a['nativeCanvases'],b['nativeCanvases'])];cross.append({'case':ident,'nativeCrossModeDecodedEqual':all(x['decodedEqual'] for x in native),'native':native,'CSS':diff(C/a['cssScreenshot'],C/b['cssScreenshot'])})
 for j in range(0,len(a['nativeCanvases']),2):
  fa,fb=a['nativeCanvases'][j:j+2];xx=array(C/fa);yy=array(C/fb);tag=fa.split(ident+'-')[1].replace('-independent.png','');kind,d=tag.rsplit('-',1)
  fixture=next(f for f in a['evidence']['fixtures'] if f['kind']==kind and f['direction']==d);record=next(r for r in captures['records'] if r['kind']==kind and r['direction']==d);basis=record['camera']['calibration'];plan=fixture['plan'];offset=a['evidence']['case']['rootOffset'];ang=next(r['rootRotationZ'] for r in n['views'] if r['direction']==d)
  def project(p):
   x,y,z=p;wx=x*math.cos(ang)-y*math.sin(ang);wy=x*math.sin(ang)+y*math.cos(ang)
   return ((offset[0]-plan['x'])*2+wx*basis['unitX'][0]-wy*basis['unitDepth'][0]+z*basis['unitHeight'][0],(offset[1]-plan['y'])*2+wx*basis['unitX'][1]-wy*basis['unitDepth'][1]+z*basis['unitHeight'][1])
  masks={}
  for port in ['W','N']:
   for typ,span in [('full-collars',.08),('contact',0)]:
    im=Image.new('L',(xx.shape[1],xx.shape[0]));dr=ImageDraw.Draw(im)
    for ya,yb,za,zb in [(-.180000007,.180000007,.039999999,.200000003),(-.090000004,.090000004,.600000024,.74000001),(.200000003,.25999999,.159999996,.349999994)]:
     points=[]
     for along in [.5-span,.5+span]:
      for t in [ya,yb]:
       for z in [za,zb]:points.append(project((-along,t,z) if port=='W' else (-t,along,z)))
     pp=hull(points)
     if len(pp)>=3:dr.polygon(pp,fill=255)
     if typ=='contact':
      for x1,y1 in points:dr.ellipse((x1-2,y1-2,x1+2,y1+2),fill=255)
      if len(pp)>=2:dr.line(pp+[pp[0]],fill=255,width=5)
    path=D/(ident+'-'+tag+'-'+port+'-'+typ+'-mask.png');im.save(path);masks[port+'-'+typ]=np.asarray(im)>0
  local={key:diff(xx,yy,mask) for key,mask in masks.items()};visible=[]
  for label,bg in [('light',[238]*3),('gray',[128]*3),('dark',[21,25,35])]:
   va=np.round(xx[:,:,:3]*xx[:,:,3:4]/255+np.array(bg)*(1-xx[:,:,3:4]/255)).astype(int);vb=np.round(yy[:,:,:3]*yy[:,:,3:4]/255+np.array(bg)*(1-yy[:,:,3:4]/255)).astype(int);dd=abs(va-vb)
   visible.append({'background':label,'fullMaxRGB':dd.max(axis=(0,1)).tolist(),'contacts':{key:{'maxRGB':dd[mask].max(0).tolist(),'pixelsOver20':int(((dd>20).any(2)&mask).sum())} for key,mask in masks.items() if 'contact' in key}})
  comparisons.append({'case':ident,'kindDirection':tag,'rawRGBA':diff(xx,yy),'localFiniteMasks':local,'visibleOnBackgrounds':visible,'maskProjection':'Measured extended camera basis, real proper root rotation, actual finite W/N sections and actual consumer plan/root offset; full collars use .08 on each side, contact plane has2-nativepixel sampling allowance.'})
  if ident=='logical128-integer':
   delta=np.zeros(xx.shape,np.uint8);delta[:,:,:3]=np.clip(abs(xx[:,:,:3]-yy[:,:,:3])*8,0,255);delta[:,:,3]=255
   sh=Image.new('RGB',(xx.shape[1]*3,xx.shape[0]+24),(45,50,55));dr=ImageDraw.Draw(sh)
   for k,(label,im) in enumerate([('actual consumer',Image.fromarray(xx.astype('uint8'))),('actual native L',Image.fromarray(yy.astype('uint8'))),('raw RGB difference x8',Image.fromarray(delta))]):
    bg=Image.new('RGB',im.size,(128,128,128));bg.paste(im,mask=im.getchannel('A'));sh.paste(bg,(k*im.width,24));dr.text((k*im.width+4,4),label,fill='white')
   sh.save(D/(tag+'-native-vs-consumer.png'))
write(O/'consumer-analysis.json',{'runs':len(runs),'versions':sorted(set(r['browserVersion'] for r in runs)),'zeroPageErrors':all(not r['errors'] for r in runs),'nativeNearestAfterEveryResize':all(not f['nativeSmoothing'] and not f['displayCanvasSmoothing'] for r in runs for f in r['evidence']['fixtures']),'helpers':{p:sha(S/'consumer'/p) for p in ['world-sprite-raster.js','sprite-layout.js']},'crossMode':cross,'nativeVsIndependent':comparisons,'interpretation':'Whole raw RGBA, background-composited visibility and projected contact/collar differences are retained separately. Broad finite-light and exterior raster residuals remain honest. No numerical evidence establishes aesthetic approval or waives a visible contact defect.'})
# Compact actual-use previews. Layout-only sheets never replace raw hero/consumer art.
def sheet(rows,path,scale=.5):
 tilew=math.ceil(rows[0][0][1].width*scale);tileh=math.ceil(rows[0][0][1].height*scale)+22;out=Image.new('RGB',(tilew*4,tileh*len(rows)),(45,50,55));dr=ImageDraw.Draw(out)
 for j,row in enumerate(rows):
  for i,(label,im) in enumerate(row):
   bg=Image.new('RGB',im.size,(128,128,128));bg.paste(im,mask=im.getchannel('A'));bg=bg.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);out.paste(bg,(i*tilew,j*tileh+22));dr.text((i*tilew+4,j*tileh+4),label,fill='white')
 out.save(path)
rows=[[(kind+' '+d,Image.open(O/kind/(d+'.png')).convert('RGBA')) for d in 'NESW'] for kind in ['middle-L','mixed-edge-L']];sheet(rows,O/'native-assemblies-logical128.png')
run=next(r for r in runs if r['mode']=='full-chromium' and r['id']=='logical128-integer');rows=[]
for kind in ['middle-L','mixed-edge-L']:
 rows.append([(kind+' '+d,Image.open(C/next(f for f in run['nativeCanvases'] if f.endswith(kind+'-'+d+'-independent.png'))).convert('RGBA')) for d in 'NESW'])
sheet(rows,O/'consumer-assemblies-logical128.png')
phone=next(r for r in runs if r['mode']=='bundled-headless-shell' and r['id']=='phone32-fractional');shutil.copyfile(C/phone['cssScreenshot'],O/'phone32-actual-css.png')
# Source-owned native metadata, recorded from actual saved candidate.
hero=next(r for r in captures['records'] if r['kind']=='hero');cam={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':2,'fps':12,'camera':n['actualCamera'],'calibration':hero['camera']['calibration'],'nativeFrame':[384,704],'nativeRoot':[192,496],'publication':'Exact direct native2x PNG identity; no reduction','sourceSHA256':n['sourceSHA256']};write(O/'published-camera.json',cam)
asset={'id':'wreck-corner','projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'scale':2,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True}},'footprint':[1,1],'height':.78,'sockets':{},'ports':json.loads(n['rootProperties']['ports']),'nonblocking':False,'depth_layer':'world','directions':list('NESW'),'nativeCollection':'S33_PROP_wreck-corner.001','nativeRoot':'wreck-corner__root.001','sourceSHA256':n['sourceSHA256']};write(O/'assetRecord.json',asset)
rig={'assetId':'wreck-corner','fps':12,'source':'source/round-01-recipe.py','static':True,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'actions':n['ownActions']}},'armatures':[],'footprint':[1,1],'projection':'square-top-front-oblique','groundRootObject':'wreck-corner__root.001','sockets':{},'actualNativeRig':{'owners':n['staticOwners'],'lights':n['lights'],'world':n['world'],'sourceSHA256':n['sourceSHA256']},'sourceFiles':{'round-01-recipe.py':sha(S/'round-01-recipe.py')},'status':'native-static-candidate-awaiting-independent-review'};write(O/'rig.json',rig)
summary={'asset':'wreck-corner','round':'round-01','nativeValidation':'candidates/round-01/native-validation.json','sourceSHA256':n['sourceSHA256'],'lighting':'Exact approved symmetric overhead195W/four114W disk8 fills; world.28; shadows off; all4 one recipe','camera':cam,'technicalChecks':{'properAll4MeasuredFacings':len(n['views'])==4,'savedSourceReplaysDecodedEqual':all(v['decodedReplay']['decodedEqual'] for v in n['views']),'savedSourceReplayMaxRGBAAtMost1':all(max(v['decodedReplay']['maxRGBA'])<=1 for v in n['views']),'nativeEnvelopeAll4':all(not v['rawFiniteEnvelopeViolations'] for v in n['views']),'finiteLowestSupportAll4':all(c['finiteSupportEqualWithin1e-6'] for c in checks),'completeFiniteCollarCoverage':all(p['completeFiniteCoverage'] for f in fields for p in f['fullCollarPatches']),'collarEntireFieldNormalErrorUnder1e-6':all(f['maxEntireFieldNormalError']<1e-6 for f in fields),'capsOutward':all(f['outwardWinding'] for f in fields),'eightBrowserRuns':len(runs)==8,'browser153':all(r['browserVersion'].startswith('153.') for r in runs),'zeroPageErrors':all(not r['errors'] for r in runs),'noExternalBlenderDependencies':not n['externalLibraries'] and not n['imageTextureNodes']},'evidence':{'finiteGeometryAndFields':'candidates/round-01/finite-contract-proof.json','consumer':'candidates/round-01/consumer/results.json','analysis':'candidates/round-01/consumer-analysis.json','fieldConstruction':'candidates/round-01/field-construction.json'},'approval':'pending original independent judge; no editor approval','limitations':'Exact canonical contact fields and source replay do not establish visible seam acceptance. Native-vs-independent full and localized residuals are preserved for judge assessment.'};write(O/'validation.json',summary)
# Add decoded replay results directly to packet-bound nativeValidation ledger; measured views remain there.
write(O/'native-validation.json',n)
print('CHECKS',summary['technicalChecks']);print('CROSS_MODE_CSS',[(c['case'],c['CSS']['maxRGBA']) for c in cross]);print('NATIVE_CONTACT_RESIDUALS',[(c['kindDirection'],[(k,v['maxRGBA']) for k,v in c['localFiniteMasks'].items() if 'contact' in k]) for c in comparisons if c['case']=='logical128-integer'])
