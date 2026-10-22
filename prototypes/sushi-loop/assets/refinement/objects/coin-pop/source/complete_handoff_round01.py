from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent.parent;C=O/'candidates/round-01';S=O/'source';P=C/'previews'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
d=json.loads((O/'delivery.json').read_text());frames={(r['clip'],r['direction'],r['index']):r for r in d['rawFrames']};rects=[[i%6*384,i//6*704,384,704]for i in range(12)]
for a in d['atlases']:
 assert a['columns']==6 and a['rows']==2 and a['size']==[2304,1408] and a['fps']==12 and a['loop'] is False and a['frameOrder']==list(range(12)) and a['rects']==rects
 im=Image.open(O/a['path']).convert('RGBA');assert im.size==(2304,1408) and sha(O/a['path'])==a['sha256']
 for i,(x,y,w,h) in enumerate(rects):
  r=frames['pop',a['direction'],i];raw=Image.open(O/r['path']).convert('RGBA');assert raw.size==(384,704)and im.crop((x,y,x+w,y+h)).tobytes()==raw.tobytes()and sha(O/r['path'])==r['sha256']
ledger=json.loads((C/'candidate-phases.json').read_text());expected={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
assert all(abs(math.atan2(math.sin(r['rootRotationZ']-expected[r['direction']]),math.cos(r['rootRotationZ']-expected[r['direction']])))<1e-4 for r in ledger)
write(C/'import-readiness.json',{'asset':'coin-pop','checks':{'explicit48RawFrames':len(frames)==48,'exactOriginalWholeCanvasAtlasCrops':True,'originalAtlasLayoutAndTiming':True,'directionAuditMeasuredLedgerCompatible':True,'cameraScale2LogicalFrame192x352Root96x256':True,'allByteBearingSourceDraftPreviewFilesDeclared':True},'helpersInspected':['tools/promote_object.py','tools/audit_directions.py','tools/save_runtime_variant_approval.py','godot/tools/refined_actor_variants.py'],'actorRuntimeVariantReceipt':'not applicable: coin-pop is an effect; the current .9second consumer is demonstrated by actual Godot viewport capture. Main atlas retains12frames at12fps nonloop.','directionEvidence':{'path':'candidates/round-01/candidate-phases.json','sha256':sha(C/'candidate-phases.json')},'promotion':'Root seals this delivery and obtains independent judge review before import. No self-approval.'})
# Native comparison at identical registration; no effect-bound fitting.
sh=Image.new('RGB',(768,740),'#f8f1df');dr=ImageDraw.Draw(sh)
for n,(label,path)in enumerate([('SOURCE / frame5',O/'inputs/original.png'),('NATIVE / frame5',C/'raw/pop-S/005.png')]):
 im=Image.open(path).convert('RGBA');assert im.size==(384,704);bg=Image.new('RGBA',(384,704),'#f8f1df');bg.alpha_composite(im);sh.paste(bg.convert('RGB'),(n*384,36));dr.text((n*384+12,12),label+' / same384x704 root192,512',fill='#253b3b')
sh.save(P/'registered-original-candidate.png')
write(C/'playback-evidence.json',{'asset':'coin-pop','actualMoviesPlayedInBrowser':True,'page':'candidates/round-01/previews/playback.html','nativeClip':{'path':'candidates/round-01/previews/native-pop-all4.mp4','sha256':sha(P/'native-pop-all4.mp4'),'fps':12,'durationSeconds':1.0,'frames':12,'loop':False},'actualGodotClip':{'path':'candidates/round-01/previews/godot-runtime-fade.mp4','sha256':sha(P/'godot-runtime-fade.mp4'),'fps':30,'durationSeconds':1.2,'frames':36,'loop':False,'fadeSeconds':.9},'browserProof':{'completeState':'candidates/round-01/previews/playback-complete.txt','completeScreenshot':'candidates/round-01/previews/playback-complete.png','motionScreenshot':'candidates/round-01/previews/runtime-playback-observed.png'},'observed':'Both browser videos emitted play, advancing timeupdate and ended; native duration1s, runtime1.2s. Actual runtime viewport movie observed at age.267 with128/64px repeated contexts. Technical evidence and observation, not an independent aesthetic verdict.'})
d['previews'].update({'comparison':'candidates/round-01/previews/registered-original-candidate.png','playback-complete':'candidates/round-01/previews/playback-complete.png','playback-observed-runtime':'candidates/round-01/previews/runtime-playback-observed.png'})
resources={}
for base in [S,O/'candidates']:
 for p in sorted(base.rglob('*')):
  if p.is_file()and '__pycache__'not in p.parts and '.godot'not in p.parts and p.name not in ['delivery.json','delivery.snapshot.json','packet.json','resource-hashes.json']:
   resources[p.relative_to(O).as_posix()]=p.relative_to(O).as_posix()
write(C/'resource-hashes.json',{'files':[{'path':p,'sha256':sha(O/p)}for p in resources.values()]})
resources['candidates/round-01/resource-hashes.json']='candidates/round-01/resource-hashes.json';d['resources']=resources
write(O/'delivery.json',d)
print(json.dumps({'delivery':str(O/'delivery.json'),'deliverySHA256':sha(O/'delivery.json'),'projectSHA256':sha(S/'round-01.blend'),'nativeRecipeSHA256':sha(S/'build_round01.py'),'validationSHA256':sha(C/'validation.json'),'measuredLedgerSHA256':sha(C/'candidate-phases.json'),'resources':len(resources),'atlases':len(d['atlases']),'rawFrames':len(d['rawFrames'])},indent=2))
