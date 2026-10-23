import sys
sys.dont_write_bytecode=True
import bpy, json, math, hashlib, importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets')
OBJ=BASE/'refinement/objects/garbage-shelving'; OUT=OBJ/'reviews/source-audit'; SRC=Path(__file__).resolve().parent/'resources'
def plain(x):
    if isinstance(x,(str,int,float,bool)) or x is None:return x
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    try:return [plain(v) for v in x]
    except:return str(x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
root=bpy.data.objects['garbage-shelving__root']
scenes=[s for s in bpy.data.scenes if root.name in s.objects]
scene=next((s for s in scenes if s.get('source')=='native_actions.py'),scenes[0])
bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
collection=next(c for c in scene.collection.children if root in list(c.all_objects))
for layer in scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=collection
for c in scene.collection.children:c.hide_render=c!=collection;c.hide_viewport=c!=collection
record=json.loads((OBJ/'inputs/source-rig.json').read_text());asset=json.loads((OBJ/'inputs/source-assetRecord.json').read_text());asset.update(root=root,collection=collection)
initial_saved={'scene':scene.name,'sceneProperties':plain(dict(scene.items())),'activeSavedCamera':scene.camera.name if scene.camera else None,'savedCamera':{'matrix':plain(scene.camera.matrix_world),'orthoScale':scene.camera.data.ortho_scale,'shiftY':scene.camera.data.shift_y} if scene.camera else None,'savedRender':[scene.render.resolution_x,scene.render.resolution_y,scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]}
actions=mod('gs_audit_actions',SRC/'native_actions.py');runtime=mod('gs_audit_runtime',SRC/'capture_runtime.py');runtime.scene=lambda:scene;runtime.SCENE_NAME=scene.name
cam_record=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),2)
scene.render.image_settings.compression=15
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
objects=list(collection.all_objects)
materials={s.material for o in objects if o.type=='MESH' for s in o.material_slots if s.material}
def material_info(m):
    return {'name':m.name,'properties':plain(dict(m.items())),'useNodes':m.use_nodes,'surfaceRenderMethod':getattr(m,'surface_render_method',None),'diffuseColor':plain(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'label':n.label,'image':n.image.filepath if hasattr(n,'image') and n.image else None,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes] if m.node_tree else [],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links] if m.node_tree else []}
def fcurves(act):return list(actions._fcurves(act))
rawactions=[]
for clip,v in record['clips'].items():
    for entry in v['actions']:
        a=bpy.data.actions[entry['action']]
        rawactions.append({'clip':clip,**entry,'properties':plain(dict(a.items())),'curves':[{'dataPath':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]} for f in fcurves(a)]})
objinfo=[]
for o in objects:
    objinfo.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'properties':plain(dict(o.items())),'rotationMode':o.rotation_mode,'matrixParentInverse':plain(o.matrix_parent_inverse),'modifiers':[{'name':m.name,'type':m.type,'target':getattr(getattr(m,'object',None),'name',None),'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],'constraints':[{'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],'meshVertices':len(o.data.vertices) if o.type=='MESH' else None,'meshFaces':len(o.data.polygons) if o.type=='MESH' else None,'uvLayers':[v.name for v in o.data.uv_layers] if o.type=='MESH' else [],'shapeKeys':[k.name for k in o.data.shape_keys.key_blocks] if o.type=='MESH' and o.data.shape_keys else [],'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'drivers':[d.data_path for d in o.animation_data.drivers] if o.animation_data else []})
phases=[]
for direction in ['S','E','N','W']:
    for clip,config in record['clips'].items():
        frames=list(range(1,config['frames']+1))+([13] if clip=='highlighted' else [])
        for frame in frames:
            actions.apply_clip(asset,record,clip,frame,direction,scene)
            deps=bpy.context.evaluated_depsgraph_get();allverts=[];perobject=[]
            for o in objects:
                state={'name':o.name,'location':plain(o.location),'rotationEuler':plain(o.rotation_euler),'scale':plain(o.scale),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'matrixWorld':plain(o.matrix_world)}
                if o.type=='MESH':
                    eo=o.evaluated_get(deps);mesh=eo.to_mesh();verts=[eo.matrix_world@v.co for v in mesh.vertices];local=[root.matrix_world.inverted()@v for v in verts];allverts+=verts
                    state.update(evaluatedVertexCount=len(verts),boundsMin=[min(v[i] for v in verts) for i in range(3)],boundsMax=[max(v[i] for v in verts) for i in range(3)],rootLocalMin=[min(v[i] for v in local) for i in range(3)],rootLocalMax=[max(v[i] for v in local) for i in range(3)],worldVertexSHA256=hashlib.sha256(json.dumps([list(v) for v in verts]).encode()).hexdigest(),meshLocalSHA256=hashlib.sha256(json.dumps([list(v.co) for v in mesh.vertices]).encode()).hexdigest())
                    eo.to_mesh_clear()
                perobject.append(state)
            projections=[world_to_camera_view(scene,scene.camera,v) for v in allverts]
            phase={'direction':direction,'clip':clip,'frame1':frame,'frame0':frame-1,'closureDiagnostic':frame==13,'root':{'location':plain(root.location),'rotation':plain(root.rotation_euler),'scale':plain(root.scale),'matrix':plain(root.matrix_world)},'boundsMin':[min(v[i] for v in allverts) for i in range(3)],'boundsMax':[max(v[i] for v in allverts) for i in range(3)],'projectedNativeBounds':[min(p.x*896 for p in projections),min((1-p.y)*1344 for p in projections),max(p.x*896 for p in projections),max((1-p.y)*1344 for p in projections)],'objects':perobject}
            phases.append(phase)
            if frame!=13:
                folder=OUT/'native-original'/f'{clip}-{direction}';folder.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(folder/f'{frame-1:03d}.png');bpy.ops.render.render(write_still=True,scene=scene.name)
                print('GS_RENDER',direction,clip,frame,flush=True)
            (OUT/'native-phases.partial.json').write_text(json.dumps(phases,indent=2)+'\n')
resources=[]
for m in materials:
    for n in m.node_tree.nodes:
        if hasattr(n,'image') and n.image:resources.append({'material':m.name,'node':n.name,'name':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file)})
report={'asset':'garbage-shelving','blenderVersion':bpy.app.version_string,'blendFile':bpy.data.filepath,'blendSHA256':sha(bpy.data.filepath),'savedStateBeforeCapture':initial_saved,'scene':scene.name,'collection':collection.name,'cameraRecord896':cam_record,'cameraObject':scene.camera.name,'cameraData':{'type':scene.camera.data.type,'orthoScale':scene.camera.data.ortho_scale,'shiftX':scene.camera.data.shift_x,'shiftY':scene.camera.data.shift_y,'sensorFit':scene.camera.data.sensor_fit,'clipStart':scene.camera.data.clip_start,'clipEnd':scene.camera.data.clip_end},'rootProperties':plain(dict(root.items())),'objects':objinfo,'materials':[material_info(m) for m in sorted(materials,key=lambda m:m.name)],'resources':resources,'libraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries],'lights':[{'name':o.name,'position':plain(o.location),'rotation':plain(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':plain(o.data.color),'type':o.data.type} for o in scene.objects if o.type=='LIGHT'],'world':{'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in scene.world.node_tree.nodes]},'render':{'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'filmTransparent':scene.render.film_transparent,'fps':scene.render.fps,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,'compositor':scene.compositing_node_group.name if scene.compositing_node_group else None},'actions':rawactions,'phases':phases,'readOnlySource':True}
(OUT/'native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('GS_AUDIT_DONE',flush=True)
