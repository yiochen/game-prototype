import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
p=HERE/'resources/original-source-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
items=[]
for ob in bpy.data.objects:
    if 'hull_panel' not in ob.name.lower(): continue
    rec={'name':ob.name,'type':ob.type,'location':list(ob.location),'scale':list(ob.scale),'rotation':list(ob.rotation_euler),'parent':ob.parent.name if ob.parent else None,'collections':[c.name for c in ob.users_collection]}
    if ob.type=='MESH':
        pts=[ob.matrix_world@v.co for v in ob.data.vertices]
        rec.update(vertices=len(pts),polygons=len(ob.data.polygons),bounds=[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)],materials=[m.name if m else None for m in ob.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in ob.modifiers])
    items.append(rec)
out={'blender':bpy.app.version_string,'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'nativeObjects':items}
(HERE/'original-native-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
