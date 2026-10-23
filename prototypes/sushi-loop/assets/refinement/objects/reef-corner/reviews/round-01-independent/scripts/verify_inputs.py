from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parents[1];obj=p.parents[1];run=obj/'candidates/round-01';packet=run/'packet.json'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
a=json.loads(packet.read_text());assert sha(packet)=='969ab83edd7a8d615fe7284bb7c979a293a5bfde0a6d0b50abe62ac16068f599'
records=[]
for group in ['files','candidateRenders','previews']:
 for key,r in a[group].items():
  f=(run/r['path']).resolve();assert sha(f)==r['sha256'],(group,key,f)
  records.append({'group':group,'key':key,'path':str(f.relative_to(obj)),'sha256':r['sha256'],'bytes':f.stat().st_size})
h=run/'editor-handoff-manifest.json';b=json.loads(h.read_text());print('handoff keys',list(b));print('handoff first',b['files'][0]);
assert sha(h)=='2123217242ac0c833da75eb90a458f48a8b553ae21be45a4144d73e3a1428876'
for rec in b['files']:
 path=rec.get('path');f=obj/path
 if not f.exists():f=run/path
 assert f.exists() and sha(f)==rec['sha256'],(rec,f)
(p/'evidence/input-integrity.json').write_text(json.dumps({'candidatePacketSHA256':sha(packet),'packetReferencesVerified':len(records),'references':records,'handoffSHA256':sha(h),'handoffFilesVerified':len(b['files']),'briefSHA256':sha(obj/'brief.json'),'nativeContractSHA256':sha(obj/'inputs/root-native-contract.json'),'acceptanceContractSHA256':sha(p/'resources/acceptance_contract.py')},indent=2)+'\n')
print('Verified',len(records),'packet references and',len(b['files']),'handoff files')
