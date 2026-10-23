from pathlib import Path
import json,subprocess
repo=Path.cwd();run=repo/'prototypes/sushi-loop/assets/refinement';own=run/'objects/safe-passage';final=own/'final'
read=lambda p:json.loads(p.read_text())
progress=read(run/'progress.json');assert progress['completed']==101 and progress['published']==100
prior=read(run/'objects/portal-entry/final/deploy-verification.json');assert prior['commit']=='0c1076ec4ab2a61b90a6d1b869c17b948c8f3277' and prior['netlifyState']=='ready' and prior['exactCommitStatus']=='success';assert not prior['remoteSmoke']['errors']
progress['current']='safe-passage'
for row in progress['objects']:
 if row['id']=='safe-passage':row.update(stage='approved-awaiting-release101',judgeStatus='approved-round01-rootchecks-passed')
(run/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
paths=set()
for folder in [own,run/'preparation/safe-passage']:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   assert p.stat().st_size<100_000_000,str(p)
   paths.add(str(p.relative_to(repo)))
paths.update(str((run.parent/'production'/p).relative_to(repo)) for p in read(final/'promotion.json')['files'])
paths.update(str(p.relative_to(repo)) for p in [run.parent/'production/library.json',run/'progress.json',run/'objects/portal-entry/final/deploy-verification.json',run/'objects/portal-entry/final/remote-smoke.json'])
allow=final/'root-release-explicit-paths.json';paths.add(str(allow.relative_to(repo)));allow.write_text(json.dumps({'asset':'safe-passage','paths':sorted(paths)},indent=2)+'\n')
for offset in range(0,len(paths),100):subprocess.run(['git','add','-f','--',*sorted(paths)[offset:offset+100]],check=True)
with (final/'strict-staged.log').open('w') as log:subprocess.run(['python3',str(run/'tools/verify_staged_object.py'),'safe-passage','--round','round-01','--stage-missing'],stdout=log,stderr=subprocess.STDOUT,check=True)
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
(final/'root-whitespace-check.json').write_text(json.dumps({'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
print(json.dumps({'allowlistedPaths':len(paths),'strict':(final/'strict-staged.log').read_text().strip(),'whitespaceExitCode':r.returncode,'whitespaceDiagnostic':r.stdout[:7000]}))
