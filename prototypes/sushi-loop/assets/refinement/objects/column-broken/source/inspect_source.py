import bpy,json, pathlib
from mathutils import Vector
p=pathlib.Path(__file__).parent
def mat(m):return [list(r) for r in m]
roots=[o for o in bpy.data.objects if "pale-column" in o.name]
obs={"blenderVersion":bpy.app.version_string,"scenes":[s.name for s in bpy.data.scenes],"roots":[]}
for r in roots:
 rec={"name":r.name,"type":r.type,"parent":r.parent.name if r.parent else None,"matrix":mat(r.matrix_world),"props":{k:str(r[k]) for k in r.keys()},"children":[]}
 for o in r.children_recursive:
  c={"name":o.name,"type":o.type,"matrix":mat(o.matrix_world),"modifiers":[m.type for m in o.modifiers],"materials":[x.name for x in o.data.materials] if o.type=="MESH" else []}
  if o.type=="MESH":
   vs=[o.matrix_world@v.co for v in o.data.vertices];c["bounds"]={"min":[min(v[i] for v in vs) for i in range(3)],"max":[max(v[i] for v in vs) for i in range(3)]};c["vertices"]=len(o.data.vertices);c["faces"]=len(o.data.polygons)
  rec["children"].append(c)
 obs["roots"].append(rec)
obs["externalResources"]={"images":[{"name":i.name,"filepath":i.filepath,"packed":bool(i.packed_file)} for i in bpy.data.images],"libraries":[l.filepath for l in bpy.data.libraries]}
obs["sceneCameras"]=[{"scene":s.name,"camera":s.camera.name if s.camera else None,"worldMatrix":mat(s.camera.matrix_world) if s.camera else None,"ortho_scale":s.camera.data.ortho_scale if s.camera else None,"shift_y":s.camera.data.shift_y if s.camera else None,"resolution":[s.render.resolution_x,s.render.resolution_y],"pixelAspect":[s.render.pixel_aspect_x,s.render.pixel_aspect_y]} for s in bpy.data.scenes]
(p/"source-scene-inspection.json").write_text(json.dumps(obs,indent=2))
print(json.dumps(obs,indent=2))
