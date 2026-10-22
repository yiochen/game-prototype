import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[2];sc=bpy.context.scene;col=next(c for c in bpy.data.collections if 'wreck-end' in c.name)
def en(lc):
 lc.exclude=False;lc.hide_viewport=False
 for c in lc.children:en(c)
en(bpy.context.view_layer.layer_collection)
col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False);o.hide_render=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
root=next(o for o in col.all_objects if o.type=='EMPTY');inv=root.matrix_world.inverted();val=lambda v:[float(x) for x in v]
def anim(x):return bool(getattr(x,'animation_data',None))
r={'root':root.name,'rootMatrix':[val(row) for row in root.matrix_world],'rootProperties':dict(root.items()),'staticOwnership':[],'Wprofiles':[],'materials':{},'shaderResources':[]}
for ob in col.all_objects:
 rr={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'localObject':ob.library is None,'localData':getattr(ob.data,'library',None) is None,'objectAnimation':anim(ob),'dataAnimation':anim(ob.data),'shapeKeys':bool(getattr(ob.data,'shape_keys',None)),'constraints':[c.type for c in ob.constraints],'modifiers':[m.type for m in ob.modifiers]};r['staticOwnership'].append(rr)
 if ob.type!='MESH':continue
 eo=ob.evaluated_get(dg);me=eo.to_mesh();ps=[inv@eo.matrix_world@v.co for v in me.vertices]
 caps=[];sides=[]
 for p in me.polygons:
  vs=[ps[i] for i in p.vertices];entry={'vertices':[val(v) for v in vs],'polygonNormal':val(p.normal),'cornerNormals':[val(me.corner_normals[i].vector) for i in p.loop_indices],'material':me.materials[p.material_index].name}
  if all(abs(v.x+.5)<1e-6 for v in vs):caps.append(entry)
  elif min(v.x for v in vs)<-.42+1e-6 and max(v.x for v in vs)>-.5+1e-6:sides.append(entry)
 if caps:r['Wprofiles'].append({'object':ob.name,'capFaces':caps,'wholeCollarRange':[-.5,-.42],'spanningSourceSideFaces':sides,'sourceFiniteField':'Source loop normals flat per side; full actual material graphs below. These old fields are observations and intentionally differ from approved canonical middle02.'})
 eo.to_mesh_clear()
 for m in ob.data.materials:
  if m.name in r['materials']:continue
  nt=m.node_tree;rr={'local':m.library is None,'materialAnimation':anim(m),'nodeAnimation':anim(nt),'nodes':[],'links':[]}
  for n in nt.nodes:
   entry={'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'attribute':getattr(n,'attribute_name',None),'inputs':[]}
   for i,s in enumerate(n.inputs):
    if hasattr(s,'default_value') and s.type not in ['SHADER','CUSTOM']:
     v=s.default_value
     if hasattr(v,'__len__') and not isinstance(v,str):v=list(v)
     entry['inputs'].append({'index':i,'name':s.name,'identifier':s.identifier,'value':v,'linked':s.is_linked})
   if hasattr(n,'color_ramp'):entry['colorRamp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
   rr['nodes'].append(entry)
  rr['links']=[{'from':[l.from_node.name,l.from_socket.identifier],'to':[l.to_node.name,l.to_socket.identifier]} for l in nt.links];r['materials'][m.name]=rr
r['genuineConflicts']=['Original source normal/albedo/material fields differ from canonical middle02 over full W collar; source geometry/profile is compatible. Adopt approved derivative fields before evaluation.','Target is opaque blue layered boards while source functional note permits open hull rails; literal full board fill is not required.','Raw authoring outline differs from evaluated bevel-trimmed outline; proposed modeling budget uses own raw outline plus declared .78 height, pending root freeze.']
(P/'source-contract-proof.json').write_text(json.dumps(r,indent=2,default=str)+'\n');print('own profiles',len(r['Wprofiles']),'static owned objects',len(r['staticOwnership']))
