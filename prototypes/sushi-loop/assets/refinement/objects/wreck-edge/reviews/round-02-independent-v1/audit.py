from pathlib import Path
import json,hashlib,math
HERE=Path(__file__).resolve().parent;RES=HERE/'resources';OBJ=HERE.parent.parent;NEW=OBJ/'candidates/round-02';OLD=OBJ/'candidates/round-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
packet=read(NEW/'packet.json');prior=read(OLD/'packet.json');review=read(OBJ/'reviews/round-01.json');mapping=read(NEW/'art-identity-and-coverage.json');checks=[]
assert sha(NEW/'packet.json')=='7fe4e36723fe87bea1a94d12f9b85e62b4cafffcc0e34b814b3298e8866aaae1'
assert sha(OBJ/'reviews/round-01.json')=='6582ca696607c85af4e49b926532cbe7babf6252126bdc73b38c98014fa0a1f7'
assert sha(NEW/'art-identity-and-coverage.json')=='81fcb1a6d0c8d3dda0d70903ff9dc5048f8dce6063a09da1a64dc9aeadab12aa'
for group in ['files','candidateRenders','previews']:
 for name,item in packet[group].items():
  p=(NEW/item['path']).resolve();assert sha(p)==item['sha256'];checks.append({'group':group,'name':name,'path':str(p.relative_to(OBJ)) if p.is_relative_to(OBJ) else str(p),'sha256':item['sha256']})
assert packet['qualityCriteria']==prior['qualityCriteria'] and packet['capture']==prior['capture'] and packet['style']==prior['style']
for p,expected in [('brief.json','5263e57dd56796644f92669499e08db67f72abf2c08a32648412f711a910144b'),('inputs/root-native-contract.json','6219699bad1dd1c0926209c5c2316d0bfbc961e2b585d00141c1243325c6f0d3'),('inputs/root-preparation-reconciliation-v1.json','caa00add74ac5cdb2abd414b14503e032986fdb9d90ef855e648afc76d87c60a')]:assert sha(OBJ/p)==expected
assert sha(OBJ/'source/round-01.blend')==sha(OBJ/'source/round-02.blend')=='a7f8357632d42d3f5113f7ee3b423634bdd834e0d3cbfb9a058ea513767a1498'
identity=[]
for group in ['candidateRenders','previews']:
 assert set(packet[group])==set(prior[group])
 for name,item in packet[group].items():
  old=prior[group][name];p=(NEW/item['path']).resolve();q=(OLD/old['path']).resolve();assert p==q and sha(p)==item['sha256']==old['sha256'];assert old['path'] in review['inspectedFiles']
  rows=[m for m in mapping['renderAndPreviewCoverageMapping'] if m['kind']==group and m['name']==name];assert len(rows)==1;m=rows[0]
  assert m['oldPacketRelativePath']==old['path'] and m['newPacketRelativePath']==item['path'] and m['objectRelativePath']==str(p.relative_to(OBJ)) and m['sha256']==sha(p)
  identity.append({'kind':group,'name':name,'newExactPacketPath':item['path'],'priorDirectlyInspectedPath':old['path'],'sameResolvedFile':str(p.relative_to(OBJ)),'sha256':sha(p),'inspectionReuse':'Verified exact same bytes and actual file; original judge direct round01 inspection remains applicable.'})
assert len(identity)==24
for m in mapping['allOldPNGInputs']:
 p=Path(m['path']) if Path(m['path']).is_absolute() else OBJ/m['path'];assert sha(p)==m['sha256']
# Verify actual original-judge evidence and source measurements, not editor ratings.
post=read(OBJ/'reviews/round-01-independent-v1/postseal.json')
for item in post['files']:assert sha(OBJ/item['path'])==item['sha256']
for name in ['supplemental-manifest.json','supplemental-manifest-v2.json']:
 for item in read(OBJ/'reviews/round-01-independent-v1'/name)['files']:assert sha(OBJ/item['path'])==item['sha256']
old_native=read(OLD/'native-validation.json');native=read(NEW/'native-validation.json');assert all(native[k]==v for k,v in old_native.items());assert set(native)-set(old_native)=={'captureRecords','measuredCaptureRecordsProvenance'}
ledger=read(OLD/'capture-records.json');outer=read(OLD/'validation.json');new_outer=read(NEW/'validation.json');assert native['captureRecords']==ledger['captureRecords']==outer['captureRecords']==new_outer['captureRecords']
proof=native['measuredCaptureRecordsProvenance'];assert proof['path']=='candidates/round-01/capture-records.json' and proof['sha256']==sha(OLD/'capture-records.json') and proof['outerWrapperSHA256']==sha(OLD/'validation.json')
assert (OBJ/new_outer['nativeValidation']).resolve()==(NEW/'native-validation.json').resolve()
bound={(NEW/v['path']).resolve():v['sha256'] for v in packet['files'].values()};assert bound[(NEW/'native-validation.json').resolve()]==sha(NEW/'native-validation.json')
own={r['direction']:r for r in read(OBJ/'reviews/round-01-independent-v1/own-capture-records.json')};directions=[]
for record in native['captureRecords']:
 d=record['direction'];assert record['sourceSHA256']==proof['actualSourceSHA256']==sha(OBJ/'source/round-02.blend');assert sha(OLD/record['path'])==record['sha256'];assert record['actualRootMatrix']==own[d]['rootMatrix'] and record['rootRotationZ']==own[d]['rootRotationZ']
 assert record['camera']['camera']['worldMatrix']==own[d]['cameraMatrix'] and record['camera']['calibration']==own[d]['calibration'];assert record['nativeFrame']==own[d]['nativeFrame']==[384,704]
 want={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d];angle=record['rootRotationZ'];assert abs(math.atan2(math.sin(angle-want),math.cos(angle-want)))<1e-6
 directions.append({'direction':d,'sourceSHA256':record['sourceSHA256'],'actualRootMatrix':record['actualRootMatrix'],'rootRotationZ':angle,'exactOriginalMeasuredRecord':True,'exactOwnSavedSourceMeasurementMatch':True,'originalNativePNG':str((OLD/record['path']).relative_to(OBJ)),'sha256':record['sha256']})
assert len(directions)==4 and {r['direction'] for r in directions}==set('NESW')
for name in ['audit_directions.py','acceptance_contract.py']:
 assert sha(RES/name)==sha(OBJ.parent.parent/'tools'/name)==sha(OBJ/'reviews/round-01-independent-v1/resources'/name)
for name,h in [('world-sprite-raster.js','570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'),('sprite-layout.js','099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65')]:assert sha(OBJ/'source/consumer'/name)==h
out={'candidatePacketSHA256':sha(NEW/'packet.json'),'allPacketDescriptorsVerified':checks,'uniqueBoundFiles':len(set(x['path'] for x in checks)),'coverageMappings':identity,'sourceBytesUnchanged':True,'frozenCriteriaCaptureStyleAndHelpersUnchanged':True,'priorJudgeEvidenceManifestsVerified':True,'nativeLedgerOriginalFieldsUnchanged':True,'onlyNativeLedgerAdditions':['captureRecords','measuredCaptureRecordsProvenance'],'supportedMeasuredRecords':directions,'reason':'The new nativeValidation target is exact packet-bound and now directly contains the actual original all4 measured records. Every record is unchanged from the original native ledger and outer wrapper and matches the original judge own saved-source matrix/camera/calibration measurement. No angle or render is invented.','scope':'Evidence-only same art; direct prior visual/native judgments and disclosed residuals remain applicable after exact hash identity checks. No new style criterion, source edit, regeneration or family approval.'}
(HERE/'independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'uniqueBoundFiles':out['uniqueBoundFiles'],'visualMappings':len(identity),'actualMeasuredDirections':len(directions),'compatibleNativeSchema':True},indent=2))
