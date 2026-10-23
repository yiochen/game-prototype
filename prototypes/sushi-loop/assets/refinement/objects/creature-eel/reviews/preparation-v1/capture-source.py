import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib,importlib.util,time
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent

def module(name,file):
 spec=importlib.util.spec_from_file_location(name,str(P/'resources/blender'/file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
N=module('eel_judge_native','native_actions.py');R=module('eel_judge_capture','capture_runtime.py')
rig=json.loads((P/'resources/inputs/source-rig.json').read_text());cat=json.loads((P/'resources/inputs/catalog-object.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];col=root.users_collection[0]
# New isolated capture scene uses the actual original owned collection, not a rebuilt model.
R.SCENE_NAME='Eel judge original body replay';sc=R.scene();sc.collection.children.link(col)
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
for lc in bpy.context.view_layer.layer_collection.children:
 lc.exclude=False;lc.hide_viewport=False
bpy.context.view_layer.update()
a={'collection':col,'root':root}
record=R.configure_camera('character-orthographic',(448,512),(224,352),4)
record['camera']['orthoScale']=sc.camera.data.ortho_scale;record['camera']['shift']=[sc.camera.data.shift_x,sc.camera.data.shift_y]
record['sourceSHA256']=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();record['blenderVersion']=bpy.app.version_string
record['render']={'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'filterSize':sc.render.filter_size,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'dither':sc.render.dither_intensity,'filmTransparent':sc.render.film_transparent,'samples':getattr(sc.eevee,'taa_render_samples',None),'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None}
record['lights']=[{'name':o.name,'type':o.data.type,'power':o.data.energy,'size':o.data.size,'color':list(o.data.color),'location':list(o.location)} for o in sc.objects if o.type=='LIGHT']
(P/'native-camera.json').write_text(json.dumps(record,indent=2)+'\n')
meshes=[o for o in col.all_objects if o.type=='MESH'];arm=next(o for o in col.all_objects if o.type=='ARMATURE')
def points(raw=False):
 dg=bpy.context.evaluated_depsgraph_get();out=[];by={}
 for o in meshes:
  e=o if raw else o.evaluated_get(dg);me=e.data if raw else e.to_mesh()
  pp=[e.matrix_world@v.co for v in me.vertices];by[o.name]=pp;out+=pp
  if not raw:e.to_mesh_clear()
 return out,by
def bounds(pp):return [[min(v[k] for v in pp) for k in range(3)],[max(v[k] for v in pp) for k in range(3)]]
def plain(m):return [list(r) for r in m]
def delta(pp,qq):return max((x-y).length for x,y in zip(pp,qq))
measure={'asset':'creature-eel','sourceSHA256':record['sourceSHA256'],'enabledOwnedCollection':col.name,'rawDefinition':'Authored mesh vertices transformed through enabled actual object matrixWorld, without armature or bevel modifiers. These are an observation, not design locks.','evaluatedDefinition':'Actual depsgraph evaluated native action + modifiers, all owned body meshes.','views':{},'closures':{},'actions':{}}
for clip,c in rig['clips'].items():
 action=bpy.data.actions[c['actions'][0]['action']];curves=list(N._fcurves(action))
 measure['actions'][clip]={'name':action.name,'frameRange':list(action.frame_range),'extrapolations':sorted({f.extrapolation for f in curves}),'interpolations':sorted({k.interpolation for f in curves for k in f.keyframe_points}),'keyCount':sum(len(f.keyframe_points) for f in curves),'channels':[{'path':f.data_path,'index':f.array_index,'keyFrames':[k.co.x for k in f.keyframe_points]} for f in curves]}
 for facing in ['N','E','S','W']:
  ledger=measure['views'].setdefault(facing,[])
  for frame in range(1,13):
   N.apply_clip(a,rig,clip,frame,facing,sc);pp,by=points();raw,rby=points(True)
   ledger.append({'clip':clip,'frame':frame,'index':frame-1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':plain(root.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(pp),'meshBounds':{name:bounds(v) for name,v in by.items()},'armLocation':list(arm.location),'armRotation':list(arm.rotation_euler),'boneRotations':{b.name:list(b.rotation_euler) for b in arm.pose.bones}})
 N.apply_clip(a,rig,clip,1,'S',sc);start,_=points()
 N.apply_clip(a,rig,clip,12,'S',sc);last,_=points()
 N.apply_clip(a,rig,clip,13,'S',sc);f13,_=points()
 N.apply_clip(a,rig,clip,24,'S',sc);f24,_=points()
 measure['closures'][clip]={'loop':c['loop'],'maxVertexDelta1to13':delta(start,f13),'maxVertexDelta12to13':delta(last,f13),'maxVertexDelta12to24':delta(last,f24),'closingFrame':c['closingKeyFrame'],'oneShotTerminalHoldFrame':24 if not c['loop'] else None}
(P/'native-measurements.json').write_text(json.dumps(measure,indent=2)+'\n')
if '--measure-only' in sys.argv:
 print('MEASURE_ONLY_FINISHED',flush=True);sys.exit()
# Compact one-bounded replay: all 44 clip/facing representatives, two full motion strips, and closure/hold controls.
jobs=[]
for clip in rig['clips']:
 for facing in ['N','E','S','W']:jobs.append((clip,facing,10 if clip=='normal' else 7))
for clip,facing in [('normal','S'),('caught','E')]:
 for frame in range(1,13):
  if (clip,facing,frame) not in jobs:jobs.append((clip,facing,frame))
jobs.extend([('normal','S',13),('caught','E',24)])
records=[]
for i,(clip,facing,frame) in enumerate(jobs):
 N.apply_clip(a,rig,clip,frame,facing,sc)
 path=P/'captures'/clip/facing/f'{frame:03}.png';path.parent.mkdir(parents=True,exist_ok=True)
 sc.render.filepath=str(path);t=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
 pp,_=points();rec={'clip':clip,'direction':facing,'frame':frame,'publishedIndex':frame-1 if frame<=12 else None,'nativePath':str(path.relative_to(P)),'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':plain(root.matrix_world),'bounds':bounds(pp),'seconds':time.monotonic()-t};records.append(rec)
 (P/'capture-records.json').write_text(json.dumps({'nativeFrame':[1792,2048],'nativeScale':4,'records':records,'sourceSHA256':record['sourceSHA256'],'camera':'native-camera.json'},indent=2)+'\n')
 print('CAPTURE',i+1,len(jobs),clip,facing,frame,flush=True)
print('FINISHED',len(records),flush=True)
