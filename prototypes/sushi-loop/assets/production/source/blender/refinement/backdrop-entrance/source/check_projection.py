import bpy,json
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
s=bpy.context.scene;c=s.camera
for v in [(0,0,0),(1,0,0),(0,0,1),(0,-.5,0),(0,-.5,3.2)]:
 q=world_to_camera_view(s,c,Vector(v));print('PROJECT',v,[q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y])
print('SETTINGS',c.data.ortho_scale,c.data.shift_y,s.render.resolution_x,s.render.resolution_y)
