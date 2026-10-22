import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).parent / 'original-collection-measurement-v1.json'
matches=[c for c in bpy.data.collections if 'decor-midground-coral' in c.name.lower()]
if not matches:
    print('COLLECTION_CANDIDATES', json.dumps([c.name for c in bpy.data.collections if 'coral' in c.name.lower()]))
    raise RuntimeError('Exact asset collection not found')
c=next((c for c in matches if c.name=='decor-midground-coral'),matches[0])
scene=bpy.context.scene
scene.frame_set(1)
deps=bpy.context.evaluated_depsgraph_get()

def bbox(points):
    if not points: return None
    return {'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]}

def material(m):
    d={'name':m.name,'diffuse_color':list(m.diffuse_color),'use_nodes':m.use_nodes}
    if m.use_nodes:
        d['nodes']=[{'name':n.name,'type':n.type} for n in m.node_tree.nodes]
        d['principled']=[{s.name:list(s.default_value) if hasattr(s.default_value,'__iter__') else s.default_value for s in n.inputs if s.name in ('Base Color','Metallic','Roughness','Alpha','Emission Color','Emission Strength')} for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']
    return d
objs=[]; all_world=[]
for o in sorted(c.all_objects,key=lambda x:x.name):
    ev=o.evaluated_get(deps)
    d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation_euler':list(o.rotation_euler),'scale':list(o.scale),'matrix_world':[list(r) for r in o.matrix_world], 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'animation_data':bool(o.animation_data),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
    if o.type=='MESH':
        local=[v.co.copy() for v in o.data.vertices]
        world=[o.matrix_world@v for v in local]
        all_world+=world
        d.update(vertices=len(o.data.vertices),edges=len(o.data.edges),polygons=len(o.data.polygons),smooth_faces=sum(p.use_smooth for p in o.data.polygons),local_bounds=bbox(local),world_bounds=bbox(world),materials=[material(m) for m in o.data.materials if m],uv_layers=list(o.data.uv_layers.keys()))
    objs.append(d)
data={'purpose':'Read-only original collection inspection before criteria or construction brief','blender_version':bpy.app.version_string,'blend_file':bpy.data.filepath,'blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'collection':c.name,'collection_custom_properties':{k:str(c[k]) for k in c.keys()},'frame':scene.frame_current,'frame_range':[scene.frame_start,scene.frame_end],'scene_camera':scene.camera.name if scene.camera else None,'objects':objs,'raw_mesh_world_bounds':bbox(all_world),'counts':{'objects':len(objs),'meshes':sum(o.type=='MESH' for o in c.all_objects)},'external_images':[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE']}
OUT.write_text(json.dumps(data,indent=2)+'\n')
print('INSPECTION_WRITTEN',OUT)
print('COLLECTION',c.name,'OBJECTS',len(objs),'BOUNDS',data['raw_mesh_world_bounds'])
