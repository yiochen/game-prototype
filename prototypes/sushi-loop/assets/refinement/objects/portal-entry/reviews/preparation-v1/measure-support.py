import bpy,sys,json,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((H/'resources/inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects))
def unexclude(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:unexclude(c)
unexclude(sc.view_layers[0].layer_collection)
for c in [col,*col.children_recursive]:c.hide_render=False;c.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
spec=importlib.util.spec_from_file_location('native',H/'resources/native/native_actions.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.apply_clip({'root':root,'collection':col},rig,'enter',frame=1,direction='S',scene=sc);bpy.context.view_layer.update()
report=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();vs=[e.matrix_world@v.co for v in mesh.vertices];pts=[]
 for edge in mesh.edges:
  a,b=(vs[i] for i in edge.vertices)
  if a.z*b.z<0:
   t=-a.z/(b.z-a.z);p=a+(b-a)*t;pts.append(list(p))
  elif abs(a.z)<1e-7:pts.append(list(a))
  elif abs(b.z)<1e-7:pts.append(list(b))
 report.append({'object':o.name,'planeZ':0,'edgeIntersections':pts,'contactSectionBounds':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]} if pts else None,'geometryZRange':[min(v.z for v in vs),max(v.z for v in vs)],'animatedOwner':o.name in [t['ownerName'] for t in rig['clips']['enter']['actions']]});e.to_mesh_clear()
(H/'support-sections.json').write_text(json.dumps({'method':'Enabled evaluated mesh edge intersections with root planeZ0 atS frame1; finite cross-sections, not a flat opaque support surface or physical collision shape. Supports are unanimated owners.','root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'objects':report},indent=2)+'\n')
