"""Reproduce this candidate only in a disposable object-folder copy before sealing.
The saved round-01.blend is the normative editable deliverable; reviewers need not
execute model construction. This driver preserves all explicit evidence steps.
"""
import sys,subprocess,time
from pathlib import Path
B=Path(__file__).resolve().parent;E=B.parent
if (E/'candidates/round-01/packet.json').exists():raise SystemExit('Copy experiment to a disposable unsealed folder before reproducing.')
BLENDER='/opt/homebrew/bin/blender';PYTHON='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def run(args):subprocess.run(args,cwd=E,check=True)
for name in ['build-round-01.py','capture-round-01.py','validate-native.py']:run([BLENDER,'-b','--python',str(B/name)])
run([PYTHON,str(B/'publish-round-01.py')])
server=subprocess.Popen([PYTHON,'-m','http.server','9138','--bind','127.0.0.1'],cwd=E,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 time.sleep(.5);run(['node',str(B/'browser-check.mjs')])
finally:server.terminate();server.wait(timeout=10)
for mode in ['fullChrome','shell']:run([PYTHON,str(B/'analyze-consumer.py'),mode])
run([PYTHON,str(B/'finalize-evidence.py')])
print('Candidate and evidence recreated. Coordinator must validate and seal independently.')
