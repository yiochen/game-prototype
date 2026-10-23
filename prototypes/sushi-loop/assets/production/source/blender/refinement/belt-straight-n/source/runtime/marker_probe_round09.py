"""Run marker and whole-renderer GPU probes in a disposable imported game project."""
from pathlib import Path
import os,re,shutil,subprocess,tempfile
R=Path(__file__).resolve().parent;P=R.parents[7];O=R.parents[1]/'candidates/round-09';env=os.environ.copy();env['BELT_MARKER_OUTPUT']=str(O/'markers');env['BELT_RUNTIME_OUTPUT']=str(O/'integration')
for n in ['markers','integration']:(O/n).mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sushi-belt-markers-') as tmp:
 project=Path(tmp)/'project';shutil.copytree(P/'prototypes/sushi-loop/godot',project,ignore=shutil.ignore_patterns('.godot','.local','build','android','review','__pycache__'))
 runtime=project/'marker-runtime';runtime.mkdir()
 for p in R.iterdir():
  if p.suffix in ['.gd','.gdshader']:shutil.copyfile(p,runtime/p.name)
 commands=[('import',['--headless','--editor','--import']),('markers',['--windowed','--audio-driver','Dummy','--resolution','1440x1000','--script','res://marker-runtime/marker_probe_round09.gd']),('integration',['--windowed','--audio-driver','Dummy','--resolution','1440x1000','--script','res://marker-runtime/integration_probe_round09.gd'])]
 for name,args in commands:
  out=subprocess.run(['/opt/homebrew/bin/godot','--path',str(project),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
  (R/('marker-'+name+'-round09.log')).write_text(out.stdout)
  print(name,out.returncode,'\n'.join(out.stdout.splitlines()[-8:]),flush=True)
  if out.returncode or re.search(r'(?:^|\n)(?:SCRIPT )?ERROR:',out.stdout):raise SystemExit(1)
