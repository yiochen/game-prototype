"""Freeze independently prepared component outcomes before fresh native editors."""
import copy, hashlib, json
from pathlib import Path
RUN = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    assert not p.exists(), str(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2)+'\n')
for asset, manifest_name, base in [
    ('sub-harpoon-mount','reviews/preparation/evidence-manifest.json','reviews'),
    ('sub-collector-inlet','reviews/preparation-manifest.json','')]:
    obj=RUN/'objects'/asset
    manifest=obj/manifest_name
    records=read(manifest)['files']
    for record in records:
        path=obj/base/record['path']
        assert path.is_file() and sha(path)==record['sha256'],str(path)
    proposal_path=obj/'reviews/source-contract-proposal.json'
    criteria_path=obj/'reviews/proposedcriteria.json'
    proposal=read(proposal_path); criteria=read(criteria_path)
    brief_path=obj/'brief.json'; brief=read(brief_path)
    assert not brief['qualityCriteria'], 'Cannot overwrite a frozen brief'
    backup=obj/'brief-v1-before-native-freeze.json'
    assert not backup.exists(); backup.write_bytes(brief_path.read_bytes())
    contract=copy.deepcopy(proposal)
    contract.update(schemaVersion=1,status='root-frozen-before-fresh-editor',candidateApproval=False,
        proposalSHA256=sha(proposal_path),preparationManifestSHA256=sha(manifest),
        proposalEvidencePathBase='Object reviews/; source proposal evidence pointers are relative to reviews/',
        rootAuthority='inputs/frozen-main-v1/project.blend and its frozen body/interface law. Actual native finite faces govern contact, not descriptive midplanes or bounding boxes.')
    capture_law='Preserve actual own registered55.0079798degree camera/aspect1.22065556, logical192x352/root96,248/cell128. Native4x768x1408/root384,992, published2x384x704/root192,496, one common symmetric EEVEE rig with filter_size.5 persisted and whole-frame BOX reduction. No fit, crop, shift, warp, alpha repair, horizontal preferred key or directional ground shadow. Main65degree square-pixel camera remains distinct; exact canonical resources, not projected pixels, must match.'
    neutral_law='Main later adopts ONLY exact approved canonical-S IDLE neutral local mesh/normals/UV/material resources at the frozen positive uniform mount. Body, mounts, camera, lights and actions remain unchanged. No post-approval remodel/recolor/rebevel/nonuniform or per-view fit, and no own active clip mapping into main. Native resource extraction identity and all4 integrated neutral views are required. Other gear and overall body remain preliminary context, not final main approval.'
    if asset=='sub-harpoon-mount':
        resolution={
            'finiteSupport':'A purposeful fully supported rear foot at localZ0 within actual finite seat X±.11571425,Y[.12714291,.55857140]; meaningful finite two-axis bearing area, intended connection center contained. Raised forward cradle clears hull/glass through every phase. No prescribed foot dimensions or arbitrary support percentage. Report actual polygon area/centroid/extents/normals/separation; old broad base intersections are defects to repair, not locks.',
            'mouth':'Provisional derived mouth[.31,-.444,.683] is a reference, not a functional endpoint lock. Declare actual candidate neutral mouth and local -Y axis, measure drift and clearance. Keep legacy[.24,-.4,.37] unchanged and distinct. No projectile/cable work.',
            'motion':'Keep source12-frame/12fps NONLOOP barrel+muzzle coherent +Y recoil displacement table exactly, including frame6 peak.04466833174228668 and frame12 residual.003000006079673767; no frame13/loop/neutralized endpoint. New static and moving cohorts/topology allowed; map the same offsets about new neutral construction. Numeric evidence plus intended-size playback required.',
            'reservation':'All neutral and active native construction inside localX±.18,Y±.62,Z[0,.48], ground root identity. Actual footprint1x1/nominalheight.55, unchanged8atlas layouts.',
            'capture':capture_law,'neutralAdoption':neutral_law,'finalApproval':False}
        outcomes=criteria['rankedVisibleOutcomes']
        definition='Compact warmly crafted red/gold launcher with cool rounded barrel, meaningful seated support and readable native recoil, clean in every standalone and frozen mounted view.'
        evidence=criteria['requiredEvidence']
        freedom=criteria['designFreedom']
    else:
        resolution={
            'finiteSupport':'Actual finite front face Y=-.45399999618530273 (localY.16500000953674315), normal-Y, X±.11699999123811722. Available contact height under frozen reservation worldZ[.1665000021457672,.25]/localZ[.19125000536441802,.4]. Descriptive embedding midplane-.435 is not a contact-plane lock. Meaningful contiguous finite surface/section connection with useful two-axis spread; report area/centroid/extents/normals/separation and intentional seat insertion separately from unintended penetration. No arbitrary percentage threshold or hidden point/line/AABB support.',
            'mouth':'Declare actual native mouth and -Y axis, compare provisional[0,-.615,.17] and old source[0,-.624,.186] honestly. Legacy[0,-.53,.21] stays unchanged and distinct. Neither provisional nor old mouth is an exact endpoint lock.',
            'motion':'Preserve mouth-pulse plus rocking-guard functional gesture,12fps/12runtime/true closing key13 excluded from atlas. Construction, owner count, pivots and numeric amplitudes may change to make the same subtle functional action perceptible in ALL4 logical/phone views. Weak source N motion is not a lock. Nonnegative continuous ground sweep, registered capture,1x1 footprint and .55 height envelope. Neutral reservation is frozen; standalone active sweep must be measured and fit these bounds, with any genuine conflict reconciled before claiming compliance. Main adopts neutral idle only.',
            'reservation':'Neutral localX±.425,Y[-.275,.25],Z[0,.4], fixed mount[0,-.52,.09],positive uniformscale.4,rot0. No body/mount/root fitting. Actual finite lamp clearance and no occlusion of baseline-visible lens samples all4; preserve skid/hover behavior. Reserved top.25 leaves conservative.01299998world gap to bumper base, not a substitute for actual native audit.',
            'capture':capture_law,'neutralAdoption':neutral_law,'finalApproval':False}
        outcomes=criteria['rankedOutcomes']
        definition='Purposefully constructed soft cyan collector, recessed guarded mouth and warm protective lip, visibly seated on its actual finite mount, with readable subtle native pulse/rock loop in every facing.'
        evidence=proposal['candidateEvidenceRequiredAfterFreeze']
        freedom=['Rebuild native forms, topology, normals, materials and purposeful details within the frozen neutral reservation.','Improve native pivots and amplitudes for the same pulse/rock action; source part count, blank plates and weak motion are not constraints.']
    contract['rootReconciliation']=resolution
    contract_path=obj/'inputs/root-native-contract.json'; write(contract_path,contract)
    brief['capture'].update(nativeFrame=[768,1408],nativeCaptureScale=4,publishedFrame=[384,704],publication='Complete native4x frame BOX reduced to published2x; native EEVEE filter_size0.5 persisted')
    brief['constraints']['nativeContract']='inputs/root-native-contract.json'
    brief['qualityCriteria']={
        'status':'root-frozen-before-editor','definitionOfGood':definition,
        'priorityOutcomes':outcomes,'modelingFreedom':freedom,'hardConstraints':[capture_law,neutral_law,resolution['reservation'],resolution['finiteSupport'],resolution['motion'],resolution['mouth']],
        'requiredEvidence':evidence,'criteriaFile':'reviews/proposedcriteria.json','criteriaFileSHA256':sha(criteria_path),'nativeContract':'inputs/root-native-contract.json',
        'rootReconciliation':resolution,'proposalSHA256':sha(proposal_path),'preparationManifestSHA256':sha(manifest)}
    resources={'root-native-contract':'inputs/root-native-contract.json','independent-preparation-manifest':manifest_name}
    for record in records:
        rel=(Path(base)/record['path']).as_posix()
        resources['own-prep:'+rel]=rel
    brief['technicalResources']=resources
    brief_path.write_text(json.dumps(brief,indent=2)+'\n')
    write(RUN/'preparation'/asset/'root-freeze-v1.json',{'asset':asset,'status':'outcomes-and-technical-contract-frozen-before-editor','briefSHA256':sha(brief_path),'contractSHA256':sha(contract_path),'criteriaSHA256':sha(criteria_path),'proposalSHA256':sha(proposal_path),'manifestSHA256':sha(manifest),'verifiedPreparationFiles':len(records),'candidateApproval':False})
    print(asset, 'brief',sha(brief_path),'contract',sha(contract_path),'prepFiles',len(records))
