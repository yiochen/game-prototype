import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,subprocess,os,re
B=Path(__file__).resolve().parents[1];O=B.parents[1];R=B.parents[7];C=O/'candidates/round-01';E=B/'evidence';reviewPath=O/'reviews/round-01.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert not reviewPath.exists(),'Immutable review already exists'
packet=json.loads((C/'packet.json').read_text());packetSHA=sha(C/'packet.json');assert packetSHA=='270d330ded27fa71bc0b1484698e5e75ef671ce5d45bde767d66af559a4ad453'
assert sha(O/'source/round-01.blend')=='0b9ffb3ca2e1aff8e176d0b1c6fe6567542050282c37c224020a2721957a3e7c'
assert sha(O/'brief.json')=='3b0374a932cf918f044804fbaaecb0e7b852d40b2135c734a4ae57ad78bc3d74'
assert sha(O/'inputs/root-native-contract.json')=='87eb6091df4060dc30192dea306d82e2ebf5c1b7d553991ec4c2adef835e2565'
assert sha(O/'reviews/preparation-v1/manifest.json')=='672931ef1e5676b89339cea8f3adbf5098bc189d6255de206a2ef42f592b62f4'
gate=R/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py';assert sha(gate)==sha(B/'resources/acceptance_contract.py')
native=json.loads((E/'independent-native-findings.json').read_text());binary=json.loads((E/'binary-interior-audit.json').read_text());heroes=json.loads((E/'hero-replay-comparison.json').read_text());consumer=json.loads((E/'consumer-independent-summary.json').read_text());assert native['allPassed'] and binary['maximumInteriorLoss']==0 and binary['maximumJoinLoss']==0 and all(r['exactDecodedRGBA'] for r in heroes)
coverage=json.loads((B/'inspection-coverage.json').read_text());coverage['independentlyInspectedDetailSheets']=[{'path':str(p.relative_to(O)),'sha256':sha(p),'inspection':'Direct image inspection at exact CSS display pixel scale; full raw outputs and QA crop mapping retained.'} for p in sorted(E.glob('detail-*.png'))];write(B/'inspection-coverage.json',coverage)
executables={'python':sys.executable,'node':'/usr/local/bin/node','blenderWrapper':'/opt/homebrew/bin/blender','blenderBinary':'/Applications/Blender.app/Contents/MacOS/Blender'}
log=(E/'consumer-launch.log').read_text()
for i,line in enumerate([l for l in log.splitlines() if '<launching> ' in l]):executables['browser'+str(i)]=line.split('<launching> ',1)[1].split(' --',1)[0]
write(E/'toolchain-executables.json',{k:{'path':v,'sha256':sha(Path(v))} for k,v in executables.items()})
candidateAudit=json.loads((E/'candidate-reopened-audit.json').read_text());canonAudit=json.loads((E/'canonical-reopened-audit.json').read_text());write(E/'completion-checks.json',{'sourcePacketBriefContractPreparationUnchanged':True,'acceptanceToolUnchanged':True,'groundTrianglesExactToCanonical':candidateAudit['groundTriangles']==canonAudit['groundTriangles'],'allPacketRecordsVerified':json.loads((E/'packet-integrity.json').read_text())['recordsVerified'],'all4NativePublicationBytesExact':all(q['exactBytes'] for q in json.loads((E/'publication-byte-check.json').read_text()).values()),'coverageAliases':19,'coverageUniquePreviewPaths':18,'independentConsumerCases':32,'binaryInteriorCases':160,'noNewSamplingPolicyOrGPUStudy':True})
refs={C/'packet.json',O/'source/round-01.blend',O/'brief.json',O/'inputs/root-native-contract.json',O/'reviews/preparation-v1/manifest.json',C/'preview-coverage-map.json',O/'final/root-preview-alias-reconciliation.json',C/'validation.json',C/'toolchain.json',C/'consumer-summary.json',C/'extent-diagnostic/summary.json',O/'source/audit-round-01.py',O/'source/capture-consumer-round-01.cjs'}
for group in ['candidateRenders','previews']:
 for rec in packet[group].values():refs.add(C/rec['path'])
for d in ['N','E','S','W']:
 refs.update([C/f'native/static/{d}/000.png',C/f'atlases/static-{d}.png',C/f'evidence/sprites/middle/{d}/000.png'])
for backend in ['full-chromium','headless-shell']:
 reportPath=C/'consumer'/(backend+'-results.json');refs.add(reportPath)
 for rec in json.loads(reportPath.read_text())['records']:
  if rec['kind']=='primary':refs.update([C/'consumer'/backend/rec['id']/'native.png',C/'consumer'/backend/rec['id']/'independent.png'])
files=[]
for p in sorted(set(B.rglob('*'))|refs):
 if not p.is_file() or p.name in ['manifest.json','postreview-seal.json','final-gate.json','final-gate.log']:continue
 assert p.stat().st_size<100_000_000,p
 assert p.suffix!='.pyc',p
 files.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'asset':'reef-edge','round':'round-01','candidatePacketSHA256':packetSHA,'pathBase':'experiment','scope':'Actual used judge resources/drivers/replay evidence plus exact inspected packet media and measured primary raw inputs. Existing packet resources referenced without recursive copying. Review, gate output and postseal excluded for acyclic binding.','files':files}
write(B/'manifest.json',manifest);manifestSHA=sha(B/'manifest.json')
inspected=list(dict.fromkeys(r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()))
review={
 'asset':'reef-edge','round':'round-01','independentReview':True,'verdict':'approve','candidatePacketSHA256':packetSHA,'sourceSHA256':sha(O/'source/round-01.blend'),'briefSHA256':sha(O/'brief.json'),'nativeContractSHA256':sha(O/'inputs/root-native-contract.json'),'inspectedFiles':inspected,
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':7,'materialDetail':7,'artifactFreeReadability':8},
 'observations':[
  'All4 facings materially improve the original sparse peg-and-slab reading. Substantial hollow teal focal tubes and purple supporting groups have distinct openings, softly rounded bright rims and useful grouped heights. Selected raised blue stones have readable top/side volume, and the support has purposeful stepped relief.',
  'The blue/cyan support, teal/green growth and purple growth remain separated at logical cell128. At phone32 the larger forms simplify into a coherent reef with recognizable color hierarchy rather than isolated noise. Every facing retains useful volume; no dead side, clipped crown, broad black patch or unwanted ground shadow was found.',
  'The source broad black lower band is replaced by readable blue lower planes. Local dark tube openings communicate depth while broad matte midtones and controlled colored rims retain the requested soft cartoon character. No artificial silhouette halo, floating ornament or coplanar flash was identified in the inspected heroes and contexts.',
  'All19 declared preview aliases/18unique preview paths were actually inspected, including native primary/topology, both complete raster matrices, both CSS primary/topology sheets, fixed style comparison and the comparison-only source-extent sheet. repeated is the exact same native-primary-all4 path/hash and reuses that inspection. Independent exact-CSS-pixel detail sheets supplement initially resized large-sheet views.',
  'The mandatory approved-middle02/edge/middle02 native and independently assembled consumer fixtures show no visibly identified local crack, stripe, profile/crown step, exposed cap or fringe in all4 facings, cell128/32, light/gray/dark and inspected baseline/fractional phases. This judgment applies to actual unmodified outputs, not the comparison-only calibrated controls.',
  'The original corner/end pieces in the turned context retain their conspicuously darker original shading. They are labeled provisional context, not an impossible edge gate, a waiver of edge-to-approved-middle continuity or an approved derivative family.'
 ],
 'blockers':[],
 'remainingDifferences':[
  'The native result is simpler, more matte and more faceted than the richly terraced glossy/caustic fixed target. Fewer branches and ornaments remain; selected larger forms satisfy the frozen readable reef outcome without reproducing painted highlights or every target detail.',
  'Broad planar spans remain near exact finite interfaces. In mixed primary contexts they read as one coherent continuous reef surface around the raised interior forms, and retain the required asymmetric functional section.',
  'Native connected-context finite area-light/location/occlusion differences and backend-dependent source-extent/nearest-tie residuals remain in raw evidence. They are not represented as universal alpha/RGB image equality.'
 ],
 'technicalEvidence':{
  'packetRecordsVerified':2230,'packetIntegrity':'reviews/round-01-independent/evidence/packet-integrity.json','coverage':'reviews/round-01-independent/inspection-coverage.json','independentNativeFindings':'reviews/round-01-independent/evidence/independent-native-findings.json','heroReplay':'reviews/round-01-independent/evidence/hero-replay-comparison.json','consumerReplay':'reviews/round-01-independent/evidence/consumer-independent-summary.json','binaryInteriorAudit':'reviews/round-01-independent/evidence/binary-interior-audit.json',
  'nativeChecks':'Saved self-contained blend independently reopened without construction. All4 hero decodedRGBA exact; replay PNG container bytes differ. Original native/published/atlas PNG bytes are identical all4. Entire W/E .08 bands contain16evaluated triangles each with exact canonical positions, geometric/corner normals and actual native material graphs. No shader-normal override. Actual registered camera/rig/world/render recipe also matches canonical.',
  'finiteGround':'102bottom triangles exactly equal canonical; area0.7599999855713424. All864core edges have2incident polygons. Candidate boundsX[-.5,.5]/Y[-.38,.38]/Z[0,.6750000119] fit its own frozen0.68ceiling. Private meshes, static object/data/material resources, no image artwork/actions/linked libraries.',
  'consumerChecks':'Own primary native fixture recreated all4 from candidate plus exact accepted canonical source. Own current570/099 pure functions replayed32cases=2modes x4facings x2sizes x2root/panpairs(0,0)and(.25,.75), with raw canvas observations and actual CSS light/gray/dark screenshots. Complete packet160case sheets also inspected; primary hard gate128cases, provisional topology32cases.',
  'independentRawResiduals':consumer['reports'],
  'alphaInterior':'A separate binary union of actual projected native core triangles avoids GPU source-over-mask holes on internal triangulation/cell boundaries. Conservative outer erosion3pixels at cell128/1pixel at32 includes the finite joined bands. Across128packet primary+32newcases:0interior loss,0join loss,minimumalpha255,atleast2362interior and476join samples/case. This bounded interior test does not waive outer silhouette defects or replace visible seam inspection.',
  'samplingLimits':'Independent actual fullChromium153 residuals reach maxalpha255/maxopaqueRGB182/localjoinRGB182; shell153 reaches3/47/24. Existing candidate comparison-only extent controls report0visible discarded pixels, exact integer restoration, comparison residualalpha7/RGB59. Those old controls were inspected rather than rerun; no new policy/GPU sweep or runtime fix. No whole-image equality or GPU-internal causal proof is claimed.',
  'provenanceLimits':'Initial editor inactive-collection numeric dump was invalid and corrected activated evidence is preserved. Original full-matrix childargv was not captured; options/version/helper hashes and later same-option diagnostic argv remain. Own relevant native/current-consumer facts were independently established, with saved drivers/preexecution input hashes and DEBUG childargv. Background native renders and headless browsers only.',
  'acceptanceGate':'Unchanged acceptance_contract.py is executed after this review; gate stdout/status/tool/review hashes are bound acyclically by postreview-seal.json.'
 },
 'supplementalEvidence':{'path':'reviews/round-01-independent/manifest.json','sha256':manifestSHA,'relativeTo':'experiment'},
 'scope':'Approval binds this exact reef-edge round-01 packet/source only. No corner/end/whole-family, production, deployment or Godot approval.'
}
write(reviewPath,review)
command=[sys.executable,str(gate),'reef-edge','--round','round-01'];result=subprocess.run(command,cwd=str(R),capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
(B/'final-gate.log').write_text(result.stdout+result.stderr)
gateRecord={'command':command,'cwd':str(R),'toolSHA256':sha(gate),'reviewSHA256':sha(reviewPath),'candidatePacketSHA256':packetSHA,'exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr};write(B/'final-gate.json',gateRecord)
for rec in files:assert sha(O/rec['path'])==rec['sha256'],rec['path']
assert result.returncode==0,result.stderr
seal={'asset':'reef-edge','round':'round-01','candidatePacketSHA256':packetSHA,'sourceSHA256':sha(O/'source/round-01.blend'),'reviewSHA256':sha(reviewPath),'supplementalManifestSHA256':manifestSHA,'supplementalFileCount':len(files),'supplementalTotalBytes':sum(r['bytes'] for r in files),'gateSHA256':sha(B/'final-gate.json'),'gateLogSHA256':sha(B/'final-gate.log'),'unchangedAcceptanceToolSHA256':sha(gate),'gateExitCode':result.returncode,'acyclic':'manifest excludes review/gate/seal; review binds manifest; gate binds review; this postseal binds all.','verdict':'approve','noFamilyOrProductionApproval':True}
write(B/'postreview-seal.json',seal);print(json.dumps(seal))
