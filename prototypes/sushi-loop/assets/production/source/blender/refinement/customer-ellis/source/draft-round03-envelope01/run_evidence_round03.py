from pathlib import Path
import subprocess,concurrent.futures
H=Path(__file__).resolve().parent
B='/opt/homebrew/bin/blender'
def run(mode):
 source=H/('round-03.blend' if mode=='main' else 'round-03-runtime.blend')
 for script in ['surface_audit_round03.py','inspect_compositor_round03.py','auxiliary_round03.py','reproduce_round03.py']:
  with (H/('round03-'+mode+'-'+script+'.log')).open('wb') as log:
   subprocess.run([B,'-b',str(source),'--python',str(H/script),'--',mode],stdout=log,stderr=subprocess.STDOUT,check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,['main','runtime']))
print('ELLIS_EXTRA_EVIDENCE_COMPLETE',flush=True)
