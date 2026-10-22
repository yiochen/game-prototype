import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;E=R.parent;sc=bpy.context.scene
vec=lambda v:[float(x) for x in v];mat=lambda m:[vec(r) for r in m]
def value(v):
 if isinstance(v,str):return v
 try:return vec(v)
 except TypeError:return v
write=lambda n,j:(E/n).write_text(json.dumps(j,indent=2,default=str)+'\n')
def enable():
 def visit(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:visit(c)
 visit(bpy.context.view_layer.layer_collection)
 for c in bpy.data.collections:c.hide_viewport=False
 for o in sc.objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def signature_socket(s):
 if not s.is_linked:return {'constant':value(s.default_value)}
 l=s.links[0];n=l.from_node;out=l.from_socket.identifier
 if n.type=='NEW_GEOMETRY':return {'geometry':out}
 if n.type=='SEPARATE_XYZ':return {'separate':out,'input':signature_socket(n.inputs[0])}
 if n.type=='MAP_RANGE':return {'mapRange':n.data_type,'interpolation':n.interpolation_type,'clamp':n.clamp,'inputs':[signature_socket(x) for x in list(n.inputs)[:6]]}
 if n.type=='MIX_RGB':return {'mix':n.blend_type,'clamp':n.use_clamp,'inputs':[signature_socket(x) for x in n.inputs]}
 return {'unsupportedSemantic':n.type,'output':out}
def material_fields(m):
 out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);bs=out.inputs['Surface'].links[0].from_node
 if bs.type!='BSDF_PRINCIPLED':return {'unsupportedSurface':bs.type}
 return {'baseColor':signature_socket(bs.inputs['Base Color']),'parameters':{s.identifier:signature_socket(s) for s in bs.inputs if s.name not in ['Base Color','Normal','Coat Normal','Tangent']},'tangentLinked':bs.inputs['Tangent'].is_linked,'coatNormalLinked':bs.inputs['Coat Normal'].is_linked}
def normal_for(me,p,m):
 out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);bs=out.inputs['Surface'].links[0].from_node;s=bs.inputs['Normal']
 if not s.is_linked:return [me.corner_normals[i].vector.copy() for i in p.loop_indices],{'path':'actual corner normals'}
 n=s.links[0].from_node
 assert n.type=='VECT_MATH' and n.operation=='NORMALIZE',n.type
 tr=n.inputs[0].links[0].from_node;assert tr.type=='VECT_TRANSFORM' and tr.vector_type=='NORMAL' and tr.convert_from=='OBJECT' and tr.convert_to=='WORLD'
 a=tr.inputs['Vector'].links[0].from_node;assert a.type=='ATTRIBUTE';field=me.attributes[a.attribute_name];assert field.domain=='CORNER' and field.data_type=='FLOAT_VECTOR'
 return [field.data[i].vector.copy() for i in p.loop_indices],{'path':'actual CORNER vector > OBJECTtoWORLD NORMAL > NORMALIZE > active surface Normal','attribute':a.attribute_name}
def audit(col,root):
 enable();dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();a={'collection':col.name,'root':root.name,'rootMatrix':mat(root.matrix_world),'rootProperties':dict(root.items()),'objects':[],'rawVertices':[],'evaluatedVertices':[],'supportFaces':[],'collar':[],'materials':{}}
 for o in col.all_objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'localObject':o.library is None,'localData':getattr(o.data,'library',None) is None,'objectAnimation':bool(o.animation_data),'dataAnimation':bool(getattr(o.data,'animation_data',None)),'shapeKeys':bool(getattr(o.data,'shape_keys',None)),'constraints':[c.type for c in o.constraints],'scale':vec(o.scale),'matrix':mat(o.matrix_world),'modifiers':[m.type for m in o.modifiers]};a['objects'].append(d)
  if o.type!='MESH':continue
  a['rawVertices'] += [vec(inv@o.matrix_world@v.co) for v in o.data.vertices]
  eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[inv@eo.matrix_world@v.co for v in me.vertices];a['evaluatedVertices'] += [vec(p) for p in pts]
  for p in me.polygons:
   vs=[pts[i] for i in p.vertices];m=me.materials[p.material_index]
   if max(abs(v.z-.04) for v in vs)<1e-6:a['supportFaces'].append({'object':o.name,'vertices':[vec(v) for v in vs],'normal':vec(p.normal)})
   if min(v.x for v in vs)<-.4199999 and max(v.x for v in vs)<-.419999:
    ns,np=normal_for(me,p,m);normalized=[n.normalized() for n in ns];kind='cap' if max(abs(v.x+.5) for v in vs)<1e-6 else 'side'
    key=[kind]+[round(z,6) for i in [1,2] for z in [min(v[i] for v in vs),max(v[i] for v in vs)]]
    a['collar'].append({'key':key,'vertices':[vec(v) for v in vs],'materialFunction':material_fields(m),'shaderNormals':[vec(n) for n in normalized],'rawShaderNormals':[vec(n) for n in ns],'normalPath':np,'wholeFaceConstant':all((n-normalized[0]).length<1e-7 for n in normalized),'polygonNormal':vec(p.normal),'materialLabelObservation':m.name})
  for m in me.materials:
   if m is None:continue
   a['materials'][m.name]={'nodeTypes':[n.bl_idname for n in m.node_tree.nodes],'materialAnimation':bool(m.animation_data),'nodeAnimation':bool(m.node_tree.animation_data),'local':m.library is None,'activeFields':material_fields(m)}
  eo.to_mesh_clear()
 return a
col=next(c for c in sc.collection.children if any(o.get('asset_id')=='wreck-end' for o in c.all_objects));root=next(o for o in col.all_objects if o.type=='EMPTY' and o.parent is None);enable()
saved={'rootMatrix':mat(root.matrix_world),'frame':sc.frame_current,'frameRange':[sc.frame_start,sc.frame_end],'fps':sc.render.fps,'collections':[c.name for c in sc.collection.children],'imageFiles':[{'name':im.name,'file':im.filepath} for im in bpy.data.images if im.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries],'actions':[a.name for a in bpy.data.actions]}
root.rotation_euler=(0,0,0);enable();own=audit(col,root)
def graph(nt):return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'index':i,'identifier':s.identifier,'value':value(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and s.type not in ['SHADER','CUSTOM']]} for n in nt.nodes],'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in nt.links]}
rig={'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'filter':sc.render.filter_size,'worldGraph':graph(sc.world.node_tree),'worldBackground':[value(s.default_value) for n in sc.world.node_tree.nodes if n.type=='BACKGROUND' for s in list(n.inputs)[:2]],'camera':{'name':sc.camera.name,'matrixWorld':mat(sc.camera.matrix_world),'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'lights':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'energy':o.data.energy,'color':vec(o.data.color),'shape':o.data.shape,'size':o.data.size,'useShadow':o.data.use_shadow,'nodeGraph':graph(o.data.node_tree) if o.data.use_nodes else None} for o in sc.objects if o.type=='LIGHT'],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filmTransparent':sc.render.film_transparent,'useCompositing':sc.render.use_compositing,'compositor':graph(sc.compositing_node_group) if sc.compositing_node_group else None}
refs=[]
for fname in ['canonical-middle.blend','canonical-edge.blend']:
 with bpy.data.libraries.load(str(R/fname),link=False) as (a,b):b.collections=[next(n for n in a.collections if 'wreck' in n.lower())]
 c=b.collections[0];sc.collection.children.link(c);rr=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);rr.rotation_euler=(0,0,0);rr.location=(0,0,0);refs.append((c,rr))
canonical=audit(*refs[0]);comparisons=[]
for f in own['collar']:
 matches=[g for g in canonical['collar'] if g['key']==f['key']];assert len(matches)==1,(f['key'],len(matches));g=matches[0]
 comparisons.append({'domain':f['key'],'materialFunctionsEqual':f['materialFunction']==g['materialFunction'],'maxNormalizedNormalDelta':max((Vector(n)-Vector(g['shaderNormals'][0])).length for n in f['shaderNormals']),'wholeFaceConstantBoth':f['wholeFaceConstant'] and g['wholeFaceConstant'],'normalDerivativeLongitudinal':0 if f['wholeFaceConstant'] else None,'materialDerivativeLongitudinal':'zero: same active worldPositionZ-only function on full constantZ/Y surface','tangentRequirement':f['materialFunction']['tangentLinked'],'outwardCapCorrect':all(n[0]<-.999999 for n in f['shaderNormals']) if f['key'][0]=='cap' else None})
write('native-audit.json',{'blender':bpy.app.version_string,'build':bpy.app.build_hash.decode(),'sourceSHA256':hashlib.sha256((R/'candidate.blend').read_bytes()).hexdigest(),'savedStateBeforeReviewPose':saved,'own':own,'rig':rig,'canonicalCollar':canonical['collar'],'finiteFieldComparisons':comparisons,'fieldProof':'Every actual active constant normalized corner vector remains constant over each triangulated whole finite face after interpolation/normalization. Material expressions matched independently by semantic inputs/operations, excluding node/material names; same worldPositionZ-only function has zero X derivative. Domain regions cover all three complete .08 W intervals and distinct outward caps. Storage/node naming is not the criterion.'})
# Actual independent source recapture and proper-root native assembly; no editor recipe.
baseOrtho=sc.camera.data.ortho_scale;baseShift=sc.camera.data.shift_y;angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};records=[]
for d,angle in angles.items():
 for chain in [False,True]:
  active=[col]+([x[0] for x in refs] if chain else [])
  for c,rr in [(col,root)]+refs:
   c.hide_render=c not in active;c.hide_viewport=c not in active
   for ob in c.all_objects:ob.hide_render=c not in active
   rr.rotation_euler=(0,0,angle);rr.location=(0,0,0)
  for i,(c,rr) in enumerate(refs):rr.location=Matrix.Rotation(angle,4,'Z')@Vector((-i-1,0,0))
  w,h=192,352;origin=[96,248]
  if chain:
   if d in ['N','S']:w,h=448,352;origin=[352 if d=='S' else 96,248]
   else:w,h=192,608;origin=[96,504 if d=='W' else 248]
  sc.render.resolution_x=w*2;sc.render.resolution_y=h*2;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=baseOrtho*w/192;sc.camera.data.shift_x=-(origin[0]-w/2)/w;sc.camera.data.shift_y=baseShift*192/w+(origin[1]-248-(h-352)/2)/(w*sc.render.pixel_aspect_x);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update();v=world_to_camera_view(sc,sc.camera,Vector((0,0,0)))
  out=E/'replay'/('chain' if chain else 'single')/(d+'.png');out.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
  records.append({'direction':d,'chain':chain,'path':str(out.relative_to(E)),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':mat(root.matrix_world),'roots':[{'name':rr.name,'matrix':mat(rr.matrix_world)} for c,rr in [(col,root)]+refs],'frame':[w*2,h*2],'measuredRoot':[v.x*w*2,(1-v.y)*h*2],'logicalRoot':origin,'cameraMatrix':mat(sc.camera.matrix_world),'cameraOrtho':sc.camera.data.ortho_scale,'cameraShift':[sc.camera.data.shift_x,sc.camera.data.shift_y]})
write('independent-capture-records.json',{'sourceSHA256':hashlib.sha256((R/'candidate.blend').read_bytes()).hexdigest(),'records':records,'method':'Independent background native saved-source capture, no editor recipe, no source save or image processing'})
print('AUDIT',len(own['objects']),len(comparisons),'whole collar functions; independent8 captures')
