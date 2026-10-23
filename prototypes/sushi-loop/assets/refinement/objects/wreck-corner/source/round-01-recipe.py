import bpy,sys,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;B=S.parent;R=S/'resources';O=B/'candidates/round-01';O.mkdir(parents=True,exist_ok=True)
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};records=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def matrix(o):return [list(r) for r in o.matrix_world]
def enable(c):
 c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
 bpy.context.view_layer.update()
def configure(sc,frame=(192,352),anchor=(96,248)):
 cam=sc.camera;sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;sc.render.resolution_percentage=100
 sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.filter_size=.01
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update();r=px((0,0,0))
 return {'frame':list(frame),'root':list(anchor),'scale':2,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'ortho':cam.data.ortho_scale,'cameraWorld':matrix(cam),'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}}
def render(sc,path,meta):
 p=O/path;p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'path':path,'direction':meta['direction'],'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':matrix(root),**meta,'sha256':sha(p)})
def bend(x,y,z):
 # Exact original finite-support piecewise ruled turn; full collars are rigid proper mappings.
 points=[(-.5,(-.5,0),(0,1)),(-.25,(-.25,0),(0,1)),(0,(0,0),(-math.sqrt(.5),math.sqrt(.5))),(.25,(0,.25),(-1,0)),(.5,(0,.5),(-1,0))]
 for (a,c,t),(bb,cc,tt) in zip(points,points[1:]):
  if x<=bb+1e-7:
   f=max(0,min(1,(x-a)/(bb-a)));cx=c[0]*(1-f)+cc[0]*f;cy=c[1]*(1-f)+cc[1]*f;tx=t[0]*(1-f)+tt[0]*f;ty=t[1]*(1-f)+tt[1]*f
   return (cx+y*tx,cy+y*ty,z),math.atan2(-tx,ty)
 raise ValueError(x)
def curved_bend(x,y,z,kind):
 raw,rawa=bend(x,y,z)
 if abs(x)>=.25:return raw,rawa
 u=(x+.25)/.5
 cx=-.25*(1-u)*(1-u);cy=.25*u*u
 dx=.5*(1-u);dy=.5*u;ln=math.hypot(dx,dy);tx=-dy/ln;ty=dx/ln
 curved=(cx+y*tx,cy+y*ty,z);a=math.atan2(-tx,ty)
 weight=1 if kind!='lower' else max(0,min(1,(z-.04)/.10))
 return tuple(raw[i]*(1-weight)+curved[i]*weight for i in range(3)),rawa*(1-weight)+a*weight

def rot(n,a):return (n[0]*math.cos(a)-n[1]*math.sin(a),n[0]*math.sin(a)+n[1]*math.cos(a),n[2])
bpy.ops.wm.open_mainfile(filepath=str(R/'wreck-middle-approved02.blend'));sc=bpy.context.scene
midcol=bpy.data.collections['Wreck middle authored candidate'];mid=bpy.data.objects['wreck-middle__root'];enable(midcol)
can={k:bpy.data.objects['wreck-middle__'+k+'_canonical_rail'] for k in ['lower','upper','rear']}
col=bpy.data.collections.new('S33_PROP_wreck-corner.001');sc.collection.children.link(col);root=bpy.data.objects.new('wreck-corner__root.001',None);col.objects.link(root)
source=json.loads((S/'initial-native-probe.json').read_text());props=next(o['properties'] for o in source['objects'] if o['name']==source['root'])
for k,v in props.items():root[k]=v
root['refinement']='warm-soft wreck corner round01';root['source_freedom']='native continuous turn, partial hull planking, rounded iron and functional fastening'
def mesh_obj(name,verts,faces,mats,indices=None,normals=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('wreck-corner__'+name,me);col.objects.link(o);o.parent=root
 for m in mats:me.materials.append(m)
 if indices:
  for f,i in zip(me.polygons,indices):f.material_index=i
 if normals:
  at=me.attributes.new('CanonicalNormal','FLOAT_VECTOR','CORNER')
  for q,n in zip(at.data,normals):q.vector=n
 return o
# Rebuild three continuous rails. The complete side/cap fields are pulled from exact approved meshes.
fieldproof=[]
for kind,src in can.items():
 me=src.data;xs=sorted(set(v.co.x for v in me.vertices));rings=[[tuple(v.co) for v in me.vertices if abs(v.co.x-x)<1e-7] for x in xs]
 assert all(len(r)==8 for r in rings)
 oldattr=me.attributes['CanonicalNormal'];stripnorm=[];stripmat=[]
 for j in range(len(xs)-1):
  fn=[];fm=[]
  for k in range(8):
   f=me.polygons[1+j*8+k];fn.append([tuple(oldattr.data[i].vector) for i in f.loop_indices]);fm.append(f.material_index)
  stripnorm.append(fn);stripmat.append(fm)
 newxs=sorted(set(xs+[-.25,.25]));verts=[]
 def interval(x):
  return next((j for j in range(len(xs)-1) if x<=xs[j+1]+1e-8),len(xs)-2)
 def sample(x,k):
  j=interval(x);f=max(0,min(1,(x-xs[j])/(xs[j+1]-xs[j])));a=Vector(rings[j][k]);bb=Vector(rings[j+1][k]);v=a.lerp(bb,f);v.x=x;return v
 def norm_at(x,k,end):
  j=interval(x);f=max(0,min(1,(x-xs[j])/(xs[j+1]-xs[j])));ns=stripnorm[j][k];return Vector(ns[end]).lerp(Vector(ns[3-end]),f)
 for x in newxs:
  for k in range(8):v=sample(x,k);verts.append(curved_bend(v.x,v.y,v.z,kind)[0])
 faces=[list(reversed(range(8)))];normals=[(-1,0,0)]*8;indices=[me.polygons[0].material_index]
 for j,(x1,x2) in enumerate(zip(newxs,newxs[1:])):
  for k in range(8):
   faces.append([j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k]);indices.append(stripmat[interval((x1+x2)/2)][k])
   for x,end in [(x1,0),(x1,1),(x2,1),(x2,0)]:
    a=curved_bend(x,0,.20,kind)[1];normals.append(rot(norm_at(x,k,end),a))
 faces.append(list(range((len(newxs)-1)*8,len(newxs)*8)));indices.append(me.polygons[-1].material_index);normals.extend([(0,1,0)]*8)
 o=mesh_obj(kind+'_continuous_hull',verts,faces,list(me.materials),indices,normals)
 for f in o.data.polygons:f.use_smooth=True
 fieldproof.append({'kind':kind,'object':o.name,'source':src.name,'canonical_source_sha256':sha(R/'wreck-middle-approved02.blend'),'source_materials':[m.name for m in me.materials],'mapping':'W baked identity; N baked properRz+90; actual CanonicalNormal vectors rotated with baked frame, object identity','stations':newxs,'field_domain':'CORNER FLOAT_VECTOR, linked exact copied canonical material graphs; normalize after interpolation','collar_side_constant':True,'caps_distinct_outward_longitudinal':True})
# Purposeful blue inset planks at rear, with rounded native edges; retain open bays.
blue=bpy.data.materials['Blue painted timber - canonical height albedo'];lowblue=bpy.data.materials['Blue painted timber - lower layered hue'];iron=bpy.data.materials['Slate iron - canonical soft edge'];weariron=bpy.data.materials['Soft worn iron bevels'];boltmat=bpy.data.materials['Pale worn metal fasteners'];cream=bpy.data.materials['Restrained cream paint wear'];grain=bpy.data.materials['Shallow blue grain grooves']
def bevel(o,width=.012,segments=3,edge=False):
 b=o.modifiers.new('Rounded crafted edge','BEVEL');b.width=width;b.segments=segments
 if edge:b.affect='EDGES';b.material=1
 w=o.modifiers.new('Weighted broad face normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=50
 return o
for i,(ya,yb,za,zb) in enumerate([(.05,.19,.224,.385),(.105,.20,.409,.554)]):
 xs=[-.375,-.25,-.16,0,.16,.25,.375];vs=[]
 for x in xs:
  for y,z in [(ya,za),(yb,za),(yb,zb),(ya,zb)]:vs.append(curved_bend(x,y,z,'inset')[0])
 fs=[[3,2,1,0]]
 for j in range(len(xs)-1):
  for k in range(4):fs.append([j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k])
 fs.append(list(range((len(xs)-1)*4,len(xs)*4)))
 bevel(mesh_obj('inset_blue_timber_'+str(i),vs,fs,[blue if i==0 else lowblue]),.011,3)
def box(name,loc,dims,material,angle=0,edge=False):
 x,y,z=[v/2 for v in dims];vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)];fs=[[0,4,6,2],[1,3,7,5],[0,1,5,4],[2,6,7,3],[0,2,3,1],[4,5,7,6]]
 o=mesh_obj(name,vs,fs,[material,weariron] if edge else [material]);o.location=loc;o.rotation_euler.z=angle;bevel(o,.009 if edge else .005,3,edge);return o
for j,x in enumerate([-.235,.235]):
 a=0 if j==0 else math.pi/2
 # Canonical station x becomes proper N wing position.
 c=(x,.005,.425) if j==0 else (-.005,x,.425)
 front=(x,-.17,.425) if j==0 else (.17,x,.425)
 box('iron_front_upright_'+str(j),front,(.084,.068,.682),iron,a,True)
 top=(x,.005,.735) if j==0 else (-.005,x,.735)
 box('iron_top_return_'+str(j),top,(.084,.374,.062),iron,a,True)
 rear=(x,.183,.40) if j==0 else (-.183,x,.40)
 box('iron_rear_upright_'+str(j),rear,(.075,.052,.57),iron,a,True)
 lower=(x,.005,.135) if j==0 else (-.005,x,.135)
 box('iron_lower_return_'+str(j),lower,(.075,.374,.05),iron,a,True)
 pl=(x,-.201,.365) if j==0 else (.201,x,.365)
 box('front_plate_'+str(j),pl,(.136,.030,.174),iron,a,True)
 back=(x,.205,.48) if j==0 else (-.205,x,.48)
 box('rear_plate_'+str(j),back,(.10,.028,.12),iron,a,True)
 for k,z in enumerate([.325,.405]):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1)
  o=bpy.context.object;o.name='wreck-corner__pale_bolt_'+str(j)+str(k)
  for cc in list(o.users_collection):cc.objects.unlink(o)
  col.objects.link(o);o.parent=root;o.data.materials.append(boltmat)
  o.location=(x,-.224,z) if j==0 else (.224,x,z);o.scale=(.021,.009,.021) if j==0 else (.009,.021,.021)
 # One large rear fastener, visible from reverse facings.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1)
 o=bpy.context.object;o.name='wreck-corner__rear_bolt_'+str(j)
 for cc in list(o.users_collection):cc.objects.unlink(o)
 col.objects.link(o);o.parent=root;o.data.materials.append(boltmat);o.location=(x,.224,.48) if j==0 else (-.224,x,.48);o.scale=(.018,.008,.018) if j==0 else (.008,.018,.018)
# Subtle shallow grain and restrained worn paint lie inside the authored budget, away from collars.
def line(name,pts,material,radius):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=8;cu.bevel_depth=radius;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new('wreck-corner__'+name,cu);col.objects.link(o);o.parent=root;cu.materials.append(material)
for i,(y,z) in enumerate([(-.015,.752),(.082,.387),(.133,.556)]):
 pts=[curved_bend(x,y+.002*math.sin(x*16+i),z,'upper')[0] for x in [-.35,-.29,-.21,-.12,0,.12,.21,.29,.35]];line('grain_'+str(i),pts,grain,.0012)
for j,(x,y,z) in enumerate([(-.31,-.064,.749),(.31,.015,.751),(-.12,.102,.556)]):
 pts=[curved_bend(x+d,y+.002*math.sin(d*40),z,'upper')[0] for d in [-.025,-.012,0,.012,.025]];line('small_worn_edge_'+str(j),pts,cream,.0016)
# Exact canonical native scene rig remains untouched; append exact approved edge for mixed controls.
with bpy.data.libraries.load(str(R/'wreck-edge-approved02.blend'),link=False) as (src,dst):dst.collections=[c for c in src.collections if 'Wreck edge' in c]
edgecol=dst.collections[0];sc.collection.children.link(edgecol);enable(edgecol);edge=next(o for o in edgecol.objects if o.get('asset_id')=='wreck-edge')
clones={}
for o in list(midcol.objects):cp=o.copy();midcol.objects.link(cp);clones[o]=cp
for o,cp in clones.items():cp.parent=clones.get(o.parent);cp.matrix_parent_inverse=o.matrix_parent_inverse.copy()
midN=clones[mid]
midcol.hide_render=True;edgecol.hide_render=True;sc.frame_set(1);sc.render.fps=12;sc.frame_start=sc.frame_end=1
root.rotation_euler=(0,0,0);root.location=(0,0,0);camera=configure(sc);bpy.context.view_layer.update()
# Exact native save before capture, without per-view tuning.
sc.render.filepath='';bpy.ops.wm.save_as_mainfile(filepath=str(S/'round-01.blend'))
(O/'field-construction.json').write_text(json.dumps(fieldproof,indent=2)+'\n')
for d,a in ANGLES.items():
 root.rotation_euler.z=a;midcol.hide_render=True;edgecol.hide_render=True;bpy.context.view_layer.update();camera=configure(sc)
 render(sc,'native/static/'+d+'/000.png',{'kind':'hero','direction':d,'camera':camera})
 dst=O/'frames/static'/d/'000.png';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/'native/static'/d/'000.png',dst)
 at=O/'atlases'/('static-'+d+'.png');at.parent.mkdir(exist_ok=True);shutil.copyfile(dst,at)
 midcol.hide_render=False;west=Vector((-math.cos(a),-math.sin(a),0));north=Vector((-math.sin(a),math.cos(a),0));mid.location=west;mid.rotation_euler.z=a;midN.location=north;midN.rotation_euler.z=a+math.pi/2
 pxroots=[(0,0),(west.x*128,-west.y*128),(north.x*128,-north.y*128)];anchor=(round(96-min(v[0] for v in pxroots)),round(248-min(v[1] for v in pxroots)))
 for kind in ['middle-L','mixed-edge-L']:
  for o in [mid]+list(mid.children_recursive):o.hide_render=kind=='mixed-edge-L'
  edgecol.hide_render=kind!='mixed-edge-L';edge.location=west;edge.rotation_euler.z=a;bpy.context.view_layer.update();camera=configure(sc,(320,480),anchor)
  render(sc,kind+'/'+d+'.png',{'kind':kind,'direction':d,'camera':camera,'moduleRootMatrices':{'corner':matrix(root),'Wneighbor':matrix(mid if kind=='middle-L' else edge),'Nneighbor':matrix(midN)},'assembly':{'roots':[[0,0,0],list(west),list(north)],'rotationsDegrees':[math.degrees(a),math.degrees(a),math.degrees(a)+90],'Wcontact':'corner W to exact neighbor E','Ncontact':'corner N to proper+90 neighbor W','capsRetained':True,'pitch':1}})
 for o in [mid]+list(mid.children_recursive):o.hide_render=False
(O/'capture-records.json').write_text(json.dumps({'blender':bpy.app.version_string,'sourceSHA256':sha(S/'round-01.blend'),'records':records},indent=2)+'\n')
print('ROUND01_NATIVE_COMPLETE',len(records))
