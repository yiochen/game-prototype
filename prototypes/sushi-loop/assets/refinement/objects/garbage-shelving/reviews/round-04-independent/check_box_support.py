import sys
sys.dont_write_bytecode=True
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-shelving');R=json.loads((O/'candidates/round-04/rig.json').read_text());S=bpy.context.scene
for r in R['clips']['idle']['actions']:
 o=bpy.data.objects[r['ownerName']];ac=bpy.data.actions[r['action']];o.animation_data_create();o.animation_data.action=ac;o.animation_data.action_slot=next(x for x in ac.slots if x.identifier==r['slotIdentifier'])
bpy.data.objects[R['groundRootObject']].rotation_euler=(0,0,0);S.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rows=[]
for i in range(6):
 ob=bpy.data.objects['garbage-shelving__stored_box_'+str(i)];shelf=bpy.data.objects['garbage-shelving__warped_shelf_'+str(0 if i<3 else 1 if i<5 else 2)];eo=shelf.evaluated_get(dg);me=eo.to_mesh();v=[eo.matrix_world@x.co for x in me.vertices];tree=BVHTree.FromPolygons(v,[list(p.vertices) for p in me.polygons]);eo.to_mesh_clear();eo=ob.evaluated_get(dg);me=eo.to_mesh();boxvs=[eo.matrix_world@x.co for x in me.vertices];minimum=min(x.z for x in boxvs);bottom=[x for x in boxvs if x.z<=minimum+.02];gaps=[]
 for pt in bottom:
  hit,n,index,d=tree.ray_cast(pt+Vector((0,0,.1)),Vector((0,0,-1)),.5)
  if hit is not None:gaps.append({'boxPoint':list(pt),'shelfPoint':list(hit),'zGap':pt.z-hit.z})
 eo.to_mesh_clear();rows.append({'box':ob.name,'shelf':shelf.name,'boxMinimumZ':minimum,'shelfMaximumZ':max(x.z for x in v),'bottomSamples':len(bottom),'rayHits':len(gaps),'minimumGap':min((x['zGap'] for x in gaps),default=None),'maximumGap':max((x['zGap'] for x in gaps),default=None),'gaps':gaps})
(O/'reviews/round-04-independent/box-support-audit.json').write_text(json.dumps({'purpose':'Supplementary native shelf-to-box support check after close frontal view. Gaps use downward rays to appropriate shelf from low evaluated box vertices. Bevel rims/tape can differ; native projections remain main visual evidence.','checks':rows},indent=2)+'\n');print([(r['box'],r['minimumGap'],r['maximumGap']) for r in rows])
