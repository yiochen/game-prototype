"""Finish portable/RGB evidence and versioned delivery without changing native artwork."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-02';REPLAY=OUT/'fresh-replay'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return Path(p).relative_to(BASE).as_posix()
def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def font(size):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size)
 except OSError:return ImageFont.load_default()
manifest=json.loads((REPLAY/'replay-manifest.json').read_text());lookup={(r['mode'],r['food'],r['clip'],r['direction'],r['index']):r for r in manifest if 'direction' in r}
fresh=[];rgb=[]
def metrics(a,b,mask):
 delta=np.abs(a.astype(np.int16)-b.astype(np.int16));v=delta[mask,:3]
 return {'pixels':int(mask.sum()),'maxRGBChannelDelta255':int(v.max()) if len(v) else None,'meanAbsoluteRGBChannelDelta255':float(v.mean()) if len(v) else None,'pixelsAnyRGBDifference':int(np.any(v>0,axis=1).sum()),'pixelsAnyDeltaGreater1':int(np.any(v>1,axis=1).sum()),'pixelsAnyDeltaGreater3':int(np.any(v>3,axis=1).sum())}
for r in manifest:
 if r['mode']!='candidate':continue
 folder=OUT/'runtimeVariants' if r['food']=='cucumber' else OUT
 shipping=folder/'frames'/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03d}.png';replayed=REPLAY/r['path'];a=rgba(shipping);b=rgba(replayed);d=np.abs(a.astype(np.int16)-b.astype(np.int16))
 fresh.append({'food':r['food'],'clip':r['clip'],'direction':r['direction'],'index':r['index'],'shippingSHA256':sha(shipping),'freshReplaySHA256':sha(replayed),'pixelIdentical':bool(np.array_equal(a,b)),'maxRGBADelta255':int(d.max()),'differentPixels':int(np.any(d,axis=2).sum()),'wholeCanvasComparison':True})
 if r['clip'].startswith(('idle','work')):continue
 base=lookup[('canonical-v2',r['food'],r['clip'],r['direction'],r['index'])];old=lookup[('approved-old-food',r['food'],r['clip'],r['direction'],r['index'])]
 a=rgba(REPLAY/base['path']);final=rgba(shipping);mask=(a[:,:,3]>=250)&(final[:,:,3]>=250)
 # Remove the complete union of canonical-v2/final/old food display quads, not an artist-selected body mask.
 verts=np.concatenate([np.array(z['quadNativePixels']) for z in [r,base,old]],axis=0);lo=np.floor(verts.min(axis=0)-2).astype(int);hi=np.ceil(verts.max(axis=0)+2).astype(int)
 mask[max(0,lo[1]):min(640,hi[1]+1),max(0,lo[0]):min(384,hi[0]+1)]=False
 oldpath=(BASE/'candidates/round-01/runtimeVariants/frames' if r['food']=='cucumber' else BASE/'candidates/round-01/frames')/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03d}.png'
 if not oldpath.exists():oldpath=P/'round-02-resources/approved-old-food-frames'/r['food']/f'{r["clip"]}-{r["direction"]}-{r["index"]:03d}.png'
 copied=OUT/'resources/approved-old-food-frames'/r['food']/f'{r["clip"]}-{r["direction"]}-{r["index"]:03d}.png';copied.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(oldpath,copied)
 oo=rgba(copied);omask=mask&(oo[:,:,3]>=250)
 rgb.append({'food':r['food'],'clip':r['clip'],'direction':r['direction'],'index':r['index'],'approvedOldPixels':{'path':rel(copied),'sha256':sha(copied)},'excludedFoodQuadUnionBoundsNativePx':[lo.tolist(),hi.tolist()],'canonicalV2DepthToV3Depth':metrics(a,final,mask),'approvedOldFoodToV3CanonicalFood':metrics(oo,final,omask),'frozenBodyGeometryMaterialsLightsRenderer':True})
closure=json.loads((REPLAY/'closure.json').read_text());assert closure['ok']
write(OUT/'fresh-replay-validation.json',{'ok':True,'method':'Fresh background Blender process, using only the copied portable source closure; full native384x640 RGBA replay compared directly to shipping pixels. Any native stochastic/denoiser differences are reported numerically, without compensation.','cases':fresh,'allReplayPixelsIdentical':all(r['pixelIdentical'] for r in fresh),'maxReplayRGBADelta255':max(r['maxRGBADelta255'] for r in fresh),'closure':closure,'intermediateFreshViews':[r for r in manifest if r['mode']=='candidate-intermediate']})
summary={kind:{'maxRGBChannelDelta255':max(r[kind]['maxRGBChannelDelta255'] or 0 for r in rgb),'maxCaseMeanAbsoluteRGBChannelDelta255':max(r[kind]['meanAbsoluteRGBChannelDelta255'] or 0 for r in rgb),'totalPixelsAnyRGBDifference':sum(r[kind]['pixelsAnyRGBDifference'] for r in rgb)} for kind in ['canonicalV2DepthToV3Depth','approvedOldFoodToV3CanonicalFood']}
write(OUT/'food-dependent-rgb-diagnostics.json',{'coverage':'32 hold/load endpoint poses: both foods, all4facings, indices0/11. RGB maxima below are observed on these diagnostic poses, not asserted as a global bound across every frame. Geometry/control/registration audits cover all288 shipping frames.','method':'Direct exported native RGB comparisons on opaque body pixels outside the full union of all old/canonical/new food quads plus2px. Both sources use exact frozen renderer/camera/body/material/light settings. Canonical-v2 versus final isolates bias change with identical canonical image/aspect; approved-old-food versus final also includes image/aspect replacement.','interpretation':'Differences remain despite exact non-food semantic/numeric parity. Food-dependent transport, occlusion/path sampling and denoiser response can contribute; their causal shares were not isolated. These differences are not relabeled as one-step noise. No grading, color correction or renderer compensation was applied.','summary':summary,'cases':rgb})
# Same registered context before/after, native resolution; include both foods and four facings.
sheet=Image.new('RGB',(1536,1408),'#e5e2d8');draw=ImageDraw.Draw(sheet);label_font=font(16)
for foodi,food in enumerate(['salmon','cucumber']):
 clip='hold' if food=='salmon' else 'hold-cucumber'
 for di,direction in enumerate(['N','E','S','W']):
  for state,mode in enumerate(['canonical-v2','candidate']):
   r=lookup[(mode,food,clip,direction,0)];im=Image.open(REPLAY/r['path']).convert('RGBA');bg=Image.new('RGBA',im.size,'#e5e2d8');bg.alpha_composite(im);mini=bg.convert('RGB').resize((192,320),Image.Resampling.LANCZOS);x=di*384+state*192;y=foodi*704
   sheet.paste(mini,(x,y+28));draw.text((x+4,y+4),f'{food} {direction} · {mode}',font=label_font,fill='#20343c')
   # Native boundary crop is an explicit review-only enlargement.
   crop=bg.convert('RGB').crop((96,320,288,480)).resize((192,320),Image.Resampling.NEAREST);sheet.paste(crop,(x,y+376));draw.text((x+4,y+352),'head/hand/food boundary',font=font(12),fill='#20343c')
sheet.save(OUT/'canonical-v2-v3-context.png')
# Repeated intended-size views include both foods, keeping the full registered canvas.
repeat=Image.new('RGB',(768,640),'#e5e2d8')
for fi,food in enumerate(['salmon','cucumber']):
 folder=OUT if fi==0 else OUT/'runtimeVariants';clip='hold' if fi==0 else 'hold-cucumber'
 for di,d in enumerate(['N','E','S','W']):
  im=Image.open(folder/'frames'/f'{clip}-{d}'/'005.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#e5e2d8');bg.alpha_composite(im);repeat.paste(bg.convert('RGB').resize((192,320),Image.Resampling.LANCZOS),(di*192,fi*320))
repeat.save(OUT/'repeated.png')
v=json.loads((OUT/'complete-validation.json').read_text());v['pendingEvidence']=[];v['freshPortableReplay']='candidates/round-02/fresh-replay-validation.json';v['foodDependentRGBDiagnostics']='candidates/round-02/food-dependent-rgb-diagnostics.json';v['foodDependentRGBSummary']=summary;v['freshReplayRGBAIdentical']=all(r['pixelIdentical'] for r in fresh)
calibration=json.loads((OUT/'joint-depth-calibration.json').read_text());image_parity={}
for f in ['salmon','cucumber']:
 source=next(s for s in calibration['sources'] if s['food']==f)['shader'];folder=OUT if f=='salmon' else OUT/'runtimeVariants';candidate=json.loads((folder/'validation.json').read_text())['image']
 image_parity[f]={k:source[k]==candidate[k] for k in ['interpolation','extension','colorspace','alphaMode']}
assert all(all(p.values()) for p in image_parity.values())
v['foodShaderImageSettingsParity']=image_parity;v['shippingMaxPerpendicularResidualInFloat32ULPsAtUnitWorld']=v['shippingMaximum']['perpendicularWorld']/float(np.spacing(np.float32(1.0)))
orientation=[]
for folder in [OUT,OUT/'runtimeVariants']:
 nativeval=json.loads((folder/'validation.json').read_text());static=json.loads((folder/'static-semantic-parity.json').read_text());nativeval['nonFoodObjectCount']=len(static['candidate']['objects']);nativeval['nonFoodMeshCount']=sum('mesh' in r for r in static['candidate']['objects'].values());nativeval.pop('bodyMeshCount',None);write(folder/'validation.json',nativeval)
 o=json.loads((folder/'semantic-orientation-validation.json').read_text());orientation.append(o);v['ok']=v['ok'] and o['ok']
v['maxActualSemanticDotVsExpressionDifference']=max(o['maxDotVsExpressionDifference'] for o in orientation);v['ok']=v['ok'] and closure['ok']
v['renderManifest']='native-frames.json'
v['supplementalRuntimeRenderManifest']='runtimeVariants/native-frames.json'
v['browserPlaybackQA']='candidates/round-02/browser-playback-qa.json'
v['hiddenRigidKnifeProof']={}
for folder,variant in [(OUT,'main'),(OUT/'runtimeVariants','runtime')]:
 nv=json.loads((folder/'validation.json').read_text());nv['nativeFrameCount']=nv.pop('nativeFrames',nv.get('nativeFrameCount'));nv['renderManifest']='native-frames.json'
 nv['notes'][0]='All visible/deforming body meshes: actual evaluated numeric positions/normals compared in memory. Fixed viewport-culled knife meshes: unchanged local geometry under actual evaluated utensil parent and native parent inverse/basis, explicitly reconstructed; cross-checked against actual evaluated visible work knife geometry. Compact per-frame/per-mesh results are serialized; raw arrays are discarded.'
 write(folder/'validation.json',nv)
 hidden=json.loads((folder/'hidden-mesh-evaluation-validation.json').read_text());v['ok']=v['ok'] and hidden['ok']
 v['hiddenRigidKnifeProof'][variant]={'path':rel(folder/'hidden-mesh-evaluation-validation.json'),'frames':len(hidden['frames']),'allSourceCandidatePositionNormalDeltasZero':all(all(x==0 for x in r['maxima']) for r in hidden['frames']),'maxReconstructionVsVisibleEvaluatedDelta':max((max(r['maxima']) for r in hidden['visibleKnifeReconstructionCrosschecks']),default=None),'method':hidden['method']}
write(OUT/'complete-validation.json',v)
delivery=json.loads((BASE/'delivery-round-02-held-food-v3.json').read_text());delivery['previews']['canonical-v2-v3-context']='candidates/round-02/canonical-v2-v3-context.png'
delivery['renderManifest']='candidates/round-02/native-frames.json'
# Explicit path lists are accepted by generic sealer/promoter and avoid digest cycles.
delivery['resources']=sorted({rel(p) for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['packet.json','delivery.snapshot.json']}|{rel(p) for p in P.glob('*round02*') if p.is_file()}|{rel(p) for p in (P/'round-02-resources').rglob('*') if p.is_file() and '__pycache__' not in p.parts})
delivery['runtimeVariants']['resources']=sorted({rel(p) for p in (OUT/'runtimeVariants').rglob('*') if p.is_file() and '__pycache__' not in p.parts}|{'candidates/round-02/portable-replay/source/runtime-round-02.blend','source/runtime-round-02.blend','source/runtime-recipe-round02.json','source/runtime-config-round02.json','source/runtime-rig-round02.json','source/food_common_round02.py','source/native_actions_round02.py','source/round-02-resources/dish-cucumber.png'})
delivery['runtimeVariants']['renderManifest']='candidates/round-02/runtimeVariants/native-frames.json'
delivery['runtimeVariants']['previews']={k:path for k,path in delivery['previews'].items() if 'cucumber' in k or k.startswith('runtime')}
delivery['status']='Ready for coordinator sealing and independent judge; no visual verdict issued'
write(OUT/'runtimeVariants/runtime-manifest.json',delivery['runtimeVariants']);write(BASE/'delivery-round-02-held-food-v3.json',delivery)
write(OUT/'editor-handoff.json',{'status':'Ready for coordinator sealing/independent visual review','briefSHA256':sha(BASE/'brief-v3-held-food-occlusion.json'),'criteriaSHA256':sha(BASE/'reviews/proposedcriteria-held-food-v3.json'),'delivery':{'path':'delivery-round-02-held-food-v3.json','sha256':sha(BASE/'delivery-round-02-held-food-v3.json')},'projects':{rel(P/n):sha(P/n) for n in ['round-02.blend','runtime-round-02.blend']},'validationSHA256':sha(OUT/'complete-validation.json'),'noSelfApproval':True})
print('FINAL EVIDENCE',v['ok'],summary,flush=True)
