import bpy,json,sys,shutil,hashlib
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native
sc=bpy.data.scenes['Noor warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_noor.001'];root=bpy.data.objects['chef_noor__ground_root.001'];arm=bpy.data.objects['chef_noor__armature.001'];rig=json.loads((P/'rig-round01.json').read_text());asset={'collection':coll,'root':root,'armature':arm}
changed=[]
for o in coll.all_objects:
 if '__R01_apron_strap_' in o.name and 'button' not in o.name:
  before=[min(v.co.z for v in o.data.vertices),max(v.co.z for v in o.data.vertices)]
  for v in o.data.vertices:v.co.z=.360+(v.co.z-.373)*(.068/.093)
  changed.append({'object':o.name,'before':before,'after':[min(v.co.z for v in o.data.vertices),max(v.co.z for v in o.data.vertices)]})
native.apply_clip(asset,rig,'idle',1,'S',sc);shutil.copy2(P/'round-01.blend',P/'preflight-v3.blend');bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-01.blend'));(P/'strap-correction-round01.json').write_text(json.dumps({'nativeStrapConnections':changed,'sourceSHA256':hashlib.sha256((P/'round-01.blend').read_bytes()).hexdigest()},indent=2));print(changed)
