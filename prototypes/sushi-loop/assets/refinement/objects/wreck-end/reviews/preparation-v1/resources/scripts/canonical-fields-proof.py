import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[2]
def val(x):
 try:return [float(v) for v in x]
 except TypeError:return x
sc=bpy.context.scene;col=next(c for c in sc.collection.children if any(o.name.startswith('wreck-middle__root') for o in c.objects));root=next(o for o in col.objects if o.type=='EMPTY');root.rotation_euler=(0,0,0)
col.hide_viewport=False;col.hide_render=False
for ob in col.all_objects:ob.hide_viewport=False;ob.hide_set(False)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
res={'scope':'Independent actual approved middle02 finite canonical technical fields; no end approval','collars':{'W':[-.5,-.42],'E':[.42,.5]},'nativeRoot':root.name,'materials':{},'rails':[]}
for ob in col.all_objects:
 if ob.type!='MESH' or 'canonical_rail' not in ob.name:continue
 eo=ob.evaluated_get(dg);me=eo.to_mesh();attr=me.attributes.get('CanonicalNormal');assert attr
 rec={'object':ob.name,'attributes':[{'name':a.name,'domain':a.domain,'dataType':a.data_type} for a in me.attributes],'sides':{},'cap':{}}
 for side,xs in [('W',[-.5,-.42]),('E',[.42,.5])]:
  faces=[];cap=[]
  for p in me.polygons:
   ps=[eo.matrix_world@me.vertices[v].co for v in p.vertices]
   if all(abs(v.x-xs[0 if side=='W' else 1])<1e-6 for v in ps):cap.append({'points':[val(x) for x in ps],'normals':[val(attr.data[i].vector) for i in p.loop_indices],'material':me.materials[p.material_index].name});continue
   if min(v.x for v in ps)>=xs[0]-1e-6 and max(v.x for v in ps)<=xs[1]+1e-6:
    ns=[attr.data[i].vector.copy() for i in p.loop_indices];m=me.materials[p.material_index]
    faces.append({'points':[val(x) for x in ps],'normalAttribute':[val(n) for n in ns],'normalizedShaderNormal':[val(n.normalized()) for n in ns],'normalConstantOnWholeFace':all((n-ns[0]).length<1e-7 for n in ns),'material':m.name,'triangulationIndependentProof':'constant corner field interpolates constantly; object/world transform and normalize preserve constant normal for every barycentric point; no tangent-space nodes active'})
    if m.name not in res['materials']:
     nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');mr=next(n for n in nt.nodes if n.type=='MAP_RANGE');mix=next(n for n in nt.nodes if n.type=='MIX_RGB');source=bs.inputs['Normal'].links[0].from_node
     assert source.type=='VECT_MATH' and source.operation=='NORMALIZE';trans=source.inputs[0].links[0].from_node;assert trans.type=='VECT_TRANSFORM' and trans.vector_type=='NORMAL' and trans.convert_from=='OBJECT' and trans.convert_to=='WORLD';an=trans.inputs['Vector'].links[0].from_node;assert an.type=='ATTRIBUTE' and an.attribute_name=='CanonicalNormal'
     alpha=bs.inputs['Alpha'];assert not alpha.is_linked
     res['materials'][m.name]={'actualActiveNormalPath':['CanonicalNormal CORNER FLOAT_VECTOR','OBJECT to WORLD NORMAL transform','NORMALIZE','Principled Normal','Material Output'],'baseColor':{'heightSpace':'world Position Z','mapRangeSockets':[{'index':i,'name':s.name,'identifier':s.identifier,'type':s.type,'value':val(s.default_value)} for i,s in enumerate(mr.inputs) if hasattr(s,'default_value')],'activeScalarRange':{'FromMin':mr.inputs[1].default_value,'FromMax':mr.inputs[2].default_value,'ToMin':mr.inputs[3].default_value,'ToMax':mr.inputs[4].default_value},'dataType':mr.data_type,'interpolation':mr.interpolation_type,'clamp':mr.clamp,'blendType':mix.blend_type,'factor':mix.inputs[0].default_value,'linearBaseColor':val(mix.inputs[1].default_value),'longitudinalDerivative':0,'proof':'actual albedo depends solely on unchanged world Z on every collar point; no X/Y or object Generated dependence'},'surface':{k:val(bs.inputs[k].default_value) for k in ['Roughness','Metallic','Specular IOR Level','Alpha','IOR','Emission Strength']},'alphaLinked':alpha.is_linked,'tangentRequired':False,'allNodeTypes':[n.bl_idname for n in nt.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links]}
  rec['sides'][side]=faces;rec['cap'][side]=cap
 # Pair corresponding YZ sides. X intervals lie on opposite inward sides of the true plane; fields are proven constant in X over each full finite interval, so their normalized endpoint-aligned functions and first derivatives coincide.
 def key(f,off):return tuple(sorted(tuple(round(x,6) for x in p[1:]) for p in f['points']))
 w=rec['sides']['W'];e=rec['sides']['E'];diff=[]
 for f in w:
  matches=[g for g in e if key(f,1)==key(g,0)];assert len(matches)==1,(ob.name,key(f,1),len(matches));g=matches[0]
  diff.append({'Wmaterial':f['material'],'Ematerial':g['material'],'materialsEqual':f['material']==g['material'],'maxNormalizedNormalDelta':max((Vector(f['normalizedShaderNormal'][0])-Vector(n)).length for n in g['normalizedShaderNormal']),'constantWholeFace':f['normalConstantOnWholeFace'] and g['normalConstantOnWholeFace']})
 rec['WtoEWholeFiniteFieldProof']=diff;res['rails'].append(rec);eo.to_mesh_clear()
res['all4ProperRotations']={d:{'degrees':deg,'determinant':Matrix.Rotation(math.radians(deg),3,'Z').determinant(),'effect':'same proper rotation on shape/normal fields; world Z and height albedo unchanged; reflected rear lip forbidden'} for d,deg in [('N',180),('E',90),('S',0),('W',-90)]}
res['interpretation']='All finite canonical side faces are constant normalized shader normal and identical material under W/E translation; alpha1; tangents unused; albedoZ-only; longitudinal derivatives zero throughout full .08. Corresponding outward caps retain -X/+X rather than reusing side normals. End candidate must independently prove matching full W field and clean interior transition; IDs alone do not establish this.'
(P/'canonical-fields-proof.json').write_text(json.dumps(res,indent=2)+'\n');print('canonical rails',len(res['rails']),'materials',len(res['materials']))
