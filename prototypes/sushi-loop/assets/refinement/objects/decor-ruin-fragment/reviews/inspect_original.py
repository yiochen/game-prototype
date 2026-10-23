import bpy, json, math
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).parent
matching = [c for c in bpy.data.collections if 'reef-face' in c.name or 'decor-ruin-fragment' in c.name]
original_scenes = []
for s in bpy.data.scenes:
    cam = s.camera
    original_scenes.append({'name':s.name,'camera':cam.name if cam else None,'resolution':[s.render.resolution_x,s.render.resolution_y], 'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y], 'cameraData':{'ortho_scale':cam.data.ortho_scale,'shift_x':cam.data.shift_x,'shift_y':cam.data.shift_y,'matrix':[list(row) for row in cam.matrix_world]} if cam else None})
scene=bpy.data.scenes.new('judge inspection decor-ruin-fragment')
bpy.context.window.scene=scene
for col in matching:
    scene.collection.children.link(col)
bpy.context.view_layer.update()
def props(x):
    return {k:str(x[k]) for k in x.keys() if k != '_RNA_UI'}
def object_record(o):
    points=[o.matrix_world @ Vector(p) for p in o.bound_box] if o.type=='MESH' else []
    return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation_euler':list(o.rotation_euler),'scale':list(o.scale),'matrix':[list(row) for row in o.matrix_world], 'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'props':props(o),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]} if points else None,'vertexCount':len(o.data.vertices) if o.type=='MESH' else None,'materials':[{'name':m.name,'nodeTree':[(n.name,n.type) for n in m.node_tree.nodes] if m and m.use_nodes else None} for m in o.data.materials if m] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'animation':bool(o.animation_data),'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else []}
objects=list({o.name:o for c in matching for o in c.all_objects}.values())
mesh_points=[o.matrix_world @ v.co for o in objects if o.type=='MESH' for v in o.data.vertices]
report={'project':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'originalScenes':original_scenes,'collections':[{'name':c.name,'props':props(c)} for c in matching],'objects':[object_record(o) for o in objects],'aggregateMeshBounds':{'min':[min(p[i] for p in mesh_points) for i in range(3)],'max':[max(p[i] for p in mesh_points) for i in range(3)]} if mesh_points else None,'externalImages':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[x.filepath for x in bpy.data.libraries]}
(OUT/'original-native-inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'collections':report['collections'],'objectCount':len(objects),'aggregateMeshBounds':report['aggregateMeshBounds'],'originalScenes':original_scenes},indent=2))
