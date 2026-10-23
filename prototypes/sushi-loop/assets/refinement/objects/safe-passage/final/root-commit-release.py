from pathlib import Path
import json,hashlib,subprocess
repo=Path.cwd();run=repo/'prototypes/sushi-loop/assets/refinement';own=run/'objects/safe-passage';F=own/'final';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tests=(F/'catalog-tests.log').read_text();assert '\n# pass 5\n' in tests and '\n# fail 0\n' in tests
smoke=read(F/'local-smoke.json');assert not smoke['errors'] and len(smoke['viewports'])==2 and all(x['status']=='approved' for x in smoke['viewports'])
production=run.parent/'production';promotion=read(F/'promotion.json')
assert all(promotion['files'][x['source']]==x['atlasSHA256'] for x in smoke['viewports'])
assert 'built in' in (F/'build.log').read_text()
assert read(F/'root-review-verification.json')['unchangedHelperHashesVerified']
assert read(F/'root-whitespace-check.json')['exitCode']==0
proof={'asset':'safe-passage','round':'round-01','approvedPacketSHA256':promotion['candidatePacketSHA256'],'reviewSHA256':promotion['reviewSHA256'],'strictArtifacts':1037,'catalogTests':{'passed':5,'failed':0},'build':'passed','localSmoke':smoke,'publishScope':'PR37 preview only','previousExactLiveGate':'portal-entry0c1076ec4ab2a61b90a6d1b869c17b948c8f3277 READY/exactGHsuccess/bothservedhashesPASS','unchangedAcceptanceSHA256':sha(run/'tools/acceptance_contract.py'),'whitespacePolicy':'Every staged path passes unchanged whitespace check; no exceptions.','rootVisualSpotcheck':'Directly viewed four-view-sheet before review; no aesthetic conclusions supplied to independent judge.'}
(F/'root-release-verification.json').write_text(json.dumps(proof,indent=2)+'\n')
subprocess.run(['python3',str(F/'root-stage-release.py')],check=True)
allow=set(read(F/'root-release-explicit-paths.json')['paths'])
for offset in range(0,len(allow),100):subprocess.run(['git','add','-f','--',*sorted(allow)[offset:offset+100]],check=True)
staged=set(subprocess.run(['git','diff','--cached','--name-only','-z'],check=True,capture_output=True).stdout.decode().split('\0'))-{''}
assert staged<=allow,sorted(staged-allow)
changed=set(subprocess.run(['git','diff','--name-only','-z'],check=True,capture_output=True).stdout.decode().split('\0'))-{''}
assert not changed&staged,sorted(changed&staged)
subprocess.run(['git','diff','--cached','--check'],check=True,capture_output=True)
p=subprocess.run(['git','commit','-m','Refine native safe passage stones and rooted foliage'],capture_output=True,text=True)
if p.returncode:print(p.stdout,p.stderr)
p.check_returncode();head=subprocess.run(['git','rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip();print('COMMIT',head,'changedPaths',len(staged),flush=True)
p=subprocess.run(['git','-c','push.useBitmaps=false','-c','pack.allowPackReuse=false','push','origin','codex/warm-soft-catalog'],capture_output=True,text=True);print('PUSH',p.returncode,p.stdout[-500:],p.stderr[-1200:],flush=True);p.check_returncode()
