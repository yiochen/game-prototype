import bpy,json,pathlib,hashlib,math
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-08';project=P/'source/round-08.blend';bpy.ops.wm.open_mainfile(filepath=str(project));s=bpy.context.scene;V=json.load(open(O/'validation.json'));sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def val(x):
 try:return list(x)
 except:return x
def nodes(nt):
 ns=[]
 for n in nt.nodes:
  props={}
  for name in ['operation','blend_type','interpolation','data_type','clamp_type','vector_type','gradient_type','distribution','invert','use_clamp']:
   if hasattr(n,name):props[name]=getattr(n,name)
  inputs=[];outputs=[]
  for typ,arr in [('inputs',inputs),('outputs',outputs)]:
   for i,t in enumerate(getattr(n,typ)):
    r={'index':i,'name':t.name,'identifier':t.identifier}
    if hasattr(t,'default_value'):r['defaultValue']=val(t.default_value)
    arr.append(r)
  row={'name':n.name,'type':n.bl_idname,'label':n.label,'properties':props,'inputs':inputs,'outputs':outputs}
  if hasattr(n,'color_ramp'):row['colorRamp']={'interpolation':n.color_ramp.interpolation,'colorMode':n.color_ramp.color_mode,'hueInterpolation':n.color_ramp.hue_interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  ns.append(row)
 return {'nodes':ns,'links':[{'fromNode':l.from_node.name,'fromSocketIndex':list(l.from_node.outputs).index(l.from_socket),'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocketIndex':list(l.to_node.inputs).index(l.to_socket),'toSocket':l.to_socket.name} for l in nt.links]}
collection=bpy.data.collections['S33_FB_belt-straight-n.001'];mats={m.name:m for o in collection.objects if o.type=='MESH' for m in o.data.materials};root=next(o for o in collection.objects if '__root.' in o.name);orient=next(o for o in collection.objects if '__orientation.' in o.name)
ports={}
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle;bpy.context.view_layer.update();pd={}
 for name,p in {'incoming':(0,.5,.64),'outgoing':(0,-.5,.64),'deck':(0,0,.64)}.items():
  world=orient.matrix_world@Vector(p);v=world_to_camera_view(s,s.camera,world);pd[name]={'world':list(world),'logicalRootRelative':[v.x*192-96,(1-v.y)*352-248]}
 ports[d]=pd
# Compare actual source endpoint vertices against evaluated candidate native S baseline.
source=json.load(open(P/'source/source-inspection.json'));sourceBy={o['name']:o for o in source['objects']};comparisons=[]
for pr in V['geometry']['exactOpenProfiles']:
 src=sourceBy[pr['name']];mat=Matrix(src['matrix']);vs=[mat@Vector(v) for v in src['vertices']]
 for end,now in pr['ends'].items():
  original=[list(v) for v in vs if abs(v.y-float(end))<1e-6];distance=max(min((Vector(v)-Vector(q)).length for q in original) for v in now);comparisons.append({'object':pr['name'],'endPlaneY':float(end),'sourceVertices':original,'candidateVertices':now,'maxNearestCornerDistance':distance,'equalWithin1e-6':distance<1e-6})
V['geometry']['sourceEndProfileComparisons']=comparisons;V['geometry']['actualProjectedPorts']=ports
V['camera']['matrixDifferenceFromOriginalMax']=max(abs(a-b) for ar,br in zip(V['camera']['worldMatrix'],json.load(open(P/'inputs/source-camera.json'))['camera']['worldMatrix']) for a,b in zip(ar,br));V['dependencyClosure']['reopenedProject']={'path':str(project),'sha256':sha(project),'libraryCount':len(bpy.data.libraries),'imageCount':len(bpy.data.images),'actionCount':len(bpy.data.actions),'actualSourceConfiguredDevice':s.cycles.device};(O/'validation.json').write_text(json.dumps(V,indent=2))
family={'schemaVersion':1,'family':'sushi-conveyor-native-v2','referenceAsset':'belt-straight-n','status':'candidate-reference-awaiting-independent-judge','project':{'path':str(project),'sha256':sha(project),'collection':collection.name},'recipe':{'path':str(P/'source/round-08-recipe.json'),'sha256':sha(P/'source/round-08-recipe.json')},'sourceOfTruth':{'path':str((P/json.load(open(P/'brief.json'))['source']['project']).resolve()),'sha256':json.load(open(P/'brief.json'))['source']['projectSHA256']},'capture':V['camera'],'render':V['render'],'world':{'name':s.world.name,'nodes':nodes(s.world.node_tree)},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'shape':o.data.shape,'size':o.data.size,'matrixWorld':[list(r) for r in o.matrix_world]} for o in s.objects if o.type=='LIGHT'],'materials':{name:{'name':name,'nodeTree':nodes(m.node_tree),'surfaceRenderMethod':getattr(m,'surface_render_method',None)} for name,m in mats.items()},'openProfiles':V['geometry']['exactOpenProfiles'],'sourceEndProfileComparisons':comparisons,'ports':ports,'bounds':V['geometry']['bounds'],'deckSocket':[0,0,.64],'heightEnvelope':[0,.695],'motion':V['motion'],'publisherRootRotationsDegrees':V['publisherRootRotationsDegrees'],'authoredChildOrientationRadians':V['authoredChildOrientationRadians'],'materialCoordinateContract':{'rail':'Straight rails use per-object localX signed across the section ±.065 and localZ relative to its center±.095; common field is invariant in the longitudinal direction. Curved family geometry must provide an equivalent native cross-section coordinate basis rather than reuse worldX.','deck':'Source UV.x incoming0→outgoing1; phase -7*i/24; FRACT(7*UV.x+phase); seven periods/cell. UV.y cross-deck remains unchanged.','wood':'Default per-mesh native object coordinates (not original orientation object), so independent module copies have identical procedural grain. Camera radiance varies only with |normal.z| for horizontal light symmetry.'},'nativeShadingNotes':['Camera-ray procedural radiance provides uninterrupted native stylized surface values. It is evaluated in Blender, contains no target image, and retains BSDF for other rays.','One deterministic TABULATED_SOBOL sample with scrambling0 and dither0 makes source-scale2 coverage binary and avoids inter-surface cut-edge mixing. No per-view fitting or recoloring.','Exact source-size alpha assembly is continuous. Independent mip/bilinear filtering reintroduces N/S silhouette overlap; see filter evidence. This is an unresolved runtime-filter compatibility issue, not an approval.'],'resources':[]}
(P/'source/family-settings.json').write_text(json.dumps(family,indent=2));print('FAMILY',P/'source/family-settings.json');print('PROFILE',[(x['object'],x['endPlaneY'],x['maxNearestCornerDistance']) for x in comparisons]);print('PORTS',ports)
