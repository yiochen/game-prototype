import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
s=bpy.context.scene
for c in bpy.data.collections:c.hide_viewport=False
for l in s.view_layers[0].layer_collection.children:l.exclude=False;l.hide_viewport=False
s.view_layers[0].update();out={}
for cn,bound in [('S33_PROP_uniform35-gate',2),('S33_PROP_uniform35-wall-plain',.5)]:
 col=bpy.data.collections[cn];objects={}
 for o in col.objects:
  d={'type':o.type,'matrix':[list(r) for r in o.matrix_world],'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':
   verts=[list(v.co) for v in o.data.vertices];polys=[list(f.vertices) for f in o.data.polygons];pts=[o.matrix_world@v.co for v in o.data.vertices]
   d.update(vertices=len(verts),polygons=len(polys),geometrySha256=hashlib.sha256(json.dumps({'verts':verts,'polys':polys},sort_keys=True).encode()).hexdigest(),bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],protectedJoin=any(abs(abs(v.x)-bound)<1e-5 for v in pts),modifiers=[{'type':m.type,**{k:getattr(m,k) for k in ['width','segments','limit_method','thickness','offset'] if hasattr(m,k)}} for m in o.modifiers])
  objects[o.name]=d
 out[cn]=objects
(P/'native-baseline.json').write_text(json.dumps(out,indent=2));print('BASELINE_SAVED')
