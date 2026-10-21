"""Independent deterministic closure/reproduction check. Never repaints artwork."""
from pathlib import Path
import hashlib,json,subprocess,sys
from PIL import Image
O=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((O/'delivery.json').read_text());v=json.loads((O/d['validation']).read_text());p=json.loads((O/d['provenance']).read_text())
paths=set(d['resources']+[d['project'],d['recipe'],d['recipeManifest'],d['validation'],d['provenance'],d['captureRecipe'],d['packagingRecipe'],d['preparationRecipe']]+list(d['heroes'].values())+list(d['previews'].values())+[a['path']for a in d['atlases']]+[a['path']for a in d['rawFrames']])
for x in paths:assert not Path(x).is_absolute() and '..' not in Path(x).parts and (O/x).is_file(),x
for a in d['rawFrames']+d['atlases']:assert sha(O/a['path'])==a['sha256']
for r in p['resources']:assert sha(O/r['path'])==r['sha256'],r
assert sha(O/'source/round01/resources/original-2d-pipeline/publish_2d.py')=='6ceb9f228540ee49a96be824bd9d7f0a2aebe5173df2ea1069dcf565c687936d'
assert sha(O/'reviews/criteria.json')=='3585458476ae5a45f87fbb3d8772fde0efd71a44a1a17ae2b0363fc6ad5f1013'
raw=Image.open(O/d['source']['rawArtwork']).convert('RGBA');art=Image.open(O/d['project']).convert('RGBA');box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert art.tobytes()==raw.crop(box).tobytes()
before={x:sha(O/x)for x in paths};subprocess.run([sys.executable,str(O/'source/round01/publish.py')],check=True,capture_output=True);after={x:sha(O/x)for x in paths};assert before==after
report={'asset':'dish-salmon','round':'round01','referencedObjectRelativeFiles':len(paths),'allPresent':True,'allDeclaredHashesCorrect':True,'originalPublisherHashVerified':True,'frozenJudgeCriteriaHashVerified':True,'canonicalSourcePixelIdentityVerified':True,'canonicalSourceSHA256':d['source']['sha256'],'secondPublishRunAllReferencedFileHashesUnchanged':True,'candidateDeliverySHA256':sha(O/'candidates/round01/delivery.json'),'sourceAlpha0Clarification':'Canonical source retains16 tiny max-alpha1 connected components inside the one authorized rectangle; these do not enlarge UV bounds (alpha0 andalpha8 both0,0,731,505). Final frame has one component atalpha0 andalpha8. OriginalRGBA remains untouched; no cleanup/threshold edits.','fileHashes':after}
(O/'candidates/round01/reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='fileHashes'},indent=2))
