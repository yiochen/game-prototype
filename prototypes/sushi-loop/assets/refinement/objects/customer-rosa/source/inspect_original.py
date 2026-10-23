import bpy,json,pathlib,hashlib
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc
root=bpy.data.objects['customer_rosa__ground_root.001']
c=next(c for c in sc.collection.children if root in list(c.all_objects))
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=c
c.hide_render=False;c.hide_viewport=False
sc.view_layers[0].update()
d={'blend':bpy.data.filepath,'scene':sc.name,'collection':c.name,'root':root.name,'objects':[],'images':[]}
for o in c.all_objects:
 v={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'loc':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'world':[[*r] for r in o.matrix_world],'hide':o.hide_render,'properties':{k:str(o[k]) for k in o.keys()}}
 if o.type=='MESH':
  v.update(verts=len(o.data.vertices),faces=len(o.data.polygons),materials=[m.name for m in o.data.materials],modifiers=[{'type':m.type,'name':m.name} for m in o.modifiers],groups=[g.name for g in o.vertex_groups],bounds=[list(o.matrix_world@Vector(v)) for v in o.bound_box])
 d['objects'].append(v)
for i in bpy.data.images:
 if i.packed_file:d['images'].append({'name':i.name,'size':list(i.size),'path':i.filepath,'sha':hashlib.sha256(i.packed_file.data).hexdigest()})
(P/'native-original-inspection.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'scene':sc.name,'collection':c.name,'objects':[{k:v for k,v in o.items() if k in ['name','type','parentBone','verts','materials','loc','scale']} for o in d['objects']],'packedImages':d['images']},indent=2))
