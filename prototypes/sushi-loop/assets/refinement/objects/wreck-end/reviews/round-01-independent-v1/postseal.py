from pathlib import Path
import json,hashlib,sys,platform
import PIL,numpy
E=Path(__file__).resolve().parent;OBJ=E.parent.parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();load=lambda p:json.loads(Path(p).read_text());review=OBJ/'reviews/round-01.json';supp=E/'supplemental-manifest.json';g=load(E/'gates/results.json');m=load(supp);r=load(review)
assert r['verdict']=='approve' and g['allPassed'] and g['reviewSHA256']==sha(review) and m['candidatePacketSHA256']==r['candidatePacketSHA256']
for f in m['files']:assert sha(OBJ/f['path'])==f['sha256'],f['path']
assert r['supplementalEvidence']['sha256']==sha(supp)
paths=[review,supp,E/'gate-runner.py',E/'postseal.py']+[p for p in (E/'gates').iterdir() if p.is_file()]
for p in E.rglob('*'):
 if p.is_file():assert p.stat().st_size<100_000_000 and '__pycache__' not in p.parts and p.suffix!='.pyc'
blender=Path('/opt/homebrew/bin/blender');actual=load(E/'native-audit.json')
out={'asset':'wreck-end','round':'round-01','verdict':'approve','candidatePacketSHA256':r['candidatePacketSHA256'],'candidateSourceSHA256':r['candidateSourceSHA256'],'review':{'path':'reviews/round-01.json','sha256':sha(review)},'supplementalEvidence':r['supplementalEvidence'],'pathBase':'object','postReviewFiles':[{'path':str(p.relative_to(OBJ)),'sha256':sha(p)} for p in paths],'gates':g,'allSupplementalFilesRehashed':len(m['files']),'directCoverage':{'declaredExactPaths':len(r['inspectedFiles']),'losslessFullPixelTiles':25,'rawConsumerUniqueDirect':16,'rawConsumerAliasTotal':64,'submittedHeroesDirect':4,'submittedNativeChainsDirect':4,'independentNativeChainsDirect':4},'execution':{'blenderExecutable':str(blender),'resolvedExecutable':str(blender.resolve()),'executableSHA256':sha(blender),'version':actual['blender'],'build':actual['build'],'options':['--factory-startup','--background','reviews/round-01-independent-v1/resources/candidate.blend','--python','reviews/round-01-independent-v1/resources/native-audit.py'],'pythonExecutable':sys.executable,'pythonVersion':sys.version,'PillowVersion':PIL.__version__,'numpyVersion':numpy.__version__,'bytecodeDisabled':True,'browserScope':'Actual original required8Chromium153 captures audited/visually inspected; no redundant browser reruns. Executables/options/versions/DPR/viewport retained in bound consumer/results.json and independent-analysis.json.'},'scope':'Original independent judge approves only exact wreck-end round01 packet. No modeling/source/candidate/production/shared-helper/Git/liveBlender/device change; no family/corner/publication approval. Review -> supplemental manifest -> inputs/independent evidence; postseal -> review/supplement/gate logs, without reverse reference.'}
(E/'postseal.json').write_text(json.dumps(out,indent=2)+'\n')
for f in m['files']:
 p=OBJ/f['path']
 if p.is_relative_to(E):p.chmod(p.stat().st_mode & ~0o222)
for p in paths+[E/'postseal.json']:p.chmod(p.stat().st_mode & ~0o222)
print('reviewSHA256',sha(review));print('supplementalSHA256',sha(supp));print('postsealSHA256',sha(E/'postseal.json'));print('gates passed;190 supplemental members rehashed')
