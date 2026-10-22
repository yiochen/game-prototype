import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[1];R=B.parents[7]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
extra={
 'native/inspected-world_components.py':R/'prototypes/sushi-loop/assets/production/source/blender/world_components.py',
 'canonical/inspected-reopen-audit.py':B.parents[1].parent/'reef-middle/reviews/round-02-independent/reopen_audit.py',
 'canonical/inspected-extra-native-audit.py':B.parents[1].parent/'reef-middle/reviews/preparation-v1/extra_native_audit.py'
}
idx=json.loads((B/'resource-index.json').read_text())
for dest,src in extra.items():
 dst=B/'resources'/dest
 if dst.exists():raise FileExistsError(dst)
 shutil.copyfile(src,dst);idx.append({'source':str(src),'frozen':str(dst.relative_to(B)),'sha256':sha(dst),'bytes':dst.stat().st_size,'role':'Inspected technical reference only; not executed or imported'})
write(B/'resource-index.json',idx)
canonical={'source/round-02.blend':'51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5','candidates/round-02/packet.json':'d60ff36edc6006a0d4082692e7c115be23e1fc1e9d674f8bdc5c2f8ccc447ca8','reviews/round-02.json':'f60dabe7a9e2ff5f0460f0e63a16fcd98a849415b21277cab7eb87ac1ec1a71e'}
integrity=[]
for p,h in canonical.items():
 path=B.parents[1].parent/'reef-middle'/p;actual=sha(path);assert actual==h;integrity.append({'path':str(path),'sha256':actual,'unchanged':True})
path=R/'prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend';assert sha(path)=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6';integrity.append({'path':str(path),'sha256':sha(path),'unchanged':True})
f=json.loads((B/'evidence/finite-native-summary.json').read_text());hist=json.loads((B/'evidence/historical-replay/summary.json').read_text())
write(B/'preparation-findings.json',{
 'asset':'reef-edge','stage':'preparation_only_complete_root_freeze_pending','verdict':'not_a_candidate_review_no_approval','independentInitial':'initial.json','criteriaProposal':'criteria-proposal.json','rootContractProposal':'root-contract-proposal.json','requiredEvidencePlan':'evidence-plan.json',
 'actualEvidence':{'nativeMeasurement':'evidence/derivative-native-audit.json','canonicalMeasurement':'evidence/canonical-native-audit.json','compactFields':'evidence/finite-native-summary.json','authoredContextTopology':'evidence/context-topology.json','historicalCaptureLedger':'evidence/historical-replay/capture-ledger.json','historicalReplaySummary':'evidence/historical-replay/summary.json','inspectedUseSizeSheet':'evidence/historical-replay/use-size-sheet.png'},
 'mainFindings':['Actual derivative W/E8point profiles equal accepted canonical source exactly. Asymmetric width handedness is preserved under all4 authored rotations.','Finite ground rectangle area0.76; source core closed. Derivative decorations stay inside nominal cell and finiteXY extent; actual maximumZ0.66 versus declared0.68. No elevated overhang requires an exception.','Canonical flat endpoint triangle/corner normals, worldPosition.Z blue/cyan linear ramp materials and symmetric native lighting were measured from the actual accepted source. Proposed adoption is explicit and is not derivative approval.','Historical registered4x/filter1.5 replay exists for all4. S after LANCZOS2x matches original decodedRGBA exactly. Common new direct2x/filter.01 recipe is adopted without a new sampling-policy or GPU study.','Mixed source topology confirms cornerW/N and endW handed rings. Proposed all4 globally rotated native/independent scenes use authored roots and a correctly oriented turn/end.'],
 'historicalSnapshotComparisonS':hist['snapshotComparisonS'],'frozenSourceIntegrity':integrity,
 'inspectionLimits':['No new reef-edge candidate/model/brief/target/production/Git/liveBlender/device edits. Only own new reviews were written.','No consumer browser matrix executed during preparation. Candidate actual browser/native/independent scenes remain required by evidence-plan.json.','Original source first unactivated dump had stale world matrices. It is retained explicitly invalid and excluded from measurements; activated original-native.json and evaluated derivative-native-audit.json are authoritative. Initial pre-activation driver version was not retained as a separate immutable file; no replay/geometry conclusion uses that invalid pass.','The three inspected external technical scripts are reference resources only. Canonical sibling approval and existing precision diagnosis are not new derivative or consumer approval.'],
 'nextGate':'Root reconciles/freezes proposed technical and visual contract, then dispatches a fresh editor. Judge candidate review remains pending.'
 })
for p in B.rglob('*.json'):
 if p.name not in ['manifest.json','seal.json']:json.loads(p.read_text())
files=[]
for p in sorted(B.rglob('*')):
 if not p.is_file() or p.name in ['manifest.json','seal.json']:continue
 assert p.stat().st_size<100_000_000,p
 assert p.suffix!='.pyc',p
 files.append({'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':sha(p)})
write(B/'manifest.json',{'asset':'reef-edge','stage':'preparation-v1','scope':'Only actual-used minimal resources, drivers, proposals and raw preparation evidence; no recursively copied candidate closure','files':files,'fileCount':len(files),'totalBytes':sum(x['bytes'] for x in files)})
seal={'asset':'reef-edge','status':'sealed_preparation_root_freeze_pending','manifestSHA256':sha(B/'manifest.json'),'fileCount':len(files),'totalBytes':sum(x['bytes'] for x in files),'largestFileBytes':max(x['bytes'] for x in files),'candidateApproval':False,'consumerApproval':False,'derivativeFamilyApproval':False}
write(B/'seal.json',seal)
for rec in files:assert sha(B/rec['path'])==rec['sha256']
print(json.dumps(seal))
