"""Make immutable editor delivery/resource manifest; does not seal a packet."""
from pathlib import Path
import json,hashlib,os,datetime
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
ledger=json.loads((O/'consumer-ledger.json').read_text());native=json.loads((O/'native-validation.json').read_text())
heroes={d:f'candidates/round-01/frames/static/{d}/000.png' for d in 'NESW'}
previews={'four-view-sheet':'candidates/round-01/four-view-sheet.png','phone':'candidates/round-01/consumer/full-chromium/viewport-320x720.png','repeated':'candidates/round-01/consumer/full-chromium/09-repeat.png'}
for d in 'NESW':previews['native-'+d]=f'candidates/round-01/native/static/{d}/000.png'
for run in ledger['runs']:
 for case in [*run['cases'],*run['viewportContexts']]:
  previews[run['mode']+'-'+Path(case['screenshot']).stem]=case['screenshot']
aliases=[]
for d in 'NESW':
 paths=[heroes[d],f'candidates/round-01/atlases/static-{d}.png',f'source/round-01-resources/consumer/sprites/decor-background-wreck/static-{d}.png']
 assert len({sha(B/p) for p in paths})==1
 aliases.append({'role':'exact published fullframe/original singleframe atlas/actual consumer own input','direction':d,'paths':paths,'sha256':sha(B/paths[0])})
for name in ['phone','repeated']:
 same=[k for k,v in previews.items() if v==previews[name]]
 aliases.append({'role':'brief required preview alias to exact declared actual media','previewNames':same,'path':previews[name],'sha256':sha(B/previews[name])})
put(O/'inspection-map.json',{'asset':'decor-background-wreck','pathBase':'object-root','candidateRenders':heroes,'previews':previews,'exactByteAliases':aliases,'coverageNote':'Original judge must directly inspect every unique exact media path, with explicit samepath/hash aliases where applicable. This map makes no review or approval claim.'})
put(P/'round-01-delivery-notes.json',{'asset':'decor-background-wreck','round':'round-01','changes':['Rebuilt hull as three rounded tapered blue timber courses with one intentional worn notch; depth .19 for actual coherent ends.','Rounded native mast and crossbar, joined three-part small cabin/roof, two muted rope wraps and one tiny integrated end-grain cap.','Single symmetric broad overhead/fourfill/neutralambient lighting recipe; native Cycles48samples fixedseed17/BlackmanHarris1.5, no cast ground plane, no external textures.'],'evidence':['Render-time actual properNESW root/camera matrices and calibration recorded from clean saved source.','REST envelope measured and static holds/frame1,2,12,25 geometry digests equal with all effective channel owners listed.','Wholecanvas LANCZOS publication and original oneframe atlas byte aliases.','Frozen099/570 native-nearest-after-resize browser fixture ran15casesx2modes plus2actual final viewport captures/mode; Chromium153/DPR1/errors/executable/options/inputs recorded.'],'technicalLimits':['No native project changes after capture. Source integrity preserved.','Ordinary CSS mode-specific residuals retained; native canvases match, screenshot channels differ up to34.','Historical source replay/native/CSS residual evidence stays referenced frozen preparation; current modeling intentionally changes source pixels.','Static standalone background asset only; no ground support, modular family, full React UI, Godot or device claim.'],'originalJudgeApproval':'pending; editor does not grade or approve','rootNextStep':'Make object-root byte-identical versioned delivery alias, seal packet using unchanged helper, dispatch original judge exact declared media.'})
skip={'round-01-resource-manifest.json','round-01-delivery.json','round-01-handoff.json','round-01-handoff.json.sha256'}
files=[]
for folder in [P,O]:
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or p.name in skip or '__pycache__' in p.parts:continue
  assert p.stat().st_size<100_000_000,(p,p.stat().st_size)
  files.append({'path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest=O/'round-01-resource-manifest.json'
put(manifest,{'asset':'decor-background-wreck','round':'round-01','pathBase':'object-root','objectRoot':str(B),'scope':'Immutable editor artifacts and minimal actual-used private native/browser/helper/art closure. Runtime trees deliberately excluded; exact runtime provenance is bound. No packet or review approval.','files':files})
resources=[{'path':r['path'],'sha256':r['sha256']} for r in files]
resources.append({'path':str(manifest.relative_to(B)),'sha256':sha(manifest)})
raw=[{'clip':'static','direction':d,'index':0,'path':heroes[d]} for d in 'NESW']
nativeframes=[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/native/static/{d}/000.png'} for d in 'NESW']
atlases=[{'clip':'static','direction':d,'path':f'candidates/round-01/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW']
delivery={'asset':'decor-background-wreck','round':'round-01','project':'source/round-01.blend','recipeScript':'source/round-01-build.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':heroes,'previews':previews,'rawFrames':raw,'nativeRawFrames':nativeframes,'atlases':atlases,'resources':resources,'resourceManifest':{'path':str(manifest.relative_to(B)),'sha256':sha(manifest),'pathBase':'object-root'},'visualInspectionMap':'candidates/round-01/inspection-map.json','notes':'Exact static native construction/capture/publication/consumer evidence. ROOT alone makes object-root delivery alias/seals packet and original judge decides visual verdict.'}
dp=O/'round-01-delivery.json';put(dp,delivery)
handoff={'asset':'decor-background-wreck','round':'round-01','createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pathBase':'object-root','delivery':{'path':str(dp.relative_to(B)),'sha256':sha(dp)},'resourceManifest':{'path':str(manifest.relative_to(B)),'sha256':sha(manifest),'fileCount':len(files)},'project':{'path':'source/round-01.blend','sha256':sha(P/'round-01.blend')},'frozenBriefSHA256':sha(B/'brief.json'),'frozenContractSHA256':sha(B/'inputs/root-native-contract.json'),'frozenCriteriaSHA256':sha(B/'reviews/proposedcriteria.json'),'initialSHA256':sha(P/'initial-observations.json'),'acknowledgmentSHA256':sha(P/'construction-acknowledgment.json'),'coverage':{'uniqueHeroPaths':len(set(heroes.values())),'previewNames':len(previews),'uniquePreviewPaths':len(set(previews.values())),'nativeViews':4,'publishedViewsAndAtlases':4,'consumerCasesPerMode':15,'actualViewportContextsPerMode':2,'browserModes':2},'sourceUnchangedAfterCapture':sha(P/'round-01.blend')==native['sourceProjectSHA256'],'scope':'Stop here for ROOT packet seal/original judge; no editor self-grade, criteria/brief/review/sharedhelper/production/Git/device/liveBlender changes or extra agents.'}
hp=O/'round-01-handoff.json';put(hp,handoff);side=hp.with_suffix('.json.sha256');side.write_text(sha(hp)+'  round-01-handoff.json\n')
for r in files:os.chmod(B/r['path'],0o444)
for p in [manifest,dp,hp,side]:os.chmod(p,0o444)
print(json.dumps({'handoff':str(hp),'handoffSHA256':sha(hp),'delivery':str(dp),'deliverySHA256':sha(dp),'resourceManifestSHA256':sha(manifest),'resources':len(files),'projectSHA256':sha(P/'round-01.blend'),'coverage':handoff['coverage']},indent=2))
