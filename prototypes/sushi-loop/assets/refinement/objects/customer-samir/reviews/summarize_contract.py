import json,pathlib,math,hashlib
from PIL import Image,ImageDraw
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir');R=P/'reviews'
main=json.loads((R/'baseline-main/audit.json').read_text());runtime=json.loads((R/'baseline-runtime/audit.json').read_text())
summary={'camera':main['camera'],'logicalFrame':[192,320],'logicalRoot':[96,248],'nativeFrame':[384,640],'rootNativePixels':main['rootProjection'],'cellSizeLogicalPixels':128,'nativeScale':main['root']['scale'],'footprint':[1,1],'restBoneCount':len(main['rig']['bones']),'restSHA256':main['rig']['restSHA256'],'runtimeRestSHA256':runtime['rig']['restSHA256'],'bodyOnlyMeshCount':48,'bodyEnvelopeBasis':'Native evaluated modifier geometry at all 480+96 required samples. Source anatomy metadata is 1.3968749344 cells in neutral pose; seat lift applies before bounding. Packed food plane/hidden utensil excluded. These are diagnostic baselines, not per-vertex coordinate locks.','clips':{},'foodDepth':{},'requiredEvidence':{'main':{'states':10,'framesPerState':12,'facings':4,'frames':480,'atlases':40,'clips':40},'runtimeVariants':{'states':['eat-salmon','seated-wait-empty'],'framesPerState':12,'facings':4,'frames':96,'atlases':8,'clips':8},'totalFrames':576}}
for mode,a in [('main',main),('runtime',runtime)]:
 allsamples=[s for c in a['clips'].values() for s in c['samples']];deltas=[]
 for s in allsamples:
  delta=[s['foodPlaneMatrix'][i][3]-s['foodRootWorld'][i] for i in range(3)];deltas.append(delta)
 ray=[0,-math.cos(math.radians(35)),math.sin(math.radians(35))]
 scalars=[sum(x*y for x,y in zip(d,ray)) for d in deltas]
 perpendicular=[math.sqrt(sum((d[i]-scalar*ray[i])**2 for i in range(3))) for d,scalar in zip(deltas,scalars)]
 palm_errors=[]
 for s in allsamples:
  palms=s['evaluatedContactsWorld']['palms'];mid=[(palms['L'][i]+palms['R'][i])/2 for i in range(3)];expected=[mid[0],mid[1],mid[2]+.0225]
  palm_errors.append(math.sqrt(sum((x-y)**2 for x,y in zip(expected,s['foodRootWorld']))))
 summary['foodDepth'][mode]={'foodRootPalmAttachmentOffsetWorldZ':.0225,'maximumFoodRootPalmAttachmentErrorWorldCells':max(palm_errors),'sourceRawAuditSHA256':hashlib.sha256((R/('baseline-'+mode)/'audit.json').read_bytes()).hexdigest(),'hiddenPlaneMeasurement':'Visibility recorded after native action evaluation; temporarily unhide render/viewport for depsgraph matrix evaluation, then restore before render. Hidden child matrices otherwise can remain stale.','towardCameraUnitRay':ray,'sourceDepthRangeCells':[min(scalars),max(scalars)],'maximumPerpendicularResidualCells':max(perpendicular),'sourceVisibleOwner':a['food']['owner'],'originalTextureSHA256':a['food']['packedSHA256'],'yawCancellation':a['food']['drivers'],'policyProposal':'One constant scalar per canonical food composition in [0,.6] cells along exact camera ray, fixed across every state/frame/facing including hidden samples. No lateral/vertical/projected anchor shifts. Baseline .6 retained in provenance. Geometry→food/body occlusion may change; cannot force visible food on rear head. Measure all projected quad corners and mapped bottom-rim support against depth=.6 on same canonical mapping, tolerance .01 native pixel. Do not compare replacement full-UV quad corners to old cropped/padded quad corners as a mapping criterion.'}
 for clip,c in a['clips'].items():
  per={}
  for dr in ['S','E','N','W']:
   ss=[s for s in c['samples'] if s['direction']==dr]
   per[dr]={'min':[min(s['bodyBounds'][0][i] for s in ss) for i in range(3)],'max':[max(s['bodyBounds'][1][i] for s in ss) for i in range(3)]}
  summary['clips'][clip]={'source':mode,'loop':c['loop'],'bodyBoundsByDirection':per,'bodyBoundsUnion':c['boundsUnion'],'foodVisibleSamples':c['foodVisibleCount'],'pelvisZRange':[min(s['pelvis'][2] for s in c['samples']),max(s['pelvis'][2] for s in c['samples'])],'frameDataPath':str(R/('baseline-'+mode)/'audit.json')}
(R/'source-contract-summary.json').write_text(json.dumps(summary,indent=2))
# Actual legacy runtime atlas cardinal labels, no assumed authority.
sheet=Image.new('RGB',(4*192,4*330),(110,110,110));d=ImageDraw.Draw(sheet);legacy=P.parents[3]/'godot/assets/recipe-variants/sprites/customer-samir'
for y,(clip,kind) in enumerate([(c,k) for c in ['eat-salmon','seated-wait-empty'] for k in ['native','legacy']]):
 for x,dr in enumerate(['S','E','N','W']):
  im=Image.open(R/'baseline-runtime'/(clip+'-'+dr+'-f05.png') if kind=='native' else legacy/(clip+'-'+dr+'.png')).convert('RGBA')
  if kind=='legacy':im=im.crop((4*384,0,5*384,640))
  im=im.resize((192,320));sheet.paste(im,(x*192,y*330+10),im);d.text((x*192+2,y*330),clip+' '+kind+' '+dr,fill='white')
sheet.save(R/'runtime-native-versus-legacy-cardinals.jpg',quality=94)
print(json.dumps({'depth':summary['foodDepth'],'bounds':{c:v['bodyBoundsUnion'] for c,v in summary['clips'].items()}},indent=2))
