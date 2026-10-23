import bpy,json,sys,hashlib,shutil
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native
sc=bpy.data.scenes['Lena warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];rig=json.loads((P/'rig-round01.json').read_text());asset={'collection':coll,'root':root,'armature':arm};native.apply_clip(asset,rig,'idle',1,'S',sc)
for other in list(bpy.data.scenes):
 if other!=sc:bpy.data.scenes.remove(other)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
old=P/'round-01-library.blend';shutil.copy2(P/'round-01.blend',old)
# Ordinary .blend saves active scene/workspace; no geometry/material/action/camera changes.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-01.blend'))
report={'operation':'Serialize same isolated scene as ordinary editable mainfile with active registered camera scene','oldLibrarySHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'finalProjectSHA256':hashlib.sha256((P/'round-01.blend').read_bytes()).hexdigest(),'scene':sc.name,'camera':sc.camera.name,'artChanges':False,'reproductionEvidence':'candidates/round-01/reproduction-manifest.json'};(P/'finalization-round01.json').write_text(json.dumps(report,indent=2))
