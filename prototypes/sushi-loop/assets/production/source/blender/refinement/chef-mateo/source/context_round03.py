import sys
sys.dont_write_bytecode=True
"""Read-only native serving context, at the same35-degree/256native-px-per-cell.
Neighbors come from the untouched original library; no production edits/saves.
The review canvas is larger, but world scale, elevation and renderer stay fixed.
"""
import bpy,json,math,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round03';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
BASE=HERE.parents[3]/'production/source';spec=importlib.util.spec_from_file_location('mateo_context_actions',HERE/'native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
scene=bpy.data.scenes['Mateo warm soft native round02'];bpy.context.window.scene=scene
rig=json.loads((OUT/'rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in scene.collection.children if root in list(c.all_objects));asset={'root':root,'collection':collection}
rr=json.loads((HERE/'context-customer-rosa-rig.json').read_text())
ra={t['action'] for cd in rr['clips'].values() for t in cd['actions']}
with bpy.data.libraries.load(str(HERE/'original-library.blend'),link=False) as (src,dst):
 wanted=[c for c in src.collections if c in ['S33_FB_belt-straight-e.001','S33_CHARACTER_customer_rosa.001']]
 assert len(wanted)==2,wanted
 dst.collections=wanted;dst.actions=[a for a in src.actions if a in ra]
for c in dst.collections:
 scene.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 for o in c.all_objects:o.hide_set(False)
beltroot=bpy.data.objects['belt-straight-e__root.001'];beltroot.location=(0,-.75,0)
rosaroot=bpy.data.objects[rr['groundRootObject']];rosacoll=next(c for c in dst.collections if rosaroot in list(c.all_objects))
n.apply_clip({'root':rosaroot,'collection':rosacoll},rr,'stand',1,'S',scene);rosaroot.location=(1.05,-.82,0)
cam=scene.camera;cam.data.ortho_scale=4
scene.render.resolution_x=1024;scene.render.resolution_y=768
cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return [p.x*1024,(1-p.y)*768]
base=pixel((0,0,0));cam.data.shift_x=1;bpy.context.view_layer.update();dx=pixel((0,0,0))[0]-base[0];cam.data.shift_x=(384-base[0])/dx
cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0))[1]-base[1];cam.data.shift_y=(560-base[1])/dy;bpy.context.view_layer.update()
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for device in prefs.devices:device.use=device.type=='METAL'
rows=[]
for clip,frame in [('work',4),('hold',1),('load',12)]:
 n.apply_clip(asset,rig,clip,frame,'S',scene)
 # Restore stand since the scene-global frame advances with Mateo's unchanged clip.
 for target in rr['clips']['stand']['actions']:
  n._assign(n._resolve_owner(target),bpy.data.actions[target['action']],target.get('slotIdentifier'))
 scene.frame_set(frame);bpy.context.view_layer.update()
 path=PRE/('native-serving-context-'+clip+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 rows.append({'clip':clip,'frame':frame,'path':str(path.relative_to(OBJ)),'chefRoot':list(root.matrix_world.translation),'beltRoot':list(beltroot.matrix_world.translation),'customerRoot':list(rosaroot.matrix_world.translation),'chefRootProjected':pixel(root.matrix_world.translation),'sourcePropRootProjected':pixel(bpy.data.objects['chef_mateo__ground_root.001__held_dish-salmon'].matrix_world.translation),'worldMatrix':[[v for v in r] for r in cam.matrix_world]})
report={'kind':'Native review context only; unchanged source belt/customer at recorded world scale. Not a new game station or modified gameplay layout.','projection':'Same recorded35-degree camera orientation and square pixels; larger1024x768 review canvas at256nativepx/world-cell matches384/1.5 main capture. No visible-bound fitting.','neighborsSourceSHA256':hashlib.sha256((HERE/'original-library.blend').read_bytes()).hexdigest(),'food':'Exact canonical salmon remains explicitly2D on the single mapped native plane, with unchanged intentional source camera-ray depth bias. Projected attachment parity is validated independently; this context does not claim its plane is physical sushi geometry.','renders':rows,'camera':{'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'resolution':[1024,768]},'noProjectSaved':True}
(OUT/'serving-context-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('MATEO_CONTEXT_DONE',json.dumps(rows))
