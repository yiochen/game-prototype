"""Portable native sofa reconstruction. Blender5.2.2. No repository imports.
Usage: blender -b --python recipe-round01.py -- --round round-01 [--preview]
Input .blend/actions and records live beside this file in resources/.
"""
import bpy, math, json, pathlib, sys, hashlib, argparse
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent; OBJ=P.parent
arg=argparse.ArgumentParser();arg.add_argument('--round',default='round-01');arg.add_argument('--preview',action='store_true');args=arg.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=OBJ/'candidates'/args.round;OUT.mkdir(parents=True,exist_ok=True)
rig=json.loads((P/'resources/original-rig.json').read_text());camera_source=json.loads((P/'resources/original-camera.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'resources/original-library.blend'))
root=bpy.data.objects['garbage-sofa__root'];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc
coll=next(c for c in bpy.data.collections if root in list(c.objects))
# Remove unrelated scenes/data before editable delivery. Source input remains byte exact.
for c in sc.collection.children:c.hide_render=False;c.hide_viewport=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=False
bpy.context.view_layer.update()
originals=[o for o in coll.objects if o.type=='MESH'];native_roles={o.name: {'matrix':o.matrix_world.copy(),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)} for o in originals}
for o in list(bpy.data.objects):
 if o!=root and o not in originals:bpy.data.objects.remove(o,do_unlink=True)
for o in originals:
 name=o.name;mat=o.matrix_world.copy();bpy.data.objects.remove(o,do_unlink=True);c=bpy.data.objects.new(name,None);coll.objects.link(c);c.parent=root;c.matrix_world=mat;c.empty_display_size=.04;c['semantic_source_role']=name
carriers={n:bpy.data.objects[n] for n in native_roles}
for c in list(bpy.data.collections):
 if c!=coll:bpy.data.collections.remove(c)
# Preserve only the sofa's actual named native actions, without re-baking.
keep={x['action'] for r in rig['clips'].values() for x in r['actions']}
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
root['native_semantic_mapping']='semantic-driver-map.json';root['sourceScale']=2

def color(h):
 s=[int(h[i:i+2],16)/255 for i in (0,2,4)];return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in s)
def material(name,h,rough=.75,var=.035):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*color(h),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.24
 bs.inputs['Emission Color'].default_value=(*color(h),1);bs.inputs['Emission Strength'].default_value=.055;l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 if var:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=1.4;tc=n.new('ShaderNodeTexCoord');tc.object=root;l.new(tc.outputs['Object'],tex.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.15;r.color_ramp.elements[0].color=tuple(x*(1-var) for x in color(h))+(1,);r.color_ramp.elements[1].position=.85;r.color_ramp.elements[1].color=tuple(min(1,x*(1+var)) for x in color(h))+(1,);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs['Color'],bs.inputs['Base Color'])
 if var and 'cloth' in name.lower():
  tc2=n.new('ShaderNodeTexCoord');tc2.object=root;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7.5;noise.inputs['Detail'].default_value=1.6;noise.inputs['Roughness'].default_value=.7;l.new(tc2.outputs['Object'],noise.inputs['Vector']);mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.62;mask.color_ramp.elements[0].color=(0,0,0,1);mask.color_ramp.elements[1].position=.73;mask.color_ramp.elements[1].color=(.45,.45,.45,1);l.new(noise.outputs['Fac'],mask.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';l.new(mask.outputs['Color'],mix.inputs[0]);l.new(r.outputs['Color'],mix.inputs[1]);mix.inputs[2].default_value=tuple(v*.72 for v in color(h))+(1,);l.new(mix.outputs[0],bs.inputs['Base Color'])
 return m
rose=material('Faded warm rose cloth','BD817C');rose_dark=material('Shadow rose cloth','AE706B');rose_light=material('Soft raised piping','CA9184',.78,.015);cream=material('Cream replacement cloth','CDC2AB');cream_seam=material('Cream seam','C3A477');wood=material('Honey wood rail','A7642F',.58,.07);wood_end=material('Wood end grain','88532F',.75,.05);dark=material('Tear inner cloth','704B47',.95,0);patch=material('Worn ochre repair cloth','89724F',.95,.06);thread=material('Golden repair stitches','D4AB63',.85,0);stuff=material('Ivory cotton filling','EAD9AA',.95,.025);metal=material('Old brass spring','9C7B42',.5,0);rubble=material('Rubbish stone','877562',.96,.06);stain=material('Muted worn cloth','A46D60',.98,.04)

def carrier(role):return carriers['garbage-sofa__'+role]
def attach(o,role,name,mat):
 c=carrier(role);o.name=role+'__'+name
 for cc in list(o.users_collection):cc.objects.unlink(o)
 coll.objects.link(o);wm=o.matrix_world.copy();o.parent=c;o.matrix_world=wm
 if mat:o.data.materials.clear();o.data.materials.append(mat)
 o['semantic_carrier']=c.name
 return o

def box(role,name,loc,dims,mat,bevel=.05,rot=(0,0,0),soft=True):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Rounded upholstered edge' if soft else 'Crafted edge','BEVEL');mod.width=bevel;mod.segments=5 if soft else 3
  bpy.ops.object.modifier_apply(modifier=mod.name)
 if soft:
  mod=o.modifiers.new('Broad soft cushion curvature','SUBSURF');mod.levels=2;mod.render_levels=2;bpy.ops.object.modifier_apply(modifier=mod.name)
  # Very gentle inflation of the broad panel faces, bounded at the authored extent.
  hx,hy,hz=[d*.5 for d in dims]
  for v in o.data.vertices:
   x,y,z=v.co
   if abs(z)>hz*.55:
    bump=.024*max(0,1-(x/hx)**2)*max(0,1-(y/hy)**2)
    if 'compressed_seat' in name and z>0:bump-=.012*math.exp(-((x/hx)**2+(y/(hy*.8))**2)*2)
    v.co.z += math.copysign(bump,z)
   # Native broad panel convexity gives cloth dimensional volume rather than planar slabs.
   if abs(x)>hx*.55:v.co.x += math.copysign(.010*max(0,1-(y/hy)**2)*max(0,1-(z/hz)**2),x)
   if abs(y)>hy*.55:v.co.y += math.copysign(.018*max(0,1-(x/hx)**2)*max(0,1-(z/hz)**2),y)
   # Paired shallow compression folds in actual seat surfaces.
   if 'compressed_seat' in name and z>hz*.65:
    v.co.z-=.008*math.exp(-((abs(x)-hx*.60)/.045)**2-((y+hy*.40)/.12)**2)
 for p in o.data.polygons:p.use_smooth=True
 return attach(o,role,name,mat)

def tube(role,name,pts,rad,mat,cyclic=False):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=rad;c.bevel_resolution=3;c.resolution_u=12
 s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);sc.collection.objects.link(o);return attach(o,role,name,mat)

def outline(role,name,center,half,plane,rad,mat,corner=.05,surface=None,side=1):
 # Rounded rectangle, with 7 points per corner. Surface plane is XY, XZ or YZ.
 points=[]
 for sx,sy,a in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
  for j in range(7):
   t=math.radians(a+j*90/6);u=sx*(half[0]-corner)+corner*math.cos(t);v=sy*(half[1]-corner)+corner*math.sin(t)
   if plane=='XY':p=(center[0]+u,center[1]+v,center[2])
   elif plane=='XZ':p=(center[0]+u,center[1],center[2]+v)
   else:p=(center[0],center[1]+u,center[2]+v)
   if surface:
    bpy.context.view_layer.update()
    axis=2 if plane=='XY' else 1 if plane=='XZ' else 0
    start=Vector(p);start[axis]=side*3;direction=Vector((0,0,0));direction[axis]=-side
    inv=surface.matrix_world.inverted();hit,loc,normal,face=surface.ray_cast(inv@start,inv.to_3x3()@direction)
    if hit:p=surface.matrix_world@loc+surface.matrix_world.to_3x3()@normal*.001
   points.append(p)
 return tube(role,name,points,rad,mat,True)

def sphere(role,name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return attach(o,role,name,mat)
# Main crafted understructure and sealed underside, all on base carrier.
box('base','wooden_understructure',(0,0,.25),(1.85,1.07,.22),wood,.045,soft=False)
box('base','underside_dust_cloth',(0,0,.143),(1.60,.86,.018),patch,.035,soft=False)
box('base','front_wood_lip',(0,-.541,.28),(1.65,.045,.12),wood,.015,soft=False)
box('base','rear_wood_lip',(0,.541,.28),(1.65,.045,.12),wood,.015,soft=False)
for x in [-.75,.75]:
 for y in [-.39,.39]:
  role='foot_'+str(x)+'_'+str(y)
  box(role,'tapered_wood_support',(x,y,.105),(.17,.18,.21),wood_end,.024,soft=False)
# Arms stay generous but inside2x2. Continuous rounded panels and end seams.
for x in [-.84,.84]:
 role='old_arm_'+str(x)
 arm=box(role,'arm',(x,-.04,.565),(.267,1.16,.535),rose,.095)
 outline(role,'front_arm_seam',(x,-.601,.565),(.116,.235),'XZ',.004,rose_light,.075,surface=arm,side=-1)
 outline(role,'top_arm_seam',(x,-.035,.819),(.106,.495),'XY',.004,rose_light,.075,surface=arm,side=1)
 # Native small fabric patch set into outer side, readable from opposite facing.
 side=x+math.copysign(.139,x)
 box(role,'side_repair',(side,.20,.56),(.008,.18,.14),rose_dark,.025,soft=False)
 for yy in [.14,.20,.26]:tube(role,'side_repair_stitch'+str(yy),[(side+math.copysign(.005,x),yy,.485),(side+math.copysign(.005,x),yy,.51)],.0035,thread)
# Tall soft continuous back shell, with integrated rear upholstery and piping.
back=box('old_back','soft_back',(0,.421,.713),(1.90,.30,.68),rose,.11,rot=(.035,0,.006))
outline('old_back','rear_perimeter_seam',(0,.574,.72),(.865,.275),'XZ',.0045,rose_light,.08,surface=back,side=1)
# Two rear stitched cloth subdivisions, visible in rear facing.
for x in [-.31,.31]:tube('old_back','rear_vertical_seam'+str(x),[(x,.576,.46),(x,.581,.70),(x,.570,.96)],.004,rose_dark)
# Cushions deliberately fuller, separate on original motion roles.
for i,x in enumerate([-.49,0,.49]):
 role='sagging_seat_'+str(i);mat=cream if i==1 else rose
 seat=box(role,'compressed_seat',(x,-.178,.465),(.460,.79,.215),mat,.072,rot=(0,.014*i,.012*(i-1)))
 outline(role,'seat_piping',(x,-.178,.520),(.216,.363),'XY',.0045,cream_seam if i==1 else rose_light,.060,surface=seat)
 # Broad stitched front panel seam continues down the front face.
 tube(role,'seat_front_seam',[(x-.17,-.565,.452),(x,-.575,.446),(x+.17,-.565,.452)],.004,cream_seam if i==1 else rose_dark)
 role='old_back_cushion_'+str(i)
 pillow=box(role,'puffy_back_pillow',(x,.171,.783),(.460,.305,.425),rose,.085,rot=(.075,0,.016*(i-1)))
 outline(role,'pillow_front_piping',(x,.018,.798),(.207,.166),'XZ',.004,rose_light,.07,surface=pillow,side=-1)
# Repair patch: native dimensional sewn cloth on left cushion.
box('torn_fabric','sewn_repair_patch',(-.47,-.28,.577),(.21,.16,.014),patch,.018,rot=(0,0,-.18),soft=False)
for j in range(4):
 xx=-.55+j*.052
 tube('torn_fabric','patch_thread_front'+str(j),[(xx,-.371,.579),(xx+.008,-.345,.586)],.004,thread)
 tube('torn_fabric','patch_thread_back'+str(j),[(xx,-.214,.579),(xx+.008,-.189,.581)],.004,thread)
for j in range(3):
 yy=-.33+j*.051
 tube('torn_fabric','patch_thread_left'+str(j),[(-.587,yy,.578),(-.563,yy+.005,.585)],.004,thread)
 tube('torn_fabric','patch_thread_right'+str(j),[(-.376,yy,.584),(-.349,yy+.005,.578)],.004,thread)
# Source stuffing retains its own independent role as small cotton visible through repair.
box('exposed_stuffing','cream_patch_center',(-.47,-.28,.588),(.075,.062,.012),cream,.010,rot=(0,0,-.18),soft=False)
# Native torn seat at right: dark recessed gash, rose lip, cotton tufts and brass spring.
# These details share the independently contracted exposed_spring carrier.
pts=[(.32,-.40,.572),(.39,-.34,.579),(.44,-.285,.583),(.53,-.20,.576),(.58,-.14,.570)]
# Cut a dimensional jagged aperture into the actual seat cushion, then line its floor.
seat=next(o for o in coll.objects if o.name=='sagging_seat_2__compressed_seat')
polygon=[(.305,-.414),(.385,-.352),(.398,-.346),(.432,-.309),(.456,-.29),(.49,-.246),(.55,-.188),(.594,-.128),(.565,-.166),(.526,-.191),(.487,-.223),(.451,-.26),(.421,-.278),(.39,-.321),(.354,-.35)]
vs=[(x,y,z) for z in [.525,.64] for x,y in polygon];n=len(polygon);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
me=bpy.data.meshes.new('Native jagged tear cutter');me.from_pydata(vs,[],faces);me.update();cut=bpy.data.objects.new('tear construction cutter',me);sc.collection.objects.link(cut);bpy.context.view_layer.update()
bpy.context.view_layer.objects.active=seat;mod=seat.modifiers.new('Native open torn cloth aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Low lining belongs to the seat; exposed fill/spring retains its own contracted motion role.
box('sagging_seat_2','tear_inner_lining',(.45,-.275,.528),(.29,.27,.012),dark,.03,soft=False)
tube('sagging_seat_2','rolled_torn_lip',[(x-.017,y-.012,z-.008) for x,y,z in pts],.0045,rose_dark)
for j,(x,y,z) in enumerate(pts[1:4]):sphere('exposed_spring','seat_cotton_'+str(j),(x,y,z-.012),(.022,.026,.016),stuff)
coil=[]
for j in range(65):
 t=j/64;coil.append((.47+.018*math.sin(t*math.tau*3),-.278+t*.12,.562+.013*math.cos(t*math.tau*3)))
tube('exposed_spring','brass_spring',coil,.0038,metal)
# Back damage attached to the continuous back: restrained repair and cotton cue.
box('old_back','rear_damage_patch',(.59,.578,.78),(.18,.014,.15),patch,.018,soft=False)
for x in [.52,.58,.64]:tube('old_back','rear_patch_stitch'+str(x),[(x,.590,.70),(x+.007,.590,.735)],.004,thread)
# Rubbish rests on z0 by native geometry, driver pivots are untouched.
for i,(x,y,d,zrot) in enumerate([(-.83,-.79,.18,-.18),(.74,-.78,.21,0),(-.65,.80,.16,.18)]):
 role='loose_debris_'+str(i)
 box(role,'grounded_rubbish',(x,y,.035),(d,d*.64,.070),rubble,.015,rot=(0,0,zrot),soft=False)
 box(role,'chipped_top',(x-.015,y+.006,.071),(d*.55,d*.38,.008),wood_end,.007,rot=(0,0,zrot),soft=False)
# Camera restored from measured asset record, not the library's saved camera.
cam=bpy.data.objects.new('Registered sofa square top-front camera',bpy.data.cameras.new('Registered sofa capture'));sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(camera_source['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=.11703243851661682
sc.render.resolution_x=896;sc.render.resolution_y=1152;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1.2206555604934692;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True
# Fourfold equal broad lights and overhead: one scene for every facing and phase.
lights=[]
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=(1,.91,.80);o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
area('Broad centered warm overhead',(0,0,4.5),105,4)
for i,(x,y) in enumerate([(3,0),(0,3),(-3,0),(0,-3)]):area('Equal cardinal soft fill '+str(i),(x,y,2.5),45,4)
world=bpy.data.worlds.new('Horizontally uniform soft world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.88,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.12;sc.world=world
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=8
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12
# Portable direct binding of the retained actual native actions.
def apply(clip,f,d='S'):
 for n,c in carriers.items():
  if c.animation_data:c.animation_data.action=None
 for t in rig['clips'][clip]['actions']:
  c=carriers[t['ownerName']];c.animation_data_create();a=bpy.data.actions[t['action']];c.animation_data.action=a
  if a.slots:
   c.animation_data.action_slot=next((s for s in a.slots if s.identifier==t['slotIdentifier']),a.slots[0])
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];sc.frame_start=1;sc.frame_end=rig['clips'][clip]['frames'];sc.frame_set(int(f),subframe=float(f)%1);bpy.context.view_layer.update()
def rows(m):return [[float(v) for v in r] for r in m]
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*896,(1-p.y)*1152]
def measure(clip,f,d):
 dg=bpy.context.evaluated_depsgraph_get();parts=[];allp=[]
 for o in coll.all_objects:
  if o.type not in ['MESH','CURVE']:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();allp+=ps;parts.append({'name':o.name,'carrier':o.parent.name,'bounds':bounds(ps)})
 return {'clip':clip,'direction':d,'frame':f,'rootRotationZ':float(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'localBounds':bounds(allp),'parts':parts,'drivers':{n:{'location':list(c.location),'rotation':list(c.rotation_euler),'scale':list(c.scale),'matrixLocal':rows(c.matrix_local)} for n,c in carriers.items()}}
apply('idle',1,'S')
for datablocks in [bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.images,bpy.data.cameras,bpy.data.lights,bpy.data.worlds]:
 for data in list(datablocks):
  if data.users==0:datablocks.remove(data)
# Neutral default S pose in self-contained editable project; all60 original actions retained.
bpy.ops.wm.save_as_mainfile(filepath=str(P/(args.round+'.blend')))
camera_record={'projection':'top-down-oblique-square-grid','frame':[448,576],'anchor':[224,352],'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=896,y=1152,scale_x=sc.render.pixel_aspect_x,scale_y=1)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'elevationDegrees':55.00797980144134},'calibration':{k:px(v) for k,v in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()},'nativeFrame':[896,1152]}
(OUT/'camera.json').write_text(json.dumps(camera_record,indent=2)+'\n')
asset_record={'id':'garbage-sofa','projection':'top-down-oblique-square-grid','frame':[448,576],'anchor':[224,352],'scale':2,'footprint':[2,2],'height':1.08,'directions':['N','E','S','W'],'clips':{k:{x:r[x] for x in ['frames','fps','loop','static'] if x in r} for k,r in rig['clips'].items()},'sockets':{},'groundRootObject':root.name,'semanticDrivers':list(carriers),'nativeGeometryCount':sum(o.type in ['MESH','CURVE'] for o in coll.objects)}
(OUT/'asset.json').write_text(json.dumps(asset_record,indent=2)+'\n');(OUT/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
lighting={'symmetry':'Fourfold equal cardinal native AREA fills plus centered overhead and uniform world; no ground plane in sprite scene','lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in lights],'worldStrength':.12,'materialsOpaque':all(m.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value==1 for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')),'viewTransform':sc.view_settings.view_transform,'engine':sc.render.engine,'samples':sc.cycles.samples}
(OUT/'lighting.json').write_text(json.dumps(lighting,indent=2)+'\n')
ledger=[]
for clip,r in rig['clips'].items():
 for d in ['N','E','S','W']:
  indices=range(1,r['frames']+1)
  if args.preview:indices=[1] if clip!='clearance' else [6,12]
  for f in indices:
   apply(clip,f,d);entry=measure(clip,f,d);path=OUT/'frames'/(clip+'-'+d)/('%03d.png'%(f-1));path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);entry['path']=str(path.relative_to(OBJ));ledger.append(entry)
(OUT/'candidate-phases.json').write_text(json.dumps(ledger,indent=2)+'\n')
# Dense in-between native geometry bounds and exact source-driver transform checks.
dense=[]
for clip,r in rig['clips'].items():
 for j in range((r['frames']-1)*4+1):
  f=1+j*.25;apply(clip,f);e=measure(clip,f,'S');dense.append({'clip':clip,'frame':f,'localBounds':e['localBounds'],'drivers':e['drivers']})
apply('highlighted',13);closure=measure('highlighted',13,'S')
apply('highlighted',1);start=measure('highlighted',1,'S')
(OUT/'dense-native-measurements.json').write_text(json.dumps({'samples':dense,'highlightedClosure':closure,'highlightedStart':start},indent=2)+'\n')
(OUT/'resource-audit.json').write_text(json.dumps({'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'fonts':[f.filepath for f in bpy.data.fonts],'externalObjects':[o.name for o in coll.all_objects if o.library or (o.data and o.data.library)],'sourceBackupSHA256':hashlib.sha256((P/'resources/original-library.blend').read_bytes()).hexdigest(),'renderCount':len(ledger)},indent=2)+'\n')
print('SOFA_NATIVE_COMPLETE',args.round,len(ledger))
