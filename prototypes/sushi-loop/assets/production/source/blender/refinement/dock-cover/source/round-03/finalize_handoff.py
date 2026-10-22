"""Immutable evidence-only delta delivery; no sealer, approval or production action."""
import sys,json,hashlib,datetime,ast
from pathlib import Path
sys.dont_write_bytecode=True
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent.parent;D=O/'candidates/round-03';L=O/'delivery/round-03'
assert not L.exists(),'Immutable handoff exists'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':str(p.relative_to(O)),'sha256':sha(p)}
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
for p in H.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
expected={'reviews/round-02.json':'d822c6fa56997e4f35c9798ccd1bda899d2df0a67c8a759c439ab4481babcf85','reviews/round-02-independent/supplemental-manifest.json':'639879779de4516be35100ccb5eafec575c76654d67b1a092b0177902227acd5','brief-v4-resource-paths.json':'7fd27d24700df7262e5aad0ed912621b1f5446d7332891923a1fb1fd1a60b269','source/round-02/cover.blend':'aea9e932ba845ede5c32ed4074eb5ff69acfef0f2c169398d147a7e6be0ad3a3','candidates/round-02/catalog-metadata-override.json':'6d88f5369c725e1635b2da28e7d684c84abfddca59df1fe420ba8c3565b17e4e','delivery/round-02/handoff.json':'4247f1e1fc61a157deadf472d98ec91be1abd2bd350efb7e7943fa43ffec9bfb'}
for p,s in expected.items():assert sha(O/p)==s,p
prior=read(O/'delivery/round-02/delivery.json');review=read(O/'reviews/round-02.json');ev=read(D/'consumer/consumer-evidence.json');old=read(O/'candidates/round-02/consumer/consumer-evidence.json');native=read(D/'native-input-verification.json')
assert ev['affectedCases']==36 and ev['changedOrderCases']==9 and ev['changedDecodedRGBACases']==0 and ev['unchangedHumanCases']==72 and not ev['errors']
assert len(ev['humanCases'])==108 and len(ev['equalityControls'])==36 and native['nativeRerendered']is False
assert ev['renderer']['sha256']=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'and ev['layout']['sha256']=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
key=lambda r:(r['case'],r['direction'],r['clip'],r['index']);oldBy={key(r):r for r in old['humanCases']};newBy={key(r):r for r in ev['humanCases']};affected={'approach','first-tread','second-tread'}
for k,r in newBy.items():
 before=oldBy[k]
 if r['case']not in affected:assert r==before
 else:
  im=Image.open(O/r['path']).convert('RGBA');ref=Image.open(O/before['path']).convert('RGBA');assert im.size==ref.size and im.tobytes()==ref.tobytes();assert sha(O/r['path'])==sha(O/before['path'])
  a=json.loads(json.dumps(r['placements']));b=json.loads(json.dumps(before['placements']))
  for ps in [a,b]:ps[-1].pop('supportedBy',None)
  assert a==b and r['plan']==before['plan']and r['sourceNativeFrame']==before['sourceNativeFrame']and r['publishedFrame']==before['publishedFrame']
  human=next(p for p in r['placements']if p['object']=='customer-rosa');assert human.get('supportedBy')==(None if r['case']=='approach'else 'dock-entry')
assert all(c['pngBytesAlsoExact']and c['correctedSourceMismatchPixels']==0 and c['allNonSupportPlacementFieldsExact']and c['uniqueEntryPlacementCount']==1 for c in ev['equalityControls'])
assert all(not c['orderChanged']or c['direction']=='N'for c in ev['equalityControls'])
assert all(r['exactPNGBytes']for r in native['atlases'])and native['verifiedRawFrames']==96 and native['repackedOriginalLayoutAtlases']==8
for r in ev['humanCases']:
 if r['case']in ['terminal-tread','transfer']:assert next(p for p in r['placements']if p['object']=='customer-rosa')['supportedBy']=='dock-deck'
# Verify prior immutable bytes, without trusting a prior approval or changing its review.
checked={}
def verify(p,s):
 p=p.resolve()
 if p not in checked:checked[p]=sha(p)
 assert checked[p]==s,str(p)
oldManifest=read(O/'delivery/round-02/artifact-manifest.json')
for r in oldManifest['files']:verify(O/r['path'],r['sha256'])
packet=read(O/'candidates/round-02/packet.json');assert sha(O/'candidates/round-02/packet.json')==review['candidatePacketSHA256']
for r in [*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]:verify(O/'candidates/round-02'/r['path'],r['sha256'])
supp=read(O/'reviews/round-02-independent/supplemental-manifest.json')
for r in supp['files']:verify(O/r['path'],r['sha256'])
write(D/'inherited-integrity.json',{'priorPacket':desc(O/'candidates/round-02/packet.json'),'priorReview':desc(O/'reviews/round-02.json'),'supplementalManifest':desc(O/'reviews/round-02-independent/supplemental-manifest.json'),'priorHandoff':desc(O/'delivery/round-02/handoff.json'),'uniqueUnchangedFilesRehashed':len(checked),'mismatches':0,'nativeSource':desc(O/prior['project']),'metadataReceipt':desc(O/'candidates/round-02/catalog-metadata-override.json'),'scope':'Read-only immutable-byte checks, not approval. Original review remains revise and metadata approved:false.'})
# Model exact unchanged promoter copy rules. No production files are written.
required={H/'reproduce.py',H/'consumer_fixture.mjs',H/'capture_consumer.mjs',H/'resources/native-references.json',H/'resources/baseline-cases.json',H/'resources/inherited-human-cases.json',O/'source/round-02/reproduce.py',O/'source/round-02/cover.blend',O/'source/round-02/rig.json',O/'inputs/shared-world-pose-v1/plan.json'}
for name in ['world-sprite-raster.js','sprite-layout.js','objects.json','sprite-inputs.json']:required.add(O/'source/round-02/resources/consumer'/name)
for r in read(H/'resources/baseline-cases.json')['cases']:required.add(O/r['referenceImage']['path'])
for r in read(O/'source/round-02/resources/consumer/sprite-inputs.json'):required.add(O/r['path'])
for r in prior['rawFrames']:required.add(O/r['path'])
assert all(p.is_file()for p in required)
write(D/'portable-dependencies.json',{'metadataOnlyRequired':True,'copyRules':'Unchanged promoter copies bound source/ and inputs/; metadataOnly preserves exact rawFrames paths. Host recipe repacks canonical atlas bytes from those96 preserved references. Source-owned baseline36 PNGs and108-row basis remove runtime dependency on old candidate consumer/review files.','requiredFiles':[desc(p)for p in sorted(required)],'externalRuntimeRequirements':['Python with Pillow','Node with repository Playwright and React dependencies','Background Blender5.2.2 only when optional --native-art is requested'],'missingFiles':[],'productionCopyExecuted':False})
L.mkdir(parents=True)
validation={'asset':'dock-cover','round':'round-03','stage':'Evidence-only single-blocker repair; original independent review pending','nativeValidation':'candidates/round-02/native-phase-audit.json','source':desc(O/prior['project']),'nativeSourceUnchanged':True,'metadataOnly':True,'actualCorrectedConsumer':desc(D/'consumer/consumer-evidence.json'),'nativeInputVerification':desc(D/'native-input-verification.json'),'priorIntegrity':desc(D/'inherited-integrity.json'),'portableDependencies':desc(D/'portable-dependencies.json'),'blockingReview':desc(O/'reviews/round-02.json'),'resolvedEvidenceScope':{'blockerId':'truthful-human-support-fixture','actualConsumerExecutions':36,'supportChanges':{'approach':None,'first-tread':'dock-entry','second-tread':'dock-entry'},'terminalTreadAndTransferSupport':'dock-deck','uniqueEntryPlacementConfirmed':True,'nonSupportPlacementFieldsAndFrameChoicesUnchanged':True,'changedOrders':9,'changedOrderDirections':['N'],'changedDecodedRGBAPixels':0,'newPNGsAlsoByteIdentical':36,'unchangedHumanRecords':72,'nativeRerenders':0},'inheritedUnchanged':{'nativeFrames':96,'originalAtlases':8,'envelopeMeasurementSamples':208,'sourceProject':desc(O/prior['project']),'metadataReceipt':prior['catalogMetadataOverride'],'priorDelivery':desc(O/'delivery/round-02/delivery.json'),'priorConsumer':'Unchanged1536 primary exterior-stop cases/18432 presentations reused; its old humanCases are superseded by the corrected108-row view in actualCorrectedConsumer.','previewPixels':'All22 declared aliases/21 unique preview files retained byte-exact. The36 contributing human cases have fresh equality proof; no misleading old support provenance is reused as current.'},'catalogMetadataOverride':prior['catalogMetadataOverride'],'metadataApprovalStillRequired':True,'selfApproval':False,'finalFamilyApproval':False,'editorSealedPacket':False,'productionWrites':False,'pending':['Coordinator seals a new exact round03 packet against unchanged v4 brief.','Same original judge independently approves or rejects this exact packet and unchanged metadata receipt.']}
write(L/'validation.json',validation)
files={(O/r['path']).resolve()for r in prior['resources']}
files|={p.resolve()for base in [H,D]for p in base.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
files|=required;files|={L/'validation.json',O/'delivery/round-02/delivery.json',O/'delivery/round-02/handoff.json',O/'delivery/round-02/artifact-manifest.json',O/'candidates/round-02/packet.json',O/'reviews/round-02.json',O/'reviews/round-02-independent/supplemental-manifest.json',O/'reviews/round-02-independent/support-metadata-control.json',O/'reviews/round-02-independent/support-metadata-control.mjs'}
for p in files:assert p.is_file()and p.resolve().is_relative_to(O.resolve())and p.stat().st_size<100_000_000,p
resources=[{**desc(p),'bytes':p.stat().st_size}for p in sorted(files)]
delivery={k:v for k,v in prior.items()if k not in ['resources','round','stage','createdUTC','validation','recipeScript']}
delivery.update(round='round-03',stage='Immutable evidence-only truthful-support delta; same original judge pending',createdUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),metadataOnly=True,validation=str((L/'validation.json').relative_to(O)),recipeScript=str((H/'reproduce.py').relative_to(O)),resources=resources,consumerEvidence=desc(D/'consumer/consumer-evidence.json'),supersedesHumanFixtures={'prior':desc(O/'candidates/round-02/consumer/consumer-evidence.json'),'field':'humanCases','replacement108Rows':desc(D/'consumer/consumer-evidence.json'),'scope':'Only36 original ground/first/second-tread rows were false;72 valid rows and all primary matrices reused exactly.'},revisionFrom={'packet':desc(O/'candidates/round-02/packet.json'),'review':desc(O/'reviews/round-02.json'),'singleBlockerId':'truthful-human-support-fixture'},selfApproval=False,finalFamilyApproval=False,finalCandidateSealed=False)
write(L/'delivery.json',delivery)
manifest={'asset':'dock-cover','round':'round-03','scope':'Minimal explicit new delta plus reused exact prior resource closure; enclosing manifest/handoff excluded to avoid hash cycles','files':resources+[{'path':str((L/'delivery.json').relative_to(O)),'sha256':sha(L/'delivery.json'),'bytes':(L/'delivery.json').stat().st_size}]};write(L/'artifact-manifest.json',manifest)
for r in manifest['files']:assert sha(O/r['path'])==r['sha256']
handoff={'asset':'dock-cover','round':'round-03','stage':'IMMUTABLE EVIDENCE-ONLY HANDOFF; STOP for coordinator/original judge','project':desc(O/prior['project']),'delivery':desc(L/'delivery.json'),'validation':desc(L/'validation.json'),'artifactManifest':desc(L/'artifact-manifest.json'),'consumerEvidence':desc(D/'consumer/consumer-evidence.json'),'brief':prior['brief'],'metadataReceipt':prior['catalogMetadataOverride'],'delta':{'correctedHumanCases':36,'changedOrderCases':9,'changedDecodedRGBACases':0,'newPNGBytesAlsoExact':36,'unchangedHumanCases':72,'nativeRerenders':0},'fileCount':len(manifest['files']),'largestFileBytes':max(r['bytes']for r in manifest['files']),'rehashMismatches':0,'metadataOnly':True,'selfApproval':False,'sealed':False,'productionWrites':False,'coordinatorNextStep':'Use a byte-identical object-root versioned delivery alias for unchanged sealer, unchanged v4 brief and new round03. Same original judge must decide exact new packet and exact6d88f536 metadata receipt. No edits to frozen round02/source/review/brief/art.'};write(L/'handoff.json',handoff)
print(json.dumps(handoff,indent=2))
