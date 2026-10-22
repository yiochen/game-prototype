"""One bounded all-four historical replay; original source unchanged on disk."""
import bpy, os, sys, json, math, importlib.util
sys.dont_write_bytecode = True
from pathlib import Path
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('wreck_preparation_capture',OUT/'dependencies/capture_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
sc=bpy.context.scene
runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
col=bpy.data.collections['S33_PROP_wreck-middle.001'];root=bpy.data.objects['wreck-middle__root.001']
def layers(l):
    yield l
    for c in l.children: yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection): l.exclude=False;l.hide_viewport=False
for l in sc.view_layers[0].layer_collection.children: l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_viewport=c!=col;c.hide_render=c!=col
for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
sc.frame_set(1);sc.view_layers[0].update()
camera=runtime.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
if hasattr(sc,'eevee'):
    for name in ['taa_render_samples','taa_samples']:
        if hasattr(sc.eevee,name):setattr(sc.eevee,name,32);break
sc.render.image_settings.compression=15
sc.render.use_persistent_data=True
records=[]
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;sc.view_layers[0].update()
    path=OUT/'historical-replay'/'native'/('static-'+d)/'000.png';path.parent.mkdir(parents=True,exist_ok=True)
    sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    records.append({'direction':d,'rootRotationDegrees':math.degrees(root.rotation_euler.z),
        'actualRootMatrix':[list(r) for r in root.matrix_world], 'frame':sc.frame_current,
        'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],
        'filterSize':sc.render.filter_size, 'engine':sc.render.engine,
        'renderSamples':getattr(getattr(sc,'eevee',None),'taa_render_samples',None),
        'camera':runtime.camera_record(sc,sc.camera,'square-top-front-oblique',(192,352),(96,248),4,camera['camera']['elevationDegrees'])})
(OUT/'historical-replay/capture-records.json').write_text(json.dumps({'camera':camera,'records':records},indent=2)+'\n')
print('BOUNDED_REPLAY_COMPLETE')
