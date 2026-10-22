from pathlib import Path
import json,math,hashlib,subprocess,shutil
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent.parent;S=O/'source';C=O/'candidates/round-01';P=C/'previews'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
R=C/'runtime-frames';frames=sorted(R.glob('*.png'));assert len(frames)==36
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(R/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','15',str(P/'godot-runtime-fade.mp4')],check=True)
# Poster and a fixed whole-viewport sequence; all pixels are real native Godot.
shutil.copyfile(R/'012.png',P/'repeated-registered-runtime.png')
contact=Image.new('RGB',(1080,3*380),'#f8f1df');dr=ImageDraw.Draw(contact)
for k,i in enumerate([0,6,12,18,24,30]):
 im=Image.open(R/f'{i:03}.png').convert('RGB').resize((540,380),Image.Resampling.LANCZOS);contact.paste(im,(k%2*540,k//2*380))
contact.save(P/'godot-runtime-temporal-contact.png')
# Runtime replay recipe, explicitly captures actual unchanged .9s fade in Godot.
(S/'capture_runtime_round01.py').write_text('''from pathlib import Path\nimport subprocess\nO=Path(__file__).resolve().parent.parent;N=O/'source/runtime-godot';R=O/'candidates/round-01/runtime-frames';R.mkdir(parents=True,exist_ok=True)\nsubprocess.run(['godot','--headless','--path',str(N),'--editor','--import'],check=True)\nsubprocess.run(['godot','--path',str(N),'--','--output',str(R)],check=True)\n''')
# Refresh exact source-closed fixture hashes after syntax repairs.
runtime=json.loads((C/'runtime-source-record.json').read_text());runtime['harnessSHA256']=sha(S/'runtime-godot/capture.gd');runtime['godotVersion']=subprocess.check_output(['godot','--version'],text=True).strip();runtime['actualCapture']={'frames':36,'fps':30,'durationSeconds':1.2,'rawViewportFramePaths':[p.relative_to(O).as_posix()for p in frames],'receipts':(R/'runtime-receipts.json').relative_to(O).as_posix(),'movie':(P/'godot-runtime-fade.mp4').relative_to(O).as_posix()};write(C/'runtime-source-record.json',runtime)
# Structural and exact phase/capture validation; no visual approval is asserted.
ledger=json.loads((C/'candidate-phases.json').read_text());native=json.loads((C/'native-scene-audit.json').read_text());cam=json.loads((C/'camera.json').read_text());index=json.loads((C/'packaging-index.json').read_text());brief=json.loads((O/'brief.json').read_text())
phaseerrs=[];areas={};allstats=[]
for r in ledger:
 t=r['index']/11;e=r['semanticEmitter'];scale=max(.025,max(0,math.sin(math.pi*t))**.45)
 phaseerrs.append({'position':max(abs(e['location'][k]-[0,0,.66+.42*t][k])for k in range(3)),'yaw':abs(e['rotationEuler'][2]-.7*t),'scale':max(abs(s-scale)for s in e['scale']),'visualYaw':abs(r['rootRotationZ']+r['visualCounterrotationZ'])})
 im=Image.open(O/r['path']).convert('RGBA');a=im.getchannel('A');area=sum(a.getdata())/255;areas[(r['direction'],r['index'])]=area;edge=a.crop((0,0,384,1)).getbbox()or a.crop((0,703,384,704)).getbbox()or a.crop((0,0,1,704)).getbbox()or a.crop((383,0,384,704)).getbbox()
 allstats.append({'direction':r['direction'],'index':r['index'],'alphaWeightedArea':area,'alphaBounds':a.getbbox(),'frameClipping':bool(edge),'sha256':sha(O/r['path'])})
union=[[min(r['bounds'][0][i]for r in ledger)for i in range(3)],[max(r['bounds'][1][i]for r in ledger)for i in range(3)]]
limits=[[-.32,-.225,.48],[.455,.225,1.465]]
ratios={d:[areas[d,i]/max(areas[d,j]for j in range(12))for i in [0,11]]for d in ['N','E','S','W']}
checks={'all48Frames':len(ledger)==48,'singleActualCamera':native['cameraCount']==1,'exactFrameAndRoot':cam['frame']==[192,352]and cam['anchor']==[96,256]and cam['captureScale']==2,'semanticPhaseTolerance':all(max(e.values())<.005 for e in phaseerrs),'counterrotationTolerance':all(e['visualYaw']<1e-5 for e in phaseerrs),'withinFrozenUnionEnvelope':all(union[0][i]>=limits[0][i]and union[1][i]<=limits[1][i]for i in range(3)),'endpointCollapseBelow1Percent':all(max(v)<=.01 for v in ratios.values()),'noRasterClipping':not any(s['frameClipping']for s in allstats),'manifoldNativeDimensionalMeshes':all(m['nonmanifoldEdges']==0 and m['signedVolume']>0 for m in native['meshes']),'noShadowBearingGround':native['noShadowBearingGround'],'noRasterSubstitute':all('ShaderNodeTexImage' not in m['nodeTypes']for m in native['materials']),'all12DistinctPerFacing':all(len({r['sha256']for r in ledger if r['direction']==d})==12 for d in ['N','E','S','W']),'actualGodotRuntimeFadeCaptured':len(frames)==36}
assert all(checks.values()),checks
V={'asset':'coin-pop','status':'technical-checks-passed-awaiting-independent-visual-review','briefSHA256':sha(O/'brief.json'),'nativeValidation':(C/'native-validation.json').relative_to(O).as_posix(),'renderManifest':(C/'candidate-phases.json').relative_to(O).as_posix(),'checks':checks,'measuredWorldUnion':union,'allowedWorldUnion':limits,'maxMeasuredSemanticErrors':{k:max(e[k]for e in phaseerrs)for k in phaseerrs[0]},'endpointAreaRatios':ratios,'rasterFrames':allstats,'sourceIntegrity':{'originalLibrary':(S/'original-library.blend').relative_to(O).as_posix(),'sha256':sha(S/'original-library.blend'),'matchesSource':sha(S/'original-library.blend')==brief['source']['projectSHA256']},'runtimeEvidence':(C/'runtime-source-record.json').relative_to(O).as_posix(),'lighting':'One centered100W area + eight equal35W radial softboxes on common radius3,z2.2,size4; neutral constant world. No geometry at ground. All facings share native camera/materials/lights.','nativeEditability':'Five closed manifold mesh objects: continuous lathed rim/face, beveled bar, three dimensional concave glints. Four native transform actions around explicit semantic emitters. No texture image nodes; one actual registered camera.'}
write(C/'native-validation.json',{'asset':'coin-pop','renderManifest':'candidate-phases.json','nativeSceneAudit':'native-scene-audit.json','measuredCamera':'camera.json','fps':12,'loop':False,'frameOrder':list(range(12)),'nativeFrameRange':[1,12],'contract':V['checks'],'lighting':V['lighting'],'semanticEmitter':'coin-pop__semantic_coin_emitter','measurementsSHA256':sha(C/'candidate-phases.json'),'sceneAuditSHA256':sha(C/'native-scene-audit.json')})
write(C/'validation.json',V)
# Actual playable mp4 clips with end-event evidence for independent browser inspection.
html='''<!doctype html><meta charset="utf-8"><title>Coin Pop Native Playback</title><style>body{background:#f8f1df;color:#253b3b;font:16px system-ui;margin:20px}video{display:block;max-width:100%;margin-bottom:10px}button{font:inherit;padding:10px 16px}#receipt{white-space:pre-wrap}</style><h1>Coin Pop · native nonloop playback</h1><p>Native12frames/12fps and actual Godot .9s runtime fade at the unchanged registered root. Replay runs both clips once.</p><button onclick="replay()">Replay both clips</button><h2>Four native facings · complete registered logical canvases</h2><video id="native" controls muted playsinline src="native-pop-all4.mp4"></video><h2>Actual Godot · 128 and64px/cell · repeated customer/stool context · three backgrounds</h2><video id="runtime" controls muted playsinline src="godot-runtime-fade.mp4"></video><pre id="receipt"></pre><script>let log=[];let ids=['native','runtime'];for(let id of ids){let v=document.getElementById(id);for(let ev of ['play','timeupdate','ended'])v.addEventListener(ev,()=>{if(ev!=='timeupdate'||v.currentTime>.25&&v.currentTime<.4){log.push({clip:id,event:ev,currentTime:v.currentTime,duration:v.duration,ended:v.ended});document.getElementById('receipt').textContent=JSON.stringify(log,null,2)}})}function replay(){log=[];for(let id of ids){let v=document.getElementById(id);v.currentTime=0;v.play()}}window.playbackEvidence=()=>({log,clips:ids.map(id=>{let v=document.getElementById(id);return{id,currentTime:v.currentTime,duration:v.duration,ended:v.ended,videoWidth:v.videoWidth,videoHeight:v.videoHeight}})});</script>'''
(P/'playback.html').write_text(html)
# Keep caches outside the packet closure.
shutil.rmtree(S/'runtime-godot/.godot',ignore_errors=True)
for p in (S/'runtime-godot').rglob('*'):
 if p.is_file() and p.suffix in ['.import','.uid']:p.unlink()
# No art/recipe changes after this handoff; only later standalone playback proof may be added.
previews={'four-view-sheet':P/'four-view-backgrounds-logical.png','repeated':P/'repeated-registered-runtime.png','native-playback':P/'native-pop-all4.mp4','runtime-fade-playback':P/'godot-runtime-fade.mp4','playback-page':P/'playback.html','runtime-contact':P/'godot-runtime-temporal-contact.png'}
for d in ['N','E','S','W']:previews['pop-'+d]=P/f'whole-canvas-64-{d}.png'
resources={}
for base in [S,O/'candidates']:
 for p in sorted(base.rglob('*')):
  if p.is_file() and '__pycache__'not in p.parts and '.godot'not in p.parts and p.name not in ['delivery.json','delivery.snapshot.json','packet.json']:
   resources[p.relative_to(O).as_posix()]=p.relative_to(O).as_posix()
D={'asset':'coin-pop','round':'round-01','project':'source/round-01.blend','recipeScript':'source/build_round01.py','packagingRecipe':'source/package_round01.py','verificationRecipe':'source/finalize_round01.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/camera.json','assetRecord':'candidates/round-01/asset-record.json','rig':'candidates/round-01/rig.json'},'heroes':{d:f'candidates/round-01/raw/pop-{d}/005.png'for d in ['N','E','S','W']},'rawFrames':index['rawFrames'],'atlases':index['atlases'],'previews':{k:p.relative_to(O).as_posix()for k,p in previews.items()},'resources':resources,'notes':'Native structural validation only. Independent judge approval pending. Whole-canvas native frames are unwarped/unpainted; previews uniformly downscale only. Runtime is actual Godot isolated current renderer fixture, not full game simulation.'}
write(O/'delivery.json',D)
write(C/'resource-hashes.json',{'files':[{'path':p,'sha256':sha(O/p)}for p in resources.values()]})
print(json.dumps({'delivery':str(O/'delivery.json'),'sourceSHA256':sha(S/'round-01.blend'),'checks':checks,'resources':len(resources),'endpointRatios':ratios},indent=2))
