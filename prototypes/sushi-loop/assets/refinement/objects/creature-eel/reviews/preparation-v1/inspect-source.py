import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib,math,importlib.util
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
OUT=P/'source-inspection.json'
def dump(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if hasattr(v,'to_list'):return dump(v.to_list())
 if isinstance(v,dict):return {k:dump(x) for k,x in v.items()}
 try:return [dump(x) for x in v]
 except:return str(v)
def props(x):return {k:dump(v) for k,v in x.items()}
result={'blenderVersion':bpy.app.version_string,'source':bpy.data.filepath,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scenes':[]}
for sc in bpy.data.scenes:
 result['scenes'].append({'name':sc.name,'camera':sc.camera.name if sc.camera else None,'collections':[c.name for c in sc.collection.children],'props':props(sc)})
roots=[o for o in bpy.data.objects if o.name.startswith('creature-eel') and 'ground_root' in o.name]
result['rootCandidates']=[{'name':o.name,'props':props(o),'collections':[c.name for c in o.users_collection]} for o in roots]
root=bpy.data.objects['creature-eel__ground_root.003'];col=root.users_collection[0]
# Enable actual owned collection ancestry and every owned object before dependency evaluation.
sc=next(s for s in bpy.data.scenes if col in list(s.collection.children_recursive));bpy.context.window.scene=sc
result['actualScene']=sc.name;result['collection']=col.name;result['preVisibility']={'collection':[col.hide_render,col.hide_viewport],'objects':{o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in col.all_objects}}
def enable_layer(lc):
 if lc.collection==col or col in list(lc.collection.children_recursive):
  lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_render=False;lc.collection.hide_viewport=False
 for c in lc.children:enable_layer(c)
enable_layer(bpy.context.view_layer.layer_collection)
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
objs=list(col.all_objects)
result['objects']=[]
for o in objs:
 rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentBone':o.parent_bone,'matrixWorld':dump(o.matrix_world),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'props':props(o),'constraints':[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],'modifiers':[]}
 for m in o.modifiers:
  rec['modifiers'].append({'name':m.name,'type':m.type,'showViewport':m.show_viewport,'showRender':m.show_render,'object':getattr(getattr(m,'object',None),'name',None),'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)})
 if o.type=='MESH':
  d=o.data;rec.update(vertices=len(d.vertices),edges=len(d.edges),polygons=len(d.polygons),smoothPolygons=sum(x.use_smooth for x in d.polygons),customNormals=d.has_custom_normals,shapeKeys=[k.name for k in d.shape_keys.key_blocks] if d.shape_keys else [],materials=[s.material.name if s.material else None for s in o.material_slots],vertexGroups=[g.name for g in o.vertex_groups],groupCounts={g.name:sum(any(w.group==g.index and w.weight>0 for w in v.groups) for v in d.vertices) for g in o.vertex_groups})
 if o.type=='ARMATURE':rec['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform} for b in o.data.bones]
 result['objects'].append(rec)
result['materials']=[]
for m in {s.material for o in objs if o.type=='MESH' for s in o.material_slots if s.material}:
 result['materials'].append({'name':m.name,'props':props(m),'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:dump(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked},'image':getattr(getattr(n,'image',None),'filepath',None)} for n in m.node_tree.nodes] if m.node_tree else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.node_tree else []})
result['usedImages']=[{'name':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file)} for m in {s.material for o in objs if o.type=='MESH' for s in o.material_slots if s.material} if m.node_tree for n in m.node_tree.nodes if getattr(n,'image',None)]
result['usedLibraries']=[{'name':o.library.filepath} for o in objs if o.library]
OUT.write_text(json.dumps(result,indent=2)+'\n');print('INSPECT_WRITTEN',OUT)
