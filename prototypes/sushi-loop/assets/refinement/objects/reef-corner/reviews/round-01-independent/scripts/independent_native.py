import bpy,json,math,collections,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
p=Path(__file__).resolve().parents[1];out=p/'evidence/native';out.mkdir(exist_ok=True)
def write(n,v):(p/'evidence'/n).write_text(json.dumps(v,indent=2)+'\n')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def plain(x):
 try:return list(x) if not isinstance(x,(float,int,str,bool)) else x
 except:return str(x)
def material(m):
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');r=next((n for n in m.node_tree.nodes if n.type=='VALTORGB'),None)
 return {'roughness':bs.inputs['Roughness'].default_value,'specularIOR':bs.inputs['Specular IOR Level'].default_value,'base':list(bs.inputs['Base Color'].default_value),'normalLinked':bs.inputs['Normal'].is_linked,'ramp':{'interpolation':r.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in r.color_ramp.elements]} if r else None,'links':[(l.from_node.bl_idname,l.from_socket.identifier,l.to_node.bl_idname,l.to_socket.identifier) for l in m.node_tree.links],'animation':bool(m.animation_data) or bool(m.node_tree.animation_data)}
def alb(m,z):
 if not m['ramp']:return m['base']
 a,b=m['ramp']['elements'];u=max(0,min(1,(z-a[0])/(b[0]-a[0])));return [a[1][j]*(1-u)+b[1][j]*u for j in range(4)]
def rig(sc):return {'lights':[{'location':list(o.location),'rotation':list(o.rotation_euler),'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'world':[{'type':n.bl_idname,'inputs':{s.identifier:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in sc.world.node_tree.nodes],'color':{'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'samples':sc.eevee.taa_render_samples,'filter':sc.render.filter_size}}
def trirecs(o,rot=Matrix.Identity(3)):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();rs=[]
 for t in me.loop_triangles:rs.append({'positions':[list(rot@me.vertices[i].co) for i in t.vertices],'corners':[list(rot@me.corner_normals[i].vector) for i in t.loops],'normal':list(rot@t.normal),'material':material(me.materials[t.material_index]),'materialName':me.materials[t.material_index].name})
 ev.to_mesh_clear();return rs
bpy.ops.wm.open_mainfile(filepath=str(p/'resources/source/canonical-middle.blend'));sc=bpy.context.scene;bpy.data.objects['reef-middle__root'].rotation_euler.z=0;bpy.context.view_layer.update();canonicalRig=rig(sc);canonical=[]
for side,rot in [('W',Matrix.Identity(3)),('N',Matrix.Rotation(math.pi/2,3,'Z'))]:
 for t in trirecs(bpy.data.objects['reef-middle__continuous_core'],rot):
  v=[q[0 if side=='W' else 1] for q in t['positions']]
  if (all(-.500001<=x<=-.419999 for x in v) if side=='W' else all(.419999<=x<=.500001 for x in v)) and max(v)-min(v)>1e-6:t['side']=side;canonical.append(t)
bpy.ops.wm.open_mainfile(filepath=str(p/'resources/source/round-01.blend'));sc=bpy.context.scene;col=bpy.data.collections['reef-corner'];root=bpy.data.objects['reef-corner__root'];root.rotation_euler.z=0;bpy.context.view_layer.update();core=bpy.data.objects['reef-corner__continuous_core'];candidate=trirecs(core);candidateRig=rig(sc)
def key(v):return tuple(round(x,6) for x in v)
lookup={tuple(sorted(key(v) for v in t['positions'])):t for t in candidate};samples=[];matches=[]
for ct in canonical:
 at=lookup[tuple(sorted(key(v) for v in ct['positions']))];order=[next(j for j,v in enumerate(at['positions']) if key(v)==key(q)) for q in ct['positions']]
 matches.append({'side':ct['side'],'canonical':ct,'candidate':at,'materialResponseEqual':ct['material']==at['material']})
 for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
  q=sum((Vector(v)*w for v,w in zip(ct['positions'],weights)),Vector());r=sum((Vector(at['positions'][i])*w for i,w in zip(order,weights)),Vector());n=sum((Vector(v)*w for v,w in zip(ct['corners'],weights)),Vector()).normalized();nn=sum((Vector(at['corners'][i])*w for i,w in zip(order,weights)),Vector()).normalized();aa=alb(ct['material'],q.z);bb=alb(at['material'],r.z)
  samples.append({'side':ct['side'],'weights':weights,'position':list(q),'positionError':(q-r).length,'canonicalShaderNormal':list(n),'candidateShaderNormal':list(nn),'normalError':(n-nn).length,'canonicalAlbedo':aa,'candidateAlbedo':bb,'albedoError':max(abs(x-y) for x,y in zip(aa,bb))})
assert len(canonical)==32 and len(samples)==128
# Finite perimeter and actual static ownership, independently evaluated.
contract=json.loads((p/'resources/object/root-native-contract.json').read_text())['nativeContract'];poly=contract['functionalContract']['support']['outerPolygonXY'][:-1]
def inside(q):
 x,y=q;v=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:v=not v
 return v
def dist(q):
 a=Vector(q);rs=[]
 for x,y in zip(poly,poly[1:]+poly[:1]):
  x=Vector(x);y=Vector(y);t=max(0,min(1,(a-x).dot(y-x)/(y-x).length_squared));rs.append((a-(x+t*(y-x))).length)
 return min(rs)
pts=[];parts=[];outside=[];dg=bpy.context.evaluated_depsgraph_get()
for o in col.all_objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();v=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];pts+=v
 for q in v:
  if not inside(q[:2]) and dist(q[:2])>1e-5:outside.append({'part':o.name,'position':list(q)})
 parts.append({'name':o.name,'meshUsers':o.data.users,'bounds':[[min(q[j] for q in v) for j in range(3)],[max(q[j] for q in v) for j in range(3)]],'animation':bool(o.animation_data),'shapeKeys':bool(o.data.shape_keys),'constraints':[x.type for x in o.constraints],'materials':[material(m) for m in me.materials]});ev.to_mesh_clear()
me=core.data;me.calc_loop_triangles();edges=collections.Counter(tuple(sorted(e)) for f in me.polygons for e in f.edge_keys);bottom=[{'positions':[list(me.vertices[i].co) for i in t.vertices],'normal':list(t.normal),'area':t.area} for t in me.loop_triangles if all(abs(me.vertices[i].co.z)<1e-7 for i in t.vertices)]
# Independent sampling of bottom coverage: no accidental source hole required, actual clean interior expected.
def inTri(q,tri):
 def cr(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 s=[cr(tri[i],tri[(i+1)%3],q) for i in range(3)];return min(s)>=-1e-10 or max(s)<=1e-10
miss=[];extra=[]
for ix in range(101):
 for iy in range(101):
  q=(-.505+ix*.01,-.385+iy*.01);expected=inside(q);actual=any(inTri(q,t['positions']) for t in bottom)
  if expected!=actual and dist(q)>1e-5:(miss if expected else extra).append(q)
cam=sc.camera
saved={'matrix':[list(r) for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'engine':sc.render.engine,'filter':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'rootMatrix':[list(r) for r in root.matrix_world]}
write('independent-native-audit.json',{'sourceSHA256':sha(p/'resources/source/round-01.blend'),'canonicalSHA256':sha(p/'resources/source/canonical-middle.blend'),'blender':bpy.app.version_string,'savedCapture':saved,'profileAndFields':{'matches':matches,'samples':samples,'triangleCount':len(matches),'maxPositionError':max(x['positionError'] for x in samples),'maxShaderNormalError':max(x['normalError'] for x in samples),'maxAlbedoError':max(x['albedoError'] for x in samples),'materialResponseEqual':all(x['materialResponseEqual'] for x in matches),'shaderNormalOverride':any(x['candidate']['material']['normalLinked'] for x in matches)},'rigEqual':canonicalRig==candidateRig,'canonicalRig':canonicalRig,'candidateRig':candidateRig,'parts':parts,'bounds':[[min(q[j] for q in pts) for j in range(3)],[max(q[j] for q in pts) for j in range(3)]],'finiteExteriorOutsideVertices':outside,'coreTopology':{'V':len(me.vertices),'E':len(edges),'F':len(me.polygons),'Euler':len(me.vertices)-len(edges)+len(me.polygons),'edgeIncidenceHistogram':dict(collections.Counter(edges.values())),'bottomTriangles':bottom,'bottomArea':sum(x['area'] for x in bottom),'upwardBottomTriangles':sum(x['normal'][2]>0 for x in bottom),'sampledMissingBottom':miss,'sampledExtraBottom':extra,'samples':10201},'actions':[a.name for a in bpy.data.actions],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images]})
# Fresh saved-source native rendering, in-memory transforms only; no source or art save.
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};records=[]
def configure(frame,anchor):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  q=world_to_camera_view(sc,cam,Vector(v));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();step=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/step;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update();r=px((0,0,0))
 return {'frame':frame,'anchor':anchor,'actualRoot':list(r),'actualX':list(px((1,0,0))-r),'actualDepth':list(px((0,-1,0))-r),'actualHeight':list(px((0,0,1))-r),'matrix':[list(x) for x in cam.matrix_world],'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
def render(name):
 sc.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
for d,a in angles.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();r=configure((192,352),(96,248));render('hero-'+d+'.png');records.append({'kind':'hero','facing':d,'camera':r,'rootMatrix':[list(x) for x in root.matrix_world]})
with bpy.data.libraries.load(str(p/'resources/source/canonical-middle.blend'),link=False) as (fr,to):to.collections=['reef-middle']
mid=to.collections[0];sc.collection.children.link(mid);mr=next(o for o in mid.objects if o.type=='EMPTY');other=bpy.data.collections.new('independent outgoing canonical middle');sc.collection.children.link(other);mp={}
for o in mid.objects:
 n=o.copy();n.data=o.data.copy() if o.data else None;other.objects.link(n);mp[o]=n
for o,n in mp.items():
 if o.parent in mp:n.parent=mp[o.parent]
nr=mp[mr]
for d,a in angles.items():
 root.rotation_euler.z=a;mr.rotation_euler.z=a;mr.location=(-math.cos(a),-math.sin(a),0);nr.rotation_euler.z=a+math.pi/2;nr.location=(-math.sin(a),math.cos(a),0);bpy.context.view_layer.update();r=configure((448,608),(224,376));render('two-port-'+d+'.png');records.append({'kind':'two-port','facing':d,'camera':r,'cornerMatrix':[list(x) for x in root.matrix_world],'incomingMatrix':[list(x) for x in mr.matrix_world],'outgoingMatrix':[list(x) for x in nr.matrix_world]})
write('independent-native-replay.json',{'scope':'source replay/control only, no saved model alteration','records':records});print('INDEPENDENT_NATIVE_COMPLETE')
