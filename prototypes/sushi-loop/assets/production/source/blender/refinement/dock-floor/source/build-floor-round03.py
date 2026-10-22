"""Native dock-floor reconstruction. Run: blender -b --python source/build-floor.py [-- --render]."""
import bpy,math,json,hashlib,sys,shutil
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np
HERE=Path(__file__).resolve().parent; OBJ=HERE.parent; RES=HERE/'resources'; OUT=OBJ/'candidates/round-03'
for p in [RES,OUT/'frames',OUT/'atlases',OUT/'native-records']:p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# The fixed source/target are provenance, never a render plane or texture.
original=OBJ.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend'
if not (RES/'original-library.blend').exists():shutil.copyfile(original,RES/'original-library.blend')
for name in ['source-camera.json','source-assetRecord.json','source-rig.json','shared-dock-entry-contract.json']:
 if not (RES/name).exists():shutil.copyfile(OBJ/'inputs'/name,RES/name)
if not (RES/'frozen-brief.json').exists():shutil.copyfile(OBJ/'brief.json',RES/'frozen-brief.json')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='DockFloor_Standalone_WarmSoft'
col=bpy.data.collections.new('WarmSoft_dock-floor');sc.collection.children.link(col)
root=bpy.data.objects.new('dock-floor__root',None);col.objects.link(root)
# Procedural source texture: long native UV grain with sparse stretched knots.
W,H=1024,2048
u,v=np.meshgrid((np.arange(W)+.5)/W,(np.arange(H)+.5)/H)
local=(u*12)%1;idx=np.minimum((u*12).astype(int),11)
phase=local*math.pi*11 + .9*np.sin(v*9+idx*1.31)+.3*np.sin(v*24+idx*.78)
lines=np.maximum(np.cos(phase),0)**12
fine=np.sin(local*93+np.sin(v*5+idx)*2)*.009
field=1-.09*lines+.027*np.sin(local*14+v*3+idx)+fine
for i in range(12):
 cy=[.28,.76,.46,.6,.34,.83,.18,.55,.7,.27,.48,.8][i]
 dx=(local-(.4 if i%2 else .59))/.35;dy=(v-cy)/.085
 r=np.sqrt(dx*dx+dy*dy)
 knot=(idx==i)*np.maximum(0,1-r/1.4)
 field-=knot*(.06+.11*np.maximum(np.cos(r*15),0)**8)
field=np.clip(field,.66,1.06).astype(np.float32)
pix=np.empty((H,W,4),dtype=np.float32);pix[:,:,:3]=field[:,:,None];pix[:,:,3]=1
im=bpy.data.images.new('Native_Long_Grain_Knots',W,H,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(pix.ravel());im.filepath_raw=str(RES/'wood-grain.png');im.file_format='PNG';im.save();im.pack()
def mat(name,color,grain=False,metallic=0,rough=.65):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic;p.inputs['Specular IOR Level'].default_value=.27 if not metallic else .5
 if grain:
  tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='EXTEND';uv=n.new('ShaderNodeTexCoord');l.new(uv.outputs['UV'],tex.inputs['Vector']);mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[1].default_value=(*color,1);l.new(tex.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],p.inputs['Base Color'])
 return m
palette=[(.68,.345,.094),(.52,.228,.055),(.58,.272,.068),(.69,.365,.11),(.56,.252,.06),(.59,.27,.063),(.70,.375,.105),(.54,.24,.055),(.60,.29,.075),(.68,.35,.095),(.55,.245,.059),(.62,.30,.079)]
mats=[mat('Honey timber %02d'%i,c,True) for i,c in enumerate(palette)]
side=mat('Warm underside timber',(.30,.12,.035),True,rough=.8)
metal=mat('Charcoal forged fixing',(.115,.14,.155),metallic=.4,rough=.36)
def move_to_col(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root
 return o
def cube(name,loc,scale,material,bev=.0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);move_to_col(o);o.data.materials.append(material)
 # UV is actual dock-local XY and is retained when boards are joined.
 uv=o.data.uv_layers.active or o.data.uv_layers.new()
 for poly in o.data.polygons:
  for li in poly.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=((p.x+1.5)/3,(p.y+1.5)/3)
 if material.name.startswith('Honey timber'):
  c=material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3]
  darker=mat(material.name+' amber end',tuple(t*.54 for t in c),True,rough=.75);lighter=mat(material.name+' rolled rim',tuple(min(t*1.18,1) for t in c),True,rough=.55)
  o.data.materials.append(darker);o.data.materials.append(lighter)
  for p in o.data.polygons:p.material_index=0 if abs(p.normal.z)>.5 else 1
 if bev:
  b=o.modifiers.new('Rounded timber edges','BEVEL');b.width=bev;b.segments=5;b.affect='EDGES';b.profile=.5
  if material.name.startswith('Honey timber'):b.material=2
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 for p in o.data.polygons:p.use_smooth=True
 n=o.modifiers.new('Weighted broad face normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=n.name)
 return o
boards=[]
for i in range(12):
 boards.append(cube('dock-floor__crafted_plank_%02d'%i,(-1.375+.25*i,0,.13),(.244,3,.18),mats[i],.024))
# Joining boards retains UVs and material assignments; exact boolean union creates
# a single bounded native support tongue, with no coplanar duplicate or alpha patch.
bpy.ops.object.select_all(action='DESELECT')
for o in boards:o.select_set(True)
bpy.context.view_layer.objects.active=boards[0];bpy.ops.object.join();deck=bpy.context.object;deck.name='dock-floor__crafted_deck'
band=cube('temporary_exact_transfer_union',(0,-1.49,.13),(1,.02,.18),mats[5],0)
bpy.context.view_layer.objects.active=deck
mod=deck.modifiers.new('Bounded exact contact closure','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=band
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(band,do_unlink=True)
# Recomputed custom normals keep top flat; bevel polygons smooth, plane faces flat.
for poly in deck.data.polygons:poly.use_smooth=abs(poly.normal.z)<.999 and abs(poly.normal.x)<.999 and abs(poly.normal.y)<.999
for x in [-1.17,1.17]:cube('dock-floor__low_joist_'+str(x),(x,0,.035),(.18,3,.07),side,.014)
for x in [-1.375,-.375,.625,1.375]:
 for y in [-1.28,1.28]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=(x,y,.223));o=bpy.context.object;o.name='dock-floor__domed_fixing';o.scale=(.027,.027,.009);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);move_to_col(o);o.data.materials.append(metal)
  for p in o.data.polygons:p.use_smooth=True
# Registered camera, exact source matrix and uniform 2x consumer capture.
camdata=bpy.data.cameras.new('Registered_camera');cam=bpy.data.objects.new('Registered_camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
cm=json.loads((RES/'source-camera.json').read_text());cam.matrix_world=Matrix(cm['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL'
sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15;sc.render.threads_mode='FIXED';sc.render.threads=6
sc.render.fps=12;sc.frame_start=1;sc.frame_end=1
sc.world=bpy.data.worlds.new('Neutral fill world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.83,.87,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-1.8;sc.view_settings.gamma=1
# Horizontal symmetry, common overhead and four equal broad fills, no ground.
def area(name,loc,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Soft centered overhead',(0,0,4.5),360,4)
for p in [(3,0,2.5),(-3,0,2.5),(0,3,2.5),(0,-3,2.5)]:area('Equal cardinal soft fill',p,180,4)
def config(frame=(448,480),anchor=(224,256)):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;camdata.ortho_scale=frame[0]/128;camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;camdata.shift_y=(anchor[1]*2-base.y)/dy;camdata.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'calibration':{'root':list(px((0,0,0))),'unitX':list(px((1,0,0))-px((0,0,0))),'unitDepth':list(px((0,-1,0))-px((0,0,0))),'unitHeight':list(px((0,0,1))-px((0,0,0)))}}
record=config();root.rotation_euler=(0,0,0);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-03.blend'),compress=True)
(OUT/'native-records/camera.json').write_text(json.dumps(record,indent=2))
asset=json.loads((RES/'source-assetRecord.json').read_text());asset['scale']=2;asset['groundRootObject']=root.name;asset['nativeProject']='source/round-03.blend';asset['artStyle']={'lighting':'soft centered overhead plus four equal cardinal fills','wood':'native packed procedural grain and sculpted rounded boards'};(OUT/'native-records/asset.json').write_text(json.dumps(asset,indent=2))
rig=json.loads((RES/'source-rig.json').read_text());rig['groundRootObject']=root.name;rig['status']='native-static-measured';(OUT/'native-records/rig.json').write_text(json.dumps(rig,indent=2))
if '--render' in sys.argv:
 phases=[]
 for d,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
  root.rotation_euler.z=ang;bpy.context.view_layer.update();p=OUT/'frames'/('static-'+d)/'000.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  shutil.copyfile(p,OUT/'atlases'/('static-'+d+'.png'));phases.append({'clip':'static','direction':d,'index':0,'path':str(p.relative_to(OBJ)),'sha256':sha(p),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'camera':config()})
 (OUT/'candidate-phases.json').write_text(json.dumps(phases,indent=2))
print('STANDALONE_SOURCE',str(HERE/'round-03.blend'),sha(HERE/'round-03.blend'),flush=True)
