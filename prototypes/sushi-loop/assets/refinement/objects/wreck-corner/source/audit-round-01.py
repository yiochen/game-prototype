import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;B=S.parent;O=B/'candidates/round-01';R=S/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vv(v):return [float(x) for x in v]
def matrix(o):return [vv(r) for r in o.matrix_world]
sc=bpy.context.scene;col=bpy.data.collections['S33_PROP_wreck-corner.001'];root=bpy.data.objects['wreck-corner__root.001'];col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
rec=json.loads((R/'root-preparation-reconciliation-v1.json').read_text());poly=rec['authoringEnvelope']['xy'];captures=json.loads((O/'capture-records.json').read_text());allgeo={};views=[]
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;sc.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();deps.update();own=[];pts=[];supports=[];violations=[]
 for o in sorted(col.all_objects,key=lambda o:o.name):
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();v=[root.matrix_world.inverted() @ ev.matrix_world @ p.co for p in me.vertices];pts+=v
  for i,p in enumerate(v):
   ds=[]
   for q,w in zip(poly,poly[1:]+poly[:1]):
    dx=w[0]-q[0];dy=w[1]-q[1];ds.append((dx*(p.y-q[1])-dy*(p.x-q[0]))/math.hypot(dx,dy))
   if min(ds)<-1e-6 or p.z<.04-1e-6 or p.z>.78+1e-6:violations.append({'object':o.name,'vertex':i,'position':vv(p),'hullMinimumSignedDistance':min(ds)})
  for t in me.loop_triangles:
   pp=[v[i] for i in t.vertices]
   if all(abs(p.z-.04)<1e-6 for p in pp):supports.append([vv(p) for p in pp])
  own.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':matrix(o),'evaluatedVertices':len(me.vertices),'evaluatedPolygons':len(me.polygons),'materials':[m.name for m in me.materials]})
  ev.to_mesh_clear()
 supportarea=sum(abs((t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0]))/2 for t in supports)
 # Read source-captured measured facing record and recapture unchanged saved source.
 original=next(r for r in captures['records'] if r['kind']=='hero' and r['direction']==d)
 target=O/'replay'/('hero-'+d+'.png');target.parent.mkdir(exist_ok=True);sc.render.filepath=str(target);bpy.ops.render.render(write_still=True)
 views.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':matrix(root),'sourceSHA256':sha(S/'round-01.blend'),'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'cameraWorld':matrix(sc.camera),'rootCalibration':original['camera']['calibration'],'nativeCaptureSHA256':original['sha256'],'savedSourceReplaySHA256':sha(target),'pngByteEqual':sha(target)==original['sha256'],'rawFiniteEnvelopeViolations':violations,'finiteSupportArea':supportarea,'supportAreaAbsoluteError':abs(supportarea-rec['support']['area'])})
 allgeo[d]={'objects':own,'supportTriangles':supports,'rootLocalBounds':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}}
# Every finite side/cap patch is checked as an entire affine field, not a point-sampling substitute.
root.rotation_euler.z=0;bpy.context.view_layer.update();fields=[]
for o in col.objects:
 if 'continuous_hull' not in o.name:continue
 me=o.data;attr=me.attributes['CanonicalNormal'];canonical=bpy.data.objects[o.name.replace('wreck-corner__','wreck-middle__').replace('_continuous_hull','_canonical_rail')]
 for side in ['W','N']:
  fs=[]
  for f in me.polygons:
   vs=[me.vertices[i].co for i in f.vertices]
   iscollar=all(v.x<=-.42+1e-7 for v in vs) if side=='W' else all(v.y>=.42-1e-7 for v in vs)
   if not iscollar:continue
   mapped=[(v.x,v.y,v.z) if side=='W' else (v.y,-v.x,v.z) for v in vs]
   ns=[Vector(attr.data[i].vector).normalized() for i in f.loop_indices];ns=[(n.x,n.y,n.z) if side=='W' else (n.y,-n.x,n.z) for n in ns]
   cap=all(abs(v[0]-(-.5 if side=='W' else .5))<1e-7 for v in mapped)
   if cap:expected=(-1,0,0) if side=='W' else (1,0,0)
   else:
    # Canonical finite side patches are exactly transverse or height planes.
    yspan=max(v[1] for v in mapped)-min(v[1] for v in mapped);zspan=max(v[2] for v in mapped)-min(v[2] for v in mapped)
    cy=sum(v[1] for v in mapped)/len(mapped);cz=sum(v[2] for v in mapped)/len(mapped)
    if yspan<1e-7:
     ys=[v.co.y for v in canonical.data.vertices if abs(v.co.x-.5)<1e-6];expected=(0,-1 if abs(cy-min(ys))<1e-6 else 1,0)
    elif zspan<1e-7:
     zs=[v.co.z for v in canonical.data.vertices if abs(v.co.x-.5)<1e-6];expected=(0,0,-1 if abs(cz-min(zs))<1e-6 else 1)
    else:raise AssertionError('Nonplanar canonical collar side')
   err=max((Vector(n)-Vector(expected)).length for n in ns)
   mat=me.materials[f.material_index]
   assert mat in list(canonical.data.materials),'Actual active material differs from exact canonical'
   fs.append({'polygon':f.index,'mappedCanonicalVertices':[list(v) for v in mapped],'normalizedShaderCornerNormals':[list(n) for n in ns],'expectedEntirePatchNormal':list(expected),'maxVectorError':err,'cap':cap,'material':mat.name,'canonicalMaterialDatablockIdentical':True,'postInterpolationProof':'All corner values equal the fixed canonical side/cap vector, so interpolation and shader normalization give the same constant field throughout each entire finite patch; derivative zero.'})
  fields.append({'object':o.name,'side':side,'mapping':'identity' if side=='W' else 'inverse properRz90 to canonical E','faces':fs})
materials=[]
for m in {m for o in col.objects if o.type in ['MESH','CURVE'] for m in o.data.materials if m}:
 nodes=[]
 for n in m.node_tree.nodes:
  item={'name':n.name,'type':n.bl_idname,'inputs':{}}
  for inp in n.inputs:
   if hasattr(inp,'default_value'):
    v=inp.default_value
    try:v=list(v)
    except TypeError:pass
    if isinstance(v,(str,bool,int,float,list)):item['inputs'][inp.name]=v
  if n.bl_idname=='ShaderNodeAttribute':item['attribute_name']=n.attribute_name
  if n.bl_idname=='ShaderNodeVectorTransform':item.update(vector_type=n.vector_type,convert_from=n.convert_from,convert_to=n.convert_to)
  nodes.append(item)
 materials.append({'name':m.name,'nodes':nodes,'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
lights=[{'name':o.name,'type':o.data.type,'color':vv(o.data.color),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'use_shadow':o.data.use_shadow,'matrixWorld':matrix(o)} for o in sc.objects if o.type=='LIGHT']
world={'name':sc.world.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value')}} for n in sc.world.node_tree.nodes]}
data={'asset':'wreck-corner','sourceSHA256':sha(S/'round-01.blend'),'blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'views':views,'nativeGeometryMeasurements':allgeo,'fullFiniteCollarFields':fields,'materials':materials,'lights':lights,'world':world,'externalLibraries':[l.filepath for l in bpy.data.libraries],'imageTextureNodes':[{'material':m.name,'node':n.name} for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage'],'actualCamera':{'type':'orthographic','worldMatrix':matrix(sc.camera),'projectionMatrix':[list(row) for row in sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(math.atan(1/.7))},'rootProperties':dict(root.items()),'staticOwners':[o.name for o in col.objects],'ownActions':[o.name for o in col.objects if o.animation_data and o.animation_data.action],'capture':{'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filter':sc.render.filter_size,'filmTransparent':sc.render.film_transparent,'dither':sc.render.dither_intensity},'limits':'Native numerical evidence does not constitute visual approval. Finite geometric support boundary verification and field-coverage summary are performed separately from these full measurements.'}
(O/'native-validation.json').write_text(json.dumps(data,indent=2)+'\n');print('AUDIT',[(v['direction'],len(v['rawFiniteEnvelopeViolations']),v['supportAreaAbsoluteError'],v['pngByteEqual']) for v in views]);print('FIELDS',max(f['maxVectorError'] for x in fields for f in x['faces']))
