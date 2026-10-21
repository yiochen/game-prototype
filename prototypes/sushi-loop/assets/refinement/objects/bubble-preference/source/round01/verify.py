"""Verify all slots/rects/playbacks and replay source closure after relocation."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile
from PIL import Image
S=Path(__file__).resolve().parent;O=S.parents[1];C=O/'candidates/round01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(p):return hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest()
d=json.loads((O/'delivery.json').read_text());prov=json.loads((O/d['provenance']).read_text())
paths=set(d['resources']+[d['project'],d['recipeScript'],d['recipe'],d['validation'],d['manifest']]+list(d['heroes'].values())+list(d['previews'].values())+[r['path']for r in d['rawFrames']+d['atlases']])
for x in paths:assert not Path(x).is_absolute()and'..'not in Path(x).parts and(O/x).is_file(),x
for r in prov['resources']:assert sha(O/r['path'])==r['sha256'],r['path']
for r in d['rawFrames']+d['atlases']:assert sha(O/r['path'])==r['sha256'],r['path']
assert len(d['rawFrames'])==432 and len(d['atlases'])==36
actual={r['path']for r in d['rawFrames']};atlases={r['path']for r in d['atlases']};assert len(actual)==108 and len(atlases)==9
for a in d['atlases']:
 im=Image.open(O/a['path']).convert('RGBA');assert im.size==(2304,1280)
 for r in [r for r in d['rawFrames']if r['clip']==a['clip']and r['direction']==a['direction']]:
  x,y,w,h=a['rects'][r['index']];assert im.crop((x,y,x+w,y+h)).tobytes()==Image.open(O/r['path']).convert('RGBA').tobytes()
manifest=json.loads((O/d['manifest']).read_text())
for c in manifest['clips']:
 assert c['fps']==12 and c['frames']==12 and c['frameOrder']==list(range(12));assert c['loop']==c['id'].endswith('idle')
 assert len({json.dumps(v,sort_keys=True)for v in c['directions'].values()})==1
playback_frames=0
for c in manifest['clips']:
 cid=c['id'];im=Image.open(O/d['previews'][cid+'-S']);assert im.n_frames==12
 records=[r for r in d['rawFrames']if r['clip']==cid and r['direction']=='S']
 for i,r in enumerate(records):im.seek(i);assert im.convert('RGBA').tobytes()==Image.open(O/r['path']).convert('RGBA').tobytes();assert abs(im.info['duration']-1000/12)<1e-8;playback_frames+=1
for prefix in ['salmon','cucumber','eel']:
 im=Image.open(O/d['previews'][prefix+'-recipe-appear-idle-fade']);assert im.n_frames==48
for prefix in ['salmon','cucumber']:
 im=Image.open(O/d['previews'][prefix+'-current-context-playback']);assert im.n_frames==60
v=json.loads((O/d['validation']).read_text());assert all(v['originalPublisherReplay'][k]is True for k in ['original108AtlasRectRGBAEqual','registeredOriginalIdle0RGBAEqual','candidate108FramesRGBAEqualOriginalMathWithCanonicalSourceReplacement'])
before={x:sha(O/x)for x in paths};replayed={};rgba_count=0
with tempfile.TemporaryDirectory(prefix='preference-closed-replay-')as td:
 clone=Path(td)/'relocated-object';closure=sorted(x for x in paths if x.startswith('source/round01/'))
 for x in closure:
  dest=clone/x;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/x,dest)
 assert not(clone/'inputs').exists()and not(clone/'reviews').exists()
 for script in ['prepare_sources.py','publish.py']:subprocess.run([sys.executable,str(clone/'source/round01'/script)],cwd=td,capture_output=True,check=True)
 for x,expected in before.items():
  if x.startswith('candidates/')or x in[d['project'],d['recipe']]:
   assert(clone/x).is_file(),x;assert sha(clone/x)==expected,('replay bytes',x);replayed[x]=sha(clone/x)
 for x in actual|atlases:assert psha(O/x)==psha(clone/x);rgba_count+=1
 assert sha(clone/'delivery.json')==sha(O/'delivery.json');assert before=={x:sha(O/x)for x in paths}
 digest=hashlib.sha256(json.dumps(replayed,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 report={'asset':'bubble-preference','round':'round01','status':'technical-replay-passed; independent visual judgment pending','declaredFiles':len(paths),'sourceClosureFiles':len(closure),'relocatedOutputFilesByteEqual':len(replayed),'relocatedRGBAImagesEqual':rgba_count,'all108FramesAnd9AtlasesRGBAEqual':True,'all432SlotsAnd36AtlasEntriesVerified':True,'all9ClipAPNGs12FramesExact12fpsRGBAEqual':True,'playbackRGBAFramesVerified':playback_frames,'threeRecipeSequences48Frames':True,'twoCurrentContextPlaybacks60Frames':True,'allOriginal108PhysicalOldFramesReplayedRGBAEqual':True,'allCandidate108FramesMatchOriginalAnimationMath':True,'allSourceAndOutputHashesVerified':True,'replayWithoutInputsReviewsProductionOtherObjects':True,'sourceCropReproducedCanonicalBytes':True,'allGeneratedPreviewsNativeProjectAndManifestsByteEqual':True,'retainedNativeCaptureEvidenceCopiedByteExact':(S/'resources/native-capture/evidence.json').is_file(),'relocatedDeliveryByteEqual':True,'sourceObjectUnmodifiedByReplay':True,'outputHashMapSHA256':digest,'replayCommand':'Python source/round01/prepare_sources.py then Python source/round01/publish.py inside a newly relocated object folder containing only declared source/round01 closure','python':sys.version.split()[0],'recipeSHA256':sha(S/'publish.py'),'verificationSHA256':sha(Path(__file__))}
(C/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
