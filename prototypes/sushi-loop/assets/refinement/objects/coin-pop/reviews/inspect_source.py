"""Independent read-only source audit; outputs only to coin-pop/reviews/."""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parent
BASE=OUT.parent
ROOT=BASE.parents[5]
def val(x):
    if isinstance(x,(str,int,float,bool)) or x is None:return x
    try:return list(x)
    except:return str(x)
def props(obj):return {k:val(v) for k,v in obj.items()}
def mat(m):
    nt=m.node_tree
    return {'name':m.name,'properties':props(m),'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'label':n.label,'properties':props(n),'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'ramps':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in nt.nodes] if nt else [],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links] if nt else []}
scenes=[s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33]
if len(scenes)!=1:raise RuntimeError([s.name for s in scenes])
sc=scenes[0]
bpy.context.window.scene=sc
rig=json.loads((BASE/'inputs/source-rig.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
cols=[c for c in sc.collection.children if root in list(c.all_objects)]
if len(cols)!=1:raise RuntimeError([c.name for c in cols])
col=cols[0]
objects=list(col.all_objects)
def reveal_layers(layer):
    layer.exclude=False
    for child in layer.children:reveal_layers(child)
reveal_layers(sc.view_layers[0].layer_collection)
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
col.hide_render=False;col.hide_viewport=False
bpy.context.window.view_layer=sc.view_layers[0]
bpy.context.view_layer.update()
record={'blenderVersion':bpy.app.version_string,'sourceBlend':bpy.data.filepath,'sourceBlendSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'nativeScene':sc.name,'sceneProperties':props(sc),'collection':col.name,'collectionProperties':props(col),'sceneSavedCamera':sc.camera.name if sc.camera else None,'sceneSavedRender':{'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'transparent':sc.render.film_transparent},'root':{'name':root.name,'properties':props(root),'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale),'matrixWorld':[list(r) for r in root.matrix_world]},'objects':[],'materials':[],'cameras':[{'name':o.name,'dataType':o.data.type,'properties':props(o),'location':list(o.location),'rotation':list(o.rotation_euler),'matrixWorld':[list(r) for r in o.matrix_world],'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'sensorFit':o.data.sensor_fit} for o in sc.objects if o.type=='CAMERA'],'lights':[{'name':o.name,'properties':props(o),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'location':list(o.location),'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'actionBinding':[]}
for o in objects:
    ad=o.animation_data
    record['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'properties':props(o),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],'action':ad.action.name if ad and ad.action else None,'constraints':[{'name':c.name,'type':c.type} for c in o.constraints]})
record['materials']=[mat(m) for m in {slot.material for o in objects if o.type=='MESH' for slot in o.material_slots if slot.material}]
# Bind exact saved native actions without importing scripts that create export paths.
for target in rig['clips']['pop']['actions']:
    o=bpy.data.objects[target['ownerName']]
    action=bpy.data.actions[target['action']]
    o.animation_data_create();o.animation_data.action=action
    if hasattr(action,'slots'):
        slot=next((s for s in action.slots if s.identifier==target.get('slotIdentifier')),None)
        if slot:o.animation_data.action_slot=slot
    for t in o.animation_data.nla_tracks:t.mute=True
    curves=[]
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                curves += [{'dataPath':f.data_path,'index':f.array_index,'keys':[[kp.co.x,kp.co.y,kp.interpolation] for kp in f.keyframe_points]} for f in bag.fcurves]
    record['actionBinding'].append({'owner':o.name,'action':action.name,'frameRange':list(action.frame_range),'curves':curves})
# Reconstruct the asset's documented camera exactly in memory, separate from the unrelated saved active camera.
camrec=json.loads((BASE/'inputs/source-camera.json').read_text())
cam=bpy.data.objects.new('JUDGE coin-pop registered camera',bpy.data.cameras.new('JUDGE coin-pop registered camera'))
sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=192/128
cam.matrix_world=Matrix(camrec['camera']['worldMatrix'])
cam.data.shift_x=0;cam.data.shift_y=camrec['camera']['projectionMatrix'][1][3]/2
sc.render.resolution_x=384;sc.render.resolution_y=704;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=camrec['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
sc.render.fps=12;sc.render.film_transparent=True
def px(v):
    p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*704]
bpy.context.view_layer.update()
# The projection translation encodes a different camera shift convention; solve the exact registered root as capture_runtime does.
cam.data.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0))
cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1]
cam.data.shift_y=(512-base[1])/dy;bpy.context.view_layer.update()
record['registeredCamera']={'name':cam.name,'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'matrixWorld':[list(r) for r in cam.matrix_world],'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,704],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1))}
record['frames']=[]
# Camera-facing coins have actual counterrotation constraints; record resulting geometry under all facings.
for direction,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle
    for i in range(12):
        sc.frame_set(i+1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        per=[];allpts=[]
        for o in objects:
            if o.type!='MESH':continue
            eo=o.evaluated_get(dg);mesh=eo.to_mesh();points=[eo.matrix_world@v.co for v in mesh.vertices];eo.to_mesh_clear()
            allpts+=points
            per.append({'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'worldOrigin':list(o.matrix_world.translation),'bounds':[[min(p[a] for p in points) for a in range(3)],[max(p[a] for p in points) for a in range(3)]],'projectedBounds':[[min(px(p)[a] for p in points) for a in range(2)],[max(px(p)[a] for p in points) for a in range(2)]]})
        record['frames'].append({'direction':direction,'index':i,'nativeFrame':i+1,'phase':i/11,'bounds':[[min(p[a] for p in allpts) for a in range(3)],[max(p[a] for p in allpts) for a in range(3)]],'projectedBounds':[[min(px(p)[a] for p in allpts) for a in range(2)],[max(px(p)[a] for p in allpts) for a in range(2)]],'objects':per})
record['drivers']=[{'owner':o.name,'dataPath':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path} for t in v.targets]} for v in f.driver.variables]} for o in objects if o.animation_data for f in o.animation_data.drivers]
record['worldNodes']=[{'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in sc.world.node_tree.nodes] if sc.world and sc.world.use_nodes else []
record['compositor']={'name':sc.compositing_node_group.name,'properties':props(sc.compositing_node_group),'nodes':[{'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in sc.compositing_node_group.nodes]} if sc.compositing_node_group else None
(OUT/'source-inspection-raw.json').write_text(json.dumps(record,indent=2)+'\n')
if '--render' in sys.argv:
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1408
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    root.rotation_euler.z=0
    for i in (0,5,11):
        sc.frame_set(i+1);bpy.context.view_layer.update()
        sc.render.filepath=str(OUT/f'original-native-pop-S-{i:02d}-4x.png')
        bpy.ops.render.render(write_still=True,scene=sc.name)
print('JUDGE_SOURCE_AUDIT_COMPLETE',col.name,len(objects),len(record['frames']))
