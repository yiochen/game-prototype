import bpy,json
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
p=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-post-rope')
r=json.loads((p/'inputs/source-camera.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=r['camera']['pixelAspect'][0];s.render.pixel_aspect_y=1
c=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',c);s.collection.objects.link(o);s.camera=o;o.matrix_world=Matrix(r['camera']['worldMatrix']);c.type='ORTHO';c.ortho_scale=1.5;c.clip_start=.1;c.clip_end=1000
for fit in ['AUTO','HORIZONTAL','VERTICAL']:
 c.sensor_fit=fit;c.shift_y=0
 m=o.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=s.render.pixel_aspect_x,scale_y=1)
 print(fit,list(map(list,m)),list(world_to_camera_view(s,o,Vector((0,0,0)))))
 c.shift_y=1
 print('ONE',list(world_to_camera_view(s,o,Vector((0,0,0)))))
