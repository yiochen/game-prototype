import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
source=root.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
cols=[c for c in bpy.data.collections if 'floor-underwater' in c.name.lower()]
result={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collections':[]}
for c in cols:
    record={'name':c.name,'objects':[]}
    for o in c.all_objects:
        r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(row) for row in o.matrix_world],'animation':bool(o.animation_data),'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []}
        if o.type=='MESH':
            pts=[o.matrix_world@v.co for v in o.data.vertices]
            r.update(vertices=len(pts),polygons=len(o.data.polygons),bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],normals=[list(p.normal) for p in o.data.polygons[:8]],uvLayers=[u.name for u in o.data.uv_layers],modifiers=[m.type for m in o.modifiers])
        record['objects'].append(r)
    result['collections'].append(record)
result['scene']={'camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'engine':bpy.context.scene.render.engine,'frame':bpy.context.scene.frame_current,'resolution':[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y],'filterSize':bpy.context.scene.render.filter_size}
(root/'source/original-native-inspection.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
