import bpy,json
from pathlib import Path
p=Path(__file__).parent
d={"meshes":{},"objects":[],"scene":bpy.context.scene.name}
for o in bpy.data.objects:
 if o.name.startswith("wreck-middle__"):
  d["objects"].append({"name":o.name,"type":o.type,"matrix":[list(r) for r in o.matrix_world],"parent":o.parent.name if o.parent else None})
  if "canonical_rail" in o.name:
   m=o.data;d["meshes"][o.name]={"vertices":[list(v.co) for v in m.vertices],"faces":[list(f.vertices) for f in m.polygons],"matindices":[f.material_index for f in m.polygons],"materials":[x.name for x in m.materials],"attributes":{a.name:{"domain":a.domain,"type":a.data_type,"data":[list(x.vector) for x in a.data] if a.data_type=="FLOAT_VECTOR" else []} for a in m.attributes if not a.name.startswith(".")}}
(p/"canonical-inspection.json").write_text(json.dumps(d,indent=2)+"\n")
for n,m in d["meshes"].items():
 print(n, "matrix",next(o["matrix"] for o in d["objects"] if o["name"]==n),"vertices",len(m["vertices"]),"faces",len(m["faces"]),"x",sorted(set(round(v[0],6) for v in m["vertices"])),"ybounds",[min(v[1] for v in m["vertices"]),max(v[1] for v in m["vertices"])],"zbounds",[min(v[2] for v in m["vertices"]),max(v[2] for v in m["vertices"])],"attrs",[(k,v["domain"],v["type"]) for k,v in m["attributes"].items()])
