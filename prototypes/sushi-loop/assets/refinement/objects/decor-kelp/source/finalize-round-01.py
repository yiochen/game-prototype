"""Prepare immutable editor delivery. Root owns packet sealing and judge dispatch."""
from pathlib import Path
import json,hashlib,shutil,os,sys,datetime
from PIL import Image,ImageDraw,ImageChops
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01';RES=BASE/'round-01-resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p=Path(p);assert not p.exists(),str(p);p.write_text(json.dumps(d,indent=2)+'\n')
def objrel(p):return str(Path(p).relative_to(OBJ))
def diff(a,b):
    a=Image.open(a).convert('RGBA');b=Image.open(b).convert('RGBA');assert a.size==b.size
    ds=ImageChops.difference(a,b).tobytes();return {'differentChannels':sum(v!=0 for v in ds),'maximumChannelDelta':max(ds)}
cons=OUT/'consumer-v02';modes=['full-chromium','headless-shell'];ids=['phone-detail','thumbnail-control','registered-context']
screens={(m,i):Image.open(cons/f'{m}-{i}.png').convert('RGBA')for m in modes for i in ids}
width=max(im.width for im in screens.values());rowheights=[max(screens[(m,i)].height for m in modes)for i in ids]
sheet=Image.new('RGBA',(width*2,sum(rowheights)+20),'#d8ddd7');dr=ImageDraw.Draw(sheet)
for c,m in enumerate(modes):dr.text((c*width+4,3),m+' actual CSS screenshots, DPR2',fill='black')
y=20
for i,h in zip(ids,rowheights):
    for c,m in enumerate(modes):sheet.paste(screens[(m,i)],(c*width,y))
    y+=h
sheet.save(OUT/'consumer-controls-sheet.png')
consumer_comparisons=[]
for ident in ids:
    for suffix in ['', '-native-canvas']:
        a=cons/f'full-chromium-{ident}{suffix}.png';b=cons/f'headless-shell-{ident}{suffix}.png'
        consumer_comparisons.append({'fixture':ident,'layer':'native-canvas' if suffix else 'actual CSS screenshot',**diff(a,b),'fullChromiumSHA256':sha(a),'headlessShellSHA256':sha(b)})
same_previous=[]
for f in cons.glob('*.png'):
    old=OUT/'consumer'/f.name
    if old.exists():same_previous.append({'portable':objrel(f),'initial':objrel(old),**diff(f,old)})
write(OUT/'consumer-comparisons.json',{'actualVersions':'Both153.0.8010.12','comparisons':consumer_comparisons,'initialCanonicalVersusFinalPrivateModuleControls':same_previous,'layers':'Canvas native integer composition and filtered whole-canvas CSS screenshots are measured separately. Native canvas agrees with independently composed common-phase oracle; CSS differences are recorded honestly, never repaired.'})

replay=Path('/tmp/decor-kelp-round01-replay-20261022');rp=OUT/'replay-smoke';rp.mkdir()
replays=[]
for d in ['S','E']:
    a=replay/'candidates/round-01/lookdev-v02/native/idle'/d/'000.png';b=OUT/'native/idle'/d/'000.png';dst=rp/f'{d}-000.png';shutil.copy2(a,dst)
    replays.append({'direction':d,'nativeFrame':1,'savedReplayPath':objrel(dst),'submittedPath':objrel(b),'replaySHA256':sha(dst),'submittedSHA256':sha(b),**diff(a,b)})
shutil.copy2(replay/'candidates/round-01/lookdev-v02/native-validation.json',rp/'native-validation.json')
write(rp/'comparison.json',{'sourceSHA256':sha(BASE/'round-01.blend'),'copiedSourceSHA256':sha(replay/'source/round-01.blend'),'method':'Cold background open of exact saved source copied into independent empty temp folder; only private frozen adapter and actual saved source needed. Two existing S/E frame1 smoke captures, no additional matrix expansion.','blenderExecutable':'/opt/homebrew/bin/blender','blenderVersion':'5.2.2 LTS','frames':replays})

n=json.loads((OUT/'native-validation.json').read_text());pub=json.loads((OUT/'publication-proof.json').read_text());consumer=json.loads((cons/'results.json').read_text());fd=json.loads((OUT/'frame-delivery.json').read_text())
records=n['captureRecords'];source_sha=sha(BASE/'round-01.blend');cam=n['nativeCamera'];sourcecam=json.loads((OBJ/'reviews/preparation-v1/evidence/registered-camera-replay.json').read_text())
checks={
    'all52NativePhases':len(records)==52,
    'all48UniqueFramesAndAtlases':len(fd['rawFrames'])==48 and len(fd['nativeRawFrames'])==48 and len(fd['atlases'])==4,
    'sourceHashMeasuredForEveryRender':all(r['sourceSHA256']==source_sha for r in records),
    'unadaptedSweptEnvelope':all(-.500001<=r['unadaptedEnvelope'][i][0]<=r['unadaptedEnvelope'][i][1]<=.500001 for r in records for i in [0,1]) and all(-.000001<=r['unadaptedEnvelope'][2][0] and r['unadaptedEnvelope'][2][1]<=2.120001 for r in records),
    'allFiniteRootAndForkCapsEmbedded':all(c['allEmbedded']for r in records for c in r['finiteContacts']),
    'actualFiniteGroundFaces':bool(n['groundSupport']['actualFiniteBottomFaces']),
    'exactHistoricalAdapterWithinFloatTolerance':n['lawMaximumError']<=1e-6,
    'evaluatedGeometryMatchesPostAdapter':n['evaluationMaximumError']==0,
    'authoringCoordinatesExactlyRestored':n['restorationMaximumError']==0,
    'physicalClosingPoseExact':all(c['maxWorldVertexDelta']==0 for c in n['closure']),
    'cameraMatrixSourceExact':cam['camera']['worldMatrix']==sourcecam['camera']['worldMatrix'],
    'cameraProjectionSourceExact':cam['camera']['projectionMatrix']==sourcecam['camera']['projectionMatrix'],
    'sourceFloatRootPreserved':cam['calibration']['root']==sourcecam['calibration']['root'],
    'publishedRootWithinExistingTolerance':max(abs(v/2-a)for v,a in zip(cam['calibration']['root'],[192,768]))<=.001,
    'nativeSourceReplayExact':all(x['differentChannels']==0 for x in replays),
    'twoActualChromium153Modes':len(consumer['results'])==2 and all(r['version'].startswith('153.')and r['viewport']=={'width':390,'height':844}and r['deviceScaleFactor']==2 and bool(r['actualBrowserProcesses'])for r in consumer['results']),
    'nearestRestoredAfterResizeAndNativeOracleExact':all(f['imageSmoothingEnabled']is False and f['oracleDifferentChannels']==0 for r in consumer['results']for f in r['fixtures']),
    'exact12fpsLosslessFourPlaybacks':len(pub['playbacks'])==4 and all(p['frameDelay']==[1,12]and p['decodedFramesExactPublishedBytes']for p in pub['playbacks']),
    'noSharedMeshAdapterOrRuntimeModifierAmbiguity':n['noSharedMeshData']and n['noRuntimeModifiersOrShapeKeys'],
}
static=[]
for direction in ['N','E','S','W']:
    ds=[r for r in records if r['direction']==direction];m0=ds[0]['objectWorldMatrices'];names=[name for name in m0 if 'cobalt' in name]
    static.append({'direction':direction,'fixedRootAndStoneMatrices':all(r['rootMatrix']==ds[0]['rootMatrix']and all(r['objectWorldMatrices'][name]==m0[name]for name in names)for r in ds),'stationaryStoneOwners':names})
checks['fixedRootAndBlueBaseThroughEveryPhase']=all(x['fixedRootAndStoneMatrices']for x in static)
assert all(checks.values()),json.dumps(checks)
write(OUT/'validation.json',{'asset':'decor-kelp','round':'round-01','allChecksPassed':True,'scope':'Technical source/capture/physical/temporal/consumer checks only. No editor visual approval. Original independent judge decides fixed visible outcomes.','checks':checks,'nativeValidation':'candidates/round-01/native-validation.json','sourceSHA256':source_sha,'frozenBriefSHA256':sha(OBJ/'brief.json'),'frozenContractSHA256':sha(OBJ/'inputs/root-native-contract.json'),'initialSHA256':sha(BASE/'initial-observations.json'),'lighting':n['renderRecipe'],'physicalSummary':{'samples':52,'interfaces':sum(len(r['finiteContacts'])for r in records),'finiteCapPoints':sum(c['testedPoints']for r in records for c in r['finiteContacts']),'sweptMinimum':[min(r['unadaptedEnvelope'][i][0]for r in records)for i in range(3)],'sweptMaximum':[max(r['unadaptedEnvelope'][i][1]for r in records)for i in range(3)],'groundSupport':n['groundSupport'],'stationaryBlueBase':static},'captureSummary':{'lawMaximumError':n['lawMaximumError'],'evaluatedPostAdapterError':n['evaluationMaximumError'],'restorationError':n['restorationMaximumError'],'nativeCamera':'candidates/round-01/native-camera.json','publishedCamera':'candidates/round-01/published-camera.json','closurePixels':pub['closurePixels'],'closureWorld':n['closure']},'consumerResults':'candidates/round-01/consumer-v02/results.json','consumerComparisons':'candidates/round-01/consumer-comparisons.json','portableClosureProof':['candidates/round-01/portable-python-smoke.json','candidates/round-01/portable-node-smoke.json','candidates/round-01/replay-smoke/comparison.json'],'publicationProof':'candidates/round-01/publication-proof.json','resourceManifest':'candidates/round-01/resource-manifest.json','limitations':['Fixed target remains an aesthetic reference, not a registration proof.','Actual4x source float root error1.4534e-3 is retained and scales to published2x0.7267e-3 within existing helper tolerance; no nudge.','Ground individual face area is not a union-area claim; finite actual solid contacts are tested directly.','Motion playback is lossless RGBA APNG with exact delay1/12, not GIF rounded timing.']})

previews={
    'four-view-sheet':'four-view-sheet.png','native-four-view-sheet':'native-four-view-sheet.png',
    'phone':'consumer-v02/full-chromium-phone-detail.png','repeated':'repeated.png',
    'logical-light-gray-dark':'logical-backgrounds.png','closure':'closure-sheet.png','actual-consumer-controls':'consumer-controls-sheet.png',
    **{'idle-'+d:'idle-'+d+'.png'for d in ['N','E','S','W']},
    **{'all-phases-'+d:'phases-'+d+'.png'for d in ['N','E','S','W']},
}
write(OUT/'review-inspection-guide.json',{'purpose':'Coverage map, not an editor verdict. Original judge must actually inspect every declared hero/preview/playback.','heroes':{d:'frames/idle/'+d+'/000.png'for d in ['N','E','S','W']},'declaredPreviews':previews,'all48UniquePhaseCoverage':{d:{'sheet':'phases-'+d+'.png','order':'row-major6x2 indexed0..11, each full registered frame uniformly resized to logical192x480','actualPlayback':'idle-'+d+'.png','playbackFormat':'APNG,12 exact published2x decoded frames,1/12second each'}for d in ['N','E','S','W']},'all4Closures':'closure-sheet.png labels compare last unique/first/closure13; full native closure files retained; technical world/pixel differences in validation/publication proof.','consumerCoverage':'consumer-controls-sheet.png includes full unscaled actual CSS screenshots of phone S0/.570, tiny E6/.099, and actual yellow submarine/eel context S0/.570 in both required modes. Native canvas files separately retained.','nativeReplayAliases':replays,'draftEvidence':'lookdev and lookdev-v02 are earlier retained tests; lookdev-v03 renders exact same final source and may be hash-mapped to final S/E0. They are not additional declared candidate previews.','ownership':'Editor has not read or changed future judge review and has not self-approved. Root seals exact delivery then original independent judge reviews it.'})

# Explicit object-relative manifest, no hash cycles with delivery/handoff/packet.
files=[]
for folder in [BASE,OUT]:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and '__pycache__'not in p.parts:
            assert p.stat().st_size<100_000_000,str(p)
            files.append({'path':objrel(p),'sha256':sha(p),'bytes':p.stat().st_size})
write(OUT/'resource-manifest.json',{'asset':'decor-kelp','round':'round-01','pathBase':'object-root','method':'Actual used private native helper/camera/catalog/context, imported Pillow native closure and CommonJS Playwright closure, exact source/recipes and all meaningful immutable captures/evidence. Trusted executables, browser binaries and stdlib/system frameworks external; no copied application trees. Preserved lookdev evidence is identified separately from delivered source.','files':files})
source_resources=[{'path':objrel(p),'sha256':sha(p),'pathBase':'object-root'}for p in sorted(BASE.rglob('*'))if p.is_file()and'__pycache__'not in p.parts]
delivery={'asset':'decor-kelp','round':'round-01','project':'source/round-01.blend','recipeScript':'source/reproduce-round-01.py','constructionRecipe':'source/build-round-01.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':{d:'candidates/round-01/frames/idle/'+d+'/000.png'for d in ['N','E','S','W']},'previews':{k:'candidates/round-01/'+v for k,v in previews.items()},'rawFrames':fd['rawFrames'],'nativeRawFrames':fd['nativeRawFrames'],'atlases':fd['atlases'],'resources':source_resources+[{'path':'candidates/round-01/resource-manifest.json','sha256':sha(OUT/'resource-manifest.json'),'pathBase':'object-root'}],'notes':'Immutable editor delivery. Root owns unchanged packet seal; original independent judge owns visual verdict. No production/Git/deploy edits. Exact measured camera and historical adapter law; uniform whole native4x LANCZOS reduction to2x;12 unique phases with separate13 closure; lossless exact12fps APNG playbacks.'}
write(OUT/'delivery.json',delivery)
write(OUT/'editor-handoff.json',{'asset':'decor-kelp','round':'round-01','stage':'immutable editor delivery; STOP; awaiting root packet seal and original independent judge','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':{'path':'source/round-01.blend','sha256':source_sha},'delivery':{'path':'candidates/round-01/delivery.json','sha256':sha(OUT/'delivery.json')},'resourceManifest':{'path':'candidates/round-01/resource-manifest.json','sha256':sha(OUT/'resource-manifest.json')},'validation':{'path':'candidates/round-01/validation.json','sha256':sha(OUT/'validation.json')},'sourceRecipe':{'path':'source/reproduce-round-01.py','sha256':sha(BASE/'reproduce-round-01.py')},'artNotes':'Seven curved twisting lens-section primary fronds, five inherited fork children and nine irregular rounded cobalt stones. Native grouped object-rotation sway, no runtime modifiers or shape-key adapter bypass. One shared symmetric soft rig and colored material edge response.','technicalChecks':checks,'packetOwner':'root coordinator','visualVerdict':'pending original independent judge; no editor selfapproval'})
for folder in [BASE,OUT]:
    for p in folder.rglob('*'):
        if p.is_file()and'__pycache__'not in p.parts:os.chmod(p,0o444)
print(json.dumps(json.loads((OUT/'editor-handoff.json').read_text()),indent=2))
