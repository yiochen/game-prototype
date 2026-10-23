import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;R=P/'resources';S=R/'source/round-01.blend';s=bpy.context.scene;root=bpy.data.objects['decor-background-wreck__root.001'];objects=[root]+list(root.children_recursive);owned=set(objects)
# Respect the saved effective visibility, then enable owned ancestry for evaluated measurement.
visibility=[{'name':o.name,'type':o.type,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get(),'parent':o.parent.name if o.parent else None} for o in s.objects]
for col in bpy.data.collections:
 if any(o in owned for o in col.all_objects):col.hide_render=False;col.hide_viewport=False
for o in objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
def en(l):
 if any(o in owned for o in l.collection.all_objects):l.exclude=False;l.hide_viewport=False
 for q in l.children:en(q)
for vl in s.view_layers:en(vl.layer_collection)
def mat(m):return [list(row) for row in m]
def bound(v):return [[min(x[i] for x in v),max(x[i] for x in v)] for i in range(3)] if v else None
def temporal(x):
 ad=getattr(x,'animation_data',None)
 return {'owner':x.name,'type':x.bl_rna.identifier,'action':ad.action.name if ad and ad.action else None,'drivers':[{'path':f.data_path,'expression':f.driver.expression} for f in ad.drivers] if ad else [],'nla':[{'track':t.name,'strips':[{'name':q.name,'action':q.action.name if q.action else None} for q in t.strips]} for t in ad.nla_tracks] if ad else []}
seen=set();owners=[]
def add(x):
 if not x:return
 key=x.as_pointer()
 if key in seen:return
 seen.add(key);owners.append(temporal(x))
 if hasattr(x,'node_tree') and x.node_tree:add(x.node_tree)
 if isinstance(x,bpy.types.NodeTree):
  for n in x.nodes:
   if n.type=='GROUP':add(n.node_tree)
add(s);add(s.world);add(s.camera);add(s.camera.data);add(getattr(s,'compositing_node_group',None))
for o in objects:
 add(o);add(o.data)
 if o.type=='MESH':
  add(o.data.shape_keys)
  for slot in o.material_slots:add(slot.material)
for o in s.objects:
 if o.type=='LIGHT':add(o);add(o.data)
records=[];holds=[];topology=[];restRaw=[];restEval=[];trees={};allvert={}
root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
for o in objects:
 if o.type!='MESH':continue
 raw=[o.matrix_world@v.co for v in o.data.vertices];restRaw+=raw;ev=o.evaluated_get(dg);me=ev.to_mesh();verts=[ev.matrix_world@v.co for v in me.vertices];restEval+=verts;faces=[list(f.vertices) for f in me.polygons];trees[o.name]=BVHTree.FromPolygons(verts,faces);allvert[o.name]=verts
 bm=bmesh.new();bm.from_mesh(me);topology.append({'object':o.name,'meshUsers':o.data.users,'rawVertices':len(raw),'evaluatedVertices':len(verts),'rawBounds':bound(raw),'evaluatedBounds':bound(verts),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'evaluatedSignedVolume':bm.calc_volume(signed=True),'modifiers':[{'name':m.name,'type':m.type,'render':m.show_render} for m in o.modifiers],'uvLayers':[u.name for u in o.data.uv_layers],'hasCustomNormals':o.data.has_custom_normals,'smoothPolygons':sum(f.use_smooth for f in o.data.polygons),'flatPolygons':sum(not f.use_smooth for f in o.data.polygons),'groundIntersectionFaces':sum(min(verts[i].z for i in f)<=0<=max(verts[i].z for i in f) for f in faces),'imageNodes':[n.image.name for sl in o.material_slots if sl.material and sl.material.node_tree for n in sl.material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]});bm.free();ev.to_mesh_clear()
intersections=[]
for i,(a,ta) in enumerate(trees.items()):
 for b,tb in list(trees.items())[i+1:]:
  overlap=ta.overlap(tb)
  if overlap:intersections.append({'a':a,'b':b,'surfaceTriangleIntersectionPairs':len(overlap)})
# Saved-source replays use exactly its saved camera,lights,filter and color recipe; only proper root direction/filepath/frame are changed.
cam=s.camera;dg=bpy.context.evaluated_depsgraph_get()
def px(v):
 p=world_to_camera_view(s,cam,Vector(v));return [p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
for d,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(degrees);s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();raw=[];evaluated=[]
 for o in objects:
  if o.type!='MESH':continue
  raw.extend(o.matrix_world@v.co for v in o.data.vertices);ev=o.evaluated_get(dg);me=ev.to_mesh();evaluated.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
 path=P/'replay'/f'{d}.png';path.parent.mkdir(exist_ok=True);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'direction':d,'nativeFrame':1,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':mat(root.matrix_world),'cameraWorldMatrix':mat(cam.matrix_world),'projectionMatrix':mat(cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)),'rootPixels':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1)),'rawBounds':bound(raw),'evaluatedBounds':bound(evaluated),'path':str(path.relative_to(P))})
root.rotation_euler.z=0
for f in [1,2,12,25]:
 s.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();parts={}
 for o in objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();v=[list(ev.matrix_world@q.co) for q in me.vertices];parts[o.name]={'matrix':mat(o.matrix_world),'geometry':hashlib.sha256(json.dumps(v).encode()).hexdigest(),'visible':not o.hide_render};ev.to_mesh_clear()
 holds.append({'nativeFrame':f,'seconds':(f-1)/12,'parts':parts})
settings={'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'cameraType':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'filterSize':s.render.filter_size,'motionBlur':s.render.use_motion_blur,'fps':s.render.fps,'fpsBase':s.render.fps_base,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'transparent':s.render.film_transparent,'cycles':{k:getattr(s.cycles,k) for k in ['samples','seed','use_denoising','pixel_filter_type','filter_width','use_animated_seed']},'compositor':{'useNodes':s.use_nodes,'group':getattr(s,'compositing_node_group',None).name if getattr(s,'compositing_node_group',None) else None},'lights':[{'name':o.name,'type':o.data.type,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':getattr(o.data,'size',None),'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT']}
report={'asset':'decor-background-wreck','candidatePacketSHA256':'f9524d3dffbb1bf59c29cfa9d634e2e438ed46f40731651e322a8081844a254c','savedSourceSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'savedScene':s.name,'effectiveSavedObjects':visibility,'ownedObjects':[o.name for o in objects],'restRawBounds':bound(restRaw),'restEvaluatedBounds':bound(restEval),'topology':topology,'nativeOwnedSurfaceIntersections':intersections,'captureRecords':records,'staticOwners':owners,'staticHolds':holds,'staticHoldGeometryMatrixVisibilityEqual':all(v['parts']==holds[0]['parts'] for v in holds[1:]),'settings':settings,'externalLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'fileSaved':False}
(P/'independent-native-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('INDEPENDENT NATIVE AUDIT AND4SOURCE REPLAYS COMPLETE')
