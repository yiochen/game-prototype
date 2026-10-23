"""Fresh reopen measurement, exact family/native contract verification."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
B=Path(__file__).resolve().parents[1];R='round-01';C=B/'candidates'/R;P=B/'source'/f'{R}.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(P));s=bpy.context.scene;c=bpy.data.collections['S33_PROP_wall-end.refined'];root=next(o for o in c.all_objects if o.type=='EMPTY');bpy.context.view_layer.update()
family=json.loads((B/'source/round-01-family-settings.json').read_text());source=json.loads((B/'candidates/inspection/source.json').read_text())
def value(v):
 if isinstance(v,(str,int,float,bool))or v is None:return v
 try:return [value(t)for t in v]
 except:return str(v)
def nodes(tree):
 result=[]
 for n in tree.nodes:
  q={'name':n.name,'bl_idname':n.bl_idname,'inputs':{str(i)+':'+v.name:value(v.default_value)for i,v in enumerate(n.inputs)if hasattr(v,'default_value')}}
  for prop in ('operation','blend_type','vector_type','convert_from','convert_to','interpolation','distribution','subsurface_method','space'):
   if hasattr(n,prop):q[prop]=value(getattr(n,prop))
  if hasattr(n,'color_ramp'):q['colorRamp']={'interpolation':n.color_ramp.interpolation,'colorMode':n.color_ramp.color_mode,'elements':[{'position':e.position,'color':list(e.color)}for e in n.color_ramp.elements]}
  result.append(q)
 return {'nodes':result,'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name,'toIndex':list(l.to_node.inputs).index(l.to_socket)}for l in tree.links]}

dg=bpy.context.evaluated_depsgraph_get();meshes=[];profileChecks=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 m=o.data;ev=o.evaluated_get(dg);pts=[o.matrix_world@v.co for v in ev.data.vertices]
 edgeuses={tuple(sorted(e.vertices)):0 for e in m.edges}
 for p in m.polygons:
  vs=list(p.vertices)
  for a,b in zip(vs,vs[1:]+vs[:1]):edgeuses[tuple(sorted((a,b)))]+=1
 boundary=[e for e,n in edgeuses.items()if n==1];bad=[e for e,n in edgeuses.items()if n>2]
 meshes.append({'name':o.name,'matrix':value(o.matrix_world),'vertices':len(m.vertices),'evaluatedVertices':len(ev.data.vertices),'polygons':len(m.polygons),'evaluatedPolygons':len(ev.data.polygons),'zeroAreaFaces':sum(p.area<1e-12 for p in ev.data.polygons),'nonManifoldEdges':len(bad),'openEdges':len(boundary),'openBoundaryXCoordinates':sorted(set(round(m.vertices[i].co.x,6)for e in boundary for i in e)),'bounds':[[min(v[i]for v in pts),max(v[i]for v in pts)]for i in range(3)],'hasCustomNormals':m.has_custom_normals,'materials':[m.name for m in m.materials],'modifiers':[{'type':q.type,'name':q.name}for q in o.modifiers]})
 if not any(k in o.name for k in['terminal_','shaft_field_','camera_cut_planes']):
  part=o.name.split('__')[1];old=next(q for q in source['objects']if q['name'].split('__')[1].replace('.001','')==part);v=old['vertices'];segments=[]
  for f in old['faces']:
   for a,b in zip(f,f[1:]+f[:1]):
    if abs(v[a][0]+.5)<1e-6 and abs(v[b][0]+.5)<1e-6:segments.append((Vector(v[a][1:]),Vector(v[b][1:])))
  ps=sorted(set((round(v.co.y,7),round(v.co.z,7))for v in m.vertices if abs(v.co.x+.5)<1e-6));oldps=sorted(set((v[1],v[2])for v in old['vertices']if abs(v[0]+.5)<1e-6))
  def dist(p):
   p=Vector(p);ds=[]
   for a,b in segments:
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared))if d.length_squared else 0;ds.append((p-a-d*t).length)
   return min(ds)
  err=max(map(dist,ps));corners=all(any((Vector(p)-Vector(q)).length<1e-6 for q in ps)for p in oldps)
  profileChecks.append({'part':part,'maximumDistanceToSourceProfile':err,'containsEverySourceCorner':corners,'passed':err<1e-6 and corners,'coordinates':ps})
matdata=[{'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':nodes(m.node_tree)}for m in bpy.data.materials if m.users and m.node_tree]
matmap={m['name']:m for m in family['materials']};materialChecks=[{'name':m['name'],'exactApprovedGraphAndValues':m==matmap.get(m['name'])}for m in matdata]
cam=s.camera;capture={'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'frame':[s.render.resolution_x,s.render.resolution_y],'cellSize':128,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'camera':{'worldMatrix':value(cam.matrix_world),'type':cam.data.type,'sensorFit':cam.data.sensor_fit,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'clipStart':cam.data.clip_start,'clipEnd':cam.data.clip_end},'facingDegrees':{'S':0,'E':90,'N':180,'W':-90}}
lighting={'world':{'name':s.world.name,'nodeTree':nodes(s.world.node_tree)},'lights':[{'name':o.name,'type':o.data.type,'shape':o.data.shape,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrix':value(o.matrix_world)}for o in s.objects if o.type=='LIGHT'],'horizontalSymmetry':4,'noGroundReceiver':True}
render={'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'denoise':s.cycles.use_denoising,'maxBounces':s.cycles.max_bounces,'transparentMaxBounces':s.cycles.transparent_max_bounces,'filterSize':s.render.filter_size,'pixelFilter':s.cycles.pixel_filter_type,'transparent':s.render.film_transparent,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'outputFormat':s.render.image_settings.file_format,'outputColorMode':s.render.image_settings.color_mode,'outputColorDepth':s.render.image_settings.color_depth}
allpts=[o.matrix_world@v.co for o in c.all_objects if o.type=='MESH'for v in o.evaluated_get(dg).data.vertices];bound=[[min(v[i]for v in allpts),max(v[i]for v in allpts)]for i in range(3)];contacts=[{'name':m['name'],'groundZ':m['bounds'][2][0],'x':m['bounds'][0],'y':m['bounds'][1]}for m in meshes if abs(m['bounds'][2][0])<1e-6]
checks={'isolatedAsset':all(o.name in c.all_objects or o.type in['LIGHT','CAMERA']for o in s.objects),'noExternalDependencies':not bpy.data.images and not bpy.data.libraries,'noZeroAreaFaces':all(m['zeroAreaFaces']==0 for m in meshes),'noNonManifoldEdges':all(m['nonManifoldEdges']==0 for m in meshes),'actualRootAtOrigin':root.location.length<1e-7,'functionalEnvelope':bound[0][0]>=-.500001 and bound[0][1]<=.410001 and bound[1][0]>=-.180001 and bound[1][1]<=.180001 and bound[2][0]>=-.000001 and bound[2][1]<=1.020001,'sourceWProfilesPreserved':all(q['passed']for q in profileChecks),'exactFamilyMaterials':all(q['exactApprovedGraphAndValues']for q in materialChecks),'exactFamilyLighting':lighting==family['lighting'],'exactFamilyRender':render==family['render'],'exactFamilyCapture':capture==family['capture'],'groundContactPresent':bool(contacts),'oneWPortOnly':json.loads(root['ports'])==[{'direction':'W','position':[-.5,0,0],'profile':'restaurant-wall-wood-blue-v2','normal':[-1,0,0]}]}
audit={'project':{'path':str(P.relative_to(B)),'sha256':sha(P)},'blender':bpy.app.version_string,'scene':s.name,'root':{'name':root.name,'location':list(root.location),'matrix':value(root.matrix_world),'ports':json.loads(root['ports'])},'sourceBounds':[[-.5,.41],[-.18,.18],[0,1.02]],'evaluatedBounds':bound,'groundContacts':contacts,'meshes':meshes,'profileChecks':profileChecks,'materialChecks':materialChecks,'capture':capture,'render':render,'lighting':lighting,'materials':matdata,'resourceClosure':{'images':[{'name':i.name,'path':i.filepath}for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]},'checks':checks}
(C/'native-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(checks,indent=2))
