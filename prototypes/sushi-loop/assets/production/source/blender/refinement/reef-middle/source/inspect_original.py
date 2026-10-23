import bpy, json
from pathlib import Path
out=Path(__file__).parent
data={'blender':bpy.app.version_string,'scenes':[]}
for sc in bpy.data.scenes:
    objs=[o for o in sc.objects if 'reef-middle' in o.name]
    if objs:
        rec={'scene':sc.name,'camera':sc.camera.name if sc.camera else None,'objects':[]}
        for o in objs:
            r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(row) for row in o.matrix_world]}
            if o.type=='MESH':
                r.update(vertices=[list(v.co) for v in o.data.vertices],polygons=[list(p.vertices) for p in o.data.polygons],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers])
            rec['objects'].append(r)
        data['scenes'].append(rec)
(out/'original-native-inspection.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({'scenes':[(s['scene'],len(s['objects'])) for s in data['scenes']]}))
