"""Portable native harpoon refinement. Execute with Blender --background --python.
Only builds this standalone scene. Frozen native context is consumed by evidence.py.
"""
import bpy, math, json, pathlib, sys, hashlib
sys.dont_write_bytecode=True
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent
E=P.parent.parent
C=E/'candidates/round-01'
CONTRACT=json.loads((E/'inputs/root-native-contract.json').read_text())
DELTAS=CONTRACT['nativeMotion']['activeDeltaLocalYBySourceFrame']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Harpoon native standalone'
coll=bpy.data.collections.new('CANONICAL__sub-harpoon-mount');sc.collection.children.link(coll)
def adopt(o,name,mat=None,parent=None):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o)
 o.parent=parent or root
 if mat:o.data.materials.append(mat)
 return o
root=bpy.data.objects.new('harpoon__root',None);coll.objects.link(root)
root['asset']='sub-harpoon-mount';root['canonicalFacing']='S'
moving=bpy.data.objects.new('harpoon__recoil_carriage',None);coll.objects.link(moving);moving.parent=root
moving['mapping']='barrel+muzzle and their attached trim receive exact original barrel/muzzle +Y delta about rebuilt neutral geometry'
def mat(name,color,metal=.0,rough=.38,coat=.15):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=.28;b.inputs['Coat Weight'].default_value=coat;b.inputs['Coat Roughness'].default_value=.32
 return m
gold=mat('Harpoon warm yellow enamel',(.95,.56,.018),.12,.32,.22)
goldedge=mat('Harpoon golden edge',(.72,.31,.012),.18,.4,.12)
red=mat('Harpoon coral pressure housing',(.72,.045,.022),.06,.35,.18)
redcap=mat('Harpoon warm red end',(.51,.028,.016),.1,.4,.12)
steel=mat('Harpoon cool gunmetal',(.115,.185,.26),.48,.32,.13)
silver=mat('Harpoon soft silver',(.47,.60,.66),.65,.3,.1)
panel=mat('Harpoon blue steel inlay',(.20,.30,.39),.35,.36,.1)
bore=mat('Harpoon recessed bore',(.024,.047,.065),.1,.6,0)
def finish(o,bevel=0):
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 if bevel:
  mod=o.modifiers.new('Native rounded edge','BEVEL');mod.width=bevel;mod.segments=4
  bpy.ops.object.modifier_apply(modifier=mod.name)
 for f in o.data.polygons:f.use_smooth=True
 mod=o.modifiers.new('Area weighted split normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
 bpy.ops.object.modifier_apply(modifier=mod.name)
 o.select_set(False)
 return o
def box(name,loc,dims,material,bevel=.01,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=adopt(bpy.context.object,name,material,parent)
 o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,bevel)
def cyl(name,loc,radius,depth,material,axis='Y',bevel=.005,parent=None,verts=40):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc)
 o=adopt(bpy.context.object,name,material,parent)
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 return finish(o,bevel)
foot=box('harpoon__bearing_foot',(0,.343,.040),(.202,.340,.080),goldedge,.010)
foot['bearing']='Evaluated downward face at local Z=0 is the actual contact polygon; deliberate rear finite two-axis bearing'
box('harpoon__rear_pedestal',(0,.343,.15),(.142,.235,.16),gold,.020)
box('harpoon__cradle_spine',(0,-.025,.255),(.155,.955,.078),gold,.018)
for s in [-1,1]:
 x=s*.113
 cyl('harpoon__red_side_housing_'+str(s),(x,-.015,.322),.052,.710,red,bevel=.018)
 for y in [-.332,.302]:
  cyl('harpoon__pod_end_'+str(s)+'_'+str(y),(x,y,.322),.045,.026,redcap,bevel=.008)
 for y in [-.235,.208]:
  cyl('harpoon__gold_band_'+str(s)+'_'+str(y),(x,y,.322),.061,.058,gold,bevel=.008)
  cyl('harpoon__band_fastener_'+str(s)+'_'+str(y),(x,y,.383),.012,.009,silver,axis='Z',bevel=.003,verts=24)
 box('harpoon__cradle_side_'+str(s),(s*.074,-.042,.314),(.026,.930,.078),gold,.010)
 cyl('harpoon__hinge_outer_'+str(s),(s*.150,.060,.344),.046,.029,steel,axis='X',bevel=.007)
 cyl('harpoon__hinge_cap_'+str(s),(s*.167,.060,.344),.029,.013,silver,axis='X',bevel=.005)
 for y in [.221,.463]:
  cyl('harpoon__foot_fixing_'+str(s)+'_'+str(y),(s*.064,y,.083),.015,.010,silver,axis='Z',bevel=.003,verts=24)
box('harpoon__rear_bridge',(0,.405,.319),(.172,.094,.098),gold,.018)
cyl('harpoon__rear_slide_socket',(0,.265,.375),.076,.094,steel,bevel=.010)
cyl('harpoon__barrel',(0,-.147,.375),.061,.770,steel,bevel=.009,parent=moving)
cyl('harpoon__barrel_rear_collar',(0,.230,.375),.067,.054,silver,bevel=.007,parent=moving)
box('harpoon__barrel_top_inlay',(0,-.130,.433),(.049,.270,.012),panel,.005,parent=moving)
# A real open ring, native inner wall and rear recess, pointing local -Y.
def tube(name,yfront,yback,outer,inner,z,material,parent):
 n=48;vs=[]
 for y,r in [(yfront,outer),(yback,outer),(yfront,inner),(yback,inner)]:
  vs += [(math.cos(i*2*math.pi/n)*r,y,z+math.sin(i*2*math.pi/n)*r) for i in range(n)]
 fs=[]
 for i in range(n):
  j=(i+1)%n
  fs += [(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);coll.objects.link(o);o.parent=parent;me.materials.append(material)
 # The topology is consistently wound by recalc, independent of Blender face order.
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
 return finish(o,.004)
tube('harpoon__silver_muzzle',-.602,-.527,.079,.044,.375,silver,moving)
cyl('harpoon__bore_recess',(0,-.532,.375),.043,.007,bore,bevel=.001,parent=moving)
mouth=bpy.data.objects.new('harpoon__actual_mouth',None);coll.objects.link(mouth);mouth.parent=moving;mouth.location=(0,-.602,.375);mouth['forwardAxis']=[0,-1,0]
for f,d in enumerate(DELTAS,1):
 moving.location.y=d;moving.keyframe_insert(data_path='location',index=1,frame=f)
act=moving.animation_data.action;act.name='Harpoon exact source nonloop recoil 12 phases'
for layer in act.layers:
 for strip in layer.strips:
  for slot in act.slots:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:
     fc.extrapolation='CONSTANT'
     for k in fc.keyframe_points:k.interpolation='LINEAR'
sc.frame_start=1;sc.frame_end=12;sc.frame_set(1);bpy.context.view_layer.update()
root['clipLaw']=json.dumps({'idle':{'frames':1,'fps':12,'loop':False,'neutralFrame':1},'active':{'frames':12,'fps':12,'loop':False,'closingKey':None,'deltaY':DELTAS}})
# Exact independent equipment projection, without using main camera or fitting alpha.
camdata=bpy.data.cameras.new('Harpoon registered camera');cam=bpy.data.objects.new('Harpoon registered camera',camdata);sc.collection.objects.link(cam);sc.camera=cam;camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5
src=json.loads((E/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(src['camera']['worldMatrix']);camdata.shift_x=0
sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=src['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
camdata.shift_y=0;bpy.context.view_layer.update()
def pix(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*768,(1-p.y)*1408))
base=pix((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=pix((0,0,0)).y-base.y;camdata.shift_y=(992-base.y)/dy
sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=64;sc.render.filter_size=.5
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=100;sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.35;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('Harpoon symmetric world');sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.12;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.65,.73,1)
def light(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=(1,.95,.87);o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-Vector(loc)).to_track_quat('-Z','Y').to_euler()
light('Centered broad overhead',(0,0,4.5),240,4)
for i,loc in enumerate([(3,0,2.3),(-3,0,2.3),(0,3,2.3),(0,-3,2.3)]):light('Equal cardinal fill '+str(i),loc,90,4)
sc['recipe']='One common symmetric overhead + equal cardinal EEVEE rig. No ground receiver; filter_size=.5; full native4x frames BOX reduced whole to published2x.'
bpy.context.view_layer.update();root.rotation_euler=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'project.blend'),compress=True)
settings={'blender':bpy.app.version_string,'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'filterSize':sc.render.filter_size,'frame':[768,1408],'publishedFrame':[384,704],'publication':'whole frame BOX x0.5','pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':list(pix((0,0,0))),'cameraMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':camdata.ortho_scale,'shiftY':camdata.shift_y,'groundReceiver':False,'lights':[{'name':o.name,'location':list(o.location),'power':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'colorManagement':{'transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'images':[i.filepath for i in bpy.data.images if i.users and i.name!='Render Result']}
(P/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
sc.render.filepath=str(C/'draft-idle-S.png');bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',P/'project.blend')
