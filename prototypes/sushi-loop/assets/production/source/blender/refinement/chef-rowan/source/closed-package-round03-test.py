"""Run only in a copied object folder; no scene/model save or art changes."""
import bpy,json,hashlib,runpy,sys
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(HERE/'audit-round03-occlusion.py'),run_name='__main__')
assert not bpy.data.libraries, 'Saved source must not require linked libraries'
images=[]
for im in bpy.data.images:
 if im.source not in ['FILE','TILED']:continue
 assert im.packed_file, 'Image must be packed for this test: '+im.name
 sha=hashlib.sha256(bytes(im.packed_file.data)).hexdigest()
 assert sha=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
 missing=OBJ/'deliberately-missing-external-images'/'salmon.png'
 assert not missing.exists()
 im.filepath=str(missing)
 im.reload()
 assert list(im.size)==[731,505] and im.has_data and im.packed_file
 images.append(dict(name=im.name,packedSHA256=sha,size=list(im.size),externalPathRedirectedToMissing=str(missing),packedReloadHasData=im.has_data))
assert len(images)==1
report=dict(test='Closed copied experiment saved-source recapture',projectSHA256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
            linkedLibraryCount=len(bpy.data.libraries),packedImages=images,
            procedure='Only the packed image external filepath is redirected in memory to a nonexistent location, then reloaded; no blend save or geometry/material changes.',
            reconstructionClaim=False,sourceCaptureScript=str(HERE/'capture-round-03.py'))
(OUT/'closed-package-environment.json').write_text(json.dumps(report,indent=2)+'\n')
runpy.run_path(str(HERE/'capture-round-03.py'),run_name='__main__')
print('CLOSED_PACKAGE_CAPTURE_COMPLETED',flush=True)
