from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageFilter
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-02';R=P/'reviews';O=P/'candidates/round-01';N=R/'round02-independent-native'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def im(p):return np.asarray(Image.open(p).convert('RGBA'))
def stat(a,b,mask=None):
 d=np.abs(a.astype(np.int16)-b.astype(np.int16));mask=np.ones(a.shape[:2],bool) if mask is None else mask;n=int(mask.sum())
 if not n:return {'regionPixels':0,'changedRGBPixels':0,'changedAlphaPixels':0,'maximumRGBChannelDifference':0,'maximumAlphaDifference':0,'meanRGBAbsoluteChannelDifference':0,'RGBChannelQuantiles':{str(q):0 for q in [50,90,99,99.9,100]}}
 rgb=d[:,:,:3][mask];al=d[:,:,3][mask];ch=np.any(rgb>0,axis=1)
 return {'regionPixels':n,'changedRGBPixels':int(ch.sum()),'changedRGBPixelFraction':float(ch.mean()),'changedAlphaPixels':int(np.count_nonzero(al)),'maximumRGBChannelDifference':int(rgb.max()),'maximumAlphaDifference':int(al.max()),'meanRGBAbsoluteChannelDifference':float(rgb.mean()),'RGBChannelQuantiles':{str(q):float(np.percentile(rgb,q)) for q in [50,90,99,99.9,100]},'changedPixelRGBMean':float(rgb[ch].mean()) if ch.any() else 0}
def diff(a,b,path=''):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):return [path+'/'+k for k in a.keys()^b.keys()]+sum((diff(a[k],b[k],path+'/'+k) for k in a.keys()&b.keys()),[])
 if isinstance(a,list):return [path] if len(a)!=len(b) else sum((diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [path]
s=rd(N/'source.json');c=rd(N/'candidate.json');assert s['static']==c['static'];assert s['phases']==c['phases'];assert len(s['phases'])==192
sr=rd(C/'source-shared.json');cr=rd(C/'candidate-shared.json');ds=diff(sr['shared'],cr['shared']);assert len(ds)==10 and all('__image_plane' in p for p in ds)
sp=rd(C/'source-phases.json');cp=rd(C/'candidate-phases.json');phasecomp=0
for a,b,x in zip(sp,cp,c['phases']):
 assert all(a[k]==b[k] for k in ['clip','direction','index','rootRotationZ','rootRotationDegrees','rootMatrix','cameraMatrix','rootPixel','physicalMeshes','pose','nativeTransforms','foodChannels'])
 assert len(a['physicalMeshes'])==69;phasecomp+=69
 assert b['rootMatrix']==x['rootMatrix']
 if b['clip'] in ['hold','load']:assert b['foodChannels'][next(n for n in b['foodChannels'] if '__image_plane' in n)]['world']==x['planeMatrix']
 assert all(abs(t-u)<1e-4 for t,u in zip(b['rootPixel'],x['rootNativePixel']))
# Recompute exact image support from the actual packed-matching dependency bytes and source/candidate geometry.
alpha=[];positions={};widths={}
for role,j,fn in [('source',s,P/'source/dependencies-round01/dish-salmon.png'),('canonical',c,P/'source/dependencies-round02/dish-salmon.png')]:
 assert sha(fn)==j['food']['packedSHA256'];a=im(fn)[:,:,3];h,w=a.shape;quad=np.array(j['food']['quad']);uv=np.array(j['food']['uv']);lo=quad.min(0);hi=quad.max(0);uvlo=uv.min(0);uvhi=uv.max(0)
 for cut in [64,128,192]:
  yy,xx=np.where(a>=cut);row=int(yy.max());bottom=np.where(a[row]>=cut)[0];uvpoint=np.array([(bottom+.5).mean()/w,1-(row+.5)/h]);t=(uvpoint-uvlo)/(uvhi-uvlo);local=lo+(hi-lo)*[t[0],t[1],0];width=(hi[0]-lo[0])*(xx.max()+1-xx.min())/w/(uvhi[0]-uvlo[0]);positions[role,cut]=local;widths[role,cut]=width
  alpha.append({'role':role,'cutoff':cut,'bbox':[int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1],'local':local.tolist(),'occupiedWidthLocal':float(width),'imageSHA256':sha(fn)})
provided=rd(C/'image-alpha-semantic-audit.json')['records']
for a,b in zip(alpha,provided):assert a['bbox']==b['bboxTopOrigin'] and np.max(np.abs(np.array(a['local'])-b['semanticLocal']))<1e-14
camera=np.array(c['static']['camera']['matrix']);up=camera[:3,1];pixscale=384/c['static']['camera']['ortho'];root=np.array(c['phases'][0]['rootNativePixel'])
def project(v):return root+pixscale*np.array([v[0],-np.dot(up,v)])
semantic=[];sem=rd(C/'semantic-support-all96.json');providedR={(r['clip'],r['direction'],r['index'],r['alphaCutoff']):r for r in sem['records']};maxWorld=0;maxPixel=0;maxMatrixWorldRecord=0;maxProjectionRecord=0;maxPalmRel=0
for a,b in zip(s['phases'],c['phases']):
 if a['clip'] not in ['hold','load']:continue
 for cut in [64,128,192]:
  sw=(np.array(a['planeMatrix'])@np.r_[positions['source',cut],1])[:3];cw=(np.array(b['planeMatrix'])@np.r_[positions['canonical',cut],1])[:3];r=providedR[a['clip'],a['direction'],a['index'],cut]
  worlderr=float(np.linalg.norm(cw-sw));pixelerr=float(np.linalg.norm(project(cw)-project(sw)));maxMatrixWorldRecord=max(maxMatrixWorldRecord,float(np.max(np.abs(sw-r['sourceRimWorld']))),float(np.max(np.abs(cw-r['candidateRimWorld']))));maxProjectionRecord=max(maxProjectionRecord,float(np.max(np.abs(project(sw)-r['sourceRimNativePixels']))),float(np.max(np.abs(project(cw)-r['candidateRimNativePixels']))))
  for side in ['L','R','midpoint']:
   srp=r['sourcePalmRelations'][side];crp=r['candidatePalmRelations'][side];assert srp['world']==crp['world'] and srp['projected']==crp['projected']
   for pos,pal,ref in [(sw,srp,r['sourceRimWorld']),(cw,crp,r['candidateRimWorld'])]:
    maxPalmRel=max(maxPalmRel,float(np.max(np.abs(np.array(ref)-pal['world']-pal['rimMinusPalmWorld']))),float(np.max(np.abs(project(pos)-pal['projected']-pal['rimMinusPalmNativePixels']))))
  if cut==128:maxWorld=max(maxWorld,worlderr);maxPixel=max(maxPixel,pixelerr)
  semantic.append({'clip':a['clip'],'direction':a['direction'],'index':a['index'],'cutoff':cut,'rimWorldShiftDoublePrecision':worlderr,'rimNativeShiftDoublePrecision':pixelerr})
assert len(semantic)==288 and maxMatrixWorldRecord<1e-7 and maxProjectionRecord<1e-4 and maxPalmRel<1e-4
# Independently measure delivered native repeat controls and body/face/filtering residuals from their actual PNGs/masks.
cal=rd(C/'native-replay-calibration.json');rad=rd(C/'radiance-residual-analysis.json');replay=[];radiance=[]
for r,z in zip(cal['controls'],rad['records']):
 label=f"{r['clip']}-{r['direction']}-{r['index']:03}";sa=im(C/'controls/source'/(label+'-a.png'));sb=im(C/'controls/source'/(label+'-b.png'));ca=im(C/'controls/candidate'/(label+'-a.png'));cb=im(C/'controls/candidate'/(label+'-b.png'));sealed=im(O/'frames'/f"{r['clip']}-{r['direction']}"/f"{r['index']:03}.png");deliv=im(C/'frames'/f"{r['clip']}-{r['direction']}"/f"{r['index']:03}.png")
 row={k:stat(x,y) for k,x,y in [('sourceSameInputRepeat',sa,sb),('sourceFreshVsSealed',sa,sealed),('candidateSameInputRepeat',ca,cb),('candidateFreshVsDelivered',ca,deliv)]}
 for k,v in row.items():assert v==r[k],(label,k)
 replay.append({'phase':label,**row})
 sm=np.load(C/'identity-masks/source'/(label+'.npz'));cm=np.load(C/'identity-masks/candidate'/(label+'.npz'));food=(sm['food']>0)|(cm['food']>0);d2=np.array(Image.fromarray((food*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)))>0;d8=np.array(Image.fromarray((food*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(17)))>0;bodyRay=(sm['body']>0)|(cm['body']>0);opaque=(sa[:,:,3]>=250)&(ca[:,:,3]>=250);body=bodyRay&opaque&~d2;head=np.zeros((640,384),bool);head[300:415,98:288]=1;head&=body;core=bodyRay&opaque&~d8
 masks={'nativeBodyInteriorOutsideFood8px':core,'headFaceInteriorOutsideFood8px':head&core,'foodFilteringBoundaryBand8px':bodyRay&opaque&d8&~food,'nativeBodyInteriorOutsideUnionFood':body,'headFaceInteriorOutsideUnionFood':head,'bodyAlphaEdgeOutsideUnionFood':((sa[:,:,3]>0)|(ca[:,:,3]>0))&~opaque&~d2,'unionFoodPrimaryCoverage':food,'transparentBackground':(sa[:,:,3]==0)&(ca[:,:,3]==0)}
 out={k:stat(sa,ca,v) for k,v in masks.items()}
 assert out==z['oldFoodVsCanonicalFood'],label
 radiance.append({'phase':label,'measuredRegions':out})
# Judge's own actual fresh native reopens/repeats, independently generated under exact saved native state.
own=[]
for role,old in [('source',O),('candidate',C)]:
 own.append({'role':role,'comparison':'same-input hold S0 repeat','metrics':stat(im(N/(role+'-hold-S-000-a.png')),im(N/(role+'-hold-S-000-b.png')))})
 for clip,d,i,label in [('hold','S',0,'hold-S-000-a'),('hold','N',5,'hold-N-005'),('load','W',5,'load-W-005')]:own.append({'role':role,'comparison':f'fresh vs sealed {clip} {d} {i}','metrics':stat(im(N/(role+'-'+label+'.png')),im(old/'frames'/f'{clip}-{d}'/f'{i:03}.png'))})
assert max(r['metrics']['maximumRGBChannelDifference'] for r in own)<=1 and all(r['metrics']['maximumAlphaDifference']==0 for r in own)
report={'packetSHA256':sha(C/'packet.json'),'independentSavedSourceAudit':{'originalSHA256':s['sourceSHA256'],'candidateSHA256':c['sourceSHA256'],'allOwnStaticInputsEqual':True,'allOwn192PhasesEqual':True,'physicalObjectComparisons':phasecomp,'coverage':'69 physical body/knife meshes: evaluated full local vertex/vertex-normal/corner-normal/polygon-normal buffers plus matrices/counts/visibility, full bone poses/root/food plane transforms. Static geometry, topology/UV/smoothing/weights/material assignments/parents/armature modifiers,24 actions and rest matrices, material/light/world/camera/render inputs compared. Separate supplied exhaustive RNA/constraint/modifier/driver audit recursively compared. World coordinate/normal equality follows exact local buffers and matrices; supplied explicit world digests independently compared as well.','providedDetailedStaticDifferencePaths':ds,'unexpectedStaticPaths':[]},'alphaAudit':alpha,'semanticAudit':{'all96PrimaryPlus192SensitivityRelationshipsChecked':True,'primaryAlpha128MaxWorldShiftDoublePrecision':maxWorld,'primaryAlpha128MaxNativeShiftDoublePrecision':maxPixel,'providedFloat32PrimaryMaxNativeShift':sem['sensitivity']['128']['maxNativeRimShiftPixels'],'maximumOwnMatrixProjectionDiscrepancyAgainstProvidedNativeWorld':maxMatrixWorldRecord,'maximumOwnProjectionDiscrepancyNativePixels':maxProjectionRecord,'maximumPalmRelationshipArithmeticDiscrepancy':maxPalmRel,'records':semantic,'limits':'Analytic semantic consistency alone is not visible contact approval. Same originally nonzero world palm-depth relationship is retained.'},'providedReplayAndRadianceRecomputedExactlyFromPixels':True,'replay12':replay,'changedInputRadiance12':radiance,'ownFreshNativeControls':own,'radianceInterpretation':'Changed input body/face residuals are real and separately assessed visually. 8px exclusion reduces primary food filtering uncertainty; masks are diagnostic sample-centre identities, not production modifications. Sparse1LSB same-input differences are empirically observed, not a universal GPU guarantee.'}
(R/'round02-independent-evidence-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'staticDeltaPaths':len(ds),'physicalComparisons':phasecomp,'primaryWorld':maxWorld,'primaryNative':maxPixel,'projectionAuditNative':maxProjectionRecord,'ownReplayControls':[(r['role'],r['comparison'],r['metrics']['changedRGBPixels'],r['metrics']['maximumRGBChannelDifference']) for r in own],'recomputedReplay12AndRadiance12':True}))
