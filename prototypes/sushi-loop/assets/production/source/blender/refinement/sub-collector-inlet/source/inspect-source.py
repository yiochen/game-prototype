import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath="/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend")
cs=[c for c in bpy.data.collections if "collector" in c.name.lower()]
out={"collections":[]}
for c in cs:
 rec={"name":c.name,"objects":[]}
 for o in c.all_objects:
  ob={"name":o.name,"type":o.type,"parent":o.parent.name if o.parent else None,"location":list(o.location),"rotation":list(o.rotation_euler),"scale":list(o.scale),"dimensions":list(o.dimensions),"custom":dict(o.items())}
  if o.type=="MESH": ob.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),materials=[m.name for m in o.data.materials],bounds=[list(o.matrix_world@__import__("mathutils").Vector(v)) for v in o.bound_box])
  if o.animation_data: ob["action"]=o.animation_data.action.name if o.animation_data.action else None
  rec["objects"].append(ob)
 out["collections"].append(rec)
Path(__file__).with_name("source-inspection.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
