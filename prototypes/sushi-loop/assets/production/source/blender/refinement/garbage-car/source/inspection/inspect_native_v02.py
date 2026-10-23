import bpy,json,math,sys,pathlib
from mathutils import Matrix,Vector
P=pathlib.Path(__file__).resolve().parents[2]; W=P.parents[5]
sys.path.insert(0,str(W/'prototypes/sushi-loop/assets/production/source/blender'))
import native_actions as N
rig=json.loads((P/'inputs/source-rig.json').read_text()); cr=json.loads((P/'inputs/source-camera.json').read_text())
root=bpy.data.objects['garbage-car__root']; coll=root.users_collection[0]
sc=bpy.context.scene
sc.camera=next(o for o in bpy.data.objects if o.type=='CAMERA')
cam=sc.camera; cam.matrix_world=Matrix(cr['camera']['worldMatrix']); cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=4.5;cam.data.shift_x=0;cam.data.shift_y=-.30769163370132446/2
sc.render.resolution_x=1152;sc.render.resolution_y=1664;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=cr['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
from bpy_extras.object_utils import world_to_camera_view
cam.data.shift_y=0;bpy.context.view_layer.update();base=world_to_camera_view(sc,cam,Vector((0,0,0)))
cam.data.shift_y=1;bpy.context.view_layer.update();p1=world_to_camera_view(sc,cam,Vector((0,0,0)))
cam.data.shift_y=(1088/sc.render.resolution_y-(1-base.y))/((1-p1.y)-(1-base.y));bpy.context.view_layer.update()
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=16
for o in sc.objects:o.hide_render=o.type not in ('LIGHT','CAMERA') and o.name not in coll.all_objects
for c in sc.collection.children:c.hide_render=c!=coll and not any(o.type in ('LIGHT','CAMERA') for o in c.all_objects)
coll.hide_render=False
asset={'root':root,'collection':coll};out=P/'source/inspection'
audit={'scene':sc.name,'cameraBeforeRestore':cr,'rootProps':dict(root.items()),'collection':coll.name,'objects':[],'frames':[]}
for o in coll.all_objects:
 audit['objects'].append({'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'parent':o.parent.name if o.parent else None,'modifiers':[m.type for m in o.modifiers]})
for clip,frames in [('idle',[1]),('highlighted',[1,4,7,10,13]),('clearance',[1,4,8,12])]:
 for fr in frames:
  N.apply_clip(asset,rig,clip,fr,'S',sc)
  verts=[o.matrix_world@Vector(v) for o in coll.all_objects if o.type=='MESH' for v in o.bound_box]
  audit['frames'].append({'clip':clip,'frame':fr,'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)],'rootMatrix':[list(row) for row in root.matrix_world],'parts':{o.name:{'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)} for o in coll.all_objects if o.type=='MESH'}})
  if (clip,fr) in [('idle',1),('clearance',8),('clearance',12)]:
   sc.render.filepath=str(out/f'native-{clip}-{fr:02d}-S.png');bpy.ops.render.render(write_still=True)
(out/'native-inspection.json').write_text(json.dumps(audit,indent=2,default=list))
