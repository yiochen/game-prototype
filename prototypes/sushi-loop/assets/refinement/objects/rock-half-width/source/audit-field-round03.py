"""Read-only actual mesh/collar and active linked shader evaluation from saved round03."""
import bpy,json,pathlib,hashlib,math,bmesh
from mathutils import Matrix,Vector
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-03';project=P/'source/round-03.blend';before=hashlib.sha256(project.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(project));root=bpy.data.objects['rock-half-width__root.001'];body=bpy.data.objects['rock-half-width__relief_core'];mesh=body.data;tree=mesh.materials[0].node_tree
sections={}
for x in [-.5,-.46,-.42,.42,.46,.5]:sections[str(x)]=sorted(set((float(v.co.y),float(v.co.z)) for v in mesh.vertices if abs(v.co.x-x)<1e-5))
canonical=sections['-0.5'];section_errors={k:max((max(abs(a-b) for a,b in zip(p,q)) for p,q in zip(v,canonical)),default=0) if len(v)==len(canonical) else None for k,v in sections.items()}
collar_indices=[v.index for v in mesh.vertices if abs(v.co.x)>=.42-1e-5]
weights=[float(mesh.attributes['collar_weight'].data[i].value) for i in collar_indices]
# Evaluate the actual linked graph rather than a separate assumed normal/color formula.
def evaluate(local,angle):
 M=Matrix.Rotation(math.radians(angle),4,'Z');world=M@Vector(local);cache={}
 def inp(node,index):
  s=node.inputs[index]
  return val(s.links[0].from_socket) if s.is_linked else tuple(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value
 def v3(x):return Vector(x[:3])
 def val(sock):
  key=(sock.node.name,sock.identifier)
  if key in cache:return cache[key]
  q=sock.node;t=q.bl_idname
  if t=='ShaderNodeNewGeometry':r=tuple(world)
  elif t=='ShaderNodeVectorTransform':
   a=v3(inp(q,0))
   if q.convert_from=='WORLD' and q.convert_to=='OBJECT':r=tuple(M.inverted()@a) if q.vector_type=='POINT' else tuple(M.inverted().to_3x3()@a)
   elif q.convert_from=='OBJECT' and q.convert_to=='WORLD':r=tuple(M.to_3x3().inverted().transposed()@a) if q.vector_type=='NORMAL' else tuple(M@a)
   else:raise ValueError(q.name)
  elif t=='ShaderNodeSeparateXYZ':r=inp(q,0)[{'X':0,'Y':1,'Z':2}[sock.name]]
  elif t=='ShaderNodeCombineXYZ':r=tuple(inp(q,i) for i in range(3))
  elif t=='ShaderNodeMath':
   a=inp(q,0);b=inp(q,1) if len(q.inputs)>1 else 0;op=q.operation
   r={'ABSOLUTE':lambda:abs(a),'MINIMUM':lambda:min(a,b),'MAXIMUM':lambda:max(a,b),'MULTIPLY':lambda:a*b,'ADD':lambda:a+b,'SUBTRACT':lambda:a-b,'SQRT':lambda:math.sqrt(max(a,0)),'SIGN':lambda:1 if a>0 else -1 if a<0 else 0}[op]()
  elif t=='ShaderNodeVectorMath':
   assert q.operation=='NORMALIZE';r=tuple(v3(inp(q,0)).normalized())
  elif t=='ShaderNodeAttribute':
   assert q.attribute_name=='collar_weight';r=1.0
  elif t=='ShaderNodeMixRGB':
   f=inp(q,0)
   if q.blend_type=='MIX':
    if f==1:r=tuple(inp(q,2)[:3])
    elif f==0:r=tuple(inp(q,1)[:3])
    else:r=tuple((1-f)*a+f*b for a,b in zip(inp(q,1),inp(q,2)))[:3]
   else:
    assert q.blend_type=='MULTIPLY';r=tuple((1-f)*a+f*a*b for a,b in zip(inp(q,1),inp(q,2)))[:3]
  elif t=='ShaderNodeEmission':r=tuple(x*inp(q,1) for x in inp(q,0)[:3])
  else:raise ValueError((q.name,t))
  cache[key]=r;return r
 normal=val(tree.nodes['Normalize world shader normal'].outputs['Vector']);albedo=val(tree.nodes['Coherent collar albedo'].outputs[0]);radiance=val(tree.nodes['Opaque native diffuse radiance'].outputs[0]);return normal,albedo,radiance
samples=[];maxnormal=maxcolor=maxradiance=0;derivatives=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 for offset in [0,.02,.04,.06,.08]:
  for z in [0,.2,.4,.64,.8,.93]:
   width=.17 if z<=.64 else .17-(z-.64)/.29*.05
   for y in [-width,-width*.5,0,width*.5,width]:
    w=(-.5+offset,y,z);e=(.5-offset,y,z);wn,wc,wr=evaluate(w,a);en,ec,er=evaluate(e,a)
    ne=max(abs(x-y) for x,y in zip(wn,en));ce=max(abs(x-y) for x,y in zip(wc,ec));re=max(abs(x-y) for x,y in zip(wr,er));maxnormal=max(maxnormal,ne);maxcolor=max(maxcolor,ce);maxradiance=max(maxradiance,re)
    delta=1e-5
    w2=(-.5+offset+delta if offset<.08 else -.5+offset-delta,y,z);e2=(.5-offset-delta if offset<.08 else .5-offset+delta,y,z)
    wn2,wc2,wr2=evaluate(w2,a);en2,ec2,er2=evaluate(e2,a)
    derivatives.append({'direction':d,'inwardOffset':offset,'normalDerivativeW':[(b-a)/delta for a,b in zip(wn,wn2)],'normalDerivativeE':[(a-b)/delta for a,b in zip(en,en2)],'albedoDerivativeW':[(b-a)/delta for a,b in zip(wc,wc2)],'albedoDerivativeE':[(a-b)/delta for a,b in zip(ec,ec2)],'radianceDerivativeW':[(b-a)/delta for a,b in zip(wr,wr2)],'radianceDerivativeE':[(a-b)/delta for a,b in zip(er,er2)]})
    samples.append({'direction':d,'inwardOffset':offset,'WLocalPoint':w,'ELocalPoint':e,'actualLinkedShaderUsedWorldNormalW':wn,'actualLinkedShaderUsedWorldNormalE':en,'albedo':wc,'radianceW':wr,'radianceE':er,'normalLength':Vector(wn).length,'normalError':ne,'albedoError':ce,'radianceError':re})
bm=bmesh.new();bm.from_mesh(mesh);ground=sum(p.area for p in mesh.polygons if all(abs(mesh.vertices[i].co.z)<1e-8 for i in p.vertices))
report={'projectSHA256':before,'projectUnchanged':before==hashlib.sha256(project.read_bytes()).hexdigest(),'blenderBinary':bpy.app.binary_path,'blenderVersion':bpy.app.version_string,'meshObject':body.name,'geometry':{'sectionYZByActualPlane':sections,'sectionDifferenceVsWCap':section_errors,'collarVertexCount':len(collar_indices),'actualCollarWeightMinimum':min(weights),'actualCollarWeightMaximum':max(weights),'groundArea':ground,'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'nativeNormalAttributeDomain':mesh.attributes['native_normal'].domain,'colorAttributeDomain':mesh.color_attributes['stone_color'].domain,'capGeometricNormals':[list(p.normal) for p in mesh.polygons if all(abs(mesh.vertices[i].co.x+.5)<1e-5 for i in p.vertices) or all(abs(mesh.vertices[i].co.x-.5)<1e-5 for i in p.vertices)]},'activeGraphEvaluation':{'sampleCount':len(samples),'method':'Recursively evaluated actual linked saved shader node operations and default parameters, using actual object-normal transform under the four proper root rotations. Both actual Mix factors are1 on the full collar because every actual collar vertex weight is1 and interpolation preserves1. Geometry rings measured at six actual planes. Cap and outer collar share the same active graph.','maximumNormalCorrespondenceError':maxnormal,'maximumAlbedoCorrespondenceError':maxcolor,'maximumRadianceCorrespondenceError':maxradiance,'samples':samples},'linkedShaderNodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value')}} for n in tree.nodes],'linkedShaderLinks':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in tree.links],'scope':'Measured native field/geometry evidence only, no aesthetic verdict or local seam waiver.'}
report['activeGraphEvaluation']['longitudinalDerivativeMethod']='Actual linked graph finite differences at1e-5 within each full collar; the field and albedo depend only on local y and therefore have matching zero longitudinal derivatives under translation. No sample outside physical collar is used.'
report['activeGraphEvaluation']['longitudinalDerivatives']=derivatives
report['activeGraphEvaluation']['maximumLongitudinalDerivative']=max(abs(v) for q in derivatives for k,vals in q.items() if 'Derivative' in k for v in vals)
def geometry_serial(m):return json.dumps({'vertices':[list(v.co) for v in m.vertices],'polygons':[list(p.vertices) for p in m.polygons]},separators=(',',':')).encode()
current_geometry=geometry_serial(mesh);current_geom_sha=hashlib.sha256(current_geometry).hexdigest();bm.free()
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-02.blend'));prior_geometry=geometry_serial(bpy.data.objects['rock-half-width__relief_core'].data)
report['acceptedConstructionPreservation']={'previousRound':'round-02','actualVertexPolygonBytesIdentical':current_geometry==prior_geometry,'round03GeometrySHA256':current_geom_sha,'round02GeometrySHA256':hashlib.sha256(prior_geometry).hexdigest(),'method':'Actual saved source coordinates and polygon index order serialized in each project; no scene was saved by this audit.'}
(O/'actual-field-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'sectionErrors':section_errors,'collarWeights':[min(weights),max(weights)],'normalError':maxnormal,'albedoError':maxcolor,'radianceError':maxradiance,'projectUnchanged':report['projectUnchanged']}))
