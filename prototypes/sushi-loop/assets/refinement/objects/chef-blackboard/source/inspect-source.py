"""Inspect unchanged native source bytes in an isolated visible collection."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;src=P/'original-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(src));sc=bpy.context.scene
r={'project':'source/original-library.blend','sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scenes':[x.name for x in bpy.data.scenes],'scene':sc.name,'libraryActiveCamera':{'name':sc.camera.name,'matrix':[list(row) for row in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,'shift_y':sc.camera.data.shift_y},'libraryActiveRender':{k:getattr(sc.render,k) for k in ['engine','resolution_x','resolution_y','pixel_aspect_x','pixel_aspect_y','film_transparent']},'note':'The original library active capture is for another object. Actual chef-blackboard registered capture is inputs/source-camera.json, copied to source/resources/registered-camera.json.'}
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(src),link=False) as (a,b):b.collections=['S33_PROP_chef-blackboard']
c=b.collections[0];bpy.context.scene.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();r['objects']=[]
for o in c.objects:
 v=[o.matrix_world@Vector(x) for x in o.bound_box] if o.type=='MESH' else []
 r['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(row) for row in o.matrix_world],'bounds':[list(map(min,zip(*v))),list(map(max,zip(*v)))] if v else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'props':dict(o.items())})
(P/'source-native-inspection.json').write_text(json.dumps(r,indent=2,default=str)+'\n');print('INSPECTED',len(r['objects']))
