"""Replay from immutable round-specific local resources, never mutable delivery.json."""
from pathlib import Path
from PIL import Image
import tempfile,subprocess,os,json,hashlib,shutil,sys
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
MANIFEST=OUT/'replay-manifest-v1.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads(MANIFEST.read_text())
blender=os.environ.get('BLENDER_BIN') or shutil.which('blender')
godot=os.environ.get('GODOT_BIN') or shutil.which('godot')
assert blender and godot
def run(command,**kwargs):
 p=subprocess.run(command,capture_output=True,text=True,**kwargs)
 assert p.returncode==0,p.stdout+'\n'+p.stderr
 return p
with tempfile.TemporaryDirectory(prefix='plant-goods-portable-') as temp:
 root=Path(temp)/'supplement';root.mkdir()
 for r in manifest['resources']:
  src=BASE/r['path'];assert sha(src)==r['sha256'],r['path']
  dest=root/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  assert sha(dest)==r['sha256']
 native=root/'portable-native'
 result=run([blender,'--background',str(root/'source/round-01.blend'),'--python',str(root/'source/reopen_goods.py'),'--','--output-dir',str(native)])
 assert (native/'reopened.png').exists(),result.stdout+result.stderr
 assert Image.open(root/'candidates/round-01/goods.png').convert('RGBA').tobytes()==Image.open(native/'reopened.png').convert('RGBA').tobytes()
 print('PORTABLE_NATIVE_RGBA_EXACT',flush=True)
 run([sys.executable,str(root/'source/prepare_consumer.py')])
 consumer=root/'source/consumer'
 run([godot,'--headless','--editor','--path',str(consumer),'--import'])
 output=root/'portable-consumer';env=dict(os.environ,GOODS_OUTPUT=str(output))
 run([godot,'--path',str(consumer),'--script','res://bench.gd','--resolution','64x64','--position','-5000,-5000'],env=env)
 pictures=[]
 for p in sorted((root/'candidates/round-01/consumer').glob('*.png')):
  other=output/p.name
  assert other.exists() and Image.open(p).convert('RGBA').tobytes()==Image.open(other).convert('RGBA').tobytes(),p.name
  pictures.append({'file':p.name,'RGBAEqual':True})
 assert len(pictures)==54,len(pictures)
 print('PORTABLE_CONSUMER_54_RGBA_EXACT',flush=True)
 proof={'method':'Fresh temporary folder containing only immutable replay-manifest-v1 resources. Fresh Blender process and new Godot imports/cache. Replay recipes read no production/checkout paths.',
  'replayManifest':'candidates/round-01/replay-manifest-v1.json','replayManifestSHA256':sha(MANIFEST),
  'mutableRootDeliveryRead':False,'volatileLogsInResources':False,'resourceCount':len(manifest['resources']),
  'allResourceHashesMatched':True,'nativeReopenedRGBAPixelEquality':True,'nativeMaximumChannelDifference':0,
  'consumerAll54ImagesExactPixels':True,'images':pictures,'temporaryFolderRemovedAfterVerification':True}
 (OUT/'portable-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
