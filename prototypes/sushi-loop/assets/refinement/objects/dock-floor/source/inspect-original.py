import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
c=bpy.data.collections['S33_PROP_dock-floor.001']
s=bpy.data.scenes.new('IndependentSourceInspection')
s.collection.children.link(c)
c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_viewport=False;o.hide_render=False
bpy.context.window.scene=s
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
a=[]
for o in c.all_objects:
 e=o.evaluated_get(dg); m=e.to_mesh() if o.type=='MESH' else None
 vs=[e.matrix_world@v.co for v in m.vertices] if m else []
 a.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'matrixWorld':[list(r) for r in e.matrix_world],'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]] if vs else None,'vertexCount':len(vs),'polygonCount':len(m.polygons) if m else None,'materials':[x.name for x in o.data.materials] if m else [],'modifiers':[{'type':x.type,'width':getattr(x,'width',None),'segments':getattr(x,'segments',None)} for x in o.modifiers]})
 if m:e.to_mesh_clear()
source=Path(bpy.data.filepath)
out={'source':str(source),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'collection':c.name,'root':[0,0,0],'objects':a,'savedActiveCameraUnrelated':True}
(p/'independent-source-inspection.json').write_text(json.dumps(out,indent=2))
