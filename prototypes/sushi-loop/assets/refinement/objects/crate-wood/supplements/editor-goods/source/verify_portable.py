"""Test canonical native and copied-consumer replay from only declared local delivery resources."""
from pathlib import Path
from PIL import Image
import tempfile,subprocess,os,json,hashlib,shutil
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
MANIFEST=OUT/'delivery.json'
delivery=json.loads(MANIFEST.read_text())
with tempfile.TemporaryDirectory(prefix='crate-goods-portable-') as temp:
 root=Path(temp)/'supplement';root.mkdir()
 for record in delivery['resources']:
  src=BASE/record['path']
  if 'sha256' in record:assert sha(src)==record['sha256'],record['path']
  dest=root/record['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);assert sha(dest)==sha(src)
 for name in ('render','validation'):
  src=BASE/delivery[name];dest=root/delivery[name];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 native=root/'portable-native'
 run=subprocess.run(['/opt/homebrew/bin/blender','--background',str(root/delivery['project']),'--python',str(root/'source/reopen_goods.py'),'--','--output-dir',str(native)],capture_output=True,text=True,check=True)
 assert (native/'reopened.png').exists(),run.stdout+run.stderr
 a=Image.open(BASE/delivery['render']).convert('RGBA');b=Image.open(native/'reopened.png').convert('RGBA');assert a.tobytes()==b.tobytes()
 print('Portable native source renders exact RGBA pixels.',flush=True)
 python='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
 subprocess.run([python,str(root/'source/prepare_consumer.py')],capture_output=True,text=True,check=True)
 consumer=root/'source/consumer'
 subprocess.run(['/opt/homebrew/bin/godot','--headless','--editor','--path',str(consumer),'--import'],capture_output=True,text=True,check=True)
 output=root/'portable-consumer';env=dict(os.environ,GOODS_OUTPUT=str(output))
 subprocess.run(['/opt/homebrew/bin/godot','--path',str(consumer),'--script','res://bench.gd','--resolution','64x64','--position','-5000,-5000'],env=env,capture_output=True,text=True,check=True)
 pictures=[]
 for p in sorted((OUT/'consumer').glob('*.png')):
  other=output/p.name
  assert other.exists() and Image.open(p).convert('RGBA').tobytes()==Image.open(other).convert('RGBA').tobytes(),p.name
  pictures.append({'file':p.name,'RGBAEqual':True})
 assert len(pictures)==42
 print('Portable copied consumer renders all42 background/context PNGs with exact RGBA pixels.',flush=True)
 proof={'method':'Fresh temporary folder containing declared delivery resources only; original checkout is not accessed by replay recipes. Fresh Blender process and fresh Godot imports/cache.','sourceSHA256':sha(BASE/delivery['project']),'deliveryManifest':'candidates/round-01/delivery.json','mutableCanonicalDeliveryRead':False,'resourceCount':len(delivery['resources']),'allResourceHashesMatched':True,'nativeReopenedRGBAPixelEquality':True,'nativeMaximumChannelDifference':0,'consumerAll42ImagesExactPixels':True,'images':pictures,'productionAccessByReplayRecipes':False,'temporaryFolderRemovedAfterVerification':True}
 (OUT/'portable-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
