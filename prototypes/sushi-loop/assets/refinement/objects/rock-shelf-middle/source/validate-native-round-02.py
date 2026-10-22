import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import intersect_ray_tri,barycentric_transform
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'candidates/round-02'
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-middle__root'];bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
objects=[];allverts=[];core=None;external=[]
for o in s.objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(dep);me=e.to_mesh();me.calc_loop_triangles();vv=[list(e.matrix_world@v.co) for v in me.vertices];allverts+=vv
 rec={'name':o.name,'hasCustomNormals':me.has_custom_normals,'vertices':len(me.vertices),'polygons':len(me.polygons),'triangles':len(me.loop_triangles),'bounds':[[min(v[k] for v in vv) for k in range(3)],[max(v[k] for v in vv) for k in range(3)]],'materialSlots':[m.name for m in me.materials],'shapeKeys':bool(o.data.shape_keys),'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'parent':o.parent.name if o.parent else None}
 if 'sculpted_core' in o.name:
  core=(o,e,me);rec['capFaces']=[{'index':p.index,'vertices':[list(me.vertices[vi].co) for vi in p.vertices],'normal':list(p.normal),'smooth':p.use_smooth} for p in me.polygons if abs(p.normal.x)>.9999 and all(abs(abs(me.vertices[vi].co.x)-.5)<1e-6 for vi in p.vertices)]
  edgeuses={}
  for p in me.polygons:
   a=list(p.vertices)
   for u,v in zip(a,a[1:]+a[:1]):key=tuple(sorted((u,v)));edgeuses[key]=edgeuses.get(key,0)+1
  rec['topology']={'boundaryEdges':sum(v==1 for v in edgeuses.values()),'nonManifoldEdges':sum(v!=2 for v in edgeuses.values())}
 objects.append(rec)
# Actual triangle-interpolated native normals and authored albedo, not names or AABBs.
o,e,me=core
attr=me.color_attributes['rock_shelf_albedo'];triangles=[]
for t in me.loop_triangles:
 triangles.append((t,[me.vertices[i].co.copy() for i in t.vertices]))
def sample(origin,direction):
 origin=Vector(origin);direction=Vector(direction);best=None
 for t,v in triangles:
  p=intersect_ray_tri(*v,direction,origin,True)
  if p is None or (p-origin).dot(direction)<-1e-7:continue
  distance=(p-origin).length
  if best and distance>=best[0]:continue
  weights=barycentric_transform(p,*v,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  normal=sum((me.corner_normals[li].vector*w for li,w in zip(t.loops,weights)),Vector()).normalized()
  color=[sum(attr.data[vi].color[c]*w for vi,w in zip(t.vertices,weights)) for c in range(4)]
  best=(distance,{'position':list(p),'normal':list(normal),'albedo':color,'material':me.materials[me.polygons[t.polygon_index].material_index].name,'polygon':t.polygon_index})
 return best[1] if best else None
samples=[]
for inset in (.0001,.001,.01,.03,.059):
 for surface,coords in [('top',[-.35,-.18,0,.18,.35]),('negativeY',[.04,.13,.23,.32,.40]),('positiveY',[.04,.13,.23,.32,.40])]:
  for q in coords:
   row={'inset':inset,'surface':surface,'transverse':q}
   for side,x in [('W',-.5+inset),('E',.5-inset)]:
    ray=((x,q,1),(0,0,-1)) if surface=='top' else ((x,-1,q),(0,1,0)) if surface=='negativeY' else ((x,1,q),(0,-1,0))
    row[side]=sample(*ray)
   a,b=row['W'],row['E'];row['delta']={'YZ':max(abs(a['position'][k]-b['position'][k]) for k in [1,2]),'normal':max(abs(a['normal'][k]-b['normal'][k]) for k in range(3)),'albedo':max(abs(a['albedo'][k]-b['albedo'][k]) for k in range(4))};samples.append(row)
# Actual graphs and animation inspection, canonical private source resources.
materials=[]
for m in bpy.data.materials:
 nodes=[]
 if m.node_tree:
  for n in m.node_tree.nodes:
   nodes.append({'name':n.name,'type':n.bl_idname,'attributeName':getattr(n,'attribute_name',None),'inputs':{a.name:list(a.default_value) if hasattr(a.default_value,'__len__') else a.default_value for a in n.inputs if hasattr(a,'default_value') and isinstance(a.default_value,(int,float,str,tuple,list)) or hasattr(a,'default_value') and type(a.default_value).__name__ in ['bpy_prop_array','Color','Vector']}})
 for nr,nn in zip(nodes,list(m.node_tree.nodes)) if m.node_tree else []:
  nr['properties']={k:getattr(nn,k) for k in ['operation','feature','voronoi_dimensions','interpolation_type','space','vector_type'] if hasattr(nn,k)}
  if hasattr(nn,'color_ramp'):nr['colorRamp']={'interpolation':nn.color_ramp.interpolation,'elements':[{'position':el.position,'color':list(el.color)} for el in nn.color_ramp.elements]}
 rec={'name':m.name,'users':m.users,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.node_tree else [],'action':m.animation_data.action.name if m.animation_data and m.animation_data.action else None,'nodeAction':m.node_tree.animation_data.action.name if m.node_tree and m.node_tree.animation_data and m.node_tree.animation_data.action else None}
 rec['resourceSHA256']=hashlib.sha256(json.dumps(rec,sort_keys=True,default=str).encode()).hexdigest();materials.append(rec)
lightrec=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'useShadow':o.data.use_shadow,'position':list(o.location),'rotation':list(o.rotation_euler)} for o in s.objects if o.type=='LIGHT']
bounds=[[min(v[k] for v in allverts) for k in range(3)],[max(v[k] for v in allverts) for k in range(3)]]
endpoints={'truePlanes':[-.5,.5],'profileYZ':[[-.45,0],[.45,0],[.45,.28],[.39,.43],[-.39,.43],[-.45,.28]],'neighborBandsWorld':.06,'orderedSamples':samples,'maxBandResidual':{k:max(x['delta'][k] for x in samples) for k in ['YZ','normal','albedo']},'normalsMethod':'Actual evaluated triangulated smooth corner normals and point albedo barycentric interpolation. Cap faces use flat shading; actual resulting boundary normals are measured, not inferred.'}
profile=endpoints['profileYZ'];ordered={}
for label,xx in [('W',-.5),('E',.5)]:
 edges=[]
 for p in me.polygons:
  on=[li for li in p.loop_indices if abs(me.vertices[me.loops[li].vertex_index].co.x-xx)<1e-7]
  if len(on)!=2:continue
  record=[]
  for li in on:
   vi=me.loops[li].vertex_index;co=me.vertices[vi].co
   pi=min(range(6),key=lambda i:(co.y-profile[i][0])**2+(co.z-profile[i][1])**2)
   record.append({'profileVertex':pi,'YZ':[co.y,co.z],'normal':list(me.corner_normals[li].vector),'albedo':list(attr.data[vi].color)})
  inds={r['profileVertex'] for r in record};edge=next(q for q in range(6) if inds=={q,(q+1)%6});record.sort(key=lambda r:0 if r['profileVertex']==edge else 1)
  edges.append({'profileEdge':edge,'outwardGeometricNormal':list(p.normal),'endpointCorners':record,'material':me.materials[p.material_index].name})
 ordered[label]=sorted(edges,key=lambda e:e['profileEdge'])
assert len(ordered['W'])==len(ordered['E'])==6
maxdirect={key:max(abs(a['endpointCorners'][c][key][k]-b['endpointCorners'][c][key][k]) for a,b in zip(ordered['W'],ordered['E']) for c in range(2) for k in range(4 if key=='albedo' else 3 if key=='normal' else 2)) for key in ['YZ','normal','albedo']}
endpoints['orderedTrueEndpointSurfaceEvidence']=ordered;endpoints['trueEndpointResidual']=maxdirect
assert maxdirect['YZ']<1e-7 and maxdirect['albedo']<1e-7 and maxdirect['normal']<1e-5,maxdirect
endpoints['planarCutfaceNativeShader']={'material':'rock-shelf-middle canonical planar cut stone v2','coordinateField':'Actual localObjectY*2.2 -> Voronoi2D.X; actual localObjectZ*4.5 -> Voronoi2D.Y; localObjectX is unlinked. Both caps share this graph; actual feature/ramps/bump/links recorded in native-validation materials.','capInputSamples':[{'YZ':yz,'nativeShaderVector':[yz[0]*2.2,yz[1]*4.5,0]} for yz in endpoints['profileYZ']],'physicalCapDisplacement':0,'appearanceMethod':'Native PBR color and rounded Voronoi bump; geometry stays exactsix-point planar cut.'}
(OUT/'endpoint-evidence.json').write_text(json.dumps(endpoints,indent=2))
static={'nativeFrame':s.frame_current,'frameStart':s.frame_start,'frameEnd':s.frame_end,'fps':s.render.fps,'loop':False,'armatures':[o.name for o in s.objects if o.type=='ARMATURE'],'objectActions':[o.name for o in s.objects if o.animation_data and o.animation_data.action],'materialActions':[m['name'] for m in materials if m['action'] or m['nodeAction']],'shapeKeys':[o['name'] for o in objects if o['shapeKeys']]}
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:external.append({'image':image.name,'path':image.filepath})
external += [{'library':x.name,'path':x.filepath} for x in bpy.data.libraries]
rec={'asset':'rock-shelf-middle','round':'round-02','approval':'pending independent original judge','sourceProjectSHA256':sha(BASE/'round-02.blend'),'embeddedRecipeSHA256':hashlib.sha256(bpy.data.texts['build-round-02.py'].as_string().encode()).hexdigest(),'externalRecipeSHA256':sha(BASE/'build-round-02.py'),'rootMatrix':[list(row) for row in root.matrix_world],'cameraWorldMatrix':[list(row) for row in s.camera.matrix_world],'orthographicScale':s.camera.data.ortho_scale,'cameraType':s.camera.data.type,'blender':bpy.app.version_string,'objects':objects,'bounds':bounds,'envelope':[[-.5,-.45,0],[.5,.45,.45]],'envelopeTolerance':1e-5,'finiteGroundSupport':{'x':[-.5,.5],'y':[-.45,.45],'z':0,'intentionalNonPortMargins':.05,'actualNativeBottomArea':sum(p.area for p in me.polygons if all(abs(me.vertices[v].co.z)<1e-7 for v in p.vertices))},'endpoints':{'evidence':'endpoint-evidence.json','maxBandResidual':endpoints['maxBandResidual']},'staticActualChecks':static,'materials':materials,'lights':lightrec,'resources':{'externalDependencies':external,'images':[(i.name,i.source,bool(i.packed_file)) for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]},'settings':{'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'filmTransparent':s.render.film_transparent,'view':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'grade':1.35,'dither':s.render.dither_intensity,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'sourceIntegrity':{name:sha(BASE.parent/name) for name in ['brief.json','inputs/root-native-contract.json','inputs/target.png','inputs/original.png']}}
assert all(bounds[0][i]>=rec['envelope'][0][i]-1e-5 and bounds[1][i]<=rec['envelope'][1][i]+1e-5 for i in range(3))
assert objects[0]['topology']['boundaryEdges']==0 and objects[0]['topology']['nonManifoldEdges']==0,objects[0]['topology']
assert not static['armatures'] and not static['objectActions'] and not static['materialActions'] and not static['shapeKeys']
assert not external
(OUT/'native-validation.json').write_text(json.dumps(rec,indent=2,default=str))
print(json.dumps({'bounds':bounds,'maxBandResidual':endpoints['maxBandResidual'],'static':static,'external':external},indent=2))
