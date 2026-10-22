"""Build the self-contained decor-starfish native candidate.
Run: blender -b --python source/round-01-recipe.py
Reproduction inputs: this script, inputs/source-camera.json and source/replay-round-01.py.
The target/original PNGs are reference only and never loaded into Blender.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent.parent
CAM=json.loads((BASE/'inputs/source-camera.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='decor-starfish warm soft round 01'
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=64;sc.cycles.use_denoising=True;sc.cycles.seed=127
sc.render.threads_mode='FIXED';sc.render.threads=6
sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=CAM['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=100;sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('Soft neutral uniform environment');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.80,.80,.80,1);bg.inputs['Strength'].default_value=.5
col=bpy.data.collections.new('S33_PROP_decor-starfish');sc.collection.children.link(col)
root=bpy.data.objects.new('starfish__root',None);col.objects.link(root)
for k,v in {'production_id':'decor-starfish','source':'prop_builders.py::build_starfish; rebuilt native design round01','footprint_cells':'[1,1]','visual_height':.2,'ground_root':'[0,0,0]','sockets':'{}','static':True,'refinementRound':1}.items():root[k]=v

def mat(name,color,rough,spec):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=spec
 return m
orange=mat('Warm coral orange skin',(.88,.185,.018),.38,.24)
bs=orange.node_tree.nodes.get('Principled BSDF');bs.inputs['Coat Weight'].default_value=.14;bs.inputs['Coat Roughness'].default_value=.32
# Gentle large-scale material variation only; no external images, no micro-bump.
n=orange.node_tree.nodes;l=orange.node_tree.links
g=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(g.outputs['Position'],sep.inputs[0]);r=n.new('ShaderNodeMapRange');r.inputs['From Min'].default_value=.02;r.inputs['From Max'].default_value=.15;l.new(sep.outputs['Z'],r.inputs['Value'])
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.66,.075,.009,1);ramp.color_ramp.elements[1].color=(1,.30,.025,1);l.new(r.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
cream=mat('Butter cream raised nodules',(.98,.71,.22),.34,.28)
cream.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.12

def mesh(name,vs,fs,material):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;o.data.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 return o
# Rounded closed 10-corner outline, sampled from quadratic corner arcs.
polygon=[]
for i in range(10):
 a=-math.pi/2+i*math.pi/5;radius=.38 if i%2==0 else .16;polygon.append(Vector((math.cos(a)*radius,math.sin(a)*radius)))
outline=[]
for i,p in enumerate(polygon):
 prev,nxt=polygon[(i-1)%10],polygon[(i+1)%10];f=.15 if i%2==0 else .17
 A=p+(prev-p)*f;B=p+(nxt-p)*f
 for j in range(12):
  t=j/12;outline.append((1-t)**2*A+2*t*(1-t)*p+t*t*B)
 # Straight edge to next corner's arc; intermediate points keep smooth topology density.
 nf=.15 if (i+1)%2==0 else .17;end=nxt+(p-nxt)*nf
 for j in range(12):outline.append(B+(end-B)*(j/12))
scale=.38/max(p.length for p in outline);outline=[p*scale for p in outline];N=len(outline)
# One continuous solid: 33 elliptical cross-section rings plus center poles.
# Radial angle parameter yields a rounded edge tangent, unlike a beveled flat cutout.
vs=[(0,0,.145)];rings=32
for j in range(1,rings):
 phi=math.pi*j/rings;t=math.sin(phi);z=.06+(.085 if phi<math.pi/2 else .035)*math.cos(phi)
 for p in outline:
  a=math.atan2(p.y,p.x);ridge=(.5+.5*math.cos(5*(a+math.pi/2)))**3
  # Subtle native arm spine rising from the hub, vanishing smoothly at the edge.
  zz=z+.010*ridge*t*(1-t) if phi<math.pi/2 else z
  vs.append((p.x*t,p.y*t,zz))
vs.append((0,0,.025));fs=[]
for i in range(N):fs.append((0,1+i,1+(i+1)%N))
for j in range(rings-2):
 a=1+j*N;b=a+N
 for i in range(N):fs.append((a+i,b+i,b+(i+1)%N,a+(i+1)%N))
last=1+(rings-2)*N;pole=len(vs)-1
for i in range(N):fs.append((last+i,pole,last+(i+1)%N))
body=mesh('One continuous puffy five-arm body',vs,fs,orange)
# A central cushion and two graduated nodules per arm, all physically seated.
def nodule(name,x,y,z,radius,h):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(x,y,z));o=bpy.context.object
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.name=name;o.parent=root;o.scale=(radius,radius,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(cream)
 for f in o.data.polygons:f.use_smooth=True
 return o
nodule('Central cream cushion',0,0,.147,.031,.022)
for i in range(5):
 a=-math.pi/2+i*math.tau/5
 for j,(r,rad,h) in enumerate([(.145,.027,.019),(.278,.021,.015)]):
  z=.06+.085*math.sqrt(1-(r/.38)**2)+.010*(r/.38)*(1-r/.38)
  nodule(f'Arm {i+1} seated nodule {j+1}',math.cos(a)*r,math.sin(a)*r,z+.004,rad,h)
# One registered camera, exact object-specific source transform and pixel aspect.
cam=bpy.data.objects.new('Registered object-specific 55.00798 degree camera',bpy.data.cameras.new('Registered55'));sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(CAM['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.clip_start=.1;cam.data.clip_end=1000;cam.data.shift_x=0;cam.data.shift_y=0
bpy.context.view_layer.update()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*768,(1-q.y)*1408))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();cam.data.shift_y=(992-base.y)/(px((0,0,0)).y-base.y);bpy.context.view_layer.update()
for name,loc,power,size in [('Broad centered overhead',(0,0,4.5),100,3.5)]+[(f'Equal cardinal soft fill {i}',(3*math.cos(i*math.pi/2),3*math.sin(i*math.pi/2),2),55,4) for i in range(4)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location+Vector((0,0,.08))).to_track_quat('-Z','Y').to_euler()
sc['sourceRootObject']=root.name;sc['assetCollection']=col.name;sc['nativeCaptureScale']=4;sc['publishedSourceScale']=2;sc['publicationSampling']='Uniform whole-canvas LANCZOS 768x1408 to384x704; no per-facing fitting/recolor'
sc.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-01.blend'))
exec(compile((BASE/'source/replay-round-01.py').read_text(),str(BASE/'source/replay-round-01.py'),'exec'))
