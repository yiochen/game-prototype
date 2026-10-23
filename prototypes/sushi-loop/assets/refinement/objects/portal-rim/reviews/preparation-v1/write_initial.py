from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parent
def w(n,d): (P/n).write_text(json.dumps(d,indent=2)+'\n')
initial={
'asset':'portal-rim','stage':'independent-preparation-only','candidateVerdict':None,
'independence':'Inspected raw original, frozen target, global warm-soft reference, raw source and native records before editor proposals or other-object aesthetic conclusions. No editor proposals read.',
'inspectedFiles':['inputs/original.png','inputs/target.png','../../style/warm-soft-reference.png','inputs/snapshot.json','inputs/catalog-object.json','inputs/source-camera.json','inputs/source-assetRecord.json','inputs/source-rig.json','../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','reviews/preparation-v1/raw/idle/S/010.png','reviews/preparation-v1/raw/idle/E/010.png'],
'originalObservations':[
'An upright open cyan torus, thin cyan outer hoop, moving blue rectangular runes and two navy faceted rock supports. Strong flat bright bands on the main hoop and nearly black lower rock faces reduce soft crafted volume.',
'The two supports and opening establish the portal identity; the black visible center in the transparent preview is actual empty alpha, not an opaque disk.',
'Native E/W views are thin edge profiles, not camera-facing circular views. The ring and blue ornaments remain identifiable from the side but the portal opening cannot be demanded as a circle at those facings.',
'Native geometry has 12 mesh objects plus an empty root, but part count, torus segmentation, blank supports and precise weak proportions are not design locks.'
],
'fixedTargetObservations':[
'Bright cyan current-like inner rim remains the visual center. Broad soft highlights and blue-to-cyan depth make the ring feel rounded, and warm gold structural trim separates the rim from the navy rock support.',
'Beveled gold housings with saturated blue jewel centers create deliberate rhythm; warm framing connects the supports and makes them look constructed.',
'The target is a single S-like presentation. Its gold trim is an optional secondary accent compatible with cyan/blue/navy identity, not authorization to change the global palette or to paint highlights into camera-facing artwork.',
'The target moves and enlarges the visible silhouette within its canvas. It is aesthetic evidence only, and does not prove registration, physical aperture clearance, frame envelope, unseen views or loop motion.',
'Any fringe/glow in the target should not be copied as an unwanted alpha halo. Do not demand photon-like bloom or specific swirling painted streaks if native soft material form gives coherent readable energy.'
],
'globalStyleInterpretation':'The plant reference uses warm raised edges, broad readable faces, soft highlight rolloff and strong simple volume. It supports softened bevels and purposeful construction rather than dense fine texture or photoreal reflections.',
'functionalInterpretation':'W14 route/decor rim beside a traveling submarine; source notes explicitly say open ring with no opaque disk and no access mechanic. Entry socket is a center reference at [0,0,0.74], not a modular join or ship-pass collision contract. Source portal-entry is a separate catalog object; only idle is required here.',
'nativeFindings':'See native-inspection.json, native-measurements.json and nativeValidation.json. Actual support/bounds, camera and native saved actions take precedence over generic footprint/full-cell assumptions. Root must reconcile permitted design envelope before editor construction.',
'status':'Preparation; criteria proposed, root reconciliation/freeze pending; no candidate or family/production approval.'}
w('initial.json',initial)
criteria={
'asset':'portal-rim','version':'proposal-v1','status':'proposed-for-root-freeze','ranking':[
{'priority':1,'area':'shapeVolume','observableOutcome':'The cyan upright open portal reads as one substantial, intentionally built ring supported by two stable navy masses. Rim, outer structure, blue ornament housings and support connections have clear volume and coherent construction. Improve forms/proportions/topology freely within the functional and registered envelope; no source part-count fidelity requirement.'},
{'priority':2,'area':'colorLightMaterial','observableOutcome':'Cyan/blue remain the focus against navy supports, with warm gold or warm neutral structural accents where useful. Rounded bevels and broad soft highlight rolloff give the warm cartoon reference feel, with controlled saturation and visible lower-face detail. All facings use coherent native materials and lighting without preferred horizontal illumination or directional ground shadow.'},
{'priority':3,'area':'readabilityMotionDefects','observableOutcome':'At logical and phone scale the ring, empty opening, structure and supports remain distinct in N/S; E/W read as purposeful physical edge views with useful thickness. Motion is a smooth 12-frame pulse/circulation, loop closure is visually continuous, and supports stay stable. No broken/tangent-looking joins, z-fighting, black dead patches, clipped ornaments, halos or unreadable tiny decoration on light/gray/dark.'}
],
'dimensions':{
'shapeVolume':'Reward meaningful native modeling improvements; retain upright open ring identity and finite support role. Do not demand target outline pixel matching.',
'color':'Maintain cyan/blue/navy hierarchy; target gold can be secondary craft accent, with root accepting palette interpretation.',
'lightingHighlights':'Soft shaped native highlights, readable lower faces and consistent volume across four views; not literal frozen target streaks.',
'materialDetail':'Clean beveled construction and restrained faceting/detail, visible at intended size; avoid dense microtexture or glossy photographic reflections.',
'artifactFreeReadability':'Every required frame/facing and actual playback inspected; N/S aperture remains open, E/W profile remains coherent, alpha clean on three backgrounds.'},
'hardTechnicalConstraintsReference':'root-native-contract.json (proposed, root owns freeze)',
'nonRequirements':['Exact target silhouette, part count, gem count, torus topology or painted streaks','Opaque/full-cell floor coverage','Invented modular joins, repeated seam or ship passing through the opening','Extra entry/enter clips or any of the 13 marked 2D effects','Unseen-view aesthetics inferred literally from the one-view target'],
'approvalRule':'No candidate exists. Later approval requires visibly improved native exports against root-frozen criteria plus all required technical and visual evidence. Missing evidence remains needs_evidence.'}
w('criteria.json',criteria)
# Required top-level own judge documents mirror exact first version; retained bytes are immutable after this write.
for n in ['initial.json','criteria.json']:(R/n).write_bytes((P/n).read_bytes())
