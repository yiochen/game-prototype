"""Portable exact native adoption. Requires a NEW destination; never overwrites source."""
import sys,json,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
if len(sys.argv)!=2:raise SystemExit('usage: python rebuild.py /absolute/new-destination')
D=Path(sys.argv[1]).resolve()
if D.exists():raise SystemExit('Destination already exists; choose a new directory')
T=D/'source/round-01';T.mkdir(parents=True);(D/'candidates/round-01').mkdir(parents=True)
for f in ['adopt.py','component_identity.py','native_common.py']:shutil.copyfile(H/f,T/f)
required=['frozen-body-v6.blend']
for prefix,project,signed in [('inputs/approved-equipment-preparation-v1/sub-hull-panels','source/round-01-neutral.blend','candidates/round-01/neutral-resource-identity.json'),('inputs/approved-equipment-preparation-v1/sub-harpoon-mount','source/round-02/project.blend','candidates/round-02/canonical-neutral-persistent-resources.json'),('inputs/approved-canonical-equipment-v1/sub-collector-inlet','source/round-02.blend','candidates/round-02/canonical-neutral-resources.json')]:required += ['approved-inputs/'+prefix+'/'+project,'approved-inputs/'+prefix+'/'+signed]
for f in required:
 dst=T/'resources'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/'resources'/f,dst)
subprocess.run(['/opt/homebrew/bin/blender','-b','--python-exit-code','1','--python',str(T/'adopt.py')],check=True)
print(T/'project.blend')
