"""Bind completed independent evidence to one exact, candidate-specific verdict."""
from pathlib import Path
import json,hashlib,shutil,os
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;CAND=OBJ/'candidates/round-01';REVIEW=OBJ/'reviews/round-01.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
assert not REVIEW.exists() and not (HERE/'supplemental-manifest.json').exists(),'Do not overwrite a review or supplement'
packetsha='20f3fe4297877ecc50affda4574c2ade50482e7068bd9d457fbfb3e6ff2bc54c';assert sha(CAND/'packet.json')==packetsha
assert sha(OBJ/'source/round-01.blend')=='f59fbb1aa5e6d45ea0dde0c916ab523d60bf63c748ccf650813072d4c46efd4d'
assert sha(HERE/'resources/instructions/actual-dispatch.txt')=='a92896df3d45326752355553ff785fd1c055cde8ca4bcb72c6277d05c924ccb3'
coverage=load(HERE/'coverage-inspection.json');assert coverage['inspectedTileIndices']==list(range(49))
checks=load(HERE/'replay-and-contract-checks.json');assert all(r['nativeCanvas']['decodedExact'] and r['screenshot']['decodedExact'] and not r['errors'] for r in checks['browserReplay'])
packet=load(CAND/'packet.json');expected={r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()};assert expected==set(coverage['coveredPacketPaths'])
helper=HERE/'resources/helpers';helper.mkdir(exist_ok=True)
for p in list(HERE.glob('*.py'))+list(HERE.glob('*.mjs')):shutil.copy2(p,helper/p.name)
members={};externalBindings=[]
def member(p):
    p=p.resolve()
    if not p.is_relative_to(OBJ.resolve()):
        digest=sha(p)
        equivalent=next((OBJ/r['path'] for r in members.values() if r['sha256']==digest),None)
        if equivalent is None:
            equivalent=HERE/'resources/packet-external'/(digest[:16]+'-'+p.name);equivalent.parent.mkdir(exist_ok=True)
            if equivalent.exists():assert sha(equivalent)==digest
            else:shutil.copy2(p,equivalent)
            member(equivalent)
        externalBindings.append({'verifiedExternalPacketFile':str(p),'sha256':digest,'frozenObjectRelativeEquivalent':str(equivalent.relative_to(OBJ.resolve()))})
        return
    assert '__pycache__' not in p.parts and p.stat().st_size<100_000_000,p
    members[str(p.relative_to(OBJ.resolve()))]={'path':str(p.relative_to(OBJ.resolve())),'sha256':sha(p),'size':p.stat().st_size}
for p in HERE.rglob('*'):
    if p.is_file():member(p)
# Retain the exact already-sealed candidate input closure verified independently;
# no duplicate runtime/application trees or alternative asset media are introduced.
member(CAND/'packet.json')
for group in ['files','candidateRenders','previews']:
    for r in packet[group].values():
        p=CAND/r['path'];assert sha(p)==r['sha256'];member(p)
manifest={'asset':'decor-background-rock','round':'round-01','candidatePacketSHA256':packetsha,'pathBase':'object root','files':list(members.values()),'externalPacketBindingsVerifiedThroughFrozenEquivalents':externalBindings,'scope':'Completed original-judge full-pixel visual coverage, exact saved-source/consumer independent replay and actual-used frozen code/input closure. No verdict, gate output or postseal is included, keeping review -> supplement -> evidence acyclic.','editorSelfRatingsUsed':False,'allFilesUnder100MB':True,'noRuntimeTreesOrPycache':True}
mp=HERE/'supplemental-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
review={
 'asset':'decor-background-rock','round':'round-01','verdict':'approve','candidatePacketSHA256':packetsha,
 'inspectedFiles':coverage['coveredPacketPaths'],
 'inspectionCoverage':{'uniqueMedia':20,'candidateRenderRecords':4,'previewRecords':19,'uniquePreviewPaths':16,'losslessTilesActuallyViewed':49,'method':'Every full pixel of all20 unique exact media paths was viewed at original detail through verified lossless tiles. Direct heroes also viewed. Three required preview aliases share already-inspected exact paths/hashes; explicit mappings in supplemental coverage files. No reduced-sheet/hash-only substitution.'},
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':7,'artifactFreeReadability':9},
 'scoreInterpretation':'Comparative evidence under the same five frozen visible outcomes, not a universal numeric approval threshold.',
 'observations':[
  {'criterion':'shape-volume','finding':'The leaning broad crown, varied shoulder height, lower body and differently sized front stones form one coherent cobalt bank. Irregular angled contours and softly finished edges improve the old repeated straight-sided pillar construction. N/W retain broad planes but no longer finish as nearly black rectangular fronts. The native closed nesting reads consistently in N/E/S/W and at logical/phone scale.'},
  {'criterion':'palette-depth','finding':'Cobalt remains the dominant family, with lighter blue upper planes and readable blue lower midtones. The original lower navy dead zones are relieved without copying the target white-cyan seam lattice. In both320px-phone contexts and fractional-pan landscape contexts, the yellow submarine remains the color focal point and the creature silhouette remains legible; the bank reads as blue scenery.'},
  {'criterion':'broad-soft-highlights','finding':'Broad restrained blue crown/shoulder lighting and small edge rolloffs describe the native volumes. Highlights remain colored, without clipped white glare, bloom, external halo or a preferred horizontal key. Small rounded stones add softer highlight transitions beside the main angular planes. One unchanged centered/equal-cardinal/ambient recipe serves all facings; no directional ground shadow is visible.'},
  {'criterion':'purposeful-material-detail','finding':'Large stone planes, varied secondary contours and sparse shallow dimples give restrained material character. Dimples are small or disappear at phone scale while the mass hierarchy still reads. This satisfies the quiet background role without random noise, mandatory target cracks or a dense decoration lattice.'},
  {'criterion':'artifact-free-readability','finding':'All4 native/published views, neutral logical/64px-cell studies, repeated3x3 all4 and all12 actual browser screenshots were inspected fully. No material black patch, broken normal, coplanar flicker pattern, exposed/open bottom, clipped form, detached stone, accidental transparency or halo was found. Narrow under-crown crevices read as intentional stone nesting. Repeated layouts are treated as density/silhouette studies, with no modular seam condition.'}
 ],
 'blockers':[],
 'remainingDifferences':[
  'The main crown retains broad angular planes and a visible lower ledge rather than the target\'s many subdivided softened boulder faces; it remains coherent and readable at game size.',
  'Surface detail is much sparser than the generated target, and the cyan-white edge network is omitted. The restraint supports the frozen quiet scenery role.',
  'Some small dimples become invisible on phone. Their disappearance does not carry the silhouette or stone hierarchy.'
 ],
 'technicalEvidence':{
  'binding':'Independently verified438 packet records /293 unique bound files against exact SHA256. Current brief/root contract/reconciliation and frozen criteria match the sealed input bytes. Candidate source remains f59fbb1aa5e6d45ea0dde0c916ab523d60bf63c748ccf650813072d4c46efd4d.',
  'native':'Opened exact saved candidate in background Blender5.2.2, enabled actual collection/objects/view layer before evaluated sampling, measured raw authored and evaluated bounds separately, and independently recaptured all4 cardinal static poses using existing camera/material/light. No source or candidate was changed.',
  'ownershipAndSupport':'Only5 owned closed positive-volume meshes with native bevel/weighted-normal modifiers,4 actual ground-reaching masses and a surface-intersection graph connecting the crown to grounded stones. No linked libraries, image-textured cards or foreign native geometry. Exact old base-cap area/shape, source four-part count and topology were not treated as locks.',
  'envelope':'All4 proper rotations fit X/Y[-.5,.5],Z[0,1.075] with frozen1e-6 tolerance. Evaluated maximumZ is1.06996786594; raw maximumZ1.06996893883. RootS identity/unit scale is preserved.',
  'camera':'Measured55.0079798-degree orthographic camera/aspect1.22065556/ortho1.5, native768x1408/filter1.5. Native root[384,1023.999938965], X[512,0],depth[0,511.999938965],height[0,-358.400146484]. Published384x704/root192,512/logical192x352/root96,256 remain registered; float residuals are retained.',
  'static':'Scene frame range1..1/fps12.36 actual relevant object/data/material/node-tree/world/capture owners have no action/NLA/drivers; no rig/shape channels. Evaluated state is invariant at source audit probes1/2/12. Required delivered clip remains exactly1 static frame per facing/nonlooping.',
  'nativeReplay':'Independent replayS is decoded-exact. N/W each differ at1pixel and E at3pixels, by at most1/255RGB; alpha is exact in every facing. Maximum channel mean is2.7744e-6/255. No byte/decoded equality is falsely claimed.',
  'publication':'Independently recomputed full native768x1408 ->384x704 LANCZOS pixels match all4 published frames exactly. Each original-layout single-frame atlas is byte-identical to its published frame. No crop/fit/warp/recolor/alpha repair.',
  'consumer':'Independently replayed the same6 frozen cases in both Chromium153.0.8010.12 modes/DPR1, from exact sealed HTML, helper099de618/570a0d0d and input atlases. All12 replay native canvases AND screenshots are decoded-exact to submitted counterparts; rectangles/root/order/bounds/plans match. No extra case matrix, React/Godot/device execution claim.',
  'twoModeResiduals':'Submitted native-canvas pairs are decoded-exact across modes. CSS screenshots retain ordinary filtering differences, maximum36/255 and channel mean at most.14004/255. Both actual mode sets received full visual coverage.',
  'lighting':'One centered overhead and four equal white cardinal area fills radius3/Z1.8 plus uniform world ambient; no ground shadow plane. Historical watts/world0/ramp/contrast were not imposed as aesthetic locks.',
  'limits':'This approval covers this exact object/candidate only. It grants no family, production, publishing, Git or Godot/device approval.'
 },
 'supplementalEvidence':{'path':str(mp.relative_to(OBJ)),'sha256':sha(mp)},
 'scope':'Original independent judge approval of exact round-01 bytes under the unchanged five frozen outcomes and clarified standalone contract. No editor self-rating or other-object aesthetic review used.'
}
REVIEW.write_text(json.dumps(review,indent=2)+'\n')
for p in HERE.rglob('*'):
    if p.is_file():os.chmod(p,0o444)
os.chmod(REVIEW,0o444)
for r in manifest['files']:assert sha(OBJ/r['path'])==r['sha256']
print('REVIEW_SHA256',sha(REVIEW));print('SUPPLEMENTAL_SHA256',sha(mp));print('SUPPLEMENTAL_FILES',len(manifest['files']));print('VERDICT',review['verdict'])
