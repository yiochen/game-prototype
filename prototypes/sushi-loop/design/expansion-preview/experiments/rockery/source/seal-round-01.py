"""Seal exact draft-05 native bytes with the current real consumer evidence.
Run with the bundled Python runtime (Pillow available).
"""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageChops
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n')
assert not (OUT/'packet.json').exists()
native=json.loads((BASE/'candidates/draft-05/validation.json').read_text())
audit=json.loads((BASE/'candidates/draft-05/reopened-validation.json').read_text())
alpha=json.loads((OUT/'alpha-validation.json').read_text())
consumer=json.loads((OUT/'consumer-validation.json').read_text())
assert sha(BASE/'source/draft-05.blend')==sha(BASE/'source/round-01.blend')==audit['projectSHA256']
replay={}
for d in ['N','E','S','W']:
 path=OUT/f'static-{d}.png'
 assert sha(path)==sha(BASE/f'candidates/draft-05/static-{d}.png')
 a=Image.open(path).convert('RGBA');b=Image.open(BASE/f'candidates/draft-05/reopened-{d}.png').convert('RGBA')
 delta=ImageChops.difference(a,b);extrema=delta.getextrema()
 assert all(v[1]==0 for v in extrema),extrema
 replay[d]={'allChannelMaximumDifference':0,'sourceRenderSHA256':sha(path),'reopenedRenderSHA256':sha(BASE/f'candidates/draft-05/reopened-{d}.png'),'byteIdenticalPNG':sha(path)==sha(BASE/f'candidates/draft-05/reopened-{d}.png')}
 assert alpha[d]['noAlphaClipping']
for record in native['renders']:record['path']=record['path'].replace('draft-05','round-01')
native.update({'status':'native-and-consumer-evidence-complete-awaiting-independent-review','round':1,
 'candidateProject':{'path':'source/round-01.blend','sha256':sha(BASE/'source/round-01.blend')},
 'promotion':{'from':'source/draft-05.blend','to':'source/round-01.blend','exactSourceBytes':True,'exactNativeRenderBytes':True,'noResaveNoRerenderNoArtChange':True,'provisionalReview':'reviews/draft-05.json'},
 'reopenedNativeAudit':audit,'replayComparison':replay,'alphaValidation':alpha,'consumer':consumer,
 'evidenceRecipes':{str(p.relative_to(BASE)):sha(p) for p in [BASE/'source/build-draft-05.py',BASE/'source/audit-candidate.py',BASE/'source/capture-consumer.mjs',BASE/'source/make-previews.py',Path(__file__)]}})
native['checks'].update({'nativeReopenReplayExact':True,'allNativeAlphaUnclipped':True,'actualDefaultPhoneEdgeAndCornerCaptured':True,'supplementalPanClearlyLabeled':True,'consumerPageErrorsAbsent':consumer['errors']==[],'fourNativeViewsCovered':True,'resourceClosureSelfContained':not audit['libraries'] and all(i['source']=='VIEWER' and i['filepath']=='' for i in audit['images'])})
assert all(native['checks'].values())
assert consumer['edgeCamera']=='1.25,0' and consumer['cornerCamera']=='1.25,-5'
assert len(consumer['substitutions'])==17 and consumer['existingOtherDecorKept']
write(OUT/'validation.json',native)
helper=Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py')
cmd=['python3',str(helper),'create','--brief',str(BASE/'brief.json'),'--project',str(BASE/'source/round-01.blend'),'--validation',str(OUT/'validation.json'),'--output',str(OUT/'packet.json')]
for d in ['N','E','S','W']:cmd+=['--render',f'{d}={OUT/f"static-{d}.png"}']
for name in ['four-view-sheet','phone-consumer','phone-consumer-pan','phone-edge','phone-corner','phone-edge-pan','phone-corner-pan']:
 cmd+=['--preview',f'{name}={OUT/f"{name}.png"}']
for name,p in [('native-recipe',BASE/'source/build-draft-05.py'),('reopen-audit-recipe',BASE/'source/audit-candidate.py'),('consumer-harness',BASE/'source/capture-consumer.mjs'),('preview-harness',BASE/'source/make-previews.py'),('seal-recipe',Path(__file__)),('consumer-validation',OUT/'consumer-validation.json'),('alpha-validation',OUT/'alpha-validation.json')]:
 cmd+=['--resource',f'{name}={p}']
subprocess.run(cmd,check=True)
subprocess.run(['python3',str(helper),'verify','--packet',str(OUT/'packet.json')],check=True)
print('SEALED_PACKET_SHA256',sha(OUT/'packet.json'))
