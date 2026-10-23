"""Sampling-only authorized revision: exact round03 geometry/rig, persisted filter.5."""
import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1];S=B/'source';O=B/'candidates/round-04';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 out={}
 for o in bpy.data.objects:
  d={'type':o.type,'matrix':[list(r) for r in o.matrix_world]}
  if o.type=='MESH':d.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],materials=[m.name for m in o.data.materials],uvs=[list(v.uv) for u in o.data.uv_layers for v in u.data],polygonMaterialIndices=[p.material_index for p in o.data.polygons])
  elif o.type=='LIGHT':d.update(energy=o.data.energy,color=list(o.data.color),size=o.data.size,shape=o.data.shape)
  elif o.type=='CAMERA':d.update(type=o.data.type,ortho=o.data.ortho_scale,shift=[o.data.shift_x,o.data.shift_y])
  out[o.name]=d
 return hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
bpy.context.view_layer.update();before=fingerprint();original=sha(S/'round-03.blend');sc=bpy.context.scene;old=sc.render.filter_size;sc.render.filter_size=.5
assert fingerprint()==before
bpy.ops.wm.save_as_mainfile(filepath=str(S/'round-04.blend'),compress=True)
(O/'sampling-revision-created.json').write_text(json.dumps({'originalSourceSHA256':original,'newSourceSHA256':sha(S/'round-04.blend'),'changedOnly':'render.filter_size','beforeFilterSize':old,'newFilterSize':sc.render.filter_size,'nativeGeometryUVMaterialAssignmentCameraLightFingerprintBefore':before,'nativeGeometryUVMaterialAssignmentCameraLightFingerprintAfter':fingerprint(),'originalSourceUnchanged':sha(S/'round-03.blend')==original,'frozenBriefSHA256':sha(B/'brief-v3-native-sampling.json')},indent=2))
print('NEW_STANDALONE',str(S/'round-04.blend'),sha(S/'round-04.blend'),before)
