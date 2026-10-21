import bpy
import hashlib
import json
from pathlib import Path

project = Path(bpy.data.filepath)
out = Path(__file__).parent / 'source-inspection.json'
scene = bpy.context.scene
root = bpy.data.objects.get('barrel-wood__root')
images = [{'name': image.name, 'source': image.source, 'path': image.filepath,
           'packed': bool(image.packed_file)} for image in bpy.data.images]
libraries = [{'name': library.name, 'path': library.filepath} for library in bpy.data.libraries]
result = {
    'inspection': 'Independent read-only reopened approved barrel source; no render or save',
    'project': str(project),
    'projectSHA256': hashlib.sha256(project.read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
    'scene': scene.name,
    'objects': [{'name': obj.name, 'type': obj.type} for obj in scene.objects],
    'root': {'name': root.name, 'location': list(root.location), 'scale': list(root.scale),
             'rotationEuler': list(root.rotation_euler)} if root else None,
    'camera': {'name': scene.camera.name, 'type': scene.camera.data.type,
               'orthoScale': scene.camera.data.ortho_scale,
               'worldMatrix': [list(row) for row in scene.camera.matrix_world]},
    'render': {'engine': scene.render.engine, 'resolution': [scene.render.resolution_x, scene.render.resolution_y],
               'percentage': scene.render.resolution_percentage,
               'pixelAspect': [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y],
               'transparent': scene.render.film_transparent,
               'compositor': scene.use_nodes, 'fps': scene.render.fps,
               'viewTransform': scene.view_settings.view_transform,
               'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure,
               'gamma': scene.view_settings.gamma},
    'materials': [{'name': material.name, 'useNodes': material.use_nodes,
                  'nodes': sorted(node.type for node in material.node_tree.nodes) if material.use_nodes else []}
                 for material in bpy.data.materials],
    'world': scene.world.name if scene.world else None,
    'lights': [{'name': obj.name, 'type': obj.data.type, 'location': list(obj.location),
                'energy': obj.data.energy, 'color': list(obj.data.color)}
               for obj in scene.objects if obj.type == 'LIGHT'],
    'libraries': libraries,
    'images': images,
    'externalDependencyCount': len(libraries) + sum(image['source'] == 'FILE' and not image['packed'] for image in images),
    'sourceUnmodified': True
}
out.write_text(json.dumps(result, indent=2) + '\n')
print('JUDGE_SOURCE_INSPECTION', json.dumps({'sha256': result['projectSHA256'],
      'scene': result['scene'], 'objects': len(result['objects']),
      'externalDependencyCount': result['externalDependencyCount'], 'root': result['root']}))
