"""Actual Godot feedback + integration probes; all evidence written only in round11."""
from pathlib import Path
import os,re,shutil,subprocess,tempfile,json,hashlib
R=Path(__file__).resolve().parent;P=R.parents[7];O=R.parents[1]/'candidates/round-11';env=os.environ.copy();env['BELT_FEEDBACK_OUTPUT']=str(O/'feedback');env['BELT_RUNTIME_OUTPUT']=str(O/'integration')
for n in ['feedback','integration']:(O/n).mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sushi-belt-feedback-') as tmp:
 project=Path(tmp)/'project';shutil.copytree(P/'prototypes/sushi-loop/godot',project,ignore=shutil.ignore_patterns('.godot','.local','build','android','review','__pycache__'))
 runtime=project/'feedback-runtime';runtime.mkdir();sources={}
 for p in R.iterdir():
  if p.suffix in ['.gd','.gdshader']:
   shutil.copyfile(p,runtime/p.name);sources[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 (O/'probe-source-hashes.json').write_text(json.dumps(sources,indent=2))
 commands=[('import',['--headless','--editor','--import']),('feedback',['--windowed','--audio-driver','Dummy','--resolution','1440x1000','--script','res://feedback-runtime/feedback_probe_round11.gd']),('integration',['--windowed','--audio-driver','Dummy','--resolution','1440x1000','--script','res://feedback-runtime/integration_probe_round09.gd'])]
 for name,args in commands:
  out=subprocess.run(['/opt/homebrew/bin/godot','--path',str(project),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
  (O/(name+'.log')).write_text(out.stdout)
  print(name,out.returncode,'\n'.join(out.stdout.splitlines()[-8:]),flush=True)
  if out.returncode or re.search(r'(?:^|\n)(?:SCRIPT )?ERROR:',out.stdout):raise SystemExit(1)
