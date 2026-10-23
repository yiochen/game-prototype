from pathlib import Path
import json,hashlib,sys,subprocess
from datetime import datetime,timezone
import PIL
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01';G=O.parents[3];REPO=G.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
packetsha='f4d3f66a3094db075819e4927ead8baa0196ae7cca6726d831b8568692707bf3';sourcesha='1efc24a21f1ade2accdcca93446f2c4d9743df4437ad2e927c1c239849003aa4'
assert sha(C/'packet.json')==packetsha;assert sha(O/'source/round-01.blend')==sourcesha
assert sha(O/'brief.json')=='23c4a76e6828750d4fecae535ac4320da074d4beac61beeb5e21a5f118644162'
assert sha(O/'inputs/root-native-contract.json')=='6c36db3b63b69f2b4028d3132210e5b9aa6f795e0cca6146af65d171a4a15fa2'
assert sha(O/'inputs/root-preparation-reconciliation-v1.json')=='d8d258600a4eb91a59669472ef29f8e8baa941a3faa453d95a765384012e858b'
assert sha(O/'reviews/criteria.json')=='fb9c07a40cedb50c4d75ae1887ac8a9dd51f25799c0f99761e3ee3adcdb4137a'
summary=json.loads((H/'technical-summary.json').read_text());coverage=json.loads((H/'visual-coverage.json').read_text());assert len(coverage['requiredPacketPaths'])==11
assert summary['all48RawAndEvaluatedNativeBoundsExactVersusPacket'] and summary['allphaseBudgetViolations']==[]
assert summary['all48PublishedFullCanvasLanczosExact'] and summary['all48OriginalAtlasCellsExact'] and summary['all48PublishedTransparentBorder']
assert summary['browserReproduction']['canvasExact']==96 and summary['browserReproduction']['CSSExact']==12
assert all(r['orderErrors']==[] and len(r['wrapTimesMs'])>=2 and r['elapsedMs']>=2200 for r in summary['browserReproduction']['actualPlayback'])
assert all(v['evaluatedGeometryExactFirstToClosing'] and v['maxLocalMatrixDelta']==0 for v in summary['firstToNativeClosingFrame13'].values())
assert not list(H.rglob('__pycache__'))
# Stop before running gates: this manifest points only to evidence, never review/gates/postseal.
commands=json.loads((H/'commands.json').read_text());commands['executed'].append({'argv':[sys.executable,str(H/'measure-residuals-and-support.py')],'log':'reviews/round-01-evidence/measure-residuals-and-support.log','environment':{'PYTHONDONTWRITEBYTECODE':'1'}});commands['executed'].append({'argv':['node',str(H/'browser-executables-v2.mjs')],'environment':{'DEBUG':'pw:browser'},'log':'reviews/round-01-evidence/browser-executables-v2.log'});commands['additionalExecutedAnalysis']['browserExecutableProbe']='Original CDPcommandline probe failed because--enable-automation absent; exact actual failure code/log retained. V2same-options browserDEBUGlaunchlogs truthfully establish fullChromium1243 and headless-shell1243 executable paths; both actual153.0.8010.12. No extra media.';(H/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(H/'runtime.json').write_text(json.dumps({'pythonExecutable':sys.executable,'pythonVersion':sys.version,'PillowVersion':PIL.__version__,'PillowImageModule':str(Path(Image.__file__)),'PillowImageModuleSHA256':sha(Path(Image.__file__)),'nodeVersion':subprocess.run(['node','--version'],capture_output=True,text=True).stdout.strip(),'blenderVersion':'5.2.2LTS actual native replay log','browserExecutableProof':'browser-executables.json and exactDEBUGlaunchlog; both153.0.8010.12','externalToolchainPolicy':'Application/runtime trees remain external. Frozen actual-used review scripts, native source copy, browser helpers, fixture/dependency outputs and exact bound input references form private evidence closure.'},indent=2)+'\n')
refs=set()
for p in H.rglob('*'):
 if p.is_file() and not p.name.startswith('gate-') and p.name not in ['supplemental-manifest.json','gates.json','postseal.json']:refs.add(p)
# Actual read/inspected frozen files; exclude editor opinions/rationale. Packet-wide byteverification is separately recorded.
for rel in ['packet.json','validation.json','native-validation.json','native-scene-record.json','native-checks.json','native-topology.json','phase-cell-map.json','review-coverage-map.json','consumer-comparisons.json','browser/manifest.json']:
 refs.add(C/rel)
for name in ['N','E','S','W']:
 refs.add(C/f'heroes/{name}.png');refs.add(C/f'previews/ambient-{name}.png');refs.add(C/f'sheets/phase-{name}.png');refs.add(C/f'atlases/ambient-{name}.png')
 for i in range(12):refs.add(C/f'native/ambient/{name}/{i:03}.png');refs.add(C/f'frames/ambient/{name}/{i:03}.png')
for rel in ['previews/four-view-sheet.png','previews/phone.png','previews/motion.png','sheets/enlarged-foliage-S-frame00.png','sheets/playback-full-chromium.png','sheets/playback-full-shell.png']:refs.add(C/rel)
for mode in ['chromium','shell']:
 for size in ['logical','phone']:
  for bg in ['light','gray','dark']:refs.add(C/f'browser/{mode}/{size}-{bg}.png')
 refs.add(C/f'browser/{mode}/actual-playback.json');refs.update((C/f'browser/{mode}/video').glob('*.webm'))
 for name in 'NESW':
  for i in range(12):refs.add(C/f'browser/{mode}/frames/{name}/{i:03}.png')
for rel in ['brief.json','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json','inputs/catalog-object.json','reviews/initial.json','reviews/criteria.json','source/round-01.blend','source/capture-round-01.py','source/browser/consumer.html','source/browser/capture-consumer.mjs','source/browser/resources/catalog-object.json','source/browser/resources/world-sprite-raster.js','source/browser/resources/sprite-layout.js','reviews/preparation-v1/hash-manifest.json','reviews/preparation-v1/seal.json','reviews/preparation-v1/camera-measured.json','reviews/preparation-v1/resources/warm-soft-reference.png']:
 refs.add(O/rel)
files=[]
for p in sorted(refs):
 assert p.is_file(),p;assert p.resolve().is_relative_to(O.resolve()),p;assert p.stat().st_size<100000000,p
 files.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'asset':'safe-passage','round':'round-01','candidatePacketSHA256':packetsha,'sourceSHA256':sourcesha,'pathBase':'object root: prototypes/sushi-loop/assets/refinement/objects/safe-passage','files':files,'fileCount':len(files),'totalBytes':sum(r['bytes'] for r in files),'coverage':'All4heroes and7exactdeclaredpreviews, all48 native/published phasecells/APNGcontent, independently opened enabled unsaved exactsource/allphase geometry/contact/attachment/topology/camera/root/actions, actual two-mode consumer replay/fullvideo/log coverage. See visual-coverage.json and technical-summary.json.','acyclicExclusions':['reviews/round-01.json','reviews/round-01-evidence/supplemental-manifest.json','reviews/round-01-evidence/gates.json','reviews/round-01-evidence/gate-*','reviews/round-01-evidence/postseal.json'],'independence':'No editor selfrating/rationale or otherobject aesthetic judgment used. Packet-byte checks do not count as aesthetic inspection.'}
mp=H/'supplemental-manifest.json';assert not mp.exists();mp.write_text(json.dumps(manifest,indent=2)+'\n')
review={
 'asset':'safe-passage','round':'round-01','verdict':'approve','candidatePacketSHA256':packetsha,'candidateProjectSHA256':sourcesha,
 'frozenInputs':{'briefSHA256':sha(O/'brief.json'),'nativeContractSHA256':sha(O/'inputs/root-native-contract.json'),'reconciliationSHA256':sha(O/'inputs/root-preparation-reconciliation-v1.json'),'independentCriteriaSHA256':sha(O/'reviews/criteria.json'),'originalPreparationManifestSHA256':sha(O/'reviews/preparation-v1/hash-manifest.json')},
 'inspectedFiles':coverage['requiredPacketPaths'],
 'inspectionCoverage':{'all4Heroes':'Each exacthero file directly opened; exactframe0 bytealiases verified.','all7Previews':'Exactfourviewsheet,phone,motion and all4ambientAPNG files directly opened. All12frames perambient APNG fullydecoded/exactmapped to inspected fullframe phase sheets; motion all12decoded frames actually viewed via two fullresolution6phase sheets and all48registeredcells match source exactly. Phone exactbytealias to submitted Chromiumgrayphone, reproduced independently.','all48PhaseCells':'All4phase sheets directlyviewed, every wholeframe cell independently verified exact source-to-logical presentation; enlarged nativeattachments/stonefaces at0/3/6/9 includephase3maxheight, guideedges inspectedS/E. Not just filehash coverage.','currentConsumer':'Both actualfullChromium andheadless-shell153.0.8010.12, actualexecutables/options recorded. All96nativegridcanvasframes and12logical/phone/lightgraydarkscreenshots independently reproduced exactly. Viewed representative fullbrowserimages/background sheets and actualpacket full3.44s12fpscompositorfilmstrips plus detailedvideo parts; separate actual rAF/cadence/order audits>=2.35s/twowraps. No APNGdefaultframe surrogate.','evidenceLimits':'Some overview/detailfilmstrips were viewerdownsampled; nativecaptures, exactpixelmapping, intended-sizeimages and technicalmeasurements retain original resolution. Utilityfixture only; no fullReact/Godot/device approval.'},
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':9},
 'scoreBasis':'Comparative observations against the original and fixedtarget under fullfrozencriteria, not a numeric approval threshold.',
 'observations':[
  'Both blue stone masses are deliberately shaped, separated and softly edged. Broader clean blue planes and rounded native edge transitions replace the original austere coarse triangles; the lower planes remain visiblyblue onlight,gray anddark, includingE/W.',
  'The crown and smaller shoot use thick layered greenleafvolumes rather than narrow segmented rods. Their lime/yellowgreen highlights and darker inner faces read as a coherent softcartoon plant inall4facings; the purposeful smallgrowth on the secondstone is an allowed modeling improvement.',
  'Three separate cyan marks retain the lane-facing role and transparent spacing. Nativebody/inset/bevel construction yields controlled bright edges and stable shallow thickness; no copied imagegenhalo or noisy specular artifact was observed.',
  'At the scoped logical and uniform.5phone scale, two blue stones, meaningful greenfoliage andall3marks remain recognizable. E/W foliage stays legible rather than becoming the original sparse upright sticks. Large clean detail carries the form without tiny visualnoise.',
  'The ambient leafmotion is gentle and rooted, with stable stones/marks/root. Completephase visualcoverage, both actualplaybacks and sourcegeometry show coherent overlap and no material frame11->0 pop. Nativeclosing13 equalsfirst; publishedframe12 was correctlynotforced equalfirst.',
  'No material clipping, navyblackdeadspot, unwantedgroundplane, directionalgroundshadow, detachedleafbase, zfight, brokennormal/exposedmechanical seam or alpha/RGBhalo was found in the requiredcoverage. Shared warmoverhead and equalcardinal fills provide coherent allviewsoftlight without a preferredhorizontal key.'
 ],
 'criteriaResults':{'shapeVolume':'met','color':'met','lightingHighlights':'met','materialDetail':'met','intendedSizeReadability':'met','artifactFree':'met','motion':'met;12slots12fps1sloop,existingminimumUniqueFrames6 retained;actual12unique descriptive'},
 'blockers':[],
 'remainingDifferences':[
  'The nativefinish is more restrained and matte than the target\'s strong ivoryglints and gemlikestreaks. Broad soft volume remains clear and consistent with the chosen style; exactgloss/streaks are not locks.',
  'Foliage is organized into a deliberate crown plus smaller shoot, with a brighterlime range and fewer pebblelike details than the singleviewtarget. These native modeling choices preserve identity, readability and frozenfunctionalbudget; exacttargetoutline/partcounts/unseenviews are not required.'
 ],
 'technicalEvidence':{
  'independentSource':'Opened exactsource unsaved inbackgroundBlender5.2.2LTS, enabledcollection/objects/depsgraph, measured/rendered all48facing/phases without model/action/camera/light/material changes. SourceSHA unchanged; owned18closedmanifoldpositivenativevolumes/propertransforms, no externalimages/targetcard.',
  'registration':'ActualORTHO1.5/HORIZONTAL,55.0079798degree camera, fixedworld/projectionmatrices and aspect1.2206555605:1 match frozencontract; rootpixel384,992/native768x1408, logical192x352/root96,248, properS0/E90/N180/W-90. Published2x/fullcanvasLanczos and alloriginal6x2atlascells exact, alphaedges0; nofit/crop/warp/nudge/recolor/repair.',
  'geometry':'All48 independently measured rawauthored/evaluatedmodifierbounds exactly match packet and fit canonicalXY±.5/Z[-.05,.53]/tol1e-5. Raw allphase S bounds[-.44494277,-.34655085,-.04700001]..[.328999996,.32524255,.50420731]; evaluated[-.44292098,-.34165579,-.03637071]..[.328999996,.32144880,.49716017]. Maxima are clearancebudget, not requiredfill. Bothstones havefiniteZ0 sections everyphase; intentional embedding accepted, nofloorlaw.',
  'attachmentsTopology':'All480evaluated leaf/phase attachment checks have atleast31evaluated leafvertices inside assignedstone, fixedpivots alsoinside. Actual overlapping nativevolumes plus visible inspection establish rootedfoliage; propertylabels alone were not used. Stable component evaluatedgeometry and root unchanged allphases, nativeframe13geometry/localcontrols equalframe1 inall4.',
  'motionConsumer':'Actual10nativeleafactions inspected;12phases12fps1sloop and existingminimum6 retained. Bothindependentactualconsumer runs showtwowraps over2.35s/noorder/page/request errors. Correctcurrent099/570helpers/root/rects/order/sourceScale; independent96canvasframes and12CSSscreenshots exact versus submitted, nearestaftercommoncanvasresize then wholeCSSfilter.',
  'honestResiduals':'Independentnative recapture differs in1–16pixels/frame, alphaexact,maxRGB15 beforecompositing; after display onlight/gray/dark maxnativeRGB1 andpublishedRGB2 with publishedmean<.000012/255. SourceRGBA/reduction/atlas outputs themselves were exactchecked and neverrepaired. Rendererrepeatability, lowalphaRGBencoding and intermodeCSSraster differences remain boundedreports, not blanket defectwaivers.',
  'scope':'Nonblockingpassage scenery only; noports, physicalaccess, literal3unitgap, modularseam/family or extra3x3fixture invented. All13annotated2Deffects excluded. No production/Godot/device/publish or broaderfamily approval.'
 },
 'supplementalEvidence':{'path':str(mp.relative_to(O)),'sha256':sha(mp)},
 'approvalScope':'Exactpacket/source/render/preview bytes for safe-passage round-01 only. Any art/source change requires a new review. No broader integration, production or publishing permission granted.'
}
rp=O/'reviews/round-01.json';assert not rp.exists();rp.write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'verdict':review['verdict'],'reviewSHA256':sha(rp),'supplementalManifestSHA256':sha(mp),'supplementalFiles':len(files),'sourceSHA256':sourcesha},indent=2))
