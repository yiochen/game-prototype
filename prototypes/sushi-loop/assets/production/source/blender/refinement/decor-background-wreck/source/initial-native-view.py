import bpy, os, json

OUT = os.path.dirname(os.path.realpath(__file__))
COLLECTION = 'S33_PROP_decor-background-wreck.001'
col = bpy.data.collections[COLLECTION]
own = set(col.all_objects)
scene = bpy.context.scene

def enable(layer):
    layer.exclude = False
    layer.hide_viewport = False
    for child in layer.children:
        enable(child)

for c in bpy.data.collections:
    c.hide_viewport = False
    c.hide_render = False
for vl in scene.view_layers:
    enable(vl.layer_collection)
for o in scene.objects:
    if o.type not in {'LIGHT','CAMERA'}:
        o.hide_render = o not in own
    if o in own:
        o.hide_viewport = False
        o.hide_set(False)
bpy.context.view_layer.update()
bpy.context.evaluated_depsgraph_get().update()
# Diagnostic isolation only: native camera, dimensions, materials, mesh data,
# object transforms, lighting, world and color management are unchanged.
scene.render.filepath = os.path.join(OUT,'initial-native-view.png')
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
bpy.ops.render.render(write_still=True)
print('Unsaved untouched-native isolation render', scene.render.filepath)
