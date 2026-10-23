import bpy,sys,math,json,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'historical'
OUT=BASE/'captures'/MODE;OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('private_capture',BASE/'resources/native/capture_runtime.py');cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
sc=bpy.context.scene;cap.SCENE_NAME=sc.name;cap.OUT=OUT
coll=next(c for c in bpy.data.collections if 'rock-shelf-edge' in c.name and any(o.type=='MESH' for o in c.all_objects));root=next(o for o in coll.all_objects if o.type=='EMPTY' and '__root' in o.name)
for c in sc.collection.children:c.hide_render=(c!=coll);c.hide_viewport=False
def enable(lc):
 lc.exclude=False;lc.hide_viewport=False
 for c in lc.children:enable(c)
enable(bpy.context.view_layer.layer_collection)
for o in coll.all_objects:o.hide_viewport=False;o.hide_set(False)
sc.frame_set(1);sc.eevee.taa_render_samples=32
records={}
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle;bpy.context.view_layer.update()
 rec=cap.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
 sc.render.filter_size=1.5 if MODE=='historical' else .5
 rec.update(filter_size=sc.render.filter_size,samples=sc.eevee.taa_render_samples,blender=bpy.app.version_string,direction=d,rootMatrix=[list(r) for r in root.matrix_world],sourceBlend=bpy.data.filepath)
 sc.render.filepath=str(OUT/f'native-{d}-4x.png');bpy.ops.render.render(write_still=True)
 records[d]=rec
(OUT/'camera-records.json').write_text(json.dumps(records,indent=2)+'\n')
print('SOURCE_REPLAY_COMPLETE',MODE,json.dumps({d:r['calibration'] for d,r in records.items()}))
