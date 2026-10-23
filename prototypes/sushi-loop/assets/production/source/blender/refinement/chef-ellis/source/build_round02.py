import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-02';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(P));import native_actions_round02 as native
from audit_common_round02 import contacts,geometry
rig=json.loads((P/'rig-round02.json').read_text())
coll=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001']
sc=bpy.data.scenes.new('Ellis warm soft round02');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
for layer in bpy.context.view_layer.layer_collection.children:layer.exclude=False;layer.hide_viewport=False
for o in coll.all_objects:o.hide_set(False)
bpy.context.view_layer.update();asset={'collection':coll,'root':root,'armature':arm}
def apply(c,f=1,d='S'):native.apply_clip(asset,rig,c,f,d,sc)
source=[]
for c in rig['clips']:
 for d in ['S','E','N','W']:
  for f in range(1,13):
   apply(c,f,d);dg=bpy.context.evaluated_depsgraph_get();ct=contacts(coll,root,arm,dg);ct.update(clip=c,direction=d,index=f-1)
   ct['bodyBounds']=[[min(geometry(o,dg)['bounds'][i][0] for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name),max(geometry(o,dg)['bounds'][i][1] for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name)] for i in range(3)];source.append(ct)
(P/'source-contacts-round02.json').write_text(json.dumps(source,separators=(',',':')))
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones};(P/'source-rest-round02.json').write_text(json.dumps(rest,indent=2))
apply('idle');arm.data.pose_position='REST';bpy.context.view_layer.update()
def key(o):return o.name.split('__',1)[1].split('.')[0]
def mat(name,h,r=.64,s=.25):
 rgb=tuple((int(h[i:i+2],16)/255/12.92 if int(h[i:i+2],16)/255<=.04045 else ((int(h[i:i+2],16)/255+.055)/1.055)**2.4) for i in (0,2,4));m=bpy.data.materials.new('Ellis02 '+name);m.use_nodes=True;m.diffuse_color=(*rgb,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=r;p.inputs['Specular IOR Level'].default_value=s;return m
M={k:mat(k,h,r,s) for k,h,r,s in [('ivory','F5E9D1',.76,.22),('ivory-edge','E8D7B6',.76,.2),('skin','F5BD73',.61,.24),('hair','CB5B1D',.56,.26),('hair-light','DB6B23',.6,.24),('hair-deep','B94C18',.6,.24),('orange','D8750C',.73,.22),('orange-light','E58413',.7,.24),('orange-shadow','B85B0B',.78,.18),('navy','17386F',.68,.27),('navy-edge','224981',.7,.24),('navy-dark','172A45',.75,.2),('eye','211A16',.3,.34),('blush','E47D60',.8,.15),('glint','FFF4D8',.5,.22),('gold','EBC170',.5,.33),('metal','B5C8CE',.32,.5),('wood','68472F',.7,.2)]}
def material_for(o):
 k=key(o)
 if any(s in k for s in ['rounded_crown','occiput','curl','side_crown','brow']):return M['hair-light'] if k.endswith(('_1','_4')) else M['hair']
 if any(s in k for s in ['head','ear','palm','thumb','nose','neck']):return M['skin']
 if k.startswith('eye_glint'):return M['glint']
 if k.startswith(('eye','glasses')) or k=='smile':return M['eye']
 if k.startswith('cheek'):return M['blush']
 if k.startswith(('kerchief','apron')):return M['orange']
 if k.startswith(('minimal_foot','leg','pelvis')):return M['navy-dark']
 if k.startswith('cap'):return M['navy']
 if 'knife_handle' in k:return M['wood']
 if 'knife_blade' in k:return M['metal']
 return M['ivory']
# Preserve weighted coordinates and palm/sole centroids. Bake only existing edges at rest.
for o in list(coll.all_objects):
 if o.type!='MESH' or '__image_plane' in o.name:continue
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(material_for(o))
 if key(o).startswith('arm_'):
  o.data.materials.append(M['skin'])
  for p in o.data.polygons:p.material_index=1 if p.index==1 or p.index>=18 else 0
 for p in o.data.polygons:p.use_smooth=True
 for mod in list(o.modifiers):
  if mod.type=='WEIGHTED_NORMAL':o.modifiers.remove(mod)
  elif mod.type=='BEVEL':
   mod.segments=8 if key(o)!='head' else 12;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
def delete(pred):
 for o in list(coll.all_objects):
  if pred(key(o)):bpy.data.objects.remove(o,do_unlink=True)
def skin(o,name,mt,bone='head',weights=None):
 o.name='chef_ellis__R02_'+name
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
 if mt:o.data.materials.append(mt)
 if weights:
  for i,ws in enumerate(weights):
   for g,w in ws.items():vg=o.vertex_groups.get(g) or o.vertex_groups.new(name=g);vg.add([i],w,'REPLACE')
 else:vg=o.vertex_groups.new(name=bone);vg.add(range(len(o.data.vertices)),1,'REPLACE')
 for p in o.data.polygons:p.use_smooth=True
 mod=o.modifiers.new('Preserved native rig','ARMATURE');mod.object=arm;o['native_refinement_round']=2;return o
def mesh(name,vs,fs,mt,bone='head',weights=None):
 me=bpy.data.meshes.new('Ellis02 '+name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);return skin(o,name,mt,bone,weights)
def sphere(name,loc,scale,mt,bone='head',tilt=0):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=loc);o=bpy.context.object;o.scale=scale;o.rotation_euler.y=tilt;return skin(o,name,mt,bone)
def box(name,loc,size,mt,bone='head',bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);be=o.modifiers.new('Baked tailored edge','BEVEL');be.width=bevel;be.segments=8;bpy.ops.object.modifier_apply(modifier=be.name);return skin(o,name,mt,bone)
def tube(name,points,depth,mt,bone='head',closed=False):
 cv=bpy.data.curves.new('Ellis02 '+name,'CURVE');cv.dimensions='3D';cv.resolution_u=16;cv.bevel_depth=depth;cv.bevel_resolution=4;sp=cv.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,cv);sc.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);return skin(o,name,mt,bone)
# Coherent soft folded cap; lofted crown, shaped band and bowed brim. Max height remains1.1175 local.
delete(lambda k:k.startswith('cap_'))
N=96;vs=[];fs=[]
levels=[(.918,.90),(.931,.985),(.953,1.005),(1.035,1.018),(1.072,.98),(1.094,.88),(1.101,.65),(1.102,.25)]
for z,fac in levels:
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t);n=3.5;vs.append((.276*math.copysign(abs(c)**(2/n),c)*fac,.030+.234*math.copysign(abs(s)**(2/n),s)*fac,z))
for j in range(len(levels)-1):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.extend([tuple(reversed(range(N))),tuple(range((len(levels)-1)*N,len(levels)*N))]);mesh('padded_cap_crown',vs,fs,M['navy'])
vs=[];fs=[]
for z,fac in [(.922,.95),(.929,.995),(.944,1.0),(.966,.997),(.975,.963)]:
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t);n=3.5;vs.append((.277*math.copysign(abs(c)**(2/n),c)*fac,.023+.239*math.copysign(abs(s)**(2/n),s)*fac,z))
for j in range(4):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.extend([tuple(reversed(range(N))),tuple(range(4*N,5*N))]);mesh('folded_cap_band',vs,fs,M['navy-edge'])
# Curved solid brim using a rounded box warped downward at sides and front.
o=box('curved_cap_brim',(0,-.211,.972),(.532,.216,.042),M['navy'],'head',.018)
for v in o.data.vertices:
 x,y,z=v.co;v.co.z-=.026*(abs(x)/.266)**2+.012*max(0,(-y-.16)/.159)**2
sphere('cap_top_button',(0,.030,1.1045),(.022,.022,.013),M['navy-edge'])
# Quiet side construction seams lie on the loft itself, without floating decoration.
for idx,t in enumerate([3.95,5.475]):
 pts=[]
 for z,fac in levels[1:-1]:
  c=math.cos(t);ss=math.sin(t);n=3.5
  pts.append((.276*math.copysign(abs(c)**(2/n),c)*(fac+.003),.030+.234*math.copysign(abs(ss)**(2/n),ss)*(fac+.003),z))
 tube('cap_panel_seam_'+str(idx),pts,.0014,M['navy-edge'])
# Rounded head and face fittings, all weighted rigidly to the original head bone.
delete(lambda k:k in ['head','nose','smile'] or k.startswith(('eye','ear','brow','cheek','glasses')))
box('soft_square_head',(0,.005,.670),(.560,.480,.480),M['skin'],'head',.074)
for sgn in [-1,1]:
 sphere('soft_ear_'+str(sgn),(sgn*.293,.013,.650),(.029,.052,.0595),M['skin'])
 sphere('friendly_eye_'+str(sgn),(sgn*.103,-.250,.6892),(.022,.012,.034),M['eye'])
 sphere('eye_catchlight_'+str(sgn),(sgn*.103-.006,-.261,.700),(.006,.004,.009),M['glint'])
 sphere('soft_blush_'+str(sgn),(sgn*.182,-.237,.5908),(.034,.012,.017),M['blush'])
 tube('rounded_brow_'+str(sgn),[(sgn*.074,-.245,.763),(sgn*.104,-.251,.768),(sgn*.135,-.245,.760)],.009,M['hair'])
 # Smooth true circular rims; no lens sheet or target card.
 pts=[(sgn*.113+.071*math.cos(math.tau*i/16),-.272,.694+.071*math.sin(math.tau*i/16)) for i in range(16)]
 tube('round_spectacle_rim_'+str(sgn),pts,.010,M['eye'],closed=True)
 tube('spectacle_arm_'+str(sgn),[(sgn*.186,-.267,.694),(sgn*.214,-.222,.694),(sgn*.218,-.08,.694),(sgn*.216,.04,.687)],.0065,M['eye'])
tube('spectacle_bridge',[(-.034,-.273,.695),(0,-.277,.696),(.034,-.273,.695)],.008,M['eye'])
box('soft_button_nose',(0,-.258,.622),(.059,.047,.051),M['skin'],'head',.020)
tube('gentle_smile',[(-.043,-.248,.549),(-.025,-.257,.535),(0,-.261,.531),(.025,-.257,.535),(.043,-.248,.549)],.0065,M['eye'])
# Hair is native sculpted clumps. Keep source fringe silhouette but remove faceted beads.
hair=[]
for o in list(coll.all_objects):
 if o.type=='MESH' and any(s in key(o) for s in ['rounded_crown','rounded_occiput','temple_curl','fringe_curl','side_crown']):
  v=list(o.data.vertices);lo=Vector([min(q.co[i] for q in v) for i in range(3)]);hi=Vector([max(q.co[i] for q in v) for i in range(3)]);hair.append((key(o),(lo+hi)/2,(hi-lo)/2))
delete(lambda k:any(s in k for s in ['rounded_crown','rounded_occiput','temple_curl','fringe_curl','side_crown','back_curl']))
for i,(k,c,r) in enumerate(hair):
 if k=='rounded_occiput':r.y*=.94
 sphere('sculpted_'+k,c,r,M['hair-light'] if i%5==1 else M['hair'],tilt=.12*math.sin(i*2.1))
for row,z in enumerate([.554,.688,.825]):
 for i,x in enumerate([-.202,-.071,.075,.207]):
  xx=x+(.018 if row==1 else 0);yy=.251-.050*(abs(xx)/.23)**1.5
  sphere('back_lock_%s_%s'%(row,i),(xx,yy,z+.018*math.sin(i*1.9+row)),(.089,.068,.101),M['hair-light'] if (i+row)%4==0 else M['hair'],tilt=.18 if i%2 else -.16)
# Cloth reconstruction with soft edges, layered bib, straps, hem and pocket.
for k,w in [('tailored_tunic',.017),('apron_skirt',.012)]:
 o=next(o for o in coll.all_objects if key(o)==k);bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Baked rounded cloth edge','BEVEL');be.width=w;be.segments=6;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
delete(lambda k:k in ['apron_bib','apron_pocket'] or k.startswith(('collar','kerchief_tail','coat_button')))
box('layered_apron_bib',(0,-.163,.273),(.270,.035,.151),M['orange-light'],'spine',.019)
box('bib_top_welt',(0,-.185,.337),(.244,.010,.012),M['orange'],'spine',.005)
box('roomy_apron_pocket',(0,-.188,.153),(.180,.027,.068),M['orange-light'],'pelvis',.014)
box('pocket_welt',(0,-.205,.181),(.163,.009,.010),M['orange-shadow'],'pelvis',.004)
box('apron_hem_front',(0,-.179,.092),(.387,.015,.016),M['orange-shadow'],'pelvis',.006)
for sgn in [-1,1]:
 box('apron_strap_'+str(sgn),(sgn*.104,-.155,.365),(.032,.024,.081),M['orange'],'spine',.010)
 sphere('bib_fastener_'+str(sgn),(sgn*.106,-.191,.323),(.010,.006,.010),M['gold'],'spine')
 pts=[(sgn*.008,-.144,.412),(sgn*.109,-.143,.393),(sgn*.080,-.180,.361),(sgn*.021,-.179,.371)]
 vs=pts+[(x,y+.014,z) for x,y,z in pts];fs=[(0,1,2,3),(7,6,5,4)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 o=mesh('shaped_collar_'+str(sgn),vs,fs,M['ivory'],'spine');bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Baked collar edge','BEVEL');be.width=.007;be.segments=5;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
 pts=[(sgn*.010,-.209,.327),(sgn*.049,-.211,.319),(sgn*.078,-.214,.258),(sgn*.045,-.219,.239),(sgn*.022,-.215,.265)];vs=pts+[(x,y+.020,z) for x,y,z in pts];fs=[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
 o=mesh('shaped_scarf_tail_'+str(sgn),vs,fs,M['orange'],'spine');bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Baked scarf hem','BEVEL');be.width=.006;be.segments=5;bpy.ops.object.modifier_move_up(modifier=be.name);bpy.ops.object.modifier_apply(modifier=be.name)
kn=next(o for o in coll.all_objects if key(o)=='kerchief_knot')
for v in kn.data.vertices:v.co.y-=.045
sphere('back_apron_knot',(0,.158,.191),(.027,.019,.023),M['orange-light'],'pelvis')
box('back_coat_yoke',(0,.145,.335),(.256,.018,.025),M['ivory-edge'],'spine',.010)
# Smooth ring-based sleeves and rolled cuffs use unchanged source centerline/weights.
for side,sgn in [('L',-1),('R',1)]:
 old=next(o for o in coll.all_objects if key(o)=='arm_'+side);a=Vector((sgn*.198,.004,.352));j=Vector((sgn*.249,-.002,.247));end=Vector((sgn*.267,-.023,.211));names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
 rings=[(a,.065,{names[0]:.85,'spine':.15}),((a+j)*.5,.061,{names[0]:1}),(j,.057,{names[0]:.5,names[1]:.5}),((j+end)*.5,.052,{names[1]:1}),(end,.048,{names[1]:.35,names[2]:.65})];vs=[];ws=[];fs=[];seg=32
 for idx,(p,r,w) in enumerate(rings):
  d=(rings[min(idx+1,4)][0]-rings[max(0,idx-1)][0]).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized()
  for k in range(seg):t=math.tau*k/seg;vs.append(p+u*math.cos(t)*r+v*math.sin(t)*r*.88);ws.append(w)
 fs=[tuple(reversed(range(seg))),tuple(range(4*seg,5*seg))]+[(j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i) for j2 in range(4) for i in range(seg)]
 o=mesh('rounded_arm_'+side,vs,fs,M['ivory'],weights=ws);o.data.materials.append(M['skin'])
 for p in o.data.polygons:p.material_index=1 if p.index==1 or p.index>=2+2*seg else 0
 bpy.data.objects.remove(old,do_unlink=True);p=j;d=(end-a).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized();vs=[];fs=[]
 for h,r in [(-.017,.058),(-.013,.063),(.009,.063),(.015,.055)]:
  for k in range(seg):t=math.tau*k/seg;vs.append(p+d*h+u*math.cos(t)*r+v*math.sin(t)*r*.88)
 for j2 in range(3):
  for i in range(seg):fs.append((j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i))
 mesh('rolled_cuff_'+side,vs,fs,M['ivory-edge'],weights=[{names[0]:.5,names[1]:.5}]*len(vs))
# Exact camera projection (horizontal fit), no subject fitting.
cam=bpy.data.objects.new('Ellis02 registered35 camera',bpy.data.cameras.new('Ellis02 registered35 camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_y=.4583320617675781;cam.matrix_world=Matrix(json.loads((BASE/'inputs/source-camera.json').read_text())['camera']['worldMatrix'])
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1;bpy.context.view_layer.update()
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*640]
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.025;sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30;sc.render.fps=12;sc.render.dither_intensity=0;sc.render.filter_size=1;sc.cycles.pixel_filter_type='BOX';sc.render.use_compositing=False;sc.render.use_sequencer=False
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.65
world=bpy.data.worlds.new('Ellis02 warm ambient');world.use_nodes=True;sc.world=world;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.82,.77,.67,1);bg.inputs['Strength'].default_value=.25
for i,(pos,energy,size) in enumerate([((0,0,4.5),200,3.5),((3,0,2),35,4),((-3,0,2),35,4),((0,3,2),35,4),((0,-3,2),35,4)]):
 ld=bpy.data.lights.new('Ellis02 symmetric area '+str(i),'AREA');lo=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(lo);lo.location=pos;lo.rotation_euler=(Vector((0,0,.8))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=energy;ld.shape='DISK';ld.size=size;ld.color=(1,.96,.88)
arm.data.pose_position='POSE';apply('idle');root['refinement_style']='Warm soft native cartoon: padded cap, smooth circular spectacles, soft curls and tailored apron'
for o in coll.all_objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image and n.image.packed_file:
      dep=P/'dependencies/dish-salmon.png';dep.parent.mkdir(exist_ok=True);dep.write_bytes(n.image.packed_file.data);n.image.filepath='//dependencies/dish-salmon.png'
ids={sc}
for c in rig['clips'].values():
 for t in c['actions']:ids.add(bpy.data.actions[t['action']])
bpy.data.libraries.write(str(P/'round-02.blend'),ids,fake_user=True,compress=True)
recipe={'asset':'chef-ellis','round':2,'sourceSHA256':hashlib.sha256((P/'original-library.blend').read_bytes()).hexdigest(),'scene':sc.name,'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'pixelAspect':[1,1],'root':px((0,0,0)),'unitX':[a-b for a,b in zip(px((1,0,0)),px((0,0,0)))],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),px((0,0,0)))],'unitHeight':[a-b for a,b in zip(px((0,0,1)),px((0,0,0)))]},'renderer':{'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'denoise':True,'filter':'BOX1','viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure},'materials':{k:{'diffuseLinear':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for k,m in M.items()},'notes':['Baked geometry in original rest space, source rig/rest/native actions retained','Padded lofted cap/fold/bowed brim; crown seams and smooth spectacles; shaped collar/cuff/apron construction','Separate source packed2D salmon and source native3D knife preserved','No ground or preferred horizontal light; no per-view/post-render adjustment']};(P/'recipe-round02.json').write_text(json.dumps(recipe,indent=2))
print('SAVED',P/'round-02.blend',flush=True)
for d in ['S','E','N','W']:
 apply('idle',1,d);sc.render.filepath=str(OUT/('scout-'+d+'.png'));bpy.ops.render.render(write_still=True)
print('SCOUTS COMPLETE',flush=True)
