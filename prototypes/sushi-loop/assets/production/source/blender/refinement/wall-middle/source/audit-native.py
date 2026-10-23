import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];R='round-06';C=B/'candidates'/R;P=B/'source'/f'{R}.blend'
bpy.ops.wm.open_mainfile(filepath=str(P));s=bpy.context.scene;c=bpy.data.collections['S33_PROP_wall-middle.001'];root=next(o for o in c.all_objects if o.type=='EMPTY');bpy.context.view_layer.update()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool))or v is None:return v
 try:return [value(t)for t in v]
 except:return str(v)
def nodes(tree):
 result=[]
 for n in tree.nodes:
  q={'name':n.name,'bl_idname':n.bl_idname,'inputs':{str(i)+':'+v.name:value(v.default_value)for i,v in enumerate(n.inputs)if hasattr(v,'default_value')}}
  for prop in ('operation','blend_type','vector_type','convert_from','convert_to','interpolation','distribution','subsurface_method','space'):
   if hasattr(n,prop):q[prop]=value(getattr(n,prop))
  if hasattr(n,'color_ramp'):q['colorRamp']={'interpolation':n.color_ramp.interpolation,'colorMode':n.color_ramp.color_mode,'elements':[{'position':e.position,'color':list(e.color)}for e in n.color_ramp.elements]}
  result.append(q)
 return {'nodes':result,'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name,'toIndex':list(l.to_node.inputs).index(l.to_socket)}for l in tree.links]}
meshes=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 m=o.data;edgeuses={tuple(sorted(e.vertices)):0 for e in m.edges}
 for p in m.polygons:
  vs=list(p.vertices)
  for a,b in zip(vs,vs[1:]+vs[:1]):edgeuses[tuple(sorted((a,b)))]+=1
 boundary=[e for e,n in edgeuses.items()if n==1];bad=[e for e,n in edgeuses.items()if n>2]
 cut_boundary=all(abs(abs(m.vertices[e[0]].co.x)-.5)<1e-6 and abs(m.vertices[e[0]].co.x-m.vertices[e[1]].co.x)<1e-6 for e in boundary)
 pts=[o.matrix_world@v.co for v in m.vertices]
 meshes.append({'name':o.name,'matrix':value(o.matrix_world),'vertices':len(m.vertices),'polygons':len(m.polygons),'materials':[m.name for m in o.data.materials],'zeroAreaFaces':sum(p.area<1e-12 for p in m.polygons),'nonManifoldNonCutEdges':len(bad),'openEdges':len(boundary),'allOpenEdgesOnDeclaredCuts':cut_boundary,'bounds':[[min(v[i]for v in pts),max(v[i]for v in pts)]for i in range(3)],'hasCustomNormals':m.has_custom_normals})
matdata=[{'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':nodes(m.node_tree)}for m in bpy.data.materials if m.users and m.node_tree]
cam=s.camera
settings={'schemaVersion':1,'family':'restaurant-wall-wood-blue-v2','status':'candidate-awaiting-independent-approval','asset':'wall-middle','candidate':R,'project':{'path':str(P.relative_to(B)),'sha256':sha(P)},'recipe':{'path':f'source/{R}.py','sha256':sha(B/'source'/f'{R}.py')},'capture':{'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'frame':[384,704],'cellSize':128,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'camera':{'worldMatrix':value(cam.matrix_world),'type':cam.data.type,'sensorFit':cam.data.sensor_fit,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'clipStart':cam.data.clip_start,'clipEnd':cam.data.clip_end},'facingDegrees':{'S':0,'E':90,'N':180,'W':-90}},'materials':matdata,'lighting':{'world':{'name':s.world.name,'nodeTree':nodes(s.world.node_tree)},'lights':[{'name':o.name,'type':o.data.type,'shape':o.data.shape,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrix':value(o.matrix_world)}for o in s.objects if o.type=='LIGHT'],'horizontalSymmetry':4,'noGroundReceiver':True},'render':{'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'denoise':s.cycles.use_denoising,'maxBounces':s.cycles.max_bounces,'transparentMaxBounces':s.cycles.transparent_max_bounces,'filterSize':s.render.filter_size,'pixelFilter':s.cycles.pixel_filter_type,'transparent':s.render.film_transparent,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'outputFormat':s.render.image_settings.file_format,'outputColorMode':s.render.image_settings.color_mode,'outputColorDepth':s.render.image_settings.color_depth},'ports':json.loads(root['ports']),'boundaryContract':{'planes':{'W':-.5,'E':.5},'bodyPanel':{'halfDepth':.105,'z':[.07,.89]},'timberBeads':[{'halfDepth':.115,'z':[z,z+.025]}for z in[.12,.34,.56,.78]],'woodCap':{'halfDepth':.15,'z':[.86,.935]},'blueCoping':{'widthZ':[[.18,.93],[.18,.97],[.12,1.01]]},'cutClosure':'Body meshes intentionally open on exact source cuts. Wood cut closure uses camera BSDF / transparent secondary rays. Blue cut closure uses the common native procedural top-radiance field for camera rays and ordinary BSDF for transport. Corners/end members must use the same material roles, radiance model, and boundary profiles.'},'blueCutRadianceModel':json.loads((B/'source/cut-radiance-model.json').read_text()),'resourceClosure':{'images':[{'name':i.name,'path':i.filepath}for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]}}
(C/'family-settings.json').write_text(json.dumps(settings,indent=2))
(C/'native-audit.json').write_text(json.dumps({'project':settings['project'],'blender':bpy.app.version_string,'scene':s.name,'selectedCollection':c.name,'root':{'name':root.name,'matrix':value(root.matrix_world),'groundRoot':json.loads(root['ground_root'])},'meshes':meshes,'resourceClosure':settings['resourceClosure'],'sceneObjectCounts':{'mesh':sum(o.type=='MESH'for o in s.objects),'lights':sum(o.type=='LIGHT'for o in s.objects),'cameras':sum(o.type=='CAMERA'for o in s.objects)},'checks':{'isolatedAsset':all(o.name in c.all_objects or o.type in['LIGHT','CAMERA']for o in s.objects),'noExternalDependencies':not bpy.data.images and not bpy.data.libraries,'noZeroAreaFaces':all(m['zeroAreaFaces']==0 for m in meshes),'allNonManifoldEdgesAreIntentionalPortBoundaries':all(m['nonManifoldNonCutEdges']==0 and m['allOpenEdgesOnDeclaredCuts']for m in meshes),'actualRootAtOrigin':root.location.length<1e-7,'functionalEnvelope':max(m['bounds'][2][1]for m in meshes)<=1.02}},indent=2))
print('AUDIT',json.dumps({'meshes':len(meshes),'zeroArea':sum(m['zeroAreaFaces']for m in meshes),'resources':settings['resourceClosure']}))
