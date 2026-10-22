import bpy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
base=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(base/'reviews/preparation-v1/resources/canonical/round-03.blend'))
o=bpy.data.objects['rock-shelf-middle__sculpted_core'];m=o.data;a=m.color_attributes['rock_shelf_albedo']
rows=[]
for p in m.polygons:
 if all(v.co.x < -.4399 for v in [m.vertices[i] for i in p.vertices]) or all(v.co.x>.4399 for v in [m.vertices[i] for i in p.vertices]):
  rows.append({'polygon':p.index,'material':p.material_index,'smooth':p.use_smooth,'normal':list(p.normal),'corners':[{'position':list(m.vertices[m.loops[li].vertex_index].co),'normal':list(m.corner_normals[li].vector),'albedo':list(a.data[m.loops[li].vertex_index].color)} for li in p.loop_indices]})
res={'objects':[{ 'name':x.name,'type':x.type,'parent':x.parent.name if x.parent else None} for x in bpy.context.scene.objects], 'bands':rows,'materials':[{'name':x.name,'nodes':[{'name':n.name,'type':n.type} for n in x.node_tree.nodes]} for x in m.materials], 'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'texts':[t.name for t in bpy.data.texts]}
(base/'source/canonical-inspection.json').write_text(json.dumps(res,indent=2))
print(json.dumps({'bandFaces':len(rows),'bands':rows},indent=2))
