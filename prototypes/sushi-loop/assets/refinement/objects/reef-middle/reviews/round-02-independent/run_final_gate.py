"""Run unchanged final acceptance once against the exact independent round02 approval."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,os,subprocess
from pathlib import Path
B=Path(__file__).resolve().parent;O=B.parent.parent;R=O.parents[5]
REVIEW=O/'reviews/round-02.json';MANIFEST=B/'manifest.json'
TOOL=R/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py'
PYTHON='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
EXPECTED_REVIEW='f60dabe7a9e2ff5f0460f0e63a16fcd98a849415b21277cab7eb87ac1ec1a71e'
EXPECTED_MANIFEST='9c3a7e8efaee290aa6fd56be56d77509293af6cdf85f594742f02bfe87612d4c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def desc(p):return {'path':os.path.relpath(p,O),'relativeTo':'experiment','sha256':sha(p),'bytes':Path(p).stat().st_size}
def save(p,v):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(v,indent=2)+'\n')
assert sha(REVIEW)==EXPECTED_REVIEW and sha(MANIFEST)==EXPECTED_MANIFEST
manifest=json.loads(MANIFEST.read_text());review=json.loads(REVIEW.read_text())
assert review['verdict']=='approve' and review['blockers']==[]
for item in manifest['files']:
 p=(O/item['path']).resolve();assert sha(p)==item['sha256'];assert p.stat().st_size<100_000_000
assert sha(TOOL)==sha(B/'resources/tools/acceptance_contract.py')
argv=[PYTHON,str(TOOL.relative_to(R)),'reef-middle','--round','round-02']
result=subprocess.run(argv,cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False)
log=B/'final-gate.log';assert not log.exists();log.write_bytes(result.stdout)
assert result.returncode==0,result.stdout.decode()
output=json.loads(result.stdout);assert output['asset']=='reef-middle' and output['method']=='independent-review' and output['sha256']==EXPECTED_REVIEW
assert sha(REVIEW)==EXPECTED_REVIEW and sha(MANIFEST)==EXPECTED_MANIFEST
status=B/'final-gate.json';save(status,{'asset':'reef-middle','round':'round-02','cwd':str(R),'commandArgv':argv,'environmentOverrides':{'PYTHONDONTWRITEBYTECODE':'1'},'tool':desc(TOOL),'exitStatus':result.returncode,'stdoutAndStderr':desc(log),'reviewSHA256Before':EXPECTED_REVIEW,'reviewSHA256After':sha(REVIEW),'supplementalManifestSHA256':sha(MANIFEST),'result':'Passing candidate-bound independent-review acceptance; no derivative or production scope.'})
seal=B/'postreview-seal.json';save(seal,{'asset':'reef-middle','round':'round-02','verdict':'approve','blockerCount':0,'candidatePacketSHA256':review['candidatePacketSHA256'],'sourceSHA256':review['sourceSHA256'],'review':desc(REVIEW),'supplementalEvidence':desc(MANIFEST),'finalGateLog':desc(log),'finalGateStatus':desc(status),'unchangedAcceptanceTool':desc(TOOL),'gateRunner':desc(Path(__file__).resolve()),'supplementalManifestFilesVerified':len(manifest['files']),'scope':'Exact reef-middle round-02 only; no derivative-family/production/deployment/Godot approval.','sealPolicy':'Separate postreviewseal avoids self-hashcycles; finalreview/manifest unchanged after gate.'})
assert sha(REVIEW)==EXPECTED_REVIEW and sha(MANIFEST)==EXPECTED_MANIFEST
print(json.dumps({'review':desc(REVIEW),'manifest':desc(MANIFEST),'postreviewSeal':desc(seal),'gateExitStatus':result.returncode},indent=2))
