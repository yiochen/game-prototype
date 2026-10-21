import bpy,math,json,pathlib,hashlib,sys
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1]; OUT=P/'candidates'/'round-01';OUT.mkdir(parents=True,exist_ok=True)
b=json.load(open(P/'brief.json'));src=(P/b['source']['project']).resolve();bpy.ops.wm.open_mainfile(filepath=str(src))
c=bpy.data.collections['S33_FB_belt-straight-n.001'];scene=bpy.data.scenes.new('BeltRegisteredCapture');bpy.context.window.scene=scene;scene.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False);o.update_tag()
scene.frame_set(1);bpy.context.view_layer.update();root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name)
# Retain actual native root, authored child orientation, flat deck UV and original phase action.
phaseMat=deck.data.materials[0];phase=phaseMat.node_tree.nodes['Value'];phase.label='Deck travel phase — original native -7*i/24 action retained'
for o in list(c.objects):
 if 'wood_leg' in o.name or 'lower_wood_frame' in o.name:bpy.data.objects.remove(o,do_unlink=True)
# Native materials: all common across directions; detail coordinate follows authored orientation.
def srgb(h):
 h=h.lstrip('#');v=[int(h[i:i+2],16)/255 for i in (0,2,4)];return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)+(1,)
def material(name,color,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;sh=n.get('Principled BSDF');sh.inputs['Base Color'].default_value=srgb(color);sh.inputs['Roughness'].default_value=rough;sh.inputs['Metallic'].default_value=metal;sh.inputs['Specular IOR Level'].default_value=.25;return m
rail=material('WarmSoft_CoralRail','#DA8065',.35);rail.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.12
wood=material('WarmSoft_HoneyWood','#B87A38',.48);n=wood.node_tree.nodes;l=wood.node_tree.links;sh=n.get('Principled BSDF');tex=n.new('ShaderNodeTexCoord');tex.object=orient;mp=n.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(21,21,2);l.new(tex.outputs['Object'],mp.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=1.4;noise.inputs['Roughness'].default_value=.6;l.new(mp.outputs[0],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.16;r.color_ramp.elements[0].color=srgb('#9E632E');r.color_ramp.elements[1].position=.84;r.color_ramp.elements[1].color=srgb('#CC914A');l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],sh.inputs['Base Color'])
shoe=material('WarmSoft_WoodFoot','#89512A',.52);brass=material('WarmSoft_BrassFastener','#D49B45',.34,.45)
def link_obj(o):
 for cc in list(o.users_collection):cc.objects.unlink(o)
 c.objects.link(o);o.parent=orient;return o
def box(name,loc,scale,mat,bev=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=link_obj(bpy.context.object);o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bev:
  mod=o.modifiers.new('Crafted round edges','BEVEL');mod.width=bev;mod.segments=4;mod.affect='EDGES';mod.harden_normals=True
  wn=o.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=40
 return o
for x in [-.28,.28]:
 for y in [-.28,.28]:
  box('Crafted_leg_%s_%s'%(x,y),(x,y,.245),(.18,.18,.49),wood,.021)
  box('Ground_shoe_%s_%s'%(x,y),(x,y,.04),(.198,.198,.08),shoe,.017)
for y in [-.28,.28]:box('Honey_crossbeam_%s'%y,(0,y,.495),(.75,.18,.13),wood,.022)
for x in [-.28,.28]:box('Honey_sidebeam_%s'%x,(x,0,.49),(.18,.74,.12),wood,.018)
# Small domed construction pegs mounted on all outward frame faces, below rail/deck clearance.
for axis in (0,1):
 for sign in [-1,1]:
  for p in [-.28,.28]:
   loc=[p,sign*.376,.493] if axis==1 else [sign*.376,p,.493]
   bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);o=link_obj(bpy.context.object);o.name='Brass_joinery_peg';o.scale=(.018,.009,.018) if axis==1 else (.009,.018,.018);o.data.materials.append(brass)
   for f in o.data.polygons:f.use_smooth=True
# Rectangular open rail cross sections are exact. Split corner normals give a broad rounded light shoulder without changing ports.
for o in [o for o in c.objects if 'stationary_rail' in o.name]:
 old=o.data;vs=[(-.065,-.5,-.095),(.065,-.5,-.095),(.065,-.5,.095),(-.065,-.5,.095),(-.065,.5,-.095),(.065,.5,-.095),(.065,.5,.095),(-.065,.5,.095)]
 fs=[(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)] # intentionally open exact joining planes
 me=bpy.data.meshes.new('Exact_open_rectangular_rail');me.from_pydata(vs,[],fs);me.update();o.data=me;me.materials.append(rail)
 normals=[]
 for f in me.polygons:
  f.use_smooth=True
  for vid in f.vertices:
   v=Vector(vs[vid]);
   if f.index==2:normal=Vector((.52*(1 if v.x>0 else -1),0,.854))
   elif f.index in (1,3):normal=Vector(((.9 if v.x>0 else -.9),0,.38*(1 if v.z>0 else -1)))
   else:normal=Vector((.4*(1 if v.x>0 else -1),0,-.92))
   normals.append(normal.normalized())
 me.normals_split_custom_set(normals)
# Continuous softly crowned slat shader on exact original deck; original phase owner/action and UV layout preserved.
n=phaseMat.node_tree.nodes;l=phaseMat.node_tree.links
keep=phase
for node in list(n):
 if node!=keep:n.remove(node)
out=n.new('ShaderNodeOutputMaterial');sh=n.new('ShaderNodeBsdfPrincipled');sh.inputs['Roughness'].default_value=.47;sh.inputs['Specular IOR Level'].default_value=.22
uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0]);mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=7;l.new(sep.outputs['X'],mul.inputs[0]);add=n.new('ShaderNodeMath');add.operation='ADD';l.new(mul.outputs[0],add.inputs[0]);l.new(phase.outputs[0],add.inputs[1]);frac=n.new('ShaderNodeMath');frac.operation='FRACT';l.new(add.outputs[0],frac.inputs[0])
r=n.new('ShaderNodeValToRGB');r.name='Soft_slat_shoulders';r.color_ramp.interpolation='EASE'
colors=[(0,'#263640'),(.055,'#263640'),(.105,'#596D7D'),(.20,'#4C6171'),(.63,'#465B6B'),(.90,'#4A6070'),(.975,'#2C3C47'),(1,'#263640')]
for e in list(r.color_ramp.elements)[2:]:r.color_ramp.elements.remove(e)
for j,(pos,col) in enumerate(colors):
 e=r.color_ramp.elements[j] if j<2 else r.color_ramp.elements.new(pos);e.position=pos;e.color=srgb(col)
l.new(frac.outputs[0],r.inputs[0]);l.new(r.outputs[0],sh.inputs['Base Color'])
# Subtle native bump crown uses periodic same phase; no displaced contacts.
height=n.new('ShaderNodeValToRGB');height.color_ramp.interpolation='EASE'
height.color_ramp.elements[0].position=.03;height.color_ramp.elements[0].color=(0,0,0,1);height.color_ramp.elements[1].position=.22;height.color_ramp.elements[1].color=(1,1,1,1)
e=height.color_ramp.elements.new(.88);e.color=(.8,.8,.8,1);e=height.color_ramp.elements.new(.995);e.color=(0,0,0,1);l.new(frac.outputs[0],height.inputs[0]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.009;l.new(height.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],sh.inputs['Normal']);l.new(sh.outputs[0],out.inputs['Surface'])
# Registered camera restored from source matrix, NOT presentation camera.
camrec=json.load(open(P/'inputs/source-camera.json'));camdata=bpy.data.cameras.new('RegisteredSquareCamera');cam=bpy.data.objects.new('RegisteredSquareCamera',camdata);scene.collection.objects.link(cam);cam.matrix_world=Matrix(camrec['camera']['worldMatrix']);camdata.type='ORTHO';camdata.ortho_scale=2/camrec['camera']['projectionMatrix'][1][1];camdata.shift_y=-camrec['camera']['projectionMatrix'][1][3]/2;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=False;scene.cycles.pixel_filter_type='BOX';scene.cycles.filter_width=1;scene.cycles.seed=41
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU';scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=camrec['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.fps=12;scene.frame_start=1;scene.frame_end=24
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('WarmSoft_symmetrical_world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.86,1,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
# Broad overhead + identical four cardinal fills. No ground or preferred horizontal source.
def area(name,pos,power,size):
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new(name,ld);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
area('Centered broad key',(0,0,4.5),250,5)
for x,y in [(3,0),(-3,0),(0,3),(0,-3)]:area('Equal cardinal fill',(x,y,2.5),100,4)
# Strip unused unrelated library data from this isolated saved source.
for sc in list(bpy.data.scenes):
 if sc!=scene:bpy.data.scenes.remove(sc)
for o in list(bpy.data.objects):
 if o.name not in scene.objects:bpy.data.objects.remove(o,do_unlink=True)
for co in list(bpy.data.collections):
 if co!=c and co.users==0:bpy.data.collections.remove(co)
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
scene.frame_set(1);root.rotation_euler.z=math.pi;bpy.context.view_layer.update()
scene['asset_id']='belt-straight-n';scene['source_project_sha256']=b['source']['projectSHA256'];scene['registered_camera_source']='inputs/source-camera.json';scene['native_phase_function']='-7*(frame-1)/24';scene['authored_child_orientation_radians']=orient.rotation_euler.z
project=P/'source'/'round-01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project))
recipe={'round':1,'source':str(src),'project':str(project),'method':'Native continuous open rectangular rails with rounded corner normals; original flat UV deck and native action with soft procedural slat shoulders; rebuilt beveled ladder frame, warm grain, shoes and attached pegs. No raster retouch.','geometryContracts':{'deck':{'x':[-.35,.35],'y':[-.5,.5],'z':.64},'rails':{'x':[[-.48,-.35],[.35,.48]],'y':[-.5,.5],'z':[.505,.695],'openEnds':True},'authoredChildOrientation':float(orient.rotation_euler.z),'shaderPhase':'-7*i/24','slatPeriods':7},'render':{'engine':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'filter':scene.cycles.pixel_filter_type,'filterWidth':scene.cycles.filter_width,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look},'modelingPolicyVersion':2}
(P/'source'/'round-01-recipe.json').write_text(json.dumps(recipe,indent=2))
scene.render.filepath=str(OUT/'hero-N.png');bpy.ops.render.render(write_still=True)
