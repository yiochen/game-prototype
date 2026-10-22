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
  lower=.785-.025*dy+.011*math.cos(7*a+.4)
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
  taper=max(.035,math.sin(math.pi*(.13+.87*t))**.62)
  for i in range(sides):
   a=2*math.pi*i/sides
   co=center+side*(width*taper*math.cos(a))+out*(depth*taper*math.sin(a));v.append(tuple(co))
 for j in range(steps):
  for i in range(sides):f.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
 f.append(tuple(range(sides-1,-1,-1)));f.append(tuple(range(steps*sides,(steps+1)*sides)))
 add(v,f)
# Five long crown-to-fringe locks flow together rather than sitting as bumps.
for k,x in enumerate([-.224,-.112,0,.112,.224]):
 z=.939-.018*abs(x)/.224
 lock([(x+.024,.171,z),(x+.042,.055,1.010),(x-.030,-.198,.960),(x-.025,-.281,.803+.012*(k%2))],.073 if k in [1,2,3] else .061,.036,(0,0,1))
# Back growth is organized into tapered vertical layers, with a scalloped nape.
for k,x in enumerate([-.224,-.112,0,.112,.224]):
 lock([(x-.016,.122,.943),(x+.014,.230,.941),(x+.025,.287,.831),(x+.005,.274,.733+.014*(k%2))],.070,.029,(0,1,.15))
# Short side locks end above the exposed spectacle arms and the ear crowns.
for sign in [-1,1]:
 for y in [-.157,-.035,.102]:
  lock([(sign*.245,y+.035,.939),(sign*.304,y+.025,.916),(sign*.313,y-.006,.837),(sign*.292,y-.030,.774+.018*(y<0))],.064,.027,(sign,0,.2))
me=bpy.data.meshes.new(prefix+'swept_short_hair topology');me.from_pydata(vs,[],fs);me.update();me.materials.append(material)
hair=bpy.data.objects.new(prefix+'swept_short_hair',me);coll.objects.link(hair)
hair.parent=root;hair.matrix_parent_inverse=Matrix.Identity(4)
# One static rest mesh obeys the original functional head-clearance planes.
planes=json.loads((HERE/'resources/hair-height-envelope.json').read_text())
for v in me.vertices:
 ceiling=min((p['ceiling']-1e-5-p['row'][3]-p['row'][0]*v.co.x-p['row'][1]*v.co.y)/p['row'][2] for p in planes)
 v.co.z=min(v.co.z,ceiling)
for p in me.polygons:p.use_smooth=True
g=hair.vertex_groups.new(name='head');g.add(list(range(len(me.vertices))),1,'REPLACE')
m=hair.modifiers.new('Preserved native weighted skeleton','ARMATURE');m.object=arm
hair['weighted_character_geometry']=True;hair['native_construction']='high anatomical scalp, swept tapered crown/fringe, short temples and layered nape'
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
