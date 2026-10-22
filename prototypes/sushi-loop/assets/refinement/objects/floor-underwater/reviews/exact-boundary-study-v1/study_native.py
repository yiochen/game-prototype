"""Bounded technical diagnostic, no aesthetic candidate or production mutation."""
import sys,json,math,importlib.util,argparse,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;R=P/'resources'
args=argparse.ArgumentParser();args.add_argument('--filter',type=float,required=True);args.add_argument('--variant',required=True);args=args.parse_args(sys.argv[sys.argv.index('--')+1:])
out=P/args.variant;out.mkdir(exist_ok=True)
def load(n):
 s=importlib.util.spec_from_file_location('exact_boundary_'+n,R/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native=load('native_actions');runtime=load('capture_runtime');scene=bpy.context.scene
rig=json.loads((R/'inputs/source-rig.json').read_text());record=json.loads((R/'inputs/source-assetRecord.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in scene.collection.children if root in list(c.all_objects));asset=dict(record,root=root,collection=col,clips=rig['clips'])
for c in scene.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for layer in scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
# Exact nominal cut planes, same native source topology, material and temporal law.
base=next(o for o in col.all_objects if 'full_square' in o.name)
for v in base.data.vertices:v.co.x=math.copysign(.5,v.co.x);v.co.y=math.copysign(.5,v.co.y)
for o in col.all_objects:
 if 'periodic_wave' not in o.name:continue
 center=-.25 if 'wave_0' in o.name else .25
 for key in o.data.shape_keys.key_blocks:
  phase=int(key.name.rsplit(' ',1)[-1])/12 if key.name.startswith('S33 sample ') else 0
  for i,v in enumerate(key.data):
   x=-.5+(i//2)/64;v.co=(x,center+(-.055 if i%2==0 else .055)+.045*math.sin((x+.5+phase)*math.tau),.002)
 for i,v in enumerate(o.data.vertices):
  x=-.5+(i//2)/64;v.co=(x,center+(-.055 if i%2==0 else .055)+.045*math.sin((x+.5)*math.tau),.002)
 o.data.update()
base.data.update()
runtime.scene=lambda:scene;runtime.SCENE_NAME=scene.name
camera=runtime.configure_camera('square-top-front-oblique',(128,128),(64,64),4)
originalFilter=scene.render.filter_size;scene.render.filter_size=args.filter
scene.render.image_settings.compression=15;scene.render.use_persistent_data=True
if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
if hasattr(scene.eevee,'taa_samples'):scene.eevee.taa_samples=32
report={'stage':'exact-boundary-technical-source-study; no aesthetic candidate','sourceSHA256':hashlib.sha256((R/'source-original.blend').read_bytes()).hexdigest(),'variant':args.variant,'sourceFilterAtLoad':originalFilter,'nativeFilter':scene.render.filter_size,'rawToExport':'Unchanged full512→256 LANCZOS, no pixel repair.','camera':camera,'normalizedGeometry':'Base actual finite quad vertices becomeX/Y±.5 atZ0. Two source wave meshes keep130vertices/64faces, source normals, source material and original geometry actions. Every shape-key profile is reconstructed onX=-.5+i/64 with measured source lawY=center±.055+.045sin(2π(X+.5+phase)); center±.25,Z.002. Source four borders unchanged within±.5,Z.004. No overlap added.','samples':[]}
def measure(direction,frame):
 native.apply_clip(asset,rig,'scroll',frame,direction,scene);deps=bpy.context.evaluated_depsgraph_get();rows=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();coords=[ev.matrix_world@v.co for v in me.vertices]
  rows.append({'name':o.name,'worldBounds':[[min(v[a] for v in coords),max(v[a] for v in coords)] for a in range(3)],'evaluatedArea':sum(p.area for p in me.polygons),'xyOverhang':max(max(abs(v[0]),abs(v[1]))-.5 for v in coords),'coordinateSHA256':hashlib.sha256(json.dumps([list(v) for v in coords],separators=(',',':')).encode()).hexdigest()})
  ev.to_mesh_clear()
 report['samples'].append({'direction':direction,'frame':frame,'meshes':rows})
for direction in 'NESW':
 folder=out/'raw-single';folder.mkdir(exist_ok=True)
 for frame in (1,4):
  measure(direction,frame);scene.render.filepath=str(folder/(direction+'-'+str(frame-1).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
native.apply_clip(asset,rig,'scroll',1,'S',scene)
scene['preparation_only']='Exact boundary technical study; not an art candidate or approval'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'source-study.blend'),check_existing=False)
# True physical3x3 assembly at the same512pixels/cell, exact1unit world pitch.
duplicates=[]
owned=list(col.all_objects)
for x,y in [(x,y) for y in (-1,0,1) for x in (-1,0,1) if x or y]:
 rr=root.copy();rr.name='EXACT_BOUNDARY_STUDY_ROOT';col.objects.link(rr);rr.location=(x,y,0)
 for o in owned:
  if o.parent==root:
   cp=o.copy();cp.name='EXACT_BOUNDARY_STUDY_'+o.name;col.objects.link(cp);cp.parent=rr
 duplicates.append(rr)
patchCamera=runtime.configure_camera('square-top-front-oblique',(384,384),(192,192),4);scene.render.filter_size=args.filter
report['patchCamera']=patchCamera;report['nativePatchPositions']=[[x,y,0] for y in (-1,0,1) for x in (-1,0,1)]
for direction in 'NESW':
 folder=out/'raw-native-patch';folder.mkdir(exist_ok=True)
 for frame in (1,4):
  native.apply_clip(asset,rig,'scroll',frame,direction,scene)
  for rr in duplicates:rr.rotation_euler=root.rotation_euler
  bpy.context.view_layer.update();scene.render.filepath=str(folder/(direction+'-'+str(frame-1).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
(out/'native-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('STUDY_DONE',args.variant,flush=True)
