"""Native Mateo refinement. No raster modification; stable rest-space meshes.
Run on source/original-library.blend. The saved result includes only Mateo,
its original action cohort, packed salmon insert, registered camera and lights.
"""
import bpy, bmesh, json, math, sys, importlib.util, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent; OBJECT=HERE.parent
BASE=HERE.parents[3]/'production/source/blender'
OUT=OBJECT/'candidates/round01'; OUT.mkdir(parents=True,exist_ok=True)
brief=json.loads((OBJECT/'brief.json').read_text())
assert brief['qualityCriteria'].get('version')==1, 'Await coordinator-frozen outcomes'
rig=json.loads((OBJECT/'inputs/source-rig.json').read_text())
assetrec=json.loads((OBJECT/'inputs/source-assetRecord.json').read_text())
assetrec['scale']=2
root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in bpy.data.collections if root in list(c.objects))
scene=bpy.data.scenes.new('Mateo warm soft native round01')
scene['source']='native_actions.py';scene['issue']=33
scene['asset']='chef-mateo';scene.collection.children.link(collection)
bpy.context.window.scene=scene;collection.hide_render=False;collection.hide_viewport=False
for o in collection.all_objects:o.hide_set(False)
arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
arm.data.pose_position='REST';root.rotation_euler.z=0
bpy.context.view_layer.update()
parts={o.name.split('__',1)[-1].replace('.001',''):o for o in collection.all_objects}

def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
native=loadmod('mateo_round01_native_actions',HERE/'native_actions.py')
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,color,rough=.5,spec=.25,metal=0):
 m=bpy.data.materials.new('Mateo warm soft '+name);m.use_nodes=True
 rgb=tuple(linear(int(color[i:i+2],16)/255) for i in (0,2,4));m.diffuse_color=(*rgb,1)
 ns=m.node_tree.nodes;ns.clear();p=ns.new('ShaderNodeBsdfPrincipled');o=ns.new('ShaderNodeOutputMaterial')
 p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Specular IOR Level'].default_value=spec;m.node_tree.links.new(p.outputs['BSDF'],o.inputs['Surface'])
 return m
mats={
 'skin':mat('tan amber skin','DE9760',.5,.08),
 'white':mat('ivory cotton','FFF4DE',.58,.2),
 'blue':mat('blue apron canvas','2473C7',.52,.09),
 'blue_edge':mat('blue sewn edges','337FD0',.55,.22),
 'red':mat('red folded cloth','D94C42',.5,.09),
 'red_edge':mat('red folded seam','E35B4B',.56,.22),
 'hair':mat('warm brown hair','4D2B24',.42,.15),
 'hair_light':mat('warm brown swept lock','5A342C',.42,.15),
 'navy':mat('dark shoes','253348',.47,.26),
 'eye':mat('polished dark eyes','241918',.23,.35),
 'blush':mat('soft cheeks','D8776B',.62,.14),
 'metal':mat('satin knife steel','9AB0B8',.36,.28,.45),
 'wood':mat('knife handle brown','493027',.5,.22),
}
def activate(o):
 for x in bpy.context.selected_objects:x.select_set(False)
 o.select_set(True);bpy.context.view_layer.objects.active=o
def bake_before_armature(o):
 activate(o)
 for mod in list(o.modifiers):
  if mod.type=='ARMATURE':break
  bpy.ops.object.modifier_apply(modifier=mod.name)
def smooth(o):
 for p in o.data.polygons:p.use_smooth=True
def addmesh(name,vertices,faces,material,bone=None,weights=None):
 me=bpy.data.meshes.new('Mateo native '+name);me.from_pydata(vertices,[],faces);me.update()
 o=bpy.data.objects.new('chef_mateo__refined_'+name,me);collection.objects.link(o);o.parent=root;o.data.materials.append(mats[material])
 if weights:
  groups={n:o.vertex_groups.new(name=n) for n in set(k for w in weights for k in w)}
  for i,w in enumerate(weights):
   for n,v in w.items():
    if v>0:groups[n].add([i],v,'REPLACE')
 elif bone:
  g=o.vertex_groups.new(name=bone);g.add(list(range(len(vertices))),1,'REPLACE')
 if weights or bone:
  m=o.modifiers.new('Original native armature','ARMATURE');m.object=arm
 o['native_refinement']='Modeled in original common rest space; original armature/actions'
 smooth(o);return o
def bevel(o,width=.006,segments=4):
 m=o.modifiers.new('Baked rounded tailored edge','BEVEL');m.width=width;m.segments=segments
 # Move ahead of armature so its topology is baked before deformation.
 idx=list(o.modifiers).index(m)
 while idx>0:o.modifiers.move(idx,idx-1);idx-=1
 bake_before_armature(o);smooth(o)
def replace(o,vertices,faces):
 me=bpy.data.meshes.new(o.name+' warm native geometry');me.from_pydata(vertices,[],faces);me.update()
 material=o.data.materials[0] if o.data.materials else None;o.data=me
 if material:o.data.materials.append(material)
 return o
def delete(o):bpy.data.objects.remove(o,do_unlink=True)
def signed(v,p):return math.copysign(abs(v)**p,v)
def ellipsoid(name,loc,scale,material,bone='head',nu=40,nv=24):
 verts=[]
 for j in range(nv+1):
  a=-math.pi/2+math.pi*j/nv
  for i in range(nu):
   t=math.tau*i/nu;verts.append((loc[0]+scale[0]*math.cos(a)*math.cos(t),loc[1]+scale[1]*math.cos(a)*math.sin(t),loc[2]+scale[2]*math.sin(a)))
 faces=[(j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i) for j in range(nv) for i in range(nu)]
 return addmesh(name,verts,faces,material,bone)
def tube(name,path,radius,material,bone,segments=8,weights=None):
 closed=(Vector(path[0])-Vector(path[-1])).length<1e-8
 if closed:path=path[:-1]
 vs=[];faces=[]
 for j,p in enumerate(path):
  p=Vector(p)
  lo=(j-1)%len(path) if closed else max(0,j-1)
  hi=(j+1)%len(path) if closed else min(j+1,len(path)-1)
  t=(Vector(path[hi])-Vector(path[lo])).normalized();ref=Vector((0,1,0))
  if abs(t.dot(ref))>.95:ref=Vector((1,0,0))
  u=t.cross(ref).normalized();v=t.cross(u).normalized()
  for i in range(segments):
   a=math.tau*i/segments;vs.append(tuple(p+radius*(u*math.cos(a)+v*math.sin(a))))
 faces=[] if closed else [tuple(reversed(range(segments))),tuple(range((len(path)-1)*segments,len(path)*segments))]
 faces += [(j*segments+i,j*segments+(i+1)%segments,((j+1)%len(path))*segments+(i+1)%segments,((j+1)%len(path))*segments+i) for j in range(len(path) if closed else len(path)-1) for i in range(segments)]
 return addmesh(name,vs,faces,material,bone)
def padded_leaf(name,outline,y,thickness,material,bone):
 # Native closed solid, bevel baked in rest space.
 n=len(outline);vs=[(x,y,z) for x,z in outline]+[(x,y+thickness,z) for x,z in outline]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=addmesh(name,vs,fs,material,bone);bevel(o,min(.006,thickness*.4),4);return o

# Replace the old world-height shaders with a single rotation-independent finish.
for o in list(collection.all_objects):
 if o.type!='MESH' or '__held_dish' in o.name:continue
 for i,m in enumerate(list(o.data.materials)):
  n=m.name
  key='skin' if 'skin_mateo' in n else 'hair_light' if '5A342C' in n else 'hair' if 'hair_brown' in n else 'white' if 'white' in n else 'blue' if 'blue' in n else 'red' if 'red' in n else 'eye' if 'eye' in n else 'blush' if 'blush' in n else 'metal' if 'metal' in n else 'wood' if 'wood_dark' in n else 'navy'
  o.data.materials[i]=mats[key]
 # Source palms/feet retain the exact rounded-box extents and centers.
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=6
 if not any(s in o.name for s in ('rounded_','quiff','headband','kerchief_tail','smile','apron_skirt','apron_pocket')):
  bake_before_armature(o);smooth(o)

# Flowing sculpted hair instead of low-poly beadlike masses.
for name,o in list(parts.items()):
 if any(s in name for s in ('rounded_crown','rounded_occiput','quiff')):delete(o)
ellipsoid('hair_crown',(0,.025,.8572),(.285,.250,.157),'hair')
ellipsoid('hair_occiput',(0,.123,.7132),(.267,.188,.207),'hair')
for sign in [-1,1]:
 ellipsoid('hair_temple_'+str(sign),(sign*.261,.025,.788),(.058,.137,.10),'hair')
for i,x in enumerate([-.18,0,.18]):
 ellipsoid('hair_nape_'+str(i),(x,.238,.775),(.095,.074,.113),'hair_light' if i==1 else 'hair')
for i,x in enumerate([-.18,-.06,.06,.18]):
 verts=[];nu=32;nv=24
 for j in range(nv+1):
  t=j/nv;rad=math.sin(math.pi*t)**.55
  cx=x+.025*math.sin(math.pi*t)-.023*t
  cy=.19-.47*t
  z=.910+.115*math.sin(math.pi*t)-.067*t+(.007 if i==1 else 0)
  tangent=Vector((0,-.47,.115*math.pi*math.cos(math.pi*t)-.067)).normalized()
  normal=Vector((0,-tangent.z,tangent.y))
  for k in range(nu):
   a=math.tau*k/nu
   q=Vector((cx+(.085 if i in [1,2] else .078)*rad*math.cos(a),cy,z))+normal*(.058*rad*math.sin(a))
   # Keep the high volume over the source frontal quiff, so the unchanged
   # forward work tilt has the original head clearance rather than a high rear crown.
   q.y-=.100*max(0,min(1,(q.z-.900)/.120))
   verts.append(tuple(q))
 faces=[(j*nu+k,j*nu+(k+1)%nu,(j+1)*nu+(k+1)%nu,(j+1)*nu+k) for j in range(nv) for k in range(nu)]
 addmesh('swept_sculpted_fringe_'+str(i),verts,faces,'hair_light' if i==1 else 'hair','head')

# One closed folded cloth band wraps the head with rounded front, side and back.
for n in ['headband','headband_back','headband_tails']:delete(parts[n])
nu=96;vs=[]
for j in range(9):
 t=j/8
 for i in range(nu):
  a=math.tau*i/nu;radial=.003*math.sin(math.pi*t)+.003*math.sin(3*math.pi*t)
  x=(.323-.023*t+radial)*signed(math.cos(a),.55)
  sy=signed(math.sin(a),.55)
  y=(.302-.027*t+radial if sy>=0 else .267+radial)*sy
  # Lower frontal fold, with a raised rear wrap seen from the registered view.
  base=.811+.025*(math.sin(a)+1)/2
  z=base+.079*t+.002*math.sin(2*a+.3)*math.sin(math.pi*t)
  vs.append((x,y,z))
fs=[(j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i) for j in range(8) for i in range(nu)]
band=addmesh('folded_wrapped_red_band',vs,fs,'red','head')
solid=band.modifiers.new('Native fabric thickness','SOLIDIFY');solid.thickness=.008;solid.offset=-1
band.modifiers.move(len(band.modifiers)-1,0);bake_before_armature(band)
for t,name in [(.10,'lower'),(.87,'upper')]:
 path=[]
 for i in range(nu+1):
  a=math.tau*i/nu;radial=.003*math.sin(math.pi*t)+.003*math.sin(3*math.pi*t)
  sy=signed(math.sin(a),.55)
  path.append(((.324-.023*t+radial)*signed(math.cos(a),.55),(.303-.027*t+radial if sy>=0 else .268+radial)*sy,.811+.025*(math.sin(a)+1)/2+.079*t+.002*math.sin(2*a+.3)*math.sin(math.pi*t)))
 tube('band_fold_'+name,path,.0025,'red_edge','head',8)
ellipsoid('band_side_knot',(.313,.176,.890),(.031,.031,.038),'red')
# Two soft tied tails remain inside the source side-tie extent.
padded_leaf('band_tail_high',[(.295,.929),(.345,.910),(.339,.866),(.312,.874),(.288,.902)],.191,.028,'red','head')
padded_leaf('band_tail_low',[(.300,.910),(.331,.868),(.315,.805),(.292,.836),(.279,.895)],.212,.025,'red','head')

# Stable subdivision smooths source continuous sleeves and tunic; original
# weights are interpolated in rest space before the unchanged armature.
for n in ['tailored_tunic','arm_L','arm_R','leg_L','leg_R']:
 o=parts[n];m=o.modifiers.new('Rest-space soft topology','SUBSURF');m.levels=2;m.render_levels=2
 o.modifiers.move(len(o.modifiers)-1,0);bake_before_armature(o);smooth(o)

# Rounded canvas wrap, replacing the hard rectangular skirt.
delete(parts['apron_skirt']);nu=64;vs=[]
for j,(z,w,front,back) in enumerate([(.083,.196,.170,.120),(.092,.205,.177,.127),(.192,.190,.164,.120),(.205,.185,.162,.116)]):
 for i in range(nu):
  a=math.tau*i/nu;sy=signed(math.sin(a),.43)
  y=(-front if sy<0 else back)*abs(sy)
  vs.append((w*signed(math.cos(a),.43),y,z))
fs=[tuple(reversed(range(nu))),tuple(range(3*nu,4*nu))]+[(j*nu+i,j*nu+(i+1)%nu,(j+1)*nu+(i+1)%nu,(j+1)*nu+i) for j in range(3) for i in range(nu)]
skirt=addmesh('rounded_apron_wrap',vs,fs,'blue','pelvis');bevel(skirt,.0035,3)
# Hem is part of the physical garment, sampled at its low front/side contour.
path=[]
for i in range(nu+1):
 a=math.tau*i/nu;sy=signed(math.sin(a),.43)
 path.append((.201*signed(math.cos(a),.43),(-.174 if sy<0 else .125)*abs(sy),.094))
tube('apron_hem_piping',path,.0025,'blue_edge','pelvis')
delete(parts['apron_pocket'])
pocket_outline=[(-.108,.174),(.108,.174),(.108,.126),(.093,.108),(-.093,.108),(-.108,.126)]
padded_leaf('generous_apron_pocket',pocket_outline,-.188,.018,'blue','pelvis')
tube('pocket_sewn_edge',[(x,-.190,z) for x,z in [(-.100,.168),(-.100,.128),(-.088,.116),(.088,.116),(.100,.128),(.100,.168)]],.0018,'blue_edge','pelvis')
for sign in [-1,1]:
 # Strap ribbon wraps over each shoulder; no new contact-bearing transform.
 path=[(sign*.113,-.171,.276),(sign*.117,-.168,.335),(sign*.130,-.124,.380),(sign*.130,-.040,.389),(sign*.129,.100,.385),(sign*.121,.147,.338),(sign*.107,.146,.213)]
 vs=[];weights=[]
 for j,(x,y,z) in enumerate(path):
  tangent=(Vector(path[min(j+1,len(path)-1)])-Vector(path[max(0,j-1)])).normalized()
  normal=Vector((0,-tangent.z,tangent.y)).normalized()
  for dx,dn in [(-.013,-.004),(.013,-.004),(.013,.004),(-.013,.004)]:
   vs.append(tuple(Vector((x+dx,y,z))+normal*dn));t=max(0,min(1,(z-.16)/.18));weights.append({'pelvis':1-t,'spine':t})
 fs=[(3,2,1,0),tuple(range((len(path)-1)*4,len(path)*4))]+[(j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k) for j in range(len(path)-1) for k in range(4)]
 strap=addmesh('apron_shoulder_strap_'+str(sign),vs,fs,'blue',weights=weights);bevel(strap,.003,3)
 ellipsoid('apron_strap_button_'+str(sign),(sign*.113,-.179,.327),(.010,.005,.010),'white','spine',24,16)

# Deliberate neckerchief leaves and curved smile replace flat source ends.
for n in ['kerchief_tail_-1','kerchief_tail_1']:delete(parts[n])
for sign in [-1,1]:
 outline=[(sign*.008,.333),(sign*.037,.313),(sign*.062,.258),(sign*.027,.273),(sign*.011,.300)]
 if sign<0:outline.reverse()
 padded_leaf('soft_neckerchief_tail_'+str(sign),outline,-.169,.026,'red','spine')
delete(parts['smile'])
path=[]
for i in range(25):
 x=-.039+.078*i/24;z=.543-.018*(1-(x/.039)**2)
 path.append((x,-.253,z))
tube('friendly_curved_smile',path,.0045,'eye','head',10)

# Rounded eye/cheek surfaces keep their source feature centers and extents.
for sign in [-1,1]:
 for stem,loc,scale,material in [('eye',(sign*.103,-.243,.6892),(.023,.012,.034),'eye'),('eye_glint',(sign*.103-.004,-.254,.6982),(.006,.004,.009),'white'),('cheek',(sign*.182,-.242,.5908),(.037,.009,.020),'blush')]:
  delete(parts[stem+'_'+str(sign)]);ellipsoid(stem+'_'+str(sign),loc,scale,material,'head',32,20)

# Every added edge/thickness operation is now real topology. Only native
# armature modifiers remain; material and mesh topology is constant over time.
for o in collection.all_objects:
 if o.type=='MESH' and '__refined_' in o.name:
  bm=bmesh.new();bm.from_mesh(o.data)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(o.data);bm.free();o.data.update()
arm.data.pose_position='POSE'
asset=dict(assetrec,root=root,collection=collection)
native.apply_clip(asset,rig,'idle',1,'S',scene)

# Restore the recorded camera, with honest captureScale2 pixel calibration.
record=json.loads((OBJECT/'inputs/source-camera.json').read_text())
cam=bpy.data.objects.new('Mateo registered 35 degree camera',bpy.data.cameras.new('Mateo registered orthographic'))
scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
cam.matrix_world=Matrix(record['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0
scene.render.resolution_x=384;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1
bpy.context.view_layer.update()
def pixel(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [v.x*384,(1-v.y)*640]
base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update()
dy=pixel((0,0,0))[1]-base[1];cam.data.shift_y=(496-base[1])/dy
bpy.context.view_layer.update()
p=pixel((0,0,0));assert abs(p[0]-192)<.01 and abs(p[1]-496)<.01,p
record['captureScale']=2;record['calibration']={'root':p,'unitX':[a-b for a,b in zip(pixel((1,0,0)),p)],'unitDepth':[a-b for a,b in zip(pixel((0,-1,0)),p)],'unitHeight':[a-b for a,b in zip(pixel((0,0,1)),p)]}
record['camera']['projectionMatrix']=[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)]

# Broad fourfold symmetric light and neutral-warm environment, no ground plane.
scene.world=bpy.data.worlds.new('Mateo soft symmetric environment');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.72,.76,.82,1);bg.inputs['Strength'].default_value=.24
lights=[]
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=(1,.93,.84)
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.65))-o.location).to_track_quat('-Z','Y').to_euler();lights.append({'name':name,'position':list(loc),'power':power,'size':size,'color':list(d.color)})
area('Mateo overhead softbox',(0,0,4.5),150,4)
for i in range(4):
 a=i*math.pi/2;area('Mateo symmetric fill '+str(i),(3*math.cos(a),3*math.sin(a),2.1),75,4)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.03
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.cycles.transparent_max_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 scene.cycles.device='GPU'
 devices=[{'name':d.name,'type':d.type,'use':d.use} for d in prefs.devices]
except Exception as e:scene.cycles.device='CPU';devices=[{'fallback':str(e)}]
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=15;scene.render.dither_intensity=0
scene.render.fps=12;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.use_compositing=False;scene.render.use_persistent_data=True
record['artStyle']={'revision':'Mateo native warm soft round01','lightingRig':lights,'worldStrength':.24,'worldColor':[.72,.76,.82],'horizontalSymmetry':4,'noGroundPlane':True,'colorManagement':{'view':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':0},'engine':'CYCLES','samples':32,'denoise':True,'device':scene.cycles.device,'devices':devices}
(OUT/'camera.json').write_text(json.dumps(record,indent=2)+'\n')
(OUT/'assetRecord.json').write_text(json.dumps(assetrec,indent=2)+'\n')
(OUT/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
# Include the original action cohorts explicitly; nonactive cohorts remain editable.
action_ids={bpy.data.actions[t['action']] for c in rig['clips'].values() for t in c['actions']}
for o in collection.all_objects:
 if o.type=='MESH':
  for m in o.modifiers:assert m.type=='ARMATURE',(o.name,m.type)
project=HERE/'round01.blend'
bpy.data.libraries.write(str(project),{scene}|action_ids,fake_user=True,compress=True)
print('MATEO_PROJECT',str(project))
# First native views for internal defect inspection before the complete capture.
for direction in ['S','E','N','W']:
 native.apply_clip(asset,rig,'idle',1,direction,scene)
 scene.render.filepath=str(OUT/('hero-'+direction+'.png'));bpy.ops.render.render(write_still=True)
print('MATEO_HEROES_DONE')
