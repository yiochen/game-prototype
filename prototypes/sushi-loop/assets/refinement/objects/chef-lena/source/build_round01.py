import bpy,json,math,sys,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(P));import native_actions_round01 as native
rig=json.loads((P/'rig-round01.json').read_text())
coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002']
sc=bpy.data.scenes.new('Lena warm soft round01');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
asset={'collection':coll,'root':root,'armature':arm};bpy.context.view_layer.update()
def apply(clip,frame=1,d='S'):native.apply_clip(asset,rig,clip,frame,d,sc)
def sample():
 dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg)
 bones={b.name:{'head':list(ae.matrix_world@b.head),'tail':list(ae.matrix_world@b.tail),'matrix':[list(r) for r in ae.matrix_world@b.matrix]} for b in ae.pose.bones}
 props={o.name:{'matrix':[list(r) for r in o.evaluated_get(dg).matrix_world],'hide':o.hide_render} for o in coll.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name}
 return {'bones':bones,'props':props,'rootMatrix':[list(r) for r in root.matrix_world],'rotation':root.rotation_euler.z}
# Actual evaluated pose reference, all states/facings. No custom-property substitution.
source=[]
for c in rig['clips']:
 for d in ['S','E','N','W']:
  for f in range(1,13):apply(c,f,d);source.append({'clip':c,'direction':d,'index':f-1,**sample()})
(P/'source-motion-round01.json').write_text(json.dumps(source,separators=(',',':')))
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones}
(P/'source-rest-round01.json').write_text(json.dumps(rest,indent=2))
apply('idle');arm.data.pose_position='REST';bpy.context.view_layer.update()
# Independent copies of material response; do not mutate global source datablocks.
def mat(name,h,rough=.68,spec=.25):
 rgb=tuple((int(h[i:i+2],16)/255/12.92 if int(h[i:i+2],16)/255<=.04045 else ((int(h[i:i+2],16)/255+.055)/1.055)**2.4) for i in (0,2,4));m=bpy.data.materials.new('Lena01 '+name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec
 return m
M={k:mat(k,h,r,s) for k,h,r,s in [('ivory','F5E6CB',.76,.2),('ivory-edge','EBD8B8',.8,.18),('skin','85503C',.66,.23),('hair','4D2B24',.55,.28),('hair-light','593126',.57,.26),('blue','246FC0',.72,.22),('blue-light','2A79CA',.7,.22),('blue-shadow','1E5C9E',.8,.17),('red','CA3E32',.7,.25),('navy','283A55',.78,.17),('eye','231715',.35,.28),('blush','BE6B5A',.8,.15),('glint','FFF5DC',.52,.2),('gold','D8AB59',.55,.3),('metal','ADBDC1',.35,.5),('wood','63402D',.7,.2)]}
def key(o):return o.name.split('__',1)[1].split('.')[0]
def material_for(o):
 k=key(o)
 if any(s in k for s in ['rounded_crown','occiput','curl','side_crown','brow']):return M['hair-light'] if k.endswith(('_1','_4')) else M['hair']
 if any(s in k for s in ['head','ear','palm','thumb','nose','neck']):return M['skin']
 if k.startswith('eye_glint'):return M['glint']
 if k.startswith('eye') or k=='smile':return M['eye']
 if k.startswith('cheek'):return M['blush']
 if k.startswith('kerchief'):return M['red']
 if k.startswith('apron'):return M['blue']
 if k.startswith(('minimal_foot','leg','pelvis')):return M['navy']
 if 'knife_handle' in k:return M['wood']
 if 'knife_blade' in k:return M['metal']
 return M['ivory']
for o in list(coll.all_objects):
 if o.type!='MESH' or '__image_plane' in o.name:continue
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(material_for(o))
 if key(o).startswith('arm_'):
  o.data.materials.append(M['skin'])
  for p in o.data.polygons:p.material_index=1 if p.index==1 or p.index>=18 else 0
 for p in o.data.polygons:p.use_smooth=True
 # Apply bevels at REST before animation, invariant topology; do not smooth broad face using weighted normals.
 for mod in list(o.modifiers):
  if mod.type=='WEIGHTED_NORMAL':o.modifiers.remove(mod)
  elif mod.type=='BEVEL':
   mod.segments=6 if not key(o).startswith('head') else 12
   bpy.context.view_layer.objects.active=o;o.select_set(True)
   bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
# Native mesh factory, common ground-root coordinates and rigid/balanced skin weights.
def skin_obj(o,name,material,bone='head',weights=None):
 o.name='chef_lena__R01_'+name
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
 if material:o.data.materials.append(material)
 if weights:
  for i,ws in enumerate(weights):
   for g,w in ws.items():
    vg=o.vertex_groups.get(g) or o.vertex_groups.new(name=g);vg.add([i],w,'REPLACE')
 else:
  vg=o.vertex_groups.new(name=bone);vg.add(range(len(o.data.vertices)),1,'REPLACE')
 for p in o.data.polygons:p.use_smooth=True
 mod=o.modifiers.new('Preserved native rig','ARMATURE');mod.object=arm
 o['native_refinement_round']=1
 return o
def mesh(name,vs,fs,material,bone='head',weights=None):
 me=bpy.data.meshes.new('Lena01 '+name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);return skin_obj(o,name,material,bone,weights)
def sphere(name,loc,scale,material,bone='head',tilt=0,shape=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=loc);o=bpy.context.object
 if shape:
  for v in o.data.vertices:v.co=shape(v.co)
 o.scale=scale;o.rotation_euler.y=tilt;return skin_obj(o,name,material,bone)
def delete_where(pred):
 for o in list(coll.all_objects):
  if pred(key(o)):bpy.data.objects.remove(o,do_unlink=True)
def roundedbox(name,loc,size,material,bone,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=o.modifiers.new('Baked fabric edge','BEVEL');mod.width=bevel;mod.segments=5;bpy.ops.object.modifier_apply(modifier=mod.name)
 return skin_obj(o,name,material,bone)
# Continuous fluted crown, top at original height1.28 local. Every azimuth has finished form.
delete_where(lambda k:k=='hat_band' or k.startswith('toque_fold'))
N=96
# Five plush native fabric lobes, welded into one continuous crown.
crown_parts=[]
for i,(loc,scale) in enumerate([((-.135,-.064,1.116),(.143,.164,.155)),((.030,-.075,1.127),(.144,.166,.153)),((.165,-.026,1.106),(.123,.154,.147)),((-.122,.112,1.112),(.148,.147,.158)),((.113,.124,1.117),(.149,.142,.158))]):
 o=sphere('crown_lobe_'+str(i),loc,scale,M['ivory']);o.modifiers.clear();o.vertex_groups.clear();crown_parts.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in crown_parts:o.select_set(True)
bpy.context.view_layer.objects.active=crown_parts[0];bpy.ops.object.join();o=crown_parts[0]
rem=o.modifiers.new('Welded soft lobe construction','REMESH');rem.mode='VOXEL';rem.voxel_size=.0045;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
smooth=o.modifiers.new('Relaxed fabric curvature','SMOOTH');smooth.factor=.6;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
o.name='chef_lena__R01_continuous_puffed_toque';o.data.materials.clear();o.data.materials.append(M['ivory']);vg=o.vertex_groups.new(name='head');vg.add(range(len(o.data.vertices)),1,'REPLACE');mod=o.modifiers.new('Preserved native rig','ARMATURE');mod.object=arm
# Keep precisely the source registered top envelope.
zmax=max(v.co.z for v in o.data.vertices)
for v in o.data.vertices:v.co.z=.983+(v.co.z-.983)*(1.28-.983)/(zmax-.983)
# Continuous fitted band with rounded profile; not a stepped box.
vs=[];fs=[]
for z,fac in [(.932,.955),(.939,.990),(.953,1.008),(1.003,1.009),(1.024,.993),(1.032,.965)]:
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t);n=3.5
  vs.append((.278*math.copysign(abs(c)**(2/n),c)*fac,.012+.229*math.copysign(abs(s)**(2/n),s)*fac,z))
for j in range(5):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.extend([tuple(reversed(range(N))),tuple(range(5*N,6*N))]);mesh('continuous_toque_band',vs,fs,M['ivory-edge'])
# Rebuild all curl volumes as smooth native geometry, grouped back locks rather than a regular bead stack.
hair=[]
for o in list(coll.all_objects):
 if o.type=='MESH' and any(s in key(o) for s in ['rounded_crown','rounded_occiput','temple_curl','fringe_curl','side_crown']):
  coords=[v.co for v in o.data.vertices];lo=Vector([min(v[i] for v in coords) for i in range(3)]);hi=Vector([max(v[i] for v in coords) for i in range(3)]);hair.append((key(o),(lo+hi)/2,(hi-lo)/2,material_for(o)))
delete_where(lambda k:any(s in k for s in ['rounded_crown','rounded_occiput','temple_curl','fringe_curl','side_crown','back_curl']))
for k,cen,rad,mt in hair:
 tilt=0
 if k.startswith('fringe'):
  i=int(k.rsplit('_',1)[1]);rad.z*=1.13;cen.z-=.003;tilt=(-.18+.07*i)
 if k=='rounded_occiput':rad.y*=.96
 sphere(k,cen,rad,mt,tilt=tilt,shape=lambda q:Vector((q.x*(1+.08*q.z),q.y,q.z)))
for row,z in enumerate([.56,.695,.835]):
 for i,x in enumerate([-.218,-.075,.075,.218]):
  y=.252-.055*(abs(x)/.218)**1.7
  sphere('sculpted_back_lock_%s_%s'%(row,i),(x,y,z+.013*math.sin(i*1.9+row)),(.097,.083,.108),M['hair-light'] if (row+i)%4==0 else M['hair'],tilt=(-.18 if i%2 else .22),shape=lambda q:Vector((q.x*(1+.08*q.z),q.y,q.z)))
# Refine softer coat: stable bevel at rest, preserve original ring weights.
tunic=next(o for o in coll.all_objects if key(o)=='tailored_tunic')
bpy.context.view_layer.objects.active=tunic
be=tunic.modifiers.new('Baked coat rounding','BEVEL');be.width=.016;be.segments=5;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
# Refined apron pocket and trim. Keep compact source hem/scale.
delete_where(lambda k:k=='apron_pocket')
roundedbox('roomy_apron_pocket',(0,-.188,.151),(.183,.023,.066),M['blue-light'],'pelvis',.014)
roundedbox('pocket_welt',(0,-.203,.178),(.166,.007,.009),M['blue-shadow'],'pelvis',.004)
roundedbox('apron_hem_front',(0,-.178,.090),(.381,.012,.014),M['blue-shadow'],'pelvis',.006)
# Rounded skirt at rest, sharp slab corners become tailored cloth edge.
skirt=next(o for o in coll.all_objects if key(o)=='apron_skirt');bpy.context.view_layer.objects.active=skirt
be=skirt.modifiers.new('Baked skirt rounding','BEVEL');be.width=.012;be.segments=5;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
# Coat lapel facets become thin curved fabric panels with softened boundaries.
for sign in [-1,1]:
 old=next(o for o in coll.all_objects if key(o)=='collar_'+str(sign));bpy.data.objects.remove(old,do_unlink=True)
 pts=[(sign*.008,-.144,.410),(sign*.113,-.142,.393),(sign*.085,-.181,.360),(sign*.023,-.180,.372)]
 vs=pts+[(x,y+.014,z) for x,y,z in pts];fs=[(0,1,2,3),(7,6,5,4)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 o=mesh('shaped_collar_'+str(sign),vs,fs,M['ivory'],'spine');bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Baked collar hem','BEVEL');be.width=.007;be.segments=4;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
 # Soft pointed scarf tails rather than rectangular strips.
 old=next(o for o in coll.all_objects if key(o)=='kerchief_tail_'+str(sign));bpy.data.objects.remove(old,do_unlink=True)
 vs=[(sign*.010,-.212,.327),(sign*.050,-.211,.319),(sign*.081,-.214,.256),(sign*.047,-.218,.237),(sign*.023,-.215,.263)]
 vs=vs+[(x,y+.021,z) for x,y,z in vs];fs=[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
 o=mesh('scarf_tail_'+str(sign),vs,fs,M['red'],'spine');bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Baked scarf edge','BEVEL');be.width=.006;be.segments=4;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
 sphere('coat_button_'+str(sign),(sign*.140,-.167,.362),(.011,.008,.012),M['gold'],'spine')
knot=next(o for o in coll.all_objects if key(o)=='kerchief_knot')
for v in knot.data.vertices:v.co.y-=.035
# Rounded limb rings use same source centerline, weights and cutoff positions; deformation topology is fixed.
for side,sgn in [('L',-1),('R',1)]:
 old=next(o for o in coll.all_objects if key(o)=='arm_'+side)
 a=Vector((sgn*.198,.004,.352));j=Vector((sgn*.249,-.002,.247));end=Vector((sgn*.267,-.023,.211));names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
 rings=[(a,.065,{names[0]:.85,'spine':.15}),((a+j)*.5,.061,{names[0]:1}),(j,.057,{names[0]:.5,names[1]:.5}),((j+end)*.5,.052,{names[1]:1}),(end,.048,{names[1]:.35,names[2]:.65})]
 vs=[];ws=[];fs=[];seg=24
 for idx,(p,r,w) in enumerate(rings):
  d=(rings[min(idx+1,4)][0]-rings[max(0,idx-1)][0]).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized()
  for k in range(seg):t=math.tau*k/seg;vs.append(p+u*math.cos(t)*r+v*math.sin(t)*r*.88);ws.append(w)
 fs=[tuple(reversed(range(seg))),tuple(range(4*seg,5*seg))]+[(j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i) for j in range(4) for i in range(seg)]
 o=mesh('rounded_arm_'+side,vs,fs,M['ivory'],weights=ws);o.data.materials.append(M['skin'])
 for p in o.data.polygons:p.material_index=1 if p.index==1 or p.index>=2+2*seg else 0
 bpy.data.objects.remove(old,do_unlink=True)
 # Cuff follows exactly the elbow/forearm blend, preserves wrist and palm attachment.
 p=j;d=(end-a).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized();vs=[];fs=[]
 for h,r in [(-.016,.058),(-.012,.062),(.009,.062),(.014,.055)]:
  for k in range(seg):t=math.tau*k/seg;vs.append(p+d*h+u*math.cos(t)*r+v*math.sin(t)*r*.88)
 for j2 in range(3):
  for i in range(seg):fs.append((j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i))
 mesh('rolled_cuff_'+side,vs,fs,M['ivory'],weights=[{names[0]:.5,names[1]:.5}]*len(vs))
# Friendly curved native smile replaces the angular source plane.
delete_where(lambda k:k=='smile')
curve=bpy.data.curves.new('Lena01 curved smile','CURVE');curve.dimensions='3D';curve.resolution_u=16;curve.bevel_depth=.005;curve.bevel_resolution=3
sp=curve.splines.new('BEZIER');sp.bezier_points.add(4)
for pt,co in zip(sp.bezier_points,[(-.043,-.252,.549),(-.024,-.258,.534),(0,-.260,.530),(.024,-.258,.534),(.043,-.252,.549)]):pt.co=co;pt.handle_left_type='AUTO';pt.handle_right_type='AUTO'
o=bpy.data.objects.new('smile',curve);sc.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);skin_obj(o,'gentle_smile',M['eye'])
# Continuous back neck band and small tied fabric knot, following existing pelvis/spine contacts.
roundedbox('back_scarf_band',(0,.133,.359),(.195,.024,.027),M['red'],'spine',.011)
sphere('apron_back_knot',(0,.154,.193),(.028,.020,.024),M['blue-light'],'pelvis')
for sign in [-1,1]:sphere('apron_back_loop_'+str(sign),(sign*.046,.150,.193),(.045,.018,.023),M['blue'],'pelvis',tilt=sign*.25)
# Actual camera calibration; source child orientation untouched.
cam=bpy.data.objects.new('Lena01 registered35 camera',bpy.data.cameras.new('Lena01 registered35 camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
cam.matrix_world=Matrix(json.loads((BASE/'inputs/source-camera.json').read_text())['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=.4583320617675781
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
bpy.context.view_layer.update()
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*640]
# Derive shift from fixed root without fitting subject.
cam.data.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0))[1];cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base;cam.data.shift_y=(496-base)/dy;bpy.context.view_layer.update()
sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True;sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.025;sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
 sc.cycles.device='GPU'
except Exception as e:print('Metal fallback',e);sc.cycles.device='CPU'
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30;sc.render.fps=12;sc.render.dither_intensity=0
sc.render.filter_size=1.0;sc.cycles.pixel_filter_type='BOX';sc.render.use_compositing=False;sc.render.use_sequencer=False
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.35
world=bpy.data.worlds.new('Lena01 warm ambient');world.use_nodes=True;sc.world=world;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.82,.77,.67,1);bg.inputs['Strength'].default_value=.25
for i,(pos,energy,size) in enumerate([((0,0,4.5),200,3.5),((3,0,2),35,4),((-3,0,2),35,4),((0,3,2),35,4),((0,-3,2),35,4)]):
 ld=bpy.data.lights.new('Lena01 symmetric area '+str(i),'AREA');lo=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,.8))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=energy;ld.shape='DISK';ld.size=size;ld.color=(1,.96,.88)
arm.data.pose_position='POSE';apply('idle');sc.frame_start=1;sc.frame_end=12
root['refinement_round']=1;root['refinement_style']='Warm soft cartoon; rounded continuous native toque, coherent locks, shaped fabric construction'
# Pack only actual dish dependency and export it as identified2D, preserving source bytes.
for o in coll.all_objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for node in m.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      im=node.image
      if im.packed_file:
       dep=P/'dependencies/dish-salmon.png';dep.parent.mkdir(exist_ok=True);dep.write_bytes(im.packed_file.data);im.filepath='//dependencies/dish-salmon.png'
      elif im.pixels:im.pack()
# Embed exact instructions and native registry, export all24 actions even when idle cohort bound.
for name,file in [('Lena01 capture instructions','render_round01.py'),('Lena01 native registry','rig-round01.json')]:
 path=P/file
 if path.exists():t=bpy.data.texts.new(name);t.write(path.read_text())
ids={sc}
for c in rig['clips'].values():
 for t in c['actions']:ids.add(bpy.data.actions[t['action']])
bpy.data.libraries.write(str(P/'round-01.blend'),ids,fake_user=True,compress=True)
recipe={'round':1,'sourceSHA256':hashlib.sha256((P/'original-library.blend').read_bytes()).hexdigest(),'scene':sc.name,'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'pixelAspect':[1,1],'root':px((0,0,0)),'unitX':[a-b for a,b in zip(px((1,0,0)),px((0,0,0)))],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),px((0,0,0)))],'unitHeight':[a-b for a,b in zip(px((0,0,1)),px((0,0,0)))]},'renderer':{'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'filter':'BOX1','viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure},'rest':rest,'materials':{k: {'diffuseLinear':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for k,m in M.items()},'notes':['All bevels baked in rest coordinates before final armature evaluation; no shape keys used','Native action owners/timing/rig rest unchanged','Separate held dish2D uses original packed pixels; chef and knife native3D','No ground plane or directional shadow']}
(P/'recipe-round01.json').write_text(json.dumps(recipe,indent=2))
print('SAVED',P/'round-01.blend')
for d in ['S','E','N','W']:
 apply('idle',1,d);sc.render.filepath=str(OUT/('scout-'+d+'.png'));bpy.ops.render.render(write_still=True)
print('SCOUTS COMPLETE')
