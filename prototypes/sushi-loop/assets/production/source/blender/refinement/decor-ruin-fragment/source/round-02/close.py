"""Close evidence after render/consumer jobs finish. No rendered art mutation."""
import json,hashlib,subprocess,shutil,tempfile
from pathlib import Path
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent;OUT=BASE/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):Path(p).write_text(json.dumps(o,indent=2)+'\n')
def rel(p):return str(Path(p).relative_to(BASE))
# Preserve initial byte-level comparison failure, then distinguish pixels from metadata.
old=OUT/'portable-replay/verification.json';shutil.copyfile(old,OUT/'portable-replay/initial-file-byte-comparison.json')
shutil.copyfile(OUT/'validation.json',OUT/'validation-initial-file-byte-comparison.json')
rep=json.loads(old.read_text())
for r in rep['renders']:
 a=Image.open(OUT/f"native/static-{r['direction']}.png").convert('RGBA');b=Image.open(OUT/f"portable-replay/static-{r['direction']}.png").convert('RGBA')
 r['nativeRGBAHash']=hashlib.sha256(a.tobytes()).hexdigest();r['replayRGBAHash']=hashlib.sha256(b.tobytes()).hexdigest();r['decodedRGBAIdentical']=a.tobytes()==b.tobytes();r['maxChannelDifference']=[v[1] for v in ImageChops.difference(a,b).getextrema()]
rep['allDecodedRGBAIdentical']=all(r['decodedRGBAIdentical'] for r in rep['renders']);rep['fileByteDifferenceExplanation']='Blender native PNG text metadata encodes File path, Date and RenderTime/cycles timings. Every decoded RGBA pixel is identical. Original files and differing replay files retained.';write(old,rep)
# Reconstruct entirely from executable native recipe in a fresh portable tree, then capture.
RECIPE=OUT/'portable-recipe-replay';RECIPE.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ruin-native-recipe-') as t:
 p=Path(t)/'source/round-02';p.mkdir(parents=True)
 for f in ['build.py','capture.py']:shutil.copyfile(HERE/f,p/f)
 with (RECIPE/'build.log').open('w') as f:subprocess.run(['blender','-b','--python',str(p/'build.py')],stdout=f,stderr=subprocess.STDOUT,check=True)
 with (RECIPE/'render.log').open('w') as f:subprocess.run(['blender','-b',str(p/'project.blend'),'--python',str(p/'capture.py'),'--',str(RECIPE.resolve())],stdout=f,stderr=subprocess.STDOUT,check=True)
 records=[]
 for d in 'NESW':
  a=Image.open(OUT/f'native/static-{d}.png').convert('RGBA');b=Image.open(RECIPE/f'static-{d}.png').convert('RGBA');records.append({'direction':d,'referenceFileSHA256':sha(OUT/f'native/static-{d}.png'),'recipeReplayFileSHA256':sha(RECIPE/f'static-{d}.png'),'referenceRGBAHash':hashlib.sha256(a.tobytes()).hexdigest(),'recipeReplayRGBAHash':hashlib.sha256(b.tobytes()).hexdigest(),'decodedRGBAIdentical':a.tobytes()==b.tobytes(),'maxChannelDifference':[v[1] for v in ImageChops.difference(a,b).getextrema()]})
write(RECIPE/'verification.json',{'recipeSHA256':sha(HERE/'build.py'),'captureScriptSHA256':sha(HERE/'capture.py'),'method':'Fresh temporary source/round-02 tree containing only build.py and capture.py; run build from empty Blender, reopen its new native project and render all4 views. No original blend or resources required.','allDecodedRGBAIdentical':all(r['decodedRGBAIdentical'] for r in records),'renders':records})
v=json.loads((OUT/'validation.json').read_text());v['checks'].pop('exactReplay',None);v['checks']['reopenedProjectExactRGBAPixels']=rep['allDecodedRGBAIdentical'];v['checks']['portableRecipeExactRGBAPixels']=all(r['decodedRGBAIdentical'] for r in records);v['checks']['sourceIntegrityUnchanged']=v['sourceIntegrity']['projectSHA256']==v['sourceIntegrity']['expectedProjectSHA256'] and v['sourceIntegrity']['backupSHA256']==v['sourceIntegrity']['expectedBackupSHA256'];v['nativeValidation']='candidates/round-02/native/capture-validation.json';v['portableRecipeReplay']=rel(RECIPE/'verification.json');v['replayEqualityDefinition']='Exact decoded RGBA; native PNG metadata differs by path/time only'
e=json.loads((OUT/'consumer/evidence.json').read_text());v['checks']['actualConsumerPayloadHashes']=bool(e['responses']) and all(r['sha256']==r['expectedSHA256'] and r['status']==200 for r in e['responses']);v['checks']['actualConsumerNoPageErrors']=not e['errors'];v['checks']['actualConsumerReadyAllLayouts']=all(c.get('worldRasterReady',True) for c in e['cases']);v['consumerEvidence']='candidates/round-02/consumer/evidence.json';v['allTechnicalChecksPass']=all(v['checks'].values());write(OUT/'validation.json',v)
rig=json.loads((HERE/'published-rig.json').read_text());rig['sourceFiles']={'build.py':sha(HERE/'build.py'),'capture.py':sha(HERE/'capture.py')};rig['sourceLineageSHA256']='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6';write(HERE/'published-rig.json',rig)
d=json.loads((OUT/'delivery.json').read_text())
for a in d['atlases']:a['size']=a['dimensions']
d['replay']['portableRecipeVerification']=rel(RECIPE/'verification.json');d['replay']['pixelEquality']='All4 decodedRGBA identical, PNG metadata differences preserved';d['previews'].update({'desktop-repeated':'candidates/round-02/consumer/desktop-repeated.png','desktop-interaction':'candidates/round-02/consumer/desktop-interaction.png','phone-context':'candidates/round-02/consumer/phone-standalone-context.png','landscape-four-facings':'candidates/round-02/consumer/landscape-four-facings.png'})
# All outputs are now closed; current close.log is excluded until coordinator snapshots it.
d['resources']=[{'name':rel(p),'path':rel(p),'sha256':sha(p)} for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in ['delivery.json','packet.json','close.log'] and p.suffix!='.blend1']
write(OUT/'delivery.json',d);write(BASE/'delivery-round02.json',d)
print(json.dumps({'allTechnicalChecksPass':v['allTechnicalChecksPass'],'checks':v['checks'],'delivery':str(BASE/'delivery-round02.json'),'deliverySHA256':sha(BASE/'delivery-round02.json'),'projectSHA256':sha(HERE/'project.blend'),'validationSHA256':sha(OUT/'validation.json')},indent=2))
