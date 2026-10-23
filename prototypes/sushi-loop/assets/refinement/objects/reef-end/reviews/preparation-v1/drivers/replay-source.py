import sys
sys.dont_write_bytecode=True
import bpy,math,json,importlib.util,hashlib
from pathlib import Path
from types import SimpleNamespace
B=Path(__file__).resolve().parents[1];R=B/'resources/capture';O=B/'evidence/source-replay';O.mkdir(exist_ok=True)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,str(p));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
bpy.ops.wm.open_mainfile(filepath=str(B/'resources/b1765262bfa897ad-sushi-loop-world-library.blend'))
w=load('judge_source_worker',R/'capture_worker.py');rt=load('judge_source_runtime',R/'capture_runtime.py');sc=w.native_scene()
c=bpy.data.collections['S33_PROP_reef-end.001'];root=bpy.data.objects['reef-end__root.001'];a=json.loads((B/'resources/source-assetRecord.json').read_text());a.update(collection=c,root=root)
w.show_only(sc,a);c.hide_render=False;c.hide_viewport=False
for l in w.layer_nodes(sc.view_layers[0].layer_collection):
 if l.collection==c:l.exclude=False;l.hide_viewport=False
for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();args=SimpleNamespace(samples=32,threads=4);records=[]
for policy,scale,filt in [('historical4x-filter1.5',4,1.5),('direct2x-filter.01-control',2,.01)]:
 a['scale']=scale;sc.render.filter_size=filt
 for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
  root.rotation_euler.z=angle;sc.view_layers[0].update();rec,settings=w.render_configuration(rt,sc,a,args)
  path=O/(policy+'-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  records.append({'policy':policy,'direction':d,'frame':1,'camera':rec,'settings':settings,'filter':sc.render.filter_size,'png':str(path.relative_to(B)),'pngSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'changes':'Untouched original geometry/materials; native source camera restored. Direct2x is sampling control only, not style or seam approval.'})
(O/'capture-measurements.json').write_text(json.dumps({'records':records,'blender':bpy.app.version_string,'noBlendSaved':True,'scope':'Bounded original source replay only; no candidate/family approval.'},indent=2)+'\n')
print('SOURCE_REPLAY_COMPLETE')
