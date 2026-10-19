"""Turn an isolated issue33 library into a normal editable startup .blend.
Run in a SEPARATE background Blender process, never in the live MCP session:
 Blender --background library.blend --python finalize_project.py -- \
   --output /private/tmp/sushi33-finalized.blend --asset chef-lena --clip hold --frame 6
The caller freezes worker inputs and atomically replaces its canonical output
only after this new file and report have been verified.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import types
import bpy

BASE=pathlib.Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path));module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def arguments():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    parser.add_argument('--export-root',type=pathlib.Path,default=BASE/'export')
    parser.add_argument('--asset',default='chef-lena')
    parser.add_argument('--clip',default='hold')
    parser.add_argument('--frame',type=int,default=6,help='One-based native timeline frame, not sprite index')
    parser.add_argument('--direction',choices=['N','E','S','W'],default='S')
    parser.add_argument('--samples',type=int,default=32)
    parser.add_argument('--preview',type=pathlib.Path,help='Optional transparent native preview render; no image fitting')
    parser.add_argument('--overwrite-output',action='store_true')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    return parser.parse_args(argv)


def main():
    args=arguments();original=pathlib.Path(bpy.data.filepath).resolve();output=args.output.resolve()
    if not original.exists():raise RuntimeError('Load the saved isolated production library first')
    if output==original:raise RuntimeError('Output must differ from frozen worker input; caller replaces it after verification')
    if output.exists() and not args.overwrite_output:raise FileExistsError('Use a fresh output path or --overwrite-output: '+str(output))
    started=time.time();input_hash=sha(original)
    worker=load('s33_finalize_worker',BASE/'capture_worker.py')
    native=load('s33_finalize_native',BASE/'native_actions.py')
    runtime=load('s33_finalize_camera',BASE/'capture_runtime.py')
    scene=worker.native_scene()
    # The library-open warning may create exactly one empty startup Scene.
    # Reject any unrelated nonempty/renamed scene rather than including it.
    remove=[]
    for candidate in bpy.data.scenes:
        if candidate==scene:continue
        if candidate.name=='Scene' and len(candidate.objects)==0:remove.append(candidate)
        else:raise RuntimeError('Unexpected foreign scene; refusing main-file export: '+candidate.name)
    with bpy.context.temp_override(scene=scene,view_layer=scene.view_layers[0]):
        source=args.export_root.resolve()/'source'
        manifest=source/'native-actions'/'library-actions.json'
        actions=json.loads(manifest.read_text()).get('assets',{}) if manifest.exists() else {}
        asset,record,hashes=worker.reconstruct(args.asset,source,actions,scene)
        if args.clip not in record['clips']:raise KeyError('Missing requested native clip '+args.clip)
        config=record['clips'][args.clip]
        if not 1<=args.frame<=config['lastUniqueFrame']:raise ValueError('Frame must be1..'+str(config['lastUniqueFrame']))
        worker.show_only(scene,asset)
        camera,settings=worker.render_configuration(runtime,scene,asset,types.SimpleNamespace(samples=args.samples,threads=0))
        native.apply_clip(asset,record,args.clip,frame=args.frame,direction=args.direction,scene=scene)
        scene.render.fps=12;scene.render.filepath='//preview.png'
        # Set a useful editable selection and camera view in saved UI areas.
        arm=next((o for o in asset['collection'].all_objects if o.type=='ARMATURE'),None)
        active=arm or asset['root']
        for obj in scene.objects:obj.select_set(False)
        active.select_set(True);scene.view_layers[0].objects.active=active
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    space=area.spaces.active
                    if space.region_3d is not None:space.region_3d.view_perspective='CAMERA'
                    space.shading.color_type='MATERIAL'
        scene['startup_asset']=args.asset;scene['startup_clip']=args.clip;scene['startup_frame']=args.frame
        scene['project_role']='Editable issue33 native model and action project; isolated from user scenes'
        scene['source_library_sha256']=input_hash
        removed=[sc.name for sc in remove]
        for candidate in remove:bpy.data.scenes.remove(candidate)
        # There is now exactly one proper production scene, so background file
        # loading and subsequent UI opening have an unambiguous active scene.
        if len(bpy.data.scenes)!=1 or bpy.data.scenes[0]!=scene:raise RuntimeError('Main project scene isolation failed')
        if bpy.context.window:
            bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
        scene.view_layers[0].update()
        preview=None
        if args.preview:
            preview=args.preview.resolve();preview.parent.mkdir(parents=True,exist_ok=True)
            scene.render.filepath=str(preview);bpy.ops.render.render(write_still=True,scene=scene.name)
            info=worker.png_information(preview)
            expected=[asset['frame'][0]*asset['scale'],asset['frame'][1]*asset['scale']]
            if not info or [info['width'],info['height']]!=expected:raise RuntimeError('Invalid optional startup render')
            scene.render.filepath='//preview.png'
        output.parent.mkdir(parents=True,exist_ok=True)
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(output),check_existing=False,compress=True)
        report={'state':'complete','output':str(output),'sha256':sha(output),'bytes':output.stat().st_size,'input':str(original),'inputSha256':input_hash,
          'scene':scene.name,'sceneCount':len(bpy.data.scenes),'removedEmptyStartupScenes':removed,'userScenesIncluded':False,'startup':{'asset':args.asset,'clip':args.clip,'frame':args.frame,'direction':args.direction,'fps':12,'camera':scene.camera.name,'cameraRecord':camera,'render':settings},
          'ownedCollections':[c.name for c in scene.collection.children],'nativeActions':len([a for a in bpy.data.actions if a.get('source')=='native_actions.py']),
          'metadataHashes':hashes,'preview':str(preview) if preview else None,'sourceScriptSha256':sha(__file__),'seconds':time.time()-started}
        output.with_suffix('.finalized.json').write_text(json.dumps(report,indent=2)+'\n')
        print('S33_PROJECT_FINALIZED '+json.dumps(report),flush=True)


if __name__=='__main__':main()
