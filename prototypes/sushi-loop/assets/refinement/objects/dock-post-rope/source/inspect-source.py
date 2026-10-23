import bpy,json,hashlib
from pathlib import Path
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-post-rope')
src=(P/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(src))
cols=[c for c in bpy.data.collections if 'dock-post-rope' in c.name]
print('COLLECTIONS',[(c.name,len(c.all_objects)) for c in cols])
c=next(c for c in cols if any(o.type=='MESH' for o in c.all_objects))
s=bpy.data.scenes.new('Inspection');s.collection.children.link(c);bpy.context.window.scene=s
c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
bpy.context.view_layer.update();s.frame_set(1);bpy.context.evaluated_depsgraph_get().update()
obs=[]
for o in c.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'matrix':list(map(list,o.matrix_world)),'props':{k:str(v) for k,v in o.items()}}
 if o.type=='MESH':
  vs=[o.matrix_world@v.co for v in o.data.vertices];r.update(vertices=len(vs),polys=len(o.data.polygons),bounds=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers],smooth=sum(p.use_smooth for p in o.data.polygons),uvLayers=[x.name for x in o.data.uv_layers])
 obs.append(r)
report={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collection':c.name,'objects':obs,'cameras':[{'name':o.name,'ortho':o.data.ortho_scale,'shiftX':o.data.shift_x,'shiftY':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA'],'materials':[{'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[(n.name,n.bl_idname) for n in m.node_tree.nodes] if m.node_tree else []} for m in bpy.data.materials if m.name in {m for o in obs if o['type']=='MESH' for m in o['materials']} ]}
(P/'source/inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
