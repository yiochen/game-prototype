from pathlib import Path
import json,subprocess
repo=Path.cwd();run=repo/'prototypes/sushi-loop/assets/refinement';own=run/'objects/attack-reef-fragments';final=own/'final'
read=lambda p:json.loads(p.read_text())
progress=read(run/'progress.json');assert progress['completed']==102 and progress['published']==101
prior=read(run/'objects/safe-passage/final/deploy-verification.json');assert prior['commit']=='a8dc27321be5838d13bc0d90f701fe0500e0f2d5' and prior['netlifyState']=='ready' and prior['exactCommitStatus']=='success';assert not prior['remoteSmoke']['errors']
progress['current']='attack-reef-fragments'
for row in progress['objects']:
 if row['id']=='attack-reef-fragments':row.update(stage='approved-awaiting-release102',judgeStatus='approved-round02-rootchecks-passed')
(run/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
paths=set()
for folder in [own,run/'preparation/attack-reef-fragments']:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   assert p.stat().st_size<100_000_000,str(p)
   paths.add(str(p.relative_to(repo)))
paths.update(str((run.parent/'production'/p).relative_to(repo)) for p in read(final/'promotion.json')['files'])
paths.update(str(p.relative_to(repo)) for p in [run.parent/'production/library.json',run/'progress.json',run/'objects/safe-passage/final/deploy-verification.json',run/'objects/safe-passage/final/remote-smoke.json'])
allow=final/'root-release-explicit-paths.json';paths.add(str(allow.relative_to(repo)));allow.write_text(json.dumps({'asset':'attack-reef-fragments','paths':sorted(paths)},indent=2)+'\n')
for offset in range(0,len(paths),100):subprocess.run(['git','add','-f','--',*sorted(paths)[offset:offset+100]],check=True)
with (final/'strict-staged.log').open('w') as log:subprocess.run(['python3',str(run/'tools/verify_staged_object.py'),'attack-reef-fragments','--round','round-02','--stage-missing'],stdout=log,stderr=subprocess.STDOUT,check=True)
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
(final/'root-whitespace-check.json').write_text(json.dumps({'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
print(json.dumps({'allowlistedPaths':len(paths),'strict':(final/'strict-staged.log').read_text().strip(),'whitespaceExitCode':r.returncode,'whitespaceDiagnostic':r.stdout[:7000]}))
