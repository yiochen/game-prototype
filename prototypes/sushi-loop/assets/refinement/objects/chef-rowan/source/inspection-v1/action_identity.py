import bpy,json,hashlib,importlib.util
from pathlib import Path
OUT=Path(__file__).parent
nativepath=OUT.parents[5]/'production/source/blender/revisions/d88e53edef8e7c73/native_actions.py'
# Resolve from the untouched library itself, independent of output location.
nativepath=Path(bpy.data.filepath).parents[1]/'d88e53edef8e7c73/native_actions.py'
spec=importlib.util.spec_from_file_location('original_native_actions',nativepath);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def h(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
actions={a.name:dict(slots=[s.identifier for s in a.slots],frameRange=list(a.frame_range),keyframeHash=h([dict(path=f.data_path,index=f.array_index,keys=[dict(co=list(k.co),interpolation=k.interpolation) for k in f.keyframe_points]) for f in native._fcurves(a)])) for a in bpy.data.actions if 'chef-rowan' in a.name}
(OUT/'original-action-identity.json').write_text(json.dumps(actions,indent=2)+'\n')
print('Original action identity count',len(actions))
