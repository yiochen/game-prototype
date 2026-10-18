"""ROOT-only Blender MCP verification of actual baked chef utensils.

  ns={'__file__':'/private/tmp/sushi33-production/validate_native_chef_utensils.py'}
  exec(compile(open(ns['__file__']).read(),ns['__file__'],'exec'),ns)
  result=ns['validate_native_chef_utensils'](r,N)

Checks384 actual work samples (8chefs x4facings x12frames). For the96 other
clip/facing cases, samples actual hidden state and independently checks every
authored visibility key is hidden with CONSTANT interpolation. No pose callbacks,
geometry edits, rendering or blend saves. Optional sampler restoration audit is
separate and exercises the new context manager without baking actions.
"""
import json
import os
from pathlib import Path
import time
import bpy
from mathutils import Vector

_UTENSIL_BASE=Path('/private/tmp/sushi33-production')


def _utensil_write(path,report):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,path)


def _utensil_path(layer,target):
    if layer.collection==target:return [layer]
    for child in layer.children:
        path=_utensil_path(child,target)
        if path:return [layer]+path
    return []


def _utensil_centroid(obj):
    if obj.type!='MESH' or not obj.data.vertices:raise ValueError('Missing actual modeled palm geometry')
    return sum((obj.matrix_world@vertex.co for vertex in obj.data.vertices),Vector())/len(obj.data.vertices)


def validate_native_chef_utensils(runtime,native,report_path=None,ids=None,directions=None,tolerance=.002):
    if getattr(runtime,'job_status',{}).get('state')=='rendering':raise RuntimeError('Wait for live capture before temporary evaluation')
    filtered=ids is not None or directions is not None
    ids=list(ids) if ids is not None else sorted(aid for aid in runtime.assets if aid.startswith('chef-') and aid!='chef-blackboard')
    directions=list(directions) if directions is not None else ['S','E','N','W']
    output=Path(report_path) if report_path else _UTENSIL_BASE/'export/validation/native-chef-utensils.json'
    report={'version':1,'ok':False,'source':'actual evaluated native utensil root and deforming right palm; actual visibility plus authored constant visibility keys',
            'createdAtUnix':time.time(),'blendPath':bpy.data.filepath,'filtered':filtered,'assetsChecked':0,
            'workCasesChecked':0,'workSamplesChecked':0,'outsideWorkCasesChecked':0,'outsideWorkSamplesChecked':0,
            'errors':[],'cases':[],'report':str(output)}
    if not filtered and len(ids)!=8:report['errors'].append({'case':'inventory','message':'Expected all8 native chefs, found '+str(len(ids))})
    scene=bpy.data.scenes.get(getattr(runtime,'SCENE_NAME','Sushi33 Production'))
    if scene is None:raise RuntimeError('Missing production scene')
    window=bpy.context.window;old_scene=window.scene if window else bpy.context.scene
    old_layer=window.view_layer if window else bpy.context.view_layer
    old_active=old_layer.objects.active;old_selected=list(bpy.context.selected_objects)
    old_frame=(scene.frame_current,scene.frame_subframe)
    old_settings=(scene.render.fps,scene.render.fps_base,scene.frame_start,scene.frame_end,scene.camera)
    owners={};objects={};bones=[];collections=[];layers={}
    try:
        if window:window.scene=scene;window.view_layer=scene.view_layers[0]
        elif bpy.context.scene!=scene:raise RuntimeError('Current scene is not production')
        for aid in ids:
            asset=runtime.assets[aid];collection=asset['collection']
            collections.append((collection,collection.hide_render,collection.hide_viewport))
            asset_objects=native._all_objects(asset)
            for obj in asset_objects:
                objects.setdefault(obj.as_pointer(),(obj,obj.matrix_basis.copy(),obj.rotation_mode,obj.hide_render,obj.hide_viewport))
                if obj.type=='ARMATURE':bones.extend((bone,bone.matrix_basis.copy(),bone.rotation_mode) for bone in obj.pose.bones)
            for owner in native._animation_owners(asset_objects,native._node_sockets(asset_objects),native._shape_meshes(asset_objects)):
                if owner.as_pointer() in owners:continue
                ad=owner.animation_data
                owners[owner.as_pointer()]=(owner,ad is not None,ad.action if ad else None,getattr(getattr(ad,'action_slot',None),'identifier',None) if ad else None,[(track,track.mute) for track in ad.nla_tracks] if ad else [])
        for aid in ids:
            asset=runtime.assets[aid];collection=asset['collection']
            collection.hide_render=False;collection.hide_viewport=False
            for layer in _utensil_path(scene.view_layers[0].layer_collection,collection):
                layers.setdefault(layer.as_pointer(),(layer,layer.exclude,layer.hide_viewport));layer.exclude=False;layer.hide_viewport=False
            bpy.context.view_layer.update()
            composition=asset.get('held_composition',{});utensil=composition.get('utensilRoot')
            if utensil is None:raise ValueError('Missing native utensilRoot '+aid)
            meshes=[obj for obj in utensil.children_recursive if obj.type=='MESH']
            if len(meshes)<2:raise ValueError('Expected native knife handle and blade geometry')
            palm=asset['parts'].get('palm_R')
            if palm is None:raise ValueError('Missing modeled right palm '+aid)
            record=getattr(runtime,'native_records',{}).get(aid)
            if record is None:record=json.loads((_UTENSIL_BASE/'export/source'/aid/'rig.json').read_text())
            for clip,config in record['clips'].items():
                count=int(config['frames']);is_work=clip=='work'
                selected=range(count) if is_work else [0]
                for direction in directions:
                    row={'id':aid,'clip':clip,'direction':direction,'work':is_work,'ok':False,'errors':[]}
                    try:
                        if utensil.parent!=asset['root'] or utensil.constraints:raise ValueError('Utensil does not have the declared unconstrained character-root parent')
                        if is_work and (count!=12 or config.get('fps')!=12):raise ValueError('Expected unchanged12-frame12fps work clip')
                        native.apply_clip(asset,record,clip,frame=1,direction=direction,scene=scene)
                        maximum=0.;worst=None
                        for index in selected:
                            scene.frame_set(index+1);bpy.context.view_layer.update()
                            graph=bpy.context.evaluated_depsgraph_get()
                            expected=_utensil_centroid(palm.evaluated_get(graph))
                            actual=utensil.evaluated_get(graph).matrix_world.translation.copy()
                            error=(actual-expected).length
                            if worst is None or error>worst['error']:worst={'frame':index,'error':error,'actualRoot':list(actual),'rightPalm':list(expected)}
                            maximum=max(maximum,error)
                            for mesh in meshes:
                                if bool(mesh.hide_render)==is_work or bool(mesh.hide_viewport)==is_work:
                                    row['errors'].append('Incorrect actual knife visibility at frame'+str(index)+': '+mesh.name)
                            if is_work:report['workSamplesChecked']+=1
                            else:report['outsideWorkSamplesChecked']+=1
                        row['sampledFrames']=list(selected)
                        if is_work:
                            row.update(maximumUtensilToPalmError=maximum,worst=worst)
                            if maximum>tolerance:row['errors'].append('Utensil root misses actual evaluated right palm; maximum world error='+str(maximum))
                        else:
                            # Every unique and closing key must hide the knife;
                            # CONSTANT interpolation proves the intervals too.
                            row['visibilityKeysProveEntireClip']=True
                            for mesh in meshes:
                                target=next((target for target in config['actions'] if target.get('ownerName')==mesh.name and target.get('ownerType')=='Object'),None)
                                if target is None:raise ValueError('Missing native knife visibility action for '+mesh.name)
                                action=bpy.data.actions.get(target['action'])
                                if action is None:raise ValueError('Missing recorded knife action '+target['action'])
                                for path in ('hide_render','hide_viewport'):
                                    curves=[curve for curve in native._fcurves(action) if curve.data_path==path]
                                    if len(curves)!=1 or not curves[0].keyframe_points or any(key.co.y<.5 or key.interpolation!='CONSTANT' for key in curves[0].keyframe_points):
                                        row['visibilityKeysProveEntireClip']=False
                                        row['errors'].append('Native outside-work '+path+' keys are not constantly hidden: '+mesh.name)
                                    if mesh.animation_data and any(driver.data_path==path for driver in mesh.animation_data.drivers):
                                        row['errors'].append('Unexpected visibility driver bypasses the native clip contract: '+mesh.name)
                        row['ok']=not row['errors']
                    except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
                    if is_work:report['workCasesChecked']+=1
                    else:report['outsideWorkCasesChecked']+=1
                    report['cases'].append(row)
                    report['errors'].extend({'case':aid+'/'+clip+'/'+direction,'message':error} for error in row['errors'])
            report['assetsChecked']+=1
            _,render,viewport=next(state for state in collections if state[0]==collection)
            collection.hide_render=render;collection.hide_viewport=viewport
    finally:
        restore_errors=[]
        for owner,had_ad,action,slot,tracks in owners.values():
            try:
                if had_ad:
                    native._assign(owner,action,slot)
                    for track,mute in tracks:track.mute=mute
                elif owner.animation_data:owner.animation_data_clear()
            except Exception as exc:restore_errors.append(str(exc))
        try:
            fps,fps_base,start,end,camera=old_settings
            scene.render.fps=fps;scene.render.fps_base=fps_base;scene.frame_start=start;scene.frame_end=end;scene.camera=camera
            scene.frame_set(old_frame[0],subframe=old_frame[1])
            for obj,matrix,mode,render,viewport in objects.values():
                obj.rotation_mode=mode;obj.matrix_basis=matrix;obj.hide_render=render;obj.hide_viewport=viewport
            for bone,matrix,mode in bones:bone.rotation_mode=mode;bone.matrix_basis=matrix
            for collection,render,viewport in collections:collection.hide_render=render;collection.hide_viewport=viewport
            for layer,exclude,viewport in layers.values():layer.exclude=exclude;layer.hide_viewport=viewport
            if window:window.scene=old_scene;window.view_layer=old_layer
            if set(bpy.context.selected_objects)!=set(old_selected):
                for obj in list(bpy.context.selected_objects):obj.select_set(False)
                for obj in old_selected:obj.select_set(True)
            old_layer.objects.active=old_active;bpy.context.view_layer.update()
        except Exception as exc:restore_errors.append(str(exc))
        report['presentationRestored']=not restore_errors
        if restore_errors:report['errors'].append({'case':'presentation-restore','message':'; '.join(restore_errors)})
    report['ok']=not report['errors'] and report['assetsChecked']==len(ids) and report['workSamplesChecked']==len(ids)*len(directions)*12
    _utensil_write(output,report);return report


def validate_sampler_visibility_restoration(runtime,native,report_path=None,ids=None):
    """Optional normal/exception exit check of the sampler; creates no actions."""
    if getattr(runtime,'job_status',{}).get('state')=='rendering':raise RuntimeError('Wait for live capture')
    ids=list(ids) if ids is not None else ['chef-noor','customer-samir']
    output=Path(report_path) if report_path else _UTENSIL_BASE/'export/validation/native-sampler-visibility-restoration.json'
    report={'ok':False,'cases':[],'errors':[],'report':str(output),'source':'actual sampler context enter/exit, with no pose callback or bake'}
    class ExpectedExit(Exception):pass
    for aid in ids:
        asset=runtime.assets[aid]
        path=_utensil_path(bpy.context.view_layer.layer_collection,asset['collection'])
        if not path:raise ValueError('Target is not in current production view layer: '+aid)
        armatures=[obj for obj in native._all_objects(asset) if obj.type=='ARMATURE']
        def snapshot():
            return {'layers':[(layer.name,layer.exclude,layer.hide_viewport) for layer in path],
                    'collections':[(layer.collection.name,layer.collection.hide_viewport) for layer in path],
                    'rigs':[(obj.name,obj.hide_viewport,obj.hide_get()) for obj in armatures]}
        before=snapshot()
        layer_restore=[(layer,layer.exclude,layer.hide_viewport,layer.collection.hide_viewport) for layer in path]
        rig_restore=[(obj,obj.hide_viewport,obj.hide_get()) for obj in armatures]
        def restore_caller():
            for layer,exclude,viewport,collection_viewport in layer_restore:
                layer.exclude=False;layer.hide_viewport=False;layer.collection.hide_viewport=False
            bpy.context.view_layer.update()
            for obj,viewport,hidden in rig_restore:obj.hide_viewport=viewport;obj.hide_set(hidden)
            for layer,exclude,viewport,collection_viewport in reversed(layer_restore):
                layer.exclude=exclude;layer.hide_viewport=viewport;layer.collection.hide_viewport=collection_viewport
            bpy.context.view_layer.update()
        for exceptional in (False,True):
            try:
                with native._sampling_visibility(asset):
                    inside=snapshot()
                    exposed=all(not exclude and not viewport for _,exclude,viewport in inside['layers']) and all(not viewport for _,viewport in inside['collections']) and all(not viewport and not hidden for _,viewport,hidden in inside['rigs'])
                    if not exposed:raise AssertionError('Sampler did not expose the actual collection path and rig')
                    if exceptional:raise ExpectedExit()
            except ExpectedExit:pass
            except Exception as exc:report['errors'].append({'asset':aid,'message':str(exc)})
            after=snapshot();restored=before==after
            report['cases'].append({'id':aid,'exceptionExit':exceptional,'restored':restored,'before':before,'after':after})
            if not restored:
                report['errors'].append({'asset':aid,'message':'Sampler changed caller visibility after exit'})
                restore_caller()
    report['ok']=not report['errors'];_utensil_write(output,report);return report
