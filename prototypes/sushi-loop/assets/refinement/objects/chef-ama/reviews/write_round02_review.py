from pathlib import Path
import json,hashlib,datetime
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-02';R=P/'reviews'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packet=rd(C/'packet.json');brief=rd(P/'brief-v3-held-food-semantic-contact.json');cal=rd(C/'native-replay-calibration.json');audit=rd(R/'round02-independent-evidence-audit.json');validation=rd(C/'complete-validation.json')
assert sha(C/'packet.json')=='2b5ead4aad701dd9b47f3467fdbe6fea0d1f04ebb202472a952b87875ca2000b'
assert sha(P/'source/round-02.blend')=='c66726f151d7348a73b4814074a2df986a71bd13f272b95b5634c695e0296f68'
assert sha(P/'brief-v3-held-food-semantic-contact.json')=='08f3f5fa4f4112023519180a61c43902f36cce5de82dff45c2a73f8a9bd2a837'
assert sha(C/'complete-validation.json')=='901a84ecd92f810e0e03b8d4dff7a5fc052e566930c2c2c9b1ecc18f4592cbf6'
assert sha(R/'proposedcriteria-held-food-v2.json')=='0f584b9a0d319a7167f9882c0f895113ff5ccf1e1b086a6751d31b5ae7a338fc'
assert sha(R/'initial-held-food-v2.json')=='64600eb9999d9d8df0bfa7ffb95500615bbb44d8ab4f59051b6da78422235bfd'
assert sha(R/'round-01.json')=='c4c6f64f337f8b50aab2a9419dbd105ae9b28d3c3547c10e7a2d89cf7c19b2bb'
inspected=list(dict.fromkeys(r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()))
assert len(inspected)==102
native=[f'frames/{clip}-{d}/{i:03}.png' for clip in ['idle','work','hold','load'] for d in ['N','E','S','W'] for i in range(12)]
playback=[{'path':f'playbacks/{clip}-{d}.mp4','durationSeconds':1,'fps':12,'decodedFrames':12,'playbackRate':1,'loop':clip!='load','readyStateObserved':4,'endedObserved':clip=='load','pausedObserved':clip=='load'} for clip in ['idle','work','hold','load'] for d in ['N','E','S','W']]
(R/'round02-browser-playback-observation.json').write_text(json.dumps({'method':'Actual local playback.html opened in Chrome; Play from frame00 used at rate1, upper and lower rows inspected, all16 video elements read through DOM after playback. All four load elements observed ended/paused at duration1 and loopfalse; idle/work/hold running with looptrue. This complements per-frame visual sheets and independent ffmpeg ordinal decoding.','url':'http://127.0.0.1:8913/playback.html','pageSHA256':sha(C/'playback.html'),'videos':playback},indent=2)+'\n')
review={
 'asset':'chef-ama','round':2,'verdict':'approve','createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'candidatePacketSHA256':sha(C/'packet.json'),'sourceSHA256':sha(P/'source/round-02.blend'),'validationSHA256':sha(C/'complete-validation.json'),
 'brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':sha(P/'brief-v3-held-food-semantic-contact.json'),'criteriaSHA256':sha(R/'proposedcriteria-held-food-v2.json'),'criteriaVersion':brief['criteriaVersion'],
 'criteriaFrozenInBriefMatchSavedCriteria':all(brief['qualityCriteria'][k]==v for k,v in rd(R/'proposedcriteria-held-food-v2.json').items()),
 'approvalScope':'Exact round02 canonical packed salmon plus the one globally frozen fullUV semantic food-quad mapping only. The already-approved physical chef/knife/rig/actions/material/light/camera and original Ama food depth/XYZ/yaw/ray law are preserved. No depth-law exception or per-pose fitting was needed.',
 'inspectedFiles':inspected,
 'inspectionCoverage':{
  'declaredCandidateRenders':4,'declaredPreviews':98,'nativeFrames':192,'states':['idle','work','hold','load'],'directions':['N','E','S','W'],'framesPerStateFacing':12,
  'method':'All192 actual native PNG frames inspected through all48 independently pixel-verified light/gray/dark logical192x320 contact sheets. Native/enlarged registration, rear crescent, E/W edge, palm/plate/face and old/new context previews inspected directly. All16 actual MP4s played in the local browser at rate1, with full192 decoded frame sequence independently compared to corresponding PNGs. All16 atlas rectangles independently compared exactly to all192 native PNGs. Eight independently rendered native controls produced from fresh original/candidate .blend reopens; three candidate risk controls also viewed directly. Technical JSON previews read and their underlying detailed data/pixels independently audited.',
  'nativeFramePathsInspectedThroughVerifiedSheets':native,
  'pixelAuditedAtlases':[f'atlases/{clip}-{d}.png' for clip in ['idle','work','hold','load'] for d in ['N','E','S','W']],
  'comparisonReferences':['inputs/original.png','inputs/target.png','source/dependencies-round02/dish-salmon.png','reviews/round-01.json','reviews/initial-held-food-v2.json','reviews/proposedcriteria-held-food-v2.json']
 },
 'scores':{'shapeVolume':7,'color':8,'lightingHighlights':8,'materialDetail':7,'artifactFreeReadability':8},
 'scoreContext':'Comparative warm-cartoon quality at the registered use size, retaining the same approved-body scores. This followup does not reopen body modeling or claim a 2D food insert is a modeled3D dish. Exact canonical image/aspect/support and visible no-regression are the principal new outcomes.',
 'observations':[
  {'criterion':'food-readable-canonical','finding':'The orange salmon bands, white rice and warm ivory plate read cleanly at logical size in S/E and the visible W portion. The round02 plate is slightly warmer than the old gray-white insert, with the approved canonical design intact. It does not look stretched or enlarged; the same occupied width is retained while padded original quad dimensions are corrected.'},
  {'criterion':'real-support-and-occlusion','finding':'Across all96 active hold/load frames, the plate lower contour retains the source support presentation and continuous motion relative to the hands. The E/W/S contact extrema and enlarged palm/plate/face contexts show no new hovering gap or detached plate travel. The same nonzero original billboard world-depth relation is preserved; this is a visual support comparison, not a literal3D zero-gap claim.'},
  {'criterion':'rear-crescent-and-profiles','finding':'Every24 N hold/load frame was inspected against source on light/gray/dark enlarged rear-crescent sheets as well as the full logical sheets. The tiny pale crescent below the rear hair/head remains a thin, intermittent baseline sliver. Canonical ivory makes it quieter in several frames; no materially enlarged bar, head patch or temporal flash appears. Load middle frames conceal it as before. E/W plate and head occlusion remains coherent with the source; eyes stay legible in the required profile context.'},
  {'criterion':'body-face-light-no-regression','finding':'Ama keeps dark-brown skin, short dark fringe, yellow folded wrap, ivory coat, green apron AND necktie, dark shoes and the approved soft highlights. Native old/new face/body comparisons and independent fresh candidate renders show no material skin-color, expression, shadow or volume regression. Actual changed-food radiance residuals are larger than replay variation and are accepted by their observed mild visual effect, not dismissed as noise.'},
  {'criterion':'temporal-and-deadspots','finding':'All192 native frames on three backgrounds retain the approved silhouette and stable foot/hand/knife motion. Hold plate scale/support stays steady; the load rise and return remain continuous without swimming, alpha popping, food tunneling, new black/bright patches, clipped salmon, objectionable halos or a new lighting dead spot. Actual12fps playback and ordered decoding preserve source timing; load is nonloop and ends at11, while idle/work/hold loop.'},
  {'criterion':'scope-and-visual-improvement','finding':'Round02 completes the canonical catalog-food followup while retaining the visibly improved approved warm native body. Useful body modeling from round01 remains intact; original unrefined proportions/part counts and the target lighter skin or framing artifacts were not reinstated as constraints.'}
 ],
 'blockers':[],
 'remainingDifferences':[
  'The food remains the original explicitly disclosed camera-facing2D alpha/emission insert; only its exact canonical dependency and one global quad/UV mapping change. No rebuilt3D food is claimed.',
  'The original tiny N rear plate crescent and source side-view face/plate overlap remain. They are not materially enlarged and are nonblocking at intended size under the frozen v3 scope.',
  'The approved body retains its simpler native cloth/facial detail and registered framing rather than the target image microtexture, brighter skin and enlarged presentation. Those accepted round01 choices are frozen in this followup.'
 ],
 'technicalEvidence':{
  'packetIntegrity':{'boundRecordCount':813,'allBoundRecordsAnd192NativeFrameHashesMatch':True,'report':'reviews/round02-independent-packet-check.json','sourceBackupAndPreviousReviewsUntouched':True},
  'exactSavedNativeParity':{
   'report':'reviews/round02-independent-evidence-audit.json','sourceAudit':'reviews/round02-independent-native/source.json','candidateAudit':'reviews/round02-independent-native/candidate.json','script':'reviews/independent_native_round02.py',
   'approvedOriginalSHA256':'73cf8d7c6c1b4ef4170020424bfa3eebaae47ca4aabd124cb7753d4b1c1d7248','candidateSHA256':sha(P/'source/round-02.blend'),'phasesReevaluatedPerSource':192,'physicalMeshesPerPhase':69,'physicalMeshPhaseComparisons':13248,'allOwnStaticDataAndPhasesExactlyEqual':True,
   'coverage':'Full evaluated local vertex, vertex-normal, corner-normal and polygon-normal buffers; object matrices/counts/visibility, full bone poses and root/food transforms on all192 phases. Static physical geometry/topology/UV/smoothing/weights/material assignments/parent inverses/armature modifiers, rest-bone hierarchy/matrices, all24 native action fcurve/key/handle/interpolation data, shader/light/world/camera/render inputs compared. Detailed supplied shared RNA, constraints, modifiers, actions/slots and drivers recursively compared; all10 differences are food-quad/UV derived geometry paths only. Supplied explicit world-coordinate/world-normal phase digests independently compared, equal in every object/phase.',
   'maximumPhysicalCoordinateNormalPoseDifference':0,'unexpectedStaticDifferencePaths':[],
   'hiddenChannels':'Idle/work food hidden in all96 original/candidate native phases. For independent full physical evaluation only, transient hide_viewport was cleared and restored without saving; this also evaluates hidden knife and hidden food transforms. Provided hidden-food evaluated matrices may be identity because those hidden objects are excluded from its depsgraph. Active food matrices match exactly; visibility and actual fresh render controls verify the delivered hidden policy.'
  },
  'canonicalAndSemanticMapping':{
   'exactPackedAndExternalRGBA_SHA256':'4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4','size':[731,505],'fullUV':[[0,0],[1,0],[1,1],[0,1]],'globalQuad':brief['semanticFoodMapping'],
   'maximumSavedQuadCoordinateError':7.368364529636295e-09,'oldNominalQuadActiveWorldWidth':0.35,'sourceAlpha128OccupiedActiveWorldWidth':0.344363940528451,
   'primarySupportFrames':96,'allAlpha64_128_192RelationshipsAudited':288,'primaryFloat32NativeRimShiftPixelsMaximum':2.288818359375e-05,'primaryWorldRimShiftMaximum':3.725290298461914e-09,'occupiedWorldWidthErrorMaximum':1.000159005615231e-08,
   'independentDoublePrecisionRecalculationPrimaryWorldShiftMaximum':audit['semanticAudit']['primaryAlpha128MaxWorldShiftDoublePrecision'],'independentDoublePrecisionRecalculationNativeShiftMaximum':audit['semanticAudit']['primaryAlpha128MaxNativeShiftDoublePrecision'],
   'alpha64SensitivityMaximumNativePixels':0.20522668263757252,'alpha192SensitivityMaximumNativePixels':0.0728389323954109,'sensitivityInterpretation':'Disclosed silhouette/reference uncertainty from different alpha thresholds, below one native pixel. Primary128 defines the one globally frozen mapping; no per-pose adjustments.',
   'sourceSpecificDepthLaw':'Original -facing yaw and -sin(facing)*0.39319298125871605 / -cos(facing)*0.39319298125871605 XY drivers, original XYZ/action/holder transforms and all six ray flags true, unchanged. No foreign depth constant or camera-only material shortcut.',
   'resources':'One exact packed canonical image plus byte-identical external dependency; actual saved source has no linked libraries. All body and food material graph inputs/interpolation/color/alpha interpretation preserved.'
  },
  'registrationAndMotion':{
   'nativeFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'observedNativeRoot':[192,496.00000381469727],'rootScale':1.25,'sourceScale':2,'cell':128,'camera':'Original orthographic1.5 and registered35degree source matrix/shift, unchanged.','sourceFacingDegrees':{'S':0,'E':90,'N':180,'W':-90},
   'functionalHeightContract':1.525,'originalEvaluatedMotionZBoundsRetained':[-0.014999999664723873,1.5278765559196472],
   'note':'The static functional envelope and exact original motion are preserved. Original bob/pose extrema are distinguished from rest functional height; no assertion that every animated top is exactly1.525.',
   'nativeFrameCount':192,'atlasCount':16,'atlasLayout':[6,2],'atlasSize':[2304,1280],'allAtlasPixelsExactlyMatchNativeFrames':True,'all48SheetCellsExactlyMatchNativeFrames':True,
   'sheetReport':'reviews/round02-independent-sheet-check.json','videoReport':'reviews/round02-independent-video-check.json','browserReport':'reviews/round02-browser-playback-observation.json','actualVideos':16,'decodedInOrderFrames':192,'fps':12,'maximumWholeFrameDecodedVideoRGB_MAE':0.5837768316268921,'loadLoop':False,'otherLoops':True,
   'videoLimit':'H264 review previews are lossy. Exact PNGs and atlas rectangles remain pixel authority; all192 MP4 decoded ordinals independently compared to corresponding exact PNG composites.'
  },
  'nativeReplayCalibration':{
   'freshOwnSourceReopens':2,'description':'Exact original and candidate separately reopened; every192 phase reevaluated and four controls rendered per source, including a same-input holdS0 repeat and active N/profile/load risk phases. Supplied twelve-phase hidden/active/N/E/W/load two-repeat controls independently recalculated from actual PNG pixels.',
   'ownSameInputAndFreshVsDeliveredMetrics':audit['ownFreshNativeControls'],'supplied12PhaseMeasuredMaxima':cal['measuredMaxima'],
   'settings':'Actual saved Blender5.2.2 Cycles GPU Metal72samples, seed0/animatedseedfalse, adaptive.02, OIDN denoise, Standard/None exposure0, BOX filterwidth1.5. Original scene data retained; installed Metal device selection and output filepath only were selected for own controls.',
   'conclusion':'Own source same-input4 pixels and candidate same-input8 pixels differ by1 RGB LSB, alpha0; independent fresh-vs-sealed source controls4/7/5 pixels and candidate5/6/8 pixels, each1LSB and alpha0. Delivered controls occupy the same sparse precision pattern as actual same-input repeats. This is scene/device/settings calibration, not a universal bit-identical GPU guarantee.'
  },
  'changedFoodRadiance':{
   'report':'candidates/round-02/radiance-residual-analysis.json','all12PhaseRegionStatisticsIndependentlyRecomputedExactly':True,'maximumCoreBodyRGBChannelDifferenceOutside8pxFoodExclusion':17,'maximumCoreFaceRGBChannelDifferenceOutside8pxFoodExclusion':13,'maximumCoreBodyMeanAbsoluteRGB':0.15171272546748304,'maximumCoreFaceMeanAbsoluteRGB':0.2476925851243463,'maximumCoreBodyAffectedPixels':14941,'maximumCoreFaceAffectedPixels':6193,'maximumCoreBodyAndFaceAlphaDifference':0,
   'nearFoodFilteringBand8pxMaxRGBDifference':92,'bodyOutside2pxMaxRGBDifference':48,'bodyAlphaEdgeOutside2pxMaxRGBDifference':68,'bodyAlphaEdgeMaxAlphaDifference':6,'transparentBackgroundMaxRGBDifference':255,'transparentBackgroundAlphaDifference':0,
   'assessment':'These changed-input residuals exceed sparse unchanged-input1LSB replay differences and are not labeled replay noise. Original all-ray food emission/alpha, primary filtering and denoising can alter reflected body pixels with identical physical inputs. Both2px and8px exclusions, body/face identity, alpha edges, food union and transparent RGB are separately reported; analytic identity masks omit multisample filtering. Real radiance cause is not visual approval by itself: native body/face comparisons, independent fresh renders, all-frame backgrounds and actual playback were also checked and show no material visual regression. No old/new nonfood RGB identity requirement or raster correction was applied.'
  },
  'limits':'Approval is specific to these saved native outputs, preserved original192-phase action contract and fixed canonical insert. Independent full parity is exhaustive over those phases; fresh native pixel replay controls are representative, augmented by the supplied12-phase controls that were independently remeasured. No extrapolation to an unrequested runtime food variant, rebuilt3D food or other object.'
 }
}
path=R/'round-02.json';assert not path.exists();path.write_text(json.dumps(review,indent=2)+'\n');print(str(path));print('ReviewSHA256',sha(path));print('Inspected',len(inspected),'declared paths and192 native frame paths')
