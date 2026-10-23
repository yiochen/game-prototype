import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=C/'packet.json';assert sha(p)=='48e08fc7f305a01eb9855350ad4a39c5487bf69da8024d832bae2d4eec8140f3';d=json.loads(p.read_text());checks=[];unique={}
for group in ['files','candidateRenders','previews']:
 for label,item in d[group].items():
  q=(C/item['path']).resolve();h=sha(q);assert h==item['sha256'],(label,q,h,item['sha256']);assert q.stat().st_size<100_000_000
  unique[str(q)]={'path':str(q),'sha256':h,'bytes':q.stat().st_size};checks.append({'group':group,'label':label,'path':item['path'],'sha256':h})
(B/'packet-integrity.json').write_text(json.dumps({'candidatePacketSHA256':sha(p),'packetRecords':checks,'uniqueFiles':list(unique.values()),'recordCount':len(checks),'uniqueCount':len(unique),'allExact':True},indent=2)+'\n')
refs=[(O/'source/round-01.blend','candidate-round01.blend'),(O/'reviews/preparation-v1/resources/canonical/reef-middle-round-02.blend','canonical-middle02.blend'),(O/'reviews/preparation-v1/resources/assembly/reef-edge-round-01.blend','approved-edge01.blend'),(O/'inputs/approved-reef-corner-v1/round-01.blend','approved-corner01.blend'),(p,'packet.json'),(O/'brief.json','brief.json'),(O/'inputs/root-native-contract.json','root-native-contract.json'),(O/'inputs/root-preparation-reconciliation-v1.json','root-reconciliation.json'),(O/'inputs/approved-reef-corner-v1/binding.json','corner-binding.json')]
for src,name in refs:shutil.copyfile(src,B/'resources'/name)
assert sha(B/'resources/candidate-round01.blend')=='afa10a0f17e610fb4f544dd40785a57d5679016982d580fe02f6fb6f66b1fb9b'
print('INPUTS EXACT',len(checks),'records',len(unique),'unique files')
