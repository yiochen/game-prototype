"""Capture actual Godot viewport evidence; source-closed isolated consumer.
Requires installed Godot + window renderer. Publisher replay reuses saved exact
native evidence; this script regenerates it separately on Godot-enabled systems.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile,sys
from PIL import Image
from publish import apng
S=Path(__file__).resolve().parent;O=S.parents[1];C=O/'candidates/round01';N=C/'native-context';R=S/'resources/native-capture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
R.mkdir(parents=True,exist_ok=True);godot=shutil.which('godot');assert godot;logs=[]
r=subprocess.run([godot,'--headless','--path',str(N),'--editor','--import'],capture_output=True,text=True,timeout=60);logs.append(r.stdout+r.stderr);assert r.returncode==0,logs[-1]
files=[]
for key,flags in [('native-current-context',[]),('native-current-context-posed',['--posed']),('native-reduced-motion',['--posed','--reduced']),('legacy-catalog-90',['--legacy'])]:
 dest=R/(key+'.png');r=subprocess.run([godot,'--path',str(N),'--','--output',str(dest.resolve())]+flags,capture_output=True,text=True,timeout=60);logs.append(r.stdout+r.stderr);assert r.returncode==0 and dest.exists(),logs[-1];files.append({'key':key,'name':dest.name,'sha256':sha(dest),'flags':flags})
with tempfile.TemporaryDirectory(prefix='panic-native-sequence-')as td:
 r=subprocess.run([godot,'--path',str(N),'--','--output',td,'--sequence','--posed'],capture_output=True,text=True,timeout=90);logs.append(r.stdout+r.stderr);assert r.returncode==0,logs[-1]
 frames=[Image.open(Path(td)/f'runtime-{i:04d}.png').convert('RGBA')for i in range(48)];dest=R/'native-runtime-wander-playback.png';apng(dest,frames);files.append({'key':'native-runtime-wander-playback','name':dest.name,'sha256':sha(dest),'frames':48,'fps':12,'durationSeconds':4,'poseOffsetCell':[.06,-.02],'pixelSHA256ByFrame':[hashlib.sha256(im.tobytes()).hexdigest()for im in frames]})
(R/'capture.log').write_text('\n'.join(logs))
evidence={'asset':'bubble-panic','evidence':'Actual Godot viewport frames from isolated native2D harness inheriting byte-exact current RestaurantView and ArtBook; not full production-game capture.','godotVersion':subprocess.check_output([godot,'--version'],text=True).strip(),'methods':['sprite','_customer_at','_feedback_at','customer_feedback','customer_pose_offset','ArtBook.frame_data','ArtBook.registered_rect'],'currentAttachmentLogical':[0,-172],'currentCustomer':'customer-rosa walk / phases walking and leaving / navigation_mode=wander','poseOffsetCell':[.06,-.02],'legacy':'Explicit separate -90logical seated-wait/stool screenshot; not runtime attachment','runtimeSequence':{'frames':48,'fps':12,'duration':4,'selection':'Original customer_feedback: appear t<1 then idle(t-1); exact ArtBook floor/clamp/loop; no runtime fade or timer ring','reducedMotion':'Original customer_feedback idle frame0 with seconds0'},'selectionAssertions':[json.loads(line)['selections']for log in logs for line in log.splitlines()if line.startswith('{')and '"native_capture"'in line],'runtimeScripts':{p.name:sha(p)for p in (S/'resources/context/runtime-scripts').glob('*.gd')},'harnessSHA256':sha(S/'native_capture.gd'),'candidateAtlases':{p.name:sha(p)for p in (C/'atlases').glob('*.png')},'renderSettings':'gl_compatibility; original linear_with_mipmaps;1080x760; cells128/80/50','files':files,'captureLogSHA256':sha(R/'capture.log'),'replay':'Run publisher then capture_native.py on Godot-enabled machine. Portable deterministic publisher copies retained original native evidence verbatim.'}
(R/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({'captures':len(files),'runtimeFrames':48,'evidence':str(R/'evidence.json')},indent=2))
shutil.rmtree(N/'.godot',ignore_errors=True)
for p in N.rglob('*'):
 if p.is_file()and p.name.endswith(('.import','.uid')):p.unlink()
