import bpy,json,pathlib,hashlib
root=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
out=root/'prototypes/sushi-loop/assets/refinement/objects/submarine-yellow/reviews/preparation-v1'
cs=[c for c in bpy.data.collections if 'submarine' in c.name.lower()]
d={'blend':bpy.data.filepath,'blender':bpy.app.version_string,'collections':[], 'scene':{'name':bpy.context.scene.name,'camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'resolution':[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y],'engine':bpy.context.scene.render.engine}}
for c in cs:
 d['collections'].append({'name':c.name,'hide_render':c.hide_render,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'materials':[m.name if m else None for m in (o.data.materials if o.type=='MESH' else [])],'vertices':len(o.data.vertices) if o.type=='MESH' else None} for o in c.all_objects]})
(out/'native-initial.json').write_text(json.dumps(d,indent=2))
print(json.dumps({'collections':[(x['name'],len(x['objects'])) for x in d['collections']],'scene':d['scene']}))
