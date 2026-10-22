"""Source-only diagnostic assembly; no saved scene/model edits."""
import sys, json, importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;R=P/'resources'
def load(n):
 s=importlib.util.spec_from_file_location('floor_patch_'+n,R/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native=load('native_actions');runtime=load('capture_runtime');scene=bpy.context.scene
rig=json.loads((R/'inputs/source-rig.json').read_text());record=json.loads((R/'inputs/source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in scene.collection.children if root in list(c.all_objects))
asset=dict(record,root=root,collection=col,clips=rig['clips'])
for c in scene.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for layer in scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
runtime.scene=lambda:scene;runtime.SCENE_NAME=scene.name
cam=runtime.configure_camera('square-top-front-oblique',(384,384),(192,192),2)
scene.render.image_settings.compression=15;scene.render.use_persistent_data=True
if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
if hasattr(scene.eevee,'taa_samples'):scene.eevee.taa_samples=32
duplicates=[]
for x,y in [(x,y) for y in (-1,0,1) for x in (-1,0,1) if x or y]:
 rr=root.copy();rr.name='PREPARATION_SOURCE_PATCH_ROOT';col.objects.link(rr);rr.location=(x,y,0)
 for o in list(col.all_objects):
  if o.parent==root:
   cp=o.copy();cp.name='PREPARATION_SOURCE_PATCH_'+o.name;col.objects.link(cp);cp.parent=rr
 duplicates.append(rr)
out=P/'native-patch';out.mkdir(exist_ok=True)
for direction in 'NESW':
 for frame in (1,4):
  native.apply_clip(asset,rig,'scroll',frame,direction,scene)
  for rr in duplicates:rr.rotation_euler=root.rotation_euler
  bpy.context.view_layer.update()
  scene.render.filepath=str(out/(direction+'-'+str(frame-1).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
(P/'native-patch-contract.json').write_text(json.dumps({'camera':cam,'positions':[[x,y,0] for y in (-1,0,1) for x in (-1,0,1)],'directions':list('NESW'),'frames':[1,4],'unchangedSourceData':'Object copies link original unchanged mesh/material/key/action datablocks, exact integer world pitch; no overlap enlargement or raster repair. Source already extends 0.001 beyond nominal pitch on base and waves.','limits':'Shared physical lighting over3x3 differs from independently rendered sprite lighting, and source mesh extension is an inherited defect, not proposed candidate permission.'},indent=2)+'\n')
