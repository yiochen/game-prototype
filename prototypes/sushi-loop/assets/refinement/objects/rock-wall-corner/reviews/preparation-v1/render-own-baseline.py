import bpy,json,math,importlib.util
from pathlib import Path
OUT=Path(__file__).resolve().parent;R=OUT/'resources';dest=OUT/'source-baseline';dest.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'original-library.blend'))
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc
root=bpy.data.objects['rock-wall-corner__root.001'];col=next(c for c in sc.collection.children if root in list(c.all_objects))
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
sp=importlib.util.spec_from_file_location('own_capture',R/'capture_runtime.py');rt=importlib.util.module_from_spec(sp);sp.loader.exec_module(rt);rt.scene=lambda:sc
record=rt.configure_camera('square-top-front-oblique',(192,352),(96,256),4)
sc.eevee.taa_render_samples=32;sc.frame_set(1)
sc.render.threads_mode='FIXED';sc.render.threads=4
for direction,degrees in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();sc.render.filepath=str(dest/f'native-static-{direction}.png');bpy.ops.render.render(write_still=True)
(dest/'camera.json').write_text(json.dumps(record,indent=2)+'\n')
(dest/'provenance.json').write_text(json.dumps({'source':'resources/original-library.blend','script':Path(__file__).name,'baseline':'new independent native source renders; not archived original capture bytes','renderer':bpy.app.version_string,'nativeScale':4,'nativeFrame':[768,1408],'publishedScale':2,'filterSize':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'sourcePublishedFrames':'resources/original-published-*.png'},indent=2)+'\n')
