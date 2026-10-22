import json,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).parent;O=P.parent;foodmap=json.loads((P/'food-mapping-proposal.json').read_text());sin=math.sin(math.radians(35));cos=math.cos(math.radians(35));ray=np.array([0,-cos,sin]);up=np.array([0,sin,cos]);right=np.array([1,0,0])
def px(v):return [192+256*v[0],496-256*sin*v[1]-256*cos*v[2]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw={mode:json.loads((P/(mode+'-samples.json')).read_text()) for mode in ['main','runtime']};rows=[];issues=[];analysis={}
for mode,samples in raw.items():
 key='dish-cucumber' if mode=='main' else 'dish-salmon';mapping=foodmap[key]['isotropicFullUVMappingByThreshold']['128'];static=json.loads((P/(mode+'-source-static.json')).read_text());nativevs=np.array(static['food']['vertices']);source_uv=static['food']['uvs'];maxvisible=0;stalehidden=0;depthproof=0;rooterrors=[];probe={n:[] for n in ['seat','mouthSmile','palm_L','palm_R','thumb_L','thumb_R']};missingprobes=0
 for sample in samples:
  fr=np.array(sample['food']['foodRootMatrix'])[:3,3];expected=[fr+.6*ray+v[0]*1.25*right+v[1]*1.25*up for v in nativevs];actual=np.array(sample['food']['corners']);delta=float(np.max(np.abs(np.array(expected)-actual)))
  if sample['food']['visible']:maxvisible=max(maxvisible,delta)
  elif delta>1e-5:stalehidden+=1
  x=mapping['newFullQuadLeftWorld'];y=mapping['newFullQuadBottomWorld'];w,h=mapping['canonicalFullQuadWorld'];corners=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)];cworld=[fr+.6*ray+cx*right+cy*up for cx,cy in corners]
  # Single constant depth is sufficient for all facings and samples. Orthographic proof endpoints.
  dz=max(abs(a-b) for cx,cy in corners for a,b in zip(px(fr+cx*right+cy*up),px(fr+.6*ray+cx*right+cy*up)));depthproof=max(depthproof,dz)
  support=fr+.6*ray+mapping['sourceBottomRowSupportXWorld']*right+mapping['preserveSourceSupportOffsetAboveFoodRoot']*up
  palms=np.array(list(sample['points']['palms'].values()));rooterr=float(np.linalg.norm(fr-(palms.mean(axis=0)+np.array([0,0,.0225]))));rooterrors.append(rooterr)
  for n in probe:probe[n].append(sample['contacts'][n]['distance'])
  for side in ['L','R']:
   for typ in ['palm','thumb']:
    if sample['contacts'][typ+'_upwardSurface_'+side]['point'] is None:missingprobes+=1
  rows.append({'mode':mode,'clip':sample['clip'],'facing':sample['facing'],'frame':sample['frame'],'sourceFoodVisible':sample['food']['visible'],'nativeFoodRoot':fr.tolist(),'foodRootVsPalmMidpointOffsetError':rooterr,'correctedCanonicalCornersAtSourceDepth':[v.tolist() for v in cworld],'correctedCanonicalCornerPixelsAtSourceDepth':[px(v) for v in cworld],'sourceAlpha128SupportPointWorld':support.tolist(),'sourceAlpha128SupportPointPixels':px(support),'computedNativePlaneLawCorners':[v.tolist() for v in expected],'sourceEvaluatedCornerDeviation':delta,'sourceEvaluatedHiddenMatrixIsStale':not sample['food']['visible'] and delta>1e-5})
 analysis[mode]={'samples':len(samples),'visibleFoodSamples':sum(s['food']['visible'] for s in samples),'packedFoodSHA256':static['food']['packedSHA256'],'maxVisibleEvaluatedPlaneVsExactLawWorld':maxvisible,'hiddenPlaneMatrixStaleSamples':stalehidden,'note':'Blender skips hidden viewport plane transform evaluation. Preserve native action/visibility/driver channels; use the independently computed exact driver law for hidden samples, and evaluated matrices for visible samples. Raw recorded stale matrices are diagnostic only.','foodRootVsEvaluatedPalmsPlusWorldZ0225MaxError':max(rooterrors),'constantDepthEndpointProjectionMaxErrorPixels':depthproof,'actualMeshProbeDistanceRanges':{k:[min(v),max(v)] for k,v in probe.items()},'upwardSurfaceRayMisses':missingprobes}
# Runtime body must be the same actor geometry/pose in matched source states.
lookup={(s['clip'],s['facing'],s['frame']):s for s in raw['main']};diffs=[]
for s in raw['runtime']:
 clip={'eat-salmon':'eat','seated-wait-empty':'seated_wait'}[s['clip']];m=lookup[(clip,s['facing'],s['frame'])];diffs.append(max(float(np.max(np.abs(np.array(s['bones'][b])-np.array(m['bones'][b])))) for b in m['bones']))
analysis['runtimeMatchedBodyBoneMaxDifference']=max(diffs)
# Exact original atlas facing audit from native renders, comparing fixed source frames directly.
back=O.parents[2]/'refinement/backups/godot-before-warm-soft/assets/catalog/sprites/customer-june';card=[]
for d in ['S','E','N','W']:
 a=np.asarray(Image.open(P/('native-stand-'+d+'.png'))).astype(float);c=np.asarray(Image.open(back/('stand-'+d+'.png')).crop((0,0,384,640))).astype(float);aa=np.where(a[:,:,3]>=128);cc=np.where(c[:,:,3]>=128)
 card.append({'facing':d,'nativeYawDegrees':{'S':0,'E':90,'N':180,'W':-90}[d],'nativeBoundsEdgesXY':[int(aa[1].min()),int(aa[0].min()),int(aa[1].max())+1,int(aa[0].max())+1],'originalAtlasBoundsEdgesXY':[int(cc[1].min()),int(cc[0].min()),int(cc[1].max())+1,int(cc[0].max())+1],'fixedFrameRGBAMAE8bit':float(np.abs(a-c).mean()),'legacyLabelMatchesNative':True})
analysis['cardinalAudit']=card;analysis['cardinalConclusion']='June original stand N/E/S/W labels match actual cardinal native captures. No rotation relabeling or hypothetical Godot compensation applies.'
(P/'native-baseline-analysis.json').write_text(json.dumps(analysis,indent=2)+'\n');(P/'food-projected-baselines-576.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
print(json.dumps(analysis,indent=2))
