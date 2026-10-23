import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[2]
r={'scene':bpy.context.scene.name,'collections':[{'name':c.name,'rootObjects':[o.name for o in c.objects if o.parent is None],'allCount':len(c.all_objects),'hideRender':c.hide_render} for c in bpy.context.scene.collection.children],'directSceneObjects':[{'name':o.name,'type':o.type,'hideRender':o.hide_render,'parent':o.parent.name if o.parent else None} for o in bpy.context.scene.collection.objects]}
(p/'ownership-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
