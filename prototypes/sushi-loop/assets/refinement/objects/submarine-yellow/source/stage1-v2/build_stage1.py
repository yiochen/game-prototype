"""Portable stage-1 submarine body + provisional native equipment. Blender 5.2.2.
Run: blender -b --python build_stage1.py [-- --no-render]
No final atlas delivery. All coordinates are canonical source-facing S world units.
"""
import bpy, math, json, hashlib, shutil, sys
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
OBJ=HERE.parents[1]
RES=HERE/'resources'
OUT=OBJ/'candidates/stage1-v2'
OUT.mkdir(parents=True,exist_ok=True)
TAU=math.tau
DIRECTIONS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
CLIPS=['idle','travel','impact','protection','dock-charging','dock-ready']
CLIPS+=['upgraded-'+c for c in CLIPS.copy()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,indent=2,default=str)+'\n')
def hashdata(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def vv(v):return [round(float(x),9) for x in v]
def bb(pts):return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def mat(name,color,rough=.38,metal=0,coat=.15,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.28;p.inputs['Specular IOR Level'].default_value=.28
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 return m
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Submarine Stage1 Preliminary'
col=bpy.data.collections.new('WarmSoft_submarine-yellow_stage1');sc.collection.children.link(col)
def empty(name,parent=None):
 o=bpy.data.objects.new(name,None);col.objects.link(o);o.parent=parent;return o
root=empty('submarine-yellow__root');root['legacyAttachmentReferences']=json.dumps({'sub_harpoon':[.24,-.40,.37],'sub_collector':[0,-.53,.21]});root['nominalHeight']=1.02;root['footprint']='[1,2]';root['stage']='PRELIMINARY stage1; canonical equipment pending';root['clips']=json.dumps({c:{'frames':12,'fps':12,'loop':not c.endswith('impact'),'static':False} for c in CLIPS})
motion=empty('submarine-yellow__body_motion',root)
M={
'yellow':mat('Sub Warm yellow enamel',(.80,.36,.003),.34,0,.2),
'gold':mat('Sub Honey gold trim',(.62,.24,.006),.36,.12,.2),
'light':mat('Sub Sunflower raised trim',(1,.60,.008),.32,0,.22),
'red':mat('Sub Coral red pod',(.75,.035,.018),.38,0,.18),
'reddark':mat('Sub Warm red seams',(.40,.027,.016),.45),
'blue':mat('Sub Vivid blue convex glass',(.003,.20,.65),.19,0,.32),
'cyan':mat('Sub Cyan status',(.025,.65,.82),.22,.05,.25,.35),
'cream':mat('Sub Warm lamp lens',(1,.82,.34),.25,0,.2,.25),
'metal':mat('Sub Soft silver fasteners',(.42,.48,.51),.36,.45,.10),
'dark':mat('Sub Warm slate fittings',(.065,.105,.145),.41,.2),
}
body=[];equip=[]
def finish(o,name,m,parent=motion,group=body):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent
 if m:o.data.materials.append(M[m] if isinstance(m,str) else m)
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
 if group is not None:group.append(o)
 return o

def uv(name,loc,scale,m,parent=motion,group=body,rot=(0,0,0),segments=48,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc)
 o=bpy.context.object;o.scale=scale;o.rotation_euler=rot;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,m,parent,group)
def box(name,loc,size,m,bevel=.015,parent=motion,group=body,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler=rot
 if bevel:
  b=o.modifiers.new('Crafted round edges','BEVEL');b.width=bevel;b.segments=4
  b.affect='EDGES';b.profile=.5
  n=o.modifiers.new('Area weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
 return finish(o,name,m,parent,group)
def cyl(name,loc,r,depth,m,rot=(0,0,0),bevel=.008,parent=motion,group=body,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.rotation_euler=rot
 if bevel:
  b=o.modifiers.new('Rounded lip geometry','BEVEL');b.width=bevel;b.segments=3
  n=o.modifiers.new('Disc weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True
 return finish(o,name,m,parent,group)
def torus(name,loc,major,minor,m,rot=(0,0,0),parent=motion,group=body):
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=12,location=loc,major_radius=major,minor_radius=minor)
 o=bpy.context.object;o.rotation_euler=rot;return finish(o,name,m,parent,group)
# Substantial rounded shell with a darker continuous lower shell.
uv('body__hull',(0,0,.405),(.343,.479,.305),'yellow')
uv('body__lower_shell',(0,-.005,.282),(.317,.433,.186),'gold')
# Porthole lies in the original upper-forward plane, not a camera-facing card.
a=math.atan2(.6,.8);R=Matrix.Rotation(a,3,'X');C=Vector((0,-.257,.651));normal=R@Vector((0,0,1))
def port(v):return C+R@Vector(v)
cyl('body__port_flange',port((0,0,0)),.217,.060,'gold',(a,0,0),.011)
cyl('body__port_enamel_trim',port((0,0,.023)),.207,.035,'light',(a,0,0),.008)
cyl('body__glass_gasket',port((0,0,.044)),.184,.014,'dark',(a,0,0),.004)
uv('body__convex_blue_glass',port((0,0,.048)),(.177,.177,.034),'blue',rot=(a,0,0))
torus('body__inner_gold_bead',port((0,0,.047)),.184,.007,'gold',(a,0,0))
for i in range(8):
 t=TAU*i/8
 uv('body__port_fastener_%02d'%i,port((.201*math.sin(t),.201*math.cos(t),.048)),(.011,.011,.007),'metal',rot=(a,0,0),segments=20,rings=10)
# Coherent octagonal access hatch aft of the canopy.
cyl('body__hatch_red_flange',(0,.126,.707),.116,.037,'red',bevel=.012)
cyl('body__hatch_octagonal_lid',(0,.126,.741),.087,.040,'light',bevel=.007,vertices=8)
for i in range(4):
 t=TAU*i/4+.45;cyl('body__hatch_fixing_%d'%i,(.099*math.cos(t),.126+.099*math.sin(t),.733),.009,.012,'metal',bevel=.003,vertices=20)
# Twin longitudinal pressure pods, bands, ends and subtle service insets.
for s in (-1,1):
 x=s*.394
 cyl('body__red_pressure_pod_%s'%s,(x,.035,.367),.133,.386,'red',(math.pi/2,0,0),.018)
 for j,y in enumerate((-.161,.231)):
  cyl('body__pod_band_%s_%s'%(s,j),(x,y,.367),.142,.047,'light',(math.pi/2,0,0),.011)
  cyl('body__pod_end_%s_%s'%(s,j),(x,y+(-.026 if j==0 else .026),.367),.120,.019,'gold',(math.pi/2,0,0),.008)
  # Two visible top-side bolts per band.
  for dx in (-.078,.078):uv('body__pod_bolt_%s_%s_%s'%(s,j,dx),(x+dx,y,.477),(.009,.012,.009),'metal',segments=16,rings=8)
 box('body__pod_service_rib_%s'%s,(x,.024,.499),(.037,.214,.011),'reddark',.005)
 # Yellow swept rear fins remain within the source-facing width cap.
 box('body__tail_fin_%s'%s,(s*.385,.347,.430),(.203,.243,.047),'yellow',.024,rot=(0,0,-s*.16))
 # Existing skids + short body attachment supports. Their entire assembly bobs.
 box('body__hover_skid_%s'%s,(s*.230,.005,.075),(.070,.628,.060),'gold',.028)
 box('body__skid_support_%s'%s,(s*.224,-.075,.171),(.047,.072,.150),'yellow',.018,rot=(0,s*.05,0))
 # Distinct pod coupler saddles fill purposeful body intersections.
 uv('body__pod_coupler_%s'%s,(s*.311,.027,.405),(.045,.135,.080),'gold')
# Nose headlight assembly and paired small bumper lamps.
cyl('body__nose_lamp_socket',(0,-.471,.367),.077,.061,'gold',(math.pi/2,0,0),.012)
cyl('body__nose_lamp_rim',(0,-.512,.367),.067,.025,'light',(math.pi/2,0,0),.008)
uv('body__nose_lamp_lens',(0,-.529,.367),(.052,.015,.052),'cream')
for s in(-1,1):
 cyl('body__bumper_lamp_base_%s'%s,(s*.154,-.467,.295),.032,.035,'gold',(math.pi/2,0,0),.008)
 uv('body__bumper_lamp_%s'%s,(s*.154,-.491,.295),(.023,.011,.023),'cream',segments=24,rings=12)
# Rear periscope + intentional forward optical face and coherent status fixture.
cyl('body__periscope_foot',(0,.214,.696),.081,.072,'gold',bevel=.010)
cyl('body__periscope_stem',(0,.214,.836),.052,.239,'dark',bevel=.010)
box('body__periscope_cap',(0,.214,.967),(.277,.111,.086),'light',.035)
box('body__periscope_optic',(0,.153,.966),(.160,.014,.040),'blue',.012)
cyl('body__status_socket',(0,.214,1.014),.047,.025,'gold',bevel=.007)
lamp=uv('body__status_cyan_lens',(0,.214,1.037),(.037,.037,.025),'cyan',segments=32,rings=16)
# Rear hub with rotating rounded propeller; shaft/axis retained along Y.
cyl('body__tail_shaft',(0,.519,.356),.044,.135,'dark',(math.pi/2,0,0),.008)
prop=empty('body__propeller_axis',motion);prop.location=(0,.607,.356)
cyl('body__propeller_hub',(0,0,0),.051,.049,'gold',(math.pi/2,0,0),.008,parent=prop)
for i in range(3):
 t=TAU*i/3;box('body__propeller_blade_%d'%i,(.082*math.cos(t),0,.082*math.sin(t)),(.156,.028,.052),'light',.023,parent=prop,rot=(0,-t,0))
# Physical seats are BODY bytes, distinct from legacy effect reference empties.
for s in(-1,1):box('body__panel_contact_seat_%s'%s,(s*.215,.16,.591),(.090,.286,.022),'gold',.011)
box('body__harpoon_contact_seat',(.31,-.12,.556),(.105,.175,.025),'gold',.012)
box('body__collector_contact_seat',(0,-.435,.212),(.258,.038,.115),'gold',.012)
legacy={}
for key,p in {'sub_harpoon':(.24,-.40,.37),'sub_collector':(0,-.53,.21)}.items():
 o=empty(key,root);o.location=p;o['semantic']='Legacy declared reference; not physical mouth/muzzle/mount';legacy[key]=o
# PROVISIONAL only. Canonical separate objects will later replace these exact groups.
mounts={
 'sub-hull-panels':{'translation':[0,.16,.602],'uniformScale':.5,'rotationZ':0,'localReservation':[[-.52,-.30,0],[.52,.30,.16]],'contactSeats':[[[-.260,.017,.580],[-.170,.303,.602]],[[.170,.017,.580],[.260,.303,.602]]],'shapeRequirement':'Two side saddles; preserve central corridor x[-.15,.15] through periscope; no central bridge above body.'},
 'sub-harpoon-mount':{'translation':[.31,-.24,.5685],'uniformScale':.35,'rotationZ':0,'localReservation':[[-.18,-.62,0],[.18,.62,.48]],'contactSeats':[[[.2575,-.2075,.5435],[.3625,-.0325,.5685]]],'shapeRequirement':'Base underside at localZ0 on body seat near localY+.343; barrel/muzzle forward toward -Y, avoid glass. Root shifted forward to center standalone occupied Y inside locked frame. Proposed mouth center [.31,-.444,.683].'},
 'sub-collector-inlet':{'translation':[0,-.52,.14],'uniformScale':.4,'rotationZ':0,'localReservation':[[-.425,-.275,0],[.425,.25,.40]],'contactSeats':[[[-.129,-.454,.1545],[.129,-.416,.2695]]],'shapeRequirement':'Rear contact face toward +Y and mouth toward -Y; nose light above. Back contact enters body seat at Y-.435.'},
}
for name,m in mounts.items():
 p=empty('MOUNT__'+name,motion);p.location=m['translation'];p.scale=(m['uniformScale'],)*3;p['role']='Frozen proposed physical native assembly frame';p['localReservation']=json.dumps(m['localReservation']);m['object']=p.name
 s=m['uniformScale'];m['matrixLocal']=[[s,0,0,m['translation'][0]],[0,s,0,m['translation'][1]],[0,0,s,m['translation'][2]],[0,0,0,1]]
 if name=='sub-hull-panels':
  for s in(-1,1):
   box('PROVISIONAL__panel_%s'%s,(s*.43,0,.061),(.18,.56,.122),'light',.030,parent=p,group=equip)
   for y in(-.20,.20):cyl('PROVISIONAL__panel_fixing_%s_%s'%(s,y),(s*.43,y,.136),.017,.020,'metal',bevel=.005,parent=p,group=equip,vertices=24)
 elif name=='sub-harpoon-mount':
  u=empty('PROVISIONAL__harpoon_old_units',p);u.location=(0,.12/.35,0);u.scale=(.5/.35,)*3;p=u
  box('PROVISIONAL__harpoon_base',(0,0,.040),(.21,.36,.080),'red',.022,parent=p,group=equip)
  box('PROVISIONAL__harpoon_support',(0,0,.15),(.14,.12,.18),'red',.018,parent=p,group=equip)
  cyl('PROVISIONAL__harpoon_barrel',(0,-.24,.228),.074,.70,'dark',(math.pi/2,0,0),.009,parent=p,group=equip)
  cyl('PROVISIONAL__harpoon_muzzle',(0,-.61,.228),.090,.075,'metal',(math.pi/2,0,0),.009,parent=p,group=equip)
 else:
  u=empty('PROVISIONAL__collector_old_units',p);u.scale=(1.25,)*3;p=u
  box('PROVISIONAL__collector_chassis',(0,0,.16),(.63,.36,.30),'metal',.045,parent=p,group=equip)
  box('PROVISIONAL__collector_dark_mouth',(0,-.190,.16),(.47,.017,.20),'dark',.026,parent=p,group=equip)
  for x in(-.14,0,.14):box('PROVISIONAL__collector_guard_%s'%x,(x,-.200,.16),(.025,.026,.225),'gold',.010,parent=p,group=equip)
for o in equip:o['status']='PROVISIONAL; canonical independent component approval pending'
# Identical horizontal lighting recipe in every facing. No receiver plane/ground shadow.
sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=64
sc.render.resolution_x=640;sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.filter_size=.5
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.35;sc.view_settings.gamma=1
world=bpy.data.worlds.new('Sub neutral soft ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.32,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.30;sc.world=world
camd=bpy.data.cameras.new('Registered 65 degree camera');cam=bpy.data.objects.new('Registered 65 degree camera',camd);sc.collection.objects.link(cam);sc.camera=cam;camd.type='ORTHO';camd.ortho_scale=3;camd.shift_y=.25
cam.matrix_world=Matrix([[1,0,0,0],[0,.906307817,-.42261821,-4.226182461],[0,.42261821,.906307817,9.063077927],[0,0,0,1]])
def light(name,pos,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.use_shadow=True;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.35))-o.location).to_track_quat('-Z','Y').to_euler()
light('Centered broad overhead',(0,0,4.5),210,4)
for i,p in enumerate([(3,0,2.3),(-3,0,2.3),(0,3,2.3),(0,-3,2.3)]):light('Equal cardinal fill %d'%i,p,85,4)
# Existing cadence/meaning: all body parts + skids bob, lateral travel, damped impact,
# idle/travel propeller turn; charging .8+.2sin scale, protection 1+.25sin, ready steady.
lampbase=lamp.location.copy();props=[]
def pose(clip,t):
 c=clip.removeprefix('upgraded-');up=clip.startswith('upgraded-');motion.location=(0,0,0)
 if c=='travel':motion.location=(.012*math.sin(TAU*t+.37),0,.01*math.sin(TAU*t*2));prop.rotation_euler.y=TAU*t*2
 elif c=='impact':motion.location.x=.045*math.sin(TAU*t*3)*(1-t);prop.rotation_euler.y=0
 else:motion.location.z=.018*math.sin(TAU*t);prop.rotation_euler.y=TAU*t
 lamp.hide_render=c not in('dock-charging','dock-ready','protection');lamp.hide_viewport=lamp.hide_render
 pulse=.8+.2*math.sin(TAU*t) if c=='dock-charging' else (1+.25*math.sin(TAU*t) if c=='protection' else 1)
 lamp.scale=(pulse,)*3
 for o in equip:o.hide_render=not up;o.hide_viewport=not up
 bpy.context.view_layer.update()
animated=[motion,prop,lamp]+equip
actions={}
for clip in CLIPS:
 for o in animated:o.animation_data_clear()
 for idx in range(13):
  pose(clip,idx/12)
  for o in animated:
   for field in (['location'] if o==motion else ['rotation_euler'] if o==prop else ['scale','hide_render','hide_viewport'] if o==lamp else ['hide_render','hide_viewport']):o.keyframe_insert(field,frame=idx+1,group=clip)
 actions[clip]={}
 for o in animated:
  ac=o.animation_data.action;ac.name='STAGE1__'+clip+'__'+o.name;ac.use_fake_user=True;actions[clip][o.name]=ac.name
  for layer in ac.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if fc.data_path.startswith('hide_') else 'LINEAR'
 for o in animated:o.animation_data_clear()
pose('idle',0);sc.frame_start=1;sc.frame_end=12
root['nativeActions']=json.dumps(actions)
# Freeze saved body source before the audit/context scene changes.
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'submarine-stage1.blend'),compress=True)
dump(OUT/'proposed-mounts.json',{'status':'PROPOSED STAGE1, root must freeze before canonical component editors','canonicalFacing':'S','positiveUniformScale':True,'placementScales':{'sub-hull-panels':.5,'sub-harpoon-mount':.35,'sub-collector-inlet':.4},'standaloneVsIntegrated':'All3 standalone native geometry rendered under their own locked camera/root/idle/active contracts. Integration uses one declared positive uniform scale per component (.5/.35/.4); no per-view or nonuniform fit. Model usable canonical parts within reservations. Baseline root and body scale remain1.','mounts':mounts,'legacyReferences':{k:list(o.location) for k,o in legacy.items()},'componentAnimations':'No standalone active animation is mapped into main clips. Main adopts neutral idle geometry only.'})
# Native data snapshot binds mesh geometry, transforms, normals/UV, materials/nodes.
def meshdata(o):
 me=o.data
 return {'name':o.name,'parent':o.parent.name if o.parent else None,'location':vv(o.location),'rotation':vv(o.rotation_euler),'scale':vv(o.scale),'vertices':[vv(v.co) for v in me.vertices],'polygons':[list(p.vertices) for p in me.polygons],'normals':[vv(p.normal) for p in me.polygons],'smooth':[p.use_smooth for p in me.polygons],'uv':{u.name:[vv(v.uv) for v in u.data] for u in me.uv_layers},'materials':[m.name for m in me.materials],'modifiers':[{'type':m.type,'name':m.name,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]}
geometry=[meshdata(o) for o in body+equip]
dump(OUT/'native-geometry.json',geometry)
materialrecords=[]
for m in M.values():
 materialrecords.append({'name':m.name,'nodes':[{'type':n.bl_idname,'name':n.name,'inputs':{s.name:vv(s.default_value) if hasattr(s.default_value,'__iter__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
dump(OUT/'native-materials.json',materialrecords)
def px(p):
 p=world_to_camera_view(sc,cam,Vector(p));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
p0=Vector(px((0,0,0)))
camera={'frame':[640,768],'logicalFrame':[320,384],'logicalRoot':[160,288],'nativeRoot':px((0,0,0)),'matrixWorld':[vv(r) for r in cam.matrix_world],'orthoScale':camd.ortho_scale,'shift':[camd.shift_x,camd.shift_y],'pixelAspect':[1,1],'unitBasis':{n:vv(Vector(px(p))-p0) for n,p in [('X',(1,0,0)),('Y',(0,1,0)),('Z',(0,0,1))]},'renderEngine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'filterSize':sc.render.filter_size,'horizontalLightSymmetry':4,'noGroundReceiver':True,'viewSettings':{'transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma}}
dump(OUT/'native-camera.json',camera)
def evaluated(objs):
 dg=bpy.context.evaluated_depsgraph_get();pts=[];faces=[];names=[]
 for o in objs:
  if o.hide_render:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();start=len(pts);pts.extend([eo.matrix_world@v.co for v in me.vertices]);faces.extend([[start+i for i in p.vertices] for p in me.polygons]);names.append(o.name);eo.to_mesh_clear()
 return pts,faces,names
# Audits include all576 actual phases and all half/closure phases, no full batch renders.
phases=[]
for clip in CLIPS:
 for d,ang in DIRECTIONS.items():
  root.rotation_euler.z=ang
  for idx in range(25):
   t=idx/24;pose(clip,t);pts,faces,names=evaluated(body+equip);inv=Matrix.Rotation(-ang,3,'Z');p=[inv@v for v in pts]
   phases.append({'clip':clip,'direction':d,'sourceFrame':1+12*t,'kind':'runtime' if idx%2==0 and idx<24 else 'closure' if idx==24 else 'half','t':t,'rootMatrix':[vv(r) for r in root.matrix_world],'motionMatrix':[vv(r) for r in motion.matrix_local],'canonicalBounds':bb(p),'visibleMeshes':names,'statusScale':list(lamp.scale),'statusVisible':not lamp.hide_render,'propellerRotationY':prop.rotation_euler.y})
dump(OUT/'native-phases.json',phases)
# Pair exact immutable accepted resources, appending collections without resaving them.
companions={}
for key,file,colname,loc in [('floor','dock-floor-round-04.blend','WarmSoft_dock-floor',(0,0,0)),('entry','dock-entry-round-06.blend','S33_PROP_dock-entry',(0,-1.5,0)),('hut','workshop-hut-round-01.blend','WarmSoft_workshop-hut',(.78,.35,.23))]:
 path=RES/file
 with bpy.data.libraries.load(str(path),link=False) as(src,dst):
  if colname not in src.collections:
   opts=[n for n in src.collections if ('hut' in n.lower() if key=='hut' else key in n.lower())];colname=opts[0]
  dst.collections=[colname]
 c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 rr=next(o for o in c.all_objects if o.parent is None and o.type=='EMPTY');rr.location=loc;rr.rotation_euler=(0,0,0)
 companions[key]={'collection':c,'root':rr,'path':str(path),'sha256':sha(path)}
for o in animated:o.animation_data_clear()
root.location=(-.70,-.42,.23);root.rotation_euler=(0,0,0);pose('dock-ready',0)
# Full actual floor triangles, including bevels/nails. Downward support rays from all
# evaluated bottom-side vertices plus triangle centroids. Exact skid underside is flat.
fp,ff,_=evaluated([o for o in companions['floor']['collection'].all_objects if o.type=='MESH']);fb=BVHTree.FromPolygons(fp,ff,all_triangles=False)
hp,hf,_=evaluated([o for o in companions['hut']['collection'].all_objects if o.type=='MESH']);hb=BVHTree.FromPolygons(hp,hf,all_triangles=False)
hover=[];hutclear=[]
for clip in CLIPS:
 for idx in range(25):
  t=idx/24;pose(clip,t);pts,faces,names=evaluated(body+equip)
  if 'dock-' in clip:
   samples=list(pts)
   for f in faces:
    z=[pts[i].z for i in f]
    if min(z)<.34:samples.append(sum((pts[i] for i in f),Vector())/len(f))
   gaps=[]
   for p in samples:
    # Relevant solid underside: exclude higher hull samples; deck mesh itself proves hit.
    if p.z>.35:continue
    q,n,fi,dist=fb.ray_cast(p+Vector((0,0,1e-7)),Vector((0,0,-1)),2)
    if q is not None:gaps.append((p.z-q.z,list(p),list(q)))
   mingap=min(gaps,key=lambda x:x[0]);hover.append({'clip':clip,'t':t,'minimumSeparation':mingap[0],'undersidePoint':mingap[1],'actualDeckPoint':mingap[2],'supportRays':len(gaps)})
  # Conservative globalX separation establishes no hut intersection for all meshes.
  b=bb(pts);hutclear.append({'clip':clip,'t':t,'subMaxX':b[1][0],'hutMinX':min(p.x for p in hp),'conservativeXSeparation':min(p.x for p in hp)-b[1][0]})
minall=[min(p['canonicalBounds'][0][i] for p in phases) for i in range(3)];maxall=[max(p['canonicalBounds'][1][i] for p in phases) for i in range(3)]
viol=[]
for p in phases:
 capx=.56 if 'dock-' in p['clip'] else .61;b=p['canonicalBounds']
 if b[0][0]<-capx-1e-6 or b[1][0]>capx+1e-6 or b[0][1]<-.64-1e-6 or b[1][1]>.68+1e-6 or b[0][2]<.01-1e-6 or b[1][2]>1.12+1e-6:viol.append({k:p[k] for k in ['clip','direction','sourceFrame','canonicalBounds']})
summary={'status':'STAGE1 PRELIMINARY ONLY; no final approval or final576 capture','sourceSHA256':sha(HERE/'submarine-stage1.blend'),'geometrySHA256':hashdata(geometry),'bodyOnlyGeometrySHA256':hashdata([g for g in geometry if not g['name'].startswith('PROVISIONAL')]),'materialSHA256':hashdata(materialrecords),'mountsSHA256':sha(OUT/'proposed-mounts.json'),'camera':camera,'phaseCount':len(phases),'runtimePhases':sum(p['kind']=='runtime' for p in phases),'closurePhases':sum(p['kind']=='closure' for p in phases),'halfPhases':sum(p['kind']=='half' for p in phases),'canonicalAllBounds':[minall,maxall],'envelopeViolations':viol,'dockedHover':{'minimum':min(h['minimumSeparation'] for h in hover),'maximum':max(h['minimumSeparation'] for h in hover),'records':hover,'method':'Downward rays from evaluated low solid vertices and low-face centroids against full immutable Floor04 BVH, including rounded plank bevels and domed nails; all4 dock clips at12runtime+12half+closure. Minimum solid underside per phase, not broaddeck only. Skids are the lowest solids. Source root[-.70,-.42,.23] unchanged.'},'hutClearance':{'minimumConservativeXSeparation':min(h['conservativeXSeparation'] for h in hutclear),'records':hutclear,'method':'All current visible body/provisional equipment native meshes, all12 clips at runtime/half/closure, actual Hut01 world bbox minX; positive disjointX planes proves no intersection.'},'companionSources':{k:{'path':v['path'],'sha256':v['sha256'],'root':list(v['root'].location),'collection':v['collection'].name} for k,v in companions.items()},'motionSemantics':{'body':'Same original.018sin idle/protection/dock and.01sin(2phase)+.012sin(phase+.37) travel; impact.045sin(3phase)*(1-t). Entire body/skids/pods/provisional equipment together.','propeller':'Idle1turn/cycle; travel2turn/cycle; impactstatic. Source meanings retained.','status':'Source .8+.2sin charging pulse,1+.25sin protection pulse,steady1ready; otherstates hidden. Now coherent lens fixture.','variants':'Only PROVISIONAL equipment visible in upgraded clips; one shared body avoids duplicate surfaces; canonical component neutral idle adoption pending.','nativeActions':actions},'resources':'No external textures, no target plane; authored native meshes and Principled materials. Resource closure copied into source/stage1-v2/resources.','pending':['Root freeze exact body/mount bytes','3 independent canonical component pairs','Adopt exact approved geometry/normals/UV/materials at frozen transforms','Final576 native renders/48atlases/playback/consumer checks and original independent main judge']}
dump(OUT/'validation.json',summary)
print('STAGE1_AUDIT',json.dumps({k:summary[k] for k in ['sourceSHA256','geometrySHA256','bodyOnlyGeometrySHA256','mountsSHA256','canonicalAllBounds']},indent=2));print('HOVER',summary['dockedHover']['minimum'],summary['dockedHover']['maximum'],'HUT',summary['hutClearance']['minimumConservativeXSeparation'],'ENVELOPEVIOLATIONS',len(viol))
if '--no-render' not in sys.argv:
 records=[]
 for key,v in companions.items():v['collection'].hide_render=True
 root.location=(0,0,0)
 for clip in ['dock-ready','upgraded-dock-ready']:
  for d,ang in DIRECTIONS.items():
   root.rotation_euler.z=ang;pose(clip,0);path=OUT/(clip+'-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'kind':'native registered representative','clip':clip,'direction':d,'t':0,'path':str(path.relative_to(OBJ)),'sha256':sha(path),'rootMatrix':[vv(r) for r in root.matrix_world],'equipment':'PROVISIONAL' if clip.startswith('upgraded') else 'none','frame':[640,768]})
 # Native family context uses SAME65degree camera/basis at larger canvas only.
 # Standalone companions retain their own frozen capture contracts separately.
 sc.render.resolution_x=1280;sc.render.resolution_y=1536;camd.ortho_scale=6;camd.shift_y=.10
 for d,ang in DIRECTIONS.items():
  R=Matrix.Rotation(ang,3,'Z');root.location=R@Vector((-.70,-.42,.23));root.rotation_euler.z=ang
  for k,v in companions.items():
   v['collection'].hide_render=False;v['root'].location=R@Vector({'floor':(0,0,0),'entry':(0,-1.5,0),'hut':(.78,.35,.23)}[k]);v['root'].rotation_euler.z=ang
  pose('upgraded-dock-ready',0);path=OUT/('family-PROVISIONAL-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'kind':'native physical family context; PROVISIONAL equipment','clip':'upgraded-dock-ready','direction':d,'path':str(path.relative_to(OBJ)),'sha256':sha(path),'rootMatrix':[vv(r) for r in root.matrix_world],'frame':[1280,1536],'cameraMatrix':[vv(r) for r in cam.matrix_world],'orthoScale':6,'shiftY':.10,'nativeScale':'Same256px/Xworld as body; larger canvas context, no physical scaling or warps','companionCameraDisclosure':'Single physical scene at main65degree; companions own standalone square55degree captures remain distinct; not pixelidentity claim.'})
 dump(OUT/'representative-captures.json',records)
