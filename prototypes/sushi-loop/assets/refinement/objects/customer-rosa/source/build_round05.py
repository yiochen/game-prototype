"""Replace only Rosa hair in the exact round04 source with a continuous sculpted bob."""
import bpy,math,json,pathlib,sys,hashlib,importlib.util
from mathutils import Vector
H=pathlib.Path(__file__).resolve().parent;O=H.parent;RT='--runtime' in sys.argv
R=json.loads((O/('inputs/runtime-variants/export/source/customer-rosa/rig.json' if RT else 'inputs/source-rig.json')).read_text());root=bpy.data.objects[R['groundRootObject']];c=root.users_collection[0];arm=next(o for o in c.all_objects if o.type=='ARMATURE');sc=bpy.context.scene
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=c
c.hide_viewport=False;c.hide_render=False;arm.hide_viewport=False;arm.hide_set(False)
hair=[o for o in c.all_objects if o.type=='MESH' and any(k in o.name for k in ['continuous rounded bob','front swept lock','rounded fringe'])];material=hair[0].data.materials[0]
for o in hair:bpy.data.objects.remove(o,do_unlink=True)
# One closed native mesh; broad sweep and side flow are displaced in the actual surface.
rx,ry,cy,ztop,zeq=.322,.296,.027,1.002,.822
seg=192;dome=40;skirt=32;vs=[];fs=[]
def bottom(a,x):
 f=min(1,max(0,(math.cos(a)+.05)/.35));f=f*f*(3-2*f)
 fringe=.786-.024*(.5+.5*math.cos(5*math.pi*x/.28))
 return (.465+.020*(.5+.5*math.cos(6*a+.5)))*(1-f)+fringe*f

def sculpt(x,y,z,a,upper,weight=1):
 # Three broad diagonal locks flow across the frontal dome and naturally round onto the sides.
 front=max(0,math.cos(a))**1.3
 curve=.852+.245*x+.35*x*x
 relief=0
 for shift in [0,.064,.127]:
  distance=z-(curve+shift)
  relief-=.014*math.exp(-.5*(distance/.008)**2)
  relief+=.008*math.exp(-.5*((distance-.024)/.021)**2)
 relief*=front
 # Long shallow side/back channels curve through the same continuous surface into the nape.
 side=1-front
 phase=6*a+4*(z-.5)+.7*math.sin(2*a)
 relief+=side*(.017*math.cos(phase)+.002*math.cos(2*phase))*(max(0,1-(z-zeq)/(ztop-zeq))**2 if upper else 1)
 # Fade smoothly at the top pole and hairline; no stacked separate locks or bevel seams.
 fade=min(1,max(0,(ztop-z)/.05))*min(1,max(0,(z-bottom(a,x))/.025))
 relief*=fade*weight
 normal=Vector((x/(rx*rx),(y-cy)/(ry*ry),max(0,(z-zeq))/((ztop-zeq)**2) if upper else .05));normal.normalize()
 point=Vector((x,y,z))+normal*relief
 # The scalp must enclose the existing rounded head, including its upper corners.
 # Exact signed distance/normal of that native rounded cuboid sets a small constructive margin.
 center=Vector((0,.002,.672));half=Vector((.28,.235,.239));radius=.083
 for _ in range(3):
  v=point-center;q=Vector((abs(v[i])-(half[i]-radius) for i in range(3)));positive=Vector((max(0,k) for k in q));distance=positive.length+min(max(q),0)-radius
  if distance>=.010:break
  if positive.length>1e-8:gradient=Vector((positive[i]*(1 if v[i]>=0 else -1) for i in range(3))).normalized()
  else:
   axis=max(range(3),key=lambda i:q[i]);gradient=Vector((0,0,0));gradient[axis]=1 if v[axis]>=0 else -1
  point+=gradient*(.010-distance)
 return tuple(point)
for j in range(dome+1):
 p=math.pi*.5*j/dome;s=math.sin(p);exponent=1-.35*s**4
 for i in range(seg):
  a=math.tau*i/seg;x=rx*s*math.copysign(abs(math.sin(a))**exponent,math.sin(a));y=cy-ry*s*math.copysign(abs(math.cos(a))**exponent,math.cos(a));z=zeq+(ztop-zeq)*math.cos(p)
  vs.append(sculpt(x,y,z,a,True))
for j in range(1,skirt+1):
 t=j/skirt;rad=1+.025*math.sin(math.pi*t)-.055*t**3
 for i in range(seg):
  a=math.tau*i/seg;x=rx*rad*math.copysign(abs(math.sin(a))**.65,math.sin(a));y=cy-ry*rad*math.copysign(abs(math.cos(a))**.65,math.cos(a));bt=bottom(a,x);z=zeq*(1-t)+bt*t
  # An integrated front fringe gets gently rounded thickness as it meets the hairline.
  front=max(0,math.cos(a))**4;bulge=.011*math.sin(math.pi*t)*front;y-=bulge
  vs.append(sculpt(x,y,z,a,False))
for j in range(dome+skirt):
 for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
# Roll the entire variable hairline inward, keeping all joins within the head volume.
outer=(dome+skirt)*seg;rollstart=len(vs)
for k in range(1,5):
 t=k/4
 for i in range(seg):
  a=math.tau*i/seg;x,y,z=vs[outer+i];vs.append((x*(1-.10*t),cy+(y-cy)*(1-.10*t),z+.014*math.sin(math.pi*t/2)))
for k in range(4):
 lo=outer if k==0 else rollstart+(k-1)*seg;hi=rollstart+k*seg
 for i in range(seg):fs.append((lo+i,lo+(i+1)%seg,hi+(i+1)%seg,hi+i))
center=len(vs);vs.append((0,.04,.66));lo=rollstart+3*seg
for i in range(seg):fs.append((lo+i,lo+(i+1)%seg,center))
me=bpy.data.meshes.new('Rosa round05 continuous swept bob');me.from_pydata(vs,[],fs);me.update();import bmesh;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();ob=bpy.data.objects.new('Rosa refined'+(' runtime' if RT else '')+' connected sculpted bob',me);c.objects.link(ob);ob.parent=root;ob.matrix_parent_inverse.identity();ob.data.materials.append(material)
for p in me.polygons:p.use_smooth=True
g=ob.vertex_groups.new(name='head');g.add(list(range(len(me.vertices))),1,'REPLACE');mod=ob.modifiers.new('Original unchanged Rosa head binding','ARMATURE');mod.object=arm
for mesh in list(bpy.data.meshes):
 if mesh.users==0:bpy.data.meshes.remove(mesh)
sc['rosa_refinement_round']='05'
spec=importlib.util.spec_from_file_location('rosa_native',H/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);asset={'root':root,'collection':c,'armature':arm};clip='eat-salmon' if RT else 'stand';native.apply_clip(asset,R,clip,1,'S',sc)
path=H/('round-05-runtime.blend' if RT else 'round-05.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True);out=O/'candidates/round-05/draft';out.mkdir(parents=True,exist_ok=True)
for d in ['N','E','S','W']:
 native.apply_clip(asset,R,clip,1,d,sc);sc.render.filepath=str(out/(('runtime-eat-' if RT else 'stand-')+d+'.png'));bpy.ops.render.render(write_still=True)
(H/('build-runtime-round05.json' if RT else 'build-main-round05.json')).write_text(json.dumps({'project':path.name,'priorSource':'round-04-runtime.blend' if RT else 'round-04.blend','priorSourceSHA256':hashlib.sha256((H/('round-04-runtime.blend' if RT else 'round-04.blend')).read_bytes()).hexdigest(),'frozenBriefSHA256':hashlib.sha256((O/'brief.json').read_bytes()).hexdigest(),'method':'one closed native sculpted bob with integrated diagonal crown relief, scalloped front hairline and continuous side/nape channels; removed all separate scalp/sweep/fringe objects','changedObjects':['hair only'],'vertices':len(me.vertices),'faces':len(me.polygons),'rigActionsBodyMaterialsLightsCameraFood':'retained exact native round04 data','blender':bpy.app.version_string},indent=2)+'\n')
