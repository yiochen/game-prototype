from pathlib import Path
import json,hashlib,datetime,re
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');B=O/'candidates/round-04';D=O/'reviews/round-04-independent';V=O/'reviews/round-04.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert not V.exists(),'Verdict exists; no overwrite permitted'
expected={B/'packet.json':'c47dd7bb6b0c8eca67437cf9bbbf0d81b2cd6f94cbbee3207f5b8877a51252da',O/'brief.json':'88ba59077ca4d7b6a31fb71e63827208d29171c8b9367f43315e8cb522776bce',O/'source/round-04/round-04.blend':'afe1f6d8d8ee72188b7ceed08b93effaa350f26002e9017fc186374eccc25d45',B/'delivery.snapshot.json':'73a91bf0254a136d7a8af18fef1342329460d7416909c644196796a44477eaf4',O/'reviews/proposedcriteria.json':'bdc70d2b8aea70b4bdb7e77e5af1ae75472899f31b0c5d6fff52c0f91c7614b6',O/'reviews/source-contract-proposal.json':'257090fd4bec8d621f09f1de3c6758d3163d53ca299c909ab291263d86f096c8',O/'inputs/target.png':'d9c243399f96332631baaa712fc1d8bb597b4bcbfa2253b2b963858f5265b08f',O/'inputs/original.png':'2bdb41e1c9ac53f08085509658e054da5ba709284a6f047a492bbf245460d195'}
for p,h in expected.items():assert sha(p)==h,(p,sha(p),h)
P=json.loads((B/'packet.json').read_text());T=json.loads((D/'technical-summary.json').read_text());C=json.loads((D/'packet-raster-context-audit.json').read_text());N=json.loads((D/'native-independent-audit.json').read_text());F=json.loads((D/'video-content-audit.json').read_text());BX=json.loads((D/'box-support-audit.json').read_text())
assert T['failures']==[] and C['hashFailures']==[] and C['contextFailures']==[]
assert len(C['frames'])==100 and len(C['atlases'])==12 and T['source54ActionCohortsAllExact']
assert T['sourcePrimaryCarrierMaximumErrors']=={'location':0,'rotation':0,'scale':0,'matrix':0}
# Final exact-input recheck also covers the original evidence, recipe resources and excluded floor references.
inputs={}
for x in C['hashChecks']:
 p=Path(x['path']);h=sha(p);assert h==x['expected'],('Changed sealed input',str(p));inputs[str(p)]=rec(p)
for p in expected:inputs[str(p.resolve())]=rec(p)
for p in [O/'prompts/judge.txt',O/'reviews/initial.json',O/'reviews/source-audit/native-audit.json',O/'reviews/source-audit/contacts-shaders-resources.json',O/'reviews/source-audit/evidence-manifest.json',Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),O.parent.parent/'preparation/garbage-shelving/judge-dispatch.txt']:
 if p.exists():inputs[str(p.resolve())]=rec(p)
# Whole registered sheets, directly inspected; phase coverage also uses independently composed sheets.
static=[]
for scale in ['native','logical','half']:
 for bg in ['light','gray','dark']:static.append(B/'previews'/f'four-view-{scale}-{bg}.png')
static += [B/'previews/four-view-consumer55-4x-gray.png',B/'previews/human-context-all4-consumer55.png',B/'previews/repeated-all4-consumer55.png',B/'previews/underside-diagnostic.png',B/'previews/ground-contact-frontal-diagnostic.png',B/'previews/rear-structure-diagnostic.png']
visual_supplement=[p for p in D.glob('*.png')]
inspected=[x['path'] for x in P['candidateRenders'].values()]+[x['path'] for x in P['previews'].values()]
# The HTML index is a navigation surface, not a separate native visual claim.
index=B/'previews/index.html';index_text=index.read_text();index_refs=sorted(set(re.findall(r'(?:src|href)="([^"]+)"',index_text)))
for u in index_refs:assert (index.parent/u).is_file(),u
body=next(p for p in N['phases'] if p['clip']=='idle' and p['direction']=='S')['objects'];body=[x for x in body if 'boundsMin' in x and all(k not in x['name'] for k in ['fallen_board','loose_debris'])];body_min=min(x['boundsMin'][0] for x in body);body_max=max(x['boundsMax'][0] for x in body)
record={
 'schemaVersion':1,'asset':'garbage-shelving','round':4,'independentJudge':'catalog_garbage_shelving_judge_v1, original preparation judge','candidatePacket':rec(B/'packet.json'),
 'visualCoverage':{
  'sourceAndTarget':'Original snapshot and fixed target independently inspected again; original native source and all original phases were inspected before editor dispatch and remain bound in unchanged initial evidence. Comparison uses the final frozen coordinatorResolution, including the pre-editor highlighted envelope correction.',
  'all100CandidateFrames':'All four idle views; every one of the96 moving phases inspected through fixed per-clip crops for native detail and whole-frame three-background sheets. Crops are supplemental views only, with one constant crop per clip/facing; they do not alter delivery or registration.',
  'registeredStaticSheets':[rec(p) for p in static],
  'allBackgrounds':{'light':[235,231,219],'gray':[118,118,118],'dark':[27,34,41]},
  'literalContexts':'All4 facings: registered chef-lena at3,0 and obstacle0,0 in5x3; repeated full2x2 assemblies on2-cell centers and a one-cell-gap row; mask/root views; every clearance phase and after-removal floor. Pixel-exact context reconstruction independently checked floor/reference/sprites and fixed roots.',
  'nativeUndersideContact':'Sealed submitted diagnostics inspected, plus eight fresh read-only native captures: all4 facings low-front contact and underside. Supplemental underside fill/camera are explicitly diagnostic and never substituted for registered renders.',
  'navigationIndex':{'file':rec(index),'method':'Read HTML structure and local image/video references; visual decisions use the actually inspected bound assets and independent sheets. This is not a claim that every optional index thumbnail was expanded.','localReferences':index_refs},
  'supplementalImagesActuallyInspected':[rec(p) for p in sorted(visual_supplement)]
 },
 'temporalObservation':{
  'method':'Chrome CUA playback of exact sealed motion-overview.html and playback.html from temporary localhost8812. All8 synchronized source/candidate canvas streams observed at12fps, including greater than11 highlighted wraps and clearance terminal hold/restart. Inspected actual55CSSpxcell gray,224x336 light,448x672 dark. DOM/screenshot records below. All8 encoded comparisons independently decoded for all336frames against bound moving-frame inputs; decoded samples visually inspected on three backgrounds.',
  'sourceCandidateEightStreamFiles':[rec(B/x['path']) for k,x in P['previews'].items() if k.startswith('highlighted-') or k.startswith('clearance-')],
  'contextPlayback':'Own context-motion.html loads exact8 sealed floor/repeated MP4s. Observed midmotion then all8 completed3seconds with retained terminal fragments. Consumer removal is separate. All12 phase stills per facing also inspected.',
  'contextHTML':rec(D/'context-motion.html'),
  'savedBrowserRecords':[rec(p) for p in sorted(D.glob('browser-*'))],
  'encodedContentAudit':rec(D/'video-content-audit.json'),
  'limitations':'Screenshots supplement actual temporal observation; they alone do not prove cadence or loop continuity. Video is lossy H264; decoder error is recorded, with no universal bitidentity claim. Temporary Chrome tab and own HTTP server were closed before sealing evidence.'
 },
 'supplementalAssemblyBindings':[
  {'output':rec(D/'box-seating-visible-comparison.png'),'inputs':[rec(B/'frames/idle-S/000.png'),rec(D/'native-contact-S.png')],'recipe':'Unscaled native crops: registered S box(210,725,705,1045), low-front diagnostic box(220,515,710,795), on gray with labels. No delivery file edited.'},
  {'output':rec(D/'decoded-preview-samples.png'),'inputs':[rec(p) for p in sorted(D.glob('decoded-*-frame04.png'))],'recipe':'8rows, input1344x336 pasted unscaled at y=row*366+30 with30px filename label. Display tools may reduce the resulting image.'},
  {'output':rec(D/'independent-rerender-samples.png'),'inputs':[rec(p) for p in sorted((D/'native-rerender').glob('*.png'))],'recipeScript':rec(D/'finalize_evidence.py')}
 ],
 'primaryBodyWidthVerification':{'excluded':['fallen_board','loose_debris'],'minX':body_min,'maxX':body_max,'width':body_max-body_min,'frozenRange':[1.90,1.999]},
 'boxSeatingDiagnostic':{'audit':rec(D/'box-support-audit.json'),'perBoxRayGapRanges':[{'box':x['box'],'minimumGap':x['minimumGap'],'maximumGap':x['maximumGap']} for x in BX['checks']],'interpretation':'Extra low-front view shows small shelf/carton separations. Largest all-sampled minimum gap0.02339345world is about2.1 logical pixels or1 consumer55pxcell pixel vertically. Some low bevel samples also intersect shelves up to0.01842244world. Registered native/phone views read as seated; these are accepted non-material interior seating imperfections, not a claim of perfect contact. Ground support contract is separately measured and passes.'},
 'reviewLimits':['No editor self-ratings or rationale used to reach aesthetic verdict. Earlier drafts are not approvals.','No native source save, sealed file mutation, Git, live Blender or extra agent.','Native phase coverage is380evaluated samples, including104keys/closures and276quarter-frame inbetweens. Fresh independent render coverage is16saved samples; all100provided reproduction images were separately compared.','Exact pixel comparisons apply only to listed input/output files and recorded Blender/runtime; they are not a renderer-wide guarantee.']
}
save(D/'inspection-record.json',record)
manifest={'schemaVersion':1,'asset':'garbage-shelving','round':4,'scope':'Independent review supplemental evidence only; original preparation files remain untouched. Verdict is deliberately outside this manifest and binds it by SHA256.','candidatePacket':rec(B/'packet.json'),'frozenBrief':rec(O/'brief.json'),'exactInputs':[inputs[k] for k in sorted(inputs)],'outputsAndHelpers':[rec(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json'],'specificComparisons':'See technical-summary.json for every own native rerender and provided reproduction input/output SHA and pixel error; video-content-audit.json for336encoded-frame comparisons; supplemental diagnostic and inspection records for exact image derivations. No universal render bitidentity asserted.'}
save(D/'evidence-manifest.json',manifest)
verdict={
 'schemaVersion':1,'asset':'garbage-shelving','round':4,'verdict':'approve','candidatePacketSHA256':sha(B/'packet.json'),
 'frozenBriefSHA256':sha(O/'brief.json'),'candidateProjectSHA256':sha(O/'source/round-04/round-04.blend'),'deliverySnapshotSHA256':sha(B/'delivery.snapshot.json'),'targetSHA256':sha(O/'inputs/target.png'),'criteriaSHA256':sha(O/'reviews/proposedcriteria.json'),'sourceContractSHA256':sha(O/'reviews/source-contract-proposal.json'),
 'judgedAgainst':'Final frozen brief88ba5907 and original independent criteria, including coordinatorResolution. Catalog2x2/sourceScale2, functional full idle capacity, grounded contact band and separate highlighted/transient envelopes applied as frozen before editor construction. Original weak topology/counts are not locks.',
 'inspectedFiles':inspected,
 'inspectionMethods':'Direct pixel inspection, verified whole-frame and fixedcrop contact sheets, actual synchronized browser temporal playback, all-frame video decoding, and fresh background native audits/captures. Exact coverage/methods and supplemental input/output hashes are in inspection-record.json. The evidence-index HTML was inspected as navigation; no claim that every optional thumbnail was expanded.',
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':7.5,'materialDetail':8,'artifactFreeReadability':7.5},
 'scoreUse':'Comparative evidence against the original baseline, not a numeric approval threshold.',
 'observations':[
  'Material visible improvement over the blank slab source in every facing: separate built wooden planks with bowed/sagging edges, rounded worn breaks, legible shelf thickness, restrained fasteners, coherent rear brace and end construction. The detached board and floor pieces retain the discarded shelving role.',
  'Broad native wood cues and taped olive/tan cartons make material functions distinct at logical, half and actual55CSSpxcell display. The formerly blank crown remains legible as constructed wood. Quarter-turn side views are top-dominated under the locked camera, but now carry readable plank construction rather than empty flat rectangles.',
  'Honey/ochre mids and darker cavities stay warm on light,gray,dark backgrounds. Balanced soft edge lighting preserves all four sides without a preferred horizontal key, harsh black dead band, clipped outlines, exterior amber halo or ground receiver shadow.',
  'All100phases and actual12fps playback retain attached surface detail, coherent silhouettes and source-scale motion. Highlighted gently pulses without shader/opacity invention; clearance scatters,lifts,yaws and shrinks opaque pieces, then holds visible terminal fragments. Clean floor appears only after explicit consumer removal.',
  'Registered literal chef, repeated whole-assembly/gap and floor contexts retain scale/root/masks across all4facings. Idle neighbors remain readable; clearance overlap is transient choreography rather than expanded idle occupancy. Exposed underside/contact diagnostics show coherent native construction with the accepted minor interior seating limitation below.'
 ],
 'blockers':[],
 'remainingDifferences':[
  {'topic':'Target wear and highlight treatment','accepted':'Native result has more restrained chips and splitting, smoother surfaces and less bright edge outlining than the painted target. It still achieves crafted worn wood with native volume and useful detail. The target halo/background/framing drift were excluded by the frozen brief.'},
  {'topic':'Interior carton seating','accepted':'Extra low frontal diagnostic reveals slight carton-to-shelf gaps and shallow bevel intersections. Ray samples range from-0.01842244 to+0.04234624world overall; largest whole sampled minimum gap is0.02339345world for stored_box_3. Registered native/logical/phone views keep the contents visually seated, with no material floating or collision at intended use size. This is explicitly accepted as a non-blocking limitation; perfect interior physical contact is not claimed. Ground support contacts satisfy the separate frozen0.002world band.'},
  {'topic':'Quarter-turn projection','accepted':'E/W show a narrow shelf profile and dominant top under the original camera. Coherent plank edges, crossmembers, carton peeks and fallen-board role give useful readable structure without fitting or changing projection.'}
 ],
 'technicalEvidence':{
  'independentEvidenceManifest':rec(D/'evidence-manifest.json'),'inspectionRecord':rec(D/'inspection-record.json'),'technicalSummary':rec(D/'technical-summary.json'),'nativeRawAudit':rec(D/'native-independent-audit.json'),'packetRasterContextAudit':rec(D/'packet-raster-context-audit.json'),'videoContentAudit':rec(D/'video-content-audit.json'),
  'packetAndResourceIntegrity':{'finalRecheckedHashEntries':C['hashEntries'],'uniquePacketReferencedFiles':C['uniqueHashFiles'],'failures':[],'originalBackupAndLibrarySHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','sourceAndTargetUnchanged':True},
  'raster':{'frames':100,'format':'completeRGBA896x1344','atlases':12,'all100AtlasCellsPixelExactToSealedFrames':True,'layout':'idle896x1344;highlighted/clearance5376x2688,6x2,order0..11,no gutters','minimumNativeAlphaBorder':53,'requiredBorder':8,'all4NativeHighlightedClosureRGBAExact':True},
  'nativeAndMotion':{'backgroundBlender':N['blenderVersion'],'readOnlySavedProjectLoad':True,'evaluatedSamples':380,'keyAndClosureSamples':104,'quarterFrameInbetweenSamples':276,'all54OriginalActionCohortsExact':True,'primaryCarrierPathMaximumErrors':T['sourcePrimaryCarrierMaximumErrors'],'nativeClosureMaximumMatrixError':0,'cameraMatrixMaximumErrorFromOriginal':T['cameraMatrixError'],'cameraProjectionMaximumError':T['cameraProjectionError'],'cameraVariationAllSamples':T['cameraMatrixVariationAll380Samples'],'root':'fixedlocation0,scale1,actualS0/E+90/N180/W-90','render':N['render'],'phaseLedgerBoundsMaximumDifference':T['providedPhaseLedgerBoundsMaximumDifference'],'actualRootLocalUnionByState':T['envelopes'],'frozenStateBounds':'Idle XY[-1,1],Z[-.002,1.6801]; highlighted XY[-1.008,1.008],Z[-.009,1.694]; clearance S min[-1.566082864,-1.555552869,-.002],max[1.563991098,1.250407248,2.277417688],rotated with root. All pass.','supportBand':'All4upright support minima within7.93e-8world of0; maximum stationXYerror0.000768world versus0.03allowed. Loose board/debris ground surfaces also within0.002band and original support regions. Highlight pulse minZ-0.00640012 passes its separately frozen bound.','mainBodyWidth':body_max-body_min,'mainBodyWidthRequired':[1.90,1.999]},
  'editableNative':{'meshObjects':len(N['sceneMeshes']),'note':'18meshes,13912vertices,14151faces are descriptive only. Genuine geometry/material surfaces; no target image card or sampled texture. Original54native action cohorts retain role-specific carriers.','materials':len(N['materials']),'materialAndNodeAnimation':'none','componentAlpha':'opaque1 and authored static visibility','linkedLibrariesActuallyLoaded':N['libraries'],'sampledImagesActuallyLoaded':[x for x in N['images'] if x['name']!='Render Result'],'groundReceiverMeshes':0,'lighting':'One140W centered overhead area and four equal55W cardinal areas; same solution for all views.'},
  'metadataDiscrepancy':{'severity':'non-blocking stale bookkeeping','finding':'Submitted native-audit.json/validation.json retain a pre-save original-library entry and false noExternalImagesOrLibraries. Independently loading the actual sealed saved source shows no linked libraries or sampled images. Its bound immutable original-library resource is also present and hash-valid. Actual dependency closure passes; do not interpret the earlier entry as a missing resource.'},
  'temporal':{'all16EncodedStreamsFPS':'12/1','sourceCandidateHighlightStreams':'4x48frames,4wraps encoded; actual canvas playback observed beyond11wraps','sourceCandidateClearanceStreams':'4x36frames,one-shot12poses then finalhold','floorAndRepeatedStreams':'8x36frames,actual midmotion and terminalhold observed','all8SourceCandidateEncodedFramesIndependentlyCompared':336,'maximumMeanRGBChannelDecodeError_0to255':max(s['maximumMeanChannelError'] for s in F['streams']),'note':'H264 lossy preview error only; all native RGBA frames separately inspected/validated.'},
  'reproduction':{'freshIndependentSavedNativeSamples':16,'freshSamplesRGBAExactCount':sum(x['pixelExact'] for x in T['independentNativeRerenderComparisons']),'freshMaximumMeanRGBAChannelError_0to255':T['independentNativeRerenderMaximumMeanRGBA'],'providedFullReproductionImagesCompared':100,'providedRGBAExactCount':sum(x['pixelExact'] for x in T['providedReproductionComparisons']),'providedMaximumMeanRGBAChannelError_0to255':T['providedReproductionMaximumMeanRGBA'],'limit':'Input/output paths and SHA256 with per-file comparisons are bound in technical-summary.json. This does not claim universal render byte or pixel identity.'},
  'limits':'No unsampled continuous-time analytical proof is claimed; exact original curve keys/interpolation and104key+276inbetween evaluations establish mechanical parity. Fresh judge render coverage is16samples; every native exported frame and provided100frame reproduction is separately covered. Supplemental low-front/underside cameras are diagnostic only.'
 },
 'approvalScope':'Approval binds only the exact round04 packet, source and delivery snapshot above. No post-approval art tweak or re-render may replace those bytes without another review. Root retains promotion/integration/publication responsibility; this verdict grants no additional publishing permission.',
 'reviewOwnership':'Only new reviews/ evidence written. Original preparation evidence and sealed brief/source/candidates/delivery left unchanged. No Git, live Blender, additional agents or source save. All judge writes stop after this verdict.'
}
assert set(x['path'] for x in list(P['candidateRenders'].values())+list(P['previews'].values()))<=set(verdict['inspectedFiles'])
# FINAL WRITE. No other file is written after the verdict.
with V.open('x') as f:f.write(json.dumps(verdict,indent=2)+'\n')
print(json.dumps({'verdict':verdict['verdict'],'path':str(V),'sha256':sha(V),'manifestSHA256':sha(D/'evidence-manifest.json'),'supplementalFileCount':len(manifest['outputsAndHelpers']),'boundUniqueInputs':len(manifest['exactInputs'])},indent=2))
