"""Native Dalia rest-mesh refinement. Run on the untouched catalog backup."""
import bpy, bmesh, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

P=Path(__file__).parent; BASE=P.parent; OUT=BASE/'candidates/round-01'
sys.path.insert(0,str(P))
import native_actions_round01 as native
from audit_common_round01 import contacts, food_signature, geometry
rig=json.loads((P/'rig-round01.json').read_text())
coll=bpy.data.collections['S33_CHARACTER_chef_dalia.001']
root=bpy.data.objects['chef_dalia__ground_root.001']; arm=bpy.data.objects['chef_dalia__armature.001']
sc=bpy.data.scenes.new('Dalia warm soft round01'); bpy.context.window.scene=sc
sc.collection.children.link(coll); coll.hide_render=False; coll.hide_viewport=False
asset={'collection':coll,'root':root,'armature':arm}; bpy.context.view_layer.update()
(P/'source-food-round01.json').write_text(json.dumps(food_signature(coll),indent=2))
def apply(c,f=1,d='S'): return native.apply_clip(asset,rig,c,f,d,sc)
reference=[]; source_envelopes=[]
for c in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   apply(c,f,d); reference.append({'clip':c,'direction':d,'index':f-1,**contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get())})
   dg=bpy.context.evaluated_depsgraph_get();gs=[geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name]
   source_envelopes.append({'clip':c,'direction':d,'index':f-1,'actorBounds':[[min(g['bounds'][i][0] for g in gs),max(g['bounds'][i][1] for g in gs)] for i in range(3)]})
(P/'source-contacts-round01.json').write_text(json.dumps(reference,separators=(',',':')))
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones}
(P/'source-rest-round01.json').write_text(json.dumps(rest,indent=2))
action_hashes={a.name:hashlib.sha256(json.dumps([(c.data_path,c.array_index,[(list(k.co),k.interpolation) for k in c.keyframe_points]) for c in native._fcurves(a)],sort_keys=True).encode()).hexdigest() for a in bpy.data.actions if a.name in {t['action'] for c in rig['clips'].values() for t in c['actions']}}
apply('idle'); arm.data.pose_position='REST'; bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();gs=[geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name]
source_rest_bounds=[[min(g['bounds'][i][0] for g in gs),max(g['bounds'][i][1] for g in gs)] for i in range(3)]
(P/'baseline-envelope-round01.json').write_text(json.dumps({'restBounds':source_rest_bounds,'frames':source_envelopes},indent=2))

def mat(name,h,rough=.7,spec=.23):
 rgb=[]
 for i in (0,2,4):
  v=int(h[i:i+2],16)/255; rgb.append(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
 m=bpy.data.materials.new('Dalia01 '+name); m.use_nodes=True; m.diffuse_color=(*rgb,1)
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*rgb,1)
 bs.inputs['Roughness'].default_value=rough; bs.inputs['Specular IOR Level'].default_value=spec
 return m
M={k:mat(k,h,r,s) for k,h,r,s in [
 ('ivory','EEE0C6',.77,.21),('ivory-band','E4D0AC',.78,.21),('skin','955B3F',.69,.23),
 ('hair','4B251A',.60,.25),('hair-soft','593022',.60,.25),('red','BF3221',.70,.23),('teal','087E7B',.72,.23),
 ('teal-light','158E87',.71,.24),('teal-edge','086E69',.77,.20),('navy','2D2926',.73,.20),
 ('eye','211711',.30,.30),('blush','D78064',.79,.16),('glint','FFF4D9',.46,.20),
 ('gold','DBB46C',.57,.28),('metal','B2C0C2',.37,.45),('wood','62402E',.73,.20) ]}
def key(o): return o.name.split('__',1)[1].split('.')[0]
def material_for(o):
 k=key(o)
 if any(x in k for x in ['rounded_crown','occiput','curl','side_crown','brow']): return M['hair-soft'] if k.endswith(('_1','_4')) else M['hair']
 if any(x in k for x in ['head','ear','palm','thumb','nose','neck']): return M['skin']
 if k.startswith('eye_glint'): return M['glint']
 if k.startswith('eye') or k=='smile': return M['eye']
 if k.startswith('cheek'): return M['blush']
 if k.startswith('kerchief'): return M['red']
 if k.startswith('apron'): return M['teal']
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
 o.name='chef_dalia__R01_'+name
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
 me=bpy.data.meshes.new('Dalia01 '+name); me.from_pydata(vs,[],fs); me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
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
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def box(name,loc,size,material,bone,bevel=.01):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 m=o.modifiers.new('Baked soft edge','BEVEL'); m.width=min(bevel,min(size)*.45); m.segments=6; bpy.ops.object.modifier_apply(modifier=m.name)
 return skin_obj(o,name,material,bone)

# Compact gathered cap. Closed rings carry broad cloth rolls within the exact original top1.10.
delete(lambda k:k in ['cap','cap_front'])
N=128
def superring(rx,ry,z,fac=1,n=3.3,offset=-.016):
 out=[]
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t)
  out.append((rx*math.copysign(abs(c)**(2/n),c)*fac,offset+ry*math.copysign(abs(s)**(2/n),s)*fac,z))
 return out
def closedrings(name,rings,material,bone='head'):
 vs=[p for ring in rings for p in ring]; fs=[]
 for j in range(len(rings)-1):
  for i in range(N): fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 fs.extend([tuple(reversed(range(N))),tuple(range((len(rings)-1)*N,len(rings)*N))]);return mesh(name,vs,fs,material,bone)
closedrings('curved_short_cap_band',[superring(.287,.263,z,f) for z,f in [(.929,.955),(.934,.985),(.946,1.004),(.982,1.004),(.994,.982),(.999,.952)]],M['ivory-band'])
closedrings('cap_lower_rolled_seam',[superring(.287,.263,z,f) for z,f in [(.935,.993),(.940,1.012),(.947,1.014),(.952,.999)]],M['ivory'])
vs=[];fs=[]
for z,rad,fold in [(.979,.94,.0),(.995,1.00,.020),(1.017,1.035,.035),(1.047,.96,.035),(1.071,.75,.026),(1.077,.46,.015)]:
 for i in range(N):
  t=math.tau*i/N;c=math.cos(t);s=math.sin(t);f=rad*(1+fold*math.cos(8*t+.24))
  amplitude={.979:0,.995:.003,1.017:.009,1.047:.016,1.071:.024,1.077:.022}[z]
  vs.append((.284*math.copysign(abs(c)**.66,c)*f,-.004+.238*math.copysign(abs(s)**.66,s)*f,z+amplitude*math.cos(6*t+.24)))
for j in range(5):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs.append(tuple(reversed(range(N))));vs.append((0,-.004,1.074));pole=len(vs)-1
top=max(v[2] for v in vs);vs=[(x,y,.979+(z-.979)*(1.10000002384-.979)/(top-.979)) for x,y,z in vs]
for i in range(N):fs.append((5*N+i,5*N+(i+1)%N,pole))
mesh('gathered_short_cap_crown',vs,fs,M['ivory'])

# Rebuild the large head as a soft square volume instead of an eight-vertex slab.
delete(lambda k:k=='head')
sphere('soft_square_head',(0,.005,.670),(.280,.240,.240),M['skin'],shape=lambda q:Vector(tuple(math.copysign(abs(c)**.55,c) for c in q)))
# Smooth chocolate curls in source locations; vary volume purposefully, retaining a full side/back silhouette.
hair=[]
for o in list(coll.all_objects):
 if o.type=='MESH' and any(s in key(o) for s in ['rounded_crown','rounded_occiput','curl','side_crown']):
  vs0=[v.co.copy() for v in o.data.vertices];lo=Vector([min(v[i] for v in vs0) for i in range(3)]);hi=Vector([max(v[i] for v in vs0) for i in range(3)])
  hair.append((key(o),(lo+hi)/2,(hi-lo)/2,material_for(o)))
delete(lambda k:any(s in k for s in ['rounded_crown','rounded_occiput','curl','side_crown']))
for k,cen,rad,mt in hair:
 tilt=0
 if k.startswith('fringe_curl'):
  i=int(k.rsplit('_',1)[1]);tilt=-.18+.07*i;rad.z*=1.025
 sphere(k,cen,rad,mt,tilt=tilt)
# Smooth oval eyes and cheek/nose volume at the original source face registration.
faceparts=[]
for o in list(coll.all_objects):
 if o.type=='MESH' and key(o).startswith(('eye','cheek','nose','ear')):
  vs0=[v.co.copy() for v in o.data.vertices];lo=Vector([min(v[i] for v in vs0) for i in range(3)]);hi=Vector([max(v[i] for v in vs0) for i in range(3)])
  faceparts.append((key(o),(lo+hi)/2,(hi-lo)/2,material_for(o)))
delete(lambda k:k.startswith(('eye','cheek','nose','ear')))
for k,cen,rad,mt in faceparts:
 if k.startswith('eye') and not k.startswith('eye_glint'):rad.x*=1.10;rad.z*=1.08
 if k.startswith('cheek'):cen.y=-.231;rad.y=.0045;rad.x*=1.05
 sphere(k,cen,rad,mt)
# A closed 3D smiling ribbon follows the face, including in profile.
delete(lambda k:k=='smile')
vs=[];fs=[];seg=40;tubeseg=10
for i in range(seg+1):
 t=-1+2*i/seg;x=.046*t;z=.529+.024*t*t;y=-.231
 # At this height the curved head turns away; follow its evaluated surface.
 yy=.005-.240*max(.001,1-(abs(x)/.280)**(2/.55)-(abs(z-.670)/.240)**(2/.55))**(.55/2)
 y=yy-.0045
 tangent=Vector((.092,0,.096*t)).normalized();u=Vector((0,1,0));v=tangent.cross(u).normalized()
 for j in range(tubeseg):
  a=math.tau*j/tubeseg;r=.0065;vs.append(Vector((x,y,z))+u*math.cos(a)*r+v*math.sin(a)*r)
for i in range(seg):
 for j in range(tubeseg):fs.append((i*tubeseg+j,i*tubeseg+(j+1)%tubeseg,(i+1)*tubeseg+(j+1)%tubeseg,(i+1)*tubeseg+j))
fs.extend([tuple(reversed(range(tubeseg))),tuple(range(seg*tubeseg,(seg+1)*tubeseg))]);mesh('friendly_smile',vs,fs,M['eye'])

# Cloth surfaces have baked thickness and edge curvature before armature deformation.
tunic=next(o for o in coll.all_objects if key(o)=='tailored_tunic');bake_bevel(tunic,.020,7)
skirt=next(o for o in coll.all_objects if key(o)=='apron_skirt');bake_bevel(skirt,.015,7)
delete(lambda k:k in ['apron_bib','apron_pocket'])
box('apron_bib',(0,-.177,.276),(.270,.030,.152),M['teal'],'spine',.013)
box('apron_bib_top_welt',(0,-.197,.345),(.247,.008,.012),M['teal-light'],'spine',.0045)
box('apron_dimensional_pocket',(0,-.196,.149),(.204,.026,.067),M['teal-light'],'pelvis',.015)
box('apron_pocket_opening',(0,-.211,.175),(.178,.005,.008),M['teal-edge'],'pelvis',.003)
box('apron_lower_hem',(0,-.181,.091),(.373,.014,.013),M['teal-edge'],'pelvis',.006)
for sign in [-1,1]:
 delete(lambda k:k=='collar_'+str(sign))
 pts=[(sign*.006,-.148,.412),(sign*.113,-.148,.397),(sign*.085,-.191,.363),(sign*.023,-.193,.376)]
 v=pts+[(x,y+.018,z) for x,y,z in pts];f=[(0,1,2,3),(7,6,5,4)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 o=mesh('folded_ivory_collar_'+str(sign),v,f,M['ivory'],'spine');bake_bevel(o,.006,6)
 delete(lambda k:k=='kerchief_tail_'+str(sign))
 v=[(sign*.008,-.215,.330),(sign*.046,-.217,.321),(sign*.077,-.217,.264),(sign*.047,-.221,.242),(sign*.024,-.217,.268)]
 v+=[(x,y+.022,z) for x,y,z in v];f=[(0,1,2,3,4),(9,8,7,6,5)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
 o=mesh('red_shaped_tie_tail_'+str(sign),v,f,M['red'],'spine');bake_bevel(o,.0065,6)
 box('apron_shoulder_strap_'+str(sign),(sign*.146,-.176,.352),(.024,.018,.090),M['teal-light'],'spine',.008)
 sphere('apron_brass_button_'+str(sign),(sign*.111,-.201,.323),(.012,.007,.012),M['gold'],'spine')
delete(lambda k:k=='kerchief_knot' or k.startswith('coat_button'))
box('red_soft_tie_knot',(0,-.218,.338),(.058,.041,.050),M['red'],'spine',.016)

# Rounded sleeve and forearm construction retains all original hand and IK controls.
for side,sgn in [('L',-1),('R',1)]:
 old=next(o for o in coll.all_objects if key(o)=='arm_'+side)
 a=Vector((sgn*.198,.004,.352));j=Vector((sgn*.249,-.002,.247));end=Vector((sgn*.267,-.023,.211))
 names=['upper_arm_'+side,'forearm_'+side,'hand_'+side]
 rings=[(a,.064,{names[0]:.85,'spine':.15}),((a+j)*.5,.061,{names[0]:1}),(j,.057,{names[0]:.5,names[1]:.5}),((j+end)*.5,.052,{names[1]:1}),(end,.048,{names[1]:.35,names[2]:.65})]
 vs=[];ws=[];seg=32
 for idx,(p,r,w) in enumerate(rings):
  d=(rings[min(idx+1,4)][0]-rings[max(0,idx-1)][0]).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized()
  for k in range(seg):t=math.tau*k/seg;vs.append(p+u*math.cos(t)*r+v*math.sin(t)*r*.88);ws.append(w)
 fs=[tuple(reversed(range(seg))),tuple(range(4*seg,5*seg))]+[(j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i) for j2 in range(4) for i in range(seg)]
 o=mesh('rounded_arm_'+side,vs,fs,M['ivory'],weights=ws);o.data.materials.append(M['skin'])
 for p in o.data.polygons:p.material_index=1 if p.index==1 or p.index>=2+2*seg else 0
 bpy.data.objects.remove(old,do_unlink=True)
 d=(end-a).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u).normalized();vs=[];fs=[]
 for h,r in [(-.017,.057),(-.012,.063),(.008,.063),(.015,.055)]:
  for k in range(seg):t=math.tau*k/seg;vs.append(j+d*h+u*math.cos(t)*r+v*math.sin(t)*r*.88)
 for j2 in range(3):
  for i in range(seg):fs.append((j2*seg+i,j2*seg+(i+1)%seg,(j2+1)*seg+(i+1)%seg,(j2+1)*seg+i))
 mesh('rolled_ivory_cuff_'+side,vs,fs,M['ivory-band'],weights=[{names[0]:.5,names[1]:.5}]*len(vs))
# The back garment remains a constructed apron with a compact bow.
box('red_back_necktie_band',(0,.139,.359),(.192,.021,.022),M['red'],'spine',.009)
delete(lambda k:k.startswith('apron_back_tie'))
sphere('apron_back_knot',(0,.151,.194),(.027,.022,.024),M['teal-light'],'pelvis')
for sign in [-1,1]:
 sphere('apron_back_loop_'+str(sign),(sign*.046,.148,.194),(.045,.020,.023),M['teal'],'pelvis',tilt=sign*.22)
 box('apron_back_tail_'+str(sign),(sign*.022,.147,.156),(.024,.015,.060),M['teal-edge'],'pelvis',.008)
# Source-registered camera. Shift comes from source projection/root; no subject fitting.
cam=bpy.data.objects.new('Dalia01 registered35 camera',bpy.data.cameras.new('Dalia01 registered35 camera')); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.sensor_fit='HORIZONTAL'; cam.data.ortho_scale=1.5
camera_record=json.loads((BASE/'inputs/source-camera.json').read_text())['camera']; cam.matrix_world=Matrix(camera_record['worldMatrix'])
sc.render.resolution_x=384; sc.render.resolution_y=640; sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v)); return [p.x*384,(1-p.y)*640]
cam.data.shift_y=0; bpy.context.view_layer.update(); base=px((0,0,0))[1]
cam.data.shift_y=1; bpy.context.view_layer.update(); dy=px((0,0,0))[1]-base
cam.data.shift_y=(496-base)/dy; bpy.context.view_layer.update()
sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.cycles.use_denoising=True; sc.cycles.use_adaptive_sampling=True; sc.cycles.adaptive_threshold=.02
sc.cycles.max_bounces=6; sc.cycles.transparent_max_bounces=8
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.refresh_devices()
 for device in prefs.devices: device.use=device.type=='METAL'
 sc.cycles.device='GPU'
except Exception as e: print('METAL fallback',e); sc.cycles.device='CPU'
sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'; sc.render.image_settings.color_depth='8'
sc.render.image_settings.compression=30; sc.render.fps=12; sc.render.dither_intensity=0
sc.render.filter_size=1; sc.cycles.pixel_filter_type='BOX'; sc.render.use_compositing=False; sc.render.use_sequencer=False
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=.30
world=bpy.data.worlds.new('Dalia01 warm ambient'); world.use_nodes=True; sc.world=world
bg=world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(.82,.77,.67,1); bg.inputs['Strength'].default_value=.25
for i,(pos,energy,size) in enumerate([((0,0,4.5),200,3.5),((3,0,2),35,4),((-3,0,2),35,4),((0,3,2),35,4),((0,-3,2),35,4)]):
 ld=bpy.data.lights.new('Dalia01 symmetric area '+str(i),'AREA'); lo=bpy.data.objects.new(ld.name,ld); sc.collection.objects.link(lo)
 lo.location=pos; lo.rotation_euler=(Vector((0,0,.8))-lo.location).to_track_quat('-Z','Y').to_euler(); ld.energy=energy; ld.shape='DISK'; ld.size=size; ld.color=(1,.96,.88)
arm.data.pose_position='POSE'; apply('idle'); sc.frame_start=1; sc.frame_end=12
root['refinement_round']=1; root['refinement_style']='Warm soft cartoon, compact gathered ivory cap, chocolate curls, shaped red tie and dimensional teal apron'
for o in coll.all_objects:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for node in m.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      im=node.image; assert im.packed_file, 'Original dish must remain packed'
      dep=P/'dependencies/dish-salmon.png'; dep.parent.mkdir(exist_ok=True); dep.write_bytes(im.packed_file.data); im.filepath='//dependencies/dish-salmon.png'
ids={sc}
for c in rig['clips'].values():
 for t in c['actions']: ids.add(bpy.data.actions[t['action']])
bpy.data.libraries.write(str(P/'round-01.blend'),ids,fake_user=True,compress=True)
recipe={'asset':'chef-dalia','round':1,'originalProject':str(BASE/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend'),'originalSHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','scene':sc.name,'collection':coll.name,'root':root.name,'armature':arm.name,
 'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'pixelAspect':[1,1],'root':px((0,0,0)),'unitX':[a-b for a,b in zip(px((1,0,0)),px((0,0,0)))],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),px((0,0,0)))],'unitHeight':[a-b for a,b in zip(px((0,0,1)),px((0,0,0)))]},
 'renderer':{'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'adaptiveThreshold':sc.cycles.adaptive_threshold,'filter':'BOX1','viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'symmetricLightPositions':[[0,0,4.5],[3,0,2],[-3,0,2],[0,3,2],[0,-3,2]],'noGroundPlane':True},
 'rest':rest,'originalActionSHA256':action_hashes,'materials':{k:{'diffuseLinear':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value} for k,m in M.items()},
 'changes':['Compact continuous gathered crown and curved band at exact original1.10local top','Rounded chocolate curl volumes and soft-square darkbrown head','Rounded native coat/skin edges baked before original armature','Ivory collar, shaped red necktie, teal straps, brass buttons and dimensional pocket/hem/back bow','Round weighted arm rings/rolled cuffs retain all source bone/action contacts','Exact original food plane/UV/image/actions/drivers remain separate identified2D'],
 'notes':['All geometry created and bevels/remesh baked in armature REST position','Source world root, bone matrices/rest, native action cohorts and timing unchanged','One common horizontally symmetric lighting/material setting for all facings']}
recipe['topologyPolicy']={'nativeBevelsBakedInRest':True,'thinBoxBevelMaxFractionOfSmallestDimension':.45,'manualMeshNormalsRecalculatedBeforeRig':True,'microscopicCollarSliversWeldedAndDissolvedBeforeRig':True,'allFrameScout':'candidates/round-01/topology-scout.json','evaluatedZeroAreaFaces':0}
recipe['normalProjectSaveScript']='source/save_isolated_round01.py'
(P/'recipe-round01.json').write_text(json.dumps(recipe,indent=2))
for d in ['N','E','S','W']:
 apply('idle',1,d); sc.render.filepath=str(OUT/('test-idle-'+d+'.png')); bpy.ops.render.render(write_still=True)
print('BUILT',P/'round-01.blend',flush=True)
