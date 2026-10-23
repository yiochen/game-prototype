import bpy,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];out={}
for aid,f in [('floor',O/'inputs/approved-dock-family-v1/dock-floor/project.blend'),('entry',O/'inputs/approved-dock-family-v1/dock-entry/project.blend'),('hut',O/'inputs/approved-dock-family-v1/workshop-hut/project.blend'),('sub',O/'inputs/frozen-mainbody-v1/project.blend'),('rosa',O/'inputs/shared-world-pose-v1/resources/source/resources/approved-human-v3/customer-rosa-approved.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(f));bpy.context.view_layer.update()
 out[aid]={'collections':[c.name for c in bpy.data.collections],'actions':[a.name for a in bpy.data.actions],'roots':[{'name':o.name,'type':o.type,'scale':list(o.scale),'location':list(o.location)}for o in bpy.context.scene.objects if o.parent is None],'scene':bpy.context.scene.name,'visibleMeshCount':len([o for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render])}
(H/'fixture-inventory.json').write_text(json.dumps(out,indent=2)+'\n')
