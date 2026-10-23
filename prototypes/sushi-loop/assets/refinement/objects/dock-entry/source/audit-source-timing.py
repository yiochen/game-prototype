import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1];p=B/'source/round-05.blend';bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene
r={'project':'source/round-05.blend','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actualSceneUIFrameRate':s.render.fps,'actualSceneUIFrameRange':[s.frame_start,s.frame_end],'actualSavedFrame':s.frame_current,'actionCount':len(bpy.data.actions),'nativeCaptureFrame':1,'exportClip':{'clip':'static','frames':1,'fps':12,'loop':False,'frameOrder':[0]},'interpretation':'The native asset has no animated mechanics/actions. Each facing exports the single captured frame1; static atlas playback is explicitly1frame at12fps. Saved scene UI factory range/rate are disclosed independently of static clip timing; immutable exchanged project is retained.'}
(B/'candidates/round-05/source-timing-audit.json').write_text(json.dumps(r,indent=2));print(r)
