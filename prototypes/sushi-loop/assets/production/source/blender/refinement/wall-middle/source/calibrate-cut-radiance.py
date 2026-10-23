"""Native linear radiance calibration for exact cut planes; no geometry or pixel edits."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];C=B/'candidates/round-05';bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-05.blend'));s=bpy.context.scene;cam=s.camera;c=bpy.data.collections['S33_PROP_wall-middle.001'];r=next(o for o in c.all_objects if o.type=='EMPTY');r.rotation_euler.z=math.pi/2;bpy.context.view_layer.update()
for offset in [-1,1]:
 for o in list(c.all_objects):
  if o.type!='MESH':continue
  d=o.copy();d.data=o.data;d.parent=None;d.matrix_world=o.matrix_world.copy();d.location+=Vector((0,offset,0));s.collection.objects.link(d)
s.render.resolution_x=896;s.render.resolution_y=1216;cam.data.ortho_scale=896/256;cam.data.shift_y=0;bpy.context.view_layer.update()
def pixel(v):
 p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*896,(1-p.y)*1216))
base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-base.y;cam.data.shift_y=(768-base.y)/dy;bpy.context.view_layer.update()
s.cycles.samples=2048;s.cycles.use_denoising=False;s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='32';s.render.filepath=str(C/'native-cut-linear.exr');bpy.ops.render.render(write_still=True)
im=bpy.data.images.load(str(C/'native-cut-linear.exr'));px=list(im.pixels);samples=[]
for xx in range(404,492):
 y=(448-(xx+.5))/256
 z=1.01 if abs(y)<=.12 else .97+(.18-abs(y))*2/3
 colors=[]
 for longitudinal in[-.5,.5]:
  p=pixel((-y,longitudinal,z))
  for delta in[-2,-1,0,1,2]:
   yy=int(round(p.y-.5))+delta;i=((1215-yy)*896+xx)*4;colors.append(px[i:i+3])
 rgb=[sum(a[k]for a in colors)/len(colors)for k in range(3)];samples.append({'localY':y,'normalizedY':y/.18,'surfaceZ':z,'linearRGB':rgb})
(C/'cut-radiance-samples.json').write_text(json.dumps({'method':'2048-sample native joined render, BOX1, unmodified scene-linear EXR; 88 horizontal samples averaged over both source join planes and five neighboring rows. One common symmetric field across facings.','samples':samples},indent=2))
print('CALIBRATED',len(samples))
