import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib
from pathlib import Path
col=bpy.data.collections.get("S33_PROP_safe-passage.001")
root=bpy.data.objects.get("safe-passage__root.001")
r={"scene_names_only":[s.name for s in bpy.data.scenes],"own_collection_found":col is not None,"own_root_found":root is not None,"own_collection_scene_membership":[s.name for s in bpy.data.scenes if col and any(c==col for c in s.collection.children_recursive)],"own_root_scene_membership":[s.name for s in bpy.data.scenes if root and root.name in s.objects]}
p=Path("/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/safe-passage/source/initial-native-locator-v1.json")
with p.open("x") as f: json.dump(r,f,indent=2);f.write("\n")
print(json.dumps(r))
