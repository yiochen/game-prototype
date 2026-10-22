import bpy,json,math,hashlib
from mathutils import Vector
from pathlib import Path
out=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/decor-starfish/reviews/source-inspection.json')
scene=bpy.context.scene
# Select the actual source collection for dependency evaluation only, without saving.
for c in bpy.data.collections:
    c.hide_viewport=False
for layer in scene.view_layers:
    def enable(lc):
        lc.exclude=False
        lc.hide_viewport=False
        for child in lc.children: enable(child)
    enable(layer.layer_collection)
bpy.context.view_layer.update()
def mat(m):return [[round(float(v),9) for v in row] for row in m]
def bounds(objs):
    pts=[o.matrix_world@Vector(c) for o in objs if o.type=='MESH' for c in o.bound_box]
    if not pts:return None
    mn=[min(p[i] for p in pts) for i in range(3)];mx=[max(p[i] for p in pts) for i in range(3)]
    return {'min':mn,'max':mx,'size':[mx[i]-mn[i] for i in range(3)]}
cols=[c for c in bpy.data.collections if 'starfish' in c.name.lower()]
records=[]
for c in cols:
    obs=list(c.all_objects)
    entries=[]
    for o in obs:
        entries.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':mat(o.matrix_world),'bounds':bounds([o]),'hideRender':o.hide_render,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'vertexCount':len(o.data.vertices) if o.type=='MESH' else None,'polygonCount':len(o.data.polygons) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'customProperties':{k:str(v) for k,v in o.items()},'actions':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'shapeKeys':o.data.shape_keys.name if o.type=='MESH' and o.data.shape_keys else None})
    records.append({'collection':c.name,'hideRender':c.hide_render,'customProperties':{k:str(v) for k,v in c.items()},'bounds':bounds(obs),'objects':entries})
cameras=[{'name':o.name,'matrixWorld':mat(o.matrix_world),'type':o.data.type,'orthoScale':o.data.ortho_scale,'shiftX':o.data.shift_x,'shiftY':o.data.shift_y,'customProperties':{k:str(v) for k,v in o.items()}} for o in bpy.data.objects if o.type=='CAMERA']
r={'project':bpy.data.filepath,'scene':scene.name,'sceneCamera':scene.camera.name if scene.camera else None,'render':{'resolutionX':scene.render.resolution_x,'resolutionY':scene.render.resolution_y,'resolutionPercentage':scene.render.resolution_percentage,'pixelAspectX':scene.render.pixel_aspect_x,'pixelAspectY':scene.render.pixel_aspect_y,'filmTransparent':scene.render.film_transparent,'engine':scene.render.engine},'collections':records,'cameras':cameras,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location),'size':getattr(o.data,'size',None)} for o in bpy.data.objects if o.type=='LIGHT']}
out.write_text(json.dumps(r,indent=2)+'\n')
print('INSPECTION',out)
