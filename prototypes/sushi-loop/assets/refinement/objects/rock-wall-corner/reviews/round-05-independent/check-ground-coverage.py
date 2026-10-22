import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(O/'resources/round-05.blend'));ob=bpy.data.objects['rock-wall-corner__unified_worn_stone'];bv=BVHTree.FromObject(ob,bpy.context.evaluated_depsgraph_get());fail=[];heights=[]
for j in range(64):
 for i in range(64):
  x=-.5+(i+.5)/64;y=-.5+(j+.5)/64;point,normal,index,distance=bv.ray_cast(Vector((x,y,-.1)),Vector((0,0,1)),.2)
  if point is None or abs(point.z)>1e-7:fail.append({'x':x,'y':y,'point':list(point) if point else None})
  else:heights.append(point.z)
(O/'ground-grid-coverage.json').write_text(json.dumps({'method':'64x64 cell-interior rays upward from Z-.1 through actual new native unified mesh; contact point must be Z0. Ground area sum is not assumed to be a union measure.','samples':4096,'missingOrNonzeroContacts':fail,'passed':not fail,'minContactZ':min(heights),'maxContactZ':max(heights)},indent=2)+'\n');print('GROUND_GRID',len(fail),'failures of4096')
