import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
record=json.loads((P.parent/'inputs/source-rig.json').read_text());root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);collection=next(c for c in sc.collection.children if root.name in c.all_objects)
def val(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return [val(x) for x in v]
 except:return str(v)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
mats={m for o in collection.all_objects if o.type=='MESH' for m in o.data.materials if m};materials=[]
for m in mats:
 materials.append({'name':m.name,'diffuse':val(m.diffuse_color),'roughness':m.roughness,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else []})
arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
out={'sourceProject':bpy.data.filepath,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'world':{'name':sc.world.name,'nodes':[{'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in sc.world.node_tree.nodes]} if sc.world else None,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':val(o.data.color),'matrix':val(o.matrix_world),'size':getattr(o.data,'size',None),'use_shadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT'],'materials':materials,'boneConstraints':{b.name:[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in b.constraints] for b in arm.pose.bones},'nativeMeshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'geometrySHA256':digest({'vertices':[val(v.co) for v in o.data.vertices],'polygons':[val(f.vertices) for f in o.data.polygons]}),'vertexGroups':[v.name for v in o.vertex_groups]} for o in collection.all_objects if o.type=='MESH']}
(P/'source-inventory.json').write_text(json.dumps(out,indent=2)+'\n');print('INVENTORY_DONE')
