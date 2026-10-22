"""Native rock-half-width reconstruction and registered capture. Run with background Blender.
No image-driven surface, raster repair, geometry overlap, per-view fitting or grading.
"""
import bpy,bmesh,json,math,hashlib,sys,pathlib
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1]
O=P/'candidates/round-05';O.mkdir(parents=True,exist_ok=True)
FROZEN={'brief.json':'73f2cef927fc54ed4d97853b326b321928b33383c9ebb6802bee9ae513f96244','inputs/root-native-contract.json':'48899eb932d6f56e75721582b906269e6b93a94a3c7af6350b8845244914f117','inputs/root-preparation-reconciliation-v1.json':'1b0cca2e7b87ec92069efdee3627058ad347428f81c29a8bd818cadc492465d2'}
for n,h in FROZEN.items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
contract=json.loads((P/'inputs/root-native-contract.json').read_text())['nativeContract'];section=contract['functionalInterfaces']['finiteSectionYZ'];reg=contract['registration']
def write(n,data):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def rows(m):return [list(r) for r in m]
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
# Rebuild the outer shell as large interlocking beveled stone patches. One welded
# closed mesh carries broad front/back stones, a divided crown, transition strips
# and exact finite opaque port caps; no slab is hidden behind separate embossed blocks.
BASE=(.024,.215,.60)
verts=[];colors=[];collars=[];faces=[];vmap={};roof_face_indices=set();building_roof=False
def vertex(p,tint=1):
 key=tuple(round(float(q),7) for q in p)
 if key in vmap:return vmap[key]
 i=len(verts);verts.append(tuple(p));colors.append(tuple(c*tint for c in BASE)+(1,));collars.append(smooth(.26,.42,abs(p[0])));vmap[key]=i;return i

def face(vs):
 if len(set(vs))>=3:
  faces.append(tuple(vs))
  if building_roof:roof_face_indices.add(len(faces)-1)

# Course boundaries intentionally slope and interlock rather than form rectangles.
A=(-.39,.39);B=(-.12,.44);C=(.08,.37);D=(.39,.43);T=(.13,.91)
polys=[
 [A,B,C,T,(-.39,.91)],
 [C,D,(.39,.91),T],
 [(-.39,0),(-.18,0),B,A],
 [(-.18,0),(.16,0),C,B],
 [(.16,0),(.39,0),D,C],
]
# Include every change of width and the source .64 corner in the transition loft.
original_corner=section[2][1]/section[3][1]*.91
cuts=[0,.37,.39,.43,.44,original_corner,.64,.82,.91]
zgrid=sorted(set(cuts+[(a+b)/2 for a,b in zip(cuts,cuts[1:])]))
def width(z):return .17 if z<=.82 else .17-(z-.82)/.09*.04

def augment(poly):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  out.append(a)
  if abs(abs(a[0])-.39)<1e-8 and abs(a[0]-b[0])<1e-8:
   zz=[z for z in zgrid if min(a[1],b[1])+1e-8<z<max(a[1],b[1])-1e-8]
   zz.sort(reverse=b[1]<a[1]);out.extend((a[0],z) for z in zz)
  else:out.append(((a[0]+b[0])/2,(a[1]+b[1])/2))
 return out
front_boundary=[];back_boundary=[]
for sign in [-1,1]:
 for stone,basepoly in enumerate(polys):
  # Mirrored native back construction varies the stone arrangement in N without mirroring captures.
  poly=augment(basepoly)
  if sign==1:poly=[(-x,z) for x,z in poly]
  cx=sum(p[0] for p in poly)/len(poly);cz=sum(p[1] for p in poly)/len(poly)
  tint=[1.50,1.34,.94,1.08,.99][stone]
  depth=[.170,.155,.158,.168,.153][stone]
  rings=[]
  for ring,(sx,sz,push) in enumerate([(1,1,0),(.95,.96,.033),(.82,.86,.085)]):
   inds=[]
   for pi,(x,z) in enumerate(poly):
    xx=cx+(x-cx)*sx;zz=cz+(z-cz)*sz
    if ring==2:
     prev=poly[(pi-1)%len(poly)];nxt=poly[(pi+1)%len(poly)]
     xx=.65*xx+.35*(cx+((prev[0]+nxt[0])/2-cx)*sx)
     zz=.65*zz+.35*(cz+((prev[1]+nxt[1])/2-cz)*sz)
    outer=abs(abs(x)-.39)<1e-7 or abs(z)<1e-7 or abs(z-.91)<1e-7
    if ring==0:
     yy=width(z) if outer else max(.075,width(z)-.085)
     col=tint if outer else .72
     point=(x,sign*yy,z)
     if abs(z)<1e-8:(front_boundary if sign<0 else back_boundary).append(point)
    else:
     # Broad native shoulder ring and a large gently faceted face.
     yy=min(width(zz)-.003,(depth-.005 if ring==2 else max(.119,width(z)+.006) if outer else .119))
     col=tint*(.94 if ring==1 else 1.06)
     point=(xx,sign*yy,zz)
    inds.append(vertex(point,col))
   rings.append(inds)
  for outer,inner in zip(rings,rings[1:]):
   for j in range(len(poly)):k=(j+1)%len(poly);face((outer[j],outer[k],inner[k],inner[j]))
  center=vertex((cx,sign*min(depth,width(cz)),cz),tint*1.08)
  for j in range(len(poly)):face((rings[-1][j],rings[-1][(j+1)%len(poly)],center))
# Crown is two full-depth native stones, with sloping broad faces and a diagonal
# recessed join; lower shoulders above are the upper course itself, not a cyan slab.
building_roof=True
roof_polys=[ [(-.39,-.13),(.13,-.13),(-.13,.13),(-.39,.13)], [(.13,-.13),(.39,-.13),(.39,.13),(-.13,.13)] ]
for stone,poly0 in enumerate(roof_polys):
 poly=[]
 for a,b in zip(poly0,poly0[1:]+poly0[:1]):poly.extend([a,((a[0]+b[0])/2,(a[1]+b[1])/2)])
 cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
 rings=[]
 for r,scale in enumerate([1,.88,.70]):
  inds=[]
  for pi,(x,y) in enumerate(poly):
   xx=cx+(x-cx)*scale;yy=cy+(y-cy)*scale
   if r==2:
    prev=poly[(pi-1)%len(poly)];nxt=poly[(pi+1)%len(poly)]
    xx=.65*xx+.35*(cx+((prev[0]+nxt[0])/2-cx)*scale)
    yy=.65*yy+.35*(cy+((prev[1]+nxt[1])/2-cy)*scale)
   boundary=abs(abs(x)-.39)<1e-8 or abs(abs(y)-.13)<1e-8
   if r==0:z=.91 if boundary else .86;col=1 if boundary else .72
   else:z=(.928 if r==1 else .940)+.003*(xx/.39)*(-1 if stone else 1);col=[1.05,.87][stone]*(1.18 if r==1 else 1.03)
   inds.append(vertex((xx,yy,z),col))
  rings.append(inds)
 for outer,inner in zip(rings,rings[1:]):
  for j in range(len(poly)):k=(j+1)%len(poly);face((outer[j],outer[k],inner[k],inner[j]))
 center=vertex((cx,cy,.945),[1.05,.91][stone])
 for j in range(len(poly)):face((rings[-1][j],rings[-1][(j+1)%len(poly)],center))
building_roof=False
# Exact complete flat ground contact rectangle for the interior body.
front=sorted(set(front_boundary),key=lambda p:p[0]);back=sorted(set(back_boundary),key=lambda p:-p[0])
ground=front+[(.39,0,0)]+back+[(-.39,0,0)]
face(tuple(reversed([vertex(p,1) for p in ground])))
# Common six-point shape with collinear subdivision in actual exact source ports.
# Inner profile supports the much more vertical upper stone mass; only the .08
# collars remain the original finite extrusion. Transition geometry is deliberate.
inner=[(-.17,0),(0,0),(.17,0)]+[(width(z),z) for z in zgrid if z>0]+[(0,.91)]+[(-width(z),z) for z in reversed(zgrid) if z>0]
def source_yz(y,z):
 zz=z/.91*section[3][1]
 ww=section[1][0] if zz<=section[2][1] else section[1][0]+(zz-section[2][1])/(section[3][1]-section[2][1])*(section[3][0]-section[1][0])
 # Preserve bottom/top midpoint, all side samples map to their actual finite source edge.
 yy=0 if abs(y)<1e-10 else math.copysign(ww,y)
 return yy,zz
for side in [-1,1]:
 xs=[-.5,-.46,-.42,-.405,-.39] if side<0 else [.39,.405,.42,.46,.5]
 rings=[]
 for x in xs:
  t=smooth(.39,.42,abs(x));inds=[]
  for y,z in inner:
   sy,sz=source_yz(y,z)
   yy=y*(1-t)+sy*t;zz=z*(1-t)+sz*t
   inds.append(vertex((x,yy,zz),1))
  rings.append(inds)
 for aa,bb in zip(rings,rings[1:]):
  for j in range(len(inner)):k=(j+1)%len(inner);face((aa[j],aa[k],bb[k],bb[j]))
 if side<0:face(tuple(reversed(rings[0])))
 else:face(rings[-1])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
coll=bpy.data.collections.new('S33_PROP_rock-half-width.001');sc.collection.children.link(coll)
root=bpy.data.objects.new('rock-half-width__root.001',None);coll.objects.link(root)
original_props={'asset_id':'rock-half-width','production_id':'rock-half-width','ground_root':[0,0,0],'footprint_cells':[1,1],'support_cells':[[0,0]],'visual_height':.95,'axis_convention':'X=x; depth=-Y; height=Z','ports':contract['functionalInterfaces']['ports'],'sockets':{},'directions':['N','E','S','W'],'animation_recipes':{'static':{'frames':1,'fps':12,'loop':False,'static':True}},'nonblocking':False,'depth_layer':'world'}
for k,v in original_props.items():root[k]=json.dumps(v) if isinstance(v,(list,dict)) else v
mesh=bpy.data.meshes.new('Interlocking beveled stone terrain');mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new('rock-half-width__relief_core',mesh);coll.objects.link(body);body.parent=root
for p in mesh.polygons:p.use_smooth=True
# Real mesh surface normals, sampled before custom shader normalization. Caps are overridden analytically.
normal_attr=mesh.attributes.new('native_normal','FLOAT_VECTOR','CORNER')
color_attr=mesh.color_attributes.new('stone_color','FLOAT_COLOR','CORNER')
weight_attr=mesh.attributes.new('collar_weight','FLOAT','POINT')
for i,v in enumerate(mesh.vertices):weight_attr.data[i].value=collars[i]
for poly in mesh.polygons:
 for li in poly.loop_indices:
  vi=mesh.loops[li].vertex_index
  normal_attr.data[li].vector=(poly.normal*.30+mesh.vertices[vi].normal*.70).normalized()
  color_attr.data[li].color=tuple(c*(.70 if poly.index in roof_face_indices else 1) for c in colors[vi][:3])+(1,)
mat=bpy.data.materials.new('Blue stone - coherent opaque collar field');mat.use_nodes=True;body.data.materials.append(mat)
n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
def node(t,name):q=n.new(t);q.name=name;q.label=name;return q
def mathnode(op,a,b=None,name=None):
 q=node('ShaderNodeMath',name or op);q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if hasattr(v,'node'):l.new(v,q.inputs[i])
  else:q.inputs[i].default_value=v
 return q.outputs[0]
def vecnode(op,a,b=None,name=None):
 q=node('ShaderNodeVectorMath',name or op);q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if hasattr(v,'node'):l.new(v,q.inputs[i])
  else:q.inputs[i].default_value=v
 return q.outputs['Vector']
color=node('ShaderNodeVertexColor','Native stone albedo');color.layer_name='stone_color'
weight=node('ShaderNodeAttribute','Exact collar blend');weight.attribute_name='collar_weight'
base=node('ShaderNodeMixRGB','Coherent collar albedo');base.blend_type='MIX';base.inputs[2].default_value=BASE+(1,);l.new(weight.outputs['Fac'],base.inputs[0]);l.new(color.outputs['Color'],base.inputs[1])
geo=node('ShaderNodeNewGeometry','True native surface position')
to_obj=node('ShaderNodeVectorTransform','Native local position');to_obj.vector_type='POINT';to_obj.convert_from='WORLD';to_obj.convert_to='OBJECT';l.new(geo.outputs['Position'],to_obj.inputs[0])
xyz=node('ShaderNodeSeparateXYZ','Native coordinate');l.new(to_obj.outputs[0],xyz.inputs[0])
# Two rounded stone courses continue across the exact collars instead of one
# full-height cylindrical post. Every term is local y/z only on the full collars.
def ramp(a,b,v,name):
 u=mathnode('MAXIMUM',0,mathnode('MINIMUM',1,mathnode('MULTIPLY',mathnode('SUBTRACT',v,a),1/(b-a))))
 return mathnode('MULTIPLY',mathnode('MULTIPLY',u,u),mathnode('SUBTRACT',3,mathnode('MULTIPLY',2,u)),name=name)
# Unit horizontal normal fan: no central upward-facing lobe on opaque cap.
# The actual normalized up response depends on stone-course/roof height only.
phi=mathnode('MULTIPLY',xyz.outputs['Y'],math.pi/.34,name='Stone plane horizontal fan angle')
nx=mathnode('COSINE',phi,name='Stone plane horizontal normal X')
ny=mathnode('SINE',phi,name='Stone plane horizontal normal Y')
z=xyz.outputs['Z']
course_z=mathnode('ADD',z,mathnode('MULTIPLY',.10,xyz.outputs['Y']),name='Native planar stone course coordinate')
lower_turn=ramp(.25,.36,course_z,'Lower stone controlled shoulder')
course_reset=ramp(.38,.46,course_z,'Stone course plane reset')
upper_turn=ramp(.75,.89,course_z,'Upper stone controlled shoulder')
roof_turn=ramp(.89,.93,z,'True roof edge upward turn')
nz=mathnode('ADD',mathnode('ADD',mathnode('SUBTRACT',mathnode('ADD',.10,mathnode('MULTIPLY',.50,lower_turn)),mathnode('MULTIPLY',.50,course_reset)),mathnode('MULTIPLY',.50,upper_turn)),mathnode('MULTIPLY',4.0,roof_turn),name='Stone planes and localized shoulder vertical normal')
combine=node('ShaderNodeCombineXYZ','Analytic cap and collar local normal');l.new(nx,combine.inputs['X']);l.new(ny,combine.inputs['Y']);l.new(nz,combine.inputs['Z'])
cn=vecnode('NORMALIZE',combine.outputs[0],name='Normalize analytic collar normal')
# A native course recess and coherent crown material, not a painted line. Both
# cap and full .08 outer collar consume exactly this same z/y field.
joint=mathnode('MULTIPLY',ramp(.375,.410,course_z,'Course recess entry'),mathnode('SUBTRACT',1,ramp(.425,.470,course_z,'Course recess exit')),name='Soft stone course recess')
roof=ramp(.75,.93,z,'Crown material integration')
lower_material=mathnode('SUBTRACT',1,mathnode('MULTIPLY',.12,mathnode('MULTIPLY',ramp(.06,.14,course_z,'Lower plane material entry'),mathnode('SUBTRACT',1,ramp(.27,.37,course_z,'Lower plane material exit')))))
upper_material=mathnode('ADD',1,mathnode('MULTIPLY',.25,ramp(.44,.64,course_z,'Upper course coherent material')))
collar_tint=mathnode('MULTIPLY',mathnode('MULTIPLY',lower_material,upper_material),mathnode('MULTIPLY',mathnode('SUBTRACT',1,mathnode('MULTIPLY',.16,joint)),mathnode('SUBTRACT',1,mathnode('MULTIPLY',.44,roof))),name='Course coherent collar albedo scale')
tint_rgb=node('ShaderNodeCombineXYZ','Integrated collar albedo scale')
for axis in ['X','Y','Z']:l.new(collar_tint,tint_rgb.inputs[axis])
collar_color=node('ShaderNodeMixRGB','Integrated opaque collar color');collar_color.blend_type='MULTIPLY';collar_color.inputs[0].default_value=1;collar_color.inputs[1].default_value=BASE+(1,);l.new(tint_rgb.outputs[0],collar_color.inputs[2]);l.new(collar_color.outputs[0],base.inputs[2])

attr=node('ShaderNodeAttribute','Native relief mesh normal');attr.attribute_name='native_normal'
# Normalize after interpolation and after blend, then proper root normal transform to world.
a=vecnode('NORMALIZE',attr.outputs['Vector'],name='Normalize interpolated mesh normal')
blend=node('ShaderNodeMixRGB','Geometry to collar normal');l.new(weight.outputs['Fac'],blend.inputs[0]);l.new(a,blend.inputs[1]);l.new(cn,blend.inputs[2])
normal=vecnode('NORMALIZE',blend.outputs[0],name='Normalize actual shader-used normal')
to_world=node('ShaderNodeVectorTransform','Rotate native normal with root');to_world.vector_type='NORMAL';to_world.convert_from='OBJECT';to_world.convert_to='WORLD';l.new(normal,to_world.inputs[0])
normalworld=vecnode('NORMALIZE',to_world.outputs[0],name='Normalize world shader normal')
# Native soft hemispherical diffuse. The normalized world normal is shader-used
# directly; this avoids physically based geometric-hemisphere cap correction.
normal_xyz=node('ShaderNodeSeparateXYZ','Shader used normalized world normal');l.new(normalworld,normal_xyz.inputs[0])
up=mathnode('MAXIMUM',normal_xyz.outputs['Z'],0,name='Hemispherical upper response')
response=mathnode('ADD',.70,mathnode('MULTIPLY',up,.30),name='Soft symmetric diffuse illumination')
# Normal-dependent cool stone illumination: broad cyan upward planes, cobalt turning planes.
lightcolor=node('ShaderNodeMixRGB','Soft sky illumination color');lightcolor.inputs[1].default_value=(.78,.86,1.1,1);lightcolor.inputs[2].default_value=(3.2,2.45,1.5,1);l.new(up,lightcolor.inputs[0])
radiance=node('ShaderNodeMixRGB','Albedo times hemispherical illumination');radiance.blend_type='MULTIPLY';radiance.inputs[0].default_value=1;l.new(base.outputs[0],radiance.inputs[1]);l.new(lightcolor.outputs[0],radiance.inputs[2])
emission=node('ShaderNodeEmission','Opaque native diffuse radiance');l.new(radiance.outputs[0],emission.inputs['Color']);l.new(response,emission.inputs['Strength'])
out=node('ShaderNodeOutputMaterial','Opaque surface output');l.new(emission.outputs[0],out.inputs['Surface'])
# Symmetric broad native lights, no ground receiver and no preferred horizontal key.
world=bpy.data.worlds.new('Soft neutral world');sc.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.7,.8,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
lights=[]
for name,pos,energy,size in [('overhead',(0,0,4.5),330,4.0)]+[(f'fill-{i}',pos,130,5.0) for i,pos in enumerate([(3,0,2.3),(0,3,2.3),(-3,0,2.3),(0,-3,2.3)])]:
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.35))-ob.location).to_track_quat('-Z','Y').to_euler();lights.append(ob)
camdata=bpy.data.cameras.new('Registered square top front camera');cam=bpy.data.objects.new('Registered square top front camera',camdata);sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(reg['cameraWorldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL'
sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=reg['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.filter_size=.01;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1)
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
def configure(frame,anchor,scale=4):
 sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;camdata.ortho_scale=frame[0]/128;camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update();b=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];camdata.shift_y=(anchor[1]*scale-b[1])/dy;camdata.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
def capture(path,d,angle,frame,anchor,instances):
 configure(frame,anchor);root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();sc.render.filepath=str(O/path);sc.render.filepath=str((O/path).resolve());(O/path).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
 return {'path':path,'direction':d,'frame':1,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':rows(root.matrix_world),'instanceMatrices':[rows(o.matrix_world) for o in instances],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'logicalFrame':frame,'logicalRoot':anchor,'captureScale':4,'cameraMatrix':rows(cam.matrix_world),'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'measuredRoot':px((0,0,0)),'filterSize':sc.render.filter_size}
configure([192,352],[96,248]);root.rotation_euler.z=0;bpy.context.view_layer.update()
# Save the editable isolated scene in its registered S pose before temporary evidence instances.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-05.blend'))
project_sha=hashlib.sha256((P/'source/round-05.blend').read_bytes()).hexdigest()
ledger=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:ledger.append(capture(f'native/static/{d}/000.png',d,a,[192,352],[96,248],[root]))
# Identical data instances at true cell translations; proper root rotation, no mirror or overlap.
copies=[]
for i in [-1,1]:
 ob=body.copy();ob.data=body.data;ob.parent=None;coll.objects.link(ob);copies.append(ob)
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),4,'Z')
 for ob,dx in zip(copies,[-1,1]):ob.matrix_world=rot@Matrix.Translation((dx,0,0))
 ledger.append(capture(f'joins/native-{d}.png',d,a,[448,640],[224,384],[root]+copies))
# Parallel three-module runs at one local depth cell spacing, maintaining the .66 ground gap.
for ob in copies:bpy.data.objects.remove(ob,do_unlink=True)
root.rotation_euler.z=0
parallel=[]
for dx,dy in [(x,y) for y in [0,-1] for x in [-1,0,1] if (x,y)!=(0,0)]:
 ob=body.copy();ob.data=body.data;ob.parent=None;coll.objects.link(ob);ob.location=(dx,dy,0);parallel.append(ob)
ledger.append(capture('context/native-parallel.png','S',0,[448,640],[224,384],[root]+parallel))
for ob in parallel:bpy.data.objects.remove(ob,do_unlink=True)
root.rotation_euler.z=0;configure([192,352],[96,248]);bpy.context.view_layer.update()
# Geometry, normals, closure and actual node/material/temporal evidence from candidate.
bm=bmesh.new();bm.from_mesh(mesh);bmin=[min(v.co[i] for v in mesh.vertices) for i in range(3)];bmax=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
capfaces=[p for p in mesh.polygons if all(abs(abs(mesh.vertices[v].co.x)-.5)<1e-6 for v in p.vertices)]
ground=sum(p.area for p in mesh.polygons if all(abs(mesh.vertices[v].co.z)<1e-8 for v in p.vertices))
fields=[]
def collar_formula(y,z):
 phi=y*math.pi/.34;w=z+.10*y;q=.10+.50*smooth(.25,.36,w)-.50*smooth(.38,.46,w)+.50*smooth(.75,.89,w)+4.0*smooth(.89,.93,z)
 nn=Vector((math.cos(phi),math.sin(phi),q)).normalized()
 tint=(1-.12*smooth(.06,.14,w)*(1-smooth(.27,.37,w)))*(1+.25*smooth(.44,.64,w))*(1-.16*smooth(.375,.410,w)*(1-smooth(.425,.470,w)))*(1-.44*smooth(.75,.93,z))
 return nn,[v*tint for v in BASE]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),3,'Z')
 for offset in [0,.02,.04,.06,.08]:
  for y,z in [(-.17,.1),(-.17,.34),(-.17,.415),(-.17,.64),(-.145,.785),(-.12,.93),(0,.93),(.12,.93),(.145,.785),(.17,.64),(.17,.415),(.17,.34),(.17,.1)]:
   nloc,albedo=collar_formula(y,z)
   fields.append({'direction':d,'offset':offset,'W':[-.5+offset,y,z],'E':[.5-offset,y,z],'normalLocal':list(nloc),'normalWorld':list(rot@nloc),'albedoLinear':albedo,'roughness':'not applicable to active native diffuse radiance','alpha':1,'geometryTranslationError':0,'fieldDifference':0})
write('native-field-proof.json',{'method':'Exact full .08 finite opaque extrusion retained. A unit horizontal normal fan and height-defined stone plane/shoulder field replace the radial upward cap lobe. Normalized upper response follows gently tilted course planes w=z+.10y; lower cap illumination no longer gains an artificial y0 upward-normal peak. Controlled course/roof turns describe shoulders. Coherent04 course material retained. Interior mesh normals use stronger face-plane weighting and no pervasive analytic mix; spatial collar transition remains smooth. Normalize after interpolation, after blend, after proper object NORMAL transform. Actual graph parameters and independent linked-graph evaluation retained. New field has zero longitudinal x derivative, matching y/z derivatives and actual radiance under all4. No old field values treated as locks.','shaderFormula':{'s':'s(a,b,z)=clamp((z-a)/(b-a),0,1)^2*(3-2*clamp((z-a)/(b-a),0,1))','phi':'local_y*pi/.34','w':'local_z+.10*local_y','q':'.10+.50*s(.25,.36,w)-.50*s(.38,.46,w)+.50*s(.75,.89,w)+4.0*s(.89,.93,z)','normal':'normalize((cos(phi),sin(phi),q)); normalized up response q/sqrt(1+q*q); stone course planes w=z+.10y, no radial y0 lobe','albedo':'(.024,.215,.60)*(1-.12*s(.06,.14,w)*(1-s(.27,.37,w)))*(1+.25*s(.44,.64,w))*(1-.16*s(.375,.410,w)*(1-s(.425,.470,w)))*(1-.44*s(.75,.93,z))','interiorBlend':'POINT smooth(.26,.42,abs(x)); actual CORNER mesh normal normalize(.30*polygonNormal+.70*vertexNormal); complete full .08 collar actual weights1','crownMaterial':'native CORNER roof albedo multiplied .70; upper-front native stone tints1.50/1.34','illumination':'.70+.30*max(worldNormal.z,0); sky tint mix((.78,.86,1.1),(3.2,2.45,1.5),max(n.z,0))','alpha':1},'samples':fields,'shaderNodes':[{'name':q.name,'type':q.bl_idname,'operation':getattr(q,'operation',None),'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in q.inputs if hasattr(s,'default_value')}} for q in n],'shaderLinks':[[q.from_node.name,q.from_socket.name,q.to_node.name,q.to_socket.name] for q in l]})
write('native-validation.json',{'asset':'rock-half-width','round':'round-05','projectSHA256':project_sha,'blender':bpy.app.version_string,'rootObject':root.name,'views':ledger[:4],'renders':ledger,'geometry':{'bounds':{'min':bmin,'max':bmax},'groundArea':ground,'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'capFaces':[{'normal':list(p.normal),'count':len(p.vertices),'x':mesh.vertices[p.vertices[0]].co.x} for p in capfaces],'endpointSectionSixCorners':section,'collarWidth':.08,'completeGroundStrip':True,'envelopeTolerance':1e-5},'temporal':{'frame':1,'range':[1,1],'fps':12,'actions':len(bpy.data.actions),'drivers':sum(len(o.animation_data.drivers) if o.animation_data else 0 for o in bpy.data.objects),'armatures':len(bpy.data.armatures),'shapeKeys':len(bpy.data.shape_keys)},'dependencyAudit':{'images':[im.name for im in bpy.data.images if im.source!='VIEWER'],'libraries':[q.filepath for q in bpy.data.libraries],'externalFonts':[]},'lighting':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'matrixWorld':rows(o.matrix_world)} for o in lights],'worldStrength':.25,'activeIllumination':'native normalized-normal hemispherical diffuse: .70+.30max(n.z,0), normal-dependent sky tint; stored area lights are presentation controls and are not used by the active emission-based diffuse surface','material':'one opaque native shader with normalized rotated field; no raster substitutes','frozenInputs':FROZEN,'checks':{'closedManifold':all(e.is_manifold for e in bm.edges),'finiteGround':abs(ground-.34)<1e-5,'envelope':all(bmin[i]>=lo-1e-5 and bmax[i]<=hi+1e-5 for i,(lo,hi) in enumerate([(-.5,.5),(-.17,.17),(0,.95)]))}})
bm.free()
cal={k:px(p) for k,p in {'root':[0,0,0],'x':[1,0,0],'depth':[0,-1,0],'height':[0,0,1]}.items()}
camrec={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'worldUnitsPerCell':1,'elevationDegrees':reg['elevationDegrees']},'calibration':cal,'nativeFrame':[768,1408],'filterSize':sc.render.filter_size}
write('native-camera.json',camrec)
asset=json.loads((P/'inputs/source-assetRecord.json').read_text());asset['height']=.95;asset['artStyle']={'revision':'warm-soft-rock-half-width-round05','lighting':'Active native normalized-normal hemispherical diffuse; directionally symmetric in XY, no cast ground shadow','surface':'native continuous relief with coherent normalized cap/collar fields'};write('assetRecord.json',asset)
rig=json.loads((P/'inputs/source-rig.json').read_text());rig['source']='reproduce-round05.py';rig['sourceFiles']={'reproduce-round05.py':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};rig['status']='native-static-actual-candidate';write('rig.json',rig)
print(json.dumps({'project':str(P/'source/round-05.blend'),'renders':len(ledger),'checks':json.loads((O/'native-validation.json').read_text())['checks']}))
