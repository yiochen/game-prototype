import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'captures';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def scalar(v):
 try:return list(v)
 except:return v
def material(m):
 if not m.use_nodes:return {'nodes':False,'diffuse':list(m.diffuse_color)}
 ns=list(m.node_tree.nodes);nodes=[]
 for n in ns:
  nr={'type':n.bl_idname,'inputs':[]}
  for i in n.inputs:
   if hasattr(i,'default_value'):nr['inputs'].append([i.name,scalar(i.default_value)])
  for p in ['operation','attribute_name','blend_type','interpolation_type','voronoi_dimensions','feature','normalize','clamp']:
   if hasattr(n,p):nr[p]=getattr(n,p)
  if n.type=='VALTORGB':nr['ramp']=[n.color_ramp.interpolation,[[e.position,list(e.color)] for e in n.color_ramp.elements]]
  nodes.append(nr)
 return {'nodes':nodes,'links':[[ns.index(l.from_node),list(l.from_node.outputs).index(l.from_socket),ns.index(l.to_node),list(l.to_node.inputs).index(l.to_socket)] for l in m.node_tree.links]}
def settings(s):
 c=s.camera
 return {'engine':s.render.engine,'frame':[s.render.resolution_x,s.render.resolution_y],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filter':s.render.filter_size,'samples':s.eevee.taa_render_samples,'filmTransparent':s.render.film_transparent,'fps':s.render.fps,'frameRange':[s.frame_start,s.frame_end],'view':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],'dither':s.render.dither_intensity,'cameraType':c.data.type,'ortho':c.data.ortho_scale,'cameraMatrix':[list(r) for r in c.matrix_world],'shift':[c.data.shift_x,c.data.shift_y],'worldStrength':s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'grade':s.compositing_node_group.get('contrastFactor')}
def lights(s):
 return sorted([{'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color),'shadow':o.data.use_shadow} for o in s.objects if o.type=='LIGHT'],key=lambda x:x['position'])
def gather(coll):
 root=next(o for o in coll.all_objects if o.type=='EMPTY' and '__root' in o.name);root.rotation_euler.z=0
 coll.hide_viewport=False;coll.hide_render=False
 for o in coll.all_objects:o.hide_viewport=False;o.hide_set(False);o.update_tag(refresh={'OBJECT'})
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted()
 result={'collection':coll.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'objects':[],'materials':{},'endpointFaces':{},'samples':[]}
 pts=[];beyond=[];ground=[];bottomArea=0;active=[]
 for o in coll.all_objects:
  od={'name':o.name,'type':o.type,'animation':bool(o.animation_data and (o.animation_data.action or o.animation_data.drivers)),'hidden':o.hide_render}
  if o.type!='MESH':result['objects'].append(od);continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();mat=inv@eo.matrix_world;nm=mat.to_3x3().inverted().transposed();vs=[mat@v.co for v in me.vertices];pts+=vs;ground+=[list(v) for v in vs if abs(v.z)<1e-7];beyond+=[v.z for v in vs if v.y<-.45001]
  attrs=me.color_attributes.get('rock_shelf_albedo');cn=me.corner_normals
  od.update(vertices=len(vs),polygons=len(me.polygons),modifiers=[m.type for m in o.modifiers],shapeKeys=bool(o.data.shape_keys),bounds=[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]])
  for m in me.materials:
   rec=material(m);sg=hashlib.sha256(json.dumps(rec,sort_keys=True,default=str).encode()).hexdigest();result['materials'][m.name]={'signature':sg,'graph':rec,'animation':bool((m.animation_data and (m.animation_data.action or m.animation_data.drivers)) or (m.node_tree.animation_data and (m.node_tree.animation_data.action or m.node_tree.animation_data.drivers)))}
  caps={}
  for port,x in [('W',-.5),('E',.5)]:
   fs=[]
   for p in me.polygons:
    if not any(abs(vs[vi].x-x)<1e-6 for vi in p.vertices):continue
    fs.append({'cap':all(abs(vs[vi].x-x)<1e-6 for vi in p.vertices),'materialSignature':result['materials'][me.materials[p.material_index].name]['signature'],'faceNormal':list(p.normal),'corners':[{'position':list(vs[me.loops[li].vertex_index]),'normal':list((nm@cn[li].vector).normalized()),'albedo':list(attrs.data[me.loops[li].vertex_index].color) if attrs else None} for li in p.loop_indices if abs(vs[me.loops[li].vertex_index].x-x)<1e-6]})
   if fs:caps[port]=fs
  if caps:
   result['endpointFaces']=caps
   bv=BVHTree.FromPolygons(vs,[list(p.vertices) for p in me.polygons],all_triangles=False);me.calc_loop_triangles();tri={}
   for t in me.loop_triangles:tri.setdefault(t.polygon_index,[]).append(t)
   def sample(pos,dr):
    hit,n,pi,dist=bv.ray_cast(Vector(pos),Vector(dr))
    assert hit is not None,(pos,dr)
    chosen=None
    for t in tri[pi]:
     aa,bb,cc=[vs[i] for i in t.vertices];v0=bb-aa;v1=cc-aa;v2=hit-aa;d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);de=d00*d11-d01*d01
     if abs(de)<1e-20:continue
     vv=(d11*v2.dot(v0)-d01*v2.dot(v1))/de;ww=(d00*v2.dot(v1)-d01*v2.dot(v0))/de;weights=[1-vv-ww,vv,ww]
     if min(weights)>=-1e-4:chosen=(t,weights);break
    assert chosen,(pos,pi)
    t,ww=chosen;nn=Vector((0,0,0));al=[0,0,0,0]
    for k,li in enumerate(t.loops):
     nn+=(nm@cn[li].vector)*ww[k]
     if attrs:
      for j in range(4):al[j]+=attrs.data[me.loops[li].vertex_index].color[j]*ww[k]
    return {'position':list(hit),'normal':list(nn.normalized()),'albedo':al,'materialSignature':result['materials'][me.materials[me.polygons[pi].material_index].name]['signature']}
   for port,sign in [('W',-1),('E',1)]:
    for inset in [.0001,.001,.01,.03,.06]:
     x=sign*(.5-inset)
     for y in [-.35,-.18,0,.18,.35]:result['samples'].append({'port':port,'inset':inset,'surface':'top','q':y,**sample((x,y,1),(0,0,-1))})
     for side,sgn in [('negativeY',-1),('positiveY',1)]:
      for z in [.04,.13,.23,.32,.40]:result['samples'].append({'port':port,'inset':inset,'surface':side,'q':z,**sample((x,sgn*2,z),(0,-sgn,0))})
  for p in me.polygons:
   if all(abs(vs[v].z)<1e-7 for v in p.vertices):bottomArea+=p.area
  result['objects'].append(od);eo.to_mesh_clear()
 result.update(bounds=[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]],groundBounds=[[min(v[k] for v in ground) for k in range(3)],[max(v[k] for v in ground) for k in range(3)]],bottomArea=bottomArea,beyondGroundMinZ=min(beyond) if beyond else None,externalImages=[i.filepath for i in bpy.data.images],libraries=[l.filepath for l in bpy.data.libraries])
 return result
s=bpy.context.scene;candidate=next(c for c in s.collection.children if any(o.type=='MESH' and 'rock-shelf-edge' in o.name for o in c.all_objects));eroot=next(o for o in candidate.all_objects if o.type=='EMPTY')
result={'blender':bpy.app.version_string,'candidateSourceSHA256':sha(BASE/'resources/source/candidate.blend'),'canonicalSourceSHA256':sha(BASE/'resources/source/canonical.blend'),'candidateSettings':settings(s),'candidateLights':lights(s),'candidate':gather(candidate)}
# Reopen-driven single renders, without executing the embedded or external construction recipe.
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 eroot.rotation_euler.z=ang;bpy.context.view_layer.update();s.render.filepath=str(OUT/f'reopen-{d}-4x.png');bpy.ops.render.render(write_still=True)
eroot.rotation_euler.z=0;bpy.context.view_layer.update()
# Load only exact approved native collection; no canonical light/camera duplication.
with bpy.data.libraries.load(str(BASE/'resources/source/canonical.blend'),link=False) as (a,b):
 b.collections=[n for n in a.collections if n=='rock-shelf-middle canonical LOW shelf']
mc=b.collections[0];s.collection.children.link(mc);result['canonical']=gather(mc)
# Independently create only an in-memory diagnostic assembly from the saved meshes.
diag=bpy.data.collections.new('judge diagnostic mixed3 only');s.collection.children.link(diag);ar=bpy.data.objects.new('judge diagnostic assembly root',None);diag.objects.link(ar)
for offset,coll in [(-1,mc),(0,candidate),(1,mc)]:
 for ob in list(coll.all_objects):
  if ob.type!='MESH':continue
  cp=ob.copy();cp.data=ob.data;diag.objects.link(cp);cp.parent=ar;cp.matrix_parent_inverse=Matrix.Identity(4);cp.matrix_basis=ob.matrix_world.copy();cp.location.x+=offset
candidate.hide_render=True;mc.hide_render=True
cam=s.camera;s.render.resolution_x=1792;s.render.resolution_y=2432;cam.data.ortho_scale=3.5;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(1504-base.y)/dy;bpy.context.view_layer.update()
result['mixedAssemblyCamera']=settings(s);result['mixedAssemblyCalibration']={'root':list(px((0,0,0))),'X':list(px((1,0,0))-px((0,0,0))),'depth':list(px((0,-1,0))-px((0,0,0))),'height':list(px((0,0,1))-px((0,0,0)))}
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 ar.rotation_euler.z=ang;bpy.context.view_layer.update();s.render.filepath=str(OUT/f'mixed3-{d}-4x.png');bpy.ops.render.render(write_still=True)
# Separate canonical scene settings/lights are read from the actual saved file last.
bpy.ops.wm.open_mainfile(filepath=str(BASE/'resources/source/canonical.blend'))
result['canonicalSettings']=settings(bpy.context.scene);result['canonicalLights']=lights(bpy.context.scene)
# Actual field comparisons, including both opposing cap rings and exposed neighboring bands.
comp=[]
for sa,sb in zip(result['candidate']['samples'],result['canonical']['samples']):
 assert all(sa[k]==sb[k] for k in ['port','inset','surface','q'])
 comp.append({k:sa[k] for k in ['port','inset','surface','q']}|{'maxPositionError':max(abs(x-y) for x,y in zip(sa['position'],sb['position'])),'maxNormalError':max(abs(x-y) for x,y in zip(sa['normal'],sb['normal'])),'maxAlbedoError':max(abs(x-y) for x,y in zip(sa['albedo'],sb['albedo'])),'materialIdentity':sa['materialSignature']==sb['materialSignature']})
result['fieldComparisons']=comp;result['lightIdentity']=result['candidateLights']==result['canonicalLights']
(BASE/'native-independent.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print(json.dumps({'candidateBounds':result['candidate']['bounds'],'ground':result['candidate']['groundBounds'],'bottomArea':result['candidate']['bottomArea'],'beyondGroundMinZ':result['candidate']['beyondGroundMinZ'],'samples':len(comp),'maxFieldError':{k:max(c[k] for c in comp) for k in ['maxPositionError','maxNormalError','maxAlbedoError']},'allMaterialsMatch':all(c['materialIdentity'] for c in comp),'lightsMatch':result['lightIdentity']},indent=2))
