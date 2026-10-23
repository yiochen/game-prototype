import bpy, bmesh, math, json, sys, hashlib, random
from pathlib import Path
from mathutils import Matrix,Vector
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
SOURCEDATA=json.loads((BASE/'inputs/source-camera.json').read_text())
# Isolate this one native asset; original-backup.blend remains byte-for-byte untouched.
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='column-broken warm soft round 03'
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.cycles.seed=31
sc.render.threads_mode='FIXED';sc.render.threads=6
sc.render.resolution_x=768;sc.render.resolution_y=1280;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1;sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=100;sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('Neutral soft environment');sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.78,.80,.82,1);bg.inputs['Strength'].default_value=.45
col=bpy.data.collections.new('S33_PROP_column-broken');sc.collection.children.link(col)
root=bpy.data.objects.new('column-broken__root',None);col.objects.link(root)
root['production_id']='column-broken';root['refinementRound']=3;root['static']=True

def move(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root;return o

def mat(name,base,rough=.8,noise=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*base,1);m.use_nodes=True;n=m.node_tree.nodes;links=m.node_tree.links
 bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*base,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.23
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=7;tex.inputs['Detail'].default_value=1.5;tex.inputs['Roughness'].default_value=.6
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[1].position=.80
  ramp.color_ramp.elements[0].color=(*[c*.89 for c in base],1);ramp.color_ramp.elements[1].color=(*[min(1,c*1.07) for c in base],1)
  links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 return m
stone=mat('Warm ivory limestone',(.72,.672,.568),.78,True)
edge=mat('Lighter chalk fracture stone',(.76,.71,.61),.8,True)
fracture=mat('Warm gray limestone fracture recess',(.46,.435,.375),.88)
moss=mat('Living olive lime moss',(.30,.40,.045),.86,True)
moss2=mat('Moss young tips',(.31,.42,.035),.82,True)

# Beveled native mesh geometry rather than shader-only silhouette rounding.
def mesh(name,vs,fs,material,bevel=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;o.data.materials.append(material)
 if bevel:
  b=o.modifiers.new('Broad worn stone arris','BEVEL');b.width=bevel;b.segments=3;b.affect='EDGES'
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=b.name);o.select_set(False)
 for f in o.data.polygons:f.use_smooth=True
 n=o.modifiers.new('Area weighted stone normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=40
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=n.name);o.select_set(False)
 return o

def prism(name,outline,z0,tops,material,bev):
 vs=[(x,y,z0) for x,y in outline]+[(x,y,z) for (x,y),z in zip(outline,tops)]
 n=len(outline);fs=[tuple(reversed(range(n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(range(n,2*n))]
 return mesh(name,vs,fs,material,bev)

# Substantial 1x1 squared plinth; grounded lower rim is not rounded upward.
outline=[(-.44,-.5),(.43,-.5),(.5,-.43),(.5,.43),(.43,.5),(-.43,.5),(-.5,.43),(-.5,-.43)]
base=prism('One-piece worn square plinth',outline,0,[.235,.25,.242,.25,.24,.235,.25,.23],stone,.035)
# Native top step and eight-sided shaft with a deliberately uneven broken crown.
step=[(-.35,-.405),(.31,-.405),(.405,-.31),(.405,.32),(.32,.405),(-.32,.405),(-.405,.32),(-.405,-.32)]
prism('Weathered shoulder supporting shaft',step,.215,[.33,.34,.33,.335,.33,.32,.335,.32],edge,.027)
shaft_outline=[(-.245,-.345),(.225,-.345),(.345,-.225),(.345,.235),(.235,.345),(-.235,.345),(-.345,.235),(-.345,-.245)]
shaft=prism('Fractured monolithic column',shaft_outline,.285,[1.625,1.66,1.71,1.69,1.72,1.685,1.75,1.695],stone,0)
shaft.data.materials.append(fracture)

def groove(name,points,width,side=0):
 # A shallow actual subtraction. Bottom remains warm gray stone, never black paint.
 vs=[]
 left=[];right=[]
 for i,(u,z) in enumerate(points):
  f=(1-.5*i/max(1,len(points)-1));left.append((u-width*f,z));right.append((u+width*f,z))
 poly=left+list(reversed(right));N=len(poly)
 for depth in ([-.56,-.43] if shaft==base else [-.405,-.275]):
  for u,z in poly:
   x,y=u,depth;a=side*math.pi/2;vs.append((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z))
 fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 cut=mesh(name,vs,fs,fracture,0);cut.data.materials.clear();cut.data.materials.append(fracture)
 # Give cutter fracture material matching target slot index.
 cut.data.materials.clear();cut.data.materials.append(stone);cut.data.materials.append(fracture)
 for f in cut.data.polygons:f.material_index=1
 bo=shaft.modifiers.new(name,'BOOLEAN');bo.operation='DIFFERENCE';bo.solver='EXACT';bo.object=cut
 bpy.context.view_layer.objects.active=shaft;shaft.select_set(True);bpy.ops.object.modifier_apply(modifier=bo.name);shaft.select_set(False);bpy.data.objects.remove(cut,do_unlink=True)

for side in range(4):
 shift=[0,.05,-.035,.02][side]
 groove('Upper natural fracture '+str(side),[(-.14+shift,1.80),(-.12+shift,1.52),(-.025+shift,1.30),(.015+shift,1.13),(.16+shift,1.04),(.27, .91)],.019,side)
 groove('Lower diagonal fracture '+str(side),[(-.29,.88),(-.21,.75),(-.07,.65),(.035,.47),(.17,.285)],.014,side)
# Soften every exposed arris, including the real crack shoulders.
b=shaft.modifiers.new('Soft chipped fracture lips','BEVEL');b.width=.021;b.segments=3
bpy.context.view_layer.objects.active=shaft;shaft.select_set(True);bpy.ops.object.modifier_apply(modifier=b.name);shaft.select_set(False)
for f in shaft.data.polygons:f.use_smooth=True
n=shaft.modifiers.new('Preserve broad limestone planes','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=55
bpy.context.view_layer.objects.active=shaft;shaft.select_set(True);bpy.ops.object.modifier_apply(modifier=n.name);shaft.select_set(False)

# Real shallow irregular plinth fractures with softened native lips.
mainshaft=shaft;shaft=base
for side in range(4):
 groove('Worn foot fracture '+str(side),[(-.29,.30),(-.255,.20),(-.34,.11),(-.36,-.02)],.012,side)
b=base.modifiers.new('Soft plinth chipped lips','BEVEL');b.width=.009;b.segments=2
bpy.context.view_layer.objects.active=base;base.select_set(True);bpy.ops.object.modifier_apply(modifier=b.name);base.select_set(False)
shaft=mainshaft
# Broad crown chips and settled rubble add purposeful broken construction.
prism('Broken crown rear ledge',[(-.265,.105),(.12,.105),(.15,.265),(-.24,.31),(-.31,.23)],1.62,[1.75,1.735,1.755,1.78,1.76],edge,.024)
random.seed(31)
for i,(x,y,z,rx,ry,h) in enumerate([(-.28,-.32,.25,.095,.075,.12),(.22,-.34,.24,.115,.07,.095),(.33,.23,.24,.08,.105,.12),(-.34,.27,.24,.08,.075,.13)]):
 outline=[(x+rx*math.cos(j*math.tau/6),y+ry*math.sin(j*math.tau/6)) for j in range(6)]
 prism('Settled limestone chip '+str(i),outline,z,[z+h*(.85+random.random()*.2) for j in range(6)],edge,.02)

# Organic continuous moss clusters are merged ellipsoidal volumes, no bright cubes.
def moss_patch(name,lobes,material):
 obs=[]
 for x,y,z,sx,sy,sz in lobes:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=(x,y,z));o=move(bpy.context.object);o.name=name+' lobe';o.scale=(sx,sy,sz)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);obs.append(o)
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=obs[0];o.name=name
 rem=o.modifiers.new('Connected organic moss volume','REMESH');rem.mode='VOXEL';rem.voxel_size=.012;rem.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=o.modifiers.new('Soft moss skin','SMOOTH');sm.factor=.75;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
 o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 o.select_set(False);return o
# Crown: low cushion plus hanging tongues integrated at actual top edges.
moss_patch('Rear-left crown moss', [(-.22,.18,1.755,.105,.12,.066),(-.265,.10,1.72,.08,.10,.085),(-.30,.075,1.665,.061,.07,.10),(-.28,.20,1.78,.067,.095,.065)],moss2)
moss_patch('Right crown moss',[ (.235,-.15,1.70,.09,.12,.068),(.31,-.12,1.645,.06,.095,.095),(.32,-.13,1.57,.048,.065,.075)],moss2)
moss_patch('Rear crown moss',[(.10,.26,1.73,.105,.095,.065),(.07,.305,1.67,.07,.055,.09)],moss)
# Four distinct climbing tracks lie against the body, narrower than the stone masses.
for side in range(4):
 a=side*math.pi/2;seq=[]
 for u,z,sx,sz in [(-.20,.37,.09,.11),(-.245,.48,.07,.12),(-.26,.65,.065,.11),(-.22,.77,.07,.10),(-.275,.86,.07,.10)]:
  x,y=u,-.334;seq.append((x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z,sx if side%2==0 else .055,.055 if side%2==0 else sx,sz))
 moss_patch('Crevice-following moss '+str(side),seq,moss)
# Resting patches on plinth, kept inside physical footprint.
for i,(x,y,z) in enumerate([(-.36,-.35,.245),(.30,.31,.25),(-.34,.30,.24),(.32,-.35,.245)]):
 moss_patch('Plinth cushion '+str(i),[(x,y,z,.115,.10,.055),(x*.94,y*.94,z+.025,.10,.08,.055)],moss)

# Exact source camera matrix/projection and root registration.
cam=bpy.data.objects.new('S33 registered 35 degree camera',bpy.data.cameras.new('S33 registered 35 degree camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(SOURCEDATA['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.4583320617675781
for name,loc,power,size in [('Soft centered overhead',(0,0,4.5),75,4.0)]+[(f'Equal cardinal fill {i}',(3*math.cos(i*math.pi/2),3*math.sin(i*math.pi/2),2),45,4.0) for i in range(4)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location+Vector((0,0,.8))).to_track_quat('-Z','Y').to_euler()
sc['captureFootingTransition']=.42;sc['captureFootingPolicy']='after facing rotation: worldY *= 1+(csc35-1)*max(0,1-max(0,z)/.42)^2'
sc['sourceRootObject']=root.name;sc['assetCollection']=col.name
sc.frame_set(1);bpy.context.view_layer.update()
# Only this native dependency-closed asset is saved; procedural materials need no files.
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source/round-03.blend'))
# Render via same portable source script used for replay.
exec(compile((BASE/'source/replay-round-03.py').read_text(),str(BASE/'source/replay-round-03.py'),'exec'))
