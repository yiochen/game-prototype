"""Bind this preparation scope; this is not a candidate/approval packet."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;O=P.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'seal.json').exists(), 'Never overwrite a signed preparation'
expected={
 'resources/native/original.blend':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6',
 'resources/inputs/original.png':'63780a765b0060bd3e20cca0cd153bf780ea05c686f8cb4f0ec6565025c4b4f0',
 'resources/inputs/target.png':'02546fbfa042e8c958beae0cf4520d87bc40d0951c5d490bfd2b63f33ae7b15b',
 'resources/inputs/warm-soft-reference.png':'02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15',
 'resources/instructions/dispatch.txt':'8693ab7a0d78e9eeb3d29aa6f14e9b163fbd90a797d12c1fb6ae92a0d8084926',
 'resources/consumer/world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545',
 'resources/consumer/sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
for n,s in expected.items():assert sha(P/n)==s,(n,sha(P/n))
metrics=json.loads((P/'verification-metrics.json').read_text());assert metrics['sourceReplay']['frames']==48 and metrics['sourceReplay']['all48PublishedDecodedRGBAExact'] and metrics['sourceReplay']['maxBorderAlpha']==0
assert len(list((P/'raw').rglob('*.png')))==48
for f,m in metrics['nativeFacings'].items():assert m['uniqueDecodedFrames']==12 and m['frame13VsFrame1TransformMaxAbs']==0 and m['supportTransformsStable']
for m in metrics['consumer'].values():assert not m['errors'] and m['updates']==27 and m['expectedFrameSequence'] and m['noSkippedFrames']
# Browser CSS residuals are evidence, not a required exact-match gate.
assert metrics['consumerCanvasBeforeCSS']['allSampledNativeCanvasPNGHashesExactAcrossModes']
assert not list(P.rglob('__pycache__'))
for n in ['initial.json','criteria.json']:assert (P/n).read_bytes()==(P.parent/n).read_bytes()
files=[p for p in P.rglob('*') if p.is_file() and p.name not in ['hash-manifest.json','seal.json']]+[P.parent/'initial.json',P.parent/'criteria.json']
assert all(p.stat().st_size<100_000_000 for p in files)
manifest={'asset':'portal-rim','stage':'preparation-only','pathBase':'portal-rim object directory','objectRoot':str(O),'fileCount':len(files),'totalBytes':sum(p.stat().st_size for p in files),'files':[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)]}
(P/'hash-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'portal-rim','stage':'preparation-only','status':'sealed-pending-root-reconciliation-and-freeze','candidateApproval':False,'manifest':{'path':'reviews/preparation-v1/hash-manifest.json','sha256':sha(P/'hash-manifest.json')},'fileCount':len(files),'sourceSHA256':expected['resources/native/original.blend'],'dispatchSHA256':expected['resources/instructions/dispatch.txt'],'criteria':{'path':'reviews/preparation-v1/criteria.json','sha256':sha(P/'criteria.json'),'status':'proposed-not-frozen'},'contract':{'path':'reviews/preparation-v1/root-native-contract.json','sha256':sha(P/'root-native-contract.json'),'status':'proposed-not-frozen'},'scope':'No candidate construction, source editing, candidate/family/production approval, integration, deployment, Git/index, device/liveBlender or extra agents.'}
(P/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
# Read back every sealed member; do not claim a seal without byte verification.
for r in manifest['files']:assert sha(O/r['path'])==r['sha256']
assert sha(P/'hash-manifest.json')==seal['manifest']['sha256']
print(json.dumps({'sealSHA256':sha(P/'seal.json'),'manifestSHA256':seal['manifest']['sha256'],'contractSHA256':seal['contract']['sha256'],'criteriaSHA256':seal['criteria']['sha256'],'fileCount':len(files),'totalBytes':manifest['totalBytes'],'verified':True},indent=2))
