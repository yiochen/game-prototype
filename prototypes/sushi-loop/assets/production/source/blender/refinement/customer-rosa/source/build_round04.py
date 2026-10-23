import bpy,math,json,pathlib,sys,hashlib,shutil,importlib.util
from mathutils import Vector
HERE=pathlib.Path(__file__).resolve().parent;OBJ=HERE.parent
runtime='--runtime' in sys.argv
brief=json.loads((OBJ/'brief.json').read_text());mappings=json.loads((OBJ/'reviews/semantic-food-mapping.json').read_text())
rigpath=OBJ/('inputs/runtime-variants/export/source/customer-rosa/rig.json' if runtime else 'inputs/source-rig.json');rig=json.loads(rigpath.read_text())
sc=next(s for s in bpy.data.scenes if s.get('meal_variants')) if runtime else next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));arm=next(o for o in col.all_objects if o.type=='ARMATURE')
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
col.hide_viewport=False;col.hide_render=False;arm.hide_viewport=False;arm.hide_set(False)
# Isolate this native actor and the fixed capture camera. No foreign body/rig resources.
for c in list(sc.collection.children):
 if c!=col:sc.collection.children.unlink(c)
for s in list(bpy.data.scenes):
 if s!=sc:bpy.data.scenes.remove(s)
owned=set(col.all_objects)|set(sc.collection.objects)
for o in list(bpy.data.objects):
 if o not in owned:bpy.data.objects.remove(o,do_unlink=True)
prefix='Rosa refined runtime' if runtime else 'Rosa refined'
def lin(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def mat(name,hex,rough=.58,coat=.0):
 m=bpy.data.materials.new(prefix+' '+name);m.diffuse_color=tuple(lin(int(hex[i:i+2],16)/255) for i in [0,2,4])+(1,);m.use_nodes=True
 n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.28;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.25;m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);return m
skin=mat('warm tan skin','EEAE68',.56,.04);hair=mat('chocolate bob','5B2C17',.45,.12);hairlight=mat('swept chocolate lock','673620',.47,.10);coral=mat('coral polo','E85343',.66);coraltrim=mat('polo fold and cuff','D94638',.64);navy=mat('navy trousers','24385F',.68);shoe=mat('dark cocoa shoes','342A26',.42,.13);eye=mat('warm dark eyes','23120B',.25,.22);white=mat('eye glints','FFF9E9',.25);blush=mat('soft coral cheeks','E9846C',.7)
def bind(o,bone):
 o.parent=root;o.matrix_parent_inverse.identity();o.location=(0,0,0);g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Original Rosa rig binding','ARMATURE');mod.object=arm;return o
def mesh(name,verts,faces,material,bone='head',bevel=0):
 me=bpy.data.meshes.new(prefix+' '+name+' mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(prefix+' '+name,me);col.objects.link(o);o.data.materials.append(material)
 for f in me.polygons:f.use_smooth=True
 if bevel:
  b=o.modifiers.new('Soft sewn rounded edge','BEVEL');b.width=bevel;b.segments=4
  b=o.modifiers.new('Broad surface normals','WEIGHTED_NORMAL');b.keep_sharp=True
 return bind(o,bone)
def uvball(name,c,d,m,bone='head',rot=0):
 vs=[];fs=[];seg=48;rings=24
 for j in range(rings+1):
  v=math.pi*j/rings
  for i in range(seg):
   u=2*math.pi*i/seg;x=d[0]*.5*math.sin(v)*math.cos(u);y=d[1]*.5*math.sin(v)*math.sin(u);z=d[2]*.5*math.cos(v)
   x,z=x*math.cos(rot)+z*math.sin(rot),-x*math.sin(rot)+z*math.cos(rot);vs.append((c[0]+x,c[1]+y,c[2]+z))
 for j in range(rings):
  for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
 return mesh(name,vs,fs,m,bone)
def box(name,c,d,m,bone,bevel=.015):
 vs=[(c[0]+x*d[0]/2,c[1]+y*d[1]/2,c[2]+z*d[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 return mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],m,bone,bevel)
def curve(name,points,r,m,bone='head'):
 cu=bpy.data.curves.new(prefix+' '+name,'CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=r;cu.bevel_resolution=4;s=cu.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(prefix+' '+name,cu);col.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.select_set(False);o.data.materials.append(m);return bind(o,bone)
# Keep source weighted limbs/palms; refine their native surface, replacing flat source material graphs.
kept=[]
for o in list(col.all_objects):
 if o.type!='MESH' or '__held_' in o.name or '__knife_' in o.name:continue
 token=o.name.split('customer_rosa__')[-1]
 if token.startswith(('arm_L','arm_R','leg_L','leg_R','palm_','thumb_')):
  kept.append(o)
  for i,m in enumerate(o.data.materials):o.data.materials[i]=navy if 'navy' in m.name else skin if 'skin' in m.name else coral
  for p in o.data.polygons:p.use_smooth=True
  for md in o.modifiers:
   if md.type=='BEVEL':md.segments=5
  if token.startswith(('arm_','leg_')):
   sub=o.modifiers.new('Soft weighted cloth and limb surface','SUBSURF');sub.subdivision_type='CATMULL_CLARK';sub.levels=2;sub.render_levels=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_move_up(modifier=sub.name)
 else:bpy.data.objects.remove(o,do_unlink=True)
# Soft face and coherent bob shell. All geometry uses original head weights and registered scale.
box('rounded face',(0,.002,.672),(.56,.47,.478),skin,'head',.083)
uvball('neck',(0,.005,.416),(.12,.12,.12),skin,'neck')
# continuous crown + side/back bob shell, variable front opening
vs=[];fs=[];seg=64
for j in range(13):
 p=(math.pi/2)*j/12
 for i in range(seg):
  a=2*math.pi*i/seg;vs.append((.318*math.sin(p)*math.copysign(abs(math.sin(a))**(1-.35*math.sin(p)**4),math.sin(a)),.027-.298*math.sin(p)*math.copysign(abs(math.cos(a))**(1-.35*math.sin(p)**4),math.cos(a)),.820+.190*math.cos(p)))
for j in range(1,5):
 for i in range(seg):
  a=2*math.pi*i/seg;front=min(1,max(0,(math.cos(a)+.05)/.35));front=front*front*(3-2*front);bottom=.462+.345*front;t=j/4;rad=1-.035*t
  vs.append((.318*rad*math.copysign(abs(math.sin(a))**.65,math.sin(a)),.027-.298*rad*math.copysign(abs(math.cos(a))**.65,math.cos(a)),.820*(1-t)+bottom*t))
for j in range(16):
 for i in range(seg):a=j*seg+i;b=j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
# seal underside to interior; hair remains actual closed volume
base=len(vs);vs.append((0,.03,.62))
for i in range(seg):fs.append((16*seg+i,16*seg+(i+1)%seg,base))
mesh('continuous rounded bob',vs,fs,hair)
# Crown shell carries broad continuous silhouette; one flowing frontal lock.
uvball('front swept lock',(-.010,-.208,.920),(.552,.194,.146),hairlight,rot=.075)
for i,x in enumerate([-.224,-.112,0,.112,.224]):
 z=[.873,.863,.875,.861,.872][i];uvball('rounded fringe '+str(i),(x,-.235,z),(.171,.110,.170),hairlight if i in [0,2,4] else hair,rot=[-.14,-.07,.05,.10,.19][i])
# Broad bob relief at each side; no separate small bead construction.
for side in [-1,1]:
 # Continuous bob skirt wraps side/back; no isolated circular side bead.
 uvball('ear '+str(side),(side*.285,.012,.652),(.066,.105,.115),skin)
 uvball('eye '+str(side),(side*.103,-.242,.688),(.052,.030,.075),eye)
 uvball('glint '+str(side),(side*.103-.006,-.258,.703),(.013,.008,.017),white)
 uvball('cheek '+str(side),(side*.186,-.240,.592),(.086,.015,.040),blush)
uvball('rounded nose',(0,-.256,.624),(.071,.055,.053),skin)
curve('friendly curved smile',[(-.049,-.241,.559),(-.025,-.252,.542),(0,-.255,.538),(.025,-.252,.542),(.049,-.241,.559)],.008,eye)
# Continuous tailored polo volume using rounded rings, weighted gradually spine/pelvis.
vs=[];fs=[];n=40
for z,rx,ry in [(.145,.177,.143),(.16,.184,.148),(.235,.197,.144),(.322,.186,.128),(.38,.155,.112),(.396,.113,.087)]:
 for i in range(n):a=2*math.pi*i/n;vs.append((rx*math.sin(a),-.008+ry*math.cos(a),z))
for j in range(5):
 for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
fs.extend([tuple(range(n-1,-1,-1)),tuple(5*n+i for i in range(n))]);o=mesh('soft tailored polo',vs,fs,coral,'spine')
g=o.vertex_groups.get('spine');g.remove(list(range(len(vs))));g2=o.vertex_groups.new(name='pelvis')
for v in o.data.vertices:
 w=min(1,max(0,(v.co.z-.15)/.16));g.add([v.index],w,'REPLACE');g2.add([v.index],1-w,'REPLACE')
sub=o.modifiers.new('Continuous broad cloth volume','SUBSURF');sub.levels=2;sub.render_levels=2
# collar, placket and cuff construction, broad enough for logical sprite size
for s in [-1,1]:
 pts=[(s*.006,-.126,.389),(s*.108,-.113,.397),(s*.139,-.127,.344),(s*.062,-.161,.327)]
 vv=pts+[(x,y+.014,z) for x,y,z in pts];mesh('folded collar '+str(s),vv,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],coraltrim,'spine',.008)
box('polo placket',(0,-.154,.303),(.043,.014,.091),coraltrim,'spine',.009)
uvball('polo button',(0,-.166,.317),(.024,.011,.024),coral,'spine')
# curved hem band and trouser pelvis
box('trouser hip',(0,.006,.118),(.318,.23,.12),navy,'pelvis',.033)
for s in [-1,1]:
 box('distinct cocoa shoe '+str(s),(s*.115,-.026,.024),(.151,.186,.048),shoe,'foot_'+('L' if s<0 else 'R'),.021)
 # seam-sized cuff at source elbow; remains fixed to upper arm
 uvball('sleeve cuff '+str(s),(s*.233,.0,.255),(.116,.126,.050),coraltrim,'upper_arm_'+('L' if s<0 else 'R'),rot=s*.32)
# Exact canonical food bytes, one frozen semantic mapping, source camera-ray depth retained.
food='dish-salmon' if runtime else 'dish-cucumber';fm=next(m for m in mappings if m['food']==food);mp=next(t for t in fm['thresholds'] if t['alphaThreshold']==128)
plane=next(o for o in col.all_objects if '__held_' in o.name and o.type=='MESH');material=plane.data.materials[0].copy();material.name=prefix+' exact canonical '+food;plane.data.materials[0]=material
art=(OBJ/brief['foodDependencies'][food]['artwork']).resolve();img=bpy.data.images.load(str(art),check_existing=False);img.name=prefix+' canonical '+food;img.pack()
for n in material.node_tree.nodes:
 if n.type=='TEX_IMAGE':n.image=img;n.interpolation='Linear';n.extension='CLIP'
w,h=mp['proposedFullUVQuadWorld'];x=mp['proposedFullUVCenterOffsetXWorld'];bottom=mp['proposedFullUVBottomOffsetWorld'];scale=root.scale.x
coords=[((x-w/2)/scale,bottom/scale,0),((x+w/2)/scale,bottom/scale,0),((x+w/2)/scale,(bottom+h)/scale,0),((x-w/2)/scale,(bottom+h)/scale,0)]
for v,co in zip(plane.data.vertices,coords):v.co=co
for d,uv in zip(plane.data.uv_layers.active.data,[(0,0),(1,0),(1,1),(0,1)]):d.uv=uv
plane['source_sha256']=brief['foodDependencies'][food]['sha256'];plane['source_image']=str(art);plane['semantic_mapping_alpha']=128;plane['world_width_cells']=w;plane['representation']='exact approved canonical packed 2D raster, not modeled 3D food'
# broad symmetric native illumination, independent of actor facing
for o in list(sc.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
sc.world=bpy.data.worlds.new(prefix+' warm soft world');sc.world.use_nodes=True;bg=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.72,.69,.64,1);bg.inputs['Strength'].default_value=.25
for i,(p,e,size) in enumerate([((0,0,4.5),180,4),((3,0,2.5),60,4),((-3,0,2.5),60,4),((0,3,2.5),60,4),((0,-3,2.5),60,4)]):
 l=bpy.data.lights.new(prefix+' symmetric area '+str(i),'AREA');l.energy=e;l.shape='DISK';l.size=size;o=bpy.data.objects.new(l.name,l);sc.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=20;sc.render.fps=12;sc.render.dither_intensity=0;sc.render.use_compositing=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.threads_mode='FIXED';sc.render.threads=6
cam=sc.camera;cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.458331435918808;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1
# retain the actual native rig, actions, rest bones and grounded root
res=HERE/'resources';res.mkdir(exist_ok=True)
for f in ['native_actions.py']:
 src=OBJ/'../../../production/source/blender'/f;shutil.copyfile(src.resolve(),res/f)
spec=importlib.util.spec_from_file_location('rosa_native',res/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset={'root':root,'collection':col,'armature':arm};clip='eat-salmon' if runtime else 'stand';native.apply_clip(asset,rig,clip,1,'S',sc)
# Remove unused old mesh/material/image datablocks; all native action cohorts remain.
for me in list(bpy.data.meshes):
 if me.users==0:bpy.data.meshes.remove(me)
for ma in list(bpy.data.materials):
 if ma.users==0:bpy.data.materials.remove(ma)
# Remove stale orphaned images and other unreferenced external dependencies.
for im in list(bpy.data.images):
 if im!=img and im.users==0:bpy.data.images.remove(im)
sc['rosa_refinement_round']='04';sc['frozen_brief_sha256']=hashlib.sha256((OBJ/'brief.json').read_bytes()).hexdigest();sc['food_display_depth']='original one constant .6 world cell; semantic corrected canonical quad'
path=HERE/('round-04-runtime.blend' if runtime else 'round-04.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
OUT=OBJ/'candidates/round-04'/'draft';OUT.mkdir(parents=True,exist_ok=True)
for d in ['S','E','N','W']:
 native.apply_clip(asset,rig,clip,1,d,sc);sc.render.filepath=str(OUT/(('runtime-eat' if runtime else 'stand')+'-'+d+'.png'));bpy.ops.render.render(write_still=True)
(HERE/('build-runtime-round04.json' if runtime else 'build-main-round04.json')).write_text(json.dumps({'project':path.name,'frozenBrief':sc['frozen_brief_sha256'],'food':food,'foodPackedSHA256':hashlib.sha256(img.packed_file.data).hexdigest(),'mapping':mp,'sourceDepthConstant':.6,'objects':len(col.all_objects),'recipe':__file__,'blender':bpy.app.version_string},indent=2)+'\n')
