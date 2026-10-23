"""Portable garbage-car native rebuild. Blender5.2: -b --python build_round01.py -- [--full]."""
import bpy,json,math,sys,hashlib,pathlib,copy
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent;RES=P/'source/resources';OUT=P/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(RES));import native_actions as A
rig=json.loads((RES/'source-rig.json').read_text());cr=json.loads((RES/'source-camera.json').read_text())
FULL='--full' in sys.argv
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.context.scene;sc.name='Garbage Car Warm Soft Round01'
with bpy.data.libraries.load(str(RES/'original-library.blend'),link=False) as (src,dst):
 dst.collections=['S33_PROP_garbage-car'];dst.actions=[x for x in src.actions if x.startswith('S33_NATIVE__garbage-car__')]
coll=dst.collections[0];sc.collection.children.link(coll)
for c in coll.children:c.hide_render=False;c.hide_viewport=False
coll.hide_render=False;coll.hide_viewport=False
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=False
root=bpy.data.objects['garbage-car__root'];root.hide_viewport=False;root.hide_render=False
asset={'root':root,'collection':coll}
A.apply_clip(asset,rig,'idle',1,'S',sc)
for o in coll.all_objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
source_objs=[o for o in coll.all_objects if o.type=='MESH'];source_info={};drivers={};idle_matrices={}
for o in source_objs:
 source_info[o.name]={'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(r) for r in o.matrix_local]}
 idle_matrices[o.name]=o.matrix_local.copy()
 oldname=o.name;o.name=oldname+'__retired'
 d=bpy.data.objects.new(oldname,None);coll.objects.link(d);d.parent=root;d.matrix_local=idle_matrices[oldname]
 d['sourceRole']=oldname;d['trajectory']='exact original native action cohort';drivers[oldname]=d
 # Preserve source mesh data for glass and frame reconstruction separately below.
 o['sourceOwnerName']=oldname
# New opaque warm materials: all surfaces are native shaders; no texture/image/opacity actions.
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def material(name,h,rough=.55,metal=.0,coat=.0):
 m=bpy.data.materials.new('GC01 '+name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');rgb=tuple(lin(int(h[i:i+2],16)/255) for i in (0,2,4));p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.38;m.diffuse_color=(*rgb,1);return m
paint=material('pale blue-gray enamel','94B3BB',.49,.06,.18);paintlight=material('roof pale blue-gray enamel','B0C9CD',.47,.04,.16);paintdark=material('turned blue-gray paint','7D9DA7',.55,.04,.12)
rust=material('warm localized rust','A87550',.85);rustlight=material('rust chipped edges','BB8D63',.85);metal=material('aged warm gray metal','A69F8E',.39,.44);metalDark=material('metal recess','686D6A',.54,.28);rubber=material('charcoal rubber','444B4D',.85);rubberlight=material('rounded tire shoulder','505859',.78);inside=material('cabin deep blue','273F49',.87);glass=material('opaque jagged blue glass','7EAFBA',.24,.08,.25);glasslight=material('glass broken edges','A8CCD2',.31,.02,.15);amber=material('cloudy amber lamp','D9AB5B',.36,.10);debris=material('discarded metal scraps','8F7B64',.87)
new=[];mapping={}
def own(obj,name,role,mat,world=True):
 obj.name='garbage-car__native__'+name
 for c in list(obj.users_collection):c.objects.unlink(obj)
 coll.objects.link(obj);obj.data.materials.clear();obj.data.materials.append(mat)
 wm=obj.matrix_basis.copy();d=drivers['garbage-car__'+role];obj.parent=d
 if world:obj.matrix_local=idle_matrices[d.name].inverted()@wm
 obj['semanticCarrier']=d.name;new.append(obj);mapping[obj.name]=d.name;return obj

def smooth(obj):
 for f in obj.data.polygons:f.use_smooth=True
 return obj

def bevel(obj,width,segments=4):
 m=obj.modifiers.new('Native rounded construction','BEVEL');m.width=width;m.segments=segments
 m=obj.modifiers.new('Stable panel normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=30
 return obj

def box(name,loc,dim,mat,role,round=.03,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.scale=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if round:bevel(o,round,5)
 return own(o,name,role,mat)

def mesh(name,verts,faces,mat,role,round=0,sm=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o)
 if round:bevel(o,round,3)
 if sm:smooth(o)
 return own(o,name,role,mat)

def beam(name,a,b,r,mat,role):
 a,b=Vector(a),Vector(b);d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();bevel(o,min(r*.55,.012),3);smooth(o);return own(o,name,role,mat)

def roundrect(w,h,r,n=6):
 pts=[]
 for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(n):
   a=math.radians(start+j*90/n);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 return pts

def panel(name,center,w,h,depth,mat,role,bulge=.025,dent=None):
 # Native closed convex panel: concentric rounded-rectangle quad rings.
 xy=roundrect(w,h,min(.12,w*.22,h*.22),8);N=len(xy);verts=[(center[0],center[1],center[2]+depth/2+bulge)]
 for t in (.25,.5,.75,1):
  for x,y in xy:
   z=center[2]+depth/2+bulge*(1-t*t)
   if dent:z-=dent[2]*math.exp(-(((x*t-dent[0])/.22)**2+((y*t-dent[1])/.26)**2))
   verts.append((center[0]+x*t,center[1]+y*t,z))
 for x,y in xy:verts.append((center[0]+x,center[1]+y,center[2]-depth/2))
 faces=[(0,1+j,1+(j+1)%N) for j in range(N)]
 for ring in range(3):
  a=1+ring*N;b=a+N
  faces.extend((a+j,b+j,b+(j+1)%N,a+(j+1)%N) for j in range(N))
 a=1+3*N;b=a+N;faces.extend((a+j,b+j,b+(j+1)%N,a+(j+1)%N) for j in range(N));faces.append(tuple(range(b,b+N))[::-1])
 return mesh(name,verts,faces,mat,role,.009,True)

def chip(name,c,rx,ry,normal,mat,role,seed=0):
 # Broad deterministic irregular native paint chips, kept sparse.
 verts=[c];N=15
 u,v=Vector((1,0,0)),Vector((0,1,0))
 if normal=='side':u,v=Vector((1,0,0)),Vector((0,0,1))
 if normal=='end':u,v=Vector((0,1,0)),Vector((0,0,1))
 for i in range(N):
  a=math.tau*i/N;r=.85+.26*math.sin(i*1.73+seed)+.14*math.sin(i*4.1+seed);pt=Vector(c)+u*(math.cos(a)*rx*r)+v*(math.sin(a)*ry*r);verts.append(tuple(pt))
 if normal=='top':
  targetname={'dented_roof':'convex_dented_roof','bent_broken_hood':'crooked_convex_hood','dull_dented_body':'curved_rear_deck'}[role];target=bpy.data.objects['garbage-car__native__'+targetname]
  bpy.context.view_layer.update();ev=target.evaluated_get(bpy.context.evaluated_depsgraph_get());inv=ev.matrix_world.inverted();conformed=[]
  for v in verts:
   hit,pt,no,idx=ev.ray_cast(inv@Vector((v[0],v[1],4)),inv.to_3x3()@Vector((0,0,-1)))
   q=ev.matrix_world@pt if hit else Vector(v);conformed.append((q.x,q.y,q.z+.002))
  verts=conformed
 return mesh(name,verts,[(0,i+1,(i+1)%N+1) for i in range(N)],mat,role)

# Chassis and continuous closed body with shaped wheel arches.
box('rounded_underframe',(0,0,.32),(2.54,1.25,.20),metalDark,'chassis',.065)
# x/z outline along lower edge with two arch cutouts.
outline=[(-1.4,.30),(-1.29,.30)]
for cx in (-.94,.94):
 if cx>0:outline.append((cx-.35,.30))
 for j in range(13):
  a=math.pi-math.pi*j/12;outline.append((cx+.35*math.cos(a),.30+.35*math.sin(a)))
outline += [(1.4,.30),(1.4,.68),(1.34,.755),(-1.33,.755),(-1.4,.69)]
N=len(outline);vs=[(x,y,z) for y in (-.735,.735) for x,z in outline];fs=[tuple(range(N))[::-1],tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
mesh('arched_continuous_body',vs,fs,paint,'dull_dented_body',.035,False)
# Fenders give physically thick soft bands around all wheel arches, same body carrier.
for y in (-.76,.76):
 for cx in (-.94,.94):
  verts=[]
  for j in range(17):
   a=math.pi-math.pi*j/16
   for R in (.348,.405):verts.append((cx+R*math.cos(a),y,.30+R*math.sin(a)))
  f=mesh(f'fender_{cx}_{y}',verts,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(16)],paintdark,'dull_dented_body',.012,True)
  m=f.modifiers.new('Rolled fender thickness','SOLIDIFY');m.thickness=.035
  for k,a in enumerate((.35,1.0,2.4,2.9)):
   xx=cx+.382*math.cos(a);zz=.30+.382*math.sin(a)
   chip(f'fender_rust_{cx}_{y}_{k}',(xx,y-math.copysign(.024,-y),zz),.043,.022,'side',rust,'dull_dented_body',k)
# Door panels, seams, side trim and purposeful sparse wear.
for y in (-.755,.755):
 for x in (-.28,.30):box(f'pressed_door_{x}_{y}',(x,y,.545),(.55,.028,.31),paint,'dull_dented_body',.035)
 beam(f'center_door_seam_{y}',(0,y+math.copysign(.018,y),.38),(0,y+math.copysign(.018,y),.735),.007,metalDark,'dull_dented_body')
 for xa,xb in [(-.56,-.025),(.025,.58)]:beam(f'lower_metal_strip_{xa}_{y}',(xa,y+math.copysign(.033,y),.405),(xb,y+math.copysign(.033,y),.405),.016,metal,'dull_dented_body')
 for k,(x,z,sx,sz) in enumerate([(-1.31,.41,.075,.1),(-.61,.40,.08,.045),(.62,.43,.05,.06),(1.31,.54,.048,.06),(.29,.43,.042,.018)]):chip(f'side_chipping_{y}_{k}',(x,y+math.copysign(.035,y),z),sx,sz,'side',rust,'dull_dented_body',k+3)
panel('curved_rear_deck',(1.12,0,.765),.53,1.37,.105,paint,'dull_dented_body',.035,(.08,.18,.028))
box('rear_metal_bumper',(1.425,0,.335),(.10,1.42,.14),metal,'dull_dented_body',.035)
for y in (-.48,.48):box(f'rear_lamp_{y}',(1.407,y,.61),(.025,.24,.13),amber,'dull_dented_body',.025)
# Recessed cabin with distinguishable seats/dashboard rather than a flat black void.
box('interior_tub',(.02,0,.76),(1.24,1.12,.16),inside,'dark_cabin_interior',.065)
for x in (-.28,.30):box(f'seat_{x}',(x,.09,.81),(.35,.78,.14),metalDark,'dark_cabin_interior',.07)
# Keep and improve original separate glass/frame trajectories, native geometry only.
for o in source_objs:
 role=o['sourceOwnerName'].removeprefix('garbage-car__')
 if 'broken_side_window' in role or 'side_center_pillar' in role or 'rust_sill' in role:
  ob=o.copy();ob.data=o.data.copy();ob.animation_data_clear();sc.collection.objects.link(ob);ob.matrix_world=idle_matrices[o['sourceOwnerName']]
  ma=inside if 'dark_opening' in role else glasslight if 'right_glass' in role else glass if 'glass' in role else rust if 'rust_sill' in role else paint if 'pillar' in role else metal
  for m in list(ob.modifiers):ob.modifiers.remove(m)
  if 'metal_frame' in role or 'pillar' in role or 'handle' in role:
   bevel(ob,.014 if 'pillar' in role else .009,5);smooth(ob)
  else:
   sol=ob.modifiers.new('Native panel thickness','SOLIDIFY');sol.thickness=.012
   if 'glass' in role:bevel(ob,.004,2)
  own(ob,'rebuilt_'+role,role,ma)
for y in (-.728,.728):
 box('raised_door_handle_'+str(y),(.30,math.copysign(.796,y),.645),(.19,.045,.047),metal,'old_handle_'+str(y),.02)
# Both sloped end windows become framed deep glass areas. They retain their original separate panel drivers.
for role,pts in [('cabin_front',[(-.72,-.72,.735),(-.48,-.58,1.17),(-.48,.58,1.17),(-.72,.72,.735)]),('cabin_back',[(.87,-.72,.735),(.55,-.58,1.17),(.55,.58,1.17),(.87,.72,.735)])]:
 mesh(role+'_dark_window',pts,[(0,1,2,3)],inside,role)
 for i in range(4):beam(role+'_rounded_rim_'+str(i),pts[i],pts[(i+1)%4],.025,metal,role)
 p0,p1,p2,p3=[Vector(p) for p in pts]
 # Jagged left and right shards on end window, opening stays dark.
 for side in (0,1):
  uv=[(.06,.05),(.45,.05),(.27,.25),(.40,.40),(.19,.59),(.34,.83),(.06,.94)] if side==0 else [(.75,.05),(.95,.05),(.95,.94),(.62,.94),(.76,.72),(.63,.50),(.82,.34)]
  vv=[]
  for u,v in uv:
   pt=(p0*(1-u)+p3*u)*(1-v)+(p1*(1-u)+p2*u)*v;pt.x+=-.006 if role=='cabin_front' else .006;vv.append(tuple(pt))
  mm=mesh(role+'_broken_shard_'+str(side),vv,[tuple(range(len(vv)))],glass if side else glasslight,role)
  so=mm.modifiers.new('End glass thickness','SOLIDIFY');so.thickness=.009
 # Paired rubber seals create visible shoulder construction.
 for a,b in [(pts[0],pts[1]),(pts[3],pts[2])]:beam(role+'_paint_pillar_'+str(a[1]),a,b,.047,paintdark,role)
# Rounded roof, slightly dented, and crooked raised hood.
panel('convex_dented_roof',(.025,0,1.19),1.15,1.23,.15,paintlight,'dented_roof',.048,(.20,.14,.065))
# Native inset rim under roof; avoids independent loose decoration.
box('roof_under_rim',(.025,0,1.125),(1.14,1.22,.07),metal,'dented_roof',.065)
panel('crooked_convex_hood',(-1.08,0,.79),.60,1.34,.105,paintlight,'bent_broken_hood',.03,(-.10,.15,.03))
roofpath=roundrect(1.16,1.24,.12,8)
for j in range(len(roofpath)):
 a=roofpath[j];b=roofpath[(j+1)%len(roofpath)];beam('continuous_roof_edge_'+str(j),(a[0]+.025,a[1],1.225),(b[0]+.025,b[1],1.225),.012,metal,'dented_roof')
# sparse top edge corrosion uses native polygons on surface, follows each panel.
for role,items in [('dented_roof',[(-.51,-.43,1.267,.04,.10),(.49,.43,1.267,.055,.07),(-.43,.55,1.268,.10,.025),(.38,-.48,1.27,.035,.022)]),('bent_broken_hood',[(-1.30,-.44,.847,.045,.075),(-.87,.46,.845,.04,.07),(-1.27,.42,.847,.055,.035)]),('dull_dented_body',[(1.29,-.52,.831,.045,.07),(1.26,.51,.834,.046,.055)])]:
 for k,(x,y,z,rx,ry) in enumerate(items):chip(role+'_edge_chip_'+str(k),(x,y,z),rx,ry,'top',rust,role,k)
# Rounded tires use a lathed closed sidewall profile along local Y. Ground contact is exact0.
for x in (-.94,.94):
 for y in (-.75,.75):
  role=f'old_tire_{x}_{y}';profile=[(-.105,.15),(-.112,.22),(-.095,.265),(-.060,.29),(.06,.29),(.095,.265),(.112,.22),(.105,.15)];verts=[];seg=40
  for yy,R in profile:
   for i in range(seg):a=math.tau*i/seg;verts.append((x+R*math.cos(a),y+yy,.29+R*math.sin(a)))
  faces=[]
  for j in range(len(profile)):
   for i in range(seg):faces.append((j*seg+i,j*seg+(i+1)%seg,((j+1)%len(profile))*seg+(i+1)%seg,((j+1)%len(profile))*seg+i))
  mesh('rounded_tire_'+str(x)+'_'+str(y),verts,faces,rubber,role,0,True)
  # Sparse shallow tread crossbars, integrated on tire driver.
  for i in range(16):
   a=math.tau*i/16
   beam(f'tread_{x}_{y}_{i}',(x+.287*math.cos(a),y-.051,.29+.287*math.sin(a)),(x+.287*math.cos(a),y+.051,.29+.287*math.sin(a)),.009,rubberlight,role)
  hrole=f'rust_hub_{x}_{y}';yy=y+math.copysign(.116,y)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(x,yy,.29));o=bpy.context.object;o.scale=(.143,.025,.143);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);smooth(o);own(o,f'convex_metal_hub_{x}_{y}',hrole,metal)
  bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,location=(x,yy+math.copysign(.003,y),.29),rotation=(math.pi/2,0,0),major_radius=.139,minor_radius=.012);smooth(bpy.context.object);own(bpy.context.object,f'hub_rust_ring_{x}_{y}',hrole,rust)
# Headlights, bent bumper, plate and grounded loose scraps retain source trajectories.
for y in (-.45,.45):
 role='cloudy_headlamp_'+str(y);box('lamp_rim_'+str(y),(-1.414,y,.58),(.033,.27,.16),metal,role,.025);box('amber_lens_'+str(y),(-1.436,y,.58),(.025,.22,.115),amber,role,.022)
box('thick_bent_front_bumper',(-1.42,0,.31),(.12,1.38,.14),metal,'bent_front_bumper',.038,(0,.055,-.035))
box('loose_plate',(1.29,-.45,.10),(.28,.26,.035),metal,'loose_number_plate',.015,(0,.30,.18))
for i,o in enumerate([q for q in source_objs if 'loose_debris_' in q['sourceOwnerName']]):
 role=o['sourceOwnerName'].removeprefix('garbage-car__');loc=list(o.location);loc[2]=.04
 box('grounded_scrap_'+str(i),loc,(.18,.1152,.07),debris,role,.016,tuple(o.rotation_euler))
# Delete old meshes only after copied window data; carriers keep source names/actions.
for o in source_objs:bpy.data.objects.remove(o,do_unlink=True)
# Remove unused source mesh/material/image datablocks for self-contained project.
for db in (bpy.data.meshes,bpy.data.materials,bpy.data.images):
 for v in list(db):
  if v.users==0:db.remove(v)
# Capture exact car camera, fixed across every facing and phase.
cam=bpy.data.objects.new('GC Registered55deg Camera',bpy.data.cameras.new('GC Registered55deg Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=4.5;cam.matrix_world=Matrix(cr['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=.18205103278160095
sc.render.resolution_x=1152;sc.render.resolution_y=1664;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=cr['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device='GPU';prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();
for device in prefs.devices:device.use=device.type=='METAL'
sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=50;sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.25;sc.view_settings.gamma=1
sc.world=bpy.data.worlds.new('GC Symmetric Soft World');sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.72,.74,.73,1);bg.inputs['Strength'].default_value=.22
lights=[]
for name,pos,power,size in [('overhead',(0,0,4.5),120,4.5)]+[(f'equal_fill_{i}',(3*math.cos(i*math.pi/2),3*math.sin(i*math.pi/2),2.5),75,4.5) for i in range(4)]:
 d=bpy.data.lights.new('GC '+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=(1,.94,.85);d.use_shadow=True;o=bpy.data.objects.new('GC '+name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
# Native scripts and exact source role/key mapping records live with the project.
(OUT/'semantic-mapping.json').write_text(json.dumps({'carriers':source_info,'renderableToCarrier':mapping,'sourceRig':'source/resources/source-rig.json','sourceActionCount':len(dst.actions),'renderableMeshes':len(new)},indent=2))
asset={'root':root,'collection':coll};A.apply_clip(asset,rig,'idle',1,'S',sc)
root['refinement']='warm-soft-rounded-native-round01';root['semantic_mapping']='candidates/round-01/semantic-mapping.json'
# Bake no new motion: copied source Actions are the native clip implementation.
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01.blend'),compress=True)
(OUT/'rig.json').write_text(json.dumps(rig,indent=2))

def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*1152,(1-v.y)*1664]

def geometry():
 deps=bpy.context.evaluated_depsgraph_get();deps.update();pts=[];rows=[]
 for o in new:
  ev=o.evaluated_get(deps);me=ev.to_mesh();v=[ev.matrix_world@p.co for p in me.vertices];ev.to_mesh_clear()
  if not v:continue
  pts.extend(v);rows.append({'name':o.name,'carrier':mapping[o.name],'bounds':[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]],'vertices':len(v)})
 return {'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],'objects':rows,'projectedBounds':[[min(px(p)[i] for p in pts) for i in range(2)],[max(px(p)[i] for p in pts) for i in range(2)]]}

def carrier_states():return {n:{'location':list(d.location),'rotationEuler':list(d.rotation_euler),'scale':list(d.scale),'matrix':[list(row) for row in d.matrix_world]} for n,d in drivers.items()}

def apply(clip,frame,direction):
 A.apply_clip(asset,rig,clip,1,direction,sc);sc.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()

def render(clip,direction,frame,path):
 apply(clip,frame,direction);sc.render.filepath=str(path);path.parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
 return {'clip':clip,'direction':direction,'index':int(frame-1),'sourceFrame':frame,'path':str(path.relative_to(P)),'rootRotationZ':float(root.rotation_euler.z),'rootMatrix':[list(row) for row in root.matrix_world],'geometry':geometry(),'carriers':carrier_states()}
frames=[]
if FULL:
 for clip,c in rig['clips'].items():
  for dr in ('N','E','S','W'):
   for fr in range(1,c['frames']+1):frames.append(render(clip,dr,fr,OUT/'frames'/f'{clip}-{dr}'/f'{fr-1:03d}.png'))
 closure=[]
 for dr in ('N','E','S','W'):closure.append(render('highlighted',dr,13,OUT/'diagnostics'/f'highlighted-{dr}-key13.png'))
 # Inbetween bounds and copied-carrier evidence at every half phase.
 inbetweens=[]
 for clip in ('highlighted','clearance'):
  for fr in [1.5+i for i in range(11)]+([12.5] if clip=='highlighted' else []):
   apply(clip,fr,'S');inbetweens.append({'clip':clip,'frame':fr,'direction':'S','rootRotationZ':float(root.rotation_euler.z),'geometry':geometry(),'carriers':carrier_states()})
 (OUT/'native-audit.json').write_text(json.dumps({'blender':bpy.app.version_string,'project':'source/round-01.blend','frames':frames,'closure':closure,'inbetweens':inbetweens,'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size,'shadow':o.data.use_shadow} for o in lights],'materials':[{'name':m.name,'alpha':m.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value,'nodes':[n.bl_idname for n in m.node_tree.nodes]} for m in bpy.data.materials if m.users>0],'resources':{'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath} for x in bpy.data.images if x.users>0]}},indent=2))
else:
 for dr in ('N','E','S','W'):frames.append(render('idle',dr,1,OUT/'draft04'/f'idle-{dr}.png'))
 for fr in (4,8,12):frames.append(render('clearance','S',fr,OUT/'draft04'/f'clearance-S-{fr:02d}.png'))
 (OUT/'draft04/audit.json').write_text(json.dumps({'frames':frames},indent=2))
zero=px((0,0,0));camera={'projection':'top-down-oblique-square-grid','frame':[576,832],'anchor':[288,544],'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1152,y=1664,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':zero,'unitX':[a-b for a,b in zip(px((1,0,0)),zero)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),zero)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),zero)]}}
(OUT/'camera.json').write_text(json.dumps(camera,indent=2));ar=json.loads((P/'inputs/source-assetRecord.json').read_text());ar['scale']=2;ar['artStyle']={'revision':'warm-soft-native-round01','lighting':'overhead plus four identical cardinal soft fills and uniform world; no ground/shadow mesh'};(OUT/'assetRecord.json').write_text(json.dumps(ar,indent=2))
print('NATIVE ROUND01 COMPLETE',len(new),len(frames))
