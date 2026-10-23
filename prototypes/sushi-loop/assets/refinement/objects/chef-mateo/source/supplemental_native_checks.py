"""Actual reopened candidate: source prop mesh/UV/driver parity and loop closure."""
import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round01'
spec=importlib.util.spec_from_file_location('mateo_extra_actions',HERE/'native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
scene=bpy.data.scenes['Mateo warm soft native round01'];bpy.context.window.scene=scene
rig=json.loads((OUT/'rig.json').read_text());source=json.loads((HERE/'source-native-audit.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in scene.collection.children if root in list(c.all_objects));asset={'root':root,'collection':collection};arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
prop={o.name:{'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'uv':{l.name:[list(x.uv) for x in l.data] for l in o.data.uv_layers},'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[(v.name,v.targets[0].id.name,v.targets[0].data_path) for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []} for o in collection.all_objects if o.type=='MESH' and '__ground_root' in o.name}
prop=json.loads(json.dumps(prop))
assert prop==source['lockedPropMeshes'],'Source food/knife geometry, UV, or composition drivers changed'
closures=[]
def state():
 return {p.name:[list(r) for r in arm.matrix_world@p.matrix] for p in arm.pose.bones}
for clip,cd in rig['clips'].items():
 if not cd['loop']:continue
 for d in ['N','E','S','W']:
  n.apply_clip(asset,rig,clip,1,d,scene);first=state()
  n.apply_clip(asset,rig,clip,cd['closingKeyFrame'],d,scene);last=state()
  error=max(abs(first[k][i][j]-last[k][i][j]) for k in first for i in range(4) for j in range(4));assert error<1e-6,(clip,d,error)
  closures.append({'clip':clip,'direction':d,'closingFrame':cd['closingKeyFrame'],'maximumBoneMatrixDelta':error})
prefs=bpy.context.preferences.addons['cycles'].preferences
try:prefs.compute_device_type='METAL';prefs.refresh_devices()
except:pass
devices=[{'name':d.name,'type':d.type,'enabled':d.use} for d in prefs.devices]
report={'reopenedExactCandidateSHA256':hashlib.sha256((HERE/'round01.blend').read_bytes()).hexdigest(),'sourcePropMeshUVAndDriverParity':True,'lockedProps':list(prop),'loopClosureCases':closures,'sourceNonloopingLoadPreserved':not rig['clips']['load']['loop'],'actualRenderEngine':scene.render.engine,'actualCyclesDevice':scene.cycles.device,'availableDevices':devices,'cameraMatrixWorld':[list(r) for r in scene.camera.matrix_world],'noCandidateSaveOrArtChange':True}
(OUT/'supplemental-native-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('MATEO_SUPPLEMENTAL',json.dumps(report))
