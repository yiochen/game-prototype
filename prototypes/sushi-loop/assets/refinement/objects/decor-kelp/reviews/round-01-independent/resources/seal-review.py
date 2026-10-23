from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[3];REVIEW=ROOT/'reviews/round-01-independent';C=ROOT/'candidates/round-01';RES=REVIEW/'resources';E=REVIEW/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Snapshot actually applied instructions before hashing; immutable dependencies are bound by their existing object-relative paths.
for src,name in [(ROOT/'prompts/judge.txt','judge.txt'),(ROOT/'reviews/preparation-v1/resources/instructions/refine-3d-model-SKILL.md','refine-3d-model-SKILL.md'),(ROOT/'reviews/preparation-v1/resources/instructions/root-AGENTS.md','root-AGENTS.md'),(ROOT/'reviews/preparation-v1/resources/instructions/sushi-loop-AGENTS.md','sushi-loop-AGENTS.md')]:shutil.copy2(src,RES/name)
packetSHA=sha(C/'packet.json');packet=json.load(open(C/'packet.json'));paths=set(p for p in REVIEW.rglob('*')if p.is_file())
# Reuse the sealed minimum dependencies, without duplicating runtime trees.
prep=ROOT/'reviews/preparation-v1'
for p in (prep/'resources/node-modules-used').rglob('*'):
 if p.is_file():paths.add(p)
for p in (prep/'resources/python-modules-used').rglob('*'):
 if p.is_file():paths.add(p)
# Capture source consumer dependencies are already private and exact packet-bound.
for rec in json.load(open(C/'resource-manifest.json'))['files']:
 if rec['path'].startswith('source/round-01-resources/'):
  p=ROOT/rec['path'];paths.add(p)
for p in [ROOT/'source/reproduce-round-01.py',ROOT/'source/round-01.blend',C/'packet.json',ROOT/'brief.json',ROOT/'inputs/root-native-contract.json',ROOT/'inputs/root-preparation-reconciliation-v1.json',ROOT/'reviews/proposedcriteria.json',ROOT/'inputs/target.png',ROOT/'inputs/original.png',ROOT/'inputs/warm-soft-reference.png',prep/'resources/concept_decoration_geometry.py']:
 paths.add(p)
# The review references this manifest; the later gates reference review and manifest. Neither is included here, so there is no cycle.
paths={p for p in paths if p.name not in ['manifest.json','postseal.json','review-gates.json']}
assert not any('__pycache__'in p.parts or p.suffix=='.pyc'for p in paths)
assert all(p.stat().st_size<100_000_000 for p in paths)
manifest={'schemaVersion':1,'asset':'decor-kelp','round':'round-01','candidatePacketSHA256':packetSHA,'pathBase':'Object root: prototypes/sushi-loop/assets/refinement/objects/decor-kelp','method':'New original-judge evidence plus exact reused immutable minimum dependencies and candidate inputs. No runtime application tree duplication. Manifest precedes review; gate receipts/postseal remain outside this manifest to avoid cycles.','files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(paths)]}
(REVIEW/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
inspected=[r['path']for g in ['candidateRenders','previews']for r in packet[g].values()]
review={
 'schemaVersion':1,'asset':'decor-kelp','round':'round-01','verdict':'approve','candidatePacketSHA256':packetSHA,'inspectedFiles':inspected,
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':9,'motion':9},
 'observations':[
  'Native fronds now flow through continuous curved bends with tapered broad faces, instead of the original sharp repeated zigzags. N/E/S/W all read as a coherent organic kelp cluster on grounded cobalt rubble. Seven primary leaves and inherited forks are useful editable reconstruction; original part counts and exact zigzag silhouette were not locks.',
  'Leaf/lime greens remain separate from rounded blue stones. Broad green face/edge shading and softly finished stone crowns provide readable volume without chalk-white highlights, plastic sparkle or black cavities. Highlights are quieter and the cluster more open than the target, while preserving its softly finished green-over-blue identity.',
  'At logical size, on light/gray/dark backgrounds, and in actual .570 phone and .099 tiny controls, the larger flowing leaf shapes remain identifiable. A few N/S leaves become narrow when edge-on, but adjacent broad curved fronds keep the cluster readable; the thin profiles remain stable through all12 phases. No clipping, detached roots/branches, abrupt normal seam, halo or coplanar flicker found in the inspected views.',
  'The3x3 repeated composition produces an interleaved kelp border with visible blue grounding. In the actual registered turquoise submarine/eel context, kelp is readable scenery and the yellow craft retains attention; there is no added directional ground shadow or preferred horizontal key.',
  'All48 unique phases were directly covered through four pixel-verified logical phase sheets. All four submitted APNGs were independently decoded and every phase matched exact published pixels; their exact frame delays are1/12s. Actual Chromium compositor screenshots over2.6s show phases1..11,0,1.. in order in all4 facings. The restrained sway stays continuous, the blue base stays still and the last/first transition shows no snap or texture swim.'
 ],
 'blockers':[],
 'remainingDifferences':[
  'Candidate uses smoother, more open ribbon curves and a less chunky silhouette than the target. This is an accepted native modeling choice within the frozen envelope, with recognizable kelp identity and coherent volume in every facing.',
  'Satin green shading and rounded cobalt stones are less glossy and less strongly rim-highlighted than the target. The broad colored highlights remain soft and controlled at intended use size and support quiet scenery hierarchy.',
  'Several N/S fronds have narrow true3D edge-on profiles. They remain stable and are supported by readable broad neighboring fronds; target single-view pixels do not define unseen facings.'
 ],
 'technicalEvidence':{
  'inputs':'Independently verified all611 packet records and every264 resource-manifest file, frozen brief/contract/criteria, target and exact source2abc7040...; no editor self-rating or persuasive design rationale read.',
  'native':'Independent Blender5.2.2LTS saved-source audit covers52 actual facing/phase states. Root0/unit with properS0/E90/N180/W-90; physical XY within±.49250003 and Z0..2.0654471 inside frozen±.5/Z0..2.12. All624 finite root/fork interfaces,17 cap points each, embedded by independent actual mesh BVH ray tests; all21 own meshes closed at every edge. Native source has no target card/image texture, linked library, runtime modifier, shape key or rig ambiguity.',
  'capture':'Measured source35-degree camera/ortho1.5/shift[0,.75]/pixelAspect1:1 with native768x1920. Exact common ordinary35 height-dependent native world-Y law measured across52 states against independent formula: maximum evaluated error2.4577213e-7; authoring coordinate restoration0. Physical envelope/contact and transient capture stretch remain separate. Symmetric overhead plus four equal cardinal broad fills; no ground shadow receiver.',
  'motion':'Seven actual assigned native primary action owners; five forks inherit parent motion; nine blue base stones stationary. All four frame1/13 physical closures exactly coincide. All four submitted native closing renders exactly match first renders in decoded RGBA. Closure13 is evidence only;12-frame atlases unchanged.',
  'sourceReplay':'Independent clean exact saved-source smoke recapture using /opt/homebrew/bin/blender produces decoded-exact S/E native frame0. This candidate replay is distinct from the documented non-byte-exact original historical replay.',
  'publication':'Independently compared all48 native4x complete-canvas LANCZOS reductions to submitted2x frames and every atlas cell; all decoded RGBA exact. Each atlas2304x1920,6x2, no extra closure cell. All48 phase-sheet content regions exactly map to the published frames at logical size; APNG12×1/12s decoded frames are exact.',
  'consumer':'Independently replayed actual sealed fixture logic/candidate atlases with both Chromium153.0.8010.12 headless modes at390x844 DPR2; actual process executables/options/hashes retained. Nearest restored after resize, common-phase native canvas oracle exact for all3 bounded controls in each mode. Six independent CSS and six native-canvas outputs exactly match submitted corresponding controls. Native canvases are identical across browser modes; actual CSS is honestly different: phone maximum11, tiny6, context14 channel units, with no material visible defect. CSS/native evidence is not conflated.',
  'limits':'Bounded asset review and actual headless consumer controls; not full native-device, Godot, family, main or publishing approval. The initial drawImage APNG sampler froze default frames and is explicitly excluded from temporal evidence; true compositor screenshots and all-phase mappings replace it. No shared helper/model/candidate/target edits.'
 },
 'inspectionCoverage':{'directHeroes':4,'declaredPreviews':15,'uniquePublishedPhases':48,'actualAPNGPlaybacks':4,'actualBrowserCSSControls':6,'method':'Heroes and all static declared previews directly viewed. APNG coverage combines independently exact decoded48-phase mapping to directly viewed phase sheets with actual changing compositor playback screenshots; no first-frame-only claim. Own consumer recaptures map decoded-exact to six directly inspected submitted screenshots. Detailed mappings in visual-coverage-mappings.json and playback-actual-css/phase-identification.json.'},
 'supplementalEvidence':{'path':'reviews/round-01-independent/manifest.json','sha256':sha(REVIEW/'manifest.json')},
 'scope':'Approval binds only exact decor-kelp round-01 packet34a0e87c... and its saved source/renders/resources. No other asset/family/main/production/Godot/deploy approval.'
}
(ROOT/'reviews/round-01.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'verdict':review['verdict'],'packetSHA256':packetSHA,'reviewSHA256':sha(ROOT/'reviews/round-01.json'),'manifestSHA256':sha(REVIEW/'manifest.json'),'manifestFiles':len(paths),'inspectedRecords':len(inspected)},indent=2))
