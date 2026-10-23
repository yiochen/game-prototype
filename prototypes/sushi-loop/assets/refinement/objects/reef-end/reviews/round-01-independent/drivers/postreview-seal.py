import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,subprocess,datetime
B=Path(__file__).resolve().parents[1];O=B.parents[1];T=O.parents[1]/'tools/acceptance_contract.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=O/'reviews/round-01.json';manifest=B/'manifest.json';r=json.loads(review.read_text());m=json.loads(manifest.read_text());assert sha(manifest)==r['supplementalEvidence']['sha256']
for f in m['files']:assert sha(O/f['path'])==f['sha256']
assert sha(T)==sha(B/'resources/acceptance_contract.py')
gate=json.loads((B/'final-gate.json').read_text());assert gate['exitCode']==0;assert gate['reviewSHA256']==sha(review)
seal={'candidatePacketSHA256':r['candidatePacketSHA256'],'review':{'path':'reviews/round-01.json','sha256':sha(review)},'supplementalEvidence':{'path':'reviews/round-01-independent/manifest.json','sha256':sha(manifest),'filesVerified':len(m['files'])},'gate':{'path':'reviews/round-01-independent/final-gate.json','sha256':sha(B/'final-gate.json'),'stdoutSHA256':sha(B/'final-gate.stdout.txt'),'stderrSHA256':sha(B/'final-gate.stderr.txt'),'checkerSHA256':sha(T),'exitCode':0},'acyclicOrder':'manifest excluding review/gate/postseal → final review references manifest → unchanged acceptance gate references final review → this postreviewseal binds all','scope':'Exact reef-end round01 approval only. No source/art/target/brief/production/Git/device/liveBlender edits. STOP.'}
(B/'postreview-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for p in B.rglob('*'):
 if p.is_file():p.chmod(0o444)
review.chmod(0o444)
print(json.dumps({'verdict':r['verdict'],'reviewSHA256':sha(review),'manifestSHA256':sha(manifest),'postsealSHA256':sha(B/'postreview-seal.json'),'filesVerified':len(m['files']),'acceptance':'passed unchanged','status':'IMMUTABLE; STOP'}))
