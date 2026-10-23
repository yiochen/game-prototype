import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(P/'source/geometry-stage.blend'))
s=bpy.context.scene;c=s.camera;bpy.context.view_layer.update()
def project(p):
 q=world_to_camera_view(s,c,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
print(json.dumps({'front':project((0,-.5,0)),'root':project((0,0,0)),'unitX':[a-b for a,b in zip(project((1,-.5,0)),project((0,-.5,0)))],'unitZ':[a-b for a,b in zip(project((0,-.5,1)),project((0,-.5,0)))]},indent=2))
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.studiolight_rotate_z=0;s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.curvature_ridge_factor=1.3;s.display.shading.curvature_valley_factor=.8
s.render.filepath=str(P/'candidates/geometry-stage-workbench.png');bpy.ops.render.render(write_still=True)
