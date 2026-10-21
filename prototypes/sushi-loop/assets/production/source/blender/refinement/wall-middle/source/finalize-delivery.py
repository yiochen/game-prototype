import json,hashlib,shutil,math
from pathlib import Path
from PIL import Image
import numpy as np
B=Path(__file__).resolve().parents[1];R='round-06';C=B/'candidates'/R
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=C/'diagnostics';D.mkdir(exist_ok=True)
for name in['native-cut-linear.exr','cut-radiance-samples.json']:shutil.copy2(B/'candidates/round-05'/name,D/name)
v=json.load(open(C/'validation.json'));a=json.load(open(C/'native-audit.json'));assembly=json.load(open(C/'assembly-validation.json'));previews=json.load(open(C/'previews-map.json'))
# Correct the cut shader transport description to match the exact saved source.
v['geometry']['openCutPlanes']='Body extrusion surfaces end at exact x±.5. Wood source cut closure is camera-only BSDF, transparent on secondary rays. Blue source cut closure uses the common symmetric native top-radiance field for camera rays and ordinary BSDF transport. No geometry extends beyond either source connector plane.'
v['render']['pixelFilter']='BOX';v['render']['filterSize']=1
v['freshReopenAudit']={'path':str((C/'native-audit.json').relative_to(B)),'checks':a['checks'],'projectSha256':a['project']['sha256']}
v['spriteAssembly']=assembly
v['alphaChecks']={};regions={}
for d in'NESW':
 raw=Image.open(C/'raw'/f'static-{d}-0000.png').convert('RGBA');box=raw.getchannel('A').getbbox();v['alphaChecks'][d]={'size':list(raw.size),'alphaBounds':list(box),'clipped':box[0]==0 or box[1]==0 or box[2]==384 or box[3]==704}
 native=np.asarray(Image.open(C/'native-joins'/f'static-{d}-3modules.png')).astype(float);sprite=np.asarray(Image.open(C/'sprite-joins'/f'static-{d}-3modules.png')).astype(float)
 if d in'EW':boxes=[(420,456,476,463),(420,712,476,719)]
 else:boxes=[(317,555,324,770),(573,555,580,770)]
 regions[d]=[]
 for box in boxes:
  x1,y1,x2,y2=box;aa=native[y1:y2,x1:x2];bb=sprite[y1:y2,x1:x2];mask=(aa[:,:,3]>250)&(bb[:,:,3]>250);delta=np.abs(aa[:,:,:3]-bb[:,:,:3])[mask]
  regions[d].append({'box':list(box),'meanRGBDelta':delta.mean(axis=0).tolist(),'meanAbsoluteRGBDelta':float(delta.mean()),'p99AbsoluteRGBDelta':float(np.percentile(delta,99)),'maximumAbsoluteRGBDelta':float(delta.max())})
v['capCutShaderValidation']['diagnosticResources']={name:{'path':str((D/name).relative_to(B)),'sha256':sha(D/name)}for name in['native-cut-linear.exr','cut-radiance-samples.json']}
v['capCutShaderValidation']['exactSeamRegions']=regions
v['checks']={**a['checks'],'sourceUnchanged':v['source']['unchanged'],'allProfilesOnSource':all(p['passed']for p in v['geometry']['boundaryChecks']),'noSpriteClipping':all(not q['clipped']for q in v['alphaChecks'].values()),'registeredRoot':max(abs(p-q)for p,q in zip(v['capture']['calibration']['root'],[192,512]))<.001,'allSourceFacingRotationsMeasured':all(abs(r['rootRotationDegrees']-{'N':180,'E':90,'S':0,'W':-90}[r['direction']])<.001 for r in v['renders'])}
v['technicalStatus']='Native checks complete; visual verdict reserved for independent judge.'
(C/'validation.json').write_text(json.dumps(v,indent=2))
for d in'NESW':
 previews['native-join-'+d]=str((C/'native-joins'/f'static-{d}-3modules.png').relative_to(B));previews['independent-join-'+d]=str((C/'sprite-joins'/f'static-{d}-3modules.png').relative_to(B))
delivery={'asset':'wall-middle','round':R,'status':'candidate-ready-for-coordinator-seal-and-independent-judge','project':f'source/{R}.blend','recipe':f'source/{R}.py','supportingRecipes':['source/audit-native.py','source/assemble-preview.py','source/calibrate-cut-radiance.py','source/finalize-delivery.py'],'validation':str((C/'validation.json').relative_to(B)),'heroes':{d:str((C/'raw'/f'static-{d}-0000.png').relative_to(B))for d in'NESW'},'rawFrames':[{'clip':'static','direction':d,'index':0,'path':str((C/'raw'/f'static-{d}-0000.png').relative_to(B))}for d in'NESW'],'atlases':[{'clip':'static','direction':d,'path':str((C/'atlases'/f'static-{d}.png').relative_to(B)),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]}for d in'NESW'],'previews':previews,'nativeRecords':{'camera':str((C/'native-camera.json').relative_to(B)),'assetRecord':str((C/'native-assetRecord.json').relative_to(B)),'rig':str((C/'native-rig.json').relative_to(B))},'resources':{'family-settings':str((C/'family-settings.json').relative_to(B)),'native-audit':str((C/'native-audit.json').relative_to(B)),'assembly-validation':str((C/'assembly-validation.json').relative_to(B)),'cut-radiance-model':'source/cut-radiance-model.json'},'notes':['Only wall-middle source/candidates/delivery touched. Originals, target, brief, reviews and production remain read-only.','Round 01–05 are retained development candidates; round 06 is submitted for the independent verdict.','Native sculpted timber relief and blue top crown fade to exact source connector sections; actual height 1.018 is inside functional 1.02. Exact x extent [-.5,.5]; no overlap geometry.','Blue cut planes use one fitted symmetric native radiance field to avoid Cycles vertical-hemisphere contamination in alpha assembly. Main surfaces remain native lit BSDF. BOX1, denoising off, no raster corrections.','family-settings.json records exact candidate materials, world/lights/render/camera/profile/project hashes. Freeze for later family members only after judge approval.']}
(B/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps({'checks':v['checks'],'seamRegions':regions,'delivery':str(B/'delivery.json'),'projectSHA256':sha(B/'source'/f'{R}.blend')},indent=2))
