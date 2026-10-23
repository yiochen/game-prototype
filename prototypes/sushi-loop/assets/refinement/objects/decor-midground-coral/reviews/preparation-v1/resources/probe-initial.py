import bpy,json,pathlib
out=pathlib.Path(__file__).parent
cols=[]
for c in bpy.data.collections:
 if 'decor-midground-coral' in c.name or c.get('asset_id')=='decor-midground-coral':
  cols.append({'name':c.name,'props':{k:c[k] for k in c.keys()},'objects':[o.name for o in c.all_objects]})
scene=bpy.context.scene
summary={'file':bpy.data.filepath,'blender':bpy.app.version_string,'scene':scene.name,'frame':scene.frame_current,'fps':scene.render.fps,'render':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':scene.camera.name if scene.camera else None,'collections':cols,'sceneKeys':list(scene.keys()),'relatedObjects':[{'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection]} for o in bpy.data.objects if 'pink-coral' in o.name], 'viewLayer':bpy.context.view_layer.name}
(out/'initial-native-probe.json').write_text(json.dumps(summary,indent=2,default=str))
print(json.dumps(summary,indent=2,default=str))
