import bpy, math, json, hashlib, bmesh
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]
SOURCE=(BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
OUT=BASE/'candidates/draft'; OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
original_hash=sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
oldscene=bpy.context.scene
scene=bpy.data.scenes.new('stool-blue isolated scene');bpy.context.window.scene=scene
collection=bpy.data.collections['S33_PROP_stool_blue.001']; root=bpy.data.objects['stool_blue__root.001']
parts=list(collection.all_objects)
if collection.name not in scene.collection.children: scene.collection.children.link(collection)
collection.hide_render=False;collection.hide_viewport=False
for o in parts: o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
print('LAYER', [(o.name,list(o.matrix_world.translation),o.visible_get()) for o in parts])
def bounds(objs):
 pts=[]; dep=bpy.context.evaluated_depsgraph_get()
 for o in objs:
  if o.type=='MESH':
   e=o.evaluated_get(dep); m=e.to_mesh(); pts += [e.matrix_world@v.co for v in m.vertices]; e.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
source_bounds=bounds(parts)
original_parts=[{'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'bounds':bounds([o]) if o.type=='MESH' else None,'meshVertices':len(o.data.vertices) if o.type=='MESH' else None} for o in parts]
keep={o.name for o in parts}
for o in list(bpy.data.objects):
 if o.name not in keep: bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=collection: bpy.data.collections.remove(c)
for o in parts: o.hide_render=False; o.hide_viewport=False; o.hide_set(False)
collection.hide_render=False;collection.hide_viewport=False
if collection.name not in scene.collection.children: scene.collection.children.link(collection)
bpy.context.view_layer.update()
scene.name='stool-blue warm soft native';scene.use_nodes=False
# Color and procedural variation stay in the editable native materials.
def linear(c): return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def color(h): return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def material(name,hexcolor,roughness=.65,wood=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['base_srgb']='#'+hexcolor
 n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Base Color'].default_value=color(hexcolor);bs.inputs['Roughness'].default_value=roughness;bs.inputs['Specular IOR Level'].default_value=.24
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=7 if wood else 145;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.65
 coord=n.new('ShaderNodeTexCoord');vec=coord.outputs['Generated']
 if wood:
  scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(5,5,.3);l.new(vec,scale.inputs[0]);vec=scale.outputs['Vector']
 l.new(vec,tex.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[1].position=.9
 base=color(hexcolor)
 ramp.color_ramp.elements[0].color=tuple(v*.94 for v in base[:3])+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,v*1.035) for v in base[:3])+(1,)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.045 if wood else .025;bump.inputs['Distance'].default_value=.002 if wood else .0007;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return m
blue=material('stool-blue warm soft cushion','197FD9',.56)
baseblue=material('stool-blue warm soft lower upholstery','1978CC',.65)
wood=material('stool-blue warm honey wood','D28D3D',.71,True)
# Closed rounded-square rings preserve the two authored upholstery parts and exact outer envelope.
def ring(a,corner,z,steps=12):
 pts=[]
 for sx,sy,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
  cx=sx*(a-corner);cy=sy*(a-corner)
  for k in range(steps+1):
   th=math.radians(start+k*90/steps);pts.append((cx+corner*math.cos(th),cy+corner*math.sin(th),z))
 return pts
# Above centers order wrong for corner starts? Positive-positive arc 0 to90 then negative-positive90to180: contiguous CCW.
def set_rings(o,spec,mat,top=True):
 vs=[];faces=[];n=52
 for a,c,z in spec:vs.extend(ring(a,c,z))
 for j in range(len(spec)-1):
  for k in range(n):
   p=j*n+k;q=j*n+(k+1)%n;r=(j+1)*n+(k+1)%n;s=(j+1)*n+k;faces.append((p,q,r,s))
 faces.append(tuple(reversed(range(n))));faces.append(tuple((len(spec)-1)*n+k for k in range(n)))
 me=bpy.data.meshes.new(o.name+' padded native mesh');me.from_pydata(vs,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
 o.data=me;o.location=(0,0,0);o.rotation_euler=(0,0,0);o.modifiers.clear();me.materials.clear();me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
# bottom to top rings; all remain inside original upholstery envelopes.
seat=bpy.data.objects['stool_blue__seat.001']
set_rings(seat,[(.300,.046,.510),(.318,.052,.516),(.329,.058,.535),(.330,.060,.567),(.327,.060,.606),(.307,.054,.633),(.282,.048,.650)],baseblue)
top=bpy.data.objects['stool_blue__cushion_top.001']
set_rings(top,[(.285,.047,.635),(.302,.052,.639),(.310,.056,.646),(.307,.055,.652),(.289,.052,.659),(.250,.048,.668),(.190,.039,.678),(.120,.028,.683),(.045,.012,.685)],blue)
for o in parts:
 if o.type=='MESH' and o not in (seat,top):
  o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(wood)
  for mod in o.modifiers:
   if mod.type=='BEVEL':mod.segments=6;mod.harden_normals=True
  for p in o.data.polygons:p.use_smooth=True
  w=o.modifiers.new('Warm soft weighted face normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=50
# Native lighting is a neutral world plus one overhead and four identical cardinal area fills.
scene.world=bpy.data.worlds.new('stool-blue neutral soft world');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.25
def area(name,loc,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=(1,.965,.91)
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.35))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Soft neutral overhead',(0,0,4.5),110,4.5)
for k in range(4):
 a=math.pi*.5*k;area('Equal cardinal fill '+str(k),(3*math.cos(a),3*math.sin(a),2.2),50,5)
# Reconstruct the object source camera; active source scene was an unrelated 35-degree character camera.
data=bpy.data.cameras.new('stool-blue registered square camera');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=math.sqrt(1+.7*.7);scene.render.pixel_aspect_y=1
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
elevation=math.atan(1/.7);cam.location=(0,-10*math.cos(elevation),10*math.sin(elevation));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=cam.data.shift_y=0
bpy.context.view_layer.update()
def pixel(p):
 v=world_to_camera_view(scene,cam,Vector(p));return Vector((v.x*384,(1-v.y)*704))
origin=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-origin.y;cam.data.shift_y=(496-origin.y)/dy;bpy.context.view_layer.update()
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.fps=12;scene.frame_start=scene.frame_end=1;scene.frame_set(1)
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.filepath=str(OUT/'static-N.png');bpy.ops.render.render(write_still=True)
print('MEASURED',json.dumps({'sourceBounds':source_bounds,'candidateBounds':bounds(parts),'root':list(pixel((0,0,0))),'unitX':list(pixel((1,0,0))-pixel((0,0,0))),'unitDepth':list(pixel((0,-1,0))-pixel((0,0,0))),'unitHeight':list(pixel((0,0,1))-pixel((0,0,0))),'cameraShift':cam.data.shift_y}))
