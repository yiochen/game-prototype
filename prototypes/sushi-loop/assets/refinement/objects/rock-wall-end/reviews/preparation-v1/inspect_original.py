import bpy, json
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
collection = bpy.data.collections.get('rock-wall-end')
if collection is None:
    matching = [c for c in bpy.data.collections if 'rock-wall-end' in c.name]
    collection = matching[0] if matching else None
assert collection, [c.name for c in bpy.data.collections]
def vec(v): return [round(float(x),9) for x in v]
def bounds(obj):
    vs=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return {'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]}
objects=[]
for obj in collection.all_objects:
    rec={'name':obj.name,'type':obj.type,'parent':obj.parent.name if obj.parent else None,'location':vec(obj.location),'rotation':vec(obj.rotation_euler),'scale':vec(obj.scale),'properties':dict(obj.items()),'bounds':bounds(obj),'constraints':[c.type for c in obj.constraints],'modifiers':[{'name':m.name,'type':m.type} for m in obj.modifiers]}
    if obj.type=='MESH':
        rec.update(vertices=len(obj.data.vertices),polygons=len(obj.data.polygons),materials=[m.name if m else None for m in obj.data.materials],smoothPolygons=sum(p.use_smooth for p in obj.data.polygons),uvLayers=[u.name for u in obj.data.uv_layers])
    objects.append(rec)
scenes=[]
for s in bpy.data.scenes:
    scenes.append({'name':s.name,'camera':s.camera.name if s.camera else None,'renderEngine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'frame':[s.frame_start,s.frame_end,s.frame_current],'filmTransparent':s.render.film_transparent,'viewSettings':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'world':s.world.name if s.world else None,'objects':len(s.objects)})
result={'collection':collection.name,'collectionProperties':dict(collection.items()),'objects':objects,'scenes':scenes,'cameras':[{'name':o.name,'location':vec(o.location),'rotation':vec(o.rotation_euler),'matrix':[list(row) for row in o.matrix_world],'type':o.data.type,'ortho_scale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]} for o in bpy.data.objects if o.type=='CAMERA'],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':vec(o.location),'size':getattr(o.data,'size',None),'shadow':o.data.use_shadow} for o in bpy.data.objects if o.type=='LIGHT'],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'libraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries]}
(OUT/'original-native-audit.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print(json.dumps({'collection':collection.name,'objects':[(o['name'],o['type'],o['bounds']) for o in objects],'scenes':scenes},indent=2))
