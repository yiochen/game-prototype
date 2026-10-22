import bpy,json
from pathlib import Path
p=Path(__file__).parents[0]
bpy.context.view_layer.update()
d={'collections':[{'name':c.name,'objects':[o.name for o in c.objects]} for c in bpy.data.collections],'roots':[{'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'props':{k:str(o[k]) for k in o.keys()}} for o in bpy.data.objects if o.parent is None],'actions':[a.name for a in bpy.data.actions],'scene':bpy.context.scene.name,'frame':bpy.context.scene.frame_current}
(p/'approved-rosa-inventory.json').write_text(json.dumps(d,indent=2));print(json.dumps({'collections':[c['name'] for c in d['collections']],'roots':[r['name'] for r in d['roots']],'actions':d['actions'][:10]}))
