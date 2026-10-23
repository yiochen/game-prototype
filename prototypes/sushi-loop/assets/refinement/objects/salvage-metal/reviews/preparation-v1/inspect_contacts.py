import sys,json,importlib.util,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
P=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('own_native_contacts',P/'resources/native/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
rig=json.loads((P/'resources/object/inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=next(c for c in sc.collection.children if root.name in c.all_objects);asset={'root':root,'collection':col};owned=list(col.all_objects)
def layers(n):
 yield n
 for c in n.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def section(mesh,matrix):
 pts=[matrix@v.co for v in mesh.vertices];hits=[]
 for e in mesh.edges:
  a,b=[pts[i] for i in e.vertices]
  if abs(a.z)<1e-7:hits.append(list(a))
  if abs(b.z)<1e-7:hits.append(list(b))
  if a.z*b.z<0:hits.append(list(a+(b-a)*(-a.z/(b.z-a.z))))
 unique={tuple(round(v,8) for v in p) for p in hits}
 return {'vertexMinZ':min(v.z for v in pts),'vertexMaxZ':max(v.z for v in pts),'belowGroundVertexCount':sum(v.z< -1e-7 for v in pts),'groundSectionPoints':sorted(unique),'note':'Exact mesh-edge intersections with registered Z=0 plane; finite shape sections, not full-cell support.'}
records=[]
for clip in ['shimmer','b-shimmer','c-shimmer']:
 native.apply_clip(asset,rig,clip,frame=1,direction='S',scene=sc)
 for o in owned:o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ob=[]
 for o in owned:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();ob.append({'name':o.name,'rawAuthoredTransformed':section(o.data,o.matrix_world),'evaluatedModifier':section(m,e.matrix_world)});e.to_mesh_clear()
 records.append({'clip':clip,'sourceFrame':1,'direction':'S','rootMatrix':[list(r) for r in root.matrix_world],'objects':ob})
(P/'native/finite-support-sections.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'records':records,'interpretation':'Plate authored tilted body intersects ground slightly; bent shard has finite bottom face at ground; mixed variant wood block has finite bottom face. There is no modeled full-cell floor or attachment connector.'},indent=2)+'\n')
print('FINITE_SUPPORT_SECTIONS_COMPLETE',len(records))
