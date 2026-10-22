import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;R=OUT/'resources/approved-middle';dest=OUT/'canonical-baseline';dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'project.blend'));sc=bpy.context.scene
col=bpy.data.collections['rock-wall-middle__asset'];root=bpy.data.objects['rock-wall-middle__root'];root.rotation_euler.z=0;bpy.context.view_layer.update()
allpts=[o.matrix_world@v.co for o in col.all_objects if o.type=='MESH' for v in o.data.vertices]
def px(v):
 p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
meshes=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 verts=list(o.data.vertices);attrs=o.data.color_attributes
 ring=[]
 for x in [-.5,.5]:
  ids=[v.index for v in verts if abs(v.co.x-x)<1e-6]
  if not ids: continue
  ring.append({'x':x,'count':len(ids),'boundsYZ':[[min(verts[i].co[j] for i in ids) for j in [1,2]],[max(verts[i].co[j] for i in ids) for j in [1,2]]],'boundaryVertexNormals':[list(verts[i].normal) for i in ids[:3]],'colors':[(list(attrs['stone_albedo'].data[i].color)) for i in ids[:3]] if attrs else []})
 meshes.append({'name':o.name,'vertices':len(verts),'polygons':len(o.data.polygons),'smoothPolygons':sum(p.use_smooth for p in o.data.polygons),'hasCustomNormals':o.data.has_custom_normals,'materials':[m.name for m in o.data.materials],'rings':ring})
cam=sc.camera
report={'source':'resources/approved-middle/project.blend','blender':bpy.app.version_string,'scene':sc.name,'rootMatrix':[list(r) for r in root.matrix_world],'bounds':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]],'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'calibration':{k:px(v) if k=='root' else [px(v)[i]-px((0,0,0))[i] for i in [0,1]] for k,v in [('root',(0,0,0)),('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'pixelFilter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'seed':sc.cycles.seed,'compositing':sc.render.use_compositing,'viewTransform':sc.view_settings.view_transform},'meshes':meshes,'images':[{'name':i.name,'file':i.filepath,'source':i.source} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries],'materials':[{'name':m.name,'nodes':[(n.name,n.type) for n in m.node_tree.nodes],'principled':[{i.name:(list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value') and i.name in ['Roughness','Specular IOR Level','Emission Strength']} for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']} for m in {m for o in col.objects if o.type=='MESH' for m in o.data.materials}],'lights':[{'name':o.name,'type':o.data.type,'power':o.data.energy,'shadow':o.data.use_shadow,'rotation':list(o.rotation_euler)} for o in sc.objects if o.type=='LIGHT']}
(dest/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
# Exact canonical scene replay, no changes except required root rotations/path/thread count.
sc.render.threads_mode='FIXED';sc.render.threads=4
for direction,degrees in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();sc.render.filepath=str(dest/f'native-static-{direction}.png');bpy.ops.render.render(write_still=True)
print('CANONICAL_DONE')
