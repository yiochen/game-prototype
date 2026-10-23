import sys
sys.dont_write_bytecode=True
import bpy,math,json,importlib.util
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
BASE=Path(__file__).resolve().parent;PREV=BASE.with_name('preparation-v1');OUT=BASE/'evidence/study-direct2x-filter001';OUT.mkdir(parents=True,exist_ok=True)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,str(path));m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
bpy.ops.wm.open_mainfile(filepath=str(PREV/'resources/source/original.blend'))
worker=load('frozen_worker',PREV/'resources/source/capture_worker.py');runtime=load('frozen_runtime',PREV/'resources/source/capture_runtime.py')
sc=worker.native_scene();c=bpy.data.collections['S33_PROP_reef-middle.001'];root=bpy.data.objects['reef-middle__root.001']
a={'collection':c,'root':root,**json.loads((PREV/'resources/object/inputs/source-assetRecord.json').read_text())}
worker.show_only(sc,a)
for l in worker.layer_nodes(sc.view_layers[0].layer_collection):
 if l.collection==c:l.exclude=False;l.hide_viewport=False
c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update()
args=SimpleNamespace(samples=32,threads=4)
original_filter=sc.render.filter_size;sc.render.filter_size=.01
a['scale']=2
record,render=worker.render_configuration(runtime,sc,a,args)
log={'sourceFrame':record,'renderSettings':render,'facings':{},'joinedCanvas':{'frame':[448,608],'root':[224,376],'pitchLogical':128,'moduleOffsets':[-1,0,1],'changes':'canvas extends by128 logical pixels on every side, same scale and projection'},'lights':[],'sourceOnlyStudy':{'historicalFilterSize':original_filter,'studyFilterSize':sc.render.filter_size,'actualNativeScale':2,'publishedScale':2,'noReduction':True,'onlyChange':'Direct native2x pixel filter width .01; source geometry/materials/camera/roots/canvas/lights unchanged. No blend save, no approval.'}}
for o in sc.objects:
 if o.type=='LIGHT' and o.data.energy>0:log['lights'].append({'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size})
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle;sc.view_layers[0].update()
 record,settings=worker.render_configuration(runtime,sc,a,args)
 p=OUT/'native'/('single-'+d+'.png');p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 log['facings'][d]={'angleRadians':angle,'actualRootMatrix':[list(r) for r in root.matrix_world],'singleCamera':record}
# Duplicate whole native hierarchy at exact rotated unit-pitch offsets. Source vertices/normals/materials unchanged.
copies=[]
for i in [-1,1]:
 cc=bpy.data.collections.new('Judge exact module '+str(i));sc.collection.children.link(cc);mapping={}
 for o in c.objects:
  n=o.copy();cc.objects.link(n);mapping[o]=n
 for o,n in mapping.items():
  if o.parent in mapping:n.parent=mapping[o.parent]
 copies.append((i,cc,mapping[root]))
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle
 for i,cc,r in copies:r.rotation_euler.z=angle;r.location=(i*math.cos(angle),i*math.sin(angle),0)
 sc.view_layers[0].update()
 rec=runtime.configure_camera(a['projection'],(448,608),(224,376),2)
 p=OUT/'native'/('three-joined-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 log['facings'][d]['joinedCamera']=rec;log['facings'][d]['moduleRoots']=[{'offset':i,'matrix':[list(row) for row in r.matrix_world]} for i,cc,r in copies]
(OUT/'capture-measurements.json').write_text(json.dumps(log,indent=2)+'\n')
print('SOURCE_REPLAY_COMPLETE',flush=True)
