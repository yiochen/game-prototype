"""Read-only native capture/filter experiments on immutable dock sources.
Run: blender -b -t6 --python source/alpha-filter-study.py [-- variant names].
No save, geometry, material, light, registration or source edits.
"""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/alpha-filter-study';O.mkdir(exist_ok=True);entry=B/'source/round-05.blend';floor=B/'inputs/paired-native/dock-floor-round-03.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before={str(p.relative_to(B)):sha(p) for p in [entry,floor]}
bpy.ops.wm.open_mainfile(filepath=str(entry));sc=bpy.context.scene;cam=sc.camera;ec=bpy.data.collections['S33_PROP_dock-entry'];er=bpy.data.objects['dock-entry__root']
with bpy.data.libraries.load(str(floor),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);fr=bpy.data.objects['dock-floor__root']
base={'engine':sc.render.engine,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples,'taa_samples':sc.eevee.taa_samples,'use_taa_reprojection':sc.eevee.use_taa_reprojection,'anisotropic_filter':sc.render.anisotropic_filter,'view_transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'pixel_aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
variants={'eevee-filter-1p5':{'filter_size':1.5},'eevee-filter-0':{'filter_size':0},'eevee-filter-0p01':{'filter_size':.01},'eevee-filter-0p5':{'filter_size':.5},'eevee-filter-0-samples256':{'filter_size':0,'taa_render_samples':256},'eevee-filter-0-samples1':{'filter_size':0,'taa_render_samples':1},'eevee-filter-0-reprojection-off':{'filter_size':0,'use_taa_reprojection':False}}
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['eevee-filter-1p5','eevee-filter-0','eevee-filter-0p01','eevee-filter-0p5']
records=[]
def setup(frame,anchor):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
 p=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-p.y;cam.data.shift_y=(anchor[1]-p.y)/dy;bpy.context.view_layer.update();p=px((0,0,0))
 return {'frameLogical':frame,'anchorLogical':list(p),'sourceScale':2,'calibration':{'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p)},'cameraWorld':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
for name in args:
 config=variants[name]
 # Reset every varied setting so each test has an actual controlled baseline.
 sc.render.engine=base['engine'];sc.render.filter_size=base['filter_size'];sc.eevee.taa_render_samples=base['taa_render_samples'];sc.eevee.use_taa_reprojection=base['use_taa_reprojection']
 for k,v in config.items():
  if k=='filter_size':sc.render.filter_size=v
  elif k=='taa_render_samples':sc.eevee.taa_render_samples=v
  elif k=='use_taa_reprojection':sc.eevee.use_taa_reprojection=v
 settings={'engine':sc.render.engine,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples,'use_taa_reprojection':sc.eevee.use_taa_reprojection};dest=O/name;dest.mkdir(exist_ok=True)
 for d,a in [('E',math.pi/2),('W',-math.pi/2)]:
  for kind in ['entry','floor','pair']:
   er.rotation_euler.z=a;fr.rotation_euler.z=a;er.location=(0,0,0);fr.location=(0,0,0);ec.hide_render=kind=='floor';fc.hide_render=kind=='entry'
   frame,anchor=([192,352],[96,248]) if kind=='entry' else ([448,480],[224,256]) if kind=='floor' else ([576,640],[288,352])
   if kind=='pair':er.location=Matrix.Rotation(a,4,'Z')@Vector((0,-1.5,0))
   cal=setup(frame,anchor);p=dest/f'{kind}-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'variant':name,'kind':kind,'direction':d,'path':str(p.relative_to(B)),'sha256':sha(p),'settings':settings,'calibration':cal,'entryRootMatrix':[list(r) for r in er.matrix_world],'floorRootMatrix':[list(r) for r in fr.matrix_world]})
 data={'sourceHashesBefore':before,'sourceHashesAfter':{str(p.relative_to(B)):sha(p) for p in [entry,floor]},'sourceUnchanged':before=={str(p.relative_to(B)):sha(p) for p in [entry,floor]},'baseline':base,'variant':name,'settings':settings,'records':[r for r in records if r['variant']==name],'notes':'RNA setting values recorded after assignment. Whether EEVEE honors each setting must be inferred only from actual rendered RGBA comparison. Same whole-frame cameras and lights; no native source saved.'};(dest/'native-records.json').write_text(json.dumps(data,indent=2))
(O/'latest-native-study.json').write_text(json.dumps({'baseline':base,'variants':args,'records':records,'sourceUnchanged':before=={str(p.relative_to(B)):sha(p) for p in [entry,floor]}},indent=2));print('FILTER_STUDY_READY',args)
