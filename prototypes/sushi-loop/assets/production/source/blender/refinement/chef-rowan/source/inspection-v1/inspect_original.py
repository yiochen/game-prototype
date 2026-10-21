import bpy
import json
from pathlib import Path

OUT = Path(__file__).parent
rows = []
for obj in bpy.data.objects:
    if 'chef_rowan' in obj.name:
        rows.append(dict(name=obj.name, type=obj.type,
                         parent=obj.parent.name if obj.parent else None,
                         parent_type=obj.parent_type, parent_bone=obj.parent_bone,
                         collections=[x.name for x in obj.users_collection],
                         hide_viewport=obj.hide_viewport, hide_render=obj.hide_render,
                         location=list(obj.location), rotation=list(obj.rotation_euler),
                         scale=list(obj.scale), dimensions=list(obj.dimensions),
                         mesh_vertices=len(obj.data.vertices) if obj.type == 'MESH' else None,
                         mesh_faces=len(obj.data.polygons) if obj.type == 'MESH' else None,
                         materials=[m.name for m in obj.data.materials if m] if obj.type == 'MESH' else [],
                         modifiers=[dict(name=m.name, type=m.type) for m in obj.modifiers],
                         custom={k:str(v)[:400] for k,v in obj.items()},
                         action=obj.animation_data.action.name if obj.animation_data and obj.animation_data.action else None))
data = dict(version=bpy.app.version_string, source=bpy.data.filepath,
            scenes=[dict(name=s.name, camera=s.camera.name if s.camera else None,
                         objects=len(s.objects), frame=s.frame_current,
                         render=[s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage],
                         engine=s.render.engine) for s in bpy.data.scenes],
            collections=[dict(name=c.name, hide_viewport=c.hide_viewport, hide_render=c.hide_render,
                              objects=[o.name for o in c.objects], children=[x.name for x in c.children])
                         for c in bpy.data.collections if any('chef_rowan' in o.name for o in c.all_objects)],
            objects=rows,
            actions=[dict(name=a.name, frame_range=list(a.frame_range),
                          slots=[dict(identifier=s.identifier, target_id_type=s.target_id_type) for s in a.slots])
                     for a in bpy.data.actions if 'chef-rowan' in a.name])
(OUT/'native-inventory.json').write_text(json.dumps(data,indent=2))
print(json.dumps(dict(version=data['version'], scenes=data['scenes'],
                      collections=[{k:v for k,v in c.items() if k!='objects'} for c in data['collections']],
                      objects=[dict(name=o['name'], type=o['type'], parent=o['parent'], parent_bone=o['parent_bone']) for o in rows],
                      action_count=len(data['actions'])),indent=2))
