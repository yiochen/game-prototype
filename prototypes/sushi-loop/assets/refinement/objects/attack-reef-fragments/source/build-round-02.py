"""Build round 01 in an isolated background process opened on the private raw copy."""
import bpy, math, json, random, sys
sys.dont_write_bytecode = True
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
S=Path(__file__).resolve().parent;B=S.parent;I=S/'round-02-inputs';C=B/'candidates/round-02'
assert (S/'construction-acknowledgment-v2.json').is_file()
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
col=bpy.data.collections['S33_CFX_attack-reef-fragments.001'];root=bpy.data.objects['attack-reef-fragments__ground_root.001']
for s in list(bpy.data.scenes):
 if s!=sc:bpy.data.scenes.remove(s)
for o in list(bpy.data.objects):
 if o!=root:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=col:bpy.data.collections.remove(c)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
root.animation_data_clear();root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
col.hide_render=False;col.hide_viewport=False
def unhide(l):
 l.exclude=False;l.hide_viewport=False
 for ch in l.children:unhide(ch)
unhide(sc.view_layers[0].layer_collection)
root.hide_set(False);root.hide_render=False;root.hide_viewport=False
def linear(hexcode):
 rgb=[int(hexcode[j:j+2],16)/255 for j in (0,2,4)]
 return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb)
def material(name,family,factor):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
 p=nt.nodes.new('ShaderNodeBsdfPrincipled');out=nt.nodes.new('ShaderNodeOutputMaterial')
 colors={'blue':['195C7D','227CA8','2898BF','60B4C9'],'purple':['563686','7043AB','8756C1','A17ACC']}[family]
 texture=nt.nodes.new('ShaderNodeTexCoord');texture.name='Stable native local volume coordinates'
 xyz=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(texture.outputs['Generated'],xyz.inputs['Vector'])
 ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.name='Colored lower middle crown hierarchy';ramp.color_ramp.interpolation='EASE'
 for e in list(ramp.color_ramp.elements)[1:]:ramp.color_ramp.elements.remove(e)
 for j,(position,hexcode) in enumerate(zip([0,.32,.72,1],colors)):
  e=ramp.color_ramp.elements[0] if j==0 else ramp.color_ramp.elements.new(position)
  e.position=position;e.color=(*[x*factor for x in linear(hexcode)],1)
 nt.links.new(xyz.outputs['Z'],ramp.inputs['Fac'])
 subtract=nt.nodes.new('ShaderNodeVectorMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=(.5,.5,.5)
 nt.links.new(texture.outputs['Generated'],subtract.inputs[0])
 length=nt.nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';nt.links.new(subtract.outputs['Vector'],length.inputs[0])
 radial=nt.nodes.new('ShaderNodeMapRange');radial.name='Soft native volume falloff';radial.clamp=True
 for key,value in [('From Min',.42),('From Max',.76),('To Min',1.05),('To Max',.83)]:radial.inputs[key].default_value=value
 nt.links.new(length.outputs['Value'],radial.inputs['Value'])
 mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
 nt.links.new(ramp.outputs['Color'],mix.inputs[1]);nt.links.new(radial.outputs['Result'],mix.inputs[2])
 nt.links.new(mix.outputs['Color'],p.inputs['Base Color']);nt.links.new(mix.outputs['Color'],p.inputs['Emission Color'])
 color=linear(colors[2]);p.inputs['Roughness'].default_value=.42;p.inputs['Specular IOR Level'].default_value=.18
 p.inputs['Coat Weight'].default_value=.06;p.inputs['Coat Roughness'].default_value=.35
 p.inputs['Emission Strength'].default_value=.08
 nt.links.new(p.outputs['BSDF'],out.inputs['Surface']);m.diffuse_color=(*color,1)
 return m
mats={}
for family in ['blue','purple']:
 mats[family]=[material('Reef mineral '+family+' '+str(j),family,factor) for j,factor in enumerate([1,1,.96])]
def chunk(name,parent,n,seed,family):
 rng=random.Random(seed);angles=[j*2*math.pi/n+rng.uniform(-.08,.08) for j in range(n)]
 radii=[rng.uniform(.88,1.03) for j in range(n)]
 # Homothetic rings give coherent planar trapezoids, rather than noisy triangulation.
 verts=[]
 rings=[(.33,-.98,-.07,.03),(.68,-.78,-.05,.025),(1,.02,0,0),(.73,.77,.04,-.025),(.35,.97,.05,-.03)]
 for radius,z,ox,oy in rings:
  for a,r in zip(angles,radii):verts.append((radius*r*math.cos(a)+ox,radius*r*math.sin(a)+oy,z))
 faces=[tuple(reversed(range(n))),tuple(range(4*n,5*n))]
 for band in range(4):
  for j in range(n):faces.append((band*n+j,band*n+(j+1)%n,(band+1)*n+(j+1)%n,(band+1)*n+j))
 mesh=bpy.data.meshes.new(name+' native faceted mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new(name,mesh);col.objects.link(o);o.parent=parent
 for m in mats[family]:mesh.materials.append(m)
 for p in mesh.polygons:p.use_smooth=True;p.material_index=1 if p.index==1 else (2 if p.index%5==0 else 0)
 bevel=o.modifiers.new('Real softened mineral edges','BEVEL');bevel.width=.055;bevel.segments=3;bevel.affect='EDGES';bevel.limit_method='ANGLE';bevel.angle_limit=.15;bevel.harden_normals=True
 normals=o.modifiers.new('Broad planar normal weighting','WEIGHTED_NORMAL');normals.keep_sharp=True;normals.weight=50
 o['native_design']='irregular five-ring volume, smaller endcaps and gradual shoulders, broad facets, real three-segment bevels';o['palette_family']=family
 return o
main=[]
for j in range(9):
 o=chunk('attack-reef-fragments__fragment_'+str(j)+'.001',root,5+j%2,170+j,'purple' if j%2==0 else 'blue');main.append(o)
 if j in [1,2,5,8]:
  chip=chunk('attack-reef-fragments__companion_'+str(j),o,5,440+j,'purple' if j%2==0 else 'blue')
  chip.location=(1.34,.24,-.26);chip.rotation_euler=(.2,.5,.7);chip.scale=(.24,.25,.30)
def smooth(t):return t*t*(3-2*t)
def pose(j,clip,t):
 q=smooth(t);theta=j*2.399963229728653+.10*math.sin(j*1.7)
 r0=.25+.065*(j%3);r1=.35+.065*(j%3);r2=.76+.075*(j%3);r3=.91+.065*(j%3)
 z0=.25+.065*(j%4);rot0=Vector((.2*j,.3*j,.5*j));rw=Vector((.13,.25,.12));ra=Vector((.60+.07*(j%3),.72,.26));rr=Vector((.18,.20,.10))
 if clip=='windup':r=r0+(r1-r0)*q+.075*math.sin(math.pi*t);z=z0+.11*math.sin(math.pi*t);rot=rot0+rw*q;size=1
 elif clip=='active':r=r1+(r2-r1)*q;z=z0+.18*math.sin(math.pi*t);rot=rot0+rw+ra*q;size=1
 else:r=r2+(r3-r2)*q;z=z0-.035*q;rot=rot0+rw+ra+rr*q;size=1-.92*q
 scale=Vector((.118+.012*(j%3),.112,.135+.008*(j%2)))*size
 return (r*math.cos(theta),r*math.sin(theta),z),rot,scale
rig={'assetId':'attack-reef-fragments','fps':12,'source':'build-round-02.py','static':False,'clips':{},'armatures':[],'footprint':[1,1],'projection':'square-top-front-oblique','groundRootObject':root.name,'sockets':{},'actionCount':27,'status':'native-actions-baked-needs-independent-visual-review'}
for clip in ['windup','active','recovery']:
 records=[]
 for j,o in enumerate(main):
  action=bpy.data.actions.new('REFINED__attack-reef-fragments__'+clip+'__'+o.name);action.use_fake_user=True
  o.animation_data_create();o.animation_data.action=action
  for frame in range(1,13):
   o.location,o.rotation_euler,o.scale=pose(j,clip,(frame-1)/11)
   for path in ['location','rotation_euler','scale']:o.keyframe_insert(data_path=path,frame=frame,group=clip)
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      fc.extrapolation='CONSTANT'
      for k in fc.keyframe_points:k.interpolation='LINEAR'
  records.append({'ownerType':'Object','ownerName':o.name,'action':action.name,'slotIdentifier':o.animation_data.action_slot.identifier,'keyframeCount':108})
 rig['clips'][clip]={'frames':12,'fps':12,'loop':False,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':None,'actions':records,'controlsByFrame':[{} for _ in range(12)],'geometryOwners':[],'shaderChannels':[],'shaderLoopClosure':{}}
root['native_action_record']=json.dumps({'source':'build-round-02.py','assetId':'attack-reef-fragments','clips':{k:[r['action'] for r in v['actions']] for k,v in rig['clips'].items()}})
root['artStyle']='warm-soft-refinement-round-02';root['animation_recipes']=json.dumps({k:{'frames':12,'fps':12,'loop':False,'static':False} for k in rig['clips']})
camdata=bpy.data.cameras.new('Registered fragment camera');cam=bpy.data.objects.new('Registered fragment camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
reference=json.loads((I/'original-camera.json').read_text());cam.matrix_world=Matrix(reference['camera']['worldMatrix'])
camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=2.5;camdata.shift_x=0;camdata.shift_y=.24576884508132935
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1280;sc.render.resolution_y=1792;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1.2206555604934692;sc.render.pixel_aspect_y=1
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30;sc.render.dither_intensity=0;sc.render.filter_size=1.5
sc.eevee.taa_render_samples=32;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.use_persistent_data=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.2;sc.view_settings.gamma=1;sc.compositing_node_group=None
sc.world=bpy.data.worlds.new('Broad cool neutral environment');sc.world.use_nodes=True
bg=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.72,.79,.88,1);bg.inputs['Strength'].default_value=.18
def light(name,location,energy,color,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=location;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();return o
light('Broad warm centered crown',(0,0,4.5),300,(1,.91,.80),3.6)
for j in range(4):
 a=j*math.pi/2;light('Equal cardinal soft fill '+str(j),(3*math.cos(a),3*math.sin(a),1.8),70,(.82,.91,1),4)
sc.frame_start=1;sc.frame_end=12;sc.render.fps=12
for record in rig['clips']['active']['actions']:
 o=bpy.data.objects[record['ownerName']];o.animation_data.action=bpy.data.actions[record['action']]
 o.animation_data.action_slot=next(s for s in o.animation_data.action.slots if s.identifier==record['slotIdentifier'])
root.rotation_euler.z=0;sc.frame_set(6);sc.view_layers[0].update()
asset=json.loads((I/'original-asset.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'warm-soft-refinement-round-02','nativeSource':'round-02.blend','lighting':'centered warm overhead plus four equal broad cardinal fills; no preferred horizontal direction'}
records=S/'round-02-records';records.mkdir()
(records/'asset.json').write_text(json.dumps(asset,indent=2)+'\n');(records/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
recipe={'nativeCaptureScale':4,'nativeFrame':[1280,1792],'publishedSourceScale':2,'publishedFrame':[640,896],'publication':'wholecanvas Pillow LANCZOS only','construction':'nine varied5/6-sided five-ring mineral chunks; small endcaps transition through shoulders to mainbody; four subordinate native chips; bevelwidth.055local/segments3, broad weighted normals','lighting':'300W centered warm area size3.6; four70W equal cool-neutral cardinal area fills size4; world strength.18','material':'opaque Principled, roughness.42/specular.18/coat.06/coatroughness.35; native Generated-Z colored lower/middle/crown ramp and soft local radial falloff, consistent through allviews/actions; emission.08 retains color in lowers; cap and body share same palette hierarchy','motion':'three persistent baked12frame oneshot actions per mainchunk; unchanged continuous functional progression from round01; recovery final8% linear scale; constant postterminal extrapolation; children inherit motion','colorManagement':'Standard/None/exposure-.2/gamma1; no compositor; dither0','samples':32,'editsScopedTo':'own new round02 source only; no prior reviewed source saved/edited'}
(S/'round-02-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
for mesh in list(bpy.data.meshes):
 if mesh.users==0:bpy.data.meshes.remove(mesh)
bpy.ops.wm.save_as_mainfile(filepath=str(S/'round-02.blend'),compress=True)
print('ROUND_02_EDITABLE_SAVED',S/'round-02.blend',flush=True)
