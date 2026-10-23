import bpy,json,pathlib
out=pathlib.Path(__file__).resolve().parent
key='sub-hull-panels'
result={'scenes':[s.name for s in bpy.data.scenes], 'collections':[], 'objects':[]}
for c in bpy.data.collections:
 if key in c.name or 'hull_panel' in c.name:
  result['collections'].append({'name':c.name,'objects':[o.name for o in c.all_objects], 'props':{k:str(v) for k,v in c.items()}})
for o in bpy.data.objects:
 if 'hull_panel' in o.name or o.get('production_id')==key:
  rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'props':{k:str(v) for k,v in o.items()},'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'bounds':[list(o.matrix_world@__import__('mathutils').Vector(c)) for c in o.bound_box] if o.type=='MESH' else [], 'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]}
  if o.type=='MESH':rec.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons))
  result['objects'].append(rec)
result['sceneSettings']={s.name:{'camera':s.camera.name if s.camera else None,'renderEngine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filmTransparent':s.render.film_transparent,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'fps':s.render.fps} for s in bpy.data.scenes}
(out/'source-inspection.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
