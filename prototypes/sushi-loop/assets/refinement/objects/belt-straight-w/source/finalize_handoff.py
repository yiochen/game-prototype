from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,hashlib,zipfile,os,shutil

P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
H=lambda p:hashlib.sha256((Path(p) if Path(p).is_absolute() else P/Path(p)).read_bytes()).hexdigest()
A=lambda p:Path(p) if Path(p).is_absolute() else P/Path(p)
read=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,indent=2)+'\n')
V=read(O/'validation.json');D=read(O/'delivery.json');F=read(P/'inputs/family-settings.json')
R=read(O/'render-reproduction.json');portable=read(O/'portable-reproduction/record.json')
scene=read(O/'scene-response-audit.json');floor=read(O/'floor-consumer-metrics.json');regions=read(O/'region-localization.json');gpu=read(O/'consumer-metrics.json')
# Every actual moving-material owner is obtained from reopening this source, not inherited N metadata.
rig=read(O/'rig.json');own=R['actualActionOwner']
rig['clips']['running']['actions'][0].update({'ownerName':own['nodeTree'],'materialOwnerName':own['material'],'action':own['action'],'slotIdentifier':own['slot']})
rig['clips']['running']['shaderChannels']=[own['nodeTree']+'::Value::outputs::0'];rig['clips']['running']['shaderLoopClosure']={own['nodeTree']+'::Value::outputs::0':-7.0}
write(O/'rig.json',rig)
fixtures=[]
for ident,slug in [('N','belt-straight-n'),('E','belt-straight-e'),('S','belt-straight-s')]:
 ref=read(P.parent/slug/'delivery.json')
 for a in ref['atlases']:
  path=Path(a['path']);path=path if path.is_absolute() else P.parent/slug/path
  fixture=O/'consumer/inputs'/f"{ident}-running-{a['direction']}.png"
  fixtures.append({'identity':ident,'direction':a['direction'],'approvedPath':str(path),'fixture':str(fixture),'sha256':H(fixture),'approvedSHA256':H(path),'equal':H(fixture)==H(path)})
write(O/'approved-fixture-hashes.json',fixtures)
# Explicitly bind the measured direction convention and directed endpoint correspondence of each route.
routes=[]
angles={'N':np.pi,'E':np.pi/2,'S':0.,'W':-np.pi/2};intrinsic={'W':-np.pi/2,'N':np.pi,'E':np.pi/2,'S':0.}
for r in V['nativeRuns']:
 if r['index']!=0:continue
 out=[]
 for index,identity in enumerate(r['pattern']):
  direction=V['nativeAssemblyContract']['sameFlowMappings'][identity][r['direction']]
  root=np.array(r['moduleRootMatrices'][index]);a=angles[direction]+intrinsic[identity]
  rotation=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
  incoming=rotation@np.array([0.,.5,.64])+root[:3,3];outgoing=rotation@np.array([0.,-.5,.64])+root[:3,3]
  out.append({'identity':identity,'publisherFacing':direction,'publisherRootDegrees':angles[direction]*180/np.pi,'intrinsicRadians':intrinsic[identity],'incomingWorld':incoming.tolist(),'outgoingWorld':outgoing.tolist(),'phaseFrame0':0.})
 joins=[]
 for k in (0,1):
  a,b=out[k],out[k+1];distAB=float(np.linalg.norm(np.array(a['outgoingWorld'])-b['incomingWorld']));distBA=float(np.linalg.norm(np.array(b['outgoingWorld'])-a['incomingWorld']))
  joins.append({'leftIndex':k,'rightIndex':k+1,'directedOrder':f"{k}->{k+1}" if distAB<distBA else f"{k+1}->{k}",'matchingPortDistance':min(distAB,distBA)})
 routes.append({'pattern':r['pattern'],'presentationFacing':r['direction'],'coverage':V['nativeAssemblyContract']['coverageByPattern'][r['pattern']],'modules':out,'joins':joins})
write(O/'directed-route-audit.json',routes)
# Actual maximum full-image residual at each pitch over ALL captured backgrounds, contexts and routes.
worst=[]
for pitch in [128,55,32]:
 r=max((r for r in gpu['pairs'] if r['pitch']==pitch),key=lambda r:max(r['fullMaxRGBA']))
 a=Image.open(A(r['current'])).convert('RGBA');b=Image.open(A(r['reference'])).convert('RGBA');delta=np.abs(np.array(a,dtype=np.int16)-np.array(b,dtype=np.int16))
 y,x,channel=np.unravel_index(delta.argmax(),delta.shape);box=(max(0,x-12),max(0,y-8),min(a.width,x+13),min(a.height,y+9));bg=(120,125,128,255)
 def visible(im):
  out=Image.new('RGBA',im.size,bg);out.alpha_composite(im);return out.convert('RGB')
 aa,bb=visible(a),visible(b);sheet=Image.new('RGB',(max(aa.width*2,600),aa.height+184),(230,233,227));sheet.paste(aa,(0,24));sheet.paste(bb,(aa.width,24))
 sheet.paste(aa.crop(box).resize((200,136),Image.Resampling.NEAREST),(0,aa.height+24));sheet.paste(bb.crop(box).resize((200,136),Image.Resampling.NEAREST),(200,aa.height+24));heat=np.minimum(delta[:,:,:3]*16,255).astype(np.uint8);sheet.paste(Image.fromarray(heat).crop(box).resize((200,136),Image.Resampling.NEAREST),(400,aa.height+24))
 ImageDraw.Draw(sheet).text((4,5),f"Worst {pitch}px {r['pattern']}/{r['direction']}/{r['index']} c{r['context']} {r['background']}: current/native; crop then RGBx16",fill=(20,30,36))
 path=O/'previews'/f'worst-all-background-residual-{pitch}.png';sheet.save(path)
 native=next(n for n in json.loads((O/'native-vs-independent-metrics.json').read_text()) if (n['pattern'],n['direction'],n['index'])==(r['pattern'],r['direction'],r['index']))
 worst.append({**r,'proof':str(path),'maxResidualXYChannel':[int(x),int(y),int(channel)],'nativeRegionCounts':native['fullResidualRegionPixelCountsOver1'],'independentJudgmentRequired':True})
write(O/'worst-all-context-residuals.json',worst)
checks=V['technicalChecks'];checks.update({
 'actualSceneLightsExactlyFrozen':scene['exactFrozenLights'],'actualSceneWorldExactlyFrozen':scene['exactFrozenWorld'],'actualSceneRenderFieldsExactlyFrozen':scene['exactFrozenRenderFields'],
 'allMaterialCoordinatesUseNativePerMeshBasis':scene['allShaderTexCoordObjectsNone'],'noGeometryAnimationOwners':scene['noGeometryAnimationOwners'],
 'reopened100PixelArraysExact':R['all100PixelExact'],'relocatedPortable100PixelArraysExact':portable['all100PixelExact'],'approvedSiblingFixturesExact':all(r['equal'] for r in fixtures),
 'nativeRoutesDirectedPortDistancesWithin1e6':all(j['matchingPortDistance']<1e-6 for r in routes for j in r['joins']),
 'actualFloor3048ComparisonPairs':floor['pairCount']==3048,'actualFloorClosurePixelEqual':floor['allClosuresPixelEqual'],
 'actualFloorJoinRGBWithin1AlphaExact':all(max(g['joinMaxRGBA'][:3])<=1 and g['joinMaxRGBA'][3]==0 for g in floor['summaryByCellPitch'].values()),
 'fullResidualLocationMeasured':regions['allActualGPUResidualsWithinNativeSupportProjection'] and floor['allResidualsWithinMeasuredCrossbeamProjection'],
 'sourceFootprintAndHeightEnvelope':all(abs(a-b)<1e-6 for row,expected in zip(V['geometry']['bounds'],[[-.5,-.48,0],[.5,.48,.695]]) for a,b in zip(row,expected)),
 'allNativeFramesRGBARegistered':all(Image.open(O/'frames'/f'running-{d}-{i:02d}.png').size==(384,704) and Image.open(O/'frames'/f'running-{d}-{i:02d}.png').mode=='RGBA' for d in 'NESW' for i in range(25)),
})
V.update({'sourceInspection':'source/independent-source-inspection-v1.json','actualSceneResponseAudit':scene,'directedRouteAudit':'candidates/round-01/directed-route-audit.json','renderReproduction':{'path':str(O/'render-reproduction.json'),'all100PixelArraysExact':R['all100PixelExact'],'note':'PNG ancillary file/date/timing metadata differs; complete native RGBA arrays are identical.'},'portableReproduction':{'project':str(O/'portable-reproduction/model.blend'),'script':str(O/'portable-reproduction/capture.py'),'record':str(O/'portable-reproduction/record.json'),'all100PixelArraysExact':portable['all100PixelExact'],'externalDependencies':[]},'fullImageRegionLocalization':str(O/'region-localization.json'),'worstCasesAllContexts':str(O/'worst-all-context-residuals.json'),'technicalChecks':checks})
V['consumer']['actualFloorEvidence']={'record':str(O/'consumer/floor-render-record.json'),'metrics':str(O/'floor-consumer-metrics.json'),'captureCount':floor['captureCount'],'pairCount':floor['pairCount'],'summaryByCellPitch':floor['summaryByCellPitch'],'floor':floor['floorTexture']}
V['consumer']['allActualCaptureCount']=V['consumer']['captureCount']+floor['captureCount'];V['consumer']['allActualPairCount']=V['consumer']['comparisonPairCount']+floor['pairCount']
V['actualPlayback']={'record':str(O/'playback-check.json'),'surface':str(O/'previews/review.html'),'meaning':'Actual browser playback observations only. Judge owns independent visual/materiality acceptance.'}
write(O/'validation.json',V);write(O/'technical-checks.json',checks)
Q=O/'portable-reproduction';expected=[{'direction':r['direction'],'index':r['index'],'pixelSHA256':hashlib.sha256(Image.open(A(r['original'])).convert('RGBA').tobytes()).hexdigest()} for r in R['renderSamples']];write(Q/'expected-pixel-hashes.json',expected)
(Q/'README.txt').write_text('Editable native W candidate. Blender5.2.2LTS. Run: blender -b --python capture.py\nOnly model.blend and capture.py are required. No textures/libraries/external IDs. Captures100 original registered RGBA PNGs under renders/. Native384x704, root192,496;24unique frames plus closure perN/E/S/W. Expected hashes bind pixel arrays, excluding PNG ancillary metadata.\n')
with zipfile.ZipFile(O/'portable-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['model.blend','capture.py','expected-pixel-hashes.json','README.txt']:z.write(Q/name,name)
recipe=read(P/'source/round-01-recipe.json');recipe.update({'recipeScript':'source/capture_native.py','sourceOnlyCapture':'blender -b --python source/capture_native.py','frozenCriteriaSHA256':H(P/'reviews/criteria.json'),'inspectionSequence':V['inspectionSequence'],'nativeRouteAudit':str(O/'directed-route-audit.json'),'renderReproduction':V['renderReproduction'],'portableReproduction':V['portableReproduction'],'fullImageRegionLocalization':str(O/'region-localization.json'),'actualFloorMetrics':str(O/'floor-consumer-metrics.json'),'allBackgroundWorstResiduals':str(O/'worst-all-context-residuals.json'),'sharedFamilyGeometry':'Exact approved open rail sections and native honey timber frame/legs, foot shoes and attached brass pegs copied in local frame under this W source orientation. Own W deck mesh/UV and linear native action retained. No collar, rail cap, overhang, raster texture or per-view repair.','reproduce':'Source-only: source/capture_native.py beside main.blend, or unzip portable-source.zip anywhere and run capture.py. Full experiment build script requires exact original source and approved family/sibling projects recorded in nativeAssemblyContract.'})
write(P/'source/round-01-recipe.json',recipe)
html=(O/'previews/review.html').read_text()
html=html.replace('<option>game</option>','<option>game-floor-cream</option>')
html=html.replace('../consumer/outputs/${v.mode}',"../consumer/${b==='game-floor-cream'?'floor-outputs':'outputs'}/${v.mode}")
if 'id="magnify"' not in html:html=html.replace('<div id="views"></div>','<label><input id="magnify" type="checkbox">Enlarge pixels</label><div id="views"></div>')
html=html.replace('let factor=p===32?4:p===55?2:1',"let factor=document.querySelector('#magnify').checked?(p===32?4:p===55?2:1):1")
(O/'previews/review.html').write_text(html)
D.update({'recipeScript':'source/capture_native.py','portableSource':str(O/'portable-source.zip'),'fullImageResidualLocalization':str(O/'region-localization.json'),'actualFloorMetrics':str(O/'floor-consumer-metrics.json'),'approvedFixtures':str(O/'approved-fixture-hashes.json'),'directedRouteAudit':str(O/'directed-route-audit.json'),'worstCasesAllContexts':str(O/'worst-all-context-residuals.json'),'allTechnicalChecksPass':all(checks.values()),'actualGPUCaptureCount':V['consumer']['allActualCaptureCount'],'actualGPUComparisonPairCount':V['consumer']['allActualPairCount'],'remainingReview':'Root coordinator seals exact bytes; independent W judge evaluates frozen criteria, actual residual pixels and ordinary-size motion/context. No editor approval.'})
D['previews'].update({'repeated':str(O/'previews/repeated-WWW-S.png'),'four-view-sheet':str(O/'previews/four-view-sheet.png'),**{'running-'+d:str(O/'previews'/f'running-{d}.png') for d in 'NESW'}})
for path in (O/'previews').iterdir():
 if path.is_file():D['previews'][path.stem]=str(path)
for a in D['atlases']:a.update({'atlasSize':[2304,2816],'rects':[[i%6*384,i//6*704,384,704] for i in range(24)]})
resources=[]
for folder in [P/'source',O]:
 for path in folder.rglob('*'):
  if path.is_file() and '.godot' not in path.parts and path.suffix not in ['.ctex','.blend1','.pyc','.log'] and path.name not in ['delivery.json','packet.json','delivery.snapshot.json'] and path not in [P/'source/round-01.blend']:resources.append(str(path))
resources.extend(str(P/'inputs'/n) for n in ['family-settings.json','family-approval.json','approved-family-native-S.png'])
resources.extend(str(path) for path in [P/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',P/'../belt-straight-n/source/round-09.blend',P/'../belt-straight-e/source/round-01.blend',P/'../belt-straight-s/source/round-01.blend'])
D['resources']=sorted(set(resources));D['allRawFrames']=D['rawFrames'];D['projectSHA256']=H(D['project']);D['recipeSHA256']=H(D['recipe']);D['recipeScriptSHA256']=H(D['recipeScript'])
config=read(O/'consumer/config.json');config['nativeReferenceDirectory']='res://../native-runs';config['objectRoot']='res://../../..';write(O/'consumer/config.json',config)
for name in ['bench_round01.gd','bench_floor_round01.gd']:
 path=P/'source'/name;code=path.read_text().replace('var reference_path := str(config.nativeReferenceDirectory).path_join(', 'var reference_path := ProjectSettings.globalize_path(str(config.nativeReferenceDirectory)).path_join(');path.write_text(code);shutil.copyfile(path,O/'consumer'/('bench-floor.gd' if 'floor' in name else 'bench.gd'))
# Experiment metadata uses relative filesystem references, including exact sibling/source dependencies.
def normalize(v):
 if isinstance(v,list):return [normalize(x) for x in v]
 if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
 if isinstance(v,str) and v.startswith('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/'):
  return os.path.relpath(v,P)
 return v
for path in list(O.rglob('*.json'))+[P/'source/round-01-recipe.json']:
 if '.godot' not in path.parts and path.name not in ['delivery.json','packet.json','delivery.snapshot.json']:
  try:write(path,normalize(read(path)))
  except json.JSONDecodeError:pass
D=normalize(D);D['recipeSHA256']=H(D['recipe']);write(O/'delivery.json',D);write(P/'delivery.json',D)
print(json.dumps({'source':D['projectSHA256'],'technicalChecksPass':D['allTechnicalChecksPass'],'failedChecks':[k for k,v in checks.items() if not v],'gpuCaptures':D['actualGPUCaptureCount'],'comparisonPairs':D['actualGPUComparisonPairCount'],'resources':len(resources)},indent=2))
