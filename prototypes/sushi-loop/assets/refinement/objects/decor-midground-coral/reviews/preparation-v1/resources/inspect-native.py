import bpy,json,pathlib,math
from mathutils import Vector
out=pathlib.Path(__file__).parent
col=bpy.data.collections['S33 production concept pink-coral.001']; root=bpy.data.objects['S33 production concept pink-coral root.001'];scene=bpy.context.scene
# Enable target before any evaluated samples.
def enable(lc):
 lc.exclude=False;lc.hide_viewport=False
 for c in lc.children: enable(c)
enable(bpy.context.view_layer.layer_collection)
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
bpy.context.view_layer.update()
def props(x):return {k:x[k] for k in x.keys()}
def matrix(m):return [list(r) for r in m]
def bounds(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh(); pts=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices]; ev.to_mesh_clear();return [[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)] if pts else []
objects=[]
for o in col.all_objects:
 a=o.animation_data.action if o.animation_data else None
 act=[]
 if a:
  for layer in a.layers:
   for st in layer.strips:
    for bag in st.channelbags:
     for fc in bag.fcurves:act.append({'path':fc.data_path,'index':fc.array_index,'keys':[[k.co.x,k.co.y,k.interpolation] for k in fc.keyframe_points]})
 objects.append({'name':o.name,'type':o.type,'props':props(o),'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':matrix(o.matrix_world),'matrixParentInverse':matrix(o.matrix_parent_inverse),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'smoothFaces':sum(p.use_smooth for p in o.data.polygons) if o.type=='MESH' else None,'uvLayers':list(o.data.uv_layers.keys()) if o.type=='MESH' else None,'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints],'action':a.name if a else None,'channels':act,'boundsRoot':bounds(o) if o.type=='MESH' else []})
mats=[]
for m in set(m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m):
 mats.append({'name':m.name,'library':m.library.filepath if m.library else None,'diffuseColor':list(m.diffuse_color),'props':props(m),'nodes':[{'name':n.name,'type':n.type,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and s.type not in ('STRING','SHADER','GEOMETRY')}} for n in m.node_tree.nodes] if m.use_nodes else [],'animation':m.animation_data.action.name if m.animation_data and m.animation_data.action else None,'nodeAnimation':m.node_tree.animation_data.action.name if m.use_nodes and m.node_tree.animation_data and m.node_tree.animation_data.action else None})
samples=[]
for frame in range(1,14):
 scene.frame_set(frame);bpy.context.view_layer.update();samples.append({'frame':frame,'root':matrix(root.matrix_world),'objects':[{'name':o.name,'rotation':list(o.rotation_euler),'boundsRoot':bounds(o)} for o in col.all_objects if o.type=='MESH']})
report={'collection':col.name,'collectionProps':props(col),'root':root.name,'rootProps':props(root),'objects':objects,'materials':mats,'samples':samples,'libraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries],'ownedImagePaths':[n['image'] for m in mats for n in m['nodes'] if n.get('image')],'savedCamera':{'name':scene.camera.name,'props':props(scene.camera),'matrix':matrix(scene.camera.matrix_world),'orthoScale':scene.camera.data.ortho_scale},'sceneProps':props(scene)}
(out/'native-inspection.json').write_text(json.dumps(report,indent=2,default=str))
print('INSPECTED',col.name,'objects',len(objects),'meshes',sum(o['type']=='MESH' for o in objects),'materials',len(mats),'sampled frames',len(samples))
