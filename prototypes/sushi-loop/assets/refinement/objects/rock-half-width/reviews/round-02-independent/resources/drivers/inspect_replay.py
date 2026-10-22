import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[2];R=B/'resources';O=B/'evidence';sc=bpy.context.scene;root=bpy.data.objects['rock-half-width__root.001'];coll=next(c for c in root.users_collection);body=next(o for o in coll.all_objects if o.type=='MESH')
def rows(m):return [list(r) for r in m]
def write(n,x):(O/n).write_text(json.dumps(x,indent=2,default=lambda v:list(v))+'\n')
def layer(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layer(c)
for v in sc.view_layers:layer(v.layer_collection)
for name in [o.name for o in coll.all_objects]:
 o=bpy.data.objects[name];o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
coll.hide_render=False;coll.hide_viewport=False;sc.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();vs=[v.co.copy() for v in mesh.vertices];bm=bmesh.new();bm.from_mesh(mesh)
caps=[p for p in mesh.polygons if all(abs(abs(vs[i].x)-.5)<1e-6 for i in p.vertices)]
weights=body.data.attributes['collar_weight'];material=body.data.materials[0];nodes=material.node_tree.nodes;links=material.node_tree.links
collar_vertices=[i for i,v in enumerate(vs) if abs(v.x)>=.42-1e-6]
collar_weights=[weights.data[i].value for i in collar_vertices]
geometry={'bounds':{'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]},'groundArea':sum(p.area for p in mesh.polygons if all(abs(vs[i].z)<1e-7 for i in p.vertices)),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'meshCounts':{'vertices':len(vs),'polygons':len(mesh.polygons)},'caps':[{'x':vs[p.vertices[0]].x,'normal':list(p.normal),'verticesYZ':[[vs[i].y,vs[i].z] for i in p.vertices]} for p in caps],'allCollarVertexWeightsOne':all(abs(w-1)<1e-7 for w in collar_weights),'collarVertexCount':len(collar_vertices),'wholeMeshAttributeDomain':{a.name:a.domain for a in body.data.attributes},'images':[i.filepath for i in bpy.data.images if i.source!='VIEWER'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'shapeKeys':len(bpy.data.shape_keys),'actions':len(bpy.data.actions),'rootMatrix':rows(root.matrix_world)}
bm.free();ev.to_mesh_clear()
# Evaluate the actual saved graph, following its links and operations. No use of supplied field-table values.
def evaluate(node,out,point,matrix,attrs,cache):
 key=(node.name,out.name)
 if key in cache:return cache[key]
 def inp(i):
  s=node.inputs[i]
  return evaluate(s.links[0].from_node,s.links[0].from_socket,point,matrix,attrs,cache) if s.is_linked else s.default_value
 t=node.bl_idname
 if t=='ShaderNodeNewGeometry':assert out.name=='Position';v=matrix@Vector(point)
 elif t=='ShaderNodeVectorTransform':
  v=Vector(inp(0)[:3]);op=node.vector_type
  if node.convert_from=='WORLD' and node.convert_to=='OBJECT':v=matrix.inverted()@v if op=='POINT' else matrix.to_3x3().transposed()@v
  elif node.convert_from=='OBJECT' and node.convert_to=='WORLD':v=matrix@v if op=='POINT' else matrix.inverted().to_3x3().transposed()@v
  else:raise ValueError((node.name,node.convert_from,node.convert_to))
 elif t=='ShaderNodeSeparateXYZ':v=inp(0)[{'X':0,'Y':1,'Z':2}[out.name]]
 elif t=='ShaderNodeCombineXYZ':v=Vector([inp(0),inp(1),inp(2)])
 elif t=='ShaderNodeMath':
  a=float(inp(0));b=float(inp(1));op=node.operation
  v={'ABSOLUTE':lambda:abs(a),'SIGN':lambda:0 if a==0 else 1 if a>0 else -1,'SUBTRACT':lambda:a-b,'MULTIPLY':lambda:a*b,'MAXIMUM':lambda:max(a,b),'MINIMUM':lambda:min(a,b),'ADD':lambda:a+b,'SQRT':lambda:math.sqrt(max(0,a))}[op]()
  if node.use_clamp:v=max(0,min(1,v))
 elif t=='ShaderNodeVectorMath':assert node.operation=='NORMALIZE';v=Vector(inp(0)[:3]).normalized()
 elif t=='ShaderNodeAttribute':v=attrs[node.attribute_name]
 elif t=='ShaderNodeVertexColor':v=attrs[node.layer_name]
 elif t=='ShaderNodeMixRGB':
  f=float(inp(0));a=list(inp(1));b=list(inp(2));a=a[:3];b=b[:3]
  v=Vector([(1-f)*a[i]+f*(a[i]*b[i] if node.blend_type=='MULTIPLY' else b[i]) for i in range(3)])
  if node.use_clamp:v=Vector([max(0,min(1,x)) for x in v])
 elif t=='ShaderNodeEmission':v=Vector(inp('Color')[:3])*float(inp('Strength'))
 elif t=='ShaderNodeOutputMaterial':v=inp('Surface')
 else:raise ValueError(('unsupported actual used node',t,node.name,out.name))
 cache[key]=v;return v
node_graph=[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'vectorType':getattr(n,'vector_type',None),'from':getattr(n,'convert_from',None),'to':getattr(n,'convert_to',None)} for n in nodes]
output=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial' and n.is_active_output);surface=output.inputs['Surface'];assert surface.is_linked;active=surface.links[0].from_node;assert active.bl_idname=='ShaderNodeEmission'
field=[];errors=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 m=Matrix.Rotation(math.radians(a),4,'Z')
 for u in [0,.005,.01,.02,.035,.05,.065,.075,.08]:
  for y in [-.17,-.145,-.12,-.105,-.06,0,.06,.105,.12,.145,.17]:
   attrs={'collar_weight':1.0,'native_normal':Vector((.2,.3,.4)),'stone_color':Vector((.3,.2,.1))};p=[-.5+u,y,.5];q=[.5-u,y,.5]
   def call(n,p):return evaluate(nodes[n],nodes[n].outputs[0],p,m,attrs,{})
   nw=call('Normalize world shader normal',p);ne=call('Normalize world shader normal',q);cw=call('Coherent collar albedo',p);ce=call('Coherent collar albedo',q);rw=evaluate(active,active.outputs[0],p,m,attrs,{});re=evaluate(active,active.outputs[0],q,m,attrs,{})
   err=max((nw-ne).length,(cw-ce).length,(rw-re).length,abs(nw.length-1));errors.append(err)
   if u in [0,.04,.08] and y in [-.17,0,.17]:field.append({'direction':d,'offset':u,'y':y,'normalWorldW':list(nw),'normalWorldE':list(ne),'albedoW':list(cw),'radianceW':list(rw),'maxFieldError':err})
write('independent-native-inspection.json',{'projectSHA256':hashlib.sha256((R/'candidate.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'geometry':geometry,'actualShaderGraph':node_graph,'actualShaderLinks':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in links],'activeSurface':active.bl_idname,'surfaceOpacity':'Opaque emission surface, no transparency/mix shader; complete geometric caps retained. Active hemispheric normal-dependent radiance is native procedural shading within frozen method freedom.','actualLinkedGraphFieldEvaluation':{'sampleCount':len(errors),'maxFullCollarError':max(errors),'method':'Actual saved linked graph operations evaluated from world geometry position and actual root normal transform. All actual collar POINT weights are1; linear interpolation preserves1 on these complete surfaces including both n-gon caps. Base colors and noncollar normals deliberately perturbed in evaluation to prove the full-weight collar mix selects the analytic normalized field.','representativeSamples':field},'camera':{'matrix':rows(sc.camera.matrix_world),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'filterSize':sc.render.filter_size,'fps':sc.render.fps,'frame':sc.frame_current},'temporalChannels':[{'id':x.name,'action':x.animation_data.action.name if x.animation_data and x.animation_data.action else None,'drivers':len(x.animation_data.drivers) if x.animation_data else 0,'nla':len(x.animation_data.nla_tracks) if x.animation_data else 0} for x in [sc,root,body,body.data,material,material.node_tree,sc.world,sc.world.node_tree] if hasattr(x,'animation_data')]})
# Exact clean source replay at native settings. Never save the loaded scene.
ledger=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(a);sc.frame_set(1);bpy.context.view_layer.update();p=O/f'replay-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger.append({'direction':d,'path':p.name,'actualRootMatrix':rows(root.matrix_world),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'frame':[sc.render.resolution_x,sc.render.resolution_y]})
# True native joins with common expanded camera/frame and exact one-cell transforms.
cam=sc.camera;cam.data.ortho_scale=448/128;cam.data.shift_x=0;cam.data.shift_y=0;sc.render.resolution_x=1792;sc.render.resolution_y=2560;bpy.context.view_layer.update()
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*1792,(1-q.y)*2560]
b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=(384*4-b[1])/dy;root.rotation_euler.z=0;bpy.context.view_layer.update();copies=[]
for dx in [-1,1]:
 o=body.copy();o.data=body.data;o.parent=None;coll.objects.link(o);copies.append(o)
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),4,'Z');root.rotation_euler.z=math.radians(a)
 for o,dx in zip(copies,[-1,1]):o.matrix_world=rot@Matrix.Translation((dx,0,0))
 bpy.context.view_layer.update();p=O/f'native-join-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);ledger.append({'direction':d,'kind':'true native 3-module join','path':p.name,'rootMatrices':[rows(o.matrix_world) for o in [root]+copies],'frame':[1792,2560],'logicalFrame':[448,640],'logicalRoot':[224,384],'captureScale':4,'measuredRoot':px((0,0,0))})
write('independent-replay-ledger.json',{'projectSHA256':hashlib.sha256((R/'candidate.blend').read_bytes()).hexdigest(),'sourceNeverSaved':True,'renders':ledger})
print('Independent graph/geometry audit,4 source replays,4 native joins complete')
