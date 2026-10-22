import bpy,sys,pathlib,json,math,importlib.util
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=pathlib.Path(__file__).parent;RES=BASE/'resources';OUT=BASE/'evidence';OUT.mkdir(exist_ok=True)
s=bpy.context.scene
spec=importlib.util.spec_from_file_location('shelf_frozen_runtime',RES/'capture/capture_runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime);runtime.scene=lambda:s
root=bpy.data.objects['rock-shelf-middle__root.001'];coll=bpy.data.collections['S33_PROP_rock-shelf-middle.001'];parts=list(coll.all_objects)
for child in s.collection.children:
 child.hide_render=child!=coll;child.hide_viewport=child!=coll
for layer in s.view_layers[0].layer_collection.children:
 layer.exclude=layer.collection!=coll;layer.hide_viewport=False
coll.hide_render=False;coll.hide_viewport=False
for o in parts:
 o.hide_viewport=False;o.hide_set(False)
s.frame_set(1);root.location=(0,0,0);root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
# update actual source evaluation before all world transforms
records=[];dep=bpy.context.evaluated_depsgraph_get()
for o in parts:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dep);me=ev.to_mesh();verts=[list(ev.matrix_world@v.co) for v in me.vertices]
 records.append({'name':o.name,'vertices':verts,'polygons':[{'vertices':list(p.vertices),'normalWorld':list(ev.matrix_world.to_3x3()@p.normal),'material':o.data.materials[p.material_index].name,'smooth':p.use_smooth} for p in me.polygons], 'bounds':[[min(v[k] for v in verts) for k in range(3)],[max(v[k] for v in verts) for k in range(3)]],'action':str(o.animation_data.action.name) if o.animation_data and o.animation_data.action else None,'shapeKeys':bool(o.data.shape_keys),'uvLayers':[u.name for u in me.uv_layers]});ev.to_mesh_clear()
(OUT/'evaluated-geometry.json').write_text(json.dumps(records,indent=2))
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
for d,angle in angles.items():
 root.rotation_euler.z=angle;bpy.context.view_layer.update()
 camrec=runtime.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
 s.render.filepath=str(OUT/('source-'+d+'-4x.png'));s.render.image_settings.compression=15;bpy.ops.render.render(write_still=True)
 (OUT/('camera-'+d+'.json')).write_text(json.dumps(camrec,indent=2))
# In-memory duplicate assembly only; no blend save, geometry edits or new candidate.
root.rotation_euler.z=0;bpy.context.view_layer.update()
assembly=bpy.data.collections.new('judge_source_three_middle_assembly');s.collection.children.link(assembly)
assemblyroot=bpy.data.objects.new('judge_source_assembly_root',None);assembly.objects.link(assemblyroot)
for x in (-1,0,1):
 for original in parts:
  if original.type!='MESH':continue
  o=original.copy();o.data=original.data;o.parent=assemblyroot;assembly.objects.link(o);o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=original.matrix_world.copy();o.location.x+=x
coll.hide_render=True
# New layer collection needs explicit active update; all master lights remain active.
for layer in s.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=assembly
s.view_layers[0].update()
for d,angle in angles.items():
 assemblyroot.rotation_euler.z=angle;bpy.context.view_layer.update()
 camrec=runtime.configure_camera('square-top-front-oblique',(448,608),(224,376),4)
 s.render.filepath=str(OUT/('joined-'+d+'-4x.png'));s.render.image_settings.compression=15;bpy.ops.render.render(write_still=True)
(OUT/'capture-settings.json').write_text(json.dumps({'purpose':'Original-source proof only, no candidate; geometry/materials unchanged','blender':bpy.app.version_string,'singleLogicalFrame':[192,352],'singleRoot':[96,248],'singleSourceScale':4,'runtimeSourceScale':2,'sampling':'Uniform full-canvas LANCZOS from source4x to runtime2x (actual shelf historical guide)','joinedLogicalFrame':[448,608],'joinedRoot':[224,376],'assemblyNativeRootOffsets':[[-1,0,0],[0,0,0],[1,0,0]],'angles':angles,'filterSize':s.render.filter_size,'shadowGround':False,'filmTransparent':s.render.film_transparent,'eeveeSettings':{p.identifier:str(getattr(s.eevee,p.identifier)) for p in s.eevee.bl_rna.properties if 'sample' in p.identifier} if hasattr(s,'eevee') else {},'scene':s.name,'cameraBasis':'X right, depth -Y down, +Z up .7cell','noSavedBlend':True},indent=2))
print('SOURCE CAPTURE COMPLETE')
