"""Prepare immutable editor delivery/manifest; root seals packet and judge reviews."""
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;BASE=RES.parent;EXP=BASE.parent;OUT=EXP/'candidates/round-02';D=EXP/'delivery/round-02'
D.mkdir(parents=True,exist_ok=True)
if (D/'manifest.json').exists():raise SystemExit('Editor manifest exists: do not overwrite immutable handoff')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def record(p):return {'path':p.relative_to(EXP).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
brief=EXP/'brief-v2-native-normal-equivalence.json';contract=EXP/'inputs/root-native-contract-v2-rendered-normal-equivalence.json';review=EXP/'reviews/round-01.json';project=BASE/'round-02.blend'
assert sha(brief)=='7c04c79d1634b3be2799b39e32709f3fa5982cc9299e54ab209901212f30c51f'
assert sha(contract)=='4c03fc7161a5730e1d52ee32d68ae9970187457ec59426b61c4f854a368824be'
assert sha(review)=='754d3afa0c5917e1822963e6e303cf2b368cbd2a0218ebc5152d81d38faf4056'
assert sha(BASE/'dependencies/canonical-middle.blend')=='3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422'
validation=json.loads((OUT/'validation.json').read_text());assert validation['sourceSHA256']==sha(project)
assert validation['topology']['boundaryEdges']==validation['topology']['nonmanifoldEdges']==validation['topology']['zeroAreaFaces']==0
assert validation['briefSHA256']==sha(brief) and validation['contractSHA256']==sha(contract)
fields=json.loads((OUT/'collar-fields.json').read_text())['summary'];assert all(v['maxAlbedoError']<1e-6 and v['maxNormalError']<1e-6 for v in fields.values())
consumer=json.loads((OUT/'evidence/consumer/results.json').read_text());assert not consumer['pageErrors']
assert consumer['currentHelpers']=={'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
old=json.loads((EXP/'delivery/round-01/manifest.json').read_text())
assert all((EXP/r['path']).is_file() and sha(EXP/r['path'])==r['sha256'] for r in old['files'])
previews={'four-view-sheet':'four-view-native.png','repeated':'consumer-L-all4.png','single-use-sizes':'single-use-sizes.png','isolated-W':'consumer-W-all4.png','isolated-N':'consumer-N-all4.png','consumer-phases':'consumer-phases-all4.png','native-vs-consumer':'native-vs-consumer-all4.png','cap-field':'cap-field-sheet.png','collar-shader-normal-all-roots':'collar-shader-normal-all-roots.png','collar-shader-albedo-all-roots':'collar-shader-albedo-all-roots.png','exposed-side-revision':'exposed-side-revision.png'}
sourcefiles=[p for root in [RES,BASE/'dependencies'] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[project,BASE/'dependency-closure.json']
delivery={
 'asset':'rock-shelf-corner','round':'round-02','status':'editor handoff; root packet and original independent judge pending',
 'brief':record(brief),'nativeContract':record(contract),'project':'source/round-02.blend','recipeScript':'source/round-02-resources/reproduce.py','validation':'candidates/round-02/validation.json',
 'nativeRecords':{'camera':'candidates/round-02/published-camera.json','assetRecord':'candidates/round-02/assetRecord.json','rig':'candidates/round-02/rig.json'},
 'heroes':{d:f'candidates/round-02/frames/static/{d}/000.png' for d in 'NESW'},
 'previews':{name:'candidates/round-02/'+path for name,path in previews.items()},
 'rawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-02/frames/static/{d}/000.png'} for d in 'NESW'],
 'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-02/native/static/{d}/000.png'} for d in 'NESW'],
 'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-02/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW'],
 'resourcePathBase':'object root','resources':[record(p) for p in sorted(set(sourcefiles))],
 'canonicalDependency':{'source':record(BASE/'dependencies/canonical-middle.blend'),'packet':record(EXP/'reviews/preparation-v1/resources/canonical/packet.json')},
 'publication':'Native4x768x1408/filter.5; complete-frame BOX2x384x704. No fitting, overlap, per-view grade, runtime change, RGB or alpha repair.',
 'normalImplementation':'Canonical .025 collar triangles retain original affine CORNER vectors; Object-to-World VECTOR then post-interpolation Normalize into cloned canonical body BSDF Normal. Encoded geometric normals separately reported. Canonical cap behavior retained with N transverse=-localX.',
 'consumer':{'browser':consumer['browser'],'dpr':consumer['devicePixelRatio'],'caseCount':len(consumer['cases']),'helpers':consumer['currentHelpers'],'evidence':'candidates/round-02/evidence/consumer/results.json'},
 'revision':{'priorReview':record(review),'priorPacketSHA256':'5e2fd306c45d9e97cf18b40c70d0b7bc373cb018648fb736d28fc6d0e3d56d55','method':'Native fitted side stones in two staggered courses; broad physical inset joints, coherent blue per-stone albedo and a normal field following the real relief. Crown function and embedded accents retained.','priorVisibleReference':'source/round-02-resources/prior-reference/identities.json','freshEvidence':'Every round02 hero, native L/W/N join, 276 browser cases, cap and all-root shader controls is newly captured from round02. Prior art appears only in explicitly labeled comparison columns.','oldImmutableRecordsVerified':len(old['files'])},
 'reviewLimit':'No editor approval or packet seal. Original independent judge decides visual outcome; root controls production/Git/publication.'
}
for path in [*delivery['heroes'].values(),*delivery['previews'].values()]:assert (EXP/path).is_file()
dump(D/'delivery.json',delivery)
dump(D/'commands.json',{'actualReproductionRecord':record(OUT/'reproduction-commands.json'),'entryPoint':'source/round-02-resources/reproduce.py','note':'Actual commands and logs are bound in the reproduction record. Reproduce only in an unsealed private copy. No editor packet seal or approval issued.'})
files=sourcefiles+[p for root in [OUT,D] for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['manifest.json','seal.json','packet.json']]
files.extend([brief,contract,EXP/'inputs/root-native-contract.json',EXP/'reviews/preparation-v1/resources/canonical/packet.json',review])
records=[record(p) for p in sorted(set(files))];assert all(r['bytes']<100_000_000 for r in records)
dump(D/'manifest.json',{'asset':'rock-shelf-corner','round':'round-02','pathBase':'object root','status':'immutable editor evidence identity; root packet and original independent judge pending','projectSHA256':sha(project),'briefSHA256':sha(brief),'contractSHA256':sha(contract),'files':records})
print(json.dumps({'delivery':str(D/'delivery.json'),'sourceSHA256':sha(project),'manifestSHA256':sha(D/'manifest.json'),'files':len(records),'bytes':sum(r['bytes'] for r in records)},indent=2))
