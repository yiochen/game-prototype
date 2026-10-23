import bpy, math, json, sys, hashlib, importlib.util
from mathutils import Vector, Matrix
from pathlib import Path
D=Path(__file__).resolve().parent; RES=D/'resources'; P=D.parent.parent
MODE=sys.argv[-1] if sys.argv[-1] in ['main','runtime'] else 'main'
rig=json.loads((RES/('source-'+MODE+'-rig.json')).read_text())
root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in bpy.data.collections if root in list(c.all_objects) and c.name.startswith('S33_CHARACTER_' if MODE=='main' else 'S10 meal S33_CHARACTER_'))
oldscene=next(s for s in bpy.data.scenes if root in list(s.objects));cam=oldscene.camera
scene=bpy.data.scenes.new('Samir Warm Soft Round 01 '+MODE)
scene.collection.children.link(collection);collection.hide_render=False;collection.hide_viewport=False
scene.collection.objects.link(cam);scene.camera=cam
bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
for l in scene.view_layers:
 def expose(x):
  x.exclude=False;x.hide_viewport=False
  for c in x.children:expose(c)
 expose(l.layer_collection)
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
cam.matrix_world=Matrix(json.loads((RES/'source-camera.json').read_text())['camera']['worldMatrix'])
cam.data.shift_x=0;cam.data.shift_y=.4583320518334706
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=384;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=50
scene.render.fps=12;scene.render.use_compositing=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world=bpy.data.worlds.new('Samir warm soft neutral world');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.32,.35,.4,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
# No ground geometry; horizontal symmetry is intrinsic to the lighting rig.
def light(name,pos,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
light('Samir soft overhead',(0,0,4.5),300,4.5,(1,.95,.86))
for i in range(4):
 a=i*math.pi/2;light('Samir soft cardinal '+str(i),(3*math.cos(a),3*math.sin(a),2.5),125,4,(1,.97,.91))
arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
body=[o for o in collection.all_objects if o.type=='MESH' and o.get('weighted_character_geometry')]
def part(o):return o.name.split('customer_samir__',1)[1].split('.')[0]
parts={part(o):o for o in body}
def lin(c):return ((c+.055)/1.055)**2.4 if c>.04045 else c/12.92
def mat(name,hex,rough=.62,spec=.24):
 m=bpy.data.materials.new('Samir R01 '+name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');b=n.new('ShaderNodeBsdfPrincipled');m.node_tree.links.new(b.outputs['BSDF'],out.inputs['Surface'])
 col=tuple(lin(int(hex[i:i+2],16)/255) for i in [0,2,4])+(1,)
 b.inputs['Base Color'].default_value=col;b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=spec
 b.inputs['Emission Color'].default_value=col;b.inputs['Emission Strength'].default_value=.045
 return m
palette={'green':mat('green shirt','229D59',.7),'skin_samir':mat('warm tan skin','C78346',.65),'hair_black':mat('blue black hair','1E2A41',.58),'2D3542':mat('hair variation','24324B',.6),'orange':mat('golden yellow cap','FFCA38',.58),'blush':mat('soft blush','E89372',.72),'eye':mat('dark eye','29170D',.35,.35),'white':mat('eye glint','FFF6DC',.42),'navy':mat('navy trousers','243D68',.7),'teal':mat('teal front panel','159EA8',.67)}
shoe=mat('blue black shoe','202C43',.6);trim=mat('cap seam gold','ECAF24',.7);collar=mat('collar green','279E58',.7)
for o in body:
 for i,m in enumerate(o.data.materials):
  key=m.name.split('S33_CHAR_')[-1]
  if key in palette:o.data.materials[i]=palette[key]
 if part(o).startswith('minimal_foot'):o.data.materials.clear();o.data.materials.append(shoe)
 for f in o.data.polygons:f.use_smooth=True
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=8;m.harden_normals=True
 # Area weighted normals hold broad front planes while bevels turn gently.
 if any(m.type=='BEVEL' for m in o.modifiers) and not any(m.type=='WEIGHTED_NORMAL' for m in o.modifiers):
  w=o.modifiers.new('R01 broad plane normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=50
  o.modifiers.move(len(o.modifiers)-1, max(0,len(o.modifiers)-2))
def bounds(o):
 vs=[v.co for v in o.data.vertices];return Vector([min(v[i] for v in vs) for i in range(3)]),Vector([max(v[i] for v in vs) for i in range(3)])
def replace(o,verts,faces,group=None):
 mats=list(o.data.materials);me=bpy.data.meshes.new(o.name+' refined native mesh');me.from_pydata(verts,[],faces);me.update();o.data=me
 for m in mats:me.materials.append(m)
 if group:
  g=o.vertex_groups.get(group) or o.vertex_groups.new(name=group);g.add(list(range(len(verts))),1,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 return o
def ellipsoid(o):
 lo,hi=bounds(o);c=(lo+hi)*.5;r=(hi-lo)*.5
 verts=[];N=32;M=16
 for j in range(M+1):
  t=math.pi*j/M
  for i in range(N):
   a=2*math.pi*i/N;verts.append(tuple(c+Vector((r.x*math.sin(t)*math.cos(a),r.y*math.sin(t)*math.sin(a),r.z*math.cos(t)))))
 faces=[]
 for j in range(M):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 replace(o,verts,faces,o.vertex_groups[0].name)
for k,o in parts.items():
 if any(k.startswith(s) for s in ['cropped_','rounded_','mustache_','eye_','cheek_']):ellipsoid(o)
for k in ['cap_crown','cap_brim','cap_button','head','palm_L','palm_R','nose','thumb_L','thumb_R','ear_-1','ear_1','minimal_foot_L','minimal_foot_R']:
 o=parts[k]
 for m in o.modifiers:
  if m.type=='BEVEL':
   if k=='cap_crown':m.width=.063;m.segments=12
   if k=='cap_button':m.width=.012;m.segments=8
   if k.startswith('palm'):m.width=.03
   if k=='nose':m.width=.022
# The bill is a solid bowed form, independently controlled in X and depth.
o=parts['cap_brim'];verts=[];N=32
for zadd in [0,-.038]:
 for back in [False,True]:
  for i in range(N+1):
   x=-.264+.528*i/N;t=x/.264;y=(-.108 if back else -.288)+(.010 if back else .025)*t**4;z=.945-.012*t*t+zadd
   verts.append((x,y,z))
faces=[];stride=N+1
for s in [0,2*stride]:
 for i in range(N):faces.append((s+i,s+i+1,s+stride+i+1,s+stride+i) if s==0 else (s+i,s+stride+i,s+stride+i+1,s+i+1))
for edge in [0,stride]:
 for i in range(N):faces.append((edge+i,edge+i+2*stride,edge+i+2*stride+1,edge+i+1))
faces.extend([(0,stride,3*stride,2*stride),(N,N+2*stride,N+3*stride,N+stride)])
replace(o,verts,faces,'head')
for m in o.modifiers:
 if m.type=='BEVEL':m.width=.006;m.segments=5
# Tailored collar leaves are visible solid wedges, with restrained edge rounding.
for side in [-1,1]:
 o=parts['collar_'+str(side)];poly=[(side*.009,-.150,.407),(side*.103,-.140,.408),(side*.094,-.183,.338),(side*.028,-.180,.368)]
 verts=poly+[(x,y+.010,z) for x,y,z in poly];faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
 replace(o,verts,faces,'spine');o.data.materials.clear();o.data.materials.append(collar)
# Garment and limb bevels smooth structural edges while preserving the rig weights.
for key in ['tailored_tunic','arm_L','arm_R','leg_L','leg_R']:
 o=parts[key];m=o.modifiers.new('R01 garment rounded edge','BEVEL');m.width=.007 if key!='tailored_tunic' else .012;m.segments=5;m.harden_normals=True
 o.modifiers.move(len(o.modifiers)-1,0)
 w=o.modifiers.new('R01 garment normals','WEIGHTED_NORMAL');w.keep_sharp=True;o.modifiers.move(len(o.modifiers)-1,1)
# Purposeful cap seam: native tubular piping, rigidly weighted to the head.
def seam(name,points,radius,material,bone):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=3
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for pt,co in zip(sp.points,points):pt.co=(*co,1)
 ob=bpy.data.objects.new(name,cu);collection.objects.link(ob);ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4);ob.location=(0,0,0)
 # Convert into weighted geometry for portable native armature evaluation.
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob=bpy.context.object;ob.select_set(False)
 ob['weighted_character_geometry']=True;ob.data.materials.append(material);g=ob.vertex_groups.new(name=bone);g.add(list(range(len(ob.data.vertices))),1,'REPLACE');mo=ob.modifiers.new('Native unchanged rig','ARMATURE');mo.object=arm
 for p in ob.data.polygons:p.use_smooth=True
 return ob
# Native thin bill seam just inside the front edge, restrained at logical size.
seam(('S10 meal ' if MODE=='runtime' else '')+'customer_samir__R01_bill_seam',[(x,-.279+.025*(x/.264)**4,.945-.012*(x/.264)**2+.0015) for x in [-.235+.47*i/48 for i in range(49)]],.0015,trim,'head')
# The existing food owner/actions stay intact; only canonical image mapping and one ray-depth scalar change.
plane=next(o for o in collection.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
food='cucumber' if MODE=='main' else 'salmon';mapping=json.loads((RES/'food-mapping-proposal.json').read_text())['proposals'][food]['thresholdSensitivity']['128']
for v,co in zip(plane.data.vertices,mapping['newFullUVLocalVertices']):v.co=co
uvs=[(0,0),(1,0),(1,1),(0,1)]
for p in plane.data.polygons:
 for li in p.loop_indices:plane.data.uv_layers.active.data[li].uv=uvs[plane.data.loops[li].vertex_index]
image_path=RES/('dish-'+food+'-canonical.png');im=bpy.data.images.load(str(image_path),check_existing=False);im.name='Samir exact approved 2D '+food;im.pack(data=image_path.read_bytes(),data_len=image_path.stat().st_size);im.filepath='//resources/'+image_path.name
for m in plane.data.materials:
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE':n.image=im;n.interpolation='Linear';n.extension='CLIP'
# Depth=.30 world cells, not per-view fitting. Local scale is 1.25; ray is registered camera ray.
depth=.30;local=depth/1.25;offsetY=local*.8191520442889918;offsetZ=local*.573576436351046
plane.location.z=offsetZ
for f in plane.animation_data.drivers:
 if f.data_path=='location' and f.array_index==0:f.driver.expression='-sin(facing)*'+repr(offsetY)
 if f.data_path=='location' and f.array_index==1:f.driver.expression='-cos(facing)*'+repr(offsetY)
plane['R01 food policy']='Exact canonical packed2D, alpha128 semantic edge mapping, fullUV, depth .30 world cells, fixed for every sample.'
spec=importlib.util.spec_from_file_location('samir_native',RES/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset={'root':root,'collection':collection};native.apply_clip(asset,rig,next(iter(rig['clips'])),1,'S',scene)
scene['refinementRecipe']='source/round-01/refine.py';scene['foodRepresentation']='Packed canonical2D raster, explicitly not modeled3D food';scene['captureScale']=2
# Packed dependency closure for the isolated scene; images are never re-encoded.
images=set()
for ob in collection.all_objects:
 for m in getattr(ob.data,'materials',[]):
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:images.add(n.image)
for im in images:
 if not im.packed_file:im.pack()
actions={bpy.data.actions[t['action']] for c in rig['clips'].values() for t in c['actions']}
out=D/('samir-'+MODE+'.blend');bpy.data.libraries.write(str(out),{scene,*actions},fake_user=True,compress=True)
report={'mode':MODE,'output':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bodyMeshCount':sum(o.type=='MESH' and bool(o.get('weighted_character_geometry')) for o in collection.all_objects),'actions':sorted(a.name for a in actions),'food':{'type':'exact packed2D raster','composition':food,'sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'mapping':mapping,'depthWorldCells':depth},'light':'300W broad overhead + four symmetric125W area disks, no ground geometry','materials':{k:m.name for k,m in palette.items()},'sourceRigRestAndActions':'Unmodified; all-frame independent baseline comparison follows.'}
(D/('build-'+MODE+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print('BUILT',out,flush=True)
