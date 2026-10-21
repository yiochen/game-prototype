"""Capture isolated Godot evidence. Requires local Godot and a window renderer.
The original inherited runtime methods are copied verbatim and hash retained.
This does not mutate production or claim to capture the full game scene.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
S=Path(__file__).resolve().parent;O=S.parents[1];C=O/'candidates/round01';N=C/'native-context';R=S/'resources/native-capture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
R.mkdir(parents=True,exist_ok=True);godot=shutil.which('godot');assert godot,'Godot required for actual native evidence'
logs=[]
result=subprocess.run([godot,'--headless','--path',str(N),'--editor','--import'],capture_output=True,text=True,timeout=60);logs.append(result.stdout+result.stderr);assert result.returncode==0,logs[-1]
files=[]
for posed,key in [(False,'native-current-context'),(True,'native-current-context-posed')]:
 out=C/'previews'/(key+'.png');cmd=[godot,'--path',str(N),'--','--output',str(out.resolve())]+(['--posed']if posed else[])
 result=subprocess.run(cmd,capture_output=True,text=True,timeout=60);logs.append(result.stdout+result.stderr);assert result.returncode==0,logs[-1];assert out.is_file()
 dest=R/out.name;shutil.copyfile(out,dest);files.append({'key':key,'name':dest.name,'sha256':sha(dest),'posed':posed})
(R/'capture.log').write_text('\n'.join(logs));receipt={'evidence':'Actual Godot viewport PNGs from isolated native2D harness calling copied original RestaurantView/ArtBook methods; not a full production-game capture.','godotVersion':subprocess.check_output([godot,'--version'],text=True).strip(),'attachmentLogical':[0,-172],'timer':'Original _feedback_at draw_circle/draw_arc, separate from balloon','customer':'Original _customer_at uses seated-wait-empty; actual copied customer/stool atlas bytes','poseOffsetCell':[.06,-.02],'eel':'Direct catalog-only sprite; no current customer_feedback eel selection claim','scriptSHA256':sha(S/'native_capture.gd'),'runtimeScripts':{p.name:sha(p)for p in (S/'resources/context/original-runtime-scripts').glob('*.gd')},'files':files,'logSHA256':sha(R/'capture.log'),'renderSettings':'gl_compatibility; original native2D linear with mipmaps;1080x760','replay':'Run publisher, then capture_native.py on a Godot-enabled machine; source-closed original scripts/art/metadata. Saved PNG evidence is retained verbatim for portable publisher replay.'}
(R/'evidence.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

# Disposable Godot import/cache files are not source or candidate evidence.
shutil.rmtree(N/'.godot',ignore_errors=True)
for p in N.rglob('*'):
 if p.is_file()and p.name.endswith(('.import','.uid')):p.unlink()
