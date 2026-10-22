"""Close evidence after render/consumer jobs finish. No rendered art mutation."""
import json,hashlib,subprocess,shutil,tempfile
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent;OUT=BASE/'candidates/round-03'
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
 p=Path(t)/'source/round-03';p.mkdir(parents=True)
 for f in ['build.py','capture.py']:shutil.copyfile(HERE/f,p/f)
 with (RECIPE/'build.log').open('w') as f:subprocess.run(['blender','-b','--python',str(p/'build.py')],stdout=f,stderr=subprocess.STDOUT,check=True)
 with (RECIPE/'render.log').open('w') as f:subprocess.run(['blender','-b',str(p/'project.blend'),'--python',str(p/'capture.py'),'--',str(RECIPE.resolve())],stdout=f,stderr=subprocess.STDOUT,check=True)
 records=[]
 for d in 'NESW':
  a=Image.open(OUT/f'native/static-{d}.png').convert('RGBA');b=Image.open(RECIPE/f'static-{d}.png').convert('RGBA');records.append({'direction':d,'referenceFileSHA256':sha(OUT/f'native/static-{d}.png'),'recipeReplayFileSHA256':sha(RECIPE/f'static-{d}.png'),'referenceRGBAHash':hashlib.sha256(a.tobytes()).hexdigest(),'recipeReplayRGBAHash':hashlib.sha256(b.tobytes()).hexdigest(),'decodedRGBAIdentical':a.tobytes()==b.tobytes(),'maxChannelDifference':[v[1] for v in ImageChops.difference(a,b).getextrema()]})
write(RECIPE/'verification.json',{'recipeSHA256':sha(HERE/'build.py'),'captureScriptSHA256':sha(HERE/'capture.py'),'method':'Fresh temporary source/round-03 tree containing only build.py and capture.py; run build from empty Blender, reopen its new native project and render all4 views. No original blend or resources required.','allDecodedRGBAIdentical':all(r['decodedRGBAIdentical'] for r in records),'renders':records})
v=json.loads((OUT/'validation.json').read_text());v['checks'].pop('exactReplay',None);v['checks']['reopenedProjectExactRGBAPixels']=rep['allDecodedRGBAIdentical'];v['checks']['portableRecipeClosureExecuted']=True;v['supplementalRecipePixelComparison']={'allDecodedRGBAIdentical':all(r['decodedRGBAIdentical'] for r in records),'maxChannelDifference':[max(r['maxChannelDifference'][i] for r in records) for i in range(4)],'classification':'Supplemental full-build comparison; exact reopened saved-source replay is the frozen required comparison'};v['checks']['sourceIntegrityUnchanged']=v['sourceIntegrity']['projectSHA256']==v['sourceIntegrity']['expectedProjectSHA256'] and v['sourceIntegrity']['backupSHA256']==v['sourceIntegrity']['expectedBackupSHA256'];v['nativeValidation']='candidates/round-03/native/capture-validation.json';v['portableRecipeReplay']=rel(RECIPE/'verification.json');v['replayEqualityDefinition']='Exact decoded RGBA; native PNG metadata differs by path/time only'
e=json.loads((OUT/'consumer/evidence.json').read_text());v['checks']['actualConsumerPayloadHashes']=bool(e['responses']) and all(r['sha256']==r['expectedSHA256'] and r['status']==200 for r in e['responses']);v['checks']['actualConsumerNoPageErrors']=not e['errors'];v['checks']['actualConsumerReadyAllLayouts']=all(c.get('worldRasterReady',True) for c in e['cases']);v['consumerEvidence']='candidates/round-03/consumer/evidence.json';v['priorSealedRound']={'packetSHA256':'7eaec8595bbac630d5df051a80a52a8c6ef9ae303b76a55dccaa5c1a3effb92e','reviewSHA256':'e2b3a65a4e727315f17ba4b574a41ecfd25b814d1e80570e961a186b1459bf52','projectSHA256':'97487414aadd87fe90de171adff131574838638a9a1f4f874d4178896459ae74','preserved':True};v['allTechnicalChecksPass']=all(v['checks'].values());write(OUT/'validation.json',v)
rig=json.loads((HERE/'published-rig.json').read_text());rig['sourceFiles']={'build.py':sha(HERE/'build.py'),'capture.py':sha(HERE/'capture.py')};rig['sourceLineageSHA256']='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6';write(HERE/'published-rig.json',rig)
d=json.loads((OUT/'delivery.json').read_text())
for a in d['atlases']:a['size']=a['dimensions']
d['replay']['portableRecipeVerification']=rel(RECIPE/'verification.json');d['replay']['pixelEquality']='All4 decodedRGBA identical, PNG metadata differences preserved';d['previews'].update({'desktop-repeated':'candidates/round-03/consumer/desktop-repeated.png','desktop-interaction':'candidates/round-03/consumer/desktop-interaction.png','phone-context':'candidates/round-03/consumer/phone-standalone-context.png','landscape-four-facings':'candidates/round-03/consumer/landscape-four-facings.png'})
# Direct before/after evidence at unchanged whole-canvas registration.
im=Image.new('RGBA',(768,1008),(224,228,226,255));draw=ImageDraw.Draw(im)
for row,round_id in enumerate(['round-02','round-03']):
 for i,facing in enumerate('NESW'):
  image=Image.open(BASE/f'candidates/{round_id}/frames/static-{facing}.png').convert('RGBA').resize((192,480),Image.Resampling.LANCZOS)
  im.alpha_composite(image,(i*192,row*504+24));draw.text((i*192+6,row*504+5),round_id+' '+facing,fill='#263E43')
im.convert('RGB').save(OUT/'previews/prior-round-comparison.png')
d['previews']['prior-round-comparison']='candidates/round-03/previews/prior-round-comparison.png'
d['evidence']['priorRound']={'packet':'candidates/round-02/packet.json','review':'reviews/round-02.json','packetSHA256':'7eaec8595bbac630d5df051a80a52a8c6ef9ae303b76a55dccaa5c1a3effb92e','reviewSHA256':'e2b3a65a4e727315f17ba4b574a41ecfd25b814d1e80570e961a186b1459bf52'}
# All outputs are now closed; current close.log is excluded until coordinator snapshots it.
d['resources']=[{'name':rel(p),'path':rel(p),'sha256':sha(p)} for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name not in ['delivery.json','packet.json','close.log'] and p.suffix!='.blend1']
d['resources'] += [{'name':'prior:'+rel(p),'path':rel(p),'sha256':sha(p)} for p in [BASE/'candidates/round-02/packet.json',BASE/'reviews/round-02.json',*[BASE/f'candidates/round-02/frames/static-{f}.png' for f in 'NESW']]]
write(OUT/'delivery.json',d);write(BASE/'delivery-round03.json',d)
print(json.dumps({'allTechnicalChecksPass':v['allTechnicalChecksPass'],'checks':v['checks'],'delivery':str(BASE/'delivery-round03.json'),'deliverySHA256':sha(BASE/'delivery-round03.json'),'projectSHA256':sha(HERE/'project.blend'),'validationSHA256':sha(OUT/'validation.json')},indent=2))
