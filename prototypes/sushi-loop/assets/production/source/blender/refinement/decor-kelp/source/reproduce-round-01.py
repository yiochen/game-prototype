"""Replay the exact saved unadapted project into a new empty output directory.

Example: python reproduce-round-01.py --output /tmp/kelp-replay --smoke
No original, reviewed artifact or production file is written.
"""
import argparse,subprocess,shutil,json,hashlib,os
from pathlib import Path
P=argparse.ArgumentParser();P.add_argument('--output',type=Path,required=True);P.add_argument('--blender',default='/opt/homebrew/bin/blender');P.add_argument('--python',default='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3');P.add_argument('--smoke',action='store_true');a=P.parse_args()
BASE=Path(__file__).resolve().parent;dst=a.output.resolve();assert not dst.exists() or not any(dst.iterdir()),'Use a new empty output directory'
(dst/'source/round-01-resources').mkdir(parents=True,exist_ok=True)
for name in ['round-01.blend','round-01-rig.json','round-01-construction.json','capture-round-01.py','publish-round-01.py']:
    shutil.copy2(BASE/name,dst/'source'/name)
shutil.copy2(BASE/'round-01-resources/concept_decoration_geometry.py',dst/'source/round-01-resources/concept_decoration_geometry.py')
command=[a.blender,'--background',str(dst/'source/round-01.blend'),'--python',str(dst/'source/capture-round-01.py')]
if a.smoke:command+=['--','--test']
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
subprocess.run(command,env=env,check=True)
if not a.smoke:subprocess.run([a.python,str(dst/'source/publish-round-01.py')],env=env,check=True)
print(json.dumps({'savedSourceSHA256':hashlib.sha256((dst/'source/round-01.blend').read_bytes()).hexdigest(),'output':str(dst),'captureCommand':command,'source':'exact saved unadapted project; source-generation recipe is independently retained in build-round-01.py','externalPrerequisites':'Blender5.2.2LTS, Python3.12/Pillow12.3.0, OS frameworks; no copied executable/runtime trees.'},indent=2))
