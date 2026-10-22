import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;out=[]
for ob in bpy.data.objects:
 if ob.type!='MESH' or 'canonical_rail' not in ob.name:continue
 me=ob.data;a=me.attributes['CanonicalNormal'];assert a.domain=='CORNER' and a.data_type=='FLOAT_VECTOR'
 for side,x,n in [('W',-.5,(-1,0,0)),('E',.5,(1,0,0))]:
  ps=[p for p in me.polygons if all(abs(me.vertices[i].co.x-x)<1e-6 for i in p.vertices)];assert len(ps)==1
  values=[list(a.data[i].vector.normalized()) for i in ps[0].loop_indices];assert all((Vector(v)-Vector(n)).length<1e-7 for v in values)
  mat=me.materials[ps[0].material_index];nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');normal=bs.inputs['Normal'];assert normal.is_linked
  norm=normal.links[0].from_node;assert norm.type=='VECT_MATH' and norm.operation=='NORMALIZE';transform=norm.inputs[0].links[0].from_node;assert transform.type=='VECT_TRANSFORM' and transform.vector_type=='NORMAL' and transform.convert_from=='OBJECT' and transform.convert_to=='WORLD';attr=transform.inputs['Vector'].links[0].from_node;assert attr.type=='ATTRIBUTE' and attr.attribute_name=='CanonicalNormal' and attr.attribute_type=='GEOMETRY'
  out.append({'object':ob.name,'port':side,'shaderUsedNormalizedCapCornerNormals':values,'normalGraphVerified':'Geometry CanonicalNormal -> Object-to-World NORMAL -> Normalize -> Principled Normal','capIsSeparateFromSideNormals':True})
(BASE.parent/'canonical-cap-field-proof.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'caps':out,'count':len(out)},indent=2)+'\n');assert len(out)==6;print('CANONICAL_CAP_FIELDS_VERIFIED',len(out))
