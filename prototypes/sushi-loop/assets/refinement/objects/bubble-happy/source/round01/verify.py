"""Verify declared closure and replay from relocated resources; no art modifications."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,struct
from PIL import Image
S=Path(__file__).resolve().parent;O=S.parents[1];C=O/'candidates/round01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(p):return hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest()
d=json.loads((O/'delivery.json').read_text());p=json.loads((O/d['provenance']).read_text());variant=d['runtimeVariants']
paths=set(d['resources']+[d['project'],d['recipeScript'],d['recipe'],d['validation'],d['manifest'],variant['manifest']]+list(d['heroes'].values())+list(d['previews'].values())+[r['path']for r in d['rawFrames']+d['atlases']+variant['rawFrames']+variant['atlases']])
for x in paths:assert not Path(x).is_absolute()and'..'not in Path(x).parts and(O/x).is_file(),x
for r in p['resources']:assert sha(O/r['path'])==r['sha256'],r['path']
for r in d['rawFrames']+d['atlases']+variant['rawFrames']+variant['atlases']:assert sha(O/r['path'])==r['sha256'],r['path']
assert len(d['rawFrames'])==192 and len(variant['rawFrames'])==48
actual_frames={r['path']for r in d['rawFrames']+variant['rawFrames']};assert len(actual_frames)==96
atlas_paths={r['path']for r in d['atlases']+variant['atlases']};assert len(atlas_paths)==8
for a in d['atlases']+variant['atlases']:
 image=Image.open(O/a['path']).convert('RGBA');assert image.size==(2304,1280)
 records=d['rawFrames']if not a['clip'].startswith('happy-smile')else variant['rawFrames']
 for r in [r for r in records if r['clip']==a['clip']and r['facing']==a['facing']]:
  x,y,w,h=a['rects'][r['index']];frame=Image.open(O/r['path']).convert('RGBA');assert image.crop((x,y,x+w,y+h)).tobytes()==frame.tobytes()
for c in json.loads((O/d['manifest']).read_text())['clips']:
 assert len({json.dumps(v,sort_keys=True)for v in c['directions'].values()})==1
playback_frames=0
for records in [d['rawFrames'],variant['rawFrames']]:
 for cid in dict.fromkeys(r['clip']for r in records):
  image=Image.open(O/d['previews'][cid+'-S']);assert image.n_frames==12
  sequence=[r for r in records if r['clip']==cid and r['facing']=='S']
  for index,record in enumerate(sequence):
   image.seek(index);assert image.convert('RGBA').tobytes()==Image.open(O/record['path']).convert('RGBA').tobytes();assert abs(image.info['duration']-1000/12)<1e-8;playback_frames+=1
runtime=Image.open(O/d['previews']['happy-smile-runtime-playback']);assert runtime.n_frames==27;duration=0
for index in range(runtime.n_frames):runtime.seek(index);duration+=runtime.info['duration']
assert abs(duration-2200)<1e-8
before={x:sha(O/x)for x in paths};replayed={};rgba_count=0
with tempfile.TemporaryDirectory(prefix='bubble-happy-closed-replay-')as td:
 clone=Path(td)/'relocated-object';closure=sorted(x for x in paths if x.startswith('source/round01/'))
 for x in closure:
  target=clone/x;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/x,target)
 assert not(clone/'inputs').exists()and not(clone/'reviews').exists()
 for script in ['prepare_sources.py','publish.py']:
  subprocess.run([sys.executable,str(clone/'source/round01'/script)],check=True,capture_output=True,cwd=td)
 for x,expected in before.items():
  if x.startswith('candidates/')or x in[d['project'],variant['project'],d['recipe']]:
   assert(clone/x).is_file(),x;assert sha(clone/x)==expected,('replay bytes',x);replayed[x]=sha(clone/x)
 for x in actual_frames|atlas_paths:assert psha(O/x)==psha(clone/x);rgba_count+=1
 assert sha(clone/'delivery.json')==sha(O/'delivery.json')
 assert before=={x:sha(O/x)for x in paths}
 digest=hashlib.sha256(json.dumps(replayed,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 report={'asset':'bubble-happy','round':'round01','status':'technical-replay-passed; independent visual judgment pending','declaredFiles':len(paths),'sourceClosureFiles':len(closure),'relocatedOutputFilesByteEqual':len(replayed),'relocatedRGBAImagesEqual':rgba_count,'all96CaptureFilesAnd8AtlasesRGBAEqual':True,'allGeneratedPreviewsAndManifestsByteEqual':True,'relocatedDeliveryByteEqual':True,'allDeclaredHashesVerified':True,'all240SlotsAndRectanglesVerified':True,'all8ClipAPNGs12FramesAtExact12fpsRGBAEqual':True,'playbackRGBAFramesVerified':playback_frames,'runtimePlaybackDurationMs':round(duration),'mainCameraFacingAliasesIdenticalMetadata':True,'replayWithoutInputsReviewsProductionOrOtherObjects':True,'sourceOnlyCropReproducedCanonicalBytes':True,'sourceObjectUnmodifiedByReplay':True,'outputHashMapSHA256':digest,'replayCommand':'Python source/round01/prepare_sources.py then Python source/round01/publish.py in a newly relocated object folder containing only declared source/round01 closure','python':sys.version.split()[0],'recipeSHA256':sha(S/'publish.py'),'verificationSHA256':sha(Path(__file__))}
(C/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
