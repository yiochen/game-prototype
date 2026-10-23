from pathlib import Path
import json,hashlib,shutil,ast,os
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (HERE/'seal.json').exists(),'Preparation already sealed; use a new version'
expected={'inputs/original.png':'f08a7ffb694aa6c7da21c55d53624485174a7e5c17f43ad556f7a53e5500aa29','inputs/target.png':'b0f3a6a09d5fcac235009e800b28c9c71d4bcffeab8e9ab35e4b6036e970cad6','../../style/warm-soft-reference.png':'02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15','../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','../../backups/b1765262bfa897ad-sushi-loop-world-library.blend':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'}
for name,digest in expected.items():assert sha(OBJ/name)==digest,(name,'raw input changed')
for p in HERE.rglob('*.py'):ast.parse(p.read_text())
for p in HERE.rglob('*.json'):json.loads(p.read_text())
for name in ['initial.json','proposedcriteria.json','source-contract-proposal.json']:
    src=OBJ/'reviews'/name;json.loads(src.read_text());dest=HERE/'resources/instructions'/name
    assert not dest.exists();shutil.copy2(src,dest)
shutil.copy2(OBJ/'reviews/proposedcriteria.json',OBJ/'reviews/criteria.json')
helper=HERE/'resources/helpers';helper.mkdir(exist_ok=True)
for src in list(HERE.glob('*.py'))+list(HERE.glob('*.mjs')):
    shutil.copy2(src,helper/src.name)
files=[]
for p in sorted(HERE.rglob('*')):
    if not p.is_file():continue
    assert '__pycache__' not in p.parts
    assert p.stat().st_size<100_000_000,p
    files.append({'path':str(p.relative_to(OBJ)),'sha256':sha(p),'size':p.stat().st_size})
for name in ['initial.json','proposedcriteria.json','criteria.json','source-contract-proposal.json']:
    p=OBJ/'reviews'/name;files.append({'path':str(p.relative_to(OBJ)),'sha256':sha(p),'size':p.stat().st_size})
manifest={'asset':'decor-background-rock','stage':'preparation only; no candidate approval','version':1,'pathBase':'object root','files':files,'externalOriginalIntegrity':[{'path':name,'sha256':digest} for name,digest in expected.items()],'checks':{'allFilesUnder100MB':True,'noPycacheOrRuntimeTrees':True,'sourceTargetBackupPreserved':True,'actualBothBrowserModesRetained':True},'rootReconciliationRequired':True}
(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'decor-background-rock','stage':'frozen independent preparation only','pathBase':'object root','manifest':{'path':str((HERE/'manifest.json').relative_to(OBJ)),'sha256':sha(HERE/'manifest.json')},'proposedCriteria':{'path':'reviews/proposedcriteria.json','sha256':sha(OBJ/'reviews/proposedcriteria.json')},'sourceContractProposal':{'path':'reviews/source-contract-proposal.json','sha256':sha(OBJ/'reviews/source-contract-proposal.json')},'initial':{'path':'reviews/initial.json','sha256':sha(OBJ/'reviews/initial.json')},'fileCount':len(files),'totalBoundBytes':sum(f['size'] for f in files),'stop':'Root must reconcile/freeze before a fresh editor independent initial assessment and construction. No candidate, approval, family approval or production authorization.'}
(HERE/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for rec in files:os.chmod(OBJ/rec['path'],0o444)
os.chmod(HERE/'manifest.json',0o444);os.chmod(HERE/'seal.json',0o444)
for rec in files:assert sha(OBJ/rec['path'])==rec['sha256']
assert sha(HERE/'manifest.json')==seal['manifest']['sha256']
print(json.dumps(seal,indent=2));print('SEAL_SHA256',sha(HERE/'seal.json'))
