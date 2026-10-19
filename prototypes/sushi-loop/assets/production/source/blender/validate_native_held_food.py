"""ROOT-only MCP audit: baked held food versus actual evaluated palm geometry.

No pose callback, custom sampled socket metadata, render or model edit runs.
  ns={'__file__':'/private/tmp/sushi33-production/validate_native_held_food.py'}
  exec(compile(open(ns['__file__']).read(),ns['__file__'],'exec'),ns)
  result=ns['validate_native_held_food'](r,N,report_path='...before.json',
      ids=['customer-samir'],directions=['W'],frames=[9])
Omit filters for all12 characters, relevant holding clips, four facings and
every native frame. Write separate before/after paths to preserve real evidence.
"""
import json
import os
from pathlib import Path
import time
import bpy
from mathutils import Vector

_HELD_BASE=Path('/private/tmp/sushi33-production')
_HELD_OFFSET=Vector((0.,-.025,.018))


def _held_centroid(obj):
    if obj.type!='MESH' or not obj.data.vertices:
        raise ValueError('Expected nonempty native palm mesh: '+obj.name)
    return sum((obj.matrix_world@vertex.co for vertex in obj.data.vertices),Vector())/len(obj.data.vertices)


def _held_children(root):
    return [obj for obj in root.children_recursive if obj.type=='MESH']


def validate_native_held_food(runtime,native,report_path=None,ids=None,directions=None,frames=None,tolerance=.002):
    if getattr(runtime,'job_status',{}).get('state')=='rendering':
        raise RuntimeError('Wait for live capture before temporary action evaluation')
    filtered=ids is not None or frames is not None or directions is not None
    ids=list(ids) if ids is not None else sorted(aid for aid in runtime.assets if (aid.startswith('chef-') and aid!='chef-blackboard') or aid.startswith('customer-'))
    directions=list(directions) if directions is not None else ['S','E','N','W']
    output=Path(report_path) if report_path else _HELD_BASE/'export/validation/native-held-food.json'
    report={'version':1,'ok':False,'source':'actual evaluated baked food-root and deforming palm meshes; no custom socket metadata or pose callbacks',
            'createdAtUnix':time.time(),'blendPath':bpy.data.filepath,'blenderVersion':bpy.app.version_string,
            'registeredFoodRootOffset':list(_HELD_OFFSET),'toleranceWorldUnits':tolerance,
            'filtered':filtered,
            'assetsChecked':0,'casesChecked':0,'samplesChecked':0,'errors':[],'cases':[],'report':str(output)}
    # `filtered` is informational; exact checked counts below establish coverage.
    report['selectedIds']=ids;report['selectedDirections']=directions
    window=bpy.context.window;old_scene=window.scene if window else bpy.context.scene
    old_layer=window.view_layer if window else bpy.context.view_layer
    old_active=old_layer.objects.active;old_selected=list(bpy.context.selected_objects)
    scene=bpy.data.scenes.get(getattr(runtime,'SCENE_NAME','Sushi33 Production'))
    if scene is None:raise RuntimeError('Production scene is not loaded')
    old_frame=(scene.frame_current,scene.frame_subframe)
    old_settings=(scene.render.fps,scene.render.fps_base,scene.frame_start,scene.frame_end,scene.camera)
    owners={};objects={};bones=[];collections=[];layers={};expected_samples=0
    try:
        if window:window.scene=scene;window.view_layer=scene.view_layers[0]
        elif bpy.context.scene!=scene:raise RuntimeError('Current scene is not production')
        for aid in ids:
            asset=runtime.assets[aid]
            collection=asset['collection'];collections.append((collection,collection.hide_render,collection.hide_viewport))
            asset_objects=native._all_objects(asset)
            for obj in asset_objects:
                objects.setdefault(obj.as_pointer(),(obj,obj.matrix_basis.copy(),obj.rotation_mode,obj.hide_render,obj.hide_viewport))
                if obj.type=='ARMATURE':bones.extend((bone,bone.matrix_basis.copy(),bone.rotation_mode) for bone in obj.pose.bones)
            for owner in native._animation_owners(asset_objects,native._node_sockets(asset_objects),native._shape_meshes(asset_objects)):
                if owner.as_pointer() in owners:continue
                ad=owner.animation_data
                owners[owner.as_pointer()]=(owner,ad is not None,ad.action if ad else None,getattr(getattr(ad,'action_slot',None),'identifier',None) if ad else None,[(track,track.mute) for track in ad.nla_tracks] if ad else [])
        def find_path(layer,target):
            if layer.collection==target:return [layer]
            for child in layer.children:
                path=find_path(child,target)
                if path:return [layer]+path
            return []
        for aid in ids:
            asset=runtime.assets[aid];collection=asset['collection']
            collection.hide_render=False;collection.hide_viewport=False
            for layer in find_path(scene.view_layers[0].layer_collection,collection):
                layers.setdefault(layer.as_pointer(),(layer,layer.exclude,layer.hide_viewport));layer.exclude=False;layer.hide_viewport=False
            bpy.context.view_layer.update()
            record=getattr(runtime,'native_records',{}).get(aid)
            if record is None:record=json.loads((_HELD_BASE/'export/source'/aid/'rig.json').read_text())
            composition=asset.get('held_composition',{})
            food=composition.get('foodRoot')
            if food is None:
                report['errors'].append({'case':aid,'message':'Native held-food root is missing'})
                continue
            root=asset['root'];arm=asset.get('armature') or asset.get('rig')
            if arm is None:raise ValueError('Missing character armature '+aid)
            relevant=['hold','load'] if aid.startswith('chef-') else ['seated_wait','eat']
            for clip in relevant:
                if clip not in record['clips'] and clip.replace('_','-') in record['clips']:clip=clip.replace('_','-')
                config=record['clips'][clip];count=int(config['frames'])
                selected=list(frames) if frames is not None else list(range(count))
                expected_samples+=len(selected)*len(directions)
                if any(index<0 or index>=count for index in selected):raise ValueError('Frame filter outside native clip '+aid+'/'+clip)
                for direction in directions:
                    label=aid+'/'+clip+'/'+direction
                    row={'id':aid,'clip':clip,'direction':direction,'ok':False,'samples':len(selected),'errors':[],
                         'foodRoot':food.name,'foodParent':food.parent.name if food.parent else None,
                         'foodConstraints':[constraint.type for constraint in food.constraints],
                         'recordedFoodAction':any(target.get('ownerName')==food.name for target in config['actions'])}
                    try:
                        if food.parent!=root:raise ValueError('Food root is not parented directly to the declared character ground root')
                        if food.constraints:raise ValueError('Unexpected food-root constraint affects the declared root-local attachment')
                        native.apply_clip(asset,record,clip,frame=selected[0]+1,direction=direction,scene=scene)
                        maximum_error=0.;maximum_palm_error=0.;worst=None;max_angle_error=0.;visibility_failures=[]
                        for index in selected:
                            scene.frame_set(index+1);bpy.context.view_layer.update()
                            graph=bpy.context.evaluated_depsgraph_get()
                            evaluated_arm=arm.evaluated_get(graph);evaluated_root=root.evaluated_get(graph)
                            evaluated_food=food.evaluated_get(graph)
                            palms={};palm_errors=[]
                            for side in ('L','R'):
                                palm=asset['parts'].get('palm_'+side)
                                if palm is None:raise ValueError('Missing modeled palm mesh '+side)
                                centroid=_held_centroid(palm.evaluated_get(graph));palms[side]=centroid
                                # A second independent route through the actual
                                # deform bone verifies this is its palm socket.
                                rest_center=sum((v.co for v in palm.data.vertices),Vector())/len(palm.data.vertices)
                                rest_in_arm=arm.matrix_world.inverted()@palm.matrix_world@rest_center
                                bone=evaluated_arm.pose.bones['hand_'+side]
                                bone_socket=evaluated_arm.matrix_world@bone.matrix@arm.data.bones['hand_'+side].matrix_local.inverted()@rest_in_arm
                                palm_errors.append((centroid-bone_socket).length)
                            expected=(palms['L']+palms['R'])*.5+evaluated_root.matrix_world.to_3x3()@_HELD_OFFSET
                            actual=evaluated_food.matrix_world.translation.copy()
                            error=(actual-expected).length
                            maximum_palm_error=max(maximum_palm_error,*palm_errors)
                            maximum_error=max(maximum_error,error)
                            # Food remains horizontal in root space at each
                            # captured facing; no camera-space fitting is used.
                            relative=evaluated_root.matrix_world.inverted()@evaluated_food.matrix_world
                            max_angle_error=max(max_angle_error,relative.to_quaternion().angle)
                            visible=[mesh for mesh in _held_children(food) if not mesh.hide_render]
                            if not visible:visibility_failures.append(index)
                            if worst is None or error>worst['error']:
                                worst={'frame':index,'error':error,'actualRoot':list(actual),'expectedRoot':list(expected),'leftPalm':list(palms['L']),'rightPalm':list(palms['R']),'rootLocalFood':list(relative.translation)}
                            report['samplesChecked']+=1
                        row.update(maximumFoodToPalmError=maximum_error,maximumPalmMeshToBoneError=maximum_palm_error,
                                   maximumRootLocalFoodTiltRadians=max_angle_error,worst=worst)
                        if maximum_error>tolerance:row['errors'].append('Held-food root misses actual evaluated palm center; max world error='+str(maximum_error))
                        if maximum_palm_error>tolerance:row['errors'].append('Modeled palm centroid disagrees with actual deform-bone socket; max='+str(maximum_palm_error))
                        if max_angle_error>1e-4:row['errors'].append('Food root no longer follows its horizontal root-local orientation')
                        if visibility_failures:row['errors'].append('Held meal is hidden in holding frames: '+str(visibility_failures))
                        row['ok']=not row['errors']
                    except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
                    report['casesChecked']+=1;report['cases'].append(row)
                    report['errors'].extend({'case':label,'message':error} for error in row['errors'])
            report['assetsChecked']+=1
            # Restore this collection's visibility immediately. Other actors do
            # not need to remain visible while this one is being evaluated.
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
        if restore_errors:report['errors'].append({'case':'presentation-restore','message':'; '.join(restore_errors)})
    report['expectedSamples']=expected_samples
    report['ok']=not report['errors'] and report['assetsChecked']==len(ids) and report['samplesChecked']==expected_samples
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,output)
    return report
