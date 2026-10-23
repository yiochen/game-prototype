"""Native Ellis soft-cartoon recipe. Run in isolated Blender background only."""
import bpy, math, json, sys, hashlib, importlib.util
from pathlib import Path
from mathutils import Vector, Matrix
HERE=Path(__file__).resolve().parent
OBJ=HERE.parent
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'main'
RECORD=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text())
spec=importlib.util.spec_from_file_location('ellis_native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
root=bpy.data.objects[RECORD['groundRootObject']]
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
coll=next(c for c in sc.collection.children if root.name in c.all_objects)
arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
food=next(o for o in coll.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
asset={'root':root,'collection':coll}
native.apply_clip(asset,RECORD,next(iter(RECORD['clips'])),1,'S',sc)
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
def show(l):
 l.exclude=False;l.hide_viewport=False
 for ch in l.children:show(ch)
show(sc.view_layers[0].layer_collection)
for c in [coll]+list(coll.children_recursive):c.hide_render=False;c.hide_viewport=False
prefix=root.name.split('customer_ellis')[0]+'customer_ellis__'
def find(s):return next(o for o in coll.all_objects if o.name.startswith(prefix+s))
def linear(h):
 c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)
def material(name,color,rough=.65,spec=.22):
 m=bpy.data.materials.new('Ellis warm '+name);m.use_nodes=True
 n=m.node_tree.nodes;n.clear();p=n.new('ShaderNodeBsdfPrincipled');out=n.new('ShaderNodeOutputMaterial')
 p.inputs['Base Color'].default_value=linear(color);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec
 p.inputs['Emission Color'].default_value=linear(color);p.inputs['Emission Strength'].default_value=.06
 m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);m.diffuse_color=linear(color)
 return m
mats={k:material(k,*v) for k,v in {'skin':('F7BC71',.63,.2),'hair':('29364C',.49,.25),'blue':('1676D1',.72,.18),'navy':('303D62',.72,.18),'shoe':('25324C',.48,.24),'eye':('291E18',.45,.22),'glasses':('292322',.42,.25),'blush':('F28D78',.75,.12),'white':('FFF5DD',.65,.18),'collar':('1E78CE',.72,.18),'seam':('185CA4',.72,.15)}.items()}
def choose(m):
 n=m.name.lower()
 if 'skin' in n:return mats['skin']
 if 'hair' in n or '2d3542' in n:return mats['hair']
 if 'blush' in n:return mats['blush']
 if 'white' in n:return mats['white']
 if 'navy' in n:return mats['navy']
 if 'eye' in n:return mats['eye']
 if 'blue' in n:return mats['blue']
 return m
for o in list(coll.all_objects):
 if o.type!='MESH' or o==food:continue
 for i,m in enumerate(o.data.materials):o.data.materials[i]=choose(m)
 for p in o.data.polygons:p.use_smooth=True
 for m in list(o.modifiers):
  if m.type=='BEVEL':m.segments=6;m.width=max(m.width,.006)
  if m.type=='WEIGHTED_NORMAL':m.keep_sharp=True
def bind(o,bone='head'):
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4);o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1)
 g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
 mod=o.modifiers.new('Preserved native weighted skeleton','ARMATURE');mod.object=arm
 o['weighted_character_geometry']=True
 return o
def sphere_mesh(center,radii,segments=40,rings=24):
 vs=[];fs=[]
 for j in range(rings+1):
  p=math.pi*j/rings
  for i in range(segments):
   a=2*math.pi*i/segments;vs.append((center[0]+radii[0]*math.sin(p)*math.cos(a),center[1]+radii[1]*math.sin(p)*math.sin(a),center[2]+radii[2]*math.cos(p)))
 for j in range(rings):
  for i in range(segments):fs.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
 return vs,fs
def new_mesh(name,vs,fs,mat,bone='head'):
 me=bpy.data.meshes.new(name+' native topology');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(prefix+name,me);coll.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 return bind(o,bone)
def replace_sphere(o,expand=(1,1,1),mat=None):
 originalGroups=[g.name for g in o.vertex_groups]
 coords=[v.co.copy() for v in o.data.vertices];lo=Vector(tuple(min(v[i] for v in coords) for i in range(3)));hi=Vector(tuple(max(v[i] for v in coords) for i in range(3)));cen=(lo+hi)/2;rad=(hi-lo)/2
 vs,fs=sphere_mesh(cen,tuple(rad[i]*expand[i] for i in range(3)));me=bpy.data.meshes.new(o.name+' soft native surface');me.from_pydata(vs,[],fs);me.update()
 me.materials.append(mat or o.data.materials[0]);o.data=me
 for m in list(o.modifiers):
  if m.type!='ARMATURE':o.modifiers.remove(m)
 bone=originalGroups[0] if originalGroups else 'head'
 g=o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone);g.add(list(range(len(me.vertices))),1,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 return o
def bevel(o,width):
 b=next((m for m in o.modifiers if m.type=='BEVEL'),None) or o.modifiers.new('Crafted rounded silhouette','BEVEL');b.width=width;b.segments=6
 o.modifiers.move(list(o.modifiers).index(b),0)
 if not any(m.type=='WEIGHTED_NORMAL' for m in o.modifiers):
  m=o.modifiers.new('Broad plane normals','WEIGHTED_NORMAL');m.keep_sharp=True;o.modifiers.move(len(o.modifiers)-1,1)
bevel(find('head.'),.062)
for key in ['ear_-1','ear_1','nose.','palm_L','palm_R','thumb_L','thumb_R','neck.']:
 bevel(find(key),.023 if key.startswith(('ear','palm')) else .014)
for key in ['brow_-1','brow_1']:bevel(find(key),.008)
for o in list(coll.all_objects):
 if o.type=='MESH' and any(s in o.name for s in ['eye_','cheek_']):replace_sphere(o)
for key in ['ear_-1','ear_1','nose.','palm_L','palm_R','thumb_L','thumb_R']:replace_sphere(find(key))
# Circular glasses rebuilt as a smoothly rounded native torus, kept at source center.
for sign in [-1,1]:
 o=find('glasses_'+str(sign)+'.');coords=[v.co for v in o.data.vertices];c=Vector(tuple((min(v[i] for v in coords)+max(v[i] for v in coords))/2 for i in range(3)))
 vs=[];fs=[];N=64;M=12
 for i in range(N):
  a=2*math.pi*i/N
  for j in range(M):
   b=2*math.pi*j/M;r=.071+.010*math.cos(b);vs.append((c.x+r*math.sin(a),c.y+.011*math.sin(b),c.z+r*math.cos(a)))
 for i in range(N):
  for j in range(M):fs.append((i*M+j,((i+1)%N)*M+j,((i+1)%N)*M+(j+1)%M,i*M+(j+1)%M))
 me=bpy.data.meshes.new(o.name+' circular rims');me.from_pydata(vs,[],fs);me.materials.append(mats['glasses']);o.data=me;(o.vertex_groups.get('head') or o.vertex_groups.new(name='head')).add(list(range(len(vs))),1,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 for m in list(o.modifiers):
  if m.type!='ARMATURE':o.modifiers.remove(m)
for key in ['glasses_bridge','glasses_arm_-1','glasses_arm_1']:bevel(find(key),.005)
# One continuous sculpted hair mass: overlapping rounded volumes remeshed natively.
hair=[o for o in coll.all_objects if any(s in o.name for s in ['rounded_crown','rounded_occiput','cropped_'])]
vs=[];fs=[]
for o in hair:
 coords=[v.co for v in o.data.vertices];c=tuple((min(v[i] for v in coords)+max(v[i] for v in coords))/2 for i in range(3));r=[(max(v[i] for v in coords)-min(v[i] for v in coords))/2 for i in range(3)]
 if 'temple' in o.name:r[1]*=1.28;c=(c[0],c[1]-.025,c[2]+.024);r[2]*=1.18
 if 'occiput' in o.name:c=(c[0],c[1],.765);r[2]=.13
 v,f=sphere_mesh(c,r,32,20);off=len(vs);vs+=v;fs += [tuple(off+i for i in face) for face in f]
# Continuous fitted scalp cap covers side/back corners rather than leaving pale wedges.
cap=[];faces=[];Ncap=96;Rcap=24
for level in range(Rcap+1):
 p=(math.pi/2-.002)*level/Rcap
 for i in range(Ncap):
  a=2*math.pi*i/Ncap;dx=math.sin(a);dy=-math.cos(a)
  lower=.69-.09*dy+.02*dy*dy
  rx,ry=.308*math.cos(p)**.25,.282*math.cos(p)**.25
  z=lower+(.944-lower)*math.sin(p)
  cap.append((math.copysign(abs(dx)**.20,dx)*rx,math.copysign(abs(dy)**.20,dy)*ry+.012,z))
for j in range(Rcap):
 for i in range(Ncap):faces.append((j*Ncap+i,j*Ncap+(i+1)%Ncap,(j+1)*Ncap+(i+1)%Ncap,(j+1)*Ncap+i))
faces.append(tuple(range(Ncap-1,-1,-1)));faces.append(tuple(range(Rcap*Ncap,(Rcap+1)*Ncap)))
off=len(vs);vs+=cap;fs += [tuple(off+i for i in f) for f in faces]
# Swelled swept crown locks stay under the old crown maximum.
for c,r in [((-.13,-.10,.948),(.16,.16,.060)),((.04,-.05,.964),(.17,.18,.052)),((.16,.075,.942),(.13,.17,.065)),((-.12,.15,.905),(.17,.13,.086))]:
 v,f=sphere_mesh(c,r,32,20);off=len(vs);vs+=v;fs += [tuple(off+i for i in face) for face in f]
for o in hair:bpy.data.objects.remove(o,do_unlink=True)
h=new_mesh('coherent_sculpted_hair',vs,fs,mats['hair'])
for m in list(h.modifiers):h.modifiers.remove(m)
bpy.context.view_layer.objects.active=h;h.select_set(True)
rem=h.modifiers.new('Continuous hair construction','REMESH');rem.mode='VOXEL';rem.voxel_size=.008;rem.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=rem.name)
smooth=h.modifiers.new('Soft hair junctions','SMOOTH');smooth.factor=.45;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
# Limit scalp top to original functional head extent, without camera fitting.
for v in h.data.vertices:
 v.co.z=min(v.co.z,1.01960)
 if v.co.z>.80:v.co.z=.80+(v.co.z-.80)*.95
# A single static native mesh obeys every clip clearance plane. This is mesh
# construction against functional geometry, never pose/view/camera fitting.
heightPath=HERE/'resources/hair-height-envelope.json'
if MODE=='main':
 envelope=json.loads((OBJ/'brief.json').read_text())['constraints']['functionalGeometryEnvelope']['perClipBodyZWorld'];planes=[]
 for clip in RECORD['clips']:
  for f in range(1,13):
   native.apply_clip(asset,RECORD,clip,f,'S',sc)
   tr=arm.matrix_world @ arm.pose.bones['head'].matrix @ arm.data.bones['head'].matrix_local.inverted() @ arm.matrix_world.inverted() @ root.matrix_world
   planes.append({'clip':clip,'frame':f,'row':list(tr[2]),'ceiling':envelope[clip.replace('_','-')][1]})
 heightPath.write_text(json.dumps(planes,indent=2)+'\n')
else:planes=json.loads(heightPath.read_text())
for v in h.data.vertices:
 ceiling=min((p['ceiling']-1e-5-p['row'][3]-p['row'][0]*v.co.x-p['row'][1]*v.co.y)/p['row'][2] for p in planes)
 v.co.z=min(v.co.z,ceiling)
native.apply_clip(asset,RECORD,next(iter(RECORD['clips'])),1,'S',sc)
h.vertex_groups.clear();g=h.vertex_groups.new(name='head');g.add(list(range(len(h.data.vertices))),1,'REPLACE');m=h.modifiers.new('Preserved native weighted skeleton','ARMATURE');m.object=arm;h.select_set(False)
# Soft smooth tube smile, grounded on the face at the source mouth trajectory.
o=find('smile.');vs=[];fs=[];N=28;M=8
for i in range(N+1):
 t=i/N;x=-.044+.088*t;z=.523+.028*(2*t-1)**2
 for j in range(M):
  a=2*math.pi*j/M;vs.append((x,.0-.255+.004*math.cos(a),z+.004*math.sin(a)))
for i in range(N):
 for j in range(M):fs.append((i*M+j,i*M+(j+1)%M,(i+1)*M+(j+1)%M,(i+1)*M+j))
me=bpy.data.meshes.new('Ellis curved smile');me.from_pydata(vs,[],fs);me.materials.append(mats['eye']);o.data=me;(o.vertex_groups.get('head') or o.vertex_groups.new(name='head')).add(list(range(len(vs))),1,'REPLACE')
for p in me.polygons:p.use_smooth=True
# Constructed soft polo collar: pointed folded leaves and a subtle placket/buttons.
for sign in [-1,1]:
 o=find('collar_'+str(sign));bpy.data.objects.remove(o,do_unlink=True)
 points=[(sign*.010,-.149,.389),(sign*.065,-.151,.416),(sign*.119,-.165,.361),(sign*.058,-.181,.330)]
 vertices=points+[(x,y+.012,z) for x,y,z in points]
 o=new_mesh('polo_collar_'+str(sign),vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mats['collar'],'spine');bevel(o,.008)
def box(name,c,d,mat,bone,width):
 x,y,z=c;a,b,e=[v/2 for v in d];vs=[(x+i*a,y+j*b,z+k*e) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]];fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 o=new_mesh(name,vs,fs,mat,bone);bevel(o,width);return o
box('polo_placket',(0,-.167,.305),(.046,.014,.112),mats['seam'],'spine',.006)
for z in [.323,.285]:
 v,f=sphere_mesh((0,-.179,z),(.008,.005,.008),24,12);new_mesh('polo_button_'+str(z),v,f,mats['blue'],'spine')
bevel(find('tailored_tunic'),.017)
oldhem=find('shirt_hem');bpy.data.objects.remove(oldhem,do_unlink=True)
box('soft_full_shirt_hem',(0,-.006,.158),(.357,.302,.027),mats['blue'],'pelvis',.013)
bevel(find('pelvis.'),.024)
for o in [find('arm_L'),find('arm_R'),find('leg_L'),find('leg_R')]:
 s=o.modifiers.new('Soft continuous limb surfaces','SUBSURF');s.levels=2;s.render_levels=2;o.modifiers.move(len(o.modifiers)-1,0)
# Distinct compact shoes with top volume, sole plane preserved at exact source ground.
for side in ['L','R']:
 o=find('minimal_foot_'+side);bevel(o,.018)
 for i in range(len(o.data.materials)):o.data.materials[i]=mats['shoe']
 x=(-1 if side=='L' else 1)*.115
 box('shoe_upper_'+side,(x,-.022,.050),(.142,.166,.071),mats['shoe'],'foot_'+side,.028)
 box('shoe_sole_'+side,(x,-.020,.010),(.148,.170,.020),mats['navy'],'foot_'+side,.007)
# Exact approved 2D food pixels, full UV/aspect, frozen semantic support map.
foodId='dish-cucumber' if MODE=='main' else 'dish-salmon'
mapping=json.loads((OBJ/'reviews/proposed-food-mappings.json').read_text())[foodId]
me=food.data.copy();food.data=me
for v,co in zip(me.vertices,mapping['proposedVerticesPlaneLocal']):v.co=co
for uv,co in zip(me.uv_layers.active.data,mapping['proposedFullUV']):uv.uv=co
img=bpy.data.images.load(str(HERE/'resources'/f'{foodId}.png'),check_existing=False);img.pack()
food.visible_shadow=False
for mat in me.materials:
 mat.surface_render_method='BLENDED';mat.use_transparency_overlap=False
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE':n.image=img;n.interpolation='Linear';n.extension='CLIP'
food['semantic_food_map']='alpha>=128 source occupied width and actual lowest rim row support';food['canonical_sha256']=mapping['canonicalTexture']['sha256'];food['depth_policy']='fixed source .6 camera ray, unchanged across all states and directions'
# Broad balanced world light. No preferred horizontal light direction and no ground.
for o in list(sc.objects):
 if o.type=='LIGHT':o.hide_render=True
def area(name,loc,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.65))-o.location).to_track_quat('-Z','Y').to_euler()
area('Ellis broad overhead',(0,0,4.5),170,4.2)
for i in range(4):
 a=i*math.pi/2;area('Ellis equal fill '+str(i),(3*math.cos(a),3*math.sin(a),2.2),95,4)
sc.world=sc.world.copy();sc.world.use_nodes=True
for n in sc.world.node_tree.nodes:
 if n.type=='BACKGROUND':n.inputs['Color'].default_value=(1,1,1,1);n.inputs['Strength'].default_value=0
sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=32
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15;sc.render.fps=12;sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.use_nodes=False
sc.render.use_persistent_data=True
# Remove unrelated scene/collections only in this isolated process. Preserve all source action owners.
keep=set(coll.all_objects)|{sc.camera}|{o for o in sc.objects if o.type=='LIGHT' and not o.hide_render}
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
 if s!=sc:bpy.data.scenes.remove(s)
for c in list(bpy.data.collections):
 if c!=coll and c not in list(coll.children_recursive) and not c.objects and not c.children:bpy.data.collections.remove(c)
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:
  try:image.pack()
  except Exception:pass
native.apply_clip(asset,RECORD,next(iter(RECORD['clips'])),1,'S',sc)
sc['refinement']='Ellis round01 warm softly lit cartoon native reconstruction';sc['captureScale']=2
path=HERE/('round-01.blend' if MODE=='main' else 'round-01-runtime.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
out=OBJ/'candidates/round-01/study';out.mkdir(parents=True,exist_ok=True)
for clip in (['stand','seated_wait','eat'] if MODE=='main' else ['eat-salmon','seated-wait-empty']):
 for direction in ['S','E','N','W']:
  native.apply_clip(asset,RECORD,clip,5,direction,sc);sc.render.filepath=str(out/(clip+'-'+direction+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
print('ELLIS_BUILD_COMPLETE',MODE,path,flush=True)
