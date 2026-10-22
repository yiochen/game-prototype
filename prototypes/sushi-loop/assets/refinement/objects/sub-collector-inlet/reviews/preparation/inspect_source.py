import bpy,json,pathlib,hashlib
from mathutils import Vector
E=pathlib.Path(__file__).resolve().parents[2]; O=E/'reviews/preparation'; R=O/'resources'
rig=json.loads((E/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']]; col=root.users_collection[0]
def curves(a):
 seen=set()
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for c in bag.fcurves:
     if c.as_pointer() not in seen:seen.add(c.as_pointer());yield c
objects=[]
for o in col.all_objects:
 verts=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
 objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'matrixWorld':[list(x) for x in o.matrix_world], 'bounds':{'min':[min(p[i] for p in verts) for i in range(3)],'max':[max(p[i] for p in verts) for i in range(3)]} if verts else None,'vertices':len(verts),'faces':len(o.data.polygons) if verts else 0,'materials':[m.name for m in o.data.materials if m] if verts else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
acts={}
for clip in rig['clips'].values():
 for ar in clip['actions']:
  a=bpy.data.actions[ar['action']];acts[a.name]=[{'path':c.data_path,'index':c.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in c.keyframe_points]} for c in curves(a)]
materials={m.name:{'diffuse':list(m.diffuse_color),'useNodes':m.use_nodes,'nodes':[{'type':n.type,'name':n.name,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and (isinstance(i.default_value,(int,float,str)) or hasattr(i.default_value,'__len__'))}} for n in m.node_tree.nodes] if m.use_nodes else []} for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m}
report={'source':bpy.data.filepath,'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collection':col.name,'root':root.name,'objects':objects,'actions':acts,'materials':materials,'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'sceneNames':[s.name for s in bpy.data.scenes]}
(O/'source-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
# Preserve actual native collection/action resources, without foreign catalog geometry.
bpy.data.libraries.write(str(R/'original-collector.blend'),{col,*[bpy.data.actions[k] for k in acts]},fake_user=True,compress=True)
print(json.dumps({'collection':col.name,'objects':len(objects),'actions':len(acts),'bounds':[o for o in objects if o['bounds']]},indent=2))
