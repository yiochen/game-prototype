"""Read-only native rock audit and registered source replay; never saves a blend."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
OBJ=HERE.parent.parent
INPUT=OBJ/'inputs'
SC=bpy.context.scene
COL=bpy.data.collections['S33 production concept cobalt-shelf.001']
ROOT=bpy.data.objects['S33 production concept cobalt-shelf root.001']
OWN=list(COL.all_objects)
CAM=SC.camera
def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    if hasattr(v,'to_list'):return v.to_list()
    try:return [plain(x) for x in v]
    except:return str(v)
def props(o):return {k:plain(o[k]) for k in o.keys() if k!='_RNA_UI'}
def mat(m):return plain(m)
def bounds(points):return {'min':[min(p[a] for p in points) for a in range(3)],'max':[max(p[a] for p in points) for a in range(3)]}
def animation(o):
    ad=getattr(o,'animation_data',None)
    if not ad:return None
    return {'action':ad.action.name if ad.action else None,'drivers':[{'dataPath':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in ad.drivers],
            'nla':[{'name':t.name,'mute':t.mute,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'start':s.frame_start,'end':s.frame_end} for s in t.strips]} for t in ad.nla_tracks]}
def tree(t):
    if not t:return None
    return {'name':t.name,'animation':animation(t),'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),
            'inputs':{f'{i}:{s.name}':plain(s.default_value) for i,s in enumerate(n.inputs) if hasattr(s,'default_value')},
            'ramp':[{'pos':e.position,'color':plain(e.color)} for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None,
            'image':n.image.name if hasattr(n,'image') and n.image else None,
            'group':tree(n.node_tree) if n.type=='GROUP' else None} for n in t.nodes],
            'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in t.links]}
saved={'frame':SC.frame_current,'camera':CAM.name,'cameraMatrix':mat(CAM.matrix_world),'orthoScale':CAM.data.ortho_scale,'shift':[CAM.data.shift_x,CAM.data.shift_y],
       'resolution':[SC.render.resolution_x,SC.render.resolution_y,SC.render.resolution_percentage],'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],
       'settings':{'engine':SC.render.engine,'filterSize':SC.render.filter_size,'fps':SC.render.fps,'view':SC.view_settings.view_transform,'look':SC.view_settings.look,'exposure':SC.view_settings.exposure,'gamma':SC.view_settings.gamma,'filmTransparent':SC.render.film_transparent,'dither':SC.render.dither_intensity},
       'collection':{'name':COL.name,'hideRender':COL.hide_render,'hideViewport':COL.hide_viewport},
       'startup':{k:props(SC).get(k) for k in ['startup_asset','startup_clip','startup_frame','s33Lighting','source_library_sha256']}}
# Enable the real collection ancestry, actual objects and actual view layer before measurement.
def enable_ancestry(lc):
    hit=lc.collection==COL
    for c in lc.children:hit=enable_ancestry(c) or hit
    if hit:lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_render=False;lc.collection.hide_viewport=False
    return hit
for vl in SC.view_layers:enable_ancestry(vl.layer_collection)
for o in SC.objects:
    if o.type=='MESH':o.hide_render=o not in OWN
for o in OWN:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
SC.frame_set(1);bpy.context.view_layer.update()
DG=bpy.context.evaluated_depsgraph_get();DG.update()
records=[];raw_all=[];eval_all=[];geometry={}
for o in OWN:
    r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':plain(o.location),'rotationEuler':plain(o.rotation_euler),'scale':plain(o.scale),'matrixWorld':mat(o.matrix_world),'properties':props(o),'animation':animation(o),
       'constraints':[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],
       'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]}
    if o.type=='MESH':
        raw=[o.matrix_world@v.co for v in o.data.vertices];raw_all+=raw
        ev=o.evaluated_get(DG);mesh=ev.to_mesh();evaluated=[ev.matrix_world@v.co for v in mesh.vertices];eval_all+=evaluated
        edges={tuple(sorted(e.vertices)):0 for e in o.data.edges}
        for p in o.data.polygons:
            for edge in p.edge_keys:edges[tuple(sorted(edge))]=edges.get(tuple(sorted(edge)),0)+1
        r.update(rawAuthoredBounds=bounds(raw),evaluatedBounds=bounds(evaluated),vertices=len(raw),evaluatedVertices=len(evaluated),polygons=len(o.data.polygons),
                 boundaryEdges=sum(n==1 for n in edges.values()),nonManifoldEdges=sum(n!=2 for n in edges.values()),
                 uvLayers=[u.name for u in o.data.uv_layers],shapeKeys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
                 dataAnimation=animation(o.data),shapeAnimation=animation(o.data.shape_keys) if o.data.shape_keys else None,
                 customNormals=o.data.has_custom_normals,smoothPolygons=sum(p.use_smooth for p in o.data.polygons),
                 materialSlots=[m.name if m else None for m in o.data.materials],materialUsers={m.name:m.users for m in o.data.materials if m})
        geometry[o.name]={'rawWorldVertices':[plain(p) for p in raw],'rawPolygons':[{'verts':list(p.vertices),'materialIndex':p.material_index,'normal':plain(p.normal)} for p in o.data.polygons],
                          'evaluatedWorldVertices':[plain(p) for p in evaluated],
                          'groundContactFaces':[list(p.vertices) for p in o.data.polygons if all(abs(raw[i].z)<1e-6 for i in p.vertices)]}
        ev.to_mesh_clear()
    records.append(r)
materials={m.name:{'diffuseColor':plain(m.diffuse_color),'users':m.users,'animation':animation(m),'tree':tree(m.node_tree)} for o in OWN if o.type=='MESH' for m in o.data.materials if m}
lights=[{'name':o.name,'matrixWorld':mat(o.matrix_world),'hideRender':o.hide_render,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'color':plain(o.data.color),'animation':animation(o),'dataAnimation':animation(o.data)} for o in SC.objects if o.type=='LIGHT']
camera=json.loads((INPUT/'source-camera.json').read_text())
SC.render.resolution_x=192*4;SC.render.resolution_y=352*4;SC.render.resolution_percentage=100
SC.render.pixel_aspect_x=camera['camera']['pixelAspect'][0];SC.render.pixel_aspect_y=camera['camera']['pixelAspect'][1]
CAM.matrix_world=Matrix(camera['camera']['worldMatrix']);CAM.data.type='ORTHO';CAM.data.sensor_fit='HORIZONTAL';CAM.data.ortho_scale=1.5;CAM.data.shift_x=0;CAM.data.shift_y=0
def px(p):
    v=world_to_camera_view(SC,CAM,Vector(p));return Vector((v.x*SC.render.resolution_x,(1-v.y)*SC.render.resolution_y))
bpy.context.view_layer.update();base=px((0,0,0));CAM.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;CAM.data.shift_y=(1024-base.y)/dy;bpy.context.view_layer.update()
SC.render.film_transparent=True;SC.render.image_settings.file_format='PNG';SC.render.image_settings.color_mode='RGBA';SC.render.image_settings.color_depth='8'
SC.render.image_settings.compression=100;SC.render.fps=12;SC.render.dither_intensity=0
calroot=px((0,0,0));cal={'root':plain(calroot),'unitX':plain(px((1,0,0))-calroot),'unitDepth':plain(px((0,-1,0))-calroot),'unitHeight':plain(px((0,0,1))-calroot)}
captures=[]
for direction,degrees in [('S',0),('E',90),('N',180),('W',-90)]:
    ROOT.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
    native=HERE/'native'/direction/'000.png';native.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(native)
    bpy.ops.render.render(write_still=True)
    captures.append({'direction':direction,'clip':'static','frameIndex':0,'nativeFrame':1,'rootRotationZ':ROOT.rotation_euler.z,'rootRotationDegrees':math.degrees(ROOT.rotation_euler.z),'actualRootMatrix':mat(ROOT.matrix_world),'path':str(native.relative_to(OBJ)),'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()})
    print('CAPTURED_SOURCE',direction,flush=True)
ROOT.rotation_euler.z=0;bpy.context.view_layer.update()
record={'asset':'decor-background-rock','status':'source-only preparation; no candidate','blender':bpy.app.version_string,'source':bpy.data.filepath,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'savedScene':saved,
        'enabledCollection':COL.name,'root':{'name':ROOT.name,'matrixWorldS':mat(ROOT.matrix_world),'properties':props(ROOT)},'objects':records,'rawAuthoredBounds':bounds(raw_all),'evaluatedBounds':bounds(eval_all),'geometry':geometry,'materials':materials,'lights':lights,'world':tree(SC.world.node_tree),
        'sceneTemporal':animation(SC),'worldTemporal':animation(SC.world),'cameraTemporal':animation(CAM),'cameraDataTemporal':animation(CAM.data),
        'replayCamera':{'name':CAM.name,'worldMatrix':mat(CAM.matrix_world),'orthoScale':CAM.data.ortho_scale,'shift':[CAM.data.shift_x,CAM.data.shift_y],'projectionMatrix':mat(CAM.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=SC.render.resolution_x,y=SC.render.resolution_y,scale_x=SC.render.pixel_aspect_x,scale_y=SC.render.pixel_aspect_y)),'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],'frame':[768,1408],'captureScale':4,'filterSize':SC.render.filter_size,'calibration':cal},'captureRecords':captures,
        'externalResources':{'libraries':[l.filepath for l in bpy.data.libraries],'ownedImageTextures':[n.image.filepath for m in materials for n in bpy.data.materials[m].node_tree.nodes if n.type=='TEX_IMAGE' and n.image]},
        'replayNotes':['Only actual source collection visibility, source static frame1/root cardinal rotations and registered camera/raster were changed in memory. No blend saved. Saved active camera is unrelated and recorded separately.','Material, topology, normals, original lighting, filter, world and color management are preserved from native source.']}
(HERE/'source-audit.json').write_text(json.dumps(record,indent=2)+'\n')
print('WROTE_SOURCE_AUDIT',flush=True)
