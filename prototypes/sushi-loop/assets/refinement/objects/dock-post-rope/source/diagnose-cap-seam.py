import bpy,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent.parent;O=P/'candidates/cap-seam-diagnostics';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-06.blend'));s=bpy.context.scene;root=bpy.data.objects['dock-post-rope__root.001'];cam=s.camera;col=next(c for c in bpy.data.collections if c.name.startswith('S33_PROP_dock-post-rope'))
parts=[o for o in col.all_objects if o.type=='MESH'];prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=512
s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32'
root.rotation_euler.z=math.pi/2;bpy.context.view_layer.update();s.render.filepath=str(O/'single-E.exr');bpy.ops.render.render(write_still=True)
root.rotation_euler.z=0;bpy.context.view_layer.update()
assembly=bpy.data.collections.new('Diagnostic assembly');s.collection.children.link(assembly);ar=bpy.data.objects.new('Diagnostic assembly root',None);assembly.objects.link(ar)
for offset in [-1,0,1]:
 nr=root.copy();assembly.objects.link(nr);nr.parent=ar;nr.location=(offset,0,0);nr.rotation_euler=(0,0,0)
 for o in parts:
  no=o.copy();no.data=o.data;assembly.objects.link(no);no.parent=nr;no.matrix_parent_inverse=o.matrix_parent_inverse.copy()
col.hide_render=True;s.render.resolution_x=1152;s.render.resolution_y=1216;cam.data.ortho_scale=4.5
from bpy_extras.object_utils import world_to_camera_view
cam.data.shift_y=0;bpy.context.view_layer.update();base=(1-world_to_camera_view(s,cam,Vector((0,0,0))).y)*1216
cam.data.shift_y=1;bpy.context.view_layer.update();one=(1-world_to_camera_view(s,cam,Vector((0,0,0))).y)*1216
cam.data.shift_y=(752-base)/(one-base);ar.rotation_euler.z=math.pi/2;bpy.context.view_layer.update();s.render.filepath=str(O/'native-E.exr');bpy.ops.render.render(write_still=True)
# Save linear samples at every first-cap seam row for native and the two pieces.
ims={n:bpy.data.images.load(str(O/f'{n}-E.exr'),check_existing=False) for n in ['single','native']};pix={n:list(i.pixels) for n,i in ims.items()}
def rgb(n,x,y):
 w,h=ims[n].size;i=((h-1-y)*w+x)*4;return pix[n][i:i+4]
samples=[]
for y in range(480,489):
 for x in range(541,611):
  # source root offsets (x=384,y=0) and (x=384,y=256), both straddling cap at 484.
  far=rgb('single',x-384,y);near=rgb('single',x-384,y-256)
  # near rendered last, standard non-premultiplied alpha over.
  a=near[3]+far[3]*(1-near[3]);comp=[(near[k]*near[3]+far[k]*far[3]*(1-near[3]))/a if a else 0 for k in range(3)]+[a]
  samples.append({'x':x,'y':y,'singleFar':far,'singleNear':near,'independentLinear':comp,'nativeLinear':rgb('native',x,y)})
(O/'linear-samples.json').write_text(json.dumps(samples,indent=2))
print('LINEAR_DIAG_COMPLETE')
