"""Reproduce real capture_starter teardown with private saves/project and verbose Godot."""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, uuid
R=pathlib.Path(__file__).resolve().parent
P=R.parents[7]
G=P/'prototypes/sushi-loop/godot'
O=R.parents[1]/'candidates/round-09/teardown';O.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--variant',default='frozen');p.add_argument('--size',default='390x844');p.add_argument('--script',default='tests/capture_starter.gd');p.add_argument('--normal',action='store_true');p.add_argument('--repeat',type=int,default=1);a=p.parse_args()
identity='SushiLoopBeltTeardown-'+uuid.uuid4().hex
out=O/(a.variant+'-'+a.size+('-normal' if a.normal else '-verbose')+('' if a.script=='tests/capture_starter.gd' else '-'+pathlib.Path(a.script).stem));out.mkdir(exist_ok=True)
env=os.environ.copy();env['SUSHI_LOOP_CAPTURE_OUTPUT']=str(out);env['SUSHI_LOOP_TEST_SIZE']=a.size
try:
 with tempfile.TemporaryDirectory(prefix='sushi-belt-teardown-') as tmp:
  project=pathlib.Path(tmp)/'project'
  ignored=shutil.ignore_patterns('.godot','.local','build','android','__pycache__','export_credentials.cfg','*.keystore','*.jks','review')
  shutil.copytree(G,project,ignore=ignored)
  config=project/'project.godot';s=config.read_text();s=re.sub(r'^config/(?:use_custom_user_dir|custom_user_dir_name)=.*\n?','',s,flags=re.M);s=s.replace('[application]\n',f'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="{identity}"\n',1);config.write_text(s)
  runtime=R/'frozen-pre-teardown' if a.variant=='frozen' else R
  for name in ['native_world_layer.gd','native_pixel_compositor.gd','native_present.gdshader','native_reduce2.gdshader']:shutil.copyfile(runtime/name,project/'scripts'/name)
  shutil.copyfile(R/'restaurant_view_baseline.gd' if a.variant=='baseline' else runtime/'restaurant_view_native.gd',project/'scripts/restaurant_view.gd')
  if a.script!='tests/capture_starter.gd':shutil.copyfile(R/a.script,project/'tests/teardown_probe.gd')
  cmds=[['/opt/homebrew/bin/godot','--headless','--path',str(project),'--editor','--import'],['/opt/homebrew/bin/godot',*([] if a.normal else ['--verbose']),'--path',str(project),'--windowed','--audio-driver','Dummy','--resolution',a.size,'--script','res://'+('tests/capture_starter.gd' if a.script=='tests/capture_starter.gd' else 'tests/teardown_probe.gd')]]
  cmds=cmds[:1]+cmds[1:]*a.repeat
  for step,cmd in enumerate(cmds):
   result=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=150)
   (out/('import.log' if step==0 else f'capture-{step:02d}.log')).write_text(result.stdout)
   print(step,result.returncode,'two-object-warning', '2 ObjectDB instances were leaked' in result.stdout,flush=True)
   if result.returncode or re.search(r'(?:^|\n)(?:SCRIPT )?ERROR:',result.stdout):raise SystemExit(1)
  print('\n'.join(result.stdout.splitlines()[-35:]),flush=True)
finally:
 shutil.rmtree(pathlib.Path.home()/'Library/Application Support'/identity,ignore_errors=True)
