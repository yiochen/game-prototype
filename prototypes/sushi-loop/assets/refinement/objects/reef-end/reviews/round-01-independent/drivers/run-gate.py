import sys
sys.dont_write_bytecode=True
import subprocess,json,hashlib,os
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B.parents[1];REF=O.parents[1];REPO=REF.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
command=['python3','-B','prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py','reef-end','--round','round-01'];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');result=subprocess.run(command,cwd=REPO,env=env,text=True,capture_output=True)
(B/'final-gate.stdout.txt').write_text(result.stdout);(B/'final-gate.stderr.txt').write_text(result.stderr)
(B/'final-gate.json').write_text(json.dumps({'command':command,'workingDirectory':str(REPO),'exitCode':result.returncode,'checker':{'path':'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py','sha256':sha(REF/'tools/acceptance_contract.py'),'unchangedCopySHA256':sha(B/'resources/acceptance_contract.py')},'reviewSHA256':sha(O/'reviews/round-01.json'),'candidatePacketSHA256':sha(O/'candidates/round-01/packet.json'),'driver':{'path':'reviews/round-01-independent/drivers/run-gate.py','sha256':sha(Path(__file__))},'stdoutSHA256':sha(B/'final-gate.stdout.txt'),'stderrSHA256':sha(B/'final-gate.stderr.txt'),'acyclicScope':'Postreview gate receipt is outside supplementalmanifest and bound by postreviewseal.'},indent=2)+'\n')
print(result.stdout,end='');print('EXIT',result.returncode)
assert result.returncode==0,result.stderr
