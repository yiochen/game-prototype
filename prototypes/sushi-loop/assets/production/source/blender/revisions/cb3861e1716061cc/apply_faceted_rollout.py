"""Apply approved finish to existing owned native models/actions through MCP.
No rebaking, model reconstruction, raster edits or user main-file writes.
"""
import bpy,sys,json,importlib.util,time,traceback,shutil
from pathlib import Path
state={}
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def write(path,value):path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def start(repo,output):
 global state
 repo=Path(repo);out=Path(output);base=repo/'prototypes/sushi-loop/assets/production/source/blender';old=sys.modules['s33_full_art_rollout'].state
 assert old['stage']=='complete' and len(old['runtime'].assets)==104
 runtime=load('s33_faceted_rollout_runtime',base/'capture_runtime.py');runtime.OUT=out;runtime.SCENE_NAME=old['scene'].name;runtime.assets=old['runtime'].assets
 style=load('s33_faceted_rollout_style',base/'catalog_style.py');sc=old['scene'];previous=bpy.context.window.scene
 # The prior iterative camera helper left unused camera/zero-light objects.
 # Unlink only unused scene-master capture objects from this owned scene.
 # Do not delete their datablocks or touch model collections/user scenes.
 keep=sc.camera
 if keep:keep['s33CaptureCamera']=True
 removed=[]
 for obj in list(sc.collection.objects):
  if obj.name.startswith('S33 ') and (obj.type=='LIGHT' or obj.type=='CAMERA' and obj!=keep):sc.collection.objects.unlink(obj);removed.append(obj.name)
 state={'repo':repo,'out':out,'base':base,'scene':sc,'runtime':runtime,'old':old,'style':style,'pending':list(runtime.assets),'done':0,'total':104,'stage':'materials','error':None,'started':time.time(),'unlinkedUnusedCaptureObjects':len(removed)}
 def status():write(out/'rollout-status.json',{k:v for k,v in state.items() if k in ('stage','done','total','current','error','started','unlinkedUnusedCaptureObjects','export')})
 def step():
  previous=bpy.context.window.scene
  try:
   bpy.context.window.scene=sc
   if state['pending']:
    aid=state['pending'].pop(0);a=runtime.assets[aid];style.apply(a,aid)
    camera=runtime.configure_camera(a['projection'],a['frame'],a['anchor'],a['scale'],a.get('camera_elevation_degrees'))
    folder=out/'source'/aid;record=old['records'][aid]
    keys=['id','projection','frame','anchor','scale','clips','footprint','height','sockets','ports','flow','camera_elevation_degrees','nonblocking','depth_layer','composition_context','facingPolicy','supportLayout','squareFooting','artStyle','directions','locomotion','conceptReference','variants']
    write(folder/'asset.json',{k:a[k] for k in keys if k in a});write(folder/'camera.json',camera);write(folder/'rig.json',record);write(out/'source/native-actions'/aid/'rig-actions.json',record)
    state['done']+=1;state['current']=aid
   else:
    state['stage']='saving';status()
    records={'version':1,'fps':12,'source':'native_actions.py','assets':old['records']};write(out/'source/native-actions/library-actions.json',records)
    runtime.show_only('chef-noor');a=runtime.assets['chef-noor'];old['native'].apply_clip(a,old['records']['chef-noor'],'idle',frame=4,direction='S',scene=sc)
    runtime.configure_camera(a['projection'],a['frame'],a['anchor'],a['scale'],a.get('camera_elevation_degrees'))
    state['export']=old['native'].save_production_library(out/'source/sushi-loop-world-library.blend',runtime.assets,records,sc,visible_asset='chef-noor',allow_unbaked_models=False)
    state['stage']='complete'
   status();return None if state['stage']=='complete' else .02
  except Exception:state['stage']='failed';state['error']=traceback.format_exc();status();return None
  finally:bpy.context.window.scene=previous
 state['step']=step;bpy.app.timers.register(step,first_interval=.05);status()
 return {'state':'started','assets':104,'output':str(out),'scene':sc.name,'unlinkedUnusedCaptureObjects':len(removed)}
