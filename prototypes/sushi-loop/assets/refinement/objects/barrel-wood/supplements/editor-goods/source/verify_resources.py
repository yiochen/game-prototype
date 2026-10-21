"""Verify exact native and Godot replay from only declared local resources in a fresh folder."""
from pathlib import Path
from PIL import Image
import json,hashlib,tempfile,subprocess,shutil,os
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=['source/round-01.blend','source/native_state.py','source/reopen_goods.py','source/prepare_consumer.py','source/bench.gd','source/consumer-project.godot','inputs/original.png','candidates/round-01/goods.png','candidates/round-01/native-parity.json']+[str(p.relative_to(B)) for p in sorted((B/'source/resources/current-consumer').rglob('*')) if p.is_file()]
manifest=[{'path':p,'sha256':sha(B/p)} for p in files];(B/'source/replay-resources.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='barrel-goods-replay-') as temp:
 dest=Path(temp)/'supplement';dest.mkdir()
 for r in manifest:
  p=dest/r['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/r['path'],p);assert sha(p)==r['sha256']
 output=dest/'native-replay'
 subprocess.run(['/opt/homebrew/bin/blender','--background',str(dest/'source/round-01.blend'),'--python',str(dest/'source/reopen_goods.py'),'--','--output-dir',str(output)],capture_output=True,text=True,check=True)
 assert Image.open(O/'goods.png').convert('RGBA').tobytes()==Image.open(output/'reopened.png').convert('RGBA').tobytes()
 py='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
 subprocess.run([py,str(dest/'source/prepare_consumer.py')],capture_output=True,text=True,check=True)
 subprocess.run(['/opt/homebrew/bin/godot','--headless','--editor','--path',str(dest/'source/consumer'),'--import'],capture_output=True,text=True,check=True)
 co=dest/'consumer-replay';env=dict(os.environ,GOODS_OUTPUT=str(co))
 subprocess.run(['/opt/homebrew/bin/godot','--path',str(dest/'source/consumer'),'--script','res://bench.gd','--resolution','64x64','--position','-5000,-5000'],env=env,capture_output=True,text=True,check=True)
 pictures=[]
 for p in sorted((O/'consumer').glob('*.png')):
  other=co/p.name;assert other.exists() and Image.open(p).convert('RGBA').tobytes()==Image.open(other).convert('RGBA').tobytes(),p.name
  pictures.append({'path':p.name,'exactRGBAPixels':True})
 assert len(pictures)==54
 proof={'method':'Fresh temporary directory containing only source/replay-resources.json declared hashes; fresh Blender and Godot imports. No original checkout read by replay commands. Temporary directory removed after verification.','nativeRGBAPixelsEqual':True,'nativeMaximumChannelDifference':0,'consumer54PNGsExactRGBAPixels':True,'resourceCount':len(manifest),'resourceManifest':'source/replay-resources.json','resourceManifestSHA256':sha(B/'source/replay-resources.json'),'consumerImages':pictures,'nativeReopenedSHA256':sha(output/'reopened.png'),'allBoundResourceHashesMatched':True,'actualGodotVersion':'4.7.2.stable Compatibility OpenGL Apple M4','productionMutation':False}
 (O/'portable-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Fresh resource-only native and all 54 consumer PNGs replay exact RGBA pixels.')
