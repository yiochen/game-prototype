"""Hair-only native revision. Open immutable round-02[,-runtime].blend first.

Background Blender --python this.py -- main|runtime [reproduce]. Reproduction
writes to separate folders; no reviewed source or rendered bytes are overwritten.
"""
import bpy, math, json, sys, hashlib, importlib.util
from pathlib import Path
from mathutils import Vector, Matrix
HERE=Path(__file__).resolve().parent; OBJ=HERE.parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['main']
MODE=args[0]; reproduce='reproduce' in args
rec=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text())
spec=importlib.util.spec_from_file_location('native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
coll=next(c for c in sc.collection.children if root.name in c.all_objects);arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
asset={'root':root,'collection':coll};native.apply_clip(asset,rec,next(iter(rec['clips'])),1,'S',sc)
old=next(o for o in coll.all_objects if 'coherent_sculpted_hair' in o.name)
material=old.data.materials[0];prefix=old.name.split('coherent_sculpted_hair')[0]
inputSHA=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
bpy.data.objects.remove(old,do_unlink=True)
vs=[];fs=[]
def add(v,f):
 off=len(vs);vs.extend(v);fs.extend(tuple(off+i for i in face) for face in f)
# A high fitted scalp, with rounded corners and a deliberately open temple line.
# The bottom contour is anatomical and static, independent of capture direction.
N=128;R=28;cap=[];faces=[]
for j in range(R+1):
 p=(math.pi/2-.002)*j/R
 for i in range(N):
  a=2*math.pi*i/N;dx=math.sin(a);dy=-math.cos(a)
  lower=.809-.018*dy+.012*math.cos(7*a+.4)
  rx=.300*math.cos(p)**.35;ry=.268*math.cos(p)**.35
  x=math.copysign(abs(dx)**.43,dx)*rx
  y=math.copysign(abs(dy)**.43,dy)*ry+.006
  z=lower+(.964-lower)*math.sin(p)
  cap.append((x,y,z))
for j in range(R):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces.append(tuple(range(N-1,-1,-1)));faces.append(tuple(range(R*N,(R+1)*N)))
add(cap,faces)
def bezier(points,t):
 a,b,c,d=[Vector(p) for p in points];s=1-t
 return s*s*s*a+3*s*s*t*b+3*s*t*t*c+t*t*t*d
def lock(points,width,depth,normal):
 """A swept tapered solid, with long ridges and actual silhouette tips."""
 v=[];f=[];steps=32;sides=16;n=Vector(normal).normalized()
 for j in range(steps+1):
  t=j/steps;center=bezier(points,t)
  tangent=(bezier(points,min(1,t+.002))-bezier(points,max(0,t-.002))).normalized()
  side=tangent.cross(n).normalized();out=side.cross(tangent).normalized()
  # Broad rooted shoulder, softer narrowing to a short rounded tip.
  taper=max(.06,math.sin(math.pi*(.10+.82*t))**.48)
  for i in range(sides):
   a=2*math.pi*i/sides
   co=center+side*(width*taper*math.cos(a))+out*(depth*taper*math.sin(a));v.append(tuple(co))
 for j in range(steps):
  for i in range(sides):f.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
 f.append(tuple(range(sides-1,-1,-1)));f.append(tuple(range(steps*sides,(steps+1)*sides)))
 add(v,f)
def ellipsoid(center,radii,angle=0):
 v=[];f=[];n=48;r=24
 for j in range(r+1):
  p=math.pi*j/r
  for i in range(n):
   a=2*math.pi*i/n;x=radii[0]*math.sin(p)*math.cos(a);y=radii[1]*math.sin(p)*math.sin(a)
   v.append((center[0]+x*math.cos(angle)-y*math.sin(angle),center[1]+x*math.sin(angle)+y*math.cos(angle),center[2]+radii[2]*math.cos(p)))
 for j in range(r):
  for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 add(v,f)
# Overlapping swept crown lobes have full rounded volumes and an offset part.
for x,y,z,rx,ry in [(-.190,.015,.932,.109,.206),(-.072,.018,.956,.119,.217),(.070,.025,.954,.119,.214),(.194,.045,.932,.105,.193)]:
 ellipsoid((x,y,z),(rx,ry,.056),-.25)
# Deliberately shorter fringe curls sit on the high frontal hairline.
for k,x in enumerate([-.226,-.113,0,.113,.226]):
 lock([(x+.034,-.173,.925),(x+.015,-.257,.908),(x-.015,-.293,.842),(x-.024,-.283,.809+.010*(k%2))],.076 if k in [1,2,3] else .063,.045,(0,-1,.3))
# Back growth is organized into tapered vertical layers, with a scalloped nape.
for k,x in enumerate([-.224,-.112,0,.112,.224]):
 lock([(x-.028,.165,.926),(x+.014,.264,.915),(x+.025,.291,.848),(x+.005,.280,.770+.014*(k%2))],.072,.035,(0,1,.15))
# Short side locks end above the exposed spectacle arms and the ear crowns.
for sign in [-1,1]:
 for y in [-.145,.015,.155]:
  lock([(sign*.250,y+.035,.922),(sign*.305,y+.005,.895),(sign*.312,y-.025,.849),(sign*.290,y-.054,.791+.015*(y<0))],.073,.031,(sign,0,.2))
me=bpy.data.meshes.new(prefix+'swept_short_hair topology');me.from_pydata(vs,[],fs);me.update();me.materials.append(material)
hair=bpy.data.objects.new(prefix+'swept_short_hair',me);coll.objects.link(hair)
hair.parent=root;hair.matrix_parent_inverse=Matrix.Identity(4)
# One static rest mesh obeys the original functional head-clearance planes.
planes=json.loads((HERE/'resources/hair-height-envelope.json').read_text())
horizontalPath=HERE/'resources/round03-functional-hair-planes.json'
if MODE=='main':
 horizontal=[]
 for clip in rec['clips']:
  for frame in range(1,13):
   native.apply_clip(asset,rec,clip,frame,'S',sc)
   tr=arm.matrix_world @ arm.pose.bones['head'].matrix @ arm.data.bones['head'].matrix_local.inverted() @ arm.matrix_world.inverted() @ root.matrix_world
   for axis in [0,1]:
    for sign in [-1,1]:horizontal.append({'clip':clip,'frame':frame,'axis':axis,'row':[sign*x for x in tr[axis]],'ceiling':.5-1e-5})
 if not horizontalPath.exists():horizontalPath.write_text(json.dumps(horizontal,indent=2)+'\n')
 else:assert json.loads(horizontalPath.read_text())==horizontal
else:horizontal=json.loads(horizontalPath.read_text())
for v in me.vertices:
 for iteration in range(4):
  ceiling=min((p['ceiling']-1e-5-p['row'][3]-p['row'][0]*v.co.x-p['row'][1]*v.co.y)/p['row'][2] for p in planes)
  v.co.z=min(v.co.z,ceiling)
  for p in horizontal:
   x,y,z,w=p['row'];excess=x*v.co.x+y*v.co.y+z*v.co.z+w-p['ceiling']
   if excess>0:
    length=x*x+y*y;v.co.x-=excess*x/length;v.co.y-=excess*y/length
for p in me.polygons:p.use_smooth=True
g=hair.vertex_groups.new(name='head');g.add(list(range(len(me.vertices))),1,'REPLACE')
m=hair.modifiers.new('Preserved native weighted skeleton','ARMATURE');m.object=arm
hair['weighted_character_geometry']=True;hair['native_construction']='high anatomical scalp, swept tapered crown/fringe, short temples and layered nape'
# Original arm bars ran inside the head. Route the same dark spectacle frame
# around the actual temple surface, retaining the front rim/bridge geometry.
for sign in [-1,1]:
 o=next(o for o in coll.all_objects if o.name.startswith(prefix+'glasses_arm_'+str(sign)+'.'))
 points=[(sign*.185,-.267,.694),(sign*.285,-.222,.694),(sign*.291,-.068,.694),(sign*.304,.018,.680)]
 curve=bpy.data.curves.new(o.name+' exposed temple path','CURVE');curve.dimensions='3D';curve.resolution_u=16;curve.bevel_depth=.0065;curve.bevel_resolution=4
 sp=curve.splines.new('BEZIER');sp.bezier_points.add(3)
 for b,p in zip(sp.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 tmp=bpy.data.objects.new('Ellis temple path temporary',curve);coll.objects.link(tmp)
 bpy.context.view_layer.objects.active=tmp;tmp.select_set(True);bpy.ops.object.convert(target='MESH');me2=tmp.data.copy();bpy.data.objects.remove(tmp,do_unlink=True)
 me2.materials.clear();me2.materials.append(o.data.materials[0]);o.data=me2
 for m in list(o.modifiers):
  if m.type!='ARMATURE':o.modifiers.remove(m)
 o.vertex_groups.clear();g=o.vertex_groups.new(name='head');g.add(list(range(len(me2.vertices))),1,'REPLACE')
 for p in me2.polygons:p.use_smooth=True
native.apply_clip(asset,rec,next(iter(rec['clips'])),1,'S',sc)
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100
dest=HERE/('reproductions-round03' if reproduce else '')/('round-03.blend' if MODE=='main' else 'round-03-runtime.blend');dest.parent.mkdir(exist_ok=True)
if dest.exists():raise RuntimeError('Immutable output exists: '+str(dest))
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
out=OBJ/'candidates'/('reproduction-round03' if reproduce else 'round-03')/'study';out.mkdir(parents=True,exist_ok=True)
evidence={'mode':MODE,'inputProjectSHA256':inputSHA,'outputProjectSHA256':hashlib.sha256(dest.read_bytes()).hexdigest(),'meshVertices':len(me.vertices),'meshPolygons':len(me.polygons),'groups':[g.name for g in hair.vertex_groups],'unchangedMaterial':material.name,'renders':[]}
for direction in 'NESW':
 native.apply_clip(asset,rec,next(iter(rec['clips'])),1,direction,sc)
 path=out/(MODE+'-'+direction+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name)
 evidence['renders'].append({'direction':direction,'rootMatrix':[list(r) for r in root.matrix_world],'path':str(path.relative_to(OBJ)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(out/(MODE+'-construction.json')).write_text(json.dumps(evidence,indent=2)+'\n')
print('ELLIS_ROUND03_BUILD',MODE,str(dest),flush=True)
