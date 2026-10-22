from pathlib import Path
import json,hashlib,copy,shutil,math
S=Path(__file__).resolve().parent;B=S.parent;F=B.parents[1];P=B/'candidates/round-01';O=B/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def relative(p):return Path(p).relative_to(B).as_posix()
assert not O.exists(),'Immutable round02 already exists'
assert sha(P/'packet.json')=='d8145dc2851683a1ea11f7ec3423e5e274f6e7d785727cc3f655f3ad6740d88d'
assert sha(P/'delivery.json')=='098edc50a864c6d968becf071e1d4b258dd3c0e32d6d4cbfa8526e20d068bc1a'
assert sha(S/'round-01.blend')=='7f724d5c7c6850f30dd3ed165f2dec09cbced174072a193561fadaecd77d8c83'
old=read(P/'delivery.json');oldmanifest=read(S/'resource-manifest-round-01.json');ledger=read(P/'native-validation.json');before={}
for r in old['resources']:
 p=B/r['path'];assert sha(p)==r['sha256'],f'Changed original resource {p}';before[r['path']]=r['sha256']
for p,h in [(B/'brief.json','ae576b24f98de165a9f30ee22a37360a3386dffa31ad5818961aa2083cd45a4f'),(B/'inputs/root-native-contract.json','104576383234ff2eef32324d4fcfaaaf78cc559159c91fffab4401e75974460b'),(B/'inputs/root-preparation-reconciliation-v1.json','44225b8a25b133cac4108c007c4bc3c4b564f2bf1ab82fed376b5d1395ba1be3')]:assert sha(p)==h
assert len(ledger['views'])==4
for v in ledger['views']:
 assert v['sourceSHA256']==sha(S/'round-01.blend')
 expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[v['direction']]
 assert abs(math.atan2(math.sin(v['rootRotationZ']-expected),math.cos(v['rootRotationZ']-expected)))<1e-4
O.mkdir();res=O/'resources';res.mkdir()
rootprep=F/'preparation/wreck-corner';checker=F/'tools/audit_directions.py'
for src,dst in [(rootprep/'unsubmitted-round01-direction-preflight.json',res/'unsubmitted-round01-direction-preflight.json'),(rootprep/'editor-round-02-evidence-dispatch.txt',res/'editor-round-02-evidence-dispatch.txt'),(checker,res/'audit_directions.py')]:shutil.copyfile(src,dst)
# Supported direction target: exact existing measured views, with complete full geometry preserved elsewhere.
thin={'asset':'wreck-corner','round':'round-02','schema':'measured-native-views-with-bound-complete-ledger-v1','evidenceOnly':True,'sourceSHA256':ledger['sourceSHA256'],'blender':ledger['blender'],'buildHash':ledger['buildHash'],'views':copy.deepcopy(ledger['views']),'completeGeometryLedger':{'path':'candidates/round-01/native-validation.json','sha256':sha(P/'native-validation.json'),'pathBase':'object-root','retention':'Unchanged full geometry, finite fields/support, materials, world/lights, camera, provenance and all measured facing data. No evidence discarded.'},'originatingUnsubmittedPacket':{'path':'candidates/round-01/packet.json','sha256':sha(P/'packet.json')},'schemaCorrection':'The direction checker consumes the supported actual views list. The full original ledger retains its richer facing-to-object nativeGeometryMeasurements mapping without presenting that incompatible recognized-key shape in this thin target.','approval':'No prior candidate review exists. No new rendering, art change or approval.'}
write(O/'native-validation.json',thin)
assert thin['views']==ledger['views'] and 'nativeGeometryMeasurements' not in thin
wrapper=read(P/'validation.json');wrapper.update(round='round-02',nativeValidation='candidates/round-02/native-validation.json',evidenceOnly=True);wrapper['evidence']['unchangedCompleteNativeLedger']={'path':'candidates/round-01/native-validation.json','sha256':sha(P/'native-validation.json')};wrapper['packagingCorrection']={'originalPacket':'candidates/round-01/packet.json','originalPacketSHA256':sha(P/'packet.json'),'preflight':'candidates/round-02/resources/unsubmitted-round01-direction-preflight.json','gate':'Exact unchanged audit_directions.py; ROOT will run after new sealing','newMeasurements':False,'artChanges':False};write(O/'validation.json',wrapper)
# Every new-round candidate render/preview aliases the exact old bytes. No review coverage reuse is claimed.
coverage=[]
for kind,key in [('hero','heroes'),('preview','previews')]:
 for name,path in old[key].items():coverage.append({'kind':kind,'name':name,'oldPath':path,'newPath':path,'sha256':sha(B/path),'byteIdenticalAlias':True})
media=[{'oldPath':r['path'],'newPath':r['path'],'sha256':r['sha256'],'byteIdenticalAlias':True} for r in old['resources'] if Path(r['path']).suffix.lower() in ['.png','.jpg','.jpeg','.webp','.gif']]
write(O/'visual-coverage-mapping.json',{'pathBase':'object-root','oldRound':'round-01','newRound':'round-02','oldRoundStatus':'Unsubmitted root packaging preflight failure before any candidate review; no judge rejection or approval','priorJudgeCandidateCoverageExists':False,'judgeRequirement':'Original judge must directly inspect every exact02 hero and declared preview afresh. The mapping proves unchanged bytes only.','declaredHeroAndPreviewAliases':coverage,'allUnchangedMedia':media,'sourceAlias':{'oldPath':old['project'],'newPath':old['project'],'sha256':sha(B/old['project'])},'noArtOperation':True})
write(O/'evidence-change-record.json',{'asset':'wreck-corner','round':'round-02','scope':'Evidence schema only','previousPacket':{'path':'candidates/round-01/packet.json','sha256':sha(P/'packet.json')},'previousCompleteLedger':{'path':'candidates/round-01/native-validation.json','sha256':sha(P/'native-validation.json')},'previousResourceManifest':{'path':'source/resource-manifest-round-01.json','sha256':sha(S/'resource-manifest-round-01.json')},'previousDelivery':{'path':'candidates/round-01/delivery.json','sha256':sha(P/'delivery.json')},'checker':{'originalPath':'../../tools/audit_directions.py','frozenCopy':'candidates/round-02/resources/audit_directions.py','sha256':sha(checker)},'preflight':{'originalPath':'../../preparation/wreck-corner/unsubmitted-round01-direction-preflight.json','frozenCopy':'candidates/round-02/resources/unsubmitted-round01-direction-preflight.json','sha256':sha(rootprep/'unsubmitted-round01-direction-preflight.json')},'reusedViewsExactlyEqualToOriginal':thin['views']==ledger['views'],'originalResourcesVerified':len(before),'notes':['Existing actual four-view measurements are copied exactly; no transforms inferred or fabricated.','Complete original ledger and original packet remain directly bound resources.','No art/source/target/criteria/brief/helper mutation, re-render or review occurred.','ROOT seals and runs the unchanged direction gate before original judge review.']})
# Explicit private closure references exact old bytes instead of copying native/media evidence.
manifest=S/'resource-manifest-round-02.json';delivery=O/'delivery.json';paths={Path(r['path']) for r in old['resources']}
paths.update([Path('candidates/round-01/delivery.json'),Path('candidates/round-01/packet.json'),Path('source/prepare-evidence-round-02.py')])
paths.update(p.relative_to(B) for p in O.rglob('*') if p.is_file())
files=[]
for rel in sorted(paths):
 p=B/rel;assert p.is_file();assert '__pycache__' not in p.parts;assert p.stat().st_size<100_000_000
 files.append({'path':rel.as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
write(manifest,{'asset':'wreck-corner','round':'round-02','evidenceOnly':True,'pathBase':'object-root','candidateProjectSHA256':sha(S/'round-01.blend'),'files':files,'scope':'Thin supported measured-facing target plus exact unchanged source/all media/proofs and original packet/resource manifest/preflight; no runtime trees','externalAssetResources':[],'excludesToAvoidHashCycle':['source/resource-manifest-round-02.json','candidates/round-02/delivery.json'],'approval':'No candidate review yet; original judge will inspect exact02 media afresh'})
deliver=copy.deepcopy(old);deliver.update(round='round-02',validation='candidates/round-02/validation.json',metadataOnly=True,evidenceOnly=True,resourceManifest={'path':relative(manifest),'sha256':sha(manifest),'pathBase':'object-root'});deliver['resources']=[{'path':r['path'],'sha256':r['sha256']} for r in files]+[{'path':relative(manifest),'sha256':sha(manifest)}];deliver['changeNotes']=['Evidence-only correction: supported nativeValidation target contains the exact four existing measured view records.','The unchanged complete original native geometry/field/support/material/lighting ledger remains hash-bound.','Source, all art/atlases/native/consumer/screenshots and visual previews reuse exactly the round01 bytes. No re-render.'];deliver['previousUnsubmittedPacket']={'path':'candidates/round-01/packet.json','sha256':sha(P/'packet.json')};deliver['visualCoverageMapping']={'path':'candidates/round-02/visual-coverage-mapping.json','sha256':sha(O/'visual-coverage-mapping.json'),'freshJudgeInspectionRequired':True};write(delivery,deliver)
for rel,h in before.items():assert sha(B/rel)==h,f'Original resource changed during evidence packaging: {rel}'
assert sha(P/'packet.json')=='d8145dc2851683a1ea11f7ec3423e5e274f6e7d785727cc3f655f3ad6740d88d'
for p in [Path(__file__),manifest]+[p for p in O.rglob('*') if p.is_file()]:p.chmod(0o444)
print(json.dumps({'delivery':str(delivery),'deliverySHA256':sha(delivery),'unchangedProject':str(S/'round-01.blend'),'sourceSHA256':sha(S/'round-01.blend'),'resourceManifest':str(manifest),'resourceManifestSHA256':sha(manifest),'thinNativeValidationSHA256':sha(O/'native-validation.json'),'retainedOriginalLedgerSHA256':sha(P/'native-validation.json'),'retainedOriginalPacketSHA256':sha(P/'packet.json'),'boundResourceFiles':len(files),'newNativeOrMediaRenders':0,'newFilesMode':'0444','packetSealing':'ROOT pending; unchanged direction gate not run here'},indent=2))
