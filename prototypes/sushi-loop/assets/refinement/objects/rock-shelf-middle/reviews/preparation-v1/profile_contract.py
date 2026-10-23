import bpy,pathlib,json,hashlib
from mathutils import Vector
BASE=pathlib.Path(__file__).parent;res={}
s=bpy.context.scene
for c in s.collection.children:
 c.hide_viewport=False
for l in s.view_layers[0].layer_collection.children:
 l.exclude=False;l.hide_viewport=False
for o in s.objects:
 o.hide_viewport=False;o.hide_set(False)
s.frame_set(1);s.view_layers[0].update();dep=bpy.context.evaluated_depsgraph_get()
for aid in ['rock-shelf-middle','rock-shelf-edge','rock-shelf-corner','rock-shelf-end']:
 root=bpy.data.objects[aid+'__root.001'];coll=bpy.data.collections['S33_PROP_'+aid+'.001'];meshes=[o for o in coll.all_objects if o.type=='MESH'];ports=json.loads(root['ports']);parts=[]
 for o in meshes:
  ev=o.evaluated_get(dep);m=ev.to_mesh();vs=[ev.matrix_world@v.co for v in m.vertices]
  parts.append({'name':o.name,'bounds':[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]],'vertexCount':len(vs),'polygonCount':len(m.polygons),'geometryUsers':o.data.users,'shapeKeys':bool(o.data.shape_keys),'modifiers':[m.type for m in o.modifiers],'objectAction':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
  ev.to_mesh_clear()
 pr=[]
 for p in ports:
  p0=Vector(p['position']);n=Vector(p['normal']);faces=[];near=[]
  for o in meshes:
   ev=o.evaluated_get(dep);m=ev.to_mesh();vs=[ev.matrix_world@v.co for v in m.vertices]
   for f in m.polygons:
    distances=[abs((vs[i]-p0).dot(n)) for i in f.vertices]
    if max(distances)<1e-6:
     faces.append({'object':o.name,'polygon':f.index,'worldVertices':[list(vs[i]) for i in f.vertices],'normal':list(ev.matrix_world.to_3x3()@f.normal),'material':o.data.materials[f.material_index].name})
    elif min(distances)<1e-6:
     near.append({'object':o.name,'polygon':f.index,'portEdgeVertices':[list(vs[i]) for i in f.vertices if abs((vs[i]-p0).dot(n))<1e-6],'normal':list(ev.matrix_world.to_3x3()@f.normal),'material':o.data.materials[f.material_index].name,'smooth':f.use_smooth})
   ev.to_mesh_clear()
  pr.append({**p,'capFaces':faces,'adjacentFaces':near})
 mats=[]
 for mat in {s.material for o in meshes for s in o.material_slots if s.material}:
  nt=mat.node_tree;output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');active=output.inputs['Surface'].links[0].from_node
  ramps=[{'name':n.name,'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]} for n in nt.nodes if n.type=='VALTORGB']
  maps=[{'name':n.name,'dataType':n.data_type,'inputs':[{'name':i.name,'value':list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value} for i in n.inputs if hasattr(i,'default_value')]} for n in nt.nodes if n.type=='MAP_RANGE']
  mats.append({'name':mat.name,'users':mat.users,'activeSurface':active.name,'activeType':active.type,'roughness':active.inputs['Roughness'].default_value,'specularIOR':active.inputs['Specular IOR Level'].default_value,'ramps':ramps,'mapRange':maps,'imageNodes':[n.image.name if n.image else None for n in nt.nodes if n.type=='TEX_IMAGE'],'materialAnimation':bool(mat.animation_data),'nodeAnimation':bool(nt.animation_data),'normalLinked':active.inputs['Normal'].is_linked,'meshUsers':[o.name for o in bpy.data.objects if o.type=='MESH' and mat in list(o.data.materials)]})
 res[aid]={'collection':coll.name,'root':root.name,'rootMatrix':[list(x) for x in root.matrix_world],'declaredHeight':root.get('visual_height'),'parts':parts,'ports':pr,'materials':mats}
(BASE/'evidence/native-family-profile-evidence.json').write_text(json.dumps(res,indent=2));print('PROFILE EVIDENCE SAVED')
