"""Blender entry point. Use -- --output-root /absolute/new/replay-folder.
Rebuild/replay in a new directory, leaving the review candidate untouched.
Then run bundled Python publish-01.py, prepare-consumer-01.py, Node capture-consumer-01.mjs,
bundled Python analyze-repeatability-01.py and finish-handoff-01.py in that directory.
"""
import bpy,pathlib,sys,shutil,runpy
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent;args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--output-root' not in args:raise RuntimeError('Pass -- --output-root /absolute/new/replay-folder; candidate bytes are immutable.')
D=pathlib.Path(args[args.index('--output-root')+1]).resolve()
if D.exists():raise RuntimeError('Output must be a new directory')
(D/'source').mkdir(parents=True)
for p in H.iterdir():
 if p.is_file() and p.suffix in {'.py','.mjs','.html','.md','.json'}:shutil.copy2(p,D/'source'/p.name)
shutil.copytree(H/'resources',D/'source/resources',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(H.parent/'inputs',D/'inputs',ignore=shutil.ignore_patterns('__pycache__'))
runpy.run_path(str(D/'source/round-01.py'),run_name='__main__')
runpy.run_path(str(D/'source/replay-01.py'),run_name='__main__')
runpy.run_path(str(D/'source/assemble-audit-01.py'),run_name='__main__')
runpy.run_path(str(D/'source/control-closure-01.py'),run_name='__main__')
runpy.run_path(str(D/'source/verify-neutral-identity-01.py'),run_name='__main__')
print('Native replay written to',str(D))
