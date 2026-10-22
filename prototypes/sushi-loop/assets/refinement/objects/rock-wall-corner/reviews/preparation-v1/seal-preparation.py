from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent;REV=OUT.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in json.loads((OUT/'resource-manifest.json').read_text())['resources']:
 p=REV/r['snapshotPath'];assert sha(p)==r['sha256'],str(p)
files=[]
for p in sorted(REV.rglob('*')):
 if not p.is_file() or p.name in ['preparation-manifest.json','preparation-seal.json']:continue
 assert p.stat().st_size<100_000_000,str(p)
 files.append({'path':str(p.relative_to(REV)),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'schemaVersion':1,'asset':'rock-wall-corner','stage':'independent preparation only; no candidate approval','root':'reviews/','files':files,'filesCount':len(files),'totalBytes':sum(x['bytes'] for x in files),'maxFileBytes':max(x['bytes'] for x in files)}
(OUT/'preparation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'preparation-seal.json').write_text(json.dumps({'asset':'rock-wall-corner','stage':'preparation-complete-awaiting-root-freeze','candidateApproval':False,'manifest':'preparation-manifest.json','manifestSHA256':sha(OUT/'preparation-manifest.json'),'filesCount':len(files),'totalBytes':manifest['totalBytes'],'maxFileBytes':manifest['maxFileBytes'],'criteriaFile':'../proposedcriteria.json','criteriaSHA256':sha(REV/'proposedcriteria.json'),'sourceContract':'../source-contract-proposal.json','sourceContractSHA256':sha(REV/'source-contract-proposal.json'),'scope':'New own reviews/ files only. Original source/backup/target checked unchanged. No native model saved, production writes, Git, live Blender, device operations, extra agents or candidate/final approval.'},indent=2)+'\n')
print((OUT/'preparation-seal.json').read_text())
