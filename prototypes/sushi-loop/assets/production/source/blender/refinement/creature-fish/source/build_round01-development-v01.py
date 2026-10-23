import bpy,bmesh,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import fish_round01 as rt
RES=P/'round-01-resources';OUT=P.parent/'candidates/round-01-development-v01';OUT.mkdir(parents=True,exist_ok=True)
source=RES/'inputs/untouched.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(source),link=False) as (a,b):
 b.collections=[rt.COLL]
 b.actions=[n for n in a.actions if n.startswith('S33_NATIVE__creature-fish__')]
coll=bpy.data.collections[rt.COLL];bpy.context.scene.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
root=bpy.data.objects[rt.ROOT];arm=bpy.data.objects[rt.ARM]
for o in list(coll.objects):
 o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
arm.animation_data_create();arm.animation_data.action=None
for b in arm.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
# Compatible Euler body channels; retain source object-motion and semantic cohorts.
for a in bpy.data.actions:
 for layer in a.layers:
  for st in layer.strips:
   bag=st.channelbag(a.slots[0],ensure=False)
   if not bag:continue
   for fc in bag.fcurves:
    if 'pose.bones' in fc.data_path and fc.data_path.endswith('rotation_euler'):
     for k in fc.keyframe_points:k.co.y*=.58;k.handle_left.y*=.58;k.handle_right.y*=.58
    fc.extrapolation='CONSTANT'

def lin(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def color(h):return tuple(lin(int(h[i:i+2],16)/255) for i in (1,3,5))+(1,)
def mix(a,b,t):return tuple(a[i]*(1-t)+b[i]*t for i in range(4))
blue=color('#1495E7');cobalt=color('#087BD1');cyan=color('#39CDE9');pale=color('#A6E8EA')
def material(name,c,rough=.42,spec=.27,coat=.12,attribute=False):
 m=bpy.data.materials.new(name);m.diffuse_color=c;m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=spec;bs.inputs['Coat Weight'].default_value=coat;bs.inputs['Coat Roughness'].default_value=.3;m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
 if attribute:
  at=n.new('ShaderNodeVertexColor');at.layer_name='fish_color';m.node_tree.links.new(at.outputs['Color'],bs.inputs['Base Color'])
 return m
skin=material('Fish cobalt cyan smooth native skin',blue,attribute=True)
white=material('Fish warm ivory eye',color('#F5F3DE'),.30,.24,.15)
iris=material('Fish ocean blue iris',color('#1595D8'),.25,.32,.24)
pupil=material('Fish navy pupil',color('#062D51'),.20,.35,.25)
glint=material('Fish pearl glint',color('#FFFFFF'),.24,.25,.10)
lip=material('Fish turquoise muzzle',color('#45C9DF'),.4,.24,.1)
mouth=material('Fish modest navy mouth',color('#07577E'),.48,.16,.0)
def weight_y(y):
 centers=[.43,.228,.026,-.176,-.378]
 # Head remains coherent; continuous rest-space blending down the spine.
 if y>=centers[0]:return [(0,1.)]
 if y<=centers[-1]:return [(4,1.)]
 for i in range(4):
  if centers[i]>=y>=centers[i+1]:
   t=(centers[i]-y)/(centers[i]-centers[i+1]);t=t*t*(3-2*t);return [(i,1-t),(i+1,t)]
def obj(name,verts,faces,mat,cols=None,rigid=None):
 mesh=bpy.data.meshes.new(name+' geometry');mesh.from_pydata(verts,[],faces);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 o=bpy.data.objects.new('creature-fish__'+name,mesh);coll.objects.link(o);o.parent=arm
 for p in mesh.polygons:p.use_smooth=True
 for i in range(5):o.vertex_groups.new(name='spine_'+str(i))
 for v in mesh.vertices:
  ws=[(rigid,1.)] if rigid is not None else weight_y(v.co.y)
  for i,w in ws:
   if w>1e-9:o.vertex_groups[i].add([v.index],w,'REPLACE')
 mod=o.modifiers.new('Coherent native spine deformation','ARMATURE');mod.object=arm;mod.use_deform_preserve_volume=True
 o.data.materials.append(mat)
 if cols:
  a=mesh.color_attributes.new(name='fish_color',type='FLOAT_COLOR',domain='POINT')
  for v,c in zip(a.data,cols):v.color=c
 return o
def sphere(name,center,scale,mat,rigid=0):
 vs=[];fs=[];N=32;M=20
 for j in range(M+1):
  p=math.pi*j/M
  for i in range(N):
   a=2*math.pi*i/N;vs.append((center[0]+scale[0]*math.sin(p)*math.cos(a),center[1]+scale[1]*math.sin(p)*math.sin(a),center[2]+scale[2]*math.cos(p)))
 for j in range(M):
  for i in range(N):
   q=j*N+i;r=j*N+(i+1)%N;fs.append((q,r,r+N,q+N))
 return obj(name,vs,fs,mat,rigid=rigid)

# Smooth radius envelope with a continuous closed body and broad pale underside.
controls=[(-.62,.025,.042),(-.50,.064,.10),(-.38,.13,.19),(-.20,.218,.267),(0,.278,.295),(.18,.286,.282),(.33,.235,.232),(.44,.145,.155),(.50,.048,.070),(.52,.001,.018)]
def radii(y):
 for k in range(len(controls)-1):
  if controls[k][0]<=y<=controls[k+1][0]:
   t=(y-controls[k][0])/(controls[k+1][0]-controls[k][0]);q=[]
   for a in (1,2):
    v0=controls[max(0,k-1)][a];v1=controls[k][a];v2=controls[k+1][a];v3=controls[min(len(controls)-1,k+2)][a]
    q.append(max(.001,.5*((2*v1)+(-v0+v2)*t+(2*v0-5*v1+4*v2-v3)*t*t+(-v0+3*v1-3*v2+v3)*t*t*t)))
   return q
 return controls[-1][1:]
vs=[];cs=[];fs=[];nr=64;ns=64
for j in range(nr+1):
 y=-.62+1.14*j/nr;rx,rz=radii(y)
 for i in range(ns):
  a=2*math.pi*i/ns;v=math.sin(a);vs.append((rx*math.cos(a),y,.44+rz*v))
  under=max(0,min(1,(-v+.12)/.85));under=under*under*(3-2*under);base=mix(cobalt,cyan,.18+.24*(1-abs(v)));cs.append(mix(base,pale,under*.87))
for j in range(nr):
 for i in range(ns):q=j*ns+i;r=j*ns+(i+1)%ns;fs.append((q,r,r+ns,q+ns))
fs.append(tuple(reversed(range(ns))));fs.append(tuple(nr*ns+i for i in range(ns)))
obj('rounded_body',vs,fs,skin,cs)

# Padded curved fin membranes, closed native volumes rather than flat cards.
def membrane(name,fun,N=32,M=16,kind='fin'):
 vs=[];cs=[];fs=[]
 for side in [1,-1]:
  for j in range(N+1):
   t=j/N
   for i in range(M+1):
    u=-1+2*i/M;p=fun(t,u,side);vs.append(p)
    c=mix(cobalt,cyan,.25+.6*abs(u));cs.append(c)
 width=M+1;count=(N+1)*width
 for side in range(2):
  offset=side*count
  for j in range(N):
   for i in range(M):
    a=offset+j*width+i;f=(a,a+1,a+1+width,a+width);fs.append(f if side==0 else tuple(reversed(f)))
 edges=[]
 for i in range(M):edges.extend([(i,i+1),(N*width+i+1,N*width+i)])
 for j in range(N):edges.extend([((j+1)*width,j*width),(j*width+M,(j+1)*width+M)])
 for a,b in edges:fs.append((a,b,b+count,a+count))
 return obj(name,vs,fs,skin,cs)
def tail(t,u,s):
 width=.034+.275*math.sin(t*math.pi/2);y=-.55+t*(-.19-.11*abs(u)**.75)
 z=.44+.045*t+.028*math.sin(math.pi*t)*(1-u*u)+s*(.006+.015*math.sin(math.pi*t))*(1-.45*abs(u))
 return (width*u,y,z)
membrane('sculpted_tail_fin',tail)
for sign in [-1,1]:
 def side(t,u,s,sign=sign):return (sign*(.205+.245*t),.025-.14*t+u*.125*math.sin(math.pi*t),.465-.10*t+.018*math.sin(math.pi*t)+s*(.004+.018*math.sin(math.pi*t))*(1-.45*abs(u)))
 membrane('sculpted_side_fin_'+str(sign),side)
def dorsal(t,u,s):
 y=.20-.78*t;v=(u+1)/2;rx,rz=radii(max(-.62,min(.52,y)));base=.44+rz*.94;rise=.22*math.sin(math.pi*t)**.8
 return (s*(.003+.028*math.sin(math.pi*v))*math.sin(math.pi*t),y,base+rise*v)
membrane('sculpted_dorsal_fin',dorsal,40,14)

for sign in [-1,1]:
 x=sign*.174
 sphere('eye_white_'+str(sign),(x,.353,.615),(.094,.078,.106),white)
 sphere('eye_iris_'+str(sign),(x,.415,.662),(.058,.034,.061),iris)
 sphere('eye_pupil_'+str(sign),(x,.439,.677),(.035,.018,.041),pupil)
 sphere('eye_glint_'+str(sign),(x-sign*.013,.455,.699),(.010,.008,.012),glint)
sphere('mouth_muzzle',(0,.493,.410),(.074,.032,.046),lip)
sphere('mouth_inset',(0,.519,.413),(.041,.012,.020),mouth)

sc=bpy.context.scene;sc.name='Creature Fish Round01 Native';sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1792;sc.render.resolution_y=2048;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.fps=12;sc.frame_start=1;sc.frame_end=12
cam=bpy.data.objects.new('Fish registered character camera',bpy.data.cameras.new('Fish registered character camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=.21428516507148743
el=math.radians(35);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
def light(name,pos,energy,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=(1.,.965,.91);o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location+Vector((0,0,.43))).to_track_quat('-Z','Y').to_euler()
light('Soft centered overhead',(0,0,4),330,5)
for i in range(4):a=math.pi*i/2;light('Equal cardinal broad '+str(i),(3*math.cos(a),3*math.sin(a),2.0),105,4)
sc.world=bpy.data.worlds.new('Fish neutral soft ambient');sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.78,.84,1.,1);bg.inputs['Strength'].default_value=.32
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15;sc.render.dither_intensity=0;sc.render.use_compositing=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.threads_mode='FIXED';sc.render.threads=4
if hasattr(sc,'eevee'):
 for k in ['taa_render_samples','taa_samples']:
  if hasattr(sc.eevee,k):setattr(sc.eevee,k,32)
sc['asset']='creature-fish';sc['scope']='native BODY only';sc['round']=1;sc['actionRepair']='Euler-compatible native bones; source bone rotation channels multiplied .58; source object motion retained';sc['pixelFilter']='native render; publication whole-canvas LANCZOS4x→2x; no RGB or alpha repairs'
rt.apply('normal',1,'S');bpy.context.view_layer.update()
out=P/'round-01-development-v01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
camera=rt.camera_record();(OUT/'camera.json').write_text(json.dumps(camera,indent=2)+'\n')
for d in rt.FACING:
 rt.apply('normal',1,d);sc.render.filepath=str(OUT/(d+'.png'));bpy.ops.render.render(write_still=True)
print('FISH_BUILD_COMPLETE',str(out),flush=True)
