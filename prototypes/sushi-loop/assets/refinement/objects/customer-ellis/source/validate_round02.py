from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import numpy as np,json,hashlib,shutil
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
main=json.loads((OUT/'main-native-audit.json').read_text());runtime=json.loads((OUT/'runtime-native-audit.json').read_text());exports=json.loads((OUT/'export-validation.json').read_text());surfaces=[json.loads((OUT/(m+'-surface-audit.json')).read_text()) for m in ['main','runtime']]
norm=lambda n:n.split('customer_ellis__')[-1]
a={norm(k):v for k,v in main['bodyGeometry'].items()};b={norm(k):v for k,v in runtime['bodyGeometry'].items()}
comparison={'geometryCount':len(a),'identicalCoordinates':all(a[k]['coordinateSHA256']==b[k]['coordinateSHA256'] for k in a),'identicalWeights':all(a[k]['weightsSHA256']==b[k]['weightsSHA256'] for k in a),'identicalGroupNames':all(a[k]['vertexGroups']==b[k]['vertexGroups'] for k in a),'sameRenderSettings':main['renderSettings']==runtime['renderSettings'],'sameLights':main['lights']==runtime['lights']}
repeats=[]
for mode,clip,d,frame in [('main','stand','S',4),('main','eat','E',11),('main','panic','N',6),('runtime','eat-salmon','S',4)]:
 paths=[OUT/'diagnostics'/f'{mode}-{clip}-{d}-repeat-{i}.png' for i in range(2)];ref=OUT/('frames' if mode=='main' else 'runtime-frames')/(clip+'-'+d)/f'{frame:03}.png'
 arrays=[np.array(Image.open(p).convert('RGBA')).astype(np.int16) for p in paths];ra=np.array(Image.open(ref).convert('RGBA')).astype(np.int16)
 diff=np.abs(arrays[0]-arrays[1]);rdiff=np.abs(arrays[0]-ra)
 repeats.append({'mode':mode,'clip':clip,'direction':d,'frameIndex':frame,'repeatPNGFileSHAEqual':sha(paths[0])==sha(paths[1]),'repeatDifferingRGBAPixels':int(np.any(diff,axis=2).sum()),'repeatMaxChannelDelta':int(diff.max()),'repeatMaxAlphaDelta':int(diff[:,:,3].max()),'exportDifferingRGBAPixels':int(np.any(rdiff,axis=2).sum()),'exportMaxChannelDelta':int(rdiff.max())})
# Original legacy-labeled atlas, original native source and remodeled native source,
# all drawn at the unchanged logical frame registration (no silhouette fitting).
font=ImageFont.load_default(size=16);canvas=Image.new('RGB',(768,1030),(237,232,219));draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['Original labeled production frame 0','Original actual native source frame 1','Remodeled actual native frame 1']):
 draw.text((8,row*342+4),label,fill=(28,38,48),font=font)
 for i,d in enumerate('NESW'):draw.text((i*192+165,row*342+4),d,fill=(28,38,48),font=font)
 for i,d in enumerate('NESW'):
  if row==0:
   f=OBJ.parents[2]/'production/sprites/customer-ellis'/('stand-'+d+'.png');copy=HERE/'resources/context'/('original-stand-'+d+'.png');shutil.copyfile(f,copy);im=Image.open(f).convert('RGBA').crop((0,0,384,640))
  elif row==1:im=Image.open(OUT/'diagnostics'/('original-native-stand-'+d+'.png')).convert('RGBA')
  else:im=Image.open(OUT/'frames'/('stand-'+d)/'000.png').convert('RGBA')
  im=im.resize((192,320),Image.Resampling.LANCZOS);canvas.paste(im,(i*192,row*342+22),im)
canvas.save(OUT/'source-direction-proof.png')
originalFlags=json.loads((OUT/'diagnostics/original-diagnostics.json').read_text())['foodFlags'];finalFlags=json.loads((OUT/'diagnostics/main-diagnostics.json').read_text())['foodFlags']
shader={'originalFlags':originalFlags,'finalFlags':finalFlags,'change':'One static global BLENDED alpha and visible_shadow=False on canonical food plane; unchanged material nodes, exact packed image bytes, fullUV/aspect, fixedsemanticmap, .6raydepth, food-root/actions/yaw/render-visibility.','evidence':'diagnostics/ contains matched source/final alpha-flag native captures at frame5 in all four facings for main wait/eat and runtime salmon/empty. All48 final native temporal clips preserve this same setup.'}
validation={'asset':'customer-ellis','round':2,'status':'technical evidence complete; independent visual verdict pending','briefSHA256':sha(OBJ/'brief.json'),'sourceContractSHA256':sha(HERE/'resources/frozen-source-contract.json'),'foodMappingSHA256':sha(HERE/'resources/frozen-food-mappings.json'),'nativeFrames':len(exports['frames']),'mainFrames':480,'runtimeFrames':96,'atlases':len(exports['atlases']),'actual12fpsClips':len(exports['clips']),'capture':main['camera'],'bodyParity':comparison,'nativeAuditMaxErrors':{x['mode']:x['maxErrors'] for x in [main,runtime]},'envelopeFailures':sum(len(x['envelopeFailures']) for x in [main,runtime]),'restMatchesSource':all(x['restMatchesSource'] for x in [main,runtime]),'actionsMatchSource':all(x['actionsMatchSource'] for x in [main,runtime]),'evaluatedFunctionalSurfaceMaximumWorld':max(x['maxSurfaceErrorWorld'] for x in surfaces),'surfaceToleranceWorld':.005,'functionalSurfaceFailures':sum(len(x['failures']) for x in surfaces),'alphaEdgeFailures':exports['alphaFailures'],'atlasWholeCanvasCopyFailures':exports['atlasCopyFailures'],'rendererRepeatability':{'empiricalSamples':repeats,'interpretation':'Only these local Blender5.2.2 EEVEE32 repeats measured. No renderer-wide or cross-platform bit-identity claim.'},'foodAlphaFlags':shader,'dependencies':{'main':main['dependencies'],'runtime':runtime['dependencies']},'limits':['Independent original judge has not reviewed this candidate.','Frozen front target does not establish unseen exact reference views.','Native .6 display-ray depth retained; original mapped plate size/support and authored pose trajectories remain.','Review WebM files are temporal previews encoded VP9alpha4:2:0; promoted PNG frames/atlases remain exact complete native RGBA pixels.','The earlier hand-weight failure is retained read-only as draft-01-hand-weights with exact failed source/output hashes; that draft is not a candidate.']}
assert all(comparison.values()) and not validation['envelopeFailures'] and validation['restMatchesSource'] and validation['actionsMatchSource'] and not validation['functionalSurfaceFailures'] and not validation['alphaEdgeFailures'] and not validation['atlasWholeCanvasCopyFailures']
browser=json.loads((OUT/'browser-playback.json').read_text())
validation['browserPlayback']=[{'viewport':r['viewport'],'states':len(r['clips']),'clipDirections':sum(len(c['after']) for c in r['clips']),'elapsedMS':r['completedAt']-r['startedAt'],'allDirectionsDecodedAtLeast12':all(v['totalVideoFrames']>=12 for c in r['clips'] for v in c['after']),'allNonLoopsEnded':all(v['ended'] for c in r['clips'] if not c['loop'] for v in c['after']),'maximumDroppedFrames':max(v['droppedVideoFrames'] for c in r['clips'] for v in c['after'])} for r in browser]
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print('ELLIS_VALIDATION',comparison,repeats,flush=True)
