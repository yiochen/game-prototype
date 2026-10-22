"""One-shot immutable editor handoff. Root coordinator creates official candidate packet."""
from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parent.parent;D=B/'delivery';E=B/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (D/'manifest.json').exists(),'Do not overwrite sealed handoff'
val=json.loads((E/'native-validation.json').read_text());end=json.loads((E/'endpoint-evidence.json').read_text());consumer=json.loads((E/'consumer-results.json').read_text());seams=json.loads((E/'seam-measurements.json').read_text())
renders={d:f'candidates/round-01/static-{d}.png' for d in 'NESW'}
previews={'four-view-sheet':'candidates/round-01/four-view-sheet.png','repeated':'candidates/round-01/consumer-gray-all4.png','native-four-view':'candidates/round-01/native-all4-4x.png','repeated-light':'candidates/round-01/consumer-light-all4.png','repeated-dark':'candidates/round-01/consumer-dark-all4.png','fractional-NS':'candidates/round-01/consumer-phases-NS.png','fractional-EW':'candidates/round-01/consumer-phases-EW.png'}
info={'schemaVersion':1,'asset':'rock-shelf-middle','round':'round-01','status':'immutable-editor-handoff-awaiting-original-independent-judge','approved':False,'officialPacketOwner':'root coordinator','sourceProject':'source/round-01.blend','candidateRenders':renders,'previews':previews,'requiredReviewCoverage':'Original judge must visibly inspect all exact declared render/preview paths in the root-created packet; full technical native/consumer evidence remains hash-bound resources. Frozen REVIEW-COVERAGE and acceptance_contract.py apply unchanged.','nativeCaptures':{d:f'candidates/round-01/native-{d}-4x.png' for d in 'NESW'},'nativeStrips':{d:f'candidates/round-01/native-strip-{d}-4x.png' for d in 'NESW'},'originalLayoutAtlases':{d:f'candidates/round-01/atlases/{d}/sheet.png' for d in 'NESW'},'capture':{'logicalFrame':[192,352],'logicalRoot':[96,248],'cell':128,'nativeScale':4,'nativeFrame':[768,1408],'publishedScale':2,'publishedFrame':[384,704],'pixelAspect':[1.2206555604934692,1],'elevationDegrees':55.00797980144134,'filterSize':.5,'publish':'wholeRGBA BOX4x-to2x','clips':[{'id':'static','frames':1,'fps':12,'loop':False,'static':True,'frameOrder':[0]}]},'measured':{'bounds':val['bounds'],'finiteGroundArea':val['finiteGroundSupport']['actualNativeBottomArea'],'closedCoreTopology':val['objects'][0]['topology'],'trueEndpointResidual':end['trueEndpointResidual'],'neighborBandRayResidual':end['maxBandResidual'],'externalBlendDependencies':val['resources']['externalDependencies'],'staticActualChecks':val['staticActualChecks'],'browserErrors':consumer['errors'],'nativeOpaqueAlphaUndercoverage':{d:seams['measurements'][d]['metrics']['allNativeOpaque']['assembledAlphaLess255Pixels'] for d in 'NESW'}},'limits':['Finite area-light native-vs-independent RGB residuals are reported; no fullimage RGB identity or aesthetic approval claimed.','Only this middle candidate was authored; no family approval or production integration.'],'frozenInputs':{str(p.relative_to(B)):sha(p) for p in [B/'brief.json',B/'inputs/root-native-contract.json',B/'inputs/target.png',B/'inputs/original.png']},'reproduction':'source/README.txt'}
(D/'delivery.json').write_text(json.dumps(info,indent=2)+'\n')
files={}
for folder in [B/'source',B/'candidates/round-01',D]:
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or p.name in ['manifest.json','seal.json']:continue
  assert p.stat().st_size<100_000_000,p
  assert '__pycache__' not in p.parts and p.suffix!='.pyc',p
  files[str(p.relative_to(B))]={'sha256':sha(p),'bytes':p.stat().st_size}
manifest={'schemaVersion':1,'asset':'rock-shelf-middle','round':'round-01','purpose':'Exact editor-owned source/candidate dependency and evidence closure. Native runtime binaries externally pinned; original/target/brief remain separate frozen inputs. No reviews or production files owned.','files':files,'frozenInputs':info['frozenInputs']}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-shelf-middle','round':'round-01','status':'sealed-awaiting-original-judge','manifestSHA256':sha(D/'manifest.json'),'deliverySHA256':sha(D/'delivery.json'),'sourceSHA256':sha(B/'source/round-01.blend'),'fileCount':len(files),'totalBytes':sum(x['bytes'] for x in files.values()),'noCandidateApproval':True}
(D/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for p,record in files.items():assert sha(B/p)==record['sha256']
print(json.dumps(seal,indent=2));print('sealSHA256',sha(D/'seal.json'))
