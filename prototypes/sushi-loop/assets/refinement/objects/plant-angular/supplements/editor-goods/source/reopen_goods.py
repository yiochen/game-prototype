"""Fresh-process native recapture and full semantic parity. Never saves source."""
import bpy,json,sys,hashlib,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;sys.path.insert(0,str(HERE))
from native_state import state,camera_record,normalize_static,ensure_visible
ROUND=BASE/'candidates/round-01'
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=ROUND)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=a.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'reopened.png').exists()
receipt=json.loads((ROUND/'native-parity.json').read_text())
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==receipt['savedProjectSHA256']
# Inspect exactly the saved binding first, then normalize idempotently.
saved=state();assert saved['sectionHashes']==receipt['candidate']['sectionHashes']
bindings=normalize_static();ensure_visible();reopened=state();camera=camera_record()
assert reopened['sectionHashes']==receipt['source']['sectionHashes']
assert camera==receipt['goodsCamera'] and saved['sectionHashes']==reopened['sectionHashes']
bpy.context.scene.render.filepath=str(OUT/'reopened.png');bpy.ops.render.render(write_still=True)
(OUT/'reopen-native.json').write_text(json.dumps({'actualFreshProcess':True,'sourcePath':'source/round-01.blend',
 'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'sectionHashes':reopened['sectionHashes'],
 'savedBindingAlreadyExact':True,'normalizationIdempotent':True,'bindings':bindings,'camera':camera,
 'nativeParityMatches':True,'output':'reopened.png'},indent=2)+'\n')
