"""Portable fresh-output adapter; only output destination differs from immutable generators.
Usage: blender --factory-startup -b --disable-autoexec source/round-02.blend --python source/reproduce_native_round04_v4.py -- controls --output-dir candidates/round-04/new-control-run
For shipping use source03, kind shipping and --all. Never replaces prior evidence.
"""
from pathlib import Path
import sys,shutil,hashlib
P=Path(__file__).parent;O=P.parent;args=sys.argv[sys.argv.index('--')+1:];kind=args[0];assert kind in ['controls','shipping'];out=Path(args[args.index('--output-dir')+1]).resolve();assert out.is_relative_to(O.resolve()) and not out.exists(),'New object-relative output directory required';out.mkdir(parents=True)
if kind=='controls':
 (out/'resources').mkdir();src=O/'candidates/round-04/resources/dish-salmon.png';assert hashlib.sha256(src.read_bytes()).hexdigest()=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4';shutil.copy2(src,out/'resources/dish-salmon.png');script=P/'generate_controls_round04.py'
else:
 assert '--all' in args,'Use --all for the full192 shipping replay';script=P/'replay_shipping_round04.py'
code=script.read_text();needle="C=O/'candidates/round-04'";assert code.count(needle)==1;code=code.replace(needle,'C=Path('+repr(str(out))+')');ns={'__file__':str(script),'__name__':'fresh_output_native_reproduction'};exec(compile(code,str(script),'exec'),ns)
