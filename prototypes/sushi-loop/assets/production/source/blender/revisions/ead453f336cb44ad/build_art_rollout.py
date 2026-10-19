"""MCP authoring coordinator; isolated owned scene, incremental native baking.
Call start(repo, output, ids) through Blender MCP, then poll rollout-status.json.
Rendering is performed later by the frozen native-action worker.
"""
import bpy,json,sys,importlib.util,time,traceback,math
from pathlib import Path

state={}
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def start(repo,output,ids):
    global state
    base=Path(repo)/'prototypes/sushi-loop/assets/production/source/blender';out=Path(output)
    out.mkdir(parents=True,exist_ok=True)
    runtime=load('s33_rollout_runtime',base/'capture_runtime.py');runtime.OUT=out
    scene=bpy.data.scenes.new('S33 approved art rollout 2026-10-19');runtime.SCENE_NAME=scene.name
    previous=bpy.context.window.scene
    try:
        bpy.context.window.scene=scene
        library=load('s33_rollout_library',base/'production_library.py');library.load()
        native=load('s33_rollout_actions',base/'native_actions.py')
    finally:bpy.context.window.scene=previous
    state={'repo':str(repo),'base':base,'out':out,'runtime':runtime,'library':library,'native':native,'scene':scene,'ids':ids,'pending':list(ids),'bake':[],'records':{},'stage':'modeling','done':0,'total':len(ids),'error':None,'started':time.time()}
    def step():
        previous=bpy.context.window.scene
        try:
            bpy.context.window.scene=scene
            if state['pending']:
                aid=state['pending'].pop(0)
                asset=library.build(aid);runtime.register(aid,asset,asset['projection'],asset['frame'],asset['anchor'],asset['scale'])
                state['bake'].append(aid);state['done']+=1;state['current']=aid
            elif state['bake']:
                state['stage']='baking'
                aid=state['bake'].pop(0);a=runtime.assets[aid]
                # Keep historical native actions alive in the user's old scene.
                previous_actions=[act for act in bpy.data.actions if act.get('source')=='native_actions.py' and act.get('asset_id')==aid]
                for act in previous_actions:act['asset_id']='historical/'+aid
                try:record=state['native'].bake_asset(aid,a,out/'source/native-actions',replace=False)
                finally:
                    for act in previous_actions:act['asset_id']=aid
                state['records'][aid]=record;state['current']=aid
                folder=out/'source'/aid;folder.mkdir(parents=True,exist_ok=True)
                keys=['id','projection','frame','anchor','scale','clips','footprint','height','sockets','ports','flow','camera_elevation_degrees','nonblocking','depth_layer','composition_context','facingPolicy','supportLayout','squareFooting','artStyle','directions','locomotion','conceptReference','variants']
                info={k:a[k] for k in keys if k in a}
                cam=runtime.configure_camera(a['projection'],a['frame'],a['anchor'],a['scale'],a.get('camera_elevation_degrees'))
                (folder/'asset.json').write_text(json.dumps(info,indent=2)+'\n');(folder/'camera.json').write_text(json.dumps(cam,indent=2)+'\n');(folder/'rig.json').write_text(json.dumps(record,indent=2)+'\n')
            else:
                state['stage']='saving'
                summary={'version':1,'fps':12,'source':'native_actions.py','assets':state['records']}
                (out/'source/native-actions/library-actions.json').write_text(json.dumps(summary,indent=2)+'\n')
                report=state['native'].save_production_library(out/'source/sushi-loop-world-library.blend',runtime.assets,summary,scene,visible_asset=ids[0],allow_unbaked_models=False)
                state['export']=report;state['stage']='complete'
            save_status()
            return None if state['stage']=='complete' else .02
        except Exception:
            state['stage']='failed';state['error']=traceback.format_exc();save_status();return None
        finally:bpy.context.window.scene=previous
    state['step']=step
    bpy.app.timers.register(step,first_interval=.1);save_status()
    return {'scene':scene.name,'output':str(out),'assets':len(ids),'state':'started'}

def save_status():
    report={k:v for k,v in state.items() if k in ('stage','done','total','current','error','started','export')}
    report['models']=len(state.get('runtime').assets);report['baked']=len(state.get('records',{}))
    (state['out']/'rollout-status.json').write_text(json.dumps(report,indent=2)+'\n')
