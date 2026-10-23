"""Verify referenced dependencies, unchanged repeat publication and isolated closure."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,shutil
from PIL import Image
O=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((O/'delivery.json').read_text());p=json.loads((O/d['provenance']).read_text())
paths=sorted(set(d['resources']+[d['project'],d['recipe'],d['recipeManifest'],d['validation'],d['provenance'],d['captureRecipe'],d['packagingRecipe'],d['preparationRecipe']]+list(d['heroes'].values())+list(d['previews'].values())+[a['path']for a in d['atlases']]+[a['path']for a in d['rawFrames']]))
for x in paths:assert not Path(x).is_absolute() and '..' not in Path(x).parts and (O/x).is_file(),x
for a in d['rawFrames']+d['atlases']:assert sha(O/a['path'])==a['sha256']
for r in p['resources']:assert sha(O/r['path'])==r['sha256'],r
frozen=json.loads((O/'source/round01/resources/frozen-brief.json').read_text())
assert sha(O/'source/round01/resources/frozen-criteria.json')==frozen['qualityCriteria']['criteriaFileSHA256']=='601e583c30393a0eb05ff15d307c054c8b148c4eaf99801f963a28ec1c28a5e9'
raw=Image.open(O/d['source']['rawArtwork']).convert('RGBA');art=Image.open(O/d['project']).convert('RGBA');box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();assert art.tobytes()==raw.crop(box).tobytes()
before={x:sha(O/x)for x in paths};subprocess.run([sys.executable,str(O/d['recipe'])],check=True,capture_output=True);after={x:sha(O/x)for x in paths};assert before==after
# Only declared resources and current outputs are copied. No original experiment,
# production tree, sibling candidate, reviews folder or undeclared criteria path.
with tempfile.TemporaryDirectory(prefix='dish-eel-closed-copy-') as temp:
 closed=Path(temp)/'dish-eel';closed.mkdir()
 for x in paths:
  dest=closed/x;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/x,dest)
 shutil.copyfile(O/'delivery.json',closed/'delivery.json')
 subprocess.run([sys.executable,str(closed/d['preparationRecipe'])],check=True,capture_output=True)
 subprocess.run([sys.executable,str(closed/d['recipe'])],check=True,capture_output=True)
 closed_hashes={x:sha(closed/x)for x in paths};assert before==closed_hashes
report={'asset':'dish-eel','round':'round01','referencedObjectRelativeFiles':len(paths),'allPresent':True,'allDeclaredHashesCorrect':True,'frozenJudgeCriteriaHashVerified':True,'canonicalSourcePixelIdentityVerified':True,'canonicalSourceSHA256':d['source']['sha256'],'secondPublishRunAllReferencedFileHashesUnchanged':True,'closedCopyPreparationAndPublication':True,'closedCopyAllReferencedHashesUnchanged':True,'closedCopyContainsOnlyDeclaredFiles':True,'closedCopyRequiresOriginalExperiment':False,'candidateDeliverySHA256':sha(O/'candidates/round01/delivery.json'),'dependencyPolicy':'All recipe-read inputs are explicitly declared object-relative resources, including copied frozen criteria. Existing held captures are historical other-recipe evidence only. No native/bubble recapture approval.','fileHashes':after}
(O/'candidates/round01/reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='fileHashes'},indent=2))
