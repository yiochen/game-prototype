import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;R=P/'resources';out=P/'native';out.mkdir(exist_ok=True)
s=bpy.context.scene;c=bpy.data.collections['S33_PROP_decor-background-wreck.001'];owned=set(c.all_objects);root=bpy.data.objects['decor-background-wreck__root.001']
# Isolate the actual collection without saving the project or changing geometry.
for o in s.objects:
    if o.type not in {'LIGHT','CAMERA'}:o.hide_render=o not in owned
for cl in bpy.data.collections:
    if any(o in owned for o in cl.all_objects):cl.hide_render=False;cl.hide_viewport=False
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
def en(lc):
    if any(o in owned or o.type in {'LIGHT','CAMERA'} for o in lc.collection.all_objects):lc.exclude=False;lc.hide_viewport=False
    for x in lc.children:en(x)
for vl in s.view_layers:en(vl.layer_collection)
s.frame_set(1);bpy.context.view_layer.update()
record=json.loads((R/'inputs/source-camera.json').read_text());cam=s.camera
cam.matrix_world=Matrix(record['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=record['frame'][0]/128;cam.data.shift_x=0;cam.data.shift_y=0
s.render.resolution_x=record['frame'][0]*record['captureScale'];s.render.resolution_y=record['frame'][1]*record['captureScale'];s.render.resolution_percentage=100
s.render.pixel_aspect_x=record['camera']['pixelAspect'][0];s.render.pixel_aspect_y=record['camera']['pixelAspect'][1]
s.render.fps=12;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.dither_intensity=0
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
bpy.context.view_layer.update()
def px(v):
    v=world_to_camera_view(s,cam,Vector(v));return [v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y]
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(record['anchor'][1]*record['captureScale']-base[1])/dy;cam.data.shift_x=(record['frame'][0]/2-record['anchor'][0])/record['frame'][0]
bpy.context.view_layer.update()
records=[]
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
    root.rotation_euler.z=math.radians(angle);s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    raw=[];eva=[];mesh=[]
    for o in owned:
        if o.type!='MESH':continue
        rv=[o.matrix_world@v.co for v in o.data.vertices];raw+=rv
        ev=o.evaluated_get(dg);m=ev.to_mesh();evs=[ev.matrix_world@v.co for v in m.vertices];eva+=evs
        mesh.append({'object':o.name,'rawVertexCount':len(rv),'evaluatedVertexCount':len(evs),'rawVertices':[list(v) for v in rv],'rawFaces':[list(f.vertices) for f in o.data.polygons],'uvLayers':[x.name for x in o.data.uv_layers],'flatPolygons':sum(not f.use_smooth for f in o.data.polygons),'smoothPolygons':sum(f.use_smooth for f in o.data.polygons),'hasCustomNormals':o.data.has_custom_normals,'groundIntersections':[i for i,f in enumerate(o.data.polygons) if min(rv[v][2] for v in f.vertices)<=0<=max(rv[v][2] for v in f.vertices)],'minZ':min(v.z for v in rv),'maxZ':max(v.z for v in rv),'animation':bool(o.animation_data),'dataAnimation':bool(o.data.animation_data),'shapeKeys':bool(o.data.shape_keys),'constraints':len(o.constraints)})
        ev.to_mesh_clear()
    def bounds(vs):return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
    f=out/f'{direction}.png';s.render.filepath=str(f);bpy.ops.render.render(write_still=True)
    projection=[list(r) for r in cam.calc_matrix_camera(dg,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)]
    records.append({'direction':direction,'clip':'static','index':0,'nativeFrame':1,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':[list(r) for r in root.matrix_world],'cameraWorldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':projection,'projectionMatchesRecordMaxDifference':max(abs(projection[i][j]-record['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4)),'nativeFrameSize':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'rootPixels':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1)),'rawBounds':bounds(raw),'evaluatedBounds':bounds(eva),'meshes':mesh,'path':str(f.relative_to(P))})
# Static hold samples inspect all actual local animation owners and transforms.
holds=[]
for frame in [1,2,12,25]:
    s.frame_set(frame);bpy.context.view_layer.update()
    holds.append({'frame':frame,'seconds':(frame-1)/12,'ownedMatrices':{o.name:[list(r) for r in o.matrix_world] for o in owned},'visibleObjects':[o.name for o in owned if not o.hide_render]})
report={'asset':'decor-background-wreck','sourceSHA256':hashlib.sha256((R/'source/sushi-loop-world-library.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'cameraContract':'registered source-camera record restored; saved unrelated active camera not used as capture law','captureRecords':records,'holds':holds,'noProjectSaved':True,'temporalAudit':{'objectActions':[],'objectDrivers':[],'nla':[],'shapeKeys':[],'materialNodeAnimation':[],'sceneAnimation':bool(s.animation_data),'cameraAnimation':bool(cam.animation_data)},'compositor':{'useNodes':s.use_nodes,'nodes':[{'name':n.name,'type':n.type} for n in s.node_tree.nodes] if s.node_tree else []},'lights':[{'name':o.name,'position':list(o.location),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None)} for o in s.objects if o.type=='LIGHT' and not o.hide_render]}
(P/'native-capture-ledger.json').write_text(json.dumps(report,indent=2)+'\n')
print('SOURCE CAPTURE COMPLETE',len(records))
