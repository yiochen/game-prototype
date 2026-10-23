import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];root=bpy.data.objects['wreck-middle__root'];sc=bpy.context.scene;root.rotation_euler=(0,0,0);root.location=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update();out=[]
for ob in root.children_recursive:
 if ob.type!='MESH' or 'canonical_rail' not in ob.name:continue
 a=ob.data.attributes['CanonicalNormal'];m=root.matrix_world.inverted()@ob.matrix_world
 for side,x in [('W',-.5),('E',.5)]:
  for p in ob.data.polygons:
   points=[m@ob.data.vertices[i].co for i in p.vertices]
   if all(abs(v.x-x)<1e-6 for v in points):
    out.append({'rail':ob.name,'side':side,'vertices':[list(v) for v in points],'shaderAttribute':a.name,'domain':a.domain,'dataType':a.data_type,'normalizedShaderCornerValues':[list(a.data[i].vector.normalized()) for i in p.loop_indices],'material':ob.data.materials[p.material_index].name,'geometryOutwardNormal':list((m.to_3x3().inverted().transposed()@p.normal).normalized())})
(P/'canonical-cap-fields.json').write_text(json.dumps({'actualNativeCapFields':out,'normalChain':'FLOAT_VECTOR CORNER -> Attribute Vector -> ObjectToWorld NORMAL -> NORMALIZE -> active surface Normal. Cap values are outward longitudinal normals; side values stay transverse/height. Equivalent storage/graphs are valid if actual postinterpolation field agrees.','scope':'Exact approved middle02 native technical evidence only'},indent=2)+'\n')
print('CAPS',len(out))
