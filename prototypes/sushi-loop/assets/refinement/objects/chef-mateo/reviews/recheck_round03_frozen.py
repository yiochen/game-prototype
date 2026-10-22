"""Read-only replay of inspected property fingerprint functions on sealed files."""
import sys, json, importlib.util, hashlib
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
OBJ=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('review_mateo_properties',OBJ/'source/round03_common.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
results=[]
for name in ['round02','round03']:
    path=OBJ/'source'/f'{name}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    saved={'scene':bpy.context.scene.name,'frame':bpy.context.scene.frame_current,'rootRotation':list(bpy.data.objects[C.rig['groundRootObject']].rotation_euler)}
    sc,asset,arm,food=C.owned()
    C.N.apply_clip(asset,C.rig,'idle',1,'S',sc)
    properties=C.invariants(sc,asset,arm,food)
    properties.pop('settings')
    results.append({'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'savedState':saved,'properties':properties})
checks={k:results[0]['properties'][k]==results[1]['properties'][k] for k in results[0]['properties']}
report={'method':'Read-only replay of inspected comprehensive native property serializer. Authorized food image binding omitted from material fingerprint; food rest geometry/UV separately verified against fixed mapping. No save.','checks':checks,'allFrozenPropertiesExact':all(checks.values()),'sources':results}
(OBJ/'reviews/round03-frozen-source-recheck.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':checks,'savedStates':[r['savedState'] for r in results]}))
