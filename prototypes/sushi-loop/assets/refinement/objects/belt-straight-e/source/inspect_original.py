import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
B=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/belt-straight-e')
P=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(P)); s=bpy.data.scenes.new('IndependentEInspection');bpy.context.window.scene=s
c=bpy.data.collections['S33_FB_belt-straight-e.001']; root=next(o for o in c.all_objects if o.type=='EMPTY' and '__root' in o.name)
# Retain only the actual named source collection and explicitly unhide it.
for other in list(s.collection.children):s.collection.children.unlink(other)
s.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False;o.update_tag()
s.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def bounds():
 dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);m=ev.to_mesh();pts += [list(ev.matrix_world@v.co) for v in m.vertices];ev.to_mesh_clear()
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
D={'project':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collection':c.name,'root':root.name,'objects':[],'boundsS':bounds(),'facings':{}}
for o in c.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'rotation':list(o.rotation_euler),'location':list(o.location),'scale':list(o.scale),'matrixWorld':[list(r) for r in o.matrix_world]}
 if o.type=='MESH':
  d.update({'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'uv':[[float(a) for a in v.uv] for v in o.data.uv_layers.active.data] if o.data.uv_layers.active else None})
 D['objects'].append(d)
for facing,a in {'S':0,'E':90,'N':180,'W':-90}.items():root.rotation_euler.z=math.radians(a);bpy.context.view_layer.update();D['facings'][facing]={'rootRotationDegrees':a,'bounds':bounds()}
D['materials']={}
for o in c.all_objects:
 if o.type!='MESH':continue
 for m in o.data.materials:
  if m and m.use_nodes:
   vs=[n for n in m.node_tree.nodes if n.type=='VALUE']
   if vs:
    phases=[]
    for i in range(25):s.frame_set(i+1);bpy.context.view_layer.update();phases.append(vs[0].outputs[0].default_value)
    D['materials'][m.name]={'phase':phases,'action':m.node_tree.animation_data.action.name if m.node_tree.animation_data else None}
(B/'source/independent-source-inspection.json').write_text(json.dumps(D,indent=2))
print('SOURCE_INSPECTION',json.dumps({'boundsS':D['boundsS'],'objects':[(o['name'],o['rotation']) for o in D['objects']],'phase':D['materials']}))
