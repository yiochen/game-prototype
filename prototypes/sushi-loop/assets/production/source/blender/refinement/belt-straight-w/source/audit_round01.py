import bpy,json,pathlib,hashlib,math
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01';F=json.loads((P/'inputs/family-settings.json').read_text());H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def val(x):
 try:return list(x)
 except:return x
def nodes(nt):
 ns=[]
 for n in nt.nodes:
  props={}
  for name in ['operation','blend_type','interpolation','data_type','clamp_type','vector_type','gradient_type','distribution','invert','use_clamp']:
   if hasattr(n,name):props[name]=getattr(n,name)
  ins=[];outs=[]
  for typ,arr in [('inputs',ins),('outputs',outs)]:
   for i,t in enumerate(getattr(n,typ)):
    r={'index':i,'name':t.name,'identifier':t.identifier}
    if hasattr(t,'default_value'):r['defaultValue']=val(t.default_value)
    arr.append(r)
  row={'name':n.name,'type':n.bl_idname,'label':n.label,'properties':props,'inputs':ins,'outputs':outs}
  if hasattr(n,'color_ramp'):row['colorRamp']={'interpolation':n.color_ramp.interpolation,'colorMode':n.color_ramp.color_mode,'hueInterpolation':n.color_ramp.hue_interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  ns.append(row)
 return {'nodes':ns,'links':[{'fromNode':l.from_node.name,'fromSocketIndex':list(l.from_node.outputs).index(l.from_socket),'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocketIndex':list(l.to_node.inputs).index(l.to_socket),'toSocket':l.to_socket.name} for l in nt.links]}
def linked():
 out=[]
 for collection in ['objects','meshes','materials','actions','node_groups','images','worlds','cameras','lights','collections','scenes']:
  for x in getattr(bpy.data,collection):
   if x.library:out.append({'type':collection,'name':x.name,'library':x.library.filepath})
 return out
# Inspect untouched actual W source in an isolated enabled scene; record end vertices and native UV incoming/outgoing association.
bpy.ops.wm.open_mainfile(filepath=F['sourceOfTruth']['path']);c=bpy.data.collections['S33_FB_belt-straight-w.001'];s=bpy.data.scenes.new('ActualSourceAudit');bpy.context.window.scene=s;s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False;o.update_tag()
root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name);root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();dep.update()
sourceProfiles={}
for o in c.objects:
 if o.type!='MESH' or ('stationary_rail' not in o.name and o!=deck):continue
 ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];sourceProfiles[o.name]={'ends':{str(sign*.5):[list(v) for v in vs if abs(v.x-sign*.5)<1e-6] for sign in [-1,1]},'localMesh':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons]};ev.to_mesh_clear()
sourceAction=json.loads((P/'inputs/source-rig.json').read_text())['clips']['running']['actions'][0]['action']
sourceUVMappings=[{'localVertex':list(deck.data.vertices[loop.vertex_index].co),'worldVertex':list(deck.matrix_world@deck.data.vertices[loop.vertex_index].co),'uv':list(deck.data.uv_layers.active.data[loop.index].uv)} for loop in deck.data.loops]
# Reopen delivered normal project, without reading bench scene. Audit actual saved values.
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-w.001'];root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name);s.frame_set(1);bpy.context.view_layer.update();V=json.loads((O/'validation.json').read_text());ports={};topology=[]
for d,a in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(a);bpy.context.view_layer.update();ports[d]={}
 for name,p in {'incoming':(0,.5,.64),'outgoing':(0,-.5,.64),'deck':(0,0,.64)}.items():
  world=orient.matrix_world@Vector(p);v=world_to_camera_view(s,s.camera,world);ports[d][name]={'world':list(world),'logicalRootRelative':[v.x*192-96,(1-v.y)*352-248]}
comparisons=[]
for pr in V['geometry']['exactOpenProfiles']:
 for e,now in pr['ends'].items():
  original=sourceProfiles[pr['name']]['ends'][e];distance=max(min((Vector(v)-Vector(q)).length for q in original) for v in now);comparisons.append({'object':pr['name'],'endPlaneX':float(e),'sourceVertices':original,'candidateVertices':now,'maxNearestCornerDistance':distance,'equalWithin1e-6':distance<1e-6})
matchecks=[]
for mat in {m for o in c.objects if o.type=='MESH' for m in o.data.materials}:
 expectedName='S33_belt-straight-n_moving_deck.001' if mat==deck.data.materials[0] else mat.name
 actual=nodes(mat.node_tree);expected=F['materials'][expectedName]['nodeTree'];matchecks.append({'name':mat.name,'approvedFamilyName':expectedName,'actualGraphSHA256':hashlib.sha256(json.dumps(actual,sort_keys=True).encode()).hexdigest(),'expectedGraphSHA256':hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest(),'equal':actual==expected})
for o in c.objects:
 if o.type!='MESH':continue
 edges={tuple(sorted(e.vertices)):0 for e in o.data.edges}
 for f in o.data.polygons:
  vs=list(f.vertices)
  for x,y in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((x,y)))]+=1
 topology.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'openBoundaryEdges':sum(v==1 for v in edges.values()),'nonmanifoldOver2Edges':sum(v>2 for v in edges.values()),'intentionalOpenPortSection':('stationary_rail' in o.name or o==deck),'modifiers':[m.type for m in o.modifiers]})
V['geometry'].update({'sourceEndProfileComparisons':comparisons,'actualProjectedPorts':ports,'topologyAudit':topology,'sourceProfiles':sourceProfiles,'actualSourceUVVertexAssociations':sourceUVMappings})
V['materialFamilyAudit']=matchecks;V['dependencyClosure']['reopenedProject']={'path':str(P/'source/round-01.blend'),'sha256':H(P/'source/round-01.blend'),'actualLinkedIDs':linked(),'libraries':[{'name':lib.name,'users':lib.users,'filepath':lib.filepath} for lib in bpy.data.libraries],'images':[{'name':im.name,'source':im.source,'packed':bool(im.packed_file)} for im in bpy.data.images],'sourceAction':sourceAction,'candidateAction':deck.data.materials[0].node_tree.animation_data.action.name,'actualCPUDevice':s.cycles.device}
V['camera']['matrixDifferenceFromOriginalMax']=max(abs(a-b) for ar,br in zip(V['camera']['worldMatrix'],json.loads((P/'inputs/source-camera.json').read_text())['camera']['worldMatrix']) for a,b in zip(ar,br))
V['inspectionSequence']='Original/target/family image and actual W source independently inspected before any brief qualityCriteria/reviews. Own unhidden source audit saved before observations/method plan sent to coordinator. Criteria subsequently frozen and acknowledged. Only technical sibling scripts then adapted; no sibling aesthetic critiques read.'
(O/'validation.json').write_text(json.dumps(V,indent=2));(O/'native-audit.json').write_text(json.dumps({'materialFamily':matchecks,'profiles':comparisons,'ports':ports,'dependencyClosure':V['dependencyClosure']['reopenedProject'],'topology':topology},indent=2));print(json.dumps({'materials':matchecks,'profileMax':max(r['maxNearestCornerDistance'] for r in comparisons),'dependency':V['dependencyClosure']['reopenedProject']},indent=2))
# Bind actual reopened scene response settings to the frozen family, rather than echoing values from input.
actualLights=[]
for o in s.objects:
 if o.type=='LIGHT':actualLights.append({'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'shape':o.data.shape,'size':o.data.size,'matrixWorld':[list(r) for r in o.matrix_world]})
actualWorld={'name':s.world.name,'nodes':nodes(s.world.node_tree)}
response={'lights':actualLights,'world':actualWorld,'actualRender':{'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'samplingPattern':s.cycles.sampling_pattern,'scramblingDistance':s.cycles.scrambling_distance,'filter':s.cycles.pixel_filter_type,'filterWidth':s.cycles.filter_width,'ditherIntensity':s.render.dither_intensity,'denoising':s.cycles.use_denoising,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure},'allShaderTexCoordObjectsNone':all(n.object is None for o in c.objects if o.type=='MESH' for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_COORD'),'noGeometryAnimationOwners':all(not o.animation_data or (not o.animation_data.action and not len(o.animation_data.nla_tracks)) for o in c.objects)}
response['exactFrozenLights']=actualLights==F['lights'];response['exactFrozenWorld']=actualWorld==F['world'];response['exactFrozenRenderFields']=all(response['actualRender'][k]==F['render'][k] for k in response['actualRender']);V['actualSceneResponseAudit']=response
(O/'validation.json').write_text(json.dumps(V,indent=2));(O/'scene-response-audit.json').write_text(json.dumps(response,indent=2));print('ACTUAL_SCENE_RESPONSE',response['exactFrozenLights'],response['exactFrozenWorld'],response['exactFrozenRenderFields'])
