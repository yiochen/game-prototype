"""Open round-01.blend in a fresh process, then --python this script. No source save."""
import bpy,json,sys,hashlib,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;sys.path.insert(0,str(HERE))
from native_state import state,camera_record
ROUND=BASE/'candidates/round-01'
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROUND);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=args.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'reopened.png').exists()
parity=json.loads((ROUND/'native-parity.json').read_text());reopened=state();camera=camera_record()
assert reopened['sectionHashes']==parity['candidate']['sectionHashes'] and camera==parity['goodsCamera']
scene=bpy.context.scene;scene.render.filepath=str(OUT/'reopened.png');bpy.ops.render.render(write_still=True)
(OUT/'reopen-native.json').write_text(json.dumps({'actualFreshProcess':True,'sourcePath':'source/round-01.blend','sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'sectionHashes':reopened['sectionHashes'],'camera':camera,'nativeParityMatches':True,'output':'reopened.png'},indent=2)+'\n')
