"""Evidence-only immutable round02. Never renders or edits native/art bytes."""
from pathlib import Path
import json,hashlib,shutil,os,copy

HERE=Path(__file__).resolve().parent;EXP=HERE.parent
OLD=EXP/'candidates/round-01';NEW=EXP/'candidates/round-02'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def write_new(p,d):
    assert not Path(p).exists(),str(p)
    Path(p).write_text(json.dumps(d,indent=2)+'\n')

expected_source='a7f8357632d42d3f5113f7ee3b423634bdd834e0d3cbfb9a058ea513767a1498'
assert sha(HERE/'round-01.blend')==expected_source
assert sha(EXP/'reviews/round-01.json')=='6582ca696607c85af4e49b926532cbe7babf6252126bdc73b38c98014fa0a1f7'
oldpacket=read(OLD/'packet.json');oldreview=read(EXP/'reviews/round-01.json')
assert sha(OLD/'packet.json')==oldreview['candidatePacketSHA256']
assert oldreview['verdict']=='needs_evidence'
assert len(oldreview['blockers'])==1

# Snapshot and bind every unique actual old packet input, plus its exact review
# and all59 original-judge supplemental inputs, without copying or rewriting any.
inputs={}
for item in [*oldpacket['files'].values(),*oldpacket['candidateRenders'].values(),*oldpacket['previews'].values()]:
    p=(OLD/item['path']).resolve();assert p.is_file() and sha(p)==item['sha256']
    inputs[p]=item['sha256']
supp=oldreview['supplementalEvidence'];sp=EXP/supp['path'];assert sha(sp)==supp['sha256']
supp_data=read(sp);assert supp_data['candidatePacketSHA256']==sha(OLD/'packet.json') and len(supp_data['files'])==59
for item in supp_data['files']:
    p=(EXP/item['path']).resolve();assert sha(p)==item['sha256'];inputs[p]=item['sha256']
for p in [OLD/'packet.json',EXP/'reviews/round-01.json',sp]:inputs[p.resolve()]=sha(p)

assert not NEW.exists();NEW.mkdir()
assert not (HERE/'round-02.blend').exists()
shutil.copyfile(HERE/'round-01.blend',HERE/'round-02.blend')
assert sha(HERE/'round-02.blend')==expected_source

ledger=read(OLD/'capture-records.json');outer=read(OLD/'validation.json')
assert ledger['captureRecords']==outer['captureRecords']
assert ledger['sourceSHA256']==expected_source
assert {r['direction'] for r in ledger['captureRecords']}==set('NESW')
for r in ledger['captureRecords']:
    p=OLD/r['path'];assert sha(p)==r['sha256'] and r['sourceSHA256']==expected_source

# The old target lacked audit_directions' recognized keys. Carry the exact
# original actual measurements directly into the new nativeValidation target.
native=read(OLD/'native-validation.json')
native['captureRecords']=copy.deepcopy(ledger['captureRecords'])
native['measuredCaptureRecordsProvenance']={
    'path':'candidates/round-01/capture-records.json','sha256':sha(OLD/'capture-records.json'),
    'verifiedExactOuterWrapper':'candidates/round-01/validation.json',
    'outerWrapperSHA256':sha(OLD/'validation.json'),
    'actualSourceSHA256':expected_source,
    'method':'Exact unmodified measured all4 records from actual original round01 capture ledger. Native renders/root matrices/rotations/camera/filter/frame and source hash are copied without alteration; no requested-angle inference or re-render.',
    'round02Change':'Expose existing actual captureRecords through the unchanged direction-audit supported schema.'}
write_new(NEW/'native-validation.json',native)
validation=copy.deepcopy(outer)
validation.update(round='round-02',nativeValidation='candidates/round-02/native-validation.json',
                  evidenceOnly=True,unchangedArtSourceSHA256=expected_source,
                  priorPacket={'path':'candidates/round-01/packet.json','sha256':sha(OLD/'packet.json')},
                  priorReview={'path':'reviews/round-01.json','sha256':sha(EXP/'reviews/round-01.json'),'verdict':'needs_evidence'},
                  change='Only validation packaging is corrected: new target includes existing measured all4 captureRecords. No native source, render, atlas, consumer image or frozen criteria changed.')
write_new(NEW/'validation.json',validation)

mapping=[]
for kind in ['candidateRenders','previews']:
    for name,item in oldpacket[kind].items():
        p=(OLD/item['path']).resolve()
        assert item['path'] in oldreview['inspectedFiles']
        mapping.append({'kind':kind,'name':name,'oldPacketRelativePath':item['path'],
                        'newPacketRelativePath':os.path.relpath(p,NEW),
                        'objectRelativePath':str(p.relative_to(EXP)),
                        'sha256':sha(p),'oldJudgeInspected':True,
                        'sameActualFile':True,'byteIdentical':True})
write_new(NEW/'art-identity-and-coverage.json',{
    'asset':'wreck-edge','round':'round-02','evidenceOnly':True,
    'oldPacketSHA256':sha(OLD/'packet.json'),'oldReviewSHA256':sha(EXP/'reviews/round-01.json'),
    'project':{'old':'source/round-01.blend','new':'source/round-02.blend','sha256':expected_source,'byteIdentical':True},
    'renderAndPreviewCoverageMapping':mapping,
    'allOldPNGInputs':[{'path':str(p.relative_to(EXP)) if p.is_relative_to(EXP) else str(p),'sha256':h,'bytesUnchanged':True} for p,h in sorted(inputs.items()) if p.suffix.lower()=='.png'],
    'scope':'Exact file/coverage identity only; original judge decides the new packet. Previous needs_evidence verdict remains immutable.'})
write_new(NEW/'evidence-inputs.json',{'asset':'wreck-edge','round':'round-02','evidenceOnly':True,'originalSupplementalFiles':59,
    'inputs':[{'path':str(p.relative_to(EXP)) if p.is_relative_to(EXP) else str(p),'sha256':h,'pathBase':'object' if p.is_relative_to(EXP) else 'absolute'} for p,h in sorted(inputs.items())],
    'unchangedValidators':[{'path':str(p.relative_to(EXP.parents[1])), 'sha256':sha(p)} for p in [EXP.parents[1]/'tools/audit_directions.py',EXP.parents[1]/'tools/seal_object.py',EXP.parents[1]/'tools/acceptance_contract.py']]})

delivery=read(EXP/'delivery.round-01.json')
delivery.update(round='round-02',project='source/round-02.blend',validation='candidates/round-02/validation.json',
                evidenceOnly=True,priorPacket={'path':'candidates/round-01/packet.json','sha256':sha(OLD/'packet.json')},
                identityProof='candidates/round-02/art-identity-and-coverage.json',
                sourceNotes='Exact byte copy of reviewed round01 source; original native recipe/resources unchanged. Evidence-only compatible actual direction-ledger packaging.',
                evidenceNotes='All art/native/atlas/consumer bytes and frozen brief/contract/criteria are reused unchanged. Existing actual measured all4 captureRecords now reside in the new nativeValidation target. Old-to-new direct inspection mapping and complete original59 supplemental input binding retained.',
                status='evidence-only editor handoff; awaits original independent judge on newly sealed packet')
resources={}
for r in delivery['resources']:
    p=(EXP/r['path']).resolve();assert sha(p)==r['sha256'];resources[p]=r['sha256']
resources.update(inputs)
for p in [HERE/'round-02.blend',Path(__file__).resolve()]:resources[p.resolve()]=sha(p)
delivery['resources']=[{'path':str(p.relative_to(EXP)) if p.is_relative_to(EXP) else str(p),'pathBase':'object' if p.is_relative_to(EXP) else 'absolute','sha256':h} for p,h in sorted(resources.items())]
write_new(EXP/'delivery.round-02.json',delivery)
print('EVIDENCE02_PREPARED','same source',expected_source,'visual aliases',len(mapping),'bound actual resources',len(resources))
