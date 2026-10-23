import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
info={'blenderVersion':bpy.app.version_string,'scenes':[],'matchingObjects':[],'matchingCollections':[],'images':[]}
for sc in bpy.data.scenes:
 info['scenes'].append({'name':sc.name,'properties':dict(sc.items()),'children':[c.name for c in sc.collection.children],'camera':sc.camera.name if sc.camera else None})
for o in bpy.data.objects:
 if 'attack-reef-fragments' in o.name: info['matchingObjects'].append({'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection],'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'properties':dict(o.items())})
for c in bpy.data.collections:
 if 'attack-reef-fragments' in c.name:info['matchingCollections'].append({'name':c.name,'objects':[o.name for o in c.objects],'children':[x.name for x in c.children],'hideRender':c.hide_render,'hideViewport':c.hide_viewport})
for im in bpy.data.images:
 if im.source=='FILE':info['images'].append({'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)})
(p/'native/locators.json').write_text(json.dumps(info,indent=2,default=str)+'\n')
print(json.dumps({k:info[k] for k in ['blenderVersion','matchingObjects','matchingCollections']},default=str))
