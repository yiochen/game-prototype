import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;R=OUT/'resources';dest=OUT/'native-joins-replay';dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'canonical-middle.blend'));sc=bpy.context.scene
midcol=bpy.data.collections['rock-wall-middle__asset'];mroot=bpy.data.objects['rock-wall-middle__root'];mroot.rotation_euler.z=0
with bpy.data.libraries.load(str(R/'round-03.blend'),link=False) as (available,wanted):wanted.collections=['rock-wall-corner__asset']
ccol=wanted.collections[0];sc.collection.children.link(ccol);ccol.hide_render=False;ccol.hide_viewport=False
croot=bpy.data.objects['rock-wall-corner__root'];croot.rotation_euler.z=0
for obj in ccol.all_objects:obj.hide_render=False
aroot=bpy.data.objects.new('independent-candidate-corner-canonical-middle-assembly',None);sc.collection.objects.link(aroot)
mroot.parent=aroot;mroot.location=(-1,0,0);croot.parent=aroot
r2=mroot.copy();r2.name='independent-middle-N-root';midcol.objects.link(r2);r2.parent=aroot;r2.location=(0,1,0);r2.rotation_euler.z=math.pi/2
for ob in list(midcol.objects):
 if ob.type=='MESH' and ob.parent==mroot:
  du=ob.copy();midcol.objects.link(du);du.parent=r2
sc.render.resolution_x=1792;sc.render.resolution_y=2432;sc.camera.data.ortho_scale=3.5;sc.camera.data.shift_x=0
sc.render.threads_mode='FIXED';sc.render.threads=4
cam=sc.camera
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
for _ in range(2):
 bpy.context.view_layer.update();b=px((0,0,0));prev=cam.data.shift_y;cam.data.shift_y=prev+1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=prev+(1536-b[1])/dy
views={}
for d,deg in {'N':180,'E':90,'S':0,'W':-90}.items():
 aroot.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(dest/f'native-joined-{d}.png');bpy.ops.render.render(write_still=True)
 views[d]={'assemblyRotation':deg,'cornerMatrix':[list(r) for r in croot.matrix_world],'W-middleMatrix':[list(r) for r in mroot.matrix_world],'N-middleMatrix':[list(r) for r in r2.matrix_world],'rootPixel':px((0,0,0))}
(dest/'provenance.json').write_text(json.dumps({'stage':'independent judge replay of sealed round03; no approval implied','construction':'Three distinct native objects assembled at exact declared ports, original corner native source plus exact canonical approved middle data; no welding/cap deletion/overlap or fitting','sourceCorner':'resources/round-03.blend','sourceMiddle':'resources/canonical-middle.blend','illumination':'Exact canonical middle scene rig/materials. Corner retains exact sealed native materials.','camera':'Common 4x basis; expanded whole canvas only, root[896,1536], no per-view fitting','pixelFilter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'samples':sc.cycles.samples,'frame':[1792,2432],'views':views},indent=2)+'\n')
print('NATIVE_JOINS_DONE')
