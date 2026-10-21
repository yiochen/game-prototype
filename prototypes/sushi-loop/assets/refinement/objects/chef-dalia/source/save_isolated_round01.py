import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native
recipe=json.loads((P/'recipe-round01.json').read_text());rig=json.loads((P/'rig-round01.json').read_text())
sc=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=sc
for other in list(bpy.data.scenes):
 if other!=sc:bpy.data.scenes.remove(other)
coll=bpy.data.collections[recipe['collection']];root=bpy.data.objects[recipe['root']];arm=bpy.data.objects[recipe['armature']]
native.apply_clip({'collection':coll,'root':root,'armature':arm},rig,'idle',1,'S',sc)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
# Pack original dependency bytes already preserved under source/dependencies/.
for im in bpy.data.images:
 if im.type!='RENDER_RESULT' and not im.packed_file and im.users:im.pack()
for _ in range(3):bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'round-01.blend'),compress=True)
print('ISOLATED_NORMAL_MAINFILE',bpy.context.scene.name,len(bpy.data.scenes),len(bpy.data.objects),[(im.name,bool(im.packed_file)) for im in bpy.data.images])
