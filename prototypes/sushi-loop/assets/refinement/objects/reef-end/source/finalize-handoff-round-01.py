"""Freeze editor-owned delivery for coordinator sealing; never create a packet."""
from pathlib import Path
import json,hashlib,math,shutil
B=Path(__file__).resolve().parent;O=B.parent;C=O/'candidates/round-01';D=O/'delivery';D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def close(a,b,tol=1e-5):return abs(a-b)<=tol
def angle_close(a,b):return abs(math.atan2(math.sin(a-b),math.cos(a-b)))<1e-5
frozen={'brief.json':'685740d1728f1e826dbf5565606e5829b964b6739d0ac599999e2a44c130090f','inputs/root-native-contract.json':'8d0366e2299c9ebc4a01cf93dcaeafa2a09086ff27ed606443762506a185269f','inputs/root-preparation-reconciliation-v1.json':'9c2d9eab422d94c349ba08bf27bf9f27ca63e5723e1b431c7828e44c432364b8','source/initial-observations.json':'b0df6ff709adaa58a7db6f2a86bb8fc841e948092d6cf91a745aa99327f96fe5'}
for p,h in frozen.items():assert sha(O/p)==h,(p,'frozen bytes changed')
assert not (C/'packet.json').exists(),'Editor must not seal a packet'
assert not (D/'round-01.json').exists(),'Immutable handoff already exists'

bindings=[]
for asset,file,packet,review,heroes in [
    ('reef-middle',B/'resources/canonical-middle02.blend',B/'resources/approval/reef-middle-packet.json',B/'resources/approval/reef-middle-review.json',B/'resources/heroes/reef-middle'),
    ('reef-edge',B/'resources/approved-edge01.blend',B/'resources/approval/reef-edge-packet.json',B/'resources/approval/reef-edge-review.json',B/'resources/heroes/reef-edge'),
    ('reef-corner',B/'resources/corner-binding/round-01.blend',B/'resources/corner-binding/packet.json',B/'resources/corner-binding/review.json',B/'resources/corner-binding'),
]:
    p=read(packet);r=read(review);source_match=sha(file)==p['files']['candidateProject']['sha256'];review_binding=r.get('candidatePacketSHA256')==sha(packet);approved=r.get('verdict',r.get('decision'))=='approve';hero_records=[]
    for d,v in p['candidateRenders'].items():hero_records.append({'direction':d,'path':str((heroes/(d+'.png')).relative_to(O)),'sha256':sha(heroes/(d+'.png')),'matchesExactPacket':sha(heroes/(d+'.png'))==v['sha256']})
    row={'asset':asset,'project':str(file.relative_to(O)),'projectSHA256':sha(file),'projectMatchesApprovedPacket':source_match,'packet':str(packet.relative_to(O)),'packetSHA256':sha(packet),'review':str(review.relative_to(O)),'reviewSHA256':sha(review),'reviewBoundToExactPacket':review_binding,'independentVerdict':r.get('verdict',r.get('decision')),'approved':approved,'heroes':hero_records}
    assert source_match and review_binding and approved and all(v['matchesExactPacket'] for v in hero_records),row
    bindings.append(row)
write(C/'companion-bindings-verified.json',{'scope':'Exact source and hero approval bindings for context only. No family-wide approval inference. Corner resolved through frozen root reconciliation; original plan pending source text is retained as history.','bindings':bindings})

plan=read(B/'resources/frozen/assembly-evidence-plan.json');captures=read(C/'capture-measurements.json');native_rows=[]
for context in captures['contexts']:
    expected=plan['all4AuthoredPositions'][context['direction']][context['kind']];actual=context['roots'];assert len(expected)==len(actual)
    checks=[]
    for wanted,got in zip(expected,actual):
        matrix=got['actualRootMatrix'];check=got['asset']==wanted['object'].removeprefix('reef-') and all(close(matrix[i][3],wanted['worldRoot'][i]) for i in range(3)) and angle_close(got['rootRotationZ'],wanted['angle']);checks.append(check)
    camera=context['camera'];cal=camera['calibration'];camera_check=camera['frame']==plan['assemblyCamera']['logicalFrame'] and camera['nativeFrame']==plan['assemblyCamera']['nativePixels'] and all(close(cal['root'][i],plan['assemblyCamera']['nativeRootForEnd'][i],1e-3) for i in range(2));assert all(checks) and camera_check
    native_rows.append({'kind':context['kind'],'direction':context['direction'],'actualRootsMatchFrozenPlan':all(checks),'actualRegisteredCameraMatchesFrozenPlan':camera_check,'path':context['path']})
consumer_rows=[]
for backend in ['full-chromium','headless-shell']:
    report=read(C/f'consumer/{backend}-results.json')
    for row in report['records']:
        expected=plan['all4AuthoredPositions'][row['d']][row['kind']];assert len(expected)==len(row['placements'])
        for wanted,got in zip(expected,row['placements']):
            assert got['object']==wanted['object'].removeprefix('reef-') and close(got['x']+.5,wanted['worldRoot'][0]) and close(-(got['y']+.5),wanted['worldRoot'][1]) and got['direction']==wanted['catalogPlacementAtEndGridRoot3.5_3.5']['direction']
        assert report['helperHashes']['world-sprite-raster.js']=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
        assert report['helperHashes']['sprite-layout.js']=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
    consumer_rows.append({'backend':backend,'cases':len(report['records']),'plannedActualRootsAndProperDirectionMappings':True,'exactConsumerHelperHashes':True,'actualVersion':report['browserVersion']})
write(C/'fixture-plan-reconciliation.json',{'native':native_rows,'consumer':consumer_rows,'portGrowthOrReflection':False,'planPendingCornerResolution':'Root native contract approvedCorner and exact bound corner01 supersede only the obsolete source placeholder; authored roots/orientations are unchanged.'})

coverage=read(C/'preview-coverage-map.json');mapped={path for preview in coverage['previews'] for tile in preview['tiles'] for path in tile.get('sources',[]) if '/actual-css-' in path}
required={str(p.relative_to(O)) for p in (C/'consumer').rglob('actual-css-*.png')};assert len(required)==768 and required<=mapped,(len(required),len(mapped))
for r in coverage['previews']:
    assert sha(O/r['preview'])==r['sha256']
validation=read(C/'validation.json');validation['checks'].update({'exactApprovedCompanionSourcesAndHeroes':True,'all8NativeFixtureRootsAndCamerasMatchFrozenPlan':True,'all256ActualConsumerFixtureMappingsMatchFrozenPlan':True,'all768CSSCasesMappedToFiniteContactPreviewCoverage':True});validation['allChecksPassed']=all(validation['checks'].values());assert validation['allChecksPassed'];write(C/'validation.json',validation)
write(C/'handoff-scope.json',{'asset':'reef-end','round':'round-01','frozenInputSHA256':frozen,'sourceSHA256':sha(B/'round-01.blend'),'status':'Immutable editor handoff; coordinator packet seal and original independent judge pending','noEditorApproval':True,'explorationsExcluded':'candidates/explorations and the now-empty source/explorations directory are not members of this used dependency closure. Rejected initial original-matrix records remain included and explicitly invalid; no historical evidence has been rewritten.','browserEvidence':'768 actual CSS screenshots,256 transparent pairs,256 comparison-only extent outputs,16 zero-visible-discard/exact-integer-restoration controls. Actual finite-light/context RGB and contour residuals remain unchanged.','productionAndGitAndDeviceChanged':False})

# Exact native source closure and actual required evidence only. Exploratory
# drafts are retained outside these traversed directories, never promoted.
files=[]
for folder in [B,C]:
    for p in sorted(folder.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or 'explorations' in p.parts or p.name in ['editor-manifest.json','finalization-run.log']:continue
        assert p.stat().st_size<100_000_000,p
        files.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'asset':'reef-end','round':'round-01','pathBase':'object-root','scope':'Minimal private actual-used native/inspection/capture/browser/reference resources and complete required evidence. Root packet and judge review are excluded; editor issues neither.','files':files,'fileCount':len(files),'totalBytes':sum(v['bytes'] for v in files),'largestFileBytes':max(v['bytes'] for v in files)}
write(C/'editor-manifest.json',manifest)
previews=read(B/'preview-index.json')['previews'];heroes={d:f'candidates/round-01/frames/static/{d}/000.png' for d in 'NESW'}
delivery={'asset':'reef-end','round':'round-01','pathBase':'object-root','project':'source/round-01.blend','recipeScript':'source/reproduce-round-01.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':heroes,'previews':previews,'rawFrames':[{'clip':'static','direction':d,'index':0,'path':p} for d,p in heroes.items()],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-01/native/static/{d}/000.png'} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-01/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW'],'resources':[{'path':v['path'],'sha256':v['sha256']} for v in files]+[{'path':'candidates/round-01/editor-manifest.json','sha256':sha(C/'editor-manifest.json')}],'editorStatus':'immutable-round01-compatible-delivery-awaiting-root-seal-and-original-judge','approval':False,'notes':'Published sprites are exact native PNGs. All declared previews require original judge inspection under strict coverage. No candidate packet, visual/family/Godot/production approval or Git/device change was made.'}
write(D/'round-01.json',delivery);shutil.copyfile(D/'round-01.json',O/'delivery-round-01.json')
# Delivery aliases are byte-identical and intentionally outside their own
# manifest to avoid recursive hashes. All source and evidence resources bound.
assert sha(D/'round-01.json')==sha(O/'delivery-round-01.json')
for row in files:assert sha(O/row['path'])==row['sha256'],row['path']
print(json.dumps({'delivery':'delivery-round-01.json','nestedDelivery':'delivery/round-01.json','deliverySHA256':sha(O/'delivery-round-01.json'),'projectSHA256':sha(B/'round-01.blend'),'manifestSHA256':sha(C/'editor-manifest.json'),'files':len(files),'totalBytes':manifest['totalBytes'],'largestFileBytes':manifest['largestFileBytes'],'previewPaths':len(set(previews.values())),'previewAliases':len(previews),'allTechnicalChecksPassed':validation['allChecksPassed']},indent=2))
