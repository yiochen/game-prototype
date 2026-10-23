"""Round02: fit folded native red cloth to the accepted rest-space head/hair.
Open immutable source/round01.blend. Change headwear only; preserve every other
mesh/material, rig/action, prop, camera and light. No edits to round01 files.
"""
import bpy,bmesh,sys,json,math,hashlib,importlib.util
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round02';OUT.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((HERE/'round01.blend').read_bytes()).hexdigest()=='91c87dd06f9fc1378e57e51752cbe797a5034c577baf3e39e886e8e8c398c169'
scene=bpy.data.scenes['Mateo warm soft native round01'];bpy.context.window.scene=scene;scene.name='Mateo warm soft native round02'
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in scene.collection.children if root in list(c.all_objects));arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
spec=importlib.util.spec_from_file_location('mateo_round02_actions',HERE/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
headwearTokens=('folded_wrapped_red_band','band_fold_','band_side_knot','band_tail_')
def isHeadwear(o):return '__refined_' in o.name and any(t in o.name for t in headwearTokens)
def meshHash(o):
 return hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[m.name for m in o.data.materials],'weights':[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices]},sort_keys=True).encode()).hexdigest()
unchanged={o.name:meshHash(o) for o in collection.all_objects if o.type=='MESH' and not isHeadwear(o)}
removed=[o.name for o in collection.all_objects if isHeadwear(o)]
for o in list(collection.all_objects):
 if isHeadwear(o):bpy.data.objects.remove(o,do_unlink=True)
red=bpy.data.materials['Mateo warm soft red folded cloth']
surface=[o for o in collection.all_objects if o.type=='MESH' and (o.name=='chef_mateo__head.001' or any(t in o.name for t in ('__refined_hair_','__refined_swept_sculpted_fringe_')))]
assert len(surface)==12,len(surface)
trees=[BVHTree.FromPolygons([o.matrix_basis@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],all_triangles=False) for o in surface]
centerY=.020
def radius(theta,z):
 d=Vector((math.cos(theta),math.sin(theta),0));origin=Vector((0,centerY,z))+d
 values=[]
 for tree in trees:
  hit,normal,index,distance=tree.ray_cast(origin,-d,1.5)
  if hit is not None:values.append((hit-Vector((0,centerY,z))).dot(d))
 assert values,(theta,z)
 return max(values)
def convexRadii(row):
 points=sorted((row[i]*math.cos(math.tau*i/len(row)),centerY+row[i]*math.sin(math.tau*i/len(row))) for i in range(len(row)))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 low=[];high=[]
 for p in points:
  while len(low)>1 and cross(low[-2],low[-1],p)<=0:low.pop()
  low.append(p)
 for p in reversed(points):
  while len(high)>1 and cross(high[-2],high[-1],p)<=0:high.pop()
  high.append(p)
 hull=low[:-1]+high[:-1];out=[]
 for i in range(len(row)):
  a=math.tau*i/len(row);dx,dy=math.cos(a),math.sin(a);hits=[]
  for j,p in enumerate(hull):
   q=hull[(j+1)%len(hull)];ex,ey=q[0]-p[0],q[1]-p[1];den=dx*ey-dy*ex
   if abs(den)<1e-12:continue
   ax,ay=p[0],p[1]-centerY;r=(ax*ey-ay*ex)/den;u=(ax*dy-ay*dx)/den
   if r>=0 and -.00001<=u<=1.00001:hits.append(r)
  assert hits;out.append(max(hits))
 return out
def cleanup(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 assert all(e.is_manifold for e in bm.edges),o.name
 assert bm.calc_volume(signed=True)>0,o.name
 bm.to_mesh(o.data);bm.free();o.data.update()
def mesh(name,verts,faces):
 me=bpy.data.meshes.new('Mateo fitted cloth '+name);me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new('chef_mateo__refined_'+name,me);collection.objects.link(o);o.parent=root;me.materials.append(red)
 group=o.vertex_groups.new(name='head');group.add(list(range(len(verts))),1,'REPLACE');mod=o.modifiers.new('Original native armature','ARMATURE');mod.object=arm
 for p in me.polygons:p.use_smooth=True
 cleanup(o);return o
# A solid, fitted fabric shell. Inner side enters the measured head/hair union
# slightly; the softly folded outer side forms a smooth majorant of that union.
# This keeps the red edges continuous while tucking the fringe/nape underneath.
nu=160;nv=24;raw=[];outer=[];fit=[]
for j in range(nv+1):
 t=j/nv;row=[]
 for i in range(nu):
  a=math.tau*i/nu
  # Same forehead band height around all views, with a subtle cloth drape.
  z=.800+.085*t+.0025*math.cos(2*a)*math.sin(math.pi*t)
  row.append(radius(a,z))
 raw.append(row)
 # Smooth upper envelope over tiny inter-lock valleys. The inner shell still
 # reaches the actual hair surface, so no empty background slot is created.
 taut=convexRadii(row)
 expanded=[max(taut[(i+k)%nu] for k in range(-2,3)) for i in range(nu)]
 smooth=[sum(expanded[(i+k)%nu]*w for k,w in [(-2,1),(-1,4),(0,6),(1,4),(2,1)])/16 for i in range(nu)]
 outer.append([max(taut[i],smooth[i])+.0095+.0025*math.sin(math.pi*t)+.0010*math.sin(2*math.pi*t)**2 for i in range(nu)])
vs=[]
for side in [0,1]:
 for j in range(nv+1):
  t=j/nv
  for i in range(nu):
   a=math.tau*i/nu;z=.800+.085*t+.0025*math.cos(2*a)*math.sin(math.pi*t)
   r=outer[j][i] if side==0 else raw[j][i]-.004
   vs.append((r*math.cos(a),centerY+r*math.sin(a),z))
offset=(nv+1)*nu;fs=[]
for j in range(nv):
 for i in range(nu):
  k=(i+1)%nu;a=j*nu+i;b=j*nu+k;c=(j+1)*nu+k;d=(j+1)*nu+i
  fs.append((a,b,c,d));fs.append((offset+d,offset+c,offset+b,offset+a))
for i in range(nu):
 k=(i+1)%nu;fs.append((i,offset+i,offset+k,k));a=nv*nu+i;b=nv*nu+k;fs.append((a,b,offset+b,offset+a))
band=mesh('fitted_folded_red_band',vs,fs)
def bandRadius(a,z):
 lo,hi=0.,1.
 for k in range(20):
  t=(lo+hi)/2;value=.800+.085*t+.0025*math.cos(2*a)*math.sin(math.pi*t)
  if value<z:lo=t
  else:hi=t
 f=(lo+hi)*.5*24;j=min(23,int(f));v=f-j
 u=(a%math.tau)/math.tau*160;i=int(u)%160;w=u-int(u)
 return (outer[j][i]*(1-w)+outer[j][(i+1)%160]*w)*(1-v)+(outer[j+1][i]*(1-w)+outer[j+1][(i+1)%160]*w)*v
def ellipsoid(name,loc,scale):
 nu=32;nv=20;verts=[]
 for j in range(nv+1):
  p=-math.pi/2+math.pi*j/nv
  for i in range(nu):
   a=math.tau*i/nu;verts.append((loc[0]+scale[0]*math.cos(p)*math.cos(a),loc[1]+scale[1]*math.cos(p)*math.sin(a),loc[2]+scale[2]*math.sin(p)))
 faces=[(j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i) for j in range(nv) for i in range(nu)]
 return mesh(name,verts,faces)
angle=.68;z=.876;r=bandRadius(angle,z)+.012
knot=ellipsoid('fitted_band_side_knot',(r*math.cos(angle),centerY+r*math.sin(angle),z),(.025,.024,.032))
# Two padded cloth leaves drape from the attached side knot over the actual hair.
for number,(length,sweep,width) in enumerate([(.070,.13,.026),(.108,-.025,.021)]):
 verts=[];nu=20;nv=24
 for j in range(nv+1):
  t=j/nv;a=angle+sweep*t;z=.879-length*t;profile=math.sin(math.pi*t)**.65
  for k in range(nu):
   ph=math.tau*k/nu
   # Angular width follows the head surface rather than a free rectangular card.
   base=radius(a,z);da=width*profile*math.cos(ph)/base;theta=a+da
   fitted=radius(theta,z)+.006
   if .800<=z<=.885:fitted=max(fitted,bandRadius(theta,z)+.006)
   r=fitted+.005*profile*math.sin(ph)
   verts.append((r*math.cos(theta),centerY+r*math.sin(theta),z))
 faces=[(j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i) for j in range(nv) for i in range(nu)]
 mesh('fitted_band_tied_tail_'+str(number),verts,faces)
assert {o.name:meshHash(o) for o in collection.all_objects if o.type=='MESH' and o.name in unchanged}==unchanged,'Unrelated accepted art changed'
native.apply_clip({'root':root,'collection':collection},rig,'idle',1,'S',scene)
for name in ['camera.json','assetRecord.json','rig.json']:
 value=json.loads((OBJ/'candidates/round01'/name).read_text())
 if name=='camera.json':value['artStyle']['revision']='Mateo native warm soft round02: fitted cloth headband'
 (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
project=HERE/'round02.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project),compress=True,check_existing=False)
report={'baseProject':'source/round01.blend','baseSHA256':hashlib.sha256((HERE/'round01.blend').read_bytes()).hexdigest(),'change':'Headband shell/knot/tails only, fitted to actual unchanged native head/hair rest geometry. Removed independent floating piping.','removedHeadwear':removed,'unchangedAcceptedMeshHashes':unchanged,'fitSurfaceObjects':[o.name for o in surface],'bandRadialSampling':{'angles':160,'rows':25,'construction':'taut convex outer cross-section, inner side fitted into actual head/hair surface','innerPenetration':.004,'outerFoldOffsets':[.0095,.0130]},'originalRigActionsPropsCameraMaterialsLightsPreserved':True,'noPriorRoundWrites':True}
(OUT/'headband-fit-validation.json').write_text(json.dumps(report,indent=2)+'\n')
for d in ['S','E','N','W']:
 native.apply_clip({'root':root,'collection':collection},rig,'idle',1,d,scene);scene.render.filepath=str(OUT/('hero-'+d+'.png'));bpy.ops.render.render(write_still=True)
print('MATEO_ROUND02_HEADWEAR_BUILT',str(project))
