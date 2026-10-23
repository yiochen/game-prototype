import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
root=bpy.data.objects['reef-edge__root.001']
s=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=s
c=bpy.data.collections['S33_PROP_reef-edge.001']
c.hide_viewport=False;c.hide_render=False
for ob in c.all_objects:ob.hide_viewport=False;ob.hide_set(False)
s.frame_set(1)
for layer in s.view_layers:
 for child in layer.layer_collection.children: child.exclude=False
 layer.update()
parts=[o for o in s.objects if o==root or o.parent==root]
rows=[]
for o in parts:
 row={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'hideRender':o.hide_render}
 if o.type=='MESH':
  vs=[o.matrix_world@v.co for v in o.data.vertices];row.update(vertices=len(vs),polygons=len(o.data.polygons),materials=[m.name for m in o.data.materials],bounds=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]])
 rows.append(row)
(O/'original-native-inspection.json').write_text(json.dumps({'scene':s.name,'root':root.name,'objects':rows,'camera':s.camera.name if s.camera else None},indent=2))
print(json.dumps({'scene':s.name,'count':len(rows),'objects':[r['name'] for r in rows]}))
