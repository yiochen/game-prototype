import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib
out=pathlib.Path(__file__).resolve().parent;reviews=out.parent;ex=reviews.parent;candidate=ex/'candidates/round-01';sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(pathlib.Path(p).read_text());packet=read(candidate/'packet.json');packet_sha=sha(candidate/'packet.json');assert packet_sha=='f811ac32a84bc59ea572a773963a5df54015b5d2a45cc5297cfd8408f8120473'
verification=read(out/'packet-verification.json')
for path,r in verification['files'].items():assert sha(path)==r['sha256'],path
native=read(out/'native-independent-audit.json');pixel=read(out/'pixel-audit.json');consumer=read(out/'consumer-independent-check.json');parity=read(out/'replay-pixel-parity.json')['summary'];closures=read(out/'closure-crosscheck.json')
assert all(x['sealedClosureNativePixelsExact'] for x in closures.values()) and native['neutralAndInverseMountMeshNormalUVMaterialIdentity'] and native['frozenBodyGeometryNormalsUVMaterialsUnchanged']
assert not any(not x['intentionalSeatContact'] for x in native['nativeBodySurfaceIntersections']) and len(native['finiteSeatContacts'])==2
assert not consumer['errors'] and all(not v['overflow'] and not any(v['rasterErrors']) and v['allNativeCanvasNearest'] for v in consumer['views'])
assert pixel['all52NativeToPublishedWholeBOXExact'] and pixel['all16NativeAndPublishedAtlasesExact']
coverage={}
for d,r in packet['candidateRenders'].items():coverage[r['path']]={'inspection':'Direct full published RGBA file view; supplemented by bound native fixed-crop detail and whole logical four-view preview.','evidence':['native-idle-detail.png','pixel-audit.json']}
for name,r in packet['previews'].items():
 if name.startswith('active-') and name not in ['active-all4']:
  d=name[-1];coverage[r['path']]={'inspection':'Actual declared APNG played in the browser; all12 APNG RGBA frames were proven byte-identical to the12 published cells already inspected in the bound native phase sheet.','evidence':[f'active-{d}-detail-all12.png','apng-source-coverage.json','loop-playback-all24.png']}
 elif name=='active-all4':coverage[r['path']]={'inspection':'Direct actual APNG view and browser playback stream; every actual APNG frame is exactly the four published cells concatenated in NESW order.','evidence':['declared-all4-apng-all12.png','loop-playback-all24.png','apng-source-coverage.json']}
 elif name=='all48-active-cells':coverage[r['path']]={'inspection':'Direct declared full sheet inspection, supplemented by per-facing detailed all12 phase sheets.','evidence':[f'active-{d}-detail-all12.png' for d in 'NESW']}
 elif name in ['consumer-phone','consumer-landscape']:coverage[r['path']]={'inspection':'Direct exact declared full screenshot at source width; also included with all78 supplied complete screenshots in the verified whole-screenshot sheets.','evidence':['pixel-audit.json','consumer-independent-check.json']}
 else:coverage[r['path']]={'inspection':'Direct exact declared preview file inspected.','evidence':['packet-verification.json']}
expected={r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()};assert set(coverage)==expected and len(expected)==15
(out/'inspection-coverage.json').write_text(json.dumps({'packetSHA256':packet_sha,'exactDeclaredPaths':coverage,'allDeclaredPathsActuallyCovered':True,'additionalWholeScreenshotCoverage':'All78 supplied screenshots inspected in12 hash-bound whole-screenshot sheets; no screenshot was cropped. Native detail crops contain the complete alpha extent of each reviewed native frame.'},indent=2)+'\n')
# Everything below this point is the final supplemental evidence closure and immutable verdict.
files=[{'path':str(p.relative_to(reviews)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='supplemental-manifest.json']
manifest={'schemaVersion':1,'asset':'sub-hull-panels','round':'round-01','candidatePacketSHA256':packet_sha,'scope':'Supplemental original independent component review evidence only. Final main approval excluded.','toolEnvironment':{'Blender':'5.2.2 LTS buildd13f752e3b9c','Python':'3.12.14','Pillow':'12.3.0 copied loaded module/native-library closure','Chromium':consumer['browser']},'files':files,'totalBytes':sum(f['bytes'] for f in files),'upstreamImmutableResourceClosure':'packet-verification.json binds all1193 unique packet files; original1664 files records plus4 candidate render records and11 previews were rechecked before sealing.'}
manifest_path=out/'supplemental-manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
contacts=[]
for c in native['finiteSeatContacts']:contacts.append({k:v for k,v in c.items() if k!='actualClippedTriangleRegions'})
review={
 'round':'round-01','asset':'sub-hull-panels','verdict':'approve','candidatePacketSHA256':packet_sha,'candidateProjectSHA256':sha(ex/'source/round-01.blend'),'canonicalNeutralProject':{'path':'source/round-01-neutral.blend','sha256':sha(ex/'source/round-01-neutral.blend')},'componentApprovalOnly':True,'finalMainApproval':False,
 'inspectedFiles':sorted(expected),
 'inspectionCoverage':{'path':'round-01-independent/inspection-coverage.json','sha256':sha(out/'inspection-coverage.json'),'all15ExactDeclaredPaths':True,'extraNativeRuntimeFrames':52,'extraHalfPhaseNativeImages':16,'extraCompleteConsumerScreenshots':78,'browserLoopPlaybackCaptures':24},
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':9},
 'scoreContext':'Comparative evidence against the untouched original and fixed target under frozen criteria, not a universal numerical approval threshold.',
 'observations':[
  'The two fitted saddles improve the original block with rounded thick edges, layered yellow/orange coating, raised cream insets and four legible silver cup/dome fasteners. Their separation is purposeful and the required center corridor remains open. The source part count and target continuous center strip were not treated as design locks.',
  'All four own-camera directions retain readable volume. Broad soft edge highlights describe the yellow shells; warm inset rims separate cream panels, and the cool fasteners provide a clear material cue. Lower faces darken into warm gold rather than black or muddy dead patches. No preferred horizontal key direction, ground shadow or ImageGen halo is present.',
  'Every published idle/active cell and the detailed native phase sheets remain coherent. The pulse/lift is deliberately subtle, with all hardware following the same native motion parent. Half phases and actual APNG playback show no pop, detached fastener, clipping, texture swimming or loop jump.',
  'All four native mounted views show the same exact neutral resources fitted to the frozen body. The supplied native assembly is real3D geometry rather than an independent sprite overlaid on main art. Contact patches support both intended centers with broad two-axis spread, and the native periscope/hull checks show no unintended intersection.',
  'At logical size and in the actual-renderer phone/landscape contexts on light, gray and dark backgrounds, the cream-and-metal accents remain distinguishable. The small fasteners become glints at scene zoom while the warm paired silhouettes carry the equipment identity. No material defects were found in required views or states.'
 ],
 'blockers':[],
 'remainingDifferences':[
  'The broad continuous target plate is interpreted as two slim separated armor saddles, as required by the frozen side boxes and periscope corridor.',
  'The target side grooves and decorative subdivisions are simplified into a restrained layered rim/inset/hardware construction that reads at the registered use size.',
  'Highlights are broader and directionally balanced rather than copying the target single-view white highlight marks.'
 ],
 'technicalEvidence':{
  'packetIntegrity':{'verifiedRecords':verification['verifiedEntries'],'verifiedUniqueFiles':verification['verifiedUniqueFiles'],'allHashesPassed':True,'frozenBriefSHA256':sha(ex/'brief.json'),'frozenNativeContractSHA256':sha(ex/'inputs/root-native-contract.json')},
  'registration':'Independently reopened saved native scene. Camera world/projection matrices match original within1e-6; actual55.00798degree/aspect1.22065556/root384,992 native4x768x1408 retained. Direct cameraRecord truthfully distinguishes published captureScale2/root192,496 from nativeCaptureScale4. Real cardinal root rotations, one-cell occupancy and logical192x352/root96,248 remain intact.',
  'captureAndPublication':'Saved EEVEE64/filter_size0.5 verified. All52 published RGBA cells are exact whole-frame BOX reductions of the corresponding768x1408 native captures. All8 published and8 native atlases contain those exact cells in the original1x1 idle or6x2 active layout. No fitting, alpha repair, sharpening, per-view coloring or runtime frame13.',
  'geometryAndResources':{'nativeMeshes':20,'insideBothFrozenSideBoxes':True,'neutralBoundsS':native['nativeNeutralBounds'],'nativeMeshNormalUVMaterialIdentityAfterNeutralExtractionAndInverseMount':True,'frozenBodyGeometryNormalsUVMaterialsUnchanged':True,'mountTranslation':[0,.16,.65],'uniformMountScale':.5,'mountRotation':0,'nativeAudit':'round-01-independent/native-independent-audit.json'},
  'animation':{'source':'Actual saved F-curves/function modifiers and one common native motion owner, not filenames.','law':'Ground-origin scale1+.015sin(theta); zBob.008(1-cos(theta)); theta2pi(frame-1)/12','runtimeFrames':12,'fps':12,'closingEvaluationFrame':13,'sealedFrame13PixelsExactlyEqualFrame1All4':True,'continuousSourceEvaluations':1201,'maximumObservedLawError':native['motionMaximumLawError'],'minimumObservedZ':native['motionMinimumZ'],'maximumObservedZ':native['motionMaximumZ'],'noStandaloneActiveMappingIntoMain':True,'mainNeutralOnly':True},
  'finiteSeatContact':{'method':'Independent actual evaluated downward triangle polygons clipped against BOTH actual native finite upward seat polygons; area/centroid from clipped polygon geometry. Not an AABB or point/line substitute.','contacts':contacts,'arbitraryPercentThresholdUsed':False,'purposefulSupportedConnectionConfirmedVisually':True,'unintendedNativeBodySurfaceIntersections':0,'intentionalSeatSurfaceContacts':2,'centralBridge':False,'reservedOtherComponentSeparation':'Inside frozen neutral side boxes; disjoint from harpoon and collector reserved Y ranges, while native hull/periscope intersection checks independently pass.'},
  'consumer':'Inspected all78 supplied complete screenshots through bound whole-frame sheets plus direct declared phone/landscape files. Independently replayed all12 active phases and idle across all4 facings,3 backgrounds and390x844/844x390 viewports. Actual copied layout/raster hook restored nearest native common-canvas sampling after resize; ordinary whole-canvas display filtering retained. No raster errors or horizontal overflow. Separate candidate pair and eel remain beside actual native assembled static main fixture.',
  'replayPrecision':parity,
  'reviewHarnessCorrection':'The initial harness incorrectly rejected the neutral library constant idle binding. The corrected check accepted only the constant idle cohort and cleared it in the ephemeral mounted review copy. Candidate/source bytes were never modified.',
  'limits':'Native mounted fixture uses the frozen preliminary body and provisional other equipment. Full576 main runtime frames, future canonical equipment/family approval and final main art approval remain pending. Supplemental re-renders are diagnostics; approval binds the supplied sealed packet bytes.'
 },
 'supplementalEvidence':{'path':'round-01-independent/supplemental-manifest.json','sha256':sha(manifest_path),'files':len(files),'bytes':manifest['totalBytes']},
 'approvalScope':'Exact sub-hull-panels round01 standalone sprites/source and canonical neutral resources at the one frozen positive uniform transform. No post-approval reshape, recolor, rebevel, new main-active mapping or final main approval is included.',
 'immutableVerdict':True
}
path=reviews/'round-01.json';assert not path.exists(),'Do not overwrite an existing signed review';path.write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'verdict':'approve','reviewSHA256':sha(path),'supplementalManifestSHA256':sha(manifest_path),'supplementalFiles':len(files),'supplementalBytes':manifest['totalBytes'],'declaredInspectionPaths':len(expected)}))
