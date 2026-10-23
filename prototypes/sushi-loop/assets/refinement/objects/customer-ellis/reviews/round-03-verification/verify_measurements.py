import json, math, hashlib, collections, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops
P=Path(__file__).resolve().parents[2];V=P/'reviews/round-03-verification'; C=P/'candidates/round-03'
def read(f):return json.loads((P/f).read_text())
def err(a,b):
 if isinstance(a,dict):return max([err(a[k],b[k]) for k in a]+[0]) if set(a)==set(b) else float('inf')
 if isinstance(a,list):return max([err(x,y) for x,y in zip(a,b)]+[0]) if len(a)==len(b) else float('inf')
 if isinstance(a,(int,float)) and not isinstance(a,bool):return abs(a-b)
 return 0 if a==b else float('inf')
def norm(s):return s.replace('S10 meal ','')
def metrics(im,t):
 a=np.asarray(im.getchannel('A')); ys,xs=np.nonzero(a>=t);y=ys.max(); xx=np.nonzero(a[y]>=t)[0]
 return {'size':list(im.size),'visibleWidthPixels':int(xs.max()-xs.min()+1),'bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'supportPixelCenterTop':[float((xx.min()+xx.max()+1)/2),float(y+.5)]}
def localpoint(food,met):
 w,h=met['size'];x,y=met['supportPixelCenterTop']; uv=food['uv']; v=food['vertices'];u=x/w; vv=1-y/h
 return np.array([v[0][0]+(v[1][0]-v[0][0])*(u-uv[0][0])/(uv[1][0]-uv[0][0]),v[0][1]+(v[3][1]-v[0][1])*(vv-uv[0][1])/(uv[3][1]-uv[0][1]),0,1])
brief=read('brief.json'); envelope=brief['constraints']['functionalGeometryEnvelope']; out={'modes':{},'food':{},'phase':{}}
allown={}
for mode,foodname in [('main','dish-cucumber'),('runtime','dish-salmon')]:
 a=read(f'reviews/round-03-verification/{mode}-audit.json');o=read(f'reviews/{mode}-audit.json'); os={(s['clip'],s['direction'],s['frame']):s for s in o['samples']}; errors=collections.defaultdict(float); bounds={};fails=[];vis=collections.Counter()
 for s in a['samples']:
  key=(s['clip'],s['direction'],s['frame']);orig=os[key]; allown[(mode,*key)]=s
  for k in ['rootMatrix','contacts']:errors[k]=max(errors[k],err(s[k],orig[k]))
  for k in ['rootMatrix','planeMatrix','localLocation','yaw','visible','authoredHideViewport']:errors['food.'+k]=max(errors['food.'+k],err(s['food'][k],orig['food'][k]))
  b=np.array(s['nativeBodyBoundsWorld']);clip=s['clip'].replace('_','-'); z=envelope['perClipBodyZWorld'][clip];tol=envelope['numericalToleranceWorld'];vis[clip]+=int(s['food']['visible']);
  if abs(b[:,:2]).max()>.5+tol or b[0,2]<z[0]-tol or b[1,2]>z[1]+tol:fails.append(list(key))
  if clip not in bounds:bounds[clip]=b.copy()
  else:bounds[clip][0]=np.minimum(bounds[clip][0],b[0]);bounds[clip][1]=np.maximum(bounds[clip][1],b[1])
 actions={clip:[(r['ownerType'],norm(r['ownerName']),r['curveDigest'],r['keyframeCount']) for r in rs] for clip,rs in a['actions'].items()}; oldactions={clip:[(r['ownerType'],norm(r['ownerName']),r['curveDigest'],r['keyframeCount']) for r in rs] for clip,rs in o['actions'].items()}
 out['modes'][mode]={'samples':len(a['samples']),'sourceSHA256':a['sourceSHA256'],'cameraError':err(a['camera'],o['camera']),'rootMatrixError':err(a['root']['matrix'],o['root']['matrix']),'restSHA256':a['armature']['restSHA256'],'restEqual':a['armature']['rest']==o['armature']['rest'],'actionsEqual':actions==oldactions,'nativeActions':sum(map(len,actions.values())),'maxErrors':dict(errors),'envelopeFailures':fails,'perClipBoundsWorld':{k:v.tolist() for k,v in bounds.items()},'foodVisibleNativeFrames':dict(vis)}
 oldim=Image.open(P/f'reviews/{mode}-source-food.png').convert('RGBA'); im=Image.open(V/f'{mode}-source-food.png').convert('RGBA');of=o['food'];af=a['food']; met128=metrics(im,128);oldmet128=metrics(oldim,128)
 lp=localpoint(af,met128);op=localpoint(of,oldmet128);support=0;scalar=[];perp=[];ray=np.array([0,-math.cos(math.radians(35)),math.sin(math.radians(35))]);sensitivity={}
 for s in a['samples']:
  orig=os[(s['clip'],s['direction'],s['frame'])];m=np.array(s['food']['planeMatrix']);om=np.array(orig['food']['planeMatrix']);support=max(support,float(abs(m@lp-om@op).max()));delta=m[:3,3]-np.array(s['food']['rootMatrix'])[:3,3]; sc=float(delta@ray);scalar.append(sc);perp.append(float(np.linalg.norm(delta-sc*ray)))
 for t in [64,128,192]:
  cm=metrics(im,t);sm=metrics(oldim,t);sp=localpoint(of,sm);cp=localpoint(af,cm);sourcewidth=(of['vertices'][1][0]-of['vertices'][0][0])/(of['uv'][1][0]-of['uv'][0][0])*sm['visibleWidthPixels']/sm['size'][0]*1.25;currentwidth=(af['vertices'][1][0]-af['vertices'][0][0])*cm['visibleWidthPixels']/cm['size'][0]*1.25
  sensitivity[t]={'source':sm,'canonical':cm,'sourceVisibleWidthWorld':sourcewidth,'candidateVisibleWidthWorld':currentwidth,'supportDeltaPlaneWorld':((cp-sp)[:2]*1.25).tolist()}
 proposal=read('reviews/proposed-food-mappings.json')[foodname]
 out['food'][foodname]={'packedSHA256':af['image']['packedSHA256'],'canonicalBytesEqual':af['image']['packedSHA256']==proposal['canonicalTexture']['sha256'],'fullUV':af['uv'],'vertexMaxErrorToFrozenMap':err(af['vertices'],proposal['proposedVerticesPlaneLocal']),'oneFixedNativeQuad':True,'supportMaxWorldError':support,'depthScalarRange':[min(scalar),max(scalar)],'maxDepthPerpendicular':max(perp),'sensitivity':sensitivity}
m=read('reviews/round-03-verification/main-inventory.json');r=read('reviews/round-03-verification/runtime-inventory.json');diffrender=[k for k in m['render'] if m['render'][k]!=r['render'].get(k)];out['parity']={'actorMeshes':len(m['body']),'geometryNormalsWeightsModifiersTransformsMaterialsEqual':m['body']==r['body'],'finiteNormalsAll':all(v['normalsFinite'] for v in m['body'].values()),'bodyMaterialGraphsEqual':all(v==r['materials'][k] for k,v in m['materials'].items() if k.startswith('Ellis warm')),'lightsEqual':m['lights']==r['lights'],'renderDifferences':diffrender,'viewEqual':m['view']==r['view'],'compositorEqual':m['compositor']==r['compositor'],'sceneUseNodes':[m['sceneUseNodes'],r['sceneUseNodes']],'foodFlags':{mode:{k:v for k,v in d['foodFlags'].items() if k!='plane'} for mode,d in [('main',m),('runtime',r)]}}
ledger=read('candidates/round-03/phase-ledger.json');pf=[];counts=collections.Counter()
for row in ledger['renders']:
 s=allown[(row['mode'],row['sourceClipId'],row['direction'],row['sourceFrame'])];counts[row['direction']]+=1
 if err(row['rootMatrix'],s['rootMatrix'])>1e-5 or row['index']!=row['sourceFrame']-1:pf.append(row['render'])
out['phase']={'frames':len(ledger['renders']),'perDirection':dict(counts),'errors':pf,'cardinalDegrees':{'S':0,'E':90,'N':180,'W':-90}}
# Verify all full-canvas atlas cells and all logical contact-sheet cells.
d=read('delivery.round-03.json');frames=d['rawFrames']+d['runtimeVariants']['rawFrames'];atlases=d['atlases']+d['runtimeVariants']['atlases'];lookup={(x['clip'],x['direction'],x['index']):x for x in frames};pixfails=[];sheetfails=[];alphafails=[];ext=[]
for f in frames:
 im=Image.open(P/f['path']).convert('RGBA');bb=im.getchannel('A').getbbox();ext.append(bb)
 if im.size!=(384,640) or bb is None or bb[0]<=0 or bb[1]<=0 or bb[2]>=384 or bb[3]>=640:alphafails.append(f['path'])
for at in atlases:
 ai=Image.open(P/at['path']).convert('RGBA'); sheet=Image.open(C/f"contact-sheets/{at['clip']}-{at['direction']}.png").convert('RGB')
 for j in range(12):
  fr=lookup[(at['clip'],at['direction'],j)];im=Image.open(P/fr['path']).convert('RGBA');crop=ai.crop((j%6*384,j//6*640,j%6*384+384,j//6*640+640))
  if crop.tobytes()!=im.tobytes():pixfails.append(fr['path'])
  logical=im.resize((192,320),Image.Resampling.LANCZOS);expect=Image.new('RGB',(192,320),(235,231,221));expect.paste(logical,(0,0),logical);actual=sheet.crop((j%6*192,32+j//6*320,j%6*192+192,32+j//6*320+320))
  if actual.tobytes()!=expect.tobytes():sheetfails.append(fr['path'])
repeat=[]
for mode,folder,clips in [('main','frames',['stand','eat']),('runtime','runtime-frames',['eat-salmon'])]:
 for clip in clips:
  for di in 'SENW':
   stem='eat-salmon' if mode=='runtime' else clip; own=V/f'{mode}-native/{stem}-{di}.png'
   if not own.exists() and mode=='runtime':own=V/f'{mode}-native/eat-{di}.png'
   target=C/f'{folder}/{clip}-{di}/004.png';repeat.append({'own':str(own.relative_to(P)),'sealed':str(target.relative_to(P)),'RGBAEqual':Image.open(own).convert('RGBA').tobytes()==Image.open(target).convert('RGBA').tobytes(),'PNGBytesEqual':own.read_bytes()==target.read_bytes()})
videos=[]
for path in d['previews'].values():
 if not path.endswith('.webm'):continue
 result=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(P/path)]));st=result['streams'][0];videos.append({'path':path,**st,**result['format']})
out['pixels']={'nativeFrames':len(frames),'atlases':len(atlases),'wholeAtlasCellFailures':pixfails,'logicalSheetCellFailures':sheetfails,'alphaBoundaryFailures':alphafails,'globalAlphaBounds':[min(b[0] for b in ext),min(b[1] for b in ext),max(b[2] for b in ext),max(b[3] for b in ext)],'independentRerenders':repeat,'actualClips':videos}
(V/'measurements.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'modes':{k:{a:b for a,b in v.items() if a!='perClipBoundsWorld'} for k,v in out['modes'].items()},'food':{k:{a:b for a,b in v.items() if a!='sensitivity'} for k,v in out['food'].items()},'parity':out['parity'],'phase':out['phase'],'pixels':{k:v for k,v in out['pixels'].items() if k not in ['independentRerenders','actualClips']},'rerendersEqual':all(x['RGBAEqual'] for x in repeat),'clipCounts':collections.Counter((v['nb_read_frames'],v['r_frame_rate'],v['duration']) for v in videos).__str__()},indent=2))
