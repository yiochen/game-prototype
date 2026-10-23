from pathlib import Path
import json,hashlib,struct,os
J=Path(__file__).resolve().parent;O=J.parent.parent;A=O/'candidates/round-01';B=O/'candidates/round-02';Q=O/'reviews/round-01-independent'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def desc(p):return {'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size}
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
expected={'oldPacket':'00ed21e5ae72ab5cc26972114dc418beed4d771fc02b2dea2b57f99405dd257f','newPacket':'b8f5dc5b60963d067045d06a952a112c0c78697c4d2336b6c4a009b17d026ded','oldReview':'e39fb466ec5f299cecfb4246bb4a384de871200c5b022091423031e0d1f9463e','oldSupplement':'831f09cc96e19ee405cc289881b8dccd3bf2ff6283ad3423481fdc5c46e17567','oldGates':'b21e610a74bed79404bd246709916d1652b26c17c44a39f60c966268fe2eccc5','oldPostseal':'1ff5b874cb70724f8490504730bf0b7340f1a01d7ed7a7626fb9ace3ceeec1a9','delivery':'5ffd142ca4e5f24184da0b40d68239712c895e975510883ccb55f692f89b1baf','rootReceipt':'cf605e39f79c107f7db906228425c1ef8516eaf51fdd28768b99f854d91bcf2f','source':'cbc7592d1c77782dbd046312bd700d31b27675ccde05c889b0fe46c192f1989c','dispatch':'bda395bfce031cf9b7e5a652bc4e2d0645a9be8ffa68b2a70d4d8a890e509786'}
paths={'oldPacket':A/'packet.json','newPacket':B/'packet.json','oldReview':O/'reviews/round-01.json','oldSupplement':Q/'supplemental-evidence.json','oldGates':Q/'gates.json','oldPostseal':Q/'postseal.json','delivery':O/'delivery.round-02.json','rootReceipt':O/'final/root-round02-submission-equivalence.json','source':O/'source/round-01.blend','dispatch':J/'resources/dispatch.txt'}
for k,p in paths.items():assert sha(p)==expected[k],k
p1=read(A/'packet.json');p2=read(B/'packet.json');r1=read(paths['oldReview']);s1=read(paths['oldSupplement']);g1=read(paths['oldGates']);z1=read(paths['oldPostseal']);d1=read(O/'delivery.round-01.json');d2=read(paths['delivery']);rootReceipt=read(paths['rootReceipt']);assert r1['verdict']=='approve' and r1['blockers']==[] and r1['candidatePacketSHA256']==expected['oldPacket'];assert g1['allPassed'] and z1['allGatesPassed'];assert r1['supplementalEvidence']['sha256']==expected['oldSupplement'];assert z1['review']['sha256']==expected['oldReview'] and z1['gates']['sha256']==expected['oldGates']
for k in ['schemaVersion','asset','style','qualityCriteria','capture']:assert p1[k]==p2[k],k
verified={};outside={}
def verify(path,digest):
 path=path.resolve()
 if path in verified:assert verified[path]==digest
 else:assert sha(path)==digest,str(path);verified[path]=digest
for r in s1['files']:verify(O/r['path'],r['sha256'])
for r in s1['externalIdenticalAliases']:
 verify(O/r['path'],r['sha256']);verify(O/r['privateEquivalent'],r['sha256']);outside[(O/r['path']).resolve()]=r
for group in ['files','candidateRenders','previews']:
 for r in p2[group].values():verify(B/r['path'],r['sha256'])
media=[]
for group in ['candidateRenders','previews']:
 assert list(p1[group])==list(p2[group])
 for name,old in p1[group].items():
  new=p2[group][name];assert old['sha256']==new['sha256'];a=(A/old['path']).resolve();b=(B/new['path']).resolve();assert a==b;assert old['path'] in r1['inspectedFiles'];verify(a,old['sha256']);media.append({'group':group,'name':name,'oldPacketPath':old['path'],'newPacketPath':new['path'],'sameObjectRelativePath':str(a.relative_to(O)),'sha256':old['sha256'],'inspectionReuse':'Own sealed original direct pixel inspection and complete lossless native usefulpixel sheet coverage; byte-identical absolute path alias, not a new rendering claim.'})
assert len(media)==51
assert [{k:r[k] for k in ['group','name','oldPacketPath','newPacketPath','sameObjectRelativePath','sha256']} for r in media]==rootReceipt['mediaMapping']
assert (B/'delivery.snapshot.json').read_bytes()==paths['delivery'].read_bytes()
assert d2['round']=='round-02'
assert d2['resources'][:len(d1['resources'])]==d1['resources'] and len(d2['resources'])==len(d1['resources'])+6
atlases=[];cat=read(O/'inputs/catalog-object.json');current={(c['id'],f):(c,v) for c in cat['clips'] for f,v in c['directions'].items()}
assert len(d1['atlases'])==len(d2['atlases'])==44
for old,new in zip(d1['atlases'],d2['atlases']):
 copy=dict(new);assert copy.pop('atlasSize')==old['dimensions'];assert copy==old
 path=O/new['path'];verify(path,new['sha256']);header=path.read_bytes()[:33];assert header[:8]==b'\x89PNG\r\n\x1a\n' and header[12:16]==b'IHDR';size=list(struct.unpack('>II',header[16:24]));assert size==new['atlasSize']==new['dimensions']==[5376,2048];assert header[25]==6
 clip,c=current[(new['clip'],new['direction'])];assert new['atlasSize']==c['atlasSize'];assert new['rects']==c['rects'] and new['columns']==c['columns'] and new['rows']==c['rows'];assert new['frames']==clip['frames'] and new['fps']==clip['fps'] and new['loop']==clip['loop'];atlases.append({'clip':new['clip'],'facing':new['direction'],**desc(path),'actualPNGHeaderSize':size,'RGBAColorType':header[25],'originalDimensions':old['dimensions'],'newAtlasSize':new['atlasSize'],'originalRectsUnchanged':True,'catalogLayoutExact':True,'onlyRecordDelta':'atlasSize alias added from dimensions'})
for key in d1:
 if key in ['round','resources','atlases']:continue
 assert d1[key]==d2[key],key
assert set(d2)-set(d1)=={'evidenceOnlySubmissionCorrection'}
assert len(d1['rawFrames'])==len(d2['rawFrames'])==528 and d1['rawFrames']==d2['rawFrames'];assert len(d1['nativeRawFrames'])==len(d2['nativeRawFrames'])==528 and d1['nativeRawFrames']==d2['nativeRawFrames']
for name in ['candidate_packet.py','audit_directions.py','acceptance_contract.py']:
 assert sha(J/'resources'/name)==sha(Q/'resources'/name),name
assert 'a.get(\'size\', a.get(\'atlasSize\'' in (J/'resources/promote_object.py').read_text()
priorNative=read(Q/'native-audit.json');priorBrowser=read(Q/'browser-replay.json');priorCoverage=read(Q/'coverage-proof.json');assert priorNative['projectSHA256']==expected['source'] and priorNative['failures']==[];assert sum(len(rs) for rs in priorNative['views'].values())==528;assert priorCoverage['nativeFrames']==528 and priorCoverage['nativeSheetCount']==44 and priorCoverage['failures']==[];assert len(priorBrowser)==2
used=[desc(p) for p in verified if p.is_relative_to(O)];externals=[outside[p] for p in verified if not p.is_relative_to(O)];assert len(externals)==2
report={'asset':'creature-eel','round':'round-02','candidatePacketSHA256':expected['newPacket'],'sourceSHA256':expected['source'],'priorBinding':{k:desc(p) for k,p in paths.items() if k.startswith('old')},'allNewPacketFileHashesVerified':True,'newPacketFileAliases':len(p2['files']),'uniqueUsedResourceHashesVerified':len(verified),'oldSupplementalFilesStillExact':len(s1['files']),'allFrozenCriteriaCaptureTargetSourceAndHelpersUnchanged':True,'metadataDelta':{'atlasSizeAliases':44,'meaning':'Importer-compatible aliases of correct existing dimensions; no art/source/rect/pixel/registration/motion/consumer-helper change.','otherPackagingChanges':['round becomes round-02','six prior packet/approval/evidence lineage resources appended','evidenceOnlySubmissionCorrection note added']},'mediaCoverage':media,'atlasMetadata':atlases,'publishedRecordsUnchanged':528,'nativeRecordsUnchanged':528,'priorFullPhaseVisualNativeConsumerProofReusable':True,'reuseLimits':['No new native rendering or browser playback was run or claimed in round02. Own exact prior direct51media/full528phase native inspection, actual saved-source native evaluation and actual2browser-mode consumer playback proofs are reused after complete exact-byte verification.','Original01packet/review/supplement/gates/postseal remain immutable; original visible criteria, scores, accepted differences and limits remain the same.','Static importer field lookup and actual44PNGheaders/catalog layouts verified; importer/production mutation is not performed by this judge.'], 'verifiedUsedFiles':sorted(used,key=lambda r:r['path']),'externalIdenticalAliases':externals,'rootEquivalenceReceipt':desc(paths['rootReceipt']),'rootReceiptIndependentlyCorroborated':True}
write(J/'equivalence-and-rebased-coverage.json',report)
print(json.dumps({k:report[k] for k in ['candidatePacketSHA256','allNewPacketFileHashesVerified','newPacketFileAliases','uniqueUsedResourceHashesVerified','oldSupplementalFilesStillExact','allFrozenCriteriaCaptureTargetSourceAndHelpersUnchanged','publishedRecordsUnchanged','nativeRecordsUnchanged','priorFullPhaseVisualNativeConsumerProofReusable']},indent=2));print('REBASED_MEDIA',len(media),'ATLAS_SIZE_ALIASES',len(atlases))
