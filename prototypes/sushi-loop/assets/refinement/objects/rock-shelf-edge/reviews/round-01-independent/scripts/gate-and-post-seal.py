from pathlib import Path
import json,hashlib,subprocess,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;EXP=BASE.parent.parent;ROOT=EXP.parents[5];TOOL=EXP.parent.parent/'tools/acceptance_contract.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=EXP/'reviews/round-01.json';manifest=BASE/'supplemental-manifest.json'
rsha=sha(review);msha=sha(manifest);tsha=sha(TOOL)
assert tsha==sha(BASE/'resources/acceptance_contract.py')
assert json.loads(review.read_text())['supplementalEvidence']['sha256']==msha
command=[sys.executable,str(TOOL),'rock-shelf-edge','--round','round-01']
result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
(BASE/'logs/final-gate.stdout.log').write_text(result.stdout)
(BASE/'logs/final-gate.stderr.log').write_text(result.stderr)
status={'asset':'rock-shelf-edge','round':'round-01','candidatePacketSHA256':sha(EXP/'candidates/round-01/packet.json'),'reviewSHA256':rsha,'supplementalManifestSHA256':msha,'toolPath':str(TOOL),'toolSHA256':tsha,'command':command,'cwd':str(ROOT),'exitCode':result.returncode,'stdoutPath':'logs/final-gate.stdout.log','stdoutSHA256':sha(BASE/'logs/final-gate.stdout.log'),'stderrPath':'logs/final-gate.stderr.log','stderrSHA256':sha(BASE/'logs/final-gate.stderr.log'),'toolUnchanged':sha(TOOL)==tsha}
(BASE/'final-gate.json').write_text(json.dumps(status,indent=2)+'\n')
assert result.returncode==0,result.stderr
assert sha(review)==rsha and sha(manifest)==msha and sha(TOOL)==tsha
for record in json.loads(manifest.read_text())['files']:assert sha(EXP/record['path'])==record['sha256'],record['path']
post={'asset':'rock-shelf-edge','round':'round-01','scope':'Candidate-specific independent approval only; no production/family/Godot approval','candidatePacketSHA256':sha(EXP/'candidates/round-01/packet.json'),'sourceProjectSHA256':sha(EXP/'source/round-01.blend'),'review':{'path':'reviews/round-01.json','sha256':rsha},'supplementalManifest':{'path':'reviews/round-01-independent/supplemental-manifest.json','sha256':msha},'finalGate':{'path':'reviews/round-01-independent/final-gate.json','sha256':sha(BASE/'final-gate.json'),'exitCode':result.returncode,'toolSHA256':tsha},'gateOutputs':[{'path':'reviews/round-01-independent/logs/final-gate.stdout.log','sha256':status['stdoutSHA256']},{'path':'reviews/round-01-independent/logs/final-gate.stderr.log','sha256':status['stderrSHA256']}],'acyclicBinding':'Supplemental manifest sealed before review; review binds that one manifest. Gate binds final review. This separate post-review seal binds review, manifest and gate; no review or manifest edits occurred after gate.','postGateEdits':False}
(BASE/'post-review-seal.json').write_text(json.dumps(post,indent=2)+'\n')
print(json.dumps({'verdict':'approve','reviewSHA256':rsha,'supplementalManifestSHA256':msha,'finalGateSHA256':sha(BASE/'final-gate.json'),'postReviewSealSHA256':sha(BASE/'post-review-seal.json'),'gateExitCode':result.returncode,'toolSHA256':tsha},indent=2))
