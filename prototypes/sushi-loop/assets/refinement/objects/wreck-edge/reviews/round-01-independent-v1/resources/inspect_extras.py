import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;root=bpy.data.objects['wreck-edge__root'];owned={root,*root.children_recursive};sc=bpy.context.scene
mats={m for o in owned if hasattr(o.data,'materials') for m in o.data.materials if m};caps=[];ownership=[]
for m in sorted(mats,key=lambda m:m.name):
 users=[o for o in bpy.data.objects if hasattr(o.data,'materials') and m in list(o.data.materials)]
 ownership.append({'material':m.name,'objectUsers':[o.name for o in users],'outsideObjectUsers':[o.name for o in users if o not in owned],'groups':[n.node_tree.name for n in m.node_tree.nodes if hasattr(n,'node_tree') and n.node_tree],'images':[n.image.filepath for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'animation':bool(m.animation_data or m.node_tree.animation_data)})
for ob in owned:
 if ob.type!='MESH' or 'canonical_rail' not in ob.name:continue
 me=ob.data;attr=me.attributes['CanonicalNormal'];assert attr.domain=='CORNER' and attr.data_type=='FLOAT_VECTOR'
 for side,x,want in [('W',-.5,(-1,0,0)),('E',.5,(1,0,0))]:
  ps=[p for p in me.polygons if all(abs(me.vertices[i].co.x-x)<1e-6 for i in p.vertices)];assert len(ps)==1;p=ps[0];ns=[list(attr.data[i].vector.normalized()) for i in p.loop_indices];assert all((Vector(n)-Vector(want)).length<1e-7 for n in ns)
  m=me.materials[p.material_index];nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');normalize=bs.inputs['Normal'].links[0].from_node;tr=normalize.inputs[0].links[0].from_node;a=tr.inputs['Vector'].links[0].from_node
  assert normalize.type=='VECT_MATH' and normalize.operation=='NORMALIZE' and tr.type=='VECT_TRANSFORM' and tr.vector_type=='NORMAL' and tr.convert_from=='OBJECT' and tr.convert_to=='WORLD' and a.type=='ATTRIBUTE' and a.attribute_name=='CanonicalNormal' and a.attribute_type=='GEOMETRY'
  caps.append({'object':ob.name,'side':side,'actualNormalizedCapFields':ns,'activeShaderPathVerified':True})
out={'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'render':{'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'percentage':sc.render.resolution_percentage,'transparent':sc.render.film_transparent,'PNG':[sc.render.image_settings.file_format,sc.render.image_settings.color_mode,sc.render.image_settings.color_depth],'useCompositing':sc.render.use_compositing,'compositorGroup':sc.compositing_node_group.name if sc.compositing_node_group else None},'caps':caps,'privateMaterials':ownership,'images':[{'name':i.name,'users':i.users,'source':i.source,'filepath':i.filepath} for i in bpy.data.images],'armatures':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'actions':[a.name for a in bpy.data.actions],'sceneObjects':[{'name':o.name,'type':o.type,'hideRender':o.hide_render} for o in sc.objects]}
assert len(caps)==6 and all(not r['outsideObjectUsers'] and not r['images'] and not r['animation'] for r in ownership)
(BASE.parent/'native-extras.json').write_text(json.dumps(out,indent=2)+'\n');print('NATIVE_EXTRAS_PRIVATE_CAP_FIELDS_VERIFIED')
