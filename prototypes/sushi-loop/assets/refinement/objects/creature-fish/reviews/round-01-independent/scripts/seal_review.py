"""Independent evidence -> review -> unchanged gates -> postseal; no candidate writes."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, platform, os
sys.dont_write_bytecode = True
P=Path(__file__).resolve().parents[1]; O=P.parents[1]; C=O/'candidates/round-01'
RUN=O.parents[1]; ROOT=RUN.parents[3]
SKILL=Path('/Users/yiouchen/.codex/skills/refine-3d-model')
PACKET='5b11c24968df9117ccc35ee5891031a7f08a8eafe6d0d1149aa111c6b3081365'
SOURCE='7e32d44911b1fd044fe7f64ef6033f9cfccd5d0ec1c23fc9a46c4497bbb63ae7'
MANIFEST=P/'supplemental-evidence.json'; REVIEW=O/'reviews/round-01.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def desc(p):return {'path':os.path.relpath(p,O),'sha256':sha(p),'bytes':p.stat().st_size}
def baseline():
    assert sha(C/'packet.json')==PACKET and sha(O/'source/round-01.blend')==SOURCE
    for path,h in [('brief.json','5279940f2703e7c92458c80cd813fe326d4e225313e93980219bb9a3ca230498'),
                   ('inputs/root-native-contract.json','c7a9c1011671a213fdf68364a2a2d067325cb0abab25faef09fe44c87623d064'),
                   ('inputs/root-preparation-reconciliation-v1.json','7db4598aaefc4883c288496f3fea17ce429f1b84481a01d70747483dd9e65589')]:
        assert sha(O/path)==h,(path,sha(O/path))
def evidence():
    assert not MANIFEST.exists() and not REVIEW.exists()
    baseline()
    # Keep only the six whole-frame partitions actually viewed before the more useful fixed-window set.
    rows=read(P/'native-sheet-panel-coverage.json');kept=[]
    for r in rows:
        q=O/r['path']
        if any('/allphase-'+clip+'-logical-' in r['path'] for clip in ['normal','swim']):kept.append(r)
        else:q.unlink()
    write(P/'native-sheet-panel-coverage.json',kept)
    copies=[(ROOT/'AGENTS.md','instructions/workspace-AGENTS.md'),
            (ROOT/'prototypes/sushi-loop/AGENTS.md','instructions/sushi-loop-AGENTS.md'),
            (SKILL/'SKILL.md','instructions/refine-3d-model-SKILL.md'),
            (SKILL/'references/blender-techniques.md','instructions/blender-techniques.md'),
            (O/'prompts/judge.txt','instructions/judge.txt'),
            (RUN/'preparation/creature-fish/judge-round-01-dispatch.txt','instructions/judge-round-01-dispatch.txt'),
            (RUN/'preparation/REVIEW-COVERAGE.txt','instructions/REVIEW-COVERAGE.txt'),
            (RUN/'preparation/PUBLISHER-HANDOFF.txt','instructions/PUBLISHER-HANDOFF.txt'),
            (RUN/'preparation/HEADLESS-BROWSER-CONFIGS.txt','instructions/HEADLESS-BROWSER-CONFIGS.txt'),
            (SKILL/'scripts/candidate_packet.py','gates/candidate_packet.py'),
            (RUN/'tools/audit_directions.py','gates/audit_directions.py'),
            (RUN/'tools/acceptance_contract.py','gates/acceptance_contract.py'),
            (RUN/'tools/seal_object.py','gates/seal_object.py'),
            (RUN/'tools/promote_object.py','gates/promote_object.py')]
    copied=[]
    for src,dst in copies:
        q=P/'resources'/dst;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,q)
        copied.append({'originalPath':str(src),'privateCopy':str(q.relative_to(O)),'sha256':sha(q)})
    write(P/'resource-copy-records.json',copied)
    native=read(P/'independent-native-evidence.json');pub=read(P/'independent-publication-checks.json')
    playback=read(C/'browser-evidence.json');cadence=[]
    rig=read(C/'rig.json')
    for mode in playback['modes']:
        assert mode['errors']==[]
        for r in mode['playback']:
            loop=rig['clips'][r['clip']]['loop'];seq=[]
            for t in r['trace']:
                expected=int(max(0,t['elapsed'])*12)
                expected=expected%12 if loop else min(11,expected)
                assert t['frames']==[expected]*4,(mode['mode'],r['clip'],t)
                if not seq or seq[-1]!=expected:seq.append(expected)
            assert set(seq)==set(range(12))
            assert r['visitedIndices']==list(range(12))
            if loop:assert seq.count(0)>=3
            else:assert seq==list(range(12)) and r['terminal']==[11]*4
            cadence.append({'mode':mode['mode'],'clip':r['clip'],'viewport':r['viewport'],
                            'viewportPixels':r['viewportPixels'],'background':r['bg'],
                            'rafSamples':len(r['trace']),'phaseSequence':seq,'allFourFacingsExpectedAtEveryRAF':True,
                            'video':r['video'],'seconds':r['seconds'],'loop':loop})
    assert len(cadence)==44 and len(native['views'])==528 and len(native['captureRecords'])==44
    assert len(pub['records'])==528 and all(r['wholeCanvasLANCZOSExact'] and r['atlasSlotExact'] and not r['alphaBorderNonzero'] for r in pub['records'])
    envelope={k:{side:[(min if side=='min' else max)(r[k][side][i] for r in native['views']) for i in range(3)]
                 for side in ['min','max']} for k in ['rawAuthoredBounds','evaluatedBounds']}
    for v in envelope.values():
        assert all(v['min'][i]>=-1.02-1e-5 and v['max'][i]<=1.02+1e-5 for i in [0,1])
        assert v['min'][2]>=.02-1e-5 and v['max'][2]<=1.18+1e-5
    assert all(r['editorLedgerMaxBoundResidual']==0 for r in native['views'])
    assert all(a['sameArmature'] and a['normalizedWeights'] for r in native['views'] for a in r['attachments'])
    assert all(r['relativeVertexResidual']==r['boneResidual']==r['objectResidual']==0 for r in native['boundaryControls'])
    replay=read(P/'native-replay-residuals.json')
    write(P/'independent-summary-checks.json',{
        'candidatePacketSHA256':PACKET,'sourceSHA256':SOURCE,'allPhaseGeometry':len(native['views']),
        'envelope':envelope,'editorLedgerMaximumBoundsResidual':0,
        'boneRelativeMatrixMaximaRange':[min(r['maxBoneResponse'] for r in native['responses']),max(r['maxBoneResponse'] for r in native['responses'])],
        'armatureRelativeVertexMaximaRange':[min(r['maxRelativeVertexResponse'] for r in native['responses']),max(r['maxRelativeVertexResponse'] for r in native['responses'])],
        'allAttachmentsSameArmatureAndNormalized':True,'boundaryControls':len(native['boundaryControls']),
        'maximumBoundaryResidual':0,'nativeReplayCount':44,'nativeReplayDecodedExactCount':sum(r['decodedExact'] for r in replay),
        'nativeReplayMaximumMeanAbsoluteRGBAByteError':max(r['maeRGBA'] for r in replay),
        'nativeReplayMaximumIndividualChannelByteError':max(r['maxByte'] for r in replay),
        'wholeCanvasLANCZOSExactCount':528,'atlasSlotExactCount':528,'alphaBordersNonzero':0,
        'independentRAFFormulaChecks':cadence,'decodedCompositorCells':sum(r['decodedFrames'] for r in read(C/'playback-decoded-manifest.json')['records']),
        'scope':'Existing frozen browser playback traces independently checked against floor(elapsed*12), wrapped/clamped by native clip semantics. Pixel replay is bounded44, geometry528; no claim of528 independent source re-renders or bitexact44.'})
    aliases=read(P/'packet-aliases.json');media={r['packetPath']:r for r in aliases}
    compact=read(P/'compact-native-coverage.json');assert sum(len(x['cells']) for x in compact)==528
    decode=read(P/'compact-playback-coverage.json');assert len(decode)==44
    inspection=[]
    for path,a in media.items():
        sheets=[r['path'] for r in compact if r['sourceSheet']==a['objectPath']]
        inspection.append({'packetPath':path,'objectPath':a['objectPath'],'sha256':a['sha256'],
                           'aliases':[{'group':r['group'],'name':r['name']} for r in aliases if r['packetPath']==path],
                           'method':'Complete useful-pixel direct inspection through fixed logical1:1 partitions, with full source-cell/hash coverage' if sheets else 'Direct image inspection of exact declared image',
                           'inspectionPartitions':sheets,'observed':True})
    assert len(inspection)==18 and len(aliases)==51
    write(P/'visual-inspection-coverage.json',{
        'candidatePacketSHA256':PACKET,'declaredAliases':51,'uniqueDeclaredImages':18,'images':inspection,
        'allphaseUsefulCells':528,'nativePartitions':{'path':'reviews/round-01-independent/compact-native-coverage.json','all22PartitionsViewed':True},
        'registrationEvidence':'Full registered hero/four-view/whole-frame normal/swim partitions plus independently measured camera/root/envelope. Fixed windows are inspection-only, never delivered frame crop/fit.',
        'playback':{'path':'reviews/round-01-independent/compact-playback-coverage.json','all44TimelinesViewed':True,'all3692ExistingDecodedCellsRepresented':True,
                    'method':'Existing compositor decode cells in chronological order, four fixed facing windows; all 44 compact images visually read. Whole overview images may be display-resized; native1:1 allphase cells and lossless consumer stills supply detailed and use-size evidence. This does not claim 3692 new scene requirements or newly recorded full video.'},
        'consumerBackgroundContacts':{'path':'reviews/round-01-independent/consumer-contact-panel-coverage.json','all8Viewed':True,'scope':'normal/hook/caught/escape, four views, light/gray/dark, both modes; native allstate and scoped playbacks cover remaining roles'},
        'ownLosslessCompositorDiagnostic':{'path':'reviews/round-01-independent/compositor-diagnostic.json','contactSheetsViewed':4,'rawPNGsRepresented':56,
                                         'scope':'normal/caught phone/light in two modes only. Bounds visible video-startup chroma/codec residuals; sparse PNGs do not replace allstate timeline evidence.'},
        'directEnlargedOwnReplays':['native-replay/caught/E/006.png','native-replay/caught/W/006.png','native-replay/hook/S/006.png','native-replay/caught/N/006.png','native-replay/escape/S/003.png'],
        'enlargedFinding':'Shallow soft body compression bands at caught E strongest bend; coherent surface without tearing, black patches or detached face/fins. Nonblocking at logical and phone. No noisy hard facet pattern.'})
    from PIL import __version__ as pillow
    write(P/'environment.json',{'python':sys.version,'pythonExecutable':sys.executable,'platform':platform.platform(),'pillow':pillow,
                              'blenderExecutable':'/opt/homebrew/bin/blender','blenderVersion':'5.2.2 LTS','blenderBuild':'d13f752e3b9c',
                              'nodeExecutable':shutil.which('node'),'nodeVersion':subprocess.check_output(['node','--version'],text=True).strip(),
                              'browser':'153.0.8010.12','browserLaunches':[{'headless':True,'channel':'chromium'},{'headless':True}],
                              'runtimeEvidence':'Candidate environment.json and source/browser-round01.log contain actual two launch commands/executables; own compositor-diagnostic.json records options/version/DPR. Installed Blender/Node/Playwright/Python runtimes remain prerequisites; no application/runtime trees copied.'})
    (P/'commands.txt').write_text('''Working directory: /Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype
Executed executable/script entry points, with retained output logs. Redirection syntax below is a reproducible invocation description, not a shell-history transcript.
1. /Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 .../reviews/round-01-independent/scripts/prepare_inspection.py > .../prepare-inspection.log
2. /opt/homebrew/bin/blender --background .../source/round-01.blend --python .../reviews/round-01-independent/scripts/native_audit.py > .../native-audit.log
3. Same Pillow runtime: scripts/compact_inspection.py. Output: GLOBAL_NATIVE_WINDOW [92,203,356,398], native22, complete_compositor44, frames3692.
4. Existing replay residuals and diagnostic contact panels were calculated from retained original PNGs using Pillow; exact source/output maps retained. No art mutation.
5. node scripts/compositor_diagnostic.mjs > compositor-diagnostic.log. First server-header ordering failure retained as script/log failed-v1. Corrected server reads before headers; exact same consumer/art, no rebuild. Successful marker COMPOSITOR_DIAGNOSTIC_COMPLETE4.
6. /opt/homebrew/bin/blender --background .../source/round-01.blend --python .../scripts/channel_material_audit.py > channel-material-audit.log. First assertion wrongly required every pose channel to be rotation; saved failed-v1 is retained. Actual pose channels also include location/scale. Corrected diagnostic asserts only rotation channels, records all paths unchanged; successful marker CHANNEL_MATERIAL_AUDIT_COMPLETE11 7.
7. Same Pillow runtime: scripts/seal_review.py evidence; then review; then gates; then postseal. Gate exact argv, return codes, stdout/stderr and unchanged helper hashes retained separately after the review.
All view_image calls were read-only direct media reads. No candidate/source/brief/criteria/target/helper edits, Git, index, live Blender, production, publishing, device or extra-agent actions.
''')
    (P/'README.txt').write_text('''Independent creature-fish BODY round01 review evidence.
The original judge retains the same three ranked outcomes and ROOT frozen contract. Background fish silhouette and all marked2D effects are excluded.
All eighteen declared distinct media receive actual visual coverage with explicit51alias equivalence. The eleven logical sheets cover all528 N/E/S/W phase cells in fixed1:1 useful-pixel windows; verified full-frame camera/root and unchanged native->published->atlas checks establish registration rather than fitting art to an inspection crop.
All44 existing encoded browser playbacks are represented by all3692 already decoded cells and their complete per-RAF traces, both actual Chromium modes at logical/phone and frozen scoped backgrounds. Traces independently match floor(elapsed*12) with loop wrap or one-shot clamp. Two bounded extra clip/mode phone/light lossless PNG sequences diagnose recording chroma drift only. The sparse PNGs are not substituted for full allstate playback. Initial blank video startup and record-final fixture stop are distinguished from native phase behavior. No default-frame APNG drawImage claim is made.
Native source is opened unsaved in background Blender5.2.2, correct owned scene/collection enabled, all528 geometry/pose phases independently measured and44 maximum-relative-motion phases re-rendered. Source replay residuals are sparse and small but not byte-exact; maxRGBA channel13, full-canvas mean<=0.000007289 byte. Independent whole-canvas LANCZOS and original atlas slot matching are exact for all528 published frames. No raster repair.
Minor soft compression bands at strongest caught E bend are seen in enlarged native replay and accepted as nonblocking; no hard facet stripe pattern or use-size face/body failure. Native joints/face/fins remain visibly connected throughout scoped phases. This is visual inspection, not an exhaustive solid-mesh intersection proof.
Minimal closure references immutable existing candidate media rather than duplicating it. Included script/history failures are actual diagnostics, not candidate defects. Installed runtimes are prerequisites. No full app tree, pycache or unseen other-object aesthetics are retained. Each file is below100MB. The two preparation seals remain unchanged and are explicit transitive dependencies.
Acyclic order: supplemental-evidence.json -> reviews/round-01.json -> gates/* -> postseal.json. Supplemental manifest contains no future review, gate output or postseal hashes. Approval applies only to this exact candidate, no publishing or integration authority.
''')
    refs=set()
    for d in ['native','published','atlases','sheets','playback-decoded','consumer-fixture']:
        refs.update(p for p in (C/d).rglob('*') if p.is_file())
    for r in aliases:refs.add(O/r['objectPath'])
    # Actual compositor originals/stills and video files used by existing trace/decode evidence.
    refs.update(p for p in (C/'consumer').rglob('*') if p.is_file())
    for n in ['packet.json','resource-manifest.json','assetRecord.json','browser-evidence.json','browser-mode-and-CSS-residuals.json',
              'consumer-bundle-metafile.json','consumer-module-dependencies.json','consumer-catalog.json','editable-source-audit.json','environment.json',
              'frame-audit.json','geometry-ledger.json','native-camera.json','native-capture-records.json','native-validation.json','validation.json',
              'playback-decoded-manifest.json','publication-records.json','published-camera.json','rig.json','runtime-cadence-audit.json','sheet-coverage.json']:
        refs.add(C/n)
    for n in ['source/round-01.blend','source/capture_round01.py','source/publish_round01.py','source/browser_round01.mjs','source/browser_media_round01.py',
              'source/audit_saved_round01.py','source/fixture_round01.js','source/browser-round01.log','brief.json','reviews/initial.json','reviews/criteria.json',
              'inputs/original.png','inputs/target.png','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json','inputs/catalog-object.json',
              'inputs/snapshot.json','inputs/source-assetRecord.json','inputs/source-camera.json','inputs/source-rig.json',
              'reviews/preparation-v1/hashmanifest.json','reviews/preparation-v1/preparation-seal.json',
              'reviews/preparation-v1-rig-supplement-v1/hashmanifest.json','reviews/preparation-v1-rig-supplement-v1/supplement-seal.json']:
        refs.add(O/n)
    refs.add(RUN/'style/warm-soft-reference.png')
    refs.update(p for p in P.rglob('*') if p.is_file() and p!=MANIFEST and 'gates' not in p.relative_to(P).parts[:1] and p.name!='postseal.json')
    assert all(p.is_file() and p.stat().st_size<100_000_000 for p in refs)
    baseline()
    records=[desc(p) for p in sorted(refs)]
    write(MANIFEST,{'asset':'creature-fish','round':'round-01','stage':'independent-evidence-before-review',
                    'candidatePacketSHA256':PACKET,'sourceSHA256':SOURCE,'pathBase':'object-root','files':records,
                    'fileCount':len(records),'totalReferencedBytes':sum(r['bytes'] for r in records),
                    'dependencyReferences':[desc(C/'resource-manifest.json'),desc(O/'reviews/preparation-v1/hashmanifest.json'),desc(O/'reviews/preparation-v1-rig-supplement-v1/hashmanifest.json')],
                    'acyclicOrder':'supplement -> review -> gate outputs -> postseal; later artifacts deliberately excluded',
                    'scope':'Actual-used private review closure plus immutable existing candidate inputs/media. Transitive manifests bind unchanged candidate/preparation dependencies without copying runtime trees or other-object reviews.'})
    print('EVIDENCE_SEALED',len(records),sha(MANIFEST))
def review():
    baseline();assert MANIFEST.is_file() and not REVIEW.exists()
    inspection=read(P/'visual-inspection-coverage.json')
    write(REVIEW,{'asset':'creature-fish','round':'round-01','independentReview':True,'verdict':'approve','candidatePacketSHA256':PACKET,
       'inspectedFiles':[r['packetPath'] for r in inspection['images']],
       'supplementalEvidence':{'path':str(MANIFEST.relative_to(O)),'sha256':sha(MANIFEST)},
       'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':7,'artifactFreeReadability':8},
       'observations':[
         'The original thin triangular pieces and angular body are replaced by a coherent rounded blue body, clear tapered waist, broad forked tail, padded side fins and a continuous dimensional dorsal. All four native views read as the same friendly floating actor; no invented rear face is required.',
         'Cobalt/cyan family, pale underside and cream-white eyes remain clear. Broad soft blue turning planes give the body volume; lower body stays readable on light, gray and dark backgrounds without the original inert dark underside. No directional ground cast or per-facing recolor is visible.',
         'Separated eye whites, blue irises, navy pupils and small glints read at logical and representative phone scale. The modest cyan mouth remains distinct where geometrically visible. Fin ridges and dorsal edges add deliberate native depth without a busy decorative pattern.',
         'All528 phase cells and44 scoped browser timelines show connected face/fin attachments and genuine body flex. Normal/pause are calmer, swim/pursuit/dash more active, weave turns, aim pitches, and hook/caught/escape retain short reaction roles. Loop wraps and one-shot settled holds remain coherent at12fps.',
         'At the strongest caught E bend, enlarged native replay shows faint soft compression bands on the body. They do not become hard facet stripes, black patches or a noisy pattern at logical/phone scale, and do not obscure anatomy or facial read. This is accepted as a small finish difference, not omitted evidence.',
         'No material clipping, tearing, detached eyes/mouth/fins, halos, black dead spots, chalky glare or texture swimming is visible in the required views and phases. The result visibly advances the fixed target and global warm-soft volume/readability outcomes.'
       ],'blockers':[],
       'remainingDifferences':[
         'The target has stronger glossy cyan sweeps and more elaborate fin/body highlights; this native result is simpler and more matte. Exact gloss, decoration count and target canvas occupancy were not frozen requirements.',
         'The native side view remains a compact generic fish with broad dimensional fins, rather than reproducing every single-view target proportion. The registered gross gameplay scale and facing coherence are preserved.',
         'Shallow transient compression bands at the largest caught E bend remain visible enlarged, with no material use-size readability loss.'
       ],'technicalEvidence':{
         'frozenContract':'Exact ROOT brief/contract/reconciliation and both immutable preparation seals bound in supplemental closure; same original three ranked outcomes applied without lowering the bar.',
         'savedNative':'Exact7e32… source opened unsaved using /opt/homebrew/bin/blender5.2.2LTS/d13f752e3b9c; correct Creature Fish Round01 Native scene/S33_CFX_creature-fish.001. Raw saved channels independently audited: all11 actions persist with fake users, pose rotation channels are Euler and five bone modes XYZ; actual location/scale channels also recorded. No prescribed XYZ fidelity rule is inferred.',
         'actualMotion':'All528 phases independently evaluate bone matrices and armature-relative vertices; every44 clip/facing has nonzero body response. Bone relative matrix max response ranges0.1837541163..1.0046235323, relative vertex displacement0.1844029545..0.8899827386. All attachments use the same armature and normalized weights; all8 loop13=1 and3 one-shot12=13=24 controls have zero measured geometry/bone/object residual.',
         'registration':'35degree CHARACTER ORTHO3.5/HORIZONTAL/aspect1/shifts0,.21428516507148743; native1792x2048 to published896x1024, logical448x512 root224,352, original6x2 atlas and frame order. Root S0/E90/N180/W-90, inner180 and exact hook/cable/nose metadata retained. No actor root travel, crop/fit/nudge or new support law.',
         'geometry':'Raw/evaluated allphase envelope independently measured and matches submitted bounds ledger exactly. Evaluated aggregate XY within±.956287 and Z[.089357935,1.048403502], inside frozen XY±1.02/Z[.02,1.18]/tol1e-5; camera bounds safely internal. Gross hit/catch scale retained; maxima are clearance budgets rather than desired body symmetry.',
         'replay':'44 independent maximum-body-response native source re-renders, one per clip/facing. None is decoded byte-identical; largest full-canvas mean absolute RGBA byte error7.2888e-6, largest individual channel difference13. These sparse tiny residuals have no observed visual effect; no claim of528 independently re-rendered frames. Independently verified all528 whole-canvas LANCZOS published frames and exact original atlas slots; no nonzero alpha border.',
         'consumer':'Exact current570a… raster/099de… layout helpers and served bundle, actual Chromium153.0.8010.12 full headless channel and default headless-shell, DPR1, scoped logical/phone/light-gray-dark plan. All44 complete RAF traces independently match floor(elapsed*12) with original wraps/clamps; all3692 existing compositor cells represented and read in44 timeline images. Both-mode still/contact evidence includes sockets. Existing bundle/module/resource closure is bound.',
         'residualLimits':'CSS/common-canvas native-nearest sampling plus whole CSS filtering is preserved and differs at antialiased edges from standalone Pillow reduction; modes also have small raster/dither residuals. Existing VP8 startup chroma/background shifts were bounded by56 lossless actual-compositor PNGs of normal/caught at phone/light in both modes: background remains exactlyRGB243,241,232. This diagnosis does not waive real motion pops or substitute sparse PNGs for allstate playback.',
         'scope':'Exact BODY candidate only. Background fish silhouette and marked2D effects deferred. Fixture checks do not establish full React/Godot integration or device behavior. Visible allphase attachment/intersection review is not an exhaustive mathematical solid-intersection test. No production/publishing approval, source edits, Git/index, device, live Blender or extra agents.'
       }})
    print('REVIEW_SEALED',sha(REVIEW))
def gates():
    baseline();assert REVIEW.is_file() and not (P/'gates/results.json').exists()
    checks=[('candidate-packet',SKILL/'scripts/candidate_packet.py',['verify','--packet',str(C/'packet.json'),'--review',str(REVIEW)]),
            ('audit-directions',RUN/'tools/audit_directions.py',['creature-fish','--round','round-01']),
            ('acceptance-contract',RUN/'tools/acceptance_contract.py',['creature-fish','--round','round-01'])]
    outputs=[];h=sha(REVIEW);m=sha(MANIFEST)
    for name,helper,args in checks:
        frozen=P/'resources/gates'/helper.name;before=sha(helper);assert before==sha(frozen)
        argv=[sys.executable,str(helper),*args]
        r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        out=P/'gates'/f'{name}.stdout.txt';err=P/'gates'/f'{name}.stderr.txt'
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(r.stdout);err.write_text(r.stderr)
        outputs.append({'name':name,'argv':argv,'cwd':str(ROOT),'exitCode':r.returncode,'helperPath':str(helper),'helperSHA256Before':before,'helperSHA256After':sha(helper),
                        'frozenHelper':desc(frozen),'stdout':desc(out),'stderr':desc(err),'candidatePacketSHA256':PACKET,'reviewSHA256':h,'supplementSHA256':m})
    assert sha(REVIEW)==h and sha(MANIFEST)==m
    baseline();write(P/'gates/results.json',{'candidatePacketSHA256':PACKET,'reviewSHA256':h,'supplementSHA256':m,'checks':outputs})
    for r in outputs:print('GATE',r['name'],r['exitCode'])
    assert all(r['exitCode']==0 and r['helperSHA256Before']==r['helperSHA256After'] for r in outputs)
def postseal():
    baseline();assert not (P/'postseal.json').exists()
    m=read(MANIFEST)
    for r in m['files']:assert sha(O/r['path'])==r['sha256'],r['path']
    results=read(P/'gates/results.json');assert all(r['exitCode']==0 for r in results['checks'])
    assert results['reviewSHA256']==sha(REVIEW) and results['supplementSHA256']==sha(MANIFEST)
    write(P/'postseal.json',{'asset':'creature-fish','round':'round-01','verdict':'approve','status':'SEALED_STOPPED_EXACT_BODY_CANDIDATE_ONLY',
                           'candidatePacket':desc(C/'packet.json'),'source':desc(O/'source/round-01.blend'),
                           'supplementalEvidence':desc(MANIFEST),'review':desc(REVIEW),
                           'gates':[desc(p) for p in sorted((P/'gates').rglob('*')) if p.is_file()],
                           'verifiedSupplementMembers':len(m['files']),'sourceAndPacketUnchanged':True,
                           'acyclicOrder':'supplement -> review -> gates -> this postseal; no predecessor includes this file',
                           'scope':'No wider catalog/family, production, Godot, device, effects or publishing approval.'})
    print('POSTSEAL',sha(P/'postseal.json'))
if __name__=='__main__':
    {'evidence':evidence,'review':review,'gates':gates,'postseal':postseal}[sys.argv[1]]()
