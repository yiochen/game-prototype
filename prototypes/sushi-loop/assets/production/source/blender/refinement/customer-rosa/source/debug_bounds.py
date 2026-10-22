exec(open(__file__.replace('debug_bounds.py','debug_plane.py')).read().split("for clip in ['stand'")[0])
import numpy as np
for clip in ['puzzled','panic']:
 maxz=(-1,None);maxy=(-1,None)
 for frame in range(1,13):
  n.apply_clip(dict(root=root,collection=c),r,clip,frame,'S',sc);dep=bpy.context.evaluated_depsgraph_get()
  for o in c.all_objects:
   if o.type!='MESH' or o==p or '__knife_' in o.name or o.hide_render:continue
   e=o.evaluated_get(dep);m=e.to_mesh();a=np.array([list(e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear()
   if a[:,2].max()>maxz[0]:maxz=(a[:,2].max(),(frame,o.name))
   if np.abs(a[:,:2]).max()>maxy[0]:maxy=(np.abs(a[:,:2]).max(),(frame,o.name))
 print('BOUNDS',clip,'maxZ',maxz,'maxXY',maxy)
