import bpy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;sc=bpy.context.scene
for c in bpy.data.collections:c.hide_viewport=False

def en(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:en(c)
en(bpy.context.view_layer.layer_collection)
col=next(c for c in sc.collection.children if any(o.get('asset_id')=='wreck-end' for o in c.all_objects));root=next(o for o in col.all_objects if o.type=='EMPTY');root.rotation_euler=(0,0,0)
for o in col.all_objects:o.hide_set(False);o.hide_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();v=lambda p:[float(x) for x in p];out=[]
for o in col.all_objects:
 if o.type!='CURVE':continue
 eo=o.evaluated_get(dg);m=eo.to_mesh();ps=[v(inv@eo.matrix_world@x.co) for x in m.vertices];raw=[]
 for s in o.data.splines:
  raw += [v(inv@o.matrix_world@p.co.to_3d()) for p in s.points]
  raw += [v(inv@o.matrix_world@p.co) for p in s.bezier_points]
 out.append({'object':o.name,'rawCurveControlPoints':raw,'evaluatedVertices':ps,'dataAnimation':bool(o.data.animation_data),'objectAnimation':bool(o.animation_data),'localData':o.data.library is None,'materials':[{'name':m.name,'local':m.library is None,'materialAnimation':bool(m.animation_data),'nodeAnimation':bool(m.node_tree.animation_data),'nodeTypes':[n.bl_idname for n in m.node_tree.nodes]} for m in o.data.materials if m]});eo.to_mesh_clear()
(R.parent/'curve-audit.json').write_text(json.dumps({'curves':out,'method':'Actual enabled own evaluated CURVE surfaces plus authored control points; no source save'},indent=2)+'\n');print('curves',len(out),'evaluated vertices',sum(len(x['evaluatedVertices']) for x in out))
