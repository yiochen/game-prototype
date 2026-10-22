"""Private native corner. Background Blender only. -- preview | capture | assemblies.
The frozen canonical .blend supplies actual body/cap shaders, rig and compositor.
"""
import bpy,sys,math,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.geometry import delaunay_2d_cdt
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'preview'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE/'dependencies/canonical-middle.blend'))
s=bpy.context.scene;cam=s.camera
canon=bpy.data.objects['rock-shelf-middle__sculpted_core'];cm=canon.data
body=cm.materials[0];capW=cm.materials[1];capN=capW.copy();capN.name='corner N canonical cutstone transverse -localX'
ns=capN.node_tree.nodes;ls=capN.node_tree.links;sep=next(n for n in ns if n.type=='SEPXYZ');neg=ns.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-1;ls.new(sep.outputs['X'],neg.inputs[0])
for link in list(ls):
 if link.from_node==sep and link.from_socket.name=='Y':dest=link.to_socket;ls.remove(link);ls.new(neg.outputs[0],dest)
# Capture exact endpoint band fields before deleting canonical geometry.
a=cm.color_attributes['rock_shelf_albedo'];fields={}
for side,x in [('W',-.5),('E',.5)]:
 fields[side]={}
 for p in cm.polygons:
  if p.material_index or not all(abs(cm.vertices[i].co.x)>.4399 for i in p.vertices):continue
  if not any(abs(cm.vertices[i].co.x-x)<1e-5 for i in p.vertices):continue
  kind='bottom' if p.normal.z<-.9 else 'top' if p.normal.z>.9 else 'body'
  for li in p.loop_indices:
   v=cm.vertices[cm.loops[li].vertex_index]
   if abs(v.co.x-x)<1e-5:fields[side][(round(v.co.y,5),round(v.co.z,5),kind)]=(tuple(cm.corner_normals[li].vector),tuple(a.data[v.index].color))
# Preserve actual canonical longitudinal variation through new .025 collars.
# Sample the frozen source's real triangles and decoded loop fields, before removal.
cm.calc_loop_triangles()
canonical_triangles=[]
for tri in cm.loop_triangles:
 pp=cm.polygons[tri.polygon_index]
 if pp.material_index:continue
 ps=[cm.vertices[i].co.copy() for i in tri.vertices]
 if not (all(p.x<-.4399 for p in ps) or all(p.x>.4399 for p in ps)):continue
 kind='bottom' if pp.normal.z<-.9 else 'top' if pp.normal.z>.9 else 'body'
 canonical_triangles.append((kind,ps,[cm.corner_normals[li].vector.copy() for li in tri.loops],[tuple(a.data[i].color) for i in tri.vertices]))
def canonical_field(x,y,z,kind):
 p=Vector((x,y,z))
 for kk,ps,nn,cc in canonical_triangles:
  if kk!=kind:continue
  a,b,c=ps;n=(b-a).cross(c-a)
  if n.length<1e-10 or abs((p-a).dot(n.normalized()))>1e-6:continue
  u0=b-a;u1=c-a;u2=p-a;d00=u0.dot(u0);d01=u0.dot(u1);d11=u1.dot(u1);d20=u2.dot(u0);d21=u2.dot(u1);den=d00*d11-d01*d01
  v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;u=1-v-w
  if min(u,v,w)<-1e-5:continue
  weights=[u,v,w];normal=sum((nn[j]*weights[j] for j in range(3)),Vector());color=tuple(sum(weights[j]*cc[j][k] for j in range(3)) for k in range(4))
  return tuple(normal),color
 raise ValueError(('canonical field missing',x,y,z,kind))
for ob in list(s.objects):
 if ob.type not in ['CAMERA','LIGHT']:bpy.data.objects.remove(ob,do_unlink=True)
for c in list(bpy.data.collections):
 if not c.objects and not c.children:bpy.data.collections.remove(c)
coll=bpy.data.collections.new('rock-shelf-corner private rounded native turn');s.collection.children.link(coll)
root=bpy.data.objects.new('rock-shelf-corner__root',None);coll.objects.link(root);root['asset']='rock-shelf-corner';root['ports']='W X=-.5; N Y=.5';root['clip']='static';root['frames']=1;root['fps']=12;root['loop']=False
s.name='rock-shelf-corner native round-01';s['asset']='rock-shelf-corner'
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def taper(x,y):return smooth(-.475,-.36,x)*(1-smooth(.36,.475,y))
seeds=[(-.27,.20),(.17,.23),(-.28,-.20),(.14,-.13)]
palette=[(.075,.34,.56),(.065,.40,.65),(.105,.43,.65),(.055,.335,.57)]
def cell(x,y):
 xx=x+.025*math.sin(8*y);yy=y+.022*math.sin(7*x+2*y)
 ds=[(xx-a)**2+(yy-b)**2 for a,b in seeds];i=min(range(4),key=lambda k:ds[k]);a,b=seeds[i]
 d=min((ds[j]-ds[i])/(2*math.hypot(c-a,e-b)) for j,(c,e) in enumerate(seeds) if j!=i)
 return i,max(0,d),math.hypot(xx-a,yy-b)
# Paired finite ground and crown boundary, from W lower side around outer SE to N,
# then the rebuilt inner turn back to W. No inherited overlapping .08 bands.
ground=[(-.475,-.45),(-.25,-.45),(.318198025226593,-.318198025226593),(.45,.25),(.45,.475),(-.45,.475),(-.45,.45),(-.475,.45)]
top=[(-.475,-.39),(-.25,-.39),(.268,-.268),(.39,.25),(.39,.475),(-.39,.475),(-.415,.415),(-.475,.39)]
# Densify non-port boundary with one-to-one correspondence.
gp=[];tp=[]
for i in range(8):
 j=(i+1)%8;dist=math.dist(ground[i],ground[j]);steps=1 if i in [4,7] else max(1,math.ceil(dist/.012))
 for k in range(steps):
  t=k/steps;gp.append(tuple((1-t)*ground[i][a]+t*ground[j][a] for a in range(2)));tp.append(tuple((1-t)*top[i][a]+t*top[j][a] for a in range(2)))
M=len(gp)
def segdist(x,y,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)));return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
def boundarydist(x,y):return min(segdist(x,y,tp[i],tp[(i+1)%M]) for i in range(M))
def crown(x,y):
 i,d,r=cell(x,y);w=taper(x,y)*smooth(0,.045,boundarydist(x,y));z=.33+.110*smooth(.001,.095,d)+.007*math.exp(-(r/.18)**2)
 return .43*(1-w)+min(.449,z)*w
verts=[];cols=[];faces=[];kinds=[];special=[];lookup={}
def color(x,y,z,kind):
 h=max(0,min(1,z/.43));base=(.105+.025*h,.285+.15*h,.52+.14*h)
 if kind=='top':
  i,d,r=cell(x,y);w=taper(x,y)*smooth(0,.045,boundarydist(x,y));lift=.54+.46*smooth(.001,.055,d);return (*[(1-w)*b+w*palette[i][k]*lift for k,b in enumerate((.08,.39,.63))],1)
 if z<=.28:
  along=x-y;centers=[-.38,.04,.48];d=[(along-c)**2 for c in centers];ii=min(range(3),key=lambda k:d[k]);dd=min((d[j]-d[ii])/(2*abs(centers[j]-centers[ii])) for j in range(3) if j!=ii)
  pal=[(.095,.235,.43),(.085,.34,.57),(.145,.30,.49)][ii];lift=.64+.36*smooth(.002,.045,max(0,dd));w=taper(x,y)*smooth(0,.025,z)*(1-smooth(.25,.28,z));base=tuple((1-w)*base[k]+w*pal[k]*lift for k in range(3))
 return (*base,1)
def V(p,kind='body'):
 key=tuple(round(x,7) for x in p)
 if key in lookup:return lookup[key]
 idx=len(verts);lookup[key]=idx;verts.append(tuple(p));cols.append(color(*p,kind));return idx
def F(v,kind='body',custom=None,material=0):
 faces.append(v);kinds.append(kind);special.append(({vi:n for vi,n in zip(v,custom)} if custom else None,material))
# Main finite side rings. Four physical heights carry a broad lower stone course.
rings=[]
for level,z in enumerate([0,.14,.28,.43]):
 ring=[]
 for j,(g,t) in enumerate(zip(gp,tp)):
  if z==.43:p=(*t,z)
  else:
   x,y=g;prev=gp[(j-1)%M];nxt=gp[(j+1)%M];out=Vector((nxt[1]-prev[1],prev[0]-nxt[0]));out.normalize();w=taper(x,y)
   # Subtle physical lower course, smoothly zero at ground and shoulder.
   rel=.028*w*(1 if z==.14 else 0)*(.35+.65*math.sin((x-y)*8+.4)**8);p=(x-out.x*rel,y-out.y*rel,z)
  ring.append(V(p,'top' if z==.43 else 'body'))
 rings.append(ring)
for lev in range(3):
 for j in range(M):
  k=(j+1)%M
  # Port-boundary strips are filled by exact native collars below.
  if all(abs(tp[q][0]+.475)<1e-6 for q in [j,k]) or all(abs(tp[q][1]-.475)<1e-6 for q in [j,k]):continue
  F([rings[lev][j],rings[lev][k],rings[lev+1][k],rings[lev+1][j]])
# Main crown: constrained native triangulation, no target image or textures.
coords=[Vector(p) for p in tp]
for i in range(78):
 for j in range(78):
  x=-.466+i*.012;y=-.382+j*.011
  # Interior point by winding ray.
  inside=False
  for a,b in zip(tp,tp[1:]+tp[:1]):
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
  if inside and boundarydist(x,y)>.002:coords.append(Vector((x,y)))
res=delaunay_2d_cdt(coords,[(i,(i+1)%M) for i in range(M)],[list(range(M))],1,1e-8)
vv,ee,ff=res[:3];topids=[]
for p,original_ids in zip(vv,res[3]):
 boundary=next((i for i in original_ids if i<M),None)
 topids.append(rings[3][boundary] if boundary is not None else V((p.x,p.y,crown(p.x,p.y)),'top'))
for f in ff:
 if len(f)>=3:F([topids[i] for i in f],'top')
F(list(reversed(rings[0])),'bottom')
# Exact .025 collars with real canonical per-corner endpoint normal/albedo field.
profile=[(-.45,0),(.45,0),(.45,.14),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28),(-.45,.14)]
def field(side,y,z,kind,x=None):
 return canonical_field((-.5 if side=='W' else .5) if x is None else x,y,z,kind)
for port in ['W','N']:
 side='W' if port=='W' else 'E'
 def transform(p):return tuple(p) if port=='W' else (-p[1],p[0],p[2])
 def rotate(n):return tuple(n) if port=='W' else (-n[1],n[0],n[2])
 cap6=[]
 for y,z in [(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]:cap6.append(V(transform((-.5 if port=='W' else .5,y,z)),'top' if z==.43 else 'body'))
 F(list(reversed(cap6)) if port=='W' else cap6,'cap',material=1 if port=='W' else 2)
 for kind,ps,nn,cc in canonical_triangles:
  if (sum(p.x for p in ps)<0)!=(port=='W'):continue
  poly=[(ps[i],nn[i],cc[i]) for i in range(3)];clipped=[];plane=-.475 if port=='W' else .475
  for i,a in enumerate(poly):
   b=poly[(i+1)%len(poly)];ina=a[0].x<=plane+1e-8 if port=='W' else a[0].x>=plane-1e-8;inb=b[0].x<=plane+1e-8 if port=='W' else b[0].x>=plane-1e-8
   if ina:clipped.append(a)
   if ina!=inb:
    t=(plane-a[0].x)/(b[0].x-a[0].x);pos=a[0].lerp(b[0],t);pos.x=plane;normal=a[1].lerp(b[1],t);interpolated_color=tuple((1-t)*a[2][k]+t*b[2][k] for k in range(4));clipped.append((pos,normal,interpolated_color))
  if len(clipped)<3:continue
  ids=[];norms=[]
  for p,n,c in clipped:
   idx=V(transform(p),kind);cols[idx]=c;ids.append(idx);norms.append(rotate(n))
  F(ids,kind,norms)
# Split common interface edges at the union of native triangle-cut and main-turn
# boundary vertices. This retains original affine field triangles and makes the
# resulting solid manifold, with no duplicate/intersecting collar skins.
interface=[i for i,p in enumerate(verts) if abs(p[0]+.475)<1e-6 or abs(p[1]-.475)<1e-6]
for fi,f in enumerate(faces):
 specified,material=special[fi];new=[]
 for j,a in enumerate(f):
  b=f[(j+1)%len(f)];new.append(a);pa=Vector(verts[a]);pb=Vector(verts[b]);edge=pb-pa
  sameW=abs(pa.x+.475)<1e-6 and abs(pb.x+.475)<1e-6;sameN=abs(pa.y-.475)<1e-6 and abs(pb.y-.475)<1e-6
  if not (sameW or sameN) or edge.length<1e-8:continue
  additions=[]
  for idx in interface:
   if idx in [a,b]:continue
   pt=Vector(verts[idx]);t=(pt-pa).dot(edge)/edge.length_squared
   if 1e-6<t<1-1e-6 and (pt-pa-edge*t).length<1e-6:additions.append((t,idx))
  for t,idx in sorted(additions):
   new.append(idx)
   if specified:specified[idx]=tuple((1-t)*specified[a][k]+t*specified[b][k] for k in range(3))
 faces[fi]=new

mesh=bpy.data.meshes.new('corner clean turn with finite support and disjoint .025 collars');mesh.from_pydata(verts,[],faces);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free();mesh.update()
ob=bpy.data.objects.new('rock-shelf-corner__continuous_rounded_turn',mesh);coll.objects.link(ob);ob.parent=root
# Preserve original affine canonical vectors until after interpolation. Native
# custom-normal storage normalizes new clipped vertices too early; this equivalent
# shader path avoids that change while the geometric codec remains measured.
bodyExact=body.copy();bodyExact.name='corner canonical collars affine native normal field'
bn=bodyExact.node_tree.nodes;bl=bodyExact.node_tree.links;bs=next(n for n in bn if n.type=='BSDF_PRINCIPLED');normalAttr=bn.new('ShaderNodeAttribute');normalAttr.attribute_name='canonical_collar_normal';transformNormal=bn.new('ShaderNodeVectorTransform');transformNormal.vector_type='VECTOR';transformNormal.convert_from='OBJECT';transformNormal.convert_to='WORLD';bl.new(normalAttr.outputs['Vector'],transformNormal.inputs['Vector']);normalize=bn.new('ShaderNodeVectorMath');normalize.operation='NORMALIZE';bl.new(transformNormal.outputs['Vector'],normalize.inputs[0]);bl.new(normalize.outputs['Vector'],bs.inputs['Normal'])
for mat in [body,capW,capN,bodyExact]:mesh.materials.append(mat)
affine=mesh.attributes.new(name='canonical_collar_normal',type='FLOAT_VECTOR',domain='CORNER')
for p,(specified,material) in zip(mesh.polygons,special):
 if specified:
  for li in p.loop_indices:affine.data[li].vector=specified[mesh.loops[li].vertex_index]

attr=mesh.color_attributes.new(name='rock_shelf_albedo',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(cols):attr.data[i].color=c
# Smooth normals: real relief in interior; exact frozen collar loops override.
acc=[Vector((0,0,0)) for v in verts]
for p,kind in zip(mesh.polygons,kinds):
 if kind in ['body','top']:
  for vi in p.vertices:acc[vi]+=p.normal*p.area
custom=[]
for p,kind,(specific,material) in zip(mesh.polygons,kinds,special):
 p.material_index=3 if specific else material;p.use_smooth=kind not in ['cap','bottom']
 for k,vi in enumerate(p.vertices):
  x,y,z=verts[vi]
  if specific:n=Vector(specific[vi])
  elif kind in ['cap','bottom']:n=p.normal
  elif kind=='top':
   e=.0001;dx=(crown(x+e,y)-crown(x-e,y))/(2*e);dy=(crown(x,y+e)-crown(x,y-e))/(2*e);n=Vector((-dx,-dy,1))
   wW=1-smooth(-.475,-.40,x);wN=smooth(.40,.475,y)
   if wW:n=n.lerp(Vector((0,(.35/.94)*y/.39,1)),wW)
   if wN:n=n.lerp(Vector(((.35/.94)*x/.39,0,1)),wN)
   if abs(x+.475)<1e-6:n=Vector(field('W',y,z,'top',-.475)[0])
   elif abs(y-.475)<1e-6:
    n0=field('E',-x,z,'top',.475)[0];n=Vector((-n0[1],n0[0],n0[2]))
  else:
   if abs(x+.475)<1e-6:
    n=Vector(field('W',y,z,'body',-.475)[0])
   elif abs(y-.475)<1e-6:
    n0=field('E',-x,z,'body',.475)[0];n=Vector((-n0[1],n0[0],n0[2]))
   else:n=acc[vi].normalized() if acc[vi].length else p.normal
  custom.append(tuple(n.normalized()))
mesh.normals_split_custom_set(custom)
# Native authored vectors before custom-normal codec, bound alongside actual source.
authored=[]
for p,(specified,material) in zip(mesh.polygons,special):
 if specified:
  authored.append({'polygon':p.index,'material':material,'corners':[{'loop':li,'vertex':mesh.loops[li].vertex_index,'position':list(mesh.vertices[mesh.loops[li].vertex_index].co),'inputNormal':list(specified[mesh.loops[li].vertex_index]),'shaderAttributeVector':list(affine.data[li].vector),'encodedNormal':list(mesh.corner_normals[li].vector)} for li in p.loop_indices]})
dump(OUT/'authored-collar-normal-fields.json',{'method':'Actual frozen canonical band triangle field carried through each new .025 collar; input vectors retained before native codec normalization/encoding. N vectors rotated Rz90.','faces':authored})
# Two small embedded native accents, intentionally away from ports.
def pebble(name,x,y,rx,ry,h,c):
 z=crown(x,y)-.006;bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(x,y,z));o=bpy.context.object;o.name=name
 for cc in list(o.users_collection):cc.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.scale=(rx,ry,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for v in o.data.vertices:v.co.z=min(v.co.z,.449-z)
 for p in o.data.polygons:p.use_smooth=True
 mat=bpy.data.materials.new(name+' private blue lavender');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=.37;bs.inputs['Specular IOR Level'].default_value=.24;o.data.materials.append(mat)
pebble('rock-shelf-corner__embedded_pearl_A',.22,-.02,.045,.037,.028,(.14,.29,.52))
pebble('rock-shelf-corner__embedded_pearl_B',-.10,.29,.033,.027,.022,(.09,.34,.48))
# Remove orphan data from canonical source; private final source owns only used art and rig.
for datablocks in [bpy.data.meshes,bpy.data.materials,bpy.data.texts]:
 for d in list(datablocks):
  if d.users==0:datablocks.remove(d)
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
t=bpy.data.texts.new('build-round-01.py');t.write(Path(__file__).read_text())
def camera(frame=(192,352),anchor=(96,248),scale=4):
 s.render.resolution_x=frame[0]*scale;s.render.resolution_y=frame[1]*scale;s.render.resolution_percentage=100;s.render.pixel_aspect_x=math.sqrt(1+.7*.7);s.render.pixel_aspect_y=1;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update();origin=px((0,0,0))
 return {'frame':list(frame),'anchor':list(anchor),'captureScale':scale,'nativeFrame':[s.render.resolution_x,s.render.resolution_y],'nativeRoot':list(origin),'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'fps':12,'camera':{'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world]},'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'filterSize':s.render.filter_size}
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
record=camera();root.rotation_euler.z=0;bpy.context.view_layer.update()
if MODE=='preview':
 s.render.filepath=str(OUT/'working-S.png');bpy.ops.render.render(write_still=True)
else:
 bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'round-01.blend'),compress=True)
 ledger={'asset':'rock-shelf-corner','round':'round-01','sourceSHA256':sha(BASE/'round-01.blend'),'views':{}}
 for d,a in angles.items():
  root.rotation_euler.z=a;bpy.context.view_layer.update();rec=camera();rec.update(direction=d,clip='static',index=0,rootRotationZ=float(root.rotation_euler.z),rootMatrix=[list(r) for r in root.matrix_world]);ledger['views'][d]=rec
  path=OUT/f'native/static/{d}/000.png';path.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 dump(OUT/'pose-ledger.json',ledger)
print('CORNER COMPLETE',MODE,flush=True)
