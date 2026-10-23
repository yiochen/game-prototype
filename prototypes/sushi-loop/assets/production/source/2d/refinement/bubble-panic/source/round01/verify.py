"""Closed relocated replay check, metadata/frame/APNG equality. No artwork edit."""
from pathlib import Path
import hashlib,json,tempfile,subprocess,sys,shutil
from PIL import Image
S=Path(__file__).resolve().parent;O=S.parents[1];C=O/'candidates/round01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pixels(p):return Image.open(p).convert('RGBA').tobytes()
d=json.loads((O/'delivery.json').read_text());prov=json.loads((O/d['provenance']).read_text())
paths=set(d['resources']+[d['project'],d['recipeScript'],d['recipe'],d['validation'],d['manifest']]+list(d['heroes'].values())+list(d['previews'].values())+[r['path']for r in d['rawFrames']+d['atlases']])
for x in paths:assert not Path(x).is_absolute()and'..'not in Path(x).parts and(O/x).is_file(),x
for r in prov['resources']:assert sha(O/r['path'])==r['sha256'],r['path']
assert len(d['rawFrames'])==144 and len({r['path']for r in d['rawFrames']})==36 and len(d['atlases'])==12 and len({r['path']for r in d['atlases']})==3
for r in d['rawFrames']+d['atlases']:assert sha(O/r['path'])==r['sha256'],r['path']
for a in d['atlases']:
 im=Image.open(O/a['path']).convert('RGBA');assert im.size==(2304,1280)
 for r in [r for r in d['rawFrames']if r['clip']==a['clip']and r['direction']==a['direction']]:
  x,y,w,h=a['rects'][r['index']];assert im.crop((x,y,x+w,y+h)).tobytes()==pixels(O/r['path'])
manifest=json.loads((O/d['manifest']).read_text())
original=json.loads((S/'resources/catalog-object.json').read_text())
for key in ['frameSize','root','sourceScale','footprint','rootCell','directionFootprints','directionRootCells','projection','facingPolicy','registration']:assert manifest[key]==original[key],key
assert manifest['frameSize']==[192,320]and manifest['root']==[96,248]and manifest['sourceScale']==2
assert [c['id']for c in manifest['clips']]==['appear','idle','fade']
for c in manifest['clips']:
 assert c['fps']==12 and c['frames']==12 and c['frameOrder']==list(range(12))and c['loop']==(c['id']=='idle')and c['static']==False
 assert len({json.dumps(v,sort_keys=True)for v in c['directions'].values()})==1
 sequence=Image.open(O/d['previews'][c['id']+'-S']);assert sequence.n_frames==12;assert sequence.info.get('loop')==(0 if c['id']=='idle'else 1)
 for i in range(12):sequence.seek(i);assert abs(sequence.info['duration']-1000/12)<1e-8;assert sequence.convert('RGBA').tobytes()==pixels(C/'raw'/f'{c["id"]}-S-{i:04d}.png')
assert 'native-runtime-wander-playback'in d['previews'],'Actual native runtime capture required before verification'
runtime=Image.open(O/d['previews']['native-runtime-wander-playback']);assert runtime.n_frames==48
receipt=json.loads((C/'native-capture-evidence.json').read_text());runtime_record=next(r for r in receipt['files']if r['key']=='native-runtime-wander-playback')
for i in range(48):runtime.seek(i);assert abs(runtime.info['duration']-1000/12)<1e-8;assert hashlib.sha256(runtime.convert('RGBA').tobytes()).hexdigest()==runtime_record['pixelSHA256ByFrame'][i]
before={p:sha(O/p)for p in paths};replayed={};actual=set(r['path']for r in d['rawFrames']+d['atlases'])
with tempfile.TemporaryDirectory(prefix='panic-relocated-closure-')as td:
 clone=Path(td)/'unrelated-object-folder';closure=sorted(p for p in paths if p.startswith('source/round01/'))
 for p in closure:
  dest=clone/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/p,dest)
 assert not(clone/'inputs').exists()and not(clone/'reviews').exists()
 for script in ['prepare_sources.py','publish.py']:subprocess.run([sys.executable,str(clone/'source/round01'/script)],check=True,capture_output=True,text=True,cwd=td)
 for p,h in before.items():
  if p.startswith('candidates/')or p in[d['project'],d['recipe'],'source/round01/crop.json']:
   assert(clone/p).is_file(),p;assert sha(clone/p)==h,('byte replay',p);replayed[p]=h
 for p in actual:assert pixels(O/p)==pixels(clone/p)
 assert sha(clone/'delivery.json')==sha(O/'delivery.json')
 assert before=={p:sha(O/p)for p in paths}
report={'asset':'bubble-panic','round':'round01','status':'technical replay passed; independent visual decision pending','declaredFiles':len(paths),'sourceClosureFiles':len(closure),'relocatedOutputFilesByteEqual':len(replayed),'all36FramesAnd3AtlasesRGBAEqual':True,'all144SlotsAndAtlasRectsVerified':True,'all3ClipAPNGs12ExactFramesAt12fpsRGBAEqual':True,'actualGodotRuntimeAPNG48FramesAt12fpsRGBAEqualReceipt':True,'runtimeDurationSeconds':4,'allGeneratedPreviewManifestMetadataBytesEqual':True,'relocatedDeliveryBytesEqual':True,'replayedWithoutInputsReviewsProductionOrOtherObjects':True,'original36AtlasRectRGBAEqual':True,'originalRegisteredIdle0RGBAEqual':True,'candidate36FramesEqualOriginalPublisherMath':True,'sourceCropRegeneratedBytesEqual':True,'declaredSourceUnmodifiedByReplay':True,'outputHashMapSHA256':hashlib.sha256(json.dumps(replayed,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'recipeSHA256':sha(S/'publish.py'),'verificationSHA256':sha(Path(__file__)),'python':sys.version.split()[0],'replayCommand':'Python source/round01/prepare_sources.py then Python source/round01/publish.py from unrelated relocated source-only closure'}
(C/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
