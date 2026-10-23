from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;EXP=BASE.parent.parent;C=EXP/'candidates/round-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=json.loads((C/'packet.json').read_text());psha=sha(C/'packet.json')
for group in ['files','candidateRenders','previews']:
 for rec in packet[group].values():assert sha((C/rec['path']).resolve())==rec['sha256']
coverage=json.loads((BASE/'declared-media-coverage.json').read_text());audit=json.loads((BASE/'final-native-publication-audit.json').read_text());native=json.loads((BASE/'native-independent.json').read_text())
assert all(s['maxPositionError']<=1e-6 and s['maxNormalError']<=1e-5 and s['maxAlbedoError']<=1e-6 and s['materialIdentity'] for s in native['fieldComparisons'])
assert native['lightIdentity']
assert native['candidate']['bounds'][0][1]>=-.51-1e-5 and native['candidate']['bounds'][1][2]<=.45+1e-5 and native['candidate']['beyondGroundMinZ']>=.02-1e-5
assert all(audit['nativeResourceClosure'][k] for k in ['meshTypesOnly','noObjectActions','noMaterialOrNodeActions','noShapeKeys'])
assert not list(BASE.rglob('__pycache__'))
exclude={'supplemental-manifest.json','final-gate.json','post-review-seal.json'}
files=sorted(p for p in BASE.rglob('*') if p.is_file() and p.name not in exclude and not p.name.startswith('final-gate.'))
assert all(p.stat().st_size<100000000 for p in files)
manifest={'schema':'independent-supplemental-files-v1','asset':'rock-shelf-edge','round':'round-01','candidatePacketSHA256':psha,'files':[{'path':str(p.relative_to(EXP)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'scope':'Own independent review supplemental evidence only. Final review/gate/post-review seal excluded to avoid hash cycles.'}
(BASE/'supplemental-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
paths=list(dict.fromkeys(rec['path'] for rec in coverage['records']))
review={
 'asset':'rock-shelf-edge','round':'round-01','verdict':'approve','independentReview':True,
 'candidatePacketSHA256':psha,'sourceProjectSHA256':sha(EXP/'source/round-01.blend'),
 'frozenBriefSHA256':sha(EXP/'brief.json'),'nativeContractSHA256':sha(EXP/'inputs/root-native-contract.json'),
 'inspectedFiles':paths,
 'previewAliasCoverage':{'repeated':{'path':'consumer-fullChrome-background-gray.png','sameAs':'fullChrome-background-gray','sha256':'6259d4757915c399e5c41ce0e9cd688a8e6a996e0bdc8dcede8435107f26412e','actualInspection':'Same exact path and hash; actual direct gray-sheet inspection reused truthfully.'}},
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':9},
 'scoreContext':'Comparative original/target judgement, not a numerical approval threshold. All required dimensions apply to this static low-shelf native asset.',
 'observations':[
  'The original broad blue slab, three ruler-like crack lines and crushed dark underband are materially improved. Broad fitted native stone plates have softened shoulders, physical clefts, an understandable lower course and restrained embedded blue/lavender stones. The exposed negative-Y ledge reads as rounded side dressing while retaining the straight low shelf role.',
  'The blue/cyan palette remains coherent with lighter upper planes and deeper readable lower mass. The broad highlights and rounded transitions carry soft cartoon volume in all4 facings, without metallic glare, a black dead band, directional ground shadow or painted target halo.',
  'At complete registered2x source size, logical128 and phone32, major stone divisions and the side ledge stay readable. Small pebble accents become quiet color notes rather than confetti; no extra ornament is required to imitate the single-view target.',
  'Every exact declared hero and unique preview file was directly viewed. Native/independent middle-edge-middle assemblies, isolated W/E controls and five-module mixed runs show continuous shoulders/ground baselines and clean actual contacts in all4 directions. No material local bright/dark cut line, notch, alpha hole, exposed internal cap, clipping or halo was visible on light/gray/dark or the CSS/root/pan phase cases in full Chromium and headless shell.',
  'The independently reopened saved source preserves actual finite support and the elevated side allowance. Opposing endpoint rings, evaluated neighboring normal/albedo/material fields and common light rig match the exact approved canonical middle within frozen tolerances. These technical checks support the visible result; they do not replace it.'
 ],
 'criteriaAssessment':{'low-shelf-volume':'pass','coherent-blue-material':'pass','purposeful-detail':'pass','rotatable-consistency':'pass','family-continuity':'pass','clean-finite-silhouette':'pass'},
 'blockers':[],
 'remainingDifferences':[
  'The target has more irregular piled slab contours, richer mottled surface painting, brighter white/caustic-like accents and additional pebbles. This native result uses broader clean stone cells, fewer accents and softer restrained highlights for consistent rotatable128/32 readability.',
  'True port bands and cap profile remain the registered canonical six-point low-shelf section rather than adopting ImageGen silhouette drift. The side ledge is a simpler rounded protrusion than the target’s layered front stones. These preserve the frozen role/envelope and are accepted differences.',
  'Standalone E/W cutfaces use the canonical native planar stone shader; they are coherent exposed ends, while matching internal contacts remain hidden and continuous in the required assemblies.'
 ],
 'technicalEvidence':{
  'independentSourceMethod':'Exact sourceSHA83765bce799260ef1cc016d02d28861b6a6c79ec883a0731a0800fab4f410657 reopened in background Blender5.2.2LTS. No embedded/external construction recipe executed. Generic judge driver measured evaluated meshes/material graphs/corner normals and rendered all4 heroes plus an in-memory diagnostic mixed3 assembly built only from the saved exact meshes.',
  'packetIntegrity':'All321 packet records /239 unique bound resources verified before review and unchanged after native/browser work. Four heroes and21 preview records cover24 unique media files; the repeated alias is explicitly mapped.',
  'nativeBounds':native['candidate']['bounds'],'finiteGround':native['candidate']['groundBounds'],'nativeBottomArea':native['candidate']['bottomArea'],'minimumDecorativeZBeyondGround':native['candidate']['beyondGroundMinZ'],
  'portFields':'Actual six-point W/E rings match opposing canonical rings exactly inYZ, cap materials match and caps have outward opposing normals. Exposed adjacent albedo error0; opposing custom corner normal component error at most2.049933300440898e-6.150 independent raycast/barycentric band samples over both ends/insets.0001..06 and top/±Y surfaces have zero position/normal/albedo residual and exact material graph identity.',
  'registrationAndStatic':'Identity ground root, exact registered55.0079798/aspect1.22065556/192x352/root96,248/cell128, native4x768x1408, published2x384x704; orthographic1.5 camera matrix measured. One static frame/native1/12fps/nonloop, no armatures, object/material/node actions or shape keys.',
  'nativePublication':'All4 sealed native4x -> complete-frame BOX published2x pixels exact; each atlas matches its declared hero frame. EEVEE32/filter.5/Standard/None/grade1.35/alpha preserved. No fitting, overlap, source-pixel repair or runtime helper mutation.',
  'resourceAndRig':'Saved candidate has native meshes/point albedo/procedural materials and no images/linked libraries. Private symmetric canonical lights match exactly; world strength0, shadow-disabled broad lights and no ground receiver. No target card or raster substitute.',
  'consumer':'Own replay imported exact current570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545 world raster and099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65 sprite layout unchanged. Full Chromium and shell153.0.8010.12, DPR1. All actual scene pixels in18 screenshots match supplied media;7/9 complete PNGs per browser match byte-for-byte. W/E control headers alone differ withinY4..21 because sealed harness says128cell and captures saycommon128cell; no scene pixels differ.',
  'honestResiduals':'Independent native reopen retains exact alpha coverage but RGB-only rendering residuals: own published hero maxRGB N1/E16/S15/W13 by largest channel, cause not isolated. Mixed joined-v-current-consumer native-opaque interior has zero alpha deficits in all4, including actual projected true-port neighborhoods. Port-neighborhood RGB maxima N/S1; E20/W19, with finite-light/interpolation/precision residuals kept raw and localized. Partial/external extent bands are separately retained: max abs alpha difference N4/E23/S3/W23 and RGB maxima up to65 in partial-alpha pixels. Those are not opaque local gaps; all required composites, unscaled128 rows and32 phone cases were visibly clean. No full-image RGB identity or numerical-only seam waiver is claimed.',
  'evidenceFiles':['native-independent.json','final-native-publication-audit.json','independent-render-residuals.json','browser-independent.json','browser-replay-comparison.json','declared-media-coverage.json','visual-crop-provenance.json'],
  'limits':'Approval is for the sealed declared art and this exact native source, under this frozen capture/consumer contract. Minor renderer/source-extent residuals and evidence heading-label drift remain documented. No gameplay/runtime code changed; engine/build tests are inapplicable to this review-only task.'
 },
 'supplementalEvidence':{'path':'reviews/round-01-independent/supplemental-manifest.json','sha256':sha(BASE/'supplemental-manifest.json')},
 'scope':'Exact rock-shelf-edge round-01 candidate only. No family, production, Godot integration or deployment approval.'
}
assert len(paths)==24 and len(coverage['records'])==25
(EXP/'reviews/round-01.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'verdict':'approve','reviewSHA256':sha(EXP/'reviews/round-01.json'),'manifestSHA256':sha(BASE/'supplemental-manifest.json'),'supplementalFiles':len(files),'totalSupplementalBytes':sum(p.stat().st_size for p in files),'inspectedUniqueMedia':len(paths)},indent=2))
