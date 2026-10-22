import bpy, json, hashlib, pathlib
from mathutils import Vector
OUT=pathlib.Path(__file__).parent
def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return {str(k):plain(v[k]) for k in v.keys()}
    except:return [plain(x) for x in v]
def props(o):return {k:plain(o[k]) for k in o.keys() if k!='_RNA_UI'}
def box(points):
    return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]} if points else None
def obj(o):
    d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(x) for x in o.matrix_world],'props':props(o),'hideRender':o.hide_render,'collections':[c.name for c in o.users_collection]}
    if o.type=='MESH':
        points=[o.matrix_world@v.co for v in o.data.vertices];d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=box(points),materials=[m.name if m else None for m in o.data.materials],modifiers=[{'type':m.type,'name':m.name} for m in o.modifiers])
    if o.type=='CAMERA':d['camera']={'type':o.data.type,'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'sensorFit':o.data.sensor_fit,'clip':[o.data.clip_start,o.data.clip_end]}
    if o.type=='LIGHT':d['light']={'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size if hasattr(o.data,'size') else None}
    return d
roots=[o for o in bpy.data.objects if o.name.startswith('workshop-hut__root')]
cols=list({c.name:c for root in roots for c in root.users_collection}.values())
names={o.name for c in cols for o in c.all_objects}
materials={m.name:m for n in names for m in (bpy.data.objects[n].data.materials if bpy.data.objects[n].type=='MESH' else []) if m}
r={'blenderVersion':bpy.app.version_string,'sourcePath':bpy.data.filepath,'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'rootCollections':[c.name for c in s.collection.children],'props':props(s),'render':{'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps,'transparent':s.render.film_transparent},'world':s.world.name if s.world else None} for s in bpy.data.scenes], 'roots':[obj(o) for o in roots], 'collections':[{'name':c.name,'props':props(c),'objects':[o.name for o in c.all_objects]} for c in cols],'objects':[obj(bpy.data.objects[n]) for n in sorted(names)],'cameras':[obj(o) for o in bpy.data.objects if o.type=='CAMERA'],'lights':[obj(o) for o in bpy.data.objects if o.type=='LIGHT'],'materials':[],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images],'libraries':[{'filepath':l.filepath} for l in bpy.data.libraries]}
for name,m in materials.items():
    nodes=[]
    if m.use_nodes:
        for n in m.node_tree.nodes:
            nodes.append({'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'image':n.image.name if hasattr(n,'image') and n.image else None})
    r['materials'].append({'name':name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'nodes':nodes,'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
(OUT/'native-source-inventory-v2.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'roots':[o.name for o in roots],'collections':[c.name for c in cols],'scenes':[(s.name,s.camera.name if s.camera else None) for s in bpy.data.scenes],'out':str(OUT/'native-source-inventory.json')}))
