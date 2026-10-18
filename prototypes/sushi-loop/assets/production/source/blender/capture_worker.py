"""Headless native-sprite worker. Author through MCP, capture saved native actions.
Example (root starts the process after MCP capture is idle):
 Blender --background library.blend --python capture_worker.py -- \
   --ids chef-lena --clips hold --directions S --frames 6 --worker test \
   --mcp-idle-confirmed --output /private/tmp/sushi33-worker-test
No model building, rigging, image fitting, image postprocessing or .blend writes.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import struct
import sys
import time
import traceback
import bpy

BASE=pathlib.Path(__file__).resolve().parent
PNG_SIGNATURE=b'\x89PNG\r\n\x1a\n'


def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def json_hash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def write_json(path,value):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n');os.replace(temporary,path)


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path));module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def words(values):
    return [word for value in (values or []) for word in value.split(',') if word]


def arguments():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids',nargs='+',required=True)
    parser.add_argument('--clips',nargs='+')
    parser.add_argument('--directions',nargs='+',default=['N','E','S','W'])
    parser.add_argument('--frames',help='Zero-based comma-separated indices or inclusive ranges; omitted means every authored frame')
    parser.add_argument('--worker',default='worker-'+str(os.getpid()))
    parser.add_argument('--export-root',type=pathlib.Path,default=BASE/'export')
    parser.add_argument('--output',type=pathlib.Path,help='Raw-frame root; default export-root/raw-frames')
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--threads',type=int,default=0)
    parser.add_argument('--mcp-idle-confirmed',action='store_true',help='Root has stopped live MCP capture before launching CLI workers')
    parser.add_argument('--overwrite',action='store_true',help='Render even PNGs with matching completed receipts')
    parser.add_argument('--limit-frames',type=int,help='Diagnostic cap; omitted captures complete requested clips')
    parser.add_argument('--dry-run',action='store_true')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    return parser.parse_args(argv)


def indices(expression,count):
    if expression is None:return list(range(count))
    result=set()
    for token in expression.split(','):
        if '-' in token:
            lo,hi=(int(x) for x in token.split('-',1));result.update(range(lo,hi+1))
        else:result.add(int(token))
    if any(i<0 or i>=count for i in result):raise ValueError('Frame index outside authored range0..'+str(count-1))
    return sorted(result)


def png_information(path):
    path=pathlib.Path(path)
    try:
        data=path.read_bytes()
        if len(data)<45 or data[:8]!=PNG_SIGNATURE or data[12:16]!=b'IHDR' or data[-8:-4]!=b'IEND':return None
        width,height=struct.unpack('>II',data[16:24])
        return {'width':width,'height':height,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    except OSError:return None


def complete_receipt(png,version,dimensions):
    receipt=png.with_suffix('.capture.json')
    if not receipt.exists():return None
    try:
        value=json.loads(receipt.read_text())
        if value.get('nativeVersion')!=version or value.get('state')!='complete':return None
        observed=png_information(png)
        if not observed or [observed['width'],observed['height']]!=list(dimensions):return None
        if observed['sha256']!=value.get('sha256') or observed['bytes']!=value.get('bytes'):return None
        return value
    except (OSError,ValueError,KeyError):return None


def layer_nodes(node):
    yield node
    for child in node.children:yield from layer_nodes(child)


def native_scene():
    candidates=[sc for sc in bpy.data.scenes if sc.get('source')=='native_actions.py' and sc.get('issue')==33]
    if len(candidates)!=1:raise RuntimeError('Expected exactly one isolated issue33 native export scene; found'+str(len(candidates)))
    scene=candidates[0]
    if bpy.context.window:
        bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
    scene.view_layers[0].update()
    return scene


def reconstruct(aid,source,actions,scene):
    asset_path=source/aid/'asset.json';rig_path=source/aid/'rig.json'
    if not asset_path.exists():raise FileNotFoundError('Missing authored asset metadata: '+str(asset_path))
    asset=json.loads(asset_path.read_text())
    rig=json.loads(rig_path.read_text()) if rig_path.exists() else actions.get(aid)
    if rig is None:raise FileNotFoundError('Missing native action record for '+aid)
    root=bpy.data.objects.get(rig['groundRootObject'])
    if root is None:raise KeyError('Missing saved native ground root '+rig['groundRootObject'])
    collection=next((c for c in scene.collection.children if root in list(c.all_objects)),None)
    if collection is None:raise KeyError('Ground root is outside isolated production collections: '+aid)
    declared=root.get('production_id') or root.get('asset_id')
    if declared not in (aid,aid.replace('-','_')) and root.get('production_id')!=aid:
        # Stable orchestration IDs may intentionally alias older native builder IDs.
        if asset.get('id')!=aid:raise ValueError('Asset identity mismatch '+aid+' vs '+str(declared))
    asset.update(root=root,collection=collection)
    asset['clips']=rig['clips']
    for key in ('frame','anchor','scale','projection'):
        if key not in asset:raise KeyError('Missing fixed capture metadata '+aid+':'+key)
    return asset,rig,{'assetJson':sha(asset_path),'rigJson':sha(rig_path) if rig_path.exists() else json_hash(rig)}


def show_only(scene,asset):
    tree=scene.view_layers[0].layer_collection
    if tree is None:raise RuntimeError('Missing active native collection tree')
    for layer in layer_nodes(tree):layer.exclude=False
    for collection in scene.collection.children:
        selected=collection==asset['collection']
        collection.hide_render=not selected;collection.hide_viewport=not selected
    scene.view_layers[0].update()


def render_configuration(runtime,scene,asset,args):
    # Reuse the exact MCP camera/calibration/lighting/color implementation. The
    # adapter is in this worker process only; capture_runtime.py is not edited.
    runtime.scene=lambda:scene;runtime.SCENE_NAME=scene.name
    record=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),int(asset['scale']),asset.get('camera_elevation_degrees'))
    eevee=getattr(scene,'eevee',None);sample_property=None
    for name in ('taa_render_samples','taa_samples'):
        if eevee is not None and hasattr(eevee,name):setattr(eevee,name,args.samples);sample_property=name;break
    if args.threads:
        scene.render.threads_mode='FIXED';scene.render.threads=args.threads
    scene.render.use_file_extension=True
    scene.render.use_persistent_data=True
    return record,{'engine':scene.render.engine,'samples':getattr(eevee,sample_property) if sample_property else None,'sampleProperty':sample_property,'threads':args.threads or 'AUTO','filmTransparent':scene.render.film_transparent,'colorMode':scene.render.image_settings.color_mode,'colorDepth':scene.render.image_settings.color_depth}


def assert_idle(export,args):
    path=export/'capture-status.json'
    if path.exists():
        state=json.loads(path.read_text())
        incomplete=state.get('state')=='rendering' and int(state.get('done',0))<int(state.get('total',0))
        if incomplete and not args.mcp_idle_confirmed:raise RuntimeError('Live MCP capture status is incomplete; stop it and pass --mcp-idle-confirmed')
    if not args.mcp_idle_confirmed:raise RuntimeError('Pass --mcp-idle-confirmed only after root has stopped MCP capture; workers must not share its frame jobs')


@contextlib.contextmanager
def asset_lock(folder,aid,worker,version):
    folder.mkdir(parents=True,exist_ok=True);path=folder/(aid+'.lock')
    claim={'assetId':aid,'worker':worker,'pid':os.getpid(),'nativeVersion':version,'startedAtUnix':time.time()}
    try:fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        prior=json.loads(path.read_text());pid=int(prior.get('pid',-1));alive=True
        try:os.kill(pid,0)
        except ProcessLookupError:alive=False
        except PermissionError:pass
        if alive:raise RuntimeError('Asset already reserved: '+json.dumps(prior))
        # Only an expired lock in this task-owned lock folder is removed.
        path.unlink();fd=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'w') as file:json.dump(claim,file)
        yield
    finally:
        if path.exists():
            current=json.loads(path.read_text())
            if current.get('pid')==os.getpid() and current.get('worker')==worker:path.unlink()


def main():
    args=arguments();args.worker=''.join(c if c.isalnum() or c in '-_' else '_' for c in args.worker)
    args.ids=list(dict.fromkeys(words(args.ids)));directions=words(args.directions);requested_clips=words(args.clips)
    if not directions or any(d not in ('N','E','S','W') for d in directions):raise ValueError('Directions must be N E S W')
    export=args.export_root.resolve();raw=(args.output or export/'raw-frames').resolve();status_dir=export/'capture-workers'
    assert_idle(export,args)
    scene=native_scene();runtime=load_module('s33_worker_camera_runtime',BASE/'capture_runtime.py');native=load_module('s33_worker_native_actions',BASE/'native_actions.py')
    source=export/'source';manifest=source/'native-actions'/'library-actions.json'
    action_records=json.loads(manifest.read_text()).get('assets',{}) if manifest.exists() else {}
    blend=pathlib.Path(bpy.data.filepath).resolve()
    if not blend.exists():raise FileNotFoundError('Worker must load a saved production .blend')
    version_base={'blend':sha(blend),'runtime':sha(BASE/'capture_runtime.py'),'nativeActions':sha(BASE/'native_actions.py'),'worker':sha(__file__),'blenderVersion':bpy.app.version_string,'samples':args.samples,'sourceScale':'authored'}
    status={'state':'planning','worker':args.worker,'pid':os.getpid(),'ids':args.ids,'done':0,'rendered':0,'skipped':0,'total':0,'startedAtUnix':time.time(),'nativeSource':version_base,'blend':str(blend),'rawRoot':str(raw),'error':None}
    status_path=status_dir/(args.worker+'.status.json');write_json(status_path,status)
    prepared=[]
    try:
        with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
            for aid in args.ids:
                asset,rig,hashes=reconstruct(aid,source,action_records,scene)
                clips=requested_clips or list(rig['clips'])
                if any(clip not in rig['clips'] for clip in clips):raise ValueError('Requested clip absent from '+aid)
                jobs=[(clip,direction,index) for clip in clips for direction in directions for index in indices(args.frames,int(rig['clips'][clip]['frames']))]
                prepared.append((aid,asset,rig,hashes,jobs));status['total']+=len(jobs)
            if args.limit_frames is not None:status['total']=min(status['total'],args.limit_frames)
            status['state']='dry-run' if args.dry_run else 'rendering';write_json(status_path,status)
            if args.dry_run:
                print('S33_WORKER_PLAN '+json.dumps({'ids':args.ids,'frames':status['total'],'rawRoot':str(raw)}),flush=True);return
            stop=False
            for aid,asset,rig,hashes,jobs in prepared:
                version=json_hash({**version_base,**hashes,'assetId':aid})
                with asset_lock(status_dir/'locks',aid,args.worker,version):
                    show_only(scene,asset)
                    camera,settings=render_configuration(runtime,scene,asset,args)
                    dimensions=[int(asset['frame'][0])*int(asset['scale']),int(asset['frame'][1])*int(asset['scale'])]
                    write_json(status_dir/'camera'/args.worker/(aid+'.json'),{'nativeVersion':version,'camera':camera,'render':settings})
                    for clip,direction,index in jobs:
                        if args.limit_frames is not None and status['done']>=args.limit_frames:stop=True;break
                        png=raw/aid/(clip+'-'+direction)/(str(index).zfill(3)+'.png')
                        receipt=None if args.overwrite else complete_receipt(png,version,dimensions)
                        if receipt:status['skipped']+=1
                        else:
                            native.apply_clip(asset,rig,clip,frame=index+1,direction=direction,scene=scene)
                            # Camera is independent of frame and facing. Never fit
                            # a particular pose or derive bounds from alpha.
                            png.parent.mkdir(parents=True,exist_ok=True)
                            temporary=png.with_name(png.stem+'.'+args.worker+'.partial.png')
                            scene.render.filepath=str(temporary);began=time.monotonic()
                            bpy.ops.render.render(write_still=True,scene=scene.name)
                            observed=png_information(temporary)
                            if not observed or [observed['width'],observed['height']]!=dimensions:raise RuntimeError('Incomplete or wrongly sized render '+str(temporary))
                            os.replace(temporary,png)
                            write_json(png.with_suffix('.capture.json'),{'state':'complete','assetId':aid,'clip':clip,'direction':direction,'index':index,'fps':12,'nativeVersion':version,'worker':args.worker,'seconds':time.monotonic()-began,**observed})
                            status['rendered']+=1
                        status['done']+=1;status.update(current=[aid,clip,direction,index],updatedAtUnix=time.time(),currentNativeVersion=version)
                        write_json(status_path,status)
                        print('S33_WORKER_PROGRESS '+json.dumps({k:status[k] for k in ('worker','done','total','rendered','skipped','current')}),flush=True)
                if stop:break
            status.update(state='complete',finishedAtUnix=time.time());write_json(status_path,status)
            print('S33_WORKER_COMPLETE '+json.dumps(status),flush=True)
    except Exception:
        status.update(state='failed',error=traceback.format_exc(),finishedAtUnix=time.time());write_json(status_path,status)
        print('S33_WORKER_FAILED '+status['error'],flush=True)
        raise


if __name__=='__main__':main()
