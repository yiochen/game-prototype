"""Retain exact closed copied-package replay evidence after final192 capture."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib,sys
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';closed=Path(sys.argv[1]);proof=HERE/'portability-proof-round03';proof.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(closed/'source/round-03.blend')==sha(HERE/'round-03.blend')
assert sha(closed/'source/audit-round03-occlusion.py')==sha(HERE/'audit-round03-occlusion.py')
shutil.copytree(closed/'candidates/round-03/preflight',proof/'preflight',dirs_exist_ok=True)
for src,dst in [(closed/'closed-capture.log','capture.log'),(closed/'candidates/round-03/native-audit.json','native-audit.json'),(closed/'candidates/round-03/occlusion-native-audit.json','occlusion-native-audit.json'),(closed/'candidates/round-03/closed-package-environment.json','environment.json')]:shutil.copy2(src,proof/dst)
records=[]
for p in sorted((proof/'preflight').glob('*.png')):
 q=OUT/'frames'/p.name;im=Image.open(p).convert('RGBA');jm=Image.open(q).convert('RGBA');equal=im.tobytes()==jm.tobytes();assert equal,p.name
 records.append(dict(path=str(p.relative_to(OBJ)),finalFrame=str(q.relative_to(OBJ)),decodedRGBAEqual=equal,sha256=sha(p)))
assert len(records)==20
main=json.loads((OUT/'occlusion-native-audit.json').read_text());replay=json.loads((proof/'occlusion-native-audit.json').read_text());assert main['allChecksPassed'] and replay['allChecksPassed']
rows_equal=main['records']==replay['records'];angles_equal=main['intermediateAngles']==replay['intermediateAngles'];assert rows_equal and angles_equal
assert not any(p.is_symlink() for p in closed.rglob('*'))
inputs=[dict(path=str(p.relative_to(closed)),sha256=sha(p)) for p in sorted(closed.rglob('*')) if p.is_file() and 'candidates' not in p.parts and p.name!='closed-capture.log' and '__pycache__' not in p.parts]
report=dict(activeBrief='brief-v4-food-occlusion.json',source='source/round-03.blend',sourceSHA256=sha(HERE/'round-03.blend'),closedCopiedObject=str(closed),copiedInputFiles=inputs,noSymlinks=True,siblingObjectFoldersPresent=False,productionFoldersPresent=False,linkedLibraries=0,exactCanonicalImagePacked=True,packedReloadFromMissingExternalPath=True,all192NativeAuditPassed=json.loads((proof/'native-audit.json').read_text())['allChecksPassed'],all192OcclusionRowsExactlyEqual=rows_equal,all29IntermediateAngleRowsExactlyEqual=angles_equal,representativeRecaptures=records,all20DecodedRGBAEqual=True,scope='Closed-resource saved-source replay, exact full192 native evaluation+29 continuous-angle checks+20 representative renders. No original-library reconstruction claim; no native source saved in replay.',command='/opt/homebrew/bin/blender -b source/round-03.blend --python source/closed-package-round03-test.py -- --preview')
(proof/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
canvas=Image.new('RGB',(1536,340),(109,113,119));draw=ImageDraw.Draw(canvas)
for x,(c,d) in enumerate((c,d) for c in ['hold','load'] for d in ['N','E','S','W']):
 im=Image.open(proof/f'preflight/{c}-{d}-{5 if c=="load" else 0:02}.png').resize((192,320));canvas.paste(im,(x*192,20),im);draw.text((x*192+4,3),f'Closed replay {c} {d}',fill='white')
canvas.save(proof/'held-load-all-facings.png');print('Closed replay:192 rows+29 intermediate rows+20 PNGs exact')
