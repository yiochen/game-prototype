"""Complete native round-03 handoff, without sealing or visual self-approval."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import copy,hashlib,json,importlib.util,os,sys,tempfile
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';RUN=OBJ.parents[1];PROTOTYPE=RUN.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
relative=lambda p:os.path.relpath(Path(p).resolve(),OBJ.resolve())
def record(p,role='native-evidence'):return {'path':relative(p),'sha256':sha(p),'role':role}
def write(p,data):
 content=json.dumps(data,indent=2)+'\n';p=Path(p)
 if p.exists():assert p.read_text()==content,f'Immutable output differs: {p}'
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
oldDelivery=read(OBJ/'delivery.round-02-import.json')
assert sha(OBJ/'delivery.round-02-import.json')=='b95f3342616aa873fa9081545a9d0b388267de15fed2c4093ad69437723ec380'
for r in oldDelivery['resources']:assert sha(OBJ/r['path'])==r['sha256'],r['path']
brief=read(HERE/'resources/frozen-brief.json');exp=read(OUT/'export-validation.json')
audits={m:read(OUT/(m+'-native-audit.json')) for m in ['main','runtime']}
surfaces={m:read(OUT/(m+'-surface-audit.json')) for m in audits}
aux={m:read(OUT/'diagnostics'/(m+'-native-settings.json')) for m in audits}
norm=lambda n:n.split('customer_ellis__')[-1]
main={norm(k):v for k,v in audits['main']['bodyGeometry'].items()};rt={norm(k):v for k,v in audits['runtime']['bodyGeometry'].items()}
parity={'meshCount':len(main),'matchingNames':main.keys()==rt.keys(),'coordinates':all(main[k]['coordinateSHA256']==rt[k]['coordinateSHA256'] for k in main),'weights':all(main[k]['weightsSHA256']==rt[k]['weightsSHA256'] for k in main),'groups':all(main[k]['vertexGroups']==rt[k]['vertexGroups'] for k in main),'shaders':aux['main']['bodyShaders']==aux['runtime']['bodyShaders'],'renderSettings':audits['main']['renderSettings']==audits['runtime']['renderSettings'],'lights':audits['main']['lights']==audits['runtime']['lights']}
assert all(parity.values())
preservation={}
for mode,audit in audits.items():
 old=read(OBJ/'candidates/round-02'/(mode+'-native-audit.json'));newBody={norm(k):v for k,v in audit['bodyGeometry'].items()};oldBody={norm(k):v for k,v in old['bodyGeometry'].items()}
 changed=[k for k in newBody if k in oldBody and newBody[k]!=oldBody[k]]
 assert set(changed)=={'glasses_arm_-1.001','glasses_arm_1.001'},changed
 assert set(oldBody)-set(newBody)=={'coherent_sculpted_hair'} and set(newBody)-set(oldBody)=={'swept_short_hair'}
 assert audit['camera']==old['camera'] and audit['renderSettings']==old['renderSettings'] and audit['lights']==old['lights'] and audit['food']==old['food']
 assert audit['armature']==old['armature'] and audit['actions']==old['actions']
 assert not audit['envelopeFailures'] and audit['restMatchesSource'] and audit['actionsMatchSource'] and not surfaces[mode]['failures']
 for s in audit['samples']:assert s['errors']['contacts']==s['errors']['root']==s['errors']['foodRoot']==s['errors']['foodPlane']==0
 assert all(v['allVerticesFullyHeadWeighted'] and v['groups']==['head'] for v in aux[mode]['objectGroupAssignments'].values())
 preservation[mode]={'changedExistingMeshes':changed,'removedMesh':'coherent_sculpted_hair','newMesh':'swept_short_hair','allOtherBodyGeometryWeightsModifiersMaterialsUnchanged':True,'cameraRenderLightsFoodRigRestAndActionsUnchanged':True,'audit':record(OUT/(mode+'-native-audit.json')),'priorAudit':record(OBJ/'candidates/round-02'/(mode+'-native-audit.json')),'actualHeadGroupAssignments':aux[mode]['objectGroupAssignments']}
def semantic_compositor(e):
 t=e['compositorTrees'][e['activeCompositorTree']];nodes=[]
 ui={'location','location_absolute','width','height','dimensions','name','label','select','show_options','show_preview','hide','use_custom_color','color','color_tag','warning_propagation','show_texture'}
 for node in t['nodes']:
  n={k:copy.deepcopy(v) for k,v in node.items() if k not in ['properties','sceneReference']};n['properties']={k:v for k,v in node['properties'].items() if k not in ui and not k.startswith('bl_')}
  if 'sceneReference' in node:n['sceneReference']='<captured scene>' if node['sceneReference']==e['scene'] else node['sceneReference']
  nodes.append(n)
 return {'nodes':nodes,'links':t['links'],'renderCompositingSettings':e['renderCompositingSettings'],'renderSettings':e['renderSettings']}
comp={m:read(OUT/'native-records'/f'compositor-{m}.json') for m in audits}
for mode in audits:
 old=read(OBJ/'candidates/round-02/import-adapter-v1'/f'compositor-{mode}.json')
 assert semantic_compositor(comp[mode])==semantic_compositor(old)
 assert comp[mode]['sourceSHA256']==audits[mode]['projectSHA256']
assert semantic_compositor(comp['main'])==semantic_compositor(comp['runtime'])
repeats=[]
for mode,clip,d,index in [('main','stand','S',4),('main','eat','E',11),('main','panic','N',6),('runtime','eat-salmon','S',4)]:
 paths=[OUT/'diagnostics'/f'{mode}-{clip}-{d}-repeat-{i}.png' for i in range(2)]
 arrays=[np.array(Image.open(p).convert('RGBA')).astype(np.int16) for p in paths];ref=np.array(Image.open(OUT/('frames' if mode=='main' else 'runtime-frames')/(clip+'-'+d)/f'{index:03}.png').convert('RGBA')).astype(np.int16)
 diff=np.abs(arrays[0]-arrays[1]);delta=np.abs(arrays[0]-ref)
 repeats.append({'mode':mode,'clip':clip,'direction':d,'index':index,'repeatDifferingRGBAPixels':int(np.any(diff,axis=2).sum()),'repeatMaxChannelDelta':int(diff.max()),'exportDifferingRGBAPixels':int(np.any(delta,axis=2).sum()),'exportMaxChannelDelta':int(delta.max())})
# Portable reproduction actually executed in both modes; compare native studies.
reproduction=[]
for mode in audits:
 for d in 'NESW':
  p=OUT/'study'/(mode+'-'+d+'.png');q=OBJ/'candidates/reproduction-round03/study'/(mode+'-'+d+'.png');a=np.array(Image.open(p)).astype(np.int16);b=np.array(Image.open(q)).astype(np.int16);delta=np.abs(a-b)
  reproduction.append({'mode':mode,'direction':d,'actual':record(p),'portableReproduction':record(q),'differingPixels':int(np.any(delta,axis=2).sum()),'maxChannelDelta':int(delta.max())})
write(OUT/'portable-reproduction-validation.json',{'actuallyExecutedBothModes':True,'script':record(HERE/'reproduce_round03.py'),'nativeRecipe':record(HERE/'build_round03.py'),'cardinalComparisons':reproduction,'interpretation':'Native geometry recipe and packed immutable inputs reproduced in both modes. Local renderer pixel deltas recorded empirically; no cross-platform bit identity assertion.'})
# Registered old actual source / old reviewed candidate / new candidate canvases.
font=ImageFont.load_default(size=16)
for name,rows in [('source-direction-proof',[('Original actual native source',OBJ/'candidates/round-02/diagnostics','original-native-stand-{d}.png'),('Reviewed round 02',OBJ/'candidates/round-02/frames','stand-{d}/000.png'),('Round 03',OUT/'frames','stand-{d}/000.png')]),('four-view-sheet',[('Round 03 native, full logical frame',OUT/'frames','stand-{d}/000.png')])]:
 canvas=Image.new('RGB',(768,342*len(rows)),(237,232,219));draw=ImageDraw.Draw(canvas)
 for row,(label,folder,pattern) in enumerate(rows):
  draw.text((8,row*342+4),label,fill=(28,38,48),font=font)
  for i,d in enumerate('NESW'):
   im=Image.open(folder/pattern.format(d=d)).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);canvas.paste(im,(i*192,row*342+22),im)
 canvas.save(OUT/(name+'.png'))
browser=read(OUT/'browser-playback.json');browserSummary=[]
for r in browser:
 assert len(r['clips'])==12 and all(len(c['after'])==4 for c in r['clips'])
 summary={'viewport':r['viewport'],'states':12,'clipDirections':48,'elapsedMS':r['completedAt']-r['startedAt'],'allDirectionsDecodedAtLeast12':all(v['totalVideoFrames']>=12 for c in r['clips'] for v in c['after']),'allNonLoopsEnded':all(v['ended'] for c in r['clips'] if not c['loop'] for v in c['after']),'maximumDroppedFrames':max(v['droppedVideoFrames'] for c in r['clips'] for v in c['after'])}
 assert summary['allDirectionsDecodedAtLeast12'] and summary['allNonLoopsEnded'];browserSummary.append(summary)
metadata={'main':{r['id']:r for r in brief['delivery']['requiredClips']},'runtime':read(OBJ/'inputs/runtime-variants/original-object.json')['clips']}
bundles={};phase=[];nativeChecks={}
for mode in audits:
 project=HERE/('round-03.blend' if mode=='main' else 'round-03-runtime.blend');audit=audits[mode];oldBundle=oldDelivery if mode=='main' else oldDelivery['runtimeVariants']
 camera=read(OBJ/oldBundle['nativeRecords']['camera']);asset=read(OBJ/oldBundle['nativeRecords']['assetRecord'])
 for v in [camera,asset]:v.pop('importMetadataAdapter',None);v['artStyle']['revision']='warm-soft-cartoon-ellis-round03';v['nativeRevision']={'inputSource':record(HERE/('round-02.blend' if mode=='main' else 'round-02-runtime.blend')),'change':'Hair mesh and exposed spectacle arm paths only; original source settings retained.','compositorEvidence':record(OUT/'native-records'/f'compositor-{mode}.json')}
 camera['nativeProjectSHA256']=sha(project);asset['captureFingerprint']=hashlib.sha256(json.dumps(camera,sort_keys=True).encode()).hexdigest()
 assert camera['captureScale']==asset['scale']==audit['camera']['captureScale']==2
 assert camera['frame']==audit['camera']['logicalFrame']==[192,320] and camera['anchor']==audit['camera']['logicalRoot']==[96,248]
 assert camera['camera']['worldMatrix']==audit['camera']['matrix'] and camera['camera']['shift']==audit['camera']['shift'] and camera['camera']['orthoScale']==audit['camera']['orthoScale'] and camera['artStyle']==asset['artStyle']
 for kind,v in [('camera',camera),('assetRecord',asset)]:write(OUT/'native-records'/f'{mode}-{kind}.json',v)
 raw=[]
 for index,s in enumerate(audit['samples']):
  clip=next(k for k,v in metadata[mode].items() if v.get('sourceClipId',k)==s['clip']);p=OBJ/s['render'];assert sha(p)==s['renderSHA256']
  raw.append({'clip':clip,'direction':s['direction'],'index':s['frame']-1,'path':s['render'],'sha256':s['renderSHA256']})
  phase.append({'mode':mode,'clip':clip,'sourceClipId':s['clip'],'direction':s['direction'],'index':s['frame']-1,'sourceFrame':s['frame'],'rootMatrix':s['rootMatrix'],'render':s['render'],'renderSHA256':s['renderSHA256'],'measuredAudit':relative(OUT/(mode+'-native-audit.json')),'measuredAuditSHA256':sha(OUT/(mode+'-native-audit.json')),'sampleIndex':index})
 atlases=[]
 for r in exp['atlases']:
  if r['mode']!=mode:continue
  meta=metadata[mode][r['id']];atlases.append({**r,'clip':r['id'],'size':[2304,1280],'frameWidth':384,'frameHeight':640,'frames':12,'fps':meta['fps'],'loop':meta['loop'],'frameOrder':meta['frameOrder']})
 bundles[mode]={'project':relative(project),'projectSHA256':sha(project),'recipeScript':'source/reproduce_round03.py','validation':'candidates/round-03/validation.json','nativeRecords':{'camera':f'candidates/round-03/native-records/{mode}-camera.json','assetRecord':f'candidates/round-03/native-records/{mode}-assetRecord.json','rig':f'source/resources/{mode}-rig.json'},'rawFrames':raw,'atlases':atlases,'previews':{f'{c}-{d}':f'candidates/round-03/playback/{c}-{d}.webm' for c in metadata[mode] for d in 'NESW'},'publishedSourceScale':2,'nativeCaptureScale':2}
 nativeChecks[mode]={'cameraMatchesActualNativeMatrix':True,'frame':[192,320],'root':[96,248],'nativeFrame':audit['camera']['resolution'],'nativeCaptureScale':2,'publishedSourceScale':2,'artStyleMatchesNativeCompositor':True,'artStyle':camera['artStyle']}
assert len(bundles['main']['rawFrames'])==480 and len(bundles['main']['atlases'])==40 and len(bundles['runtime']['rawFrames'])==96 and len(bundles['runtime']['atlases'])==8
write(OUT/'phase-ledger.json',{'asset':'customer-ellis','kind':'measured-native-capture-phases','interpretation':'Directions and root matrices copied verbatim from actual native evaluations; no rotation inferred from filenames or expected facing.','renders':phase})
validation={'asset':'customer-ellis','round':3,'status':'technical evidence complete; original independent visual verdict pending','briefSHA256':sha(OBJ/'brief.json'),'nativeFrameCount':576,'mainFrameCount':480,'runtimeFrameCount':96,'atlasCount':48,'actual12fpsClipCount':48,'renderManifest':'phase-ledger.json','renderManifestSHA256':sha(OUT/'phase-ledger.json'),'capture':audits['main']['camera'],'bodyParity':parity,'round02Preservation':preservation,'nativeRecordCompatibility':nativeChecks,'nativeAuditMaxErrors':{m:a['maxErrors'] for m,a in audits.items()},'envelopeFailures':sum(len(a['envelopeFailures']) for a in audits.values()),'restMatchesSource':all(a['restMatchesSource'] for a in audits.values()),'actionsMatchSource':all(a['actionsMatchSource'] for a in audits.values()),'evaluatedFunctionalSurfaceMaximumWorld':max(s['maxSurfaceErrorWorld'] for s in surfaces.values()),'surfaceToleranceWorld':.005,'functionalSurfaceFailures':sum(len(s['failures']) for s in surfaces.values()),'alphaEdgeFailures':exp['alphaFailures'],'atlasWholeCanvasCopyFailures':exp['atlasCopyFailures'],'rendererRepeatability':{'empiricalSamples':repeats,'interpretation':'Only these local Blender5.2.2 EEVEE32 repeats measured; no renderer-wide or cross-platform bit identity claim.'},'portableRecipeEvidence':'portable-reproduction-validation.json','compositorEvidence':{m:record(OUT/'native-records'/f'compositor-{m}.json') for m in audits},'mainRuntimeCompositorSemanticAgreement':True,'compositorMatchesRound02':True,'foodFlagsAndMapUnchanged':True,'foodCanonicalSHA256':{m:a['food']['mappingCanonicalSHA256'] for m,a in audits.items()},'dependencies':{m:a['dependencies'] for m,a in audits.items()},'browserPlayback':browserSummary,'limits':['Independent original judge has not reviewed round 03.','Frozen front target does not establish exact unseen reference views.','Native fixed .6 display-ray food depth and canonical fullUV semantic map retained.','VP9 alpha temporal previews use 4:2:0; PNG frames/atlases retain complete native RGBA pixels.','Prior failed drafts and the first rejected round-03 hair study remain explicitly resource-bound.']}
assert not validation['alphaEdgeFailures'] and not validation['atlasWholeCanvasCopyFailures']
write(OUT/'validation.json',validation)
# Exercise the actual direction consumer without sealing or writing production.
spec=importlib.util.spec_from_file_location('direction',RUN/'tools/audit_directions.py');consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
with tempfile.TemporaryDirectory(prefix='ellis-round03-interface-') as temp:
 fake=Path(temp)/'customer-ellis';pb=fake/'candidates/interface-test';pb.mkdir(parents=True)
 packet={'capture':{'views':['N','E','S','W']},'files':{k:{'path':os.path.relpath(p.resolve(),pb.resolve()),'sha256':sha(p)} for k,p in [('nativeValidation',OUT/'validation.json'),('candidateResource:phaseLedger',OUT/'phase-ledger.json')]}}
 (pb/'packet.json').write_text(json.dumps(packet));direction=consumer.audit(fake,'interface-test')
assert direction['sampleCounts']=={d:144 for d in 'NESW'}
write(OUT/'consumer-checks.json',{'actualDirectionConsumer':direction,'method':'Temporary data-only packet fixture; no actual seal or approval.','frameCoverage':[480,96],'atlasCoverage':[40,8],'wholeCells':not exp['atlasCopyFailures'],'consumerSources':{str(p.relative_to(PROTOTYPE)):sha(p) for p in [RUN/'preparation/DELIVERY-CONTRACT.md',RUN/'tools/promote_object.py',RUN/'tools/save_runtime_variant_approval.py',RUN/'tools/audit_directions.py',PROTOTYPE/'godot/tools/refined_actor_variants.py']},'limitation':'Promotion/runtime approval receipt/Godot import require independent approval and main promotion; none executed here.'})
previews={**bundles['main']['previews'],**bundles['runtime']['previews'],**{k:f'candidates/round-03/{v}' for k,v in {'four-view-sheet':'four-view-sheet.png','repeated':'light-background.png','source-directions':'source-direction-proof.png','background-gray':'gray-background.png','background-dark':'dark-background.png','context-seated':'seated-wait-stool-context.png','context-eat-cucumber':'eat-stool-context.png','context-eat-salmon':'eat-salmon-stool-context.png','context-empty':'seated-wait-empty-stool-context.png','phone-eat-salmon':'browser-phone-eat-salmon.png','phone-empty-dark':'browser-phone-empty-dark.png','desktop-playback':'browser-desktop.png'}.items()}}
assert set(brief['capture']['previews'])<=set(previews) and all((OBJ/p).is_file() for p in previews.values())
resources={r['path']:r for r in oldDelivery['resources']}
for base in [HERE,OBJ/'candidates']:
 for p in sorted(base.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.name in ['.DS_Store','packet.json','delivery.snapshot.json']:continue
  r=record(p,'current-native-round03' if '/round-03/' in relative(p) or 'round03' in p.name else 'retained-native-source-and-evidence')
  if r['path'] in resources:assert resources[r['path']]['sha256']==r['sha256']
  else:resources[r['path']]=r
for p in [OBJ/'delivery.round-02.json',OBJ/'delivery.round-02-import.json',OBJ/'reviews/round-02.json',OBJ/'candidates/round-02/packet.json',OBJ/'candidates/round-02/delivery.snapshot.json']:
 if p.exists():resources[relative(p)]=record(p,'immutable-reviewed-round02')
failed=[r for r in resources.values() if 'draft-01-hand-weights' in r['path']];assert len(failed)==792
runtime=bundles['runtime'];runtime['resources']=[record(OBJ/p,'runtime-recipe-or-native-evidence') for p in [runtime['project'],runtime['recipeScript'],'source/build_round03.py','source/round-02-runtime.blend','source/resources/runtime-rig.json','source/resources/native_actions.py','source/resources/hair-height-envelope.json','source/resources/dish-salmon.png',runtime['validation'],'candidates/round-03/phase-ledger.json',*runtime['nativeRecords'].values(),*runtime['previews'].values()]]
delivery={**bundles['main'],'asset':'customer-ellis','round':'round-03','status':'complete native handoff; awaiting original independent judge; not sealed or approved','source':{'blend':bundles['main']['project'],'sha256':bundles['main']['projectSHA256'],'actuallyExecutedRecipe':'source/build_round03.py','actuallyExecutedRecipeSHA256':sha(HERE/'build_round03.py'),'reproductionScript':'source/reproduce_round03.py','portablePathAdapterValidation':'candidates/round-03/portable-reproduction-validation.json'},'heroes':{d:f'candidates/round-03/frames/stand-{d}/000.png' for d in 'NESW'},'previews':previews,'runtimeVariants':runtime,'resources':list(resources.values()),'counts':{'mainNativeFrames':480,'mainAtlases':40,'mainActual12fpsClips':40,'supplementalNativeFrames':96,'supplementalAtlases':8,'supplementalActual12fpsClips':8,'completeNativeFrames':576,'boundResourceFiles':len(resources)},'previousReviewedDelivery':record(OBJ/'delivery.round-02-import.json'),'frozenInputs':oldDelivery['frozenInputs'],'technicalSummary':{'bodyParity':parity,'clearanceFailures':validation['envelopeFailures'],'maxEvaluatedFunctionalSurfaceErrorWorld':validation['evaluatedFunctionalSurfaceMaximumWorld'],'browserPlayback':browserSummary,'unchangedCaptureCompositorFoodRigActions':True},'failedDraft':{'originalExplicitFileCount':792,'manifest':'source/draft-01-hand-weights/immutable-manifest.json','round03Study':'source/draft-round03-study01/manifest.json'},'limitations':validation['limits']}
assert all(sha(OBJ/r['path'])==r['sha256'] for r in delivery['resources'])
write(OBJ/'delivery.round-03.json',delivery)
print(json.dumps({'delivery':record(OBJ/'delivery.round-03.json'),'validation':record(OUT/'validation.json'),'phaseLedger':record(OUT/'phase-ledger.json'),'main':record(HERE/'round-03.blend'),'runtime':record(HERE/'round-03-runtime.blend'),'resources':len(resources),'retainedOriginalFailedDraftFiles':len(failed),'bodyParity':parity,'maximumSurfaceErrorWorld':validation['evaluatedFunctionalSurfaceMaximumWorld'],'browserPlayback':browserSummary},indent=2))
