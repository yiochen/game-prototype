"""Native Ama rest-mesh refinement. Run on the untouched catalog backup."""
import bpy, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).parent; BASE=P.parent; OUT=BASE/'candidates/round-01'
sys.path.insert(0,str(P))
import native_actions_round01 as native
from audit_common_round01 import contacts, food_signature
rig=json.loads((P/'rig-round01.json').read_text())
coll=bpy.data.collections['S33_CHARACTER_chef_ama.002']
root=bpy.data.objects['chef_ama__ground_root.002']; arm=bpy.data.objects['chef_ama__armature.001']
sc=bpy.data.scenes.new('Ama warm soft round01'); bpy.context.window.scene=sc
sc.collection.children.link(coll); coll.hide_render=False; coll.hide_viewport=False
asset={'collection':coll,'root':root,'armature':arm}; bpy.context.view_layer.update()
(P/'source-food-round01.json').write_text(json.dumps(food_signature(coll),indent=2))
def apply(c,f=1,d='S'): return native.apply_clip(asset,rig,c,f,d,sc)
reference=[]
for c in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   apply(c,f,d); reference.append({'clip':c,'direction':d,'index':f-1,**contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get())})
(P/'source-contacts-round01.json').write_text(json.dumps(reference,separators=(',',':')))
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones}
(P/'source-rest-round01.json').write_text(json.dumps(rest,indent=2))
action_hashes={a.name:hashlib.sha256(json.dumps([(c.data_path,c.array_index,[(list(k.co),k.interpolation) for k in c.keyframe_points]) for c in native._fcurves(a)],sort_keys=True).encode()).hexdigest() for a in bpy.data.actions if a.name in {t['action'] for c in rig['clips'].values() for t in c['actions']}}
apply('idle'); arm.data.pose_position='REST'; bpy.context.view_layer.update()

def mat(name,h,rough=.7,spec=.23):
 rgb=[]
 for i in (0,2,4):
  v=int(h[i:i+2],16)/255; rgb.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
 m=bpy.data.materials.new('Ama01 '+name); m.use_nodes=True; m.diffuse_color=(*rgb,1)
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*rgb,1)
 bs.inputs['Roughness'].default_value=rough; bs.inputs['Specular IOR Level'].default_value=spec
 return m
M={k:mat(k,h,r,s) for k,h,r,s in [
 ('ivory','F4E5C9',.76,.21),('ivory-band','EEDBBA',.77,.21),('skin','75432F',.68,.23),
 ('hair','3D241D',.63,.24),('hair-soft','492A20',.62,.24),('teal','167549',.76,.21),
 ('teal-light','238355',.74,.22),('teal-edge','10643D',.78,.19),('navy','302C2B',.76,.19),
 ('eye','211711',.30,.30),('blush','D78064',.79,.16),('glint','FFF4D9',.46,.20),
 ('gold','D6A448',.62,.25),('wrap','E8AC18',.82,.14),('wrap-light','F5BE33',.82,.14),('wrap-shadow','DDA018',.88,.08),('metal','B2C0C2',.37,.45),('wood','62402E',.73,.20) ]}
def key(o): return o.name.split('__',1)[1].split('.')[0]
def material_for(o):
 if '__knife_handle' in o.name:return M['wood']
 if '__knife_blade' in o.name:return M['metal']
 k=key(o)
 if any(x in k for x in ['rounded_crown','occiput','cropped','brow']): return M['hair-soft'] if k.endswith(('_1','_4')) else M['hair']
 if any(x in k for x in ['head','ear','palm','thumb','nose','neck']): return M['skin']
 if k.startswith('eye_glint'): return M['glint']
 if k.startswith('eye') or k=='smile': return M['eye']
 if k.startswith('cheek'): return M['blush']
 if k.startswith(('kerchief','apron')): return M['teal']
 if k.startswith(('minimal_foot','leg','pelvis')): return M['navy']
 if 'knife_handle' in k: return M['wood']
 if 'knife_blade' in k: return M['metal']
 return M['ivory']
for o in list(coll.all_objects):
 if o.type!='MESH' or '__image_plane' in o.name: continue
 o.data=o.data.copy(); old_indices=[p.material_index for p in o.data.polygons]
 o.data.materials.clear(); o.data.materials.append(material_for(o))
 if key(o).startswith('arm_'):
  o.data.materials.append(M['skin'])
  for p,i in zip(o.data.polygons,old_indices): p.material_index=min(i,1)
 for p in o.data.polygons: p.use_smooth=True
 for mod in list(o.modifiers):
  if mod.type=='WEIGHTED_NORMAL': o.modifiers.remove(mod)
  elif mod.type=='BEVEL':
   # Bake in undeformed rest coordinates. No angle-threshold topology during motion.
   mod.segments=12 if key(o)=='head' else (mod.segments if key(o).startswith('minimal_foot') else 6)
   bpy.context.view_layer.objects.active=o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
   bpy.ops.object.modifier_apply(modifier=mod.name); o.select_set(False)

def skin_obj(o,name,material,bone='head',weights=None):
 o.name='chef_ama__R01_'+name
 for c in list(o.users_collection): c.objects.unlink(o)
 coll.objects.link(o); o.parent=root; o.matrix_parent_inverse=Matrix.Identity(4)
 bpy.context.view_layer.objects.active=o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True); o.select_set(False)
 if material: o.data.materials.append(material)
 if weights:
  for i,ws in enumerate(weights):
   for g,w in ws.items():
    vg=o.vertex_groups.get(g) or o.vertex_groups.new(name=g); vg.add([i],w,'REPLACE')
 else:
  vg=o.vertex_groups.new(name=bone); vg.add(range(len(o.data.vertices)),1,'REPLACE')
 for p in o.data.polygons: p.use_smooth=True
 mod=o.modifiers.new('Preserved native C125 rig','ARMATURE'); mod.object=arm
 o['native_refinement_round']=1
 return o
def mesh(name,vs,fs,material,bone='head',weights=None):
 me=bpy.data.meshes.new('Ama01 '+name); me.from_pydata(vs,[],fs); me.update()
 o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); return skin_obj(o,name,material,bone,weights)
def sphere(name,loc,size,material,bone='head',tilt=0,shape=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,radius=1,location=loc); o=bpy.context.object
 if shape:
  for v in o.data.vertices: v.co=shape(v.co)
 o.scale=size; o.rotation_euler.y=tilt; return skin_obj(o,name,material,bone)
def delete(pred):
 for o in list(coll.all_objects):
  if pred(key(o)): bpy.data.objects.remove(o,do_unlink=True)
def bake_bevel(o,w,seg=5):
 bpy.context.view_layer.objects.active=o; bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
 m=o.modifiers.new('Baked tailored edge','BEVEL'); m.width=w; m.segments=seg
 while list(o.modifiers).index(m)>0: bpy.ops.object.modifier_move_up(modifier=m.name)
 bpy.ops.object.modifier_apply(modifier=m.name); o.select_set(False)
def box(name,loc,size,material,bone,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 m=o.modifiers.new('Baked soft edge','BEVEL'); m.width=bevel; m.segments=6; bpy.ops.object.modifier_apply(modifier=m.name)
 return skin_obj(o,name,material,bone)

# Continuous golden headwrap: softly folded cloth crown, wraparound bands and side knot.
# Broad native fabric ridges are geometry, not a front image or thin facade.
delete(lambda k:k.startswith('turban'))
N=128; vs=[]; fs=[]
# Rounded cross-sections narrow to an offset folded crown peak, exact original z1.22 maximum.
rings=[(.944,.91),(.970,.995),(1.015,1.0),(1.070,.98),(1.117,.89),(1.160,.72),(1.194,.48),(1.214,.24),(1.220,.025)]
for j,(z,fac) in enumerate(rings):
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t);n=3.15
  # Gentle diagonal cloth compression: two broad crease valleys continue over side/rear.
  crease=1-.065*math.exp(-((math.sin(t-.55)-.12*(z-1.05)/.15)/.24)**2)*(math.sin(math.pi*j/(len(rings)-1))**2)
  x=.302*math.copysign(abs(c)**(2/n),c)*fac*crease+.033*((z-.944)/.276)
  y=.014+.239*math.copysign(abs(s)**(2/n),s)*fac*crease
  zz=z+(.025*math.sin(3*t+.5)-.014*math.cos(2*t-1))*math.sin(math.pi*j/(len(rings)-1))
  vs.append((x,y,min(1.22,zz)))
for j in range(len(rings)-1):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.extend([tuple(reversed(range(N))),tuple(range((len(rings)-1)*N,len(rings)*N))])
crown=mesh('folded_golden_cloth_crown',vs,fs,M['wrap'])
bpy.context.view_layer.objects.active=crown;bpy.ops.object.select_all(action='DESELECT');crown.select_set(True)
sub=crown.modifiers.new('Relaxed folded cloth curvature','SUBSURF');sub.levels=2;sub.render_levels=2;bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name);crown.select_set(False)

# Continuous fabric bands have a rolled cross section and slight diagonal overlap at the side knot.
for band,(base,height,mt) in enumerate([(.920,.047,M['wrap-light']),(.962,.048,M['wrap']), (1.004,.047,M['wrap-light'])]):
 vs=[];fs=[]
 profile=[(-.5,.970),(-.40,1.008),(-.18,1.023),(.20,1.023),(.42,1.008),(.50,.974)]
 for h,fac in profile:
  for i in range(N):
   t=math.tau*i/N;c=math.cos(t);s=math.sin(t);n=3.45
   tilt=.015*c+.004*math.sin(2*t+band*.4)
   vs.append((.290*math.copysign(abs(c)**(2/n),c)*fac,.012+.248*math.copysign(abs(s)**(2/n),s)*fac,base+h*height+tilt))
 for j in range(len(profile)-1):
  for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 fs.extend([tuple(reversed(range(N))),tuple(range((len(profile)-1)*N,len(profile)*N))]);mesh('rolled_wrap_band_'+str(band),vs,fs,mt)
# Knotted cloth at Ama's right temple, under the original x/y/z functional envelope.
sphere('headwrap_side_knot',(.253,-.100,1.096),(.081,.105,.101),M['wrap-light'],tilt=-.32,shape=lambda q:Vector((q.x*(.91+.09*q.z),q.y*(.92+.08*q.x),q.z)))
# A curved folded panel crosses the crown above the band. It follows the body of the wrap.
# Cloth volume as a closed tapered lens, with the central line rising diagonally.
vs=[];fs=[];nx=36;ny=12
for side in [0,1]:
 for i in range(nx+1):
  u=i/nx;x=-.265+.495*u;zmid=1.060+.077*u
  for j in range(ny+1):
   v=j/ny;z=zmid+(v-.5)*(.075*math.sin(math.pi*u)**.6+.002)
   hit,co,no,ind=crown.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   xx=x
   for attempt in range(12):
    if hit:break
    xx*=.96;hit,co,no,ind=crown.ray_cast(Vector((xx,-1,z)),Vector((0,1,0)))
   assert hit,(x,z)
   x=xx;y=co.y-.004-.016*math.sin(math.pi*v)*math.sin(math.pi*u)
   if side:y+=.032
   vs.append((x,y,z))
layer=(nx+1)*(ny+1)
for side in [0,1]:
 for i in range(nx):
  for j in range(ny):
   k=side*layer+i*(ny+1)+j;quad=(k,k+ny+1,k+ny+2,k+1);fs.append(quad if side==0 else tuple(reversed(quad)))
for i in range(nx):
 for j in [0,ny]:
  a=i*(ny+1)+j;b=(i+1)*(ny+1)+j;fs.append((a,b,b+layer,a+layer))
for i in [0,nx]:
 for j in range(ny):
  a=i*(ny+1)+j;b=a+1;fs.append((a,b,b+layer,a+layer))
panel=mesh('broad_diagonal_fold',vs,fs,M['wrap'])
# Native union blends the draped panel into the crown, removing thin exposed panel ends.
for o in [crown,panel]:o.modifiers.clear();o.vertex_groups.clear()
bpy.ops.object.select_all(action='DESELECT');crown.select_set(True);panel.select_set(True);bpy.context.view_layer.objects.active=crown;bpy.ops.object.join()
rem=crown.modifiers.new('Welded cloth fold','REMESH');rem.mode='VOXEL';rem.voxel_size=.0035;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
sm=crown.modifiers.new('Soft fold transitions','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
top=max(v.co.z for v in crown.data.vertices)
for v in crown.data.vertices:v.co.z=.944+(v.co.z-.944)*(1.22-.944)/(top-.944)
vg=crown.vertex_groups.new(name='head');vg.add(range(len(crown.data.vertices)),1,'REPLACE');mod=crown.modifiers.new('Preserved native C125 rig','ARMATURE');mod.object=arm
crown.name='chef_ama__R01_continuous_folded_golden_crown'


# Rounded native hair and moustache retain the same cropped blue-black identity/envelope.
hair=[]
for o in list(coll.all_objects):
 if o.type=='MESH' and any(s in key(o) for s in ['rounded_crown','rounded_occiput','cropped']):
  vs0=[v.co.copy() for v in o.data.vertices]; lo=Vector([min(v[i] for v in vs0) for i in range(3)]); hi=Vector([max(v[i] for v in vs0) for i in range(3)])
  hair.append((key(o),(lo+hi)/2,(hi-lo)/2,material_for(o)))
delete(lambda k:any(s in k for s in ['rounded_crown','rounded_occiput','cropped']))
for k,cen,rad,mt in hair:
 tilt=0
 if k.startswith('cropped_fringe'):
  i=int(k.rsplit('_',1)[1]); tilt=-.16+.08*i; rad.z*=1.07
 if k.startswith('mustache'): rad.z*=1.13; rad.y*=1.1; mt=M['hair']
 sphere(k,cen,rad,mt,tilt=tilt)

# Native garments with thickness; stable rest topology before bending.
tunic=next(o for o in coll.all_objects if key(o)=='tailored_tunic'); bake_bevel(tunic,.017)
skirt=next(o for o in coll.all_objects if key(o)=='apron_skirt'); bake_bevel(skirt,.014)
delete(lambda k:k in ['apron_bib','apron_pocket'])
box('apron_bib',(0,-.177,.276),(.271,.029,.151),M['teal'],'spine',.012)
box('apron_bib_top_welt',(0,-.196,.344),(.252,.007,.012),M['teal-light'],'spine',.0045)
box('apron_large_pocket',(0,-.193,.150),(.191,.026,.065),M['teal-light'],'pelvis',.014)
box('apron_pocket_opening',(0,-.208,.177),(.170,.006,.008),M['teal-edge'],'pelvis',.003)
box('apron_front_hem',(0,-.180,.091),(.374,.013,.013),M['teal-edge'],'pelvis',.006)
for sign in [-1,1]:
 # Rounded cloth lapels face the same -Y front as the native source.
 delete(lambda k:k=='collar_'+str(sign))
 pts=[(sign*.008,-.148,.411),(sign*.113,-.146,.394),(sign*.085,-.187,.359),(sign*.023,-.187,.373)]
 v=pts+[(x,y+.015,z) for x,y,z in pts]; f=[(0,1,2,3),(7,6,5,4)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 o=mesh('folded_collar_'+str(sign),v,f,M['ivory'],'spine'); bake_bevel(o,.007,4)
 delete(lambda k:k=='kerchief_tail_'+str(sign))
 v=[(sign*.010,-.215,.328),(sign*.049,-.214,.320),(sign*.078,-.216,.257),(sign*.046,-.220,.239),(sign*.024,-.217,.265)]
 v+= [(x,y+.020,z) for x,y,z in v]; f=[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
 o=mesh('pointed_necktie_tail_'+str(sign),v,f,M['teal'],'spine'); bake_bevel(o,.005,4)
 box('apron_shoulder_strap_'+str(sign),(sign*.146,-.174,.354),(.022,.017,.091),M['teal-light'],'spine',.008)
knot=next(o for o in coll.all_objects if key(o)=='kerchief_knot')
for v in knot.data.vertices: v.co.y-=.040
delete(lambda k:k.startswith('coat_button_'))
# Put the two useful chest buttons above the bib, not hidden inside it.
for sign in [-1,1]: sphere('ivory_coat_button_'+str(sign),(sign*.112,-.175,.367),(.010,.007,.011),M['gold'],'spine')

for side,sgn in [('L',-1),('R',1)]:
 old=next(o for o in coll.all_objects if key(o)=='arm_'+side)
 a=Vector((sgn*.198,.004,.352)); j=Vector((sgn*.249,-.002,.247)); end=Vector((sgn*.267,-.023,.211))
 names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
 rings=[(a,.065,{names[0]:.85,'spine':.15}),((a+j)*.5,.061,{names[0]:1}),(j,.057,{names[0]:.5,names[1]:.5}),((j+end)*.5,.052,{names[1]:1}),(end,.048,{names[1]:.35,names[2]:.65})]
 vs=[]; ws=[]; seg=32
 for idx,(p,r,w) in enumerate(rings):
  d=(rings[min(idx+1,4)][0]-rings[max(0,idx-1)][0]).normalized(); u=d.cross(Vector((0,1,0))).normalized(); v=d.cross(u).normalized()
  for k in range(seg): t=math.tau*k/seg; vs.append(p+u*math.cos(t)*r+v*math.sin(t)*r*.88); ws.append(w)
 fs=[tuple(reversed(range(seg))),tuple(range(4*seg,5*seg))]+[(j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i) for j2 in range(4) for i in range(seg)]
 o=mesh('rounded_arm_'+side,vs,fs,M['ivory'],weights=ws); o.data.materials.append(M['skin'])
 for p in o.data.polygons: p.material_index=1 if p.index==1 or p.index>=2+2*seg else 0
 bpy.data.objects.remove(old,do_unlink=True)
 d=(end-a).normalized(); u=d.cross(Vector((0,1,0))).normalized(); v=d.cross(u).normalized(); vs=[]; fs=[]
 for h,r in [(-.017,.057),(-.012,.063),(.008,.063),(.015,.055)]:
  for k in range(seg): t=math.tau*k/seg; vs.append(j+d*h+u*math.cos(t)*r+v*math.sin(t)*r*.88)
 for j2 in range(3):
  for i in range(seg): fs.append((j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i))
 mesh('rolled_cuff_'+side,vs,fs,M['ivory-band'],weights=[{names[0]:.5,names[1]:.5}]*len(vs))
# A tiny native curved smile is embedded in the evaluated rounded face surface.
delete(lambda k:k=='smile')
curve=bpy.data.curves.new('Ama01 smile','CURVE');curve.dimensions='3D';curve.resolution_u=24;curve.bevel_depth=.0045;curve.bevel_resolution=4;curve.use_fill_caps=True
sp=curve.splines.new('BEZIER');sp.bezier_points.add(4)
for pt,(x,z) in zip(sp.bezier_points,[(-.040,.551),(-.022,.537),(0,.533),(.022,.537),(.040,.551)]):
 y=-.235+(.125-math.sqrt(.125**2-max(0,.555-z)**2))+.0015
 pt.co=(x,y,z);pt.handle_left_type='AUTO';pt.handle_right_type='AUTO'
o=bpy.data.objects.new('smile',curve);sc.collection.objects.link(o);bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);skin_obj(o,'embedded_friendly_smile',M['eye'])
# Small back bow and neckband give side/back garment continuation.
box('back_necktie_band',(0,.137,.357),(.196,.023,.025),M['teal'],'spine',.010)
delete(lambda k:k.startswith('apron_back_tie'))
sphere('apron_back_knot',(0,.151,.194),(.027,.022,.024),M['teal-light'],'pelvis')
for sign in [-1,1]:
 sphere('apron_back_loop_'+str(sign),(sign*.046,.148,.194),(.045,.020,.023),M['teal'],'pelvis',tilt=sign*.22)
 o=box('apron_back_tail_'+str(sign),(sign*.022,.146,.156),(.024,.014,.060),M['teal-edge'],'pelvis',.008)

# Consistent outward native normals after all rest mesh construction.
import bmesh
for o in coll.all_objects:
 if o.type=='MESH' and '__image_plane' not in o.name:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
# Source-registered camera. Shift comes from source projection/root; no subject fitting.
cam=bpy.data.objects.new('Ama01 registered35 camera',bpy.data.cameras.new('Ama01 registered35 camera')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.sensor_fit='HORIZONTAL'; cam.data.ortho_scale=1.5
camera_record=json.loads((BASE/'inputs/source-camera.json').read_text())['camera']; cam.matrix_world=Matrix(camera_record['worldMatrix'])
sc.render.resolution_x=384; sc.render.resolution_y=640; sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v)); return [p.x*384,(1-p.y)*640]
cam.data.shift_y=0; bpy.context.view_layer.update(); base=px((0,0,0))[1]
cam.data.shift_y=1; bpy.context.view_layer.update(); dy=px((0,0,0))[1]-base
cam.data.shift_y=(496-base)/dy; bpy.context.view_layer.update()
sc.render.engine='CYCLES'; sc.cycles.samples=72; sc.cycles.use_denoising=True; sc.cycles.use_adaptive_sampling=True; sc.cycles.adaptive_threshold=.02
sc.cycles.max_bounces=6; sc.cycles.transparent_max_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.refresh_devices()
 for device in prefs.devices: device.use=device.type=='METAL'
 sc.cycles.device='GPU'
except Exception as e: print('METAL fallback',e); sc.cycles.device='CPU'
sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'; sc.render.image_settings.color_depth='8'
sc.render.image_settings.compression=30; sc.render.fps=12; sc.render.dither_intensity=0
sc.render.filter_size=1; sc.cycles.pixel_filter_type='BOX'; sc.render.use_compositing=False; sc.render.use_sequencer=False
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.view_settings.exposure=0.0
world=bpy.data.worlds.new('Ama01 warm ambient'); world.use_nodes=True; sc.world=world
bg=world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(.82,.77,.67,1); bg.inputs['Strength'].default_value=.42
for i,(pos,energy,size) in enumerate([((0,0,4.5),135,3.5),((3,0,2),25,4),((-3,0,2),25,4),((0,3,2),25,4),((0,-3,2),25,4)]):
 ld=bpy.data.lights.new('Ama01 symmetric area '+str(i),'AREA'); lo=bpy.data.objects.new(ld.name,ld); sc.collection.objects.link(lo)
 lo.location=pos; lo.rotation_euler=(Vector((0,0,.8))-lo.location).to_track_quat('-Z','Y').to_euler(); ld.energy=energy; ld.shape='DISK'; ld.size=size; ld.color=(1,.96,.88)
arm.data.pose_position='POSE'; apply('idle'); sc.frame_start=1; sc.frame_end=12
root['refinement_round']=1; root['refinement_style']='Warm soft cartoon, folded golden headwrap, shaped ivory collar, rolled cuffs and dimensional green apron'
for o in coll.all_objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for node in m.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      im=node.image; assert im.packed_file, 'Original dish must remain packed'
      dep=P/'dependencies-round01/dish-salmon.png'; dep.parent.mkdir(exist_ok=True); dep.write_bytes(im.packed_file.data); im.filepath='//dependencies-round01/dish-salmon.png'
ids={sc}
for c in rig['clips'].values():
 for t in c['actions']: ids.add(bpy.data.actions[t['action']])
bpy.data.libraries.write(str(P/'round-01.blend'),ids,fake_user=True,compress=True)
recipe={'asset':'chef-ama','round':1,'originalProject':str(BASE/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend'),'originalSHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','scene':sc.name,'collection':coll.name,'root':root.name,'armature':arm.name,
 'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'pixelAspect':[1,1],'root':px((0,0,0)),'unitX':[a-b for a,b in zip(px((1,0,0)),px((0,0,0)))],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),px((0,0,0)))],'unitHeight':[a-b for a,b in zip(px((0,0,1)),px((0,0,0)))]},
 'renderer':{'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'adaptiveThreshold':sc.cycles.adaptive_threshold,'filter':'BOX1','viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'symmetricLightPositions':[[0,0,4.5],[3,0,2],[-3,0,2],[0,3,2],[0,-3,2]],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'position':list(o.location),'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'ambientWorld':{'color':list(bg.inputs['Color'].default_value),'strength':bg.inputs['Strength'].default_value},'noGroundPlane':True},
 'rest':rest,'originalActionSHA256':action_hashes,'materials':{k:{'diffuseLinear':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for k,m in M.items()},
 'changes':['Native folded golden crown and continuous rolled bands at exact original1.22local top','Rounded short dark-brown fringe and back hair volumes retaining source envelope','Rounded native coat/skin edges baked before original armature','Layered ivory collar, pointed green necktie, straps, dimensional pocket/hem and back bow','Round weighted arm rings/rolled cuffs retain all source bone/action contacts','Exact original food plane/UV/image/actions/drivers remain separate identified2D'],
 'notes':['All geometry created and bevels/remesh baked in armature REST position','Source world root, bone matrices/rest, native action cohorts and timing unchanged','One common horizontally symmetric lighting/material setting for all facings']}
(P/'recipe-round01.json').write_text(json.dumps(recipe,indent=2))
for d in ['N','E','S','W']:
 apply('idle',1,d); sc.render.filepath=str(OUT/('test-idle-'+d+'.png')); bpy.ops.render.render(write_still=True)
print('BUILT',P/'round-01.blend',flush=True)
