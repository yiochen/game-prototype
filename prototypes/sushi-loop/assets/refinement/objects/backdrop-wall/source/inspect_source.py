import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/backdrop-wall')
SOURCE=(BASE/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
col=bpy.data.collections['S33_PROP_uniform35-wall-plain']
scene=bpy.data.scenes.new('WallIndependentInspection')
scene.collection.children.link(col)
bpy.context.window.scene=scene
bpy.context.view_layer.update()
def record(o):
 d={'name':o.name,'type':o.type,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'matrix':[list(r) for r in o.matrix_world],'dimensions':list(o.dimensions),'parent':o.parent.name if o.parent else None,'modifiers':[{ 'name':m.name,'type':m.type} for m in o.modifiers]}
 if o.type=='MESH':
  d.update({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[m.name if m else None for m in o.data.materials]})
 return d
out={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'version':bpy.app.version_string,'collections':[c.name for c in bpy.data.collections],'scenes':[s.name for s in bpy.data.scenes],'objects':[record(o) for o in col.all_objects],'materials':[{ 'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':[{ 'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(float,int)) or (hasattr(i,'default_value') and i.type in ['RGBA','VECTOR'])}} for n in m.node_tree.nodes] if m.use_nodes else []} for m in bpy.data.materials]}
(BASE/'source/source-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'objects':[dict(name=x['name'],location=x['location'],scale=x['scale'],dimensions=x['dimensions'],materials=x.get('materials')) for x in out['objects']],'sourceSha256':out['sha256']},indent=2))
