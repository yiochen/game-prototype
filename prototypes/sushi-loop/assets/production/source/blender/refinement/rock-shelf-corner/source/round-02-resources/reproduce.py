"""Reproduce native art and scoped evidence in an unsealed private copy.
Requires exact Blender 5.2.2, bundled Python3.12/Pillow closure, Node22+ and the
workspace @playwright/test Chromium runtime. Never rerun in an immutable round.
"""
import os,sys,subprocess,json,hashlib
from pathlib import Path
RES=Path(__file__).resolve().parent;BASE=RES.parent;EXP=BASE.parent;OUT=EXP/'candidates/round-02'
BLENDER='/opt/homebrew/bin/blender';PYTHON='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
if (OUT/'packet.json').exists() or (EXP/'delivery/round-02/manifest.json').exists():raise SystemExit('Immutable round: reproduce in a separate private copy, retaining source/dependencies and inputs.')
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};commands=[]
def run(command,log):
 result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(OUT/log).write_text(result.stdout);commands.append({'command':command,'log':f'candidates/round-02/{log}','returnCode':result.returncode})
 if result.returncode or 'Traceback (most recent call last)' in result.stdout:raise RuntimeError(f'Failed native evidence step: {log}')
OUT.mkdir(parents=True,exist_ok=True)
for script,log,args in [('build-round-02.py','build-capture.log',['--','capture']),('capture-evidence.py','capture-evidence.log',[]),('measure-collars.py','collar-fields.log',[]),('classify-normal-precision.py','normal-precision.log',[]),('capture-cap-fields.py','cap-fields.log',[]),('capture-collar-shader-controls.py','collar-shader-controls.log',[])]:
 run([BLENDER,'--background','--factory-startup','--python',str(RES/script),*args],log)
 if script=='measure-collars.py':
  fields=json.loads((OUT/'collar-fields.json').read_text())['summary']
  if any(v['maxAlbedoError']>1e-6 or v['maxNormalError']>1e-6 for v in fields.values()):raise RuntimeError('Canonical collar field regression; inspect actual fields before further captures')
for script,log in [('publish-evidence.py','publication.log'),('measure-shader-controls.py','shader-control-measure.log')]:run([PYTHON,str(RES/script)],log)
run(['node',str(RES/'capture-consumer.mjs')],'consumer.log');run([PYTHON,str(RES/'finish-evidence.py')],'finish.log');run([BLENDER,'--background','--factory-startup','--python',str(RES/'audit-final-source.py')],'source-audit.log')
(OUT/'reproduction-commands.json').write_text(json.dumps({'commands':commands,'noRepair':'Whole-frame BOX only; native art, exact current helper composition, ordinary whole-canvas browser filtering.'},indent=2)+'\n');print('REPRODUCTION COMPLETE')
