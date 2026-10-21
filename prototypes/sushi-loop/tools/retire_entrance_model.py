"""Run in background Blender; retire only the old active entrance collection.
Immutable source snapshots remain the provenance authority for other assets.
"""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'assets/production/source/blender'
old=bpy.data.collections.get('S33_PROP_entrance.001')
assert old is not None,'Expected old entrance collection not found'
removed=[o.name for o in old.all_objects]
for obj in list(old.all_objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.data.collections.remove(old)
assert not any('entry-finished' in o.name for o in bpy.data.objects)
# Add the new editable backdrop study as its own scene, preserving the other
# registered assets and their original source snapshots unchanged.
with bpy.data.libraries.load(str(ROOT/'assets/production/source/backdrop/restaurant-backdrop-35.blend'),link=False) as (available,loaded):
 loaded.scenes=[name for name in available.scenes if name=='Sushi Loop Uniform Wood Backdrop35 Study']
assert loaded.scenes
path=source/'sushi-loop-world-library-current.blend'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
receipt={'removedCollection':'S33_PROP_entrance.001','removedObjects':removed,'replacementScene':loaded.scenes[0].name,'currentProject':str(path.relative_to(ROOT/'assets/production')),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'originalSnapshot':'source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'}
target=ROOT/'review/33/restaurant-backdrop/integration';target.mkdir(parents=True,exist_ok=True)
(target/'model-retirement.json').write_text(json.dumps(receipt,indent=2)+'\n')
(source/'sushi-loop-world-library-current.export.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('REMOVED_ENTRANCE_MODEL',len(removed),'objects; new editable backdrop imported')
