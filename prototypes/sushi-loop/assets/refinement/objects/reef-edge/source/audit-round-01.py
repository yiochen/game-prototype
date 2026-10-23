import sys
sys.dont_write_bytecode=True
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent;O=B.parent;OUT=O/'candidates/round-01/evidence'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def mat(m):
 nt=m.node_tree;nodes=[]
 for n in nt.nodes:
  q={'type':n.bl_idname,'name':n.name,'inputs':{}}
  for s in n.inputs:
   if hasattr(s,'default_value') and s.type in ['VALUE','VECTOR','RGBA','BOOLEAN','INT']:q['inputs'][s.identifier]=list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value
  if n.type=='VALTORGB':q['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  nodes.append(q)
 return {'nodes':nodes,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in nt.links],'objectAnimation':bool(m.animation_data),'nodeAnimation':bool(nt.animation_data)}
def inspect(p,aid):
 bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();r=bpy.data.objects[aid+'__root'];c=bpy.data.collections[aid];dg=bpy.context.evaluated_depsgraph_get();rows=[];pts=[];bands={};grounds=[]
 for ob in c.all_objects:
  if ob.type!='MESH':continue
  e=ob.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles();m=r.matrix_world.inverted()@e.matrix_world;nm=m.to_3x3().inverted().transposed();vs=[m@v.co for v in me.vertices];pts+=vs
  q={'name':ob.name,'vertices':len(vs),'triangles':len(me.loop_triangles),'rootLocalBounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)],'meshUsers':ob.data.users,'modifiers':[m.type for m in ob.modifiers],'objectAnimation':bool(ob.animation_data),'meshAnimation':bool(ob.data.animation_data),'shapeKeys':bool(ob.data.shape_keys),'materials':[m.name for m in me.materials]}
  if 'continuous_core' in ob.name:
   edges={}
   for poly in me.polygons:
    for a,b in poly.edge_keys:edges[tuple(sorted((a,b)))]=edges.get(tuple(sorted((a,b))),0)+1
   q['nonmanifoldEdgeCount']=sum(v!=2 for v in edges.values());q['groundTriangles']=[]
   for t in me.loop_triangles:
    if all(abs(vs[i].z)<1e-7 for i in t.vertices):q['groundTriangles'].append([list(vs[i]) for i in t.vertices]);grounds.append(t.area)
   for side in ['W','E']:
    sign=-1 if side=='W' else 1;tris=[]
    for t in me.loop_triangles:
     a=[vs[i] for i in t.vertices]
     if all(v.x*sign>=.42-1e-6 for v in a) and not all(abs(v.x-sign*.5)<1e-6 for v in a):
      tris.append({'vertices':[list(v) for v in a],'normal':list(nm@t.normal),'cornerNormals':[list(nm@me.corner_normals[i].vector) for i in t.loops],'materialName':me.materials[t.material_index].name,'materialField':mat(me.materials[t.material_index])})
    bands[side]=tris
   q['orderedRings']={side:[list(v) for v in vs if abs(v.x-x)<1e-6] for side,x in [('W',-.5),('E',.5)]}
  rows.append(q);e.to_mesh_clear()
 return {'asset':aid,'scene':s.name,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'objects':rows,'bounds':[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)],'groundArea':sum(grounds),'endpointBands':bands,'materials':{m.name:mat(m) for m in bpy.data.materials if m.users},'lighting':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'world':{'nodes':[(n.type,{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value')}) for n in s.world.node_tree.nodes]},'render':{'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'transparent':s.render.film_transparent,'fps':s.render.fps,'frame':s.frame_current,'compositor':s.use_nodes},'images':[i.name for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'actions':[a.name for a in bpy.data.actions]}
canon=inspect(B/'resources/canonical-middle02.blend','reef-middle');cur=inspect(B/'round-01.blend','reef-edge')
write(OUT/'canonical-native-audit.json',canon);write(OUT/'candidate-native-audit.json',cur)
checks={'entireWBandsExact':canon['endpointBands']['W']==cur['endpointBands']['W'],'entireEBandsExact':canon['endpointBands']['E']==cur['endpointBands']['E'],'sharedLightsExact':canon['lighting']==cur['lighting'],'sharedWorldExact':canon['world']==cur['world'],'sharedRenderExact':canon['render']==cur['render'],'finiteGroundArea':abs(cur['groundArea']-.76)<1e-5,'envelope':all(cur['bounds'][k][0]>=v-1e-5 and cur['bounds'][k][1]<=w+1e-5 for k,v,w in [(0,-.5,.5),(1,-.38,.38),(2,0,.68)]),'noLinkedLibraries':not cur['linkedLibraries'],'noImageArtwork':not cur['images'],'noActions':not cur['actions'],'privateMeshes':all(q['meshUsers']==1 for q in cur['objects']),'closedCore':next(q for q in cur['objects'] if 'continuous_core' in q['name'])['nonmanifoldEdgeCount']==0}
write(OUT/'native-contract-comparison.json',{'checks':checks,'allChecksPassed':all(checks.values()),'coverage':'Every evaluated triangle and corner-normal vector spanning full actual .08 endpoint bands, native active material fields, common rig/world/color; no normal override branch. Root native rotations preserve equality. Geometry and shader normals are identical for these flat bands.','fieldSources':['canonical-native-audit.json','candidate-native-audit.json'],'scope':'Native technical measurements only, not visual approval.'})
print(json.dumps(checks))
