"""Portable native cover rebuild. Blender 5.2.2 LTS; no source/companion mutation."""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/preliminary-v2';OUT.mkdir(parents=True,exist_ok=True)
TAU=math.tau
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='WarmSoft Dock Cover Preliminary v1';col=bpy.data.collections.new('WarmSoft_dock-cover');sc.collection.children.link(col)
def link(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 col.objects.link(ob);return ob
root=bpy.data.objects.new('dock-cover__root',None);col.objects.link(root)
root['socket_dock_floor']=[0.,0.,0.];root['footprint']=[3,3];root['nonblocking']=True;root['depth_layer']='overhead'
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(n,h,rough=.5,spec=.25):
 m=bpy.data.materials.new(n);m.diffuse_color=tuple(linear(int(h[i:i+2],16)/255)for i in(0,2,4))+(1,);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec;return m
mats=[mat('Canvas warm golden saffron','E8BE58',.65,.22),mat('Canvas warm pale butter','F0D582',.65,.22),mat('Canvas cream','EFE2BE',.7,.2),mat('Canvas sea turquoise','51B4AE',.62,.24),mat('Warm rounded timber','A96A30',.48,.3),mat('Honey endgrain','D6A253',.48,.3),mat('Woven edge binding','B49768',.72,.2),mat('Stitch ivory','E5D4A5',.8,.1)]
def mesh(n,v,f,mi=0,smooth=True):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.materials.append(mats[mi]);me.update();ob=bpy.data.objects.new(n,me);col.objects.link(ob);ob.parent=root
 for p in me.polygons:p.use_smooth=smooth
 return ob
def tube(n,path,r,mi=4,sides=12):
 v=[];f=[]
 for k,p in enumerate(path):
  tan=Vector(path[min(k+1,len(path)-1)])-Vector(path[max(k-1,0)]);tan.normalize();ref=Vector((0,0,1)) if abs(tan.z)<.9 else Vector((1,0,0));a=tan.cross(ref).normalized();b=tan.cross(a).normalized()
  for j in range(sides):v.append(Vector(p)+r*(math.cos(TAU*j/sides)*a+math.sin(TAU*j/sides)*b))
 for k in range(len(path)-1):
  for j in range(sides):a=k*sides+j;b=k*sides+(j+1)%sides;f.append((a,b,b+sides,a+sides))
 f.extend([tuple(reversed(range(sides))),tuple((len(path)-1)*sides+j for j in range(sides))]);return mesh(n,v,f,mi)
def beam(n,a,b,r=.035,mi=4):return tube(n,[a,b],r,mi,20)
def box(n,loc,scale,mi=4,bevel=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=link(bpy.context.object);o.name=n;o.parent=root;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[mi]);b=o.modifiers.new('Crafted soft edges','BEVEL');b.width=bevel;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 no=o.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL');return o
# Four visibly connected uprights and flat finite bearing pads, without beveling the bottom contact.
for x in [-1.42,1.42]:
 for y in [-1.26,1.26]:
  tag=f'{x:+.2f}_{y:+.2f}'
  box('dock-cover__finite_deck_foot_'+tag,(x+math.copysign(.028,x),y,.015),(.086,.12,.05),4,0.008)
  # Dedicated finite bearing plate has exact planar underside at -.010, no bottom bevel.
  box('dock-cover__bearing_sole_'+tag,(x+math.copysign(.028,x),y,-.005),(.078,.108,.01),5,0)
  beam('dock-cover__timber_upright_'+tag,(x,y,.04),(x,y,2.005),.031,4)
  beam('dock-cover__foot_ferrule_'+tag,(x,y,.03),(x,y,.115),.043,5)
  beam('dock-cover__top_ferrule_'+tag,(x,y,1.94),(x,y,2.055),.046,5)
# Continuous side carriers, rear spindle, split near-edge frame preserves a useful peek/entry.
for x in [-1.42,1.42]:beam('dock-cover__side_carrier_'+str(x),(x,-1.26,2.005),(x,1.26,2.005),.031,4)
beam('dock-cover__rear_spindle',(-1.42,1.26,2.032),(1.42,1.26,2.032),.043,4)
for a,b in [(-1.42,-.345),(.345,1.42)]:beam('dock-cover__split_front_carrier_'+str(a),(a,-1.26,2.005),(b,-1.26,2.005),.034,4)
for x in [-1.42,1.42]:
 for y in [-1.26,1.26]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.052,location=(x,y,2.035));o=link(bpy.context.object);o.name='dock-cover__rounded_joint';o.parent=root;o.data.materials.append(mats[5]);
  for p in o.data.polygons:p.use_smooth=True
# Finite thickness cloth and all sewn attachments are one native deformation owner.
def roof(x,y):return 1.975+.153*math.cos(y*math.pi/2.52)-.025*math.sin(math.pi*(x+1.38)/2.76)**2
moving=[];xs=[-1.38+i*.345 for i in range(9)];ys=[-1.26,-.63,0,.63,1.26]
colors=[[0,0,2,3],[3,0,0,2],[0,2,3,0],[3,0,0,2]]
for ix in range(8):
 for iy in range(4):
  if ix in [3,4] and iy==0:continue
  nx,ny=4,9;vs=[];faces=[]
  for side in [0,1]:
   for j in range(ny+1):
    y=ys[iy]+(ys[iy+1]-ys[iy])*j/ny
    for i in range(nx+1):
     x=xs[ix]+(xs[ix+1]-xs[ix])*i/nx;z=roof(x,y)-.018*math.sin(math.pi*i/nx)*math.sin(math.pi*j/ny)-side*.018;vs.append((x,y,z))
  off=(nx+1)*(ny+1)
  for j in range(ny):
   for i in range(nx):
    a=j*(nx+1)+i;faces.extend([(a,a+1,a+nx+2,a+nx+1),(off+a+nx+1,off+a+nx+2,off+a+1,off+a)])
  perimeter=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1)for j in range(ny-1,0,-1)]
  for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):faces.append((a,b,b+off,a+off))
  moving.append(mesh(f'dock-cover__curved_canvas_{ix}_{iy}',vs,faces,colors[iy][ix//2]))
# Sewn bindings follow all cloth outer/interior panel seams and notch. Repeated strips are actual tubes.
for x in [-1.38,-.69,0,.69,1.38]:
 start=-.63 if x==0 else -1.26
 path=[(x,start+(1.26-start)*i/48,roof(x,start+(1.26-start)*i/48)+.004)for i in range(49)];moving.append(tube('dock-cover__long_sewn_binding',path,.008,6,8))
for y in ys:
 sections=[(-1.38,-.345),(.345,1.38)]if y==-1.26 else[(-1.38,1.38)]
 for a,b in sections:
  path=[(a+(b-a)*i/40,y,roof(a+(b-a)*i/40,y)+.004)for i in range(41)];moving.append(tube('dock-cover__rounded_hem',path,.012 if abs(y)>1.2 else .007,6,10))
for x in [-.345,.345]:
 moving.append(tube('dock-cover__peek_bound_edge',[(x,-1.26+.63*i/16,roof(x,-1.26+.63*i/16)+.004)for i in range(17)],.01,6,10))
# Restrained real stitches across selected seams.
for x in [-.69,.69]:
 for j in range(25):
  y=-1.20+j*.096
  moving.append(tube('dock-cover__ivory_stitch',[(x-.022,y,roof(x-.022,y)+.013),(x-.022,y+.038,roof(x-.022,y+.038)+.013)],.0028,7,6))
bpy.ops.object.select_all(action='DESELECT')
for o in moving:o.select_set(True)
bpy.context.view_layer.objects.active=moving[0];bpy.ops.object.join();cloth=bpy.context.object;cloth.name='dock-cover__attached_canvas_hems_and_stitches';
for v in cloth.data.vertices:v.co.x*=1.008
base=[v.co.copy()for v in cloth.data.vertices];cloth.shape_key_add(name='Basis')
keys={}
for clip,count in [('covered',13),('uncover',12)]:
 keys[clip]=[]
 for index in range(count):
  key=cloth.shape_key_add(name=f'{clip}_{index+1:02d}');keys[clip].append(key)
  t=index/12 if clip=='covered'else index/11;u=0 if clip=='covered'else t*t*(3-2*t)
  for k,v in enumerate(base):
   x,y,z=v;v01=(y+1.26)/2.52
   flutter=.004*math.sin(TAU*t+1.3*x)*math.sin(math.pi*v01)**2 if clip=='covered'else 0
   key.data[k].co=(x,y*(1-.89*u)+1.2614*u,z+flutter+u*(.015+.035*math.sin(8*math.pi*v01)))
  key.value=0
sk=cloth.data.shape_keys;acts={}
for clip,count in [('covered',13),('uncover',12)]:
 sk.animation_data_create();a=bpy.data.actions.new('dock-cover__'+clip+'__attached_native_fold');a.use_fake_user=True;sk.animation_data.action=a
 for f in range(1,count+1):
  for key in keys[clip]:key.value=1. if key==keys[clip][f-1]else 0.;key.keyframe_insert(data_path='value',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     fc.extrapolation='CONSTANT'
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 acts[clip]=a
for key in sk.key_blocks:key.value=0
sk.animation_data.action=acts['covered'];sc.frame_set(1)
# Exact fixed capture geometry, no per-facing fit.
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1472;sc.render.resolution_y=1408;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
cam=bpy.data.objects.new('DockCover fixed calibrated camera',bpy.data.cameras.new('DockCover fixed calibrated camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=5.75
el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*1472,(1-p.y)*1408))
b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(960-b.y)/dy;bpy.context.view_layer.update()
sc.render.film_transparent=True;sc.render.filter_size=.5;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=20;sc.render.fps=12;sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-1.1;sc.world=bpy.data.worlds.new('Symmetric soft neutral world');sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.18
for n,pos,power,size in [('overhead',(0,0,5),190,4.5)]+[(f'cardinal{i}',(3*math.cos(TAU*i/4),3*math.sin(TAU*i/4),2.5),100,4)for i in range(4)]:
 ob=bpy.data.objects.new('Soft symmetric '+n,bpy.data.lights.new('Soft symmetric '+n,'AREA'));sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.use_persistent_data=True
sc.frame_start=1;sc.frame_end=12
if hasattr(sc,'eevee') and hasattr(sc.eevee,'taa_render_samples'):sc.eevee.taa_render_samples=32
bpy.context.view_layer.update();p0=px((0,0,0));rec={'projection':'top-down-oblique-square-grid','frame':[736,704],'anchor':[368,480],'captureScale':2,'cellSize':128,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r)for r in cam.matrix_world],'projectionMatrix':[list(r)for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1472,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'elevationDegrees':math.degrees(el),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':list(p0),'unitX':list(px((1,0,0))-p0),'unitDepth':list(px((0,-1,0))-p0),'unitHeight':list(px((0,0,1))-p0)}}
(HERE/'camera.json').write_text(json.dumps(rec,indent=2)+'\n');(HERE/'rig.json').write_text(json.dumps({'groundRootObject':root.name,'shapeKeyOwner':cloth.name,'clips':{k:{'action':a.name,'frames':12,'fps':12,'loop':k=='covered','closureKey':13 if k=='covered'else None,'heldTerminalBeyond12':k=='uncover'}for k,a in acts.items()}},indent=2)+'\n')
(HERE/'assetRecord.json').write_text(json.dumps({'id':'dock-cover','frame':[736,704],'anchor':[368,480],'scale':2,'footprint':[3,3],'sockets':{'dock_floor':[0,0,0]},'nonblocking':True,'depth_layer':'overhead','composition_context':{'compositionOffset':[0,0,.23]},'provisional':True},indent=2)+'\n')
sc['native_recipe']='build_cover.py';sc['preliminary_only']=True
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'cover.blend'),compress=True)
sc.render.filepath=str(OUT/'first-S.png');bpy.ops.render.render(write_still=True)
print('SAVED STANDALONE',HERE/'cover.blend')
