"""Native review contexts with declared neighbor grid placements. No production write."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-05';CTX=OUT/'contexts-side';CTX.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round05 as native
rig=json.loads((P/'rig-round05.json').read_text());sc=bpy.data.scenes['Ellis warm soft round04'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];asset={'root':root,'collection':coll,'armature':bpy.data.objects['chef_ellis__armature.001']}
rosaRig=json.loads((P/'dependencies/round05/customer-rosa-rig.json').read_text())
rosaActions={x['action'] for c in rosaRig['clips'].values() for x in c['actions']}
wanted=['S33_FB_belt-straight-e.001','S33_CHARACTER_customer_rosa.001','S33_PROP_stool_wood.001']
with bpy.data.libraries.load(str(P/'original-library.blend'),link=False) as (src,dst):
 dst.collections=[c for c in src.collections if c in wanted];dst.actions=[a for a in src.actions if a in rosaActions]
print('APPENDED',[(c.name,len(c.all_objects)) for c in dst.collections],flush=True)
for c in dst.collections:
 sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 for o in c.all_objects:o.hide_set(False)
belt=next(c for c in dst.collections if 'belt-straight-e' in c.name);beltroot=next(o for o in belt.objects if o.parent is None)
rosa=next(c for c in dst.collections if 'customer_rosa' in c.name);rosaroot=next(o for o in rosa.objects if o.parent is None)
stool=next(c for c in dst.collections if 'stool_wood' in c.name);stoolroot=next(o for o in stool.objects if o.parent is None)
cam=sc.camera;cam.data.ortho_scale=4;cam.data.shift_x=0;cam.data.shift_y=0;sc.render.resolution_x=1024;sc.render.resolution_y=768
# Same native256px/world-cell, square pixels and35° orientation. Larger context canvas only.
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*1024,(1-p.y)*768]
bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_x=1;bpy.context.view_layer.update();dx=px((0,0,0))[0]-base[0];cam.data.shift_x=(384-base[0])/dx;cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(540-base[1])/dy
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
# Supplemental declared separate dish-salmon placement: original packed2D source plane.
native.apply_clip(asset,rig,'hold',1,'S',sc)
plane=bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane']
held=bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
mat=plane.evaluated_get(dg).matrix_world.copy();heldpos=held.evaluated_get(dg).matrix_world.translation.copy()
recipe=json.loads((P/'recipe-round05.json').read_text());heightUnit=abs(recipe['camera']['unitHeight'][1]);declaredOffsetNative=57.3440234375*2
beltDish=bpy.data.objects.new('Review only source2D dish on neighboring belt',plane.data.copy());sc.collection.objects.link(beltDish);beltDish.matrix_world=mat;beltDish.matrix_world.translation+=Vector((1,0,declaredOffsetNative/heightUnit))-heldpos;beltDish['representation']='Separate canonical approved packed2D reference; no modeled food or release event'
rows=[]

for clip,frame in [('work',4),('hold',6),('load',1),('load',6),('load',12)]:
 for c in [rosa,stool]:c.hide_render=True;c.hide_viewport=True
 belt.hide_render=False;belt.hide_viewport=False;root.location=(0,0,0);beltroot.location=(1,0,0);beltroot.rotation_euler.z=math.pi/2
 native.apply_clip(asset,rig,clip,frame,'E',sc);path=CTX/('native-belt-E-'+clip+'-'+str(frame)+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 rows.append({'path':str(path.relative_to(BASE)),'context':'Chef faces neighboring serving belt','catalogRelativeGrid':{'chef':[0,0],'belt':[0,1]},'nativeRootPositions':{'chef':list(root.location),'belt':list(beltroot.location)},'clip':clip,'frame':frame,'chefFacing':'E','layoutRotationDegrees':90,'cameraWorld':[list(r) for r in cam.matrix_world]})
report={'kind':'Native side view of the declared chef/belt layout, rotated90degrees as a unit with fixed camera and world scale. Original S context remains supplied. This view exposes original hand/knife clearance otherwise occluded by source belt front rail. No gameplay event changed.','neighborsSourceSHA256':hashlib.sha256((P/'original-library.blend').read_bytes()).hexdigest(),'heldDish':'Source original packed2D, not modeled food.','separateBeltDish':'Stationary canonical2D catalog placement, not a release.','renders':rows,'noProjectSaved':True};(OUT/'native-side-context-validation.json').write_text(json.dumps(report,indent=2));print('SIDE_CONTEXT_DONE',flush=True)
