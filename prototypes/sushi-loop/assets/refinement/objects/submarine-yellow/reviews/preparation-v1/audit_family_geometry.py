import bpy,json,pathlib,hashlib
from mathutils import Vector
out=pathlib.Path(__file__).resolve().parent;res=out/'resources'
def vv(v):return [round(float(x),9) for x in v]
def box(pts):return [vv([min(p[i] for p in pts) for i in range(3)]),vv([max(p[i] for p in pts) for i in range(3)])]
reports=[]
for file in ['original-library.blend','dock-floor-round04.blend','dock-entry-round06.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(res/file));old=bpy.context.scene;sc=bpy.data.scenes.new('Judge family geometry');bpy.context.window.scene=sc
 if file=='original-library.blend':cols=[c for c in bpy.data.collections if any(x in c.name.lower() for x in ['hull_panel','harpoon_mount','collector_inlet','dock-floor','dock-entry','workshop-hut','dock-cover'])]
 else:cols=[c for c in bpy.data.collections if c.objects and not any(c in list(other.children) for other in bpy.data.collections)]
 for c in cols:sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 bpy.context.view_layer.update();report={'resource':file,'collections':[]}
 for c in cols:
  rr={'name':c.name,'objects':[]}
  for o in c.all_objects:
   if o.type!='MESH':continue
   eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];faces=[]
   for p in me.polygons:
    world=[pts[i] for i in p.vertices];no=(eo.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized()
    if abs(no.z)>.99:faces.append({'normal':vv(no),'bounds':box(world),'vertices':[vv(x) for x in world]})
   rr['objects'].append({'name':o.name,'mesh':o.data.name,'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'location':vv(o.location),'scale':vv(o.scale),'rotation':vv(o.rotation_euler),'worldMatrix':[vv(x) for x in eo.matrix_world],'bounds':box(pts),'materials':[m.name for m in me.materials],'geometrySHA256':hashlib.sha256(json.dumps({'vertices':[vv(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]},sort_keys=True).encode()).hexdigest(),'horizontalFaces':faces})
   eo.to_mesh_clear()
  report['collections'].append(rr)
 reports.append(report)
(out/'family-geometry-audit.json').write_text(json.dumps(reports,separators=(',',':')))
print(json.dumps([{'resource':r['resource'],'collections':[{'name':c['name'],'meshes':len(c['objects'])} for c in r['collections']]} for r in reports]))
