"""ROOT-only Blender MCP audit of actual baked customer walk/panic actions.

No procedural pose callbacks, rendering or model edits. Run BEFORE and AFTER
the source fix with different report filenames to retain actual native evidence:
  scope={'__file__':'/private/tmp/sushi33-production/validate_native_character_gait.py'}
  exec(compile(open(scope['__file__']).read(),scope['__file__'],'exec'),scope)
  result=scope['validate_native_character_gait'](r,N,report_path='...before.json')
  print({k:result[k] for k in ('ok','casesChecked','samplesChecked','errors','report')})
Presentation/action state is restored. Only the requested JSON report is written.
"""
import json
import math
import os
from pathlib import Path
import time
import bpy
from mathutils import Vector

_GAIT_IDS = ('customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june')
_GAIT_FRONT = {'S': (0., -1., 0.), 'E': (1., 0., 0.), 'N': (0., 1., 0.), 'W': (-1., 0., 0.)}
_GAIT_BASE = Path('/private/tmp/sushi33-production')


def _gait_correlation(first, second):
    a = sum(first)/len(first); b = sum(second)/len(second)
    numerator = sum((x-a)*(y-b) for x,y in zip(first,second))
    denominator = math.sqrt(sum((x-a)**2 for x in first)*sum((y-b)**2 for y in second))
    return numerator/denominator if denominator > 1e-12 else None


def validate_native_character_gait(runtime, native, report_path=None, slip_tolerance=.0015):
    if getattr(runtime, 'job_status', {}).get('state') == 'rendering':
        raise RuntimeError('Wait for live capture before temporary native-action inspection')
    output = Path(report_path) if report_path else _GAIT_BASE/'export/validation/native-character-gait.json'
    report = {'version':1, 'ok':False, 'source':'actual evaluated baked foot/hand/pelvis matrices and deformed soles; no pose callback',
              'blendPath':bpy.data.filepath, 'blenderVersion':bpy.app.version_string, 'createdAtUnix':time.time(),
              'rootTravelPerGaitCycle':.56, 'halfStride':.14, 'canonicalFront':'-Y',
              'casesChecked':0, 'samplesChecked':0, 'errors':[], 'cases':[], 'report':str(output)}
    window=bpy.context.window
    old_scene=window.scene if window else bpy.context.scene
    old_layer=window.view_layer if window else bpy.context.view_layer
    old_active=old_layer.objects.active
    old_selected=list(bpy.context.selected_objects)
    scene=bpy.data.scenes.get(getattr(runtime,'SCENE_NAME','Sushi33 Production'))
    if scene is None:raise RuntimeError('Production scene is not loaded')
    old_frame=(scene.frame_current,scene.frame_subframe)
    old_settings=(scene.render.fps,scene.render.fps_base,scene.frame_start,scene.frame_end,scene.camera)
    owners={};objects={};bones=[];collections=[];layers={}
    try:
        if window:window.scene=scene;window.view_layer=scene.view_layers[0]
        elif bpy.context.scene!=scene:raise RuntimeError('Current headless scene is not production')
        for aid in _GAIT_IDS:
            asset=runtime.assets[aid]
            collection=asset['collection'];collections.append((collection,collection.hide_render,collection.hide_viewport))
            asset_objects=native._all_objects(asset)
            for obj in asset_objects:
                objects.setdefault(obj.as_pointer(),(obj,obj.matrix_basis.copy(),obj.rotation_mode,obj.hide_render,obj.hide_viewport))
                if obj.type=='ARMATURE':
                    bones.extend((bone,bone.matrix_basis.copy(),bone.rotation_mode) for bone in obj.pose.bones)
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
        for aid in _GAIT_IDS:
            collection=runtime.assets[aid]['collection'];collection.hide_render=False;collection.hide_viewport=False
            for layer in find_path(scene.view_layers[0].layer_collection,collection):
                layers.setdefault(layer.as_pointer(),(layer,layer.exclude,layer.hide_viewport));layer.exclude=False;layer.hide_viewport=False
        bpy.context.view_layer.update()
        for aid in _GAIT_IDS:
            asset=runtime.assets[aid]
            record=getattr(runtime,'native_records',{}).get(aid)
            if record is None:record=json.loads((_GAIT_BASE/'export/source'/aid/'rig.json').read_text())
            armature=asset.get('armature') or asset.get('rig')
            if armature is None:raise ValueError('Missing native armature '+aid)
            for clip,quick in (('walk',1),('panic',2)):
                config=record['clips'][clip];count=int(config['frames'])
                for direction in ('S','E','N','W'):
                    label=aid+'/'+clip+'/'+direction
                    row={'id':aid,'clip':clip,'direction':direction,'ok':False,'errors':[], 'advisories':[]}
                    try:
                        if count!=12 or config.get('fps')!=12 or not config.get('loop'):
                            raise ValueError('Expected unchanged 12-frame12fps loop')
                        if config.get('closingKeyFrame')!=count+1:
                            raise ValueError('Native cycle has no explicit closing key')
                        native.apply_clip(asset,record,clip,frame=1,direction=direction,scene=scene)
                        facing=Vector(_GAIT_FRONT[direction]);duration=count/12.
                        row.update(frames=count,cycleSeconds=duration,gaitCyclesPerClip=quick,matchingForwardSpeed=.56*quick/duration)
                        samples=[];minimum_toe_dot=1.
                        for index in range(count+1):
                            scene.frame_set(index+1);bpy.context.view_layer.update()
                            graph=bpy.context.evaluated_depsgraph_get();evaluated=armature.evaluated_get(graph)
                            feet={};sole_z={};hands={}
                            for side in ('L','R'):
                                foot=evaluated.pose.bones['foot_'+side]
                                head=evaluated.matrix_world@foot.head;tail=evaluated.matrix_world@foot.tail
                                heading=tail-head;heading.z=0.
                                if heading.length<1e-8:raise ValueError('Degenerate native toe heading')
                                minimum_toe_dot=min(minimum_toe_dot,heading.normalized().dot(facing))
                                feet[side]=head
                                sole=asset['parts'].get('sole_'+side)
                                if sole is None:raise ValueError('Missing actual weighted sole '+side)
                                evaluated_sole=sole.evaluated_get(graph)
                                sole_z[side]=min((evaluated_sole.matrix_world@vertex.co).z for vertex in evaluated_sole.data.vertices)
                                hand=evaluated.pose.bones['hand_'+side]
                                hands[side]=evaluated.matrix_world@hand.head
                            pelvis=evaluated.matrix_world@evaluated.pose.bones['pelvis'].head
                            samples.append({'feet':feet,'soles':sole_z,'hands':hands,'hipZ':pelvis.z})
                            report['samplesChecked']+=1
                        if minimum_toe_dot<.99:row['errors'].append('Actual toes oppose/miss facing; minimum alignment='+str(minimum_toe_dot))
                        row['minimumToeFacingDot']=minimum_toe_dot
                        metrics={}
                        for side in ('L','R'):
                            slips=[];stance_velocity=[];swing_velocity=[];ground_errors=[]
                            for index in range(count):
                                current=samples[index];following=samples[index+1]
                                delta=following['feet'][side]-current['feet'][side]
                                # Detect support from the actual deformed soles,
                                # independently of the authoring gait formula.
                                planted = abs(current['soles'][side]) <= .002 and abs(following['soles'][side]) <= .002
                                if planted:
                                    # A correct planted foot moves backward relative
                                    # to the root, cancelling forward world travel.
                                    residual=delta+facing*(.56*quick/count)
                                    slips.append(residual.length)
                                    stance_velocity.append(delta.dot(facing)*count/duration)
                                    ground_errors.extend((abs(current['soles'][side]),abs(following['soles'][side])))
                                else:
                                    swing_velocity.append(delta.dot(facing)*count/duration)
                            closure=(samples[-1]['feet'][side]-samples[0]['feet'][side]).length
                            swing_lift=max(s['soles'][side] for s in samples)-min(s['soles'][side] for s in samples)
                            metric={'stancePairs':len(slips),'maximumVirtualWorldSlip':max(slips,default=float('inf')),
                                    'meanRootRelativeStanceVelocityAlongFacing':sum(stance_velocity)/len(stance_velocity) if stance_velocity else None,
                                    'minimumRootRelativeSwingVelocityAlongFacing':min(swing_velocity,default=None),
                                    'maximumGroundContactError':max(ground_errors,default=float('inf')),
                                    'sampledSwingLift':swing_lift,'cycleClosureError':closure}
                            metrics[side]=metric
                            if len(slips)!=count//2:row['errors'].append(side+': incorrect support interval coverage')
                            if metric['maximumVirtualWorldSlip']>slip_tolerance:row['errors'].append(side+': planted sole slides when virtual root advances; max='+str(metric['maximumVirtualWorldSlip']))
                            if metric['meanRootRelativeStanceVelocityAlongFacing'] is None or metric['meanRootRelativeStanceVelocityAlongFacing']>=-1e-4:row['errors'].append(side+': support foot travels forward relative to root (moonwalk)')
                            if metric['minimumRootRelativeSwingVelocityAlongFacing'] is None or metric['minimumRootRelativeSwingVelocityAlongFacing']<=1e-4:row['errors'].append(side+': lifted foot does not recover forward')
                            if metric['maximumGroundContactError']>.002:row['errors'].append(side+': actual weighted sole is not on the ground during support')
                            if swing_lift<.04:row['errors'].append(side+': native swing does not clearly lift sole')
                            if closure>.0002:row['errors'].append(side+': native closing foot pose does not match opening pose')
                            arm_positions=[s['hands'][side].dot(facing) for s in samples[:-1]]
                            foot_positions=[s['feet'][side].dot(facing) for s in samples[:-1]]
                            metric['sameSideArmFootPositionCorrelation']=_gait_correlation(arm_positions,foot_positions)
                            if metric['sameSideArmFootPositionCorrelation'] is None or metric['sameSideArmFootPositionCorrelation']>-.5:
                                row['advisories'].append(side+': arm swing is not strongly contralateral; unchanged stylization, not a support-direction failure')
                        contacts=[s['hipZ'] for s in samples[:-1] if max(s['soles'].values())<.002]
                        passing=[s['hipZ'] for s in samples[:-1] if max(s['soles'].values())>.06]
                        if contacts and passing:
                            delta=sum(contacts)/len(contacts)-sum(passing)/len(passing)
                            row['hipContactMinusPassingHeight']=delta
                            if delta>0:row['advisories'].append('Hip bob peaks at split-foot contacts; retained as secondary stylization')
                        row['feet']=metrics;row['ok']=not row['errors']
                    except Exception as exc:row['errors'].append(type(exc).__name__+': '+str(exc))
                    report['casesChecked']+=1;report['cases'].append(row)
                    report['errors'].extend({'case':label,'message':error} for error in row['errors'])
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
            for obj,matrix,mode,hide_render,hide_viewport in objects.values():
                obj.rotation_mode=mode;obj.matrix_basis=matrix;obj.hide_render=hide_render;obj.hide_viewport=hide_viewport
            for bone,matrix,mode in bones:bone.rotation_mode=mode;bone.matrix_basis=matrix
            for collection,render,viewport in collections:collection.hide_render=render;collection.hide_viewport=viewport
            for layer,exclude,viewport in layers.values():layer.exclude=exclude;layer.hide_viewport=viewport
            if window:window.scene=old_scene;window.view_layer=old_layer
            if set(bpy.context.selected_objects)!=set(old_selected):
                for obj in list(bpy.context.selected_objects):obj.select_set(False)
                for obj in old_selected:obj.select_set(True)
            old_layer.objects.active=old_active;bpy.context.view_layer.update()
        except Exception as exc:restore_errors.append(str(exc))
        if restore_errors:report['errors'].append({'case':'restore','message':'; '.join(restore_errors)})
    report['ok']=not report['errors'] and report['casesChecked']==32 and report['samplesChecked']==416
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(report,indent=2)+'\n');os.replace(temporary,output)
    return report
