import sys,json,hashlib,math
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
P=Path(__file__).resolve().parent
scene=bpy.context.scene
root=next((o for o in scene.objects if o.get('production_id')=='floor-underwater'),None)
if root is None:root=next(o for o in scene.objects if o.type=='EMPTY' and 'floor-underwater' in o.name)
cols=list(root.users_collection);meshes=[o for o in scene.objects if o.type=='MESH'];materials={m for o in meshes for m in o.data.materials}
def val(v):
 try:return [val(x) for x in v]
 except TypeError:return v
def scalar(v):
 try:return list(v)
 except TypeError:return v if isinstance(v,(str,int,float,bool)) else str(v)
report={'blender':bpy.app.version_string,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':scene.name,'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale)},'camera':{'worldMatrix':[list(row) for row in scene.camera.matrix_world],'orthoScale':scene.camera.data.ortho_scale,'sensorFit':scene.camera.data.sensor_fit,'shifts':[scene.camera.data.shift_x,scene.camera.data.shift_y]},'capture':{'resolution':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'filter':scene.render.filter_size,'fps':scene.render.fps,'engine':scene.render.engine,'viewTransform':scene.view_settings.view_transform},'meshes':[],'materials':[],'actions':[],'frames':[],'lights':[],'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.type=='IMAGE'],'libraries':[x.filepath for x in bpy.data.libraries]}
for o in meshes:
 report['meshes'].append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'normals':[list(p.normal) for p in o.data.polygons],'uvLayers':[l.name for l in o.data.uv_layers],'modifiers':[m.type for m in o.modifiers]})
for m in materials:
 nodes=[]
 for n in m.node_tree.nodes:
  nodes.append({'name':n.name,'label':n.label,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':{f'{i}:{s.name}':scalar(s.default_value) for i,s in enumerate(n.inputs) if hasattr(s,'default_value') and not s.is_linked},'outputs':{s.name:scalar(s.default_value) for s in n.outputs if hasattr(s,'default_value')},'ramp':{'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements],'interpolation':n.color_ramp.interpolation} if hasattr(n,'color_ramp') else None})
 report['materials'].append({'name':m.name,'nodes':nodes,'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links],'animationAction':m.node_tree.animation_data.action.name if m.node_tree.animation_data and m.node_tree.animation_data.action else None})
for a in bpy.data.actions:
 curves=[]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for f in bag.fcurves:curves.append({'path':f.data_path,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'left':list(k.handle_left),'right':list(k.handle_right)} for k in f.keyframe_points]})
 report['actions'].append({'name':a.name,'range':list(a.frame_range),'curves':curves})
for frame in [1,1.5,2,4,7,12,12.5,13]:
 scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update();values={}
 for m in materials:
  for n in m.node_tree.nodes:
   for s in n.outputs:
    if hasattr(s,'default_value') and s.type=='VALUE':values[m.name+':'+n.name+':'+s.name]=s.default_value
 report['frames'].append({'frame':frame,'values':values})
for o in scene.objects:
 if o.type=='LIGHT':report['lights'].append({'name':o.name,'energy':o.data.energy,'type':o.data.type,'location':list(o.location),'color':list(o.data.color),'size':getattr(o.data,'size',None)})
(P/'native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
scene.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
native=P/'native-replay';native.mkdir(exist_ok=True)
for direction,rotation in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=rotation
 for frame in (1,7,13):
  scene.frame_set(frame);bpy.context.view_layer.update();scene.render.filepath=str(native/(direction+'-'+str(frame-1).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
print('INDEPENDENT_AUDIT_DONE',flush=True)
