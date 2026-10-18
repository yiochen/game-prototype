"""Issue33 native action baking and isolated production-only .blend export.
Execute only through Blender MCP after captures are idle. This adapter samples
existing builder pose callbacks without changing source builders or runtime.
It bakes complete independent clip cohorts, including composed food visibility,
rig channels, procedural tube geometry and conveyor shader phase.
"""
import bpy
import json
import math
import pathlib
import hashlib
import time
from mathutils import Vector, Matrix

PREFIX='S33_NATIVE__'
BAKED_KEY_PREFIX='S33 sample '


def _plain(value):
    if isinstance(value,(bool,str,int,float)) or value is None:return value
    if isinstance(value,dict):return {str(k):_plain(v) for k,v in value.items()}
    if isinstance(value,Matrix):return [[float(x) for x in row] for row in value]
    if isinstance(value,(tuple,list)):return [_plain(v) for v in value]
    try:return [float(v) for v in value]
    except (TypeError,ValueError):return str(value)


def _num(value):
    if isinstance(value,bool):return bool(value)
    if isinstance(value,(int,float)):return float(value)
    try:
        values=tuple(float(v) for v in value)
        if all(math.isfinite(v) for v in values):return values
    except (TypeError,ValueError):pass
    return None


def _different(a,b,tol=1e-8):
    if isinstance(a,(tuple,list)) and isinstance(b,(tuple,list)):
        return len(a)!=len(b) or any(_different(x,y,tol) for x,y in zip(a,b))
    if isinstance(a,bool) or isinstance(b,bool):return a!=b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)>tol
    return a!=b


def _safe_name(text):return ''.join(c if c.isalnum() or c in '-_.' else '_' for c in str(text))


def _object_state(obj):
    rotation='rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_axis_angle' if obj.rotation_mode=='AXIS_ANGLE' else 'rotation_euler'
    return {'location':tuple(obj.location),rotation:tuple(getattr(obj,rotation)),'scale':tuple(obj.scale),'hide_render':bool(obj.hide_render),'hide_viewport':bool(obj.hide_viewport),'_rotation_mode':obj.rotation_mode}


def _bone_state(bone):
    rotation='rotation_quaternion' if bone.rotation_mode=='QUATERNION' else 'rotation_axis_angle' if bone.rotation_mode=='AXIS_ANGLE' else 'rotation_euler'
    return {'location':tuple(bone.location),rotation:tuple(getattr(bone,rotation)),'scale':tuple(bone.scale),'_rotation_mode':bone.rotation_mode}


def _socket_controls(asset):
    arm=asset.get('armature') or asset.get('rig')
    if not arm:return {}
    result={}
    for name in ('hand_sockets_current','seat_contact_current','hip_control_current','feet_current'):
        if name in arm:
            try:result[name]=json.loads(arm[name])
            except (TypeError,ValueError):result[name]=str(arm[name])
    return result


def _all_objects(asset):
    collection=asset.get('collection')
    if not collection:raise ValueError('Asset must expose its production collection')
    objects=list(collection.all_objects)
    root=asset.get('root')
    if root is None or root not in objects:raise ValueError('Asset ground root is outside its collection')
    for obj in objects:
        if obj.parent and obj.parent not in objects:raise ValueError('Foreign parent dependency: '+obj.name)
        for mod in obj.modifiers:
            target=getattr(mod,'object',None)
            if target and target not in objects:raise ValueError('Foreign modifier dependency: '+obj.name+' -> '+target.name)
        for con in obj.constraints:
            target=getattr(con,'target',None)
            if target and target not in objects:raise ValueError('Foreign constraint dependency: '+obj.name+' -> '+target.name)
    return objects


def _node_sockets(objects):
    """Numeric native shader values; links, menu/string and image data excluded."""
    result={};seen=set()
    for obj in objects:
        if not hasattr(obj.data,'materials'):continue
        for material in obj.data.materials:
            if material is None or not material.use_nodes or not material.node_tree:continue
            tree=material.node_tree
            if tree.as_pointer() in seen:continue
            seen.add(tree.as_pointer())
            for node in tree.nodes:
                for kind in ('inputs','outputs'):
                    for index,socket in enumerate(getattr(node,kind)):
                        if not hasattr(socket,'default_value') or (kind=='inputs' and socket.is_linked):continue
                        if _num(socket.default_value) is None:continue
                        key=tree.name+'::'+node.name+'::'+kind+'::'+str(index)
                        result[key]=(tree,node,socket,kind,index)
    return result


def _shape_meshes(objects):
    return {o.name:o for o in objects if o.type=='MESH' and o.data.shape_keys is not None}


def _shape_snapshot(obj,include_baked=False):
    keys=obj.data.shape_keys
    if not keys.use_relative:raise ValueError('Absolute shape-key time requires explicit adapter: '+obj.name)
    blocks=keys.key_blocks;basis=blocks[0]
    result=[tuple(v.co) for v in basis.data]
    for key in blocks[1:]:
        if (key.name.startswith(BAKED_KEY_PREFIX) and not include_baked) or abs(key.value)<1e-12:continue
        relative=key.relative_key
        if len(key.data)!=len(result):raise ValueError('Shape topology changed: '+obj.name)
        for i,(v,reference) in enumerate(zip(key.data,relative.data)):
            delta=v.co-reference.co
            result[i]=(result[i][0]+key.value*delta.x,result[i][1]+key.value*delta.y,result[i][2]+key.value*delta.z)
    return tuple(result)


def _animation_owners(objects,nodes,shapes):
    owners={obj.as_pointer():obj for obj in objects}
    for tree,*_ in nodes.values():owners[tree.as_pointer()]=tree
    for obj in shapes.values():owners[obj.data.shape_keys.as_pointer()]=obj.data.shape_keys
    return list(owners.values())


def _detach(owners):
    saved=[]
    for owner in owners:
        ad=owner.animation_data
        if ad:
            saved.append((owner,ad.action,getattr(ad,'action_slot',None),[(track,track.mute) for track in ad.nla_tracks]))
            ad.action=None
            for track in ad.nla_tracks:track.mute=True
    return saved


def _assign(owner,action,slot_identifier=None):
    owner.animation_data_create();owner.animation_data.action=action
    if action is not None and hasattr(owner.animation_data,'action_slot') and hasattr(action,'slots'):
        slots=list(action.slots)
        match=next((slot for slot in slots if slot.identifier==slot_identifier),None)
        if match is None and len(slots)==1:match=slots[0]
        if match is not None:owner.animation_data.action_slot=match


def _restore_animation(saved):
    for owner,action,slot,tracks in saved:
        _assign(owner,action,getattr(slot,'identifier',None))
        for track,mute in tracks:track.mute=mute


def _new_action(owner,asset_id,clip,suffix):
    action=bpy.data.actions.new(PREFIX+_safe_name(asset_id)+'__'+_safe_name(clip)+'__'+_safe_name(suffix))
    action.use_fake_user=True;action['issue']=33;action['asset_id']=asset_id;action['clip_id']=clip
    action['fps']=12;action['source']='native_actions.py';_assign(owner,action)
    return action


def _fcurves(action):
    seen=set()
    try:
        for curve in action.fcurves:
            if curve.as_pointer() not in seen:seen.add(curve.as_pointer());yield curve
    except (AttributeError,RuntimeError):pass
    for layer in getattr(action,'layers',[]):
        for strip in layer.strips:
            bags=list(getattr(strip,'channelbags',[]))
            if not bags and hasattr(strip,'channelbag'):
                for slot in getattr(action,'slots',[]):
                    bag=strip.channelbag(slot)
                    if bag:bags.append(bag)
            for bag in bags:
                for curve in bag.fcurves:
                    if curve.as_pointer() not in seen:seen.add(curve.as_pointer());yield curve


def _linear_keys(action):
    for curve in _fcurves(action):
        constant=curve.data_path.endswith(('hide_render','hide_viewport'))
        for key in curve.keyframe_points:key.interpolation='CONSTANT' if constant else 'LINEAR'


def _target_record(owner,action):
    slot=getattr(owner.animation_data,'action_slot',None) if owner.animation_data else None
    result={'ownerType':owner.bl_rna.identifier,'ownerName':owner.name,'action':action.name,'slotIdentifier':getattr(slot,'identifier',None),'keyframeCount':sum(len(c.keyframe_points) for c in _fcurves(action))}
    if owner.bl_rna.identifier=='ShaderNodeTree':
        materials=[m for m in bpy.data.materials if m.use_nodes and m.node_tree and m.node_tree.as_pointer()==owner.as_pointer()]
        if len(materials)==1:
            result['materialOwnerName']=materials[0].name
            action['material_owner_name']=materials[0].name
        elif len(materials)>1:raise ValueError('Ambiguous material ownership for shader tree '+owner.name)
        elif bpy.data.node_groups.get(owner.name)==owner:result['nodeGroupOwnerName']=owner.name
        else:raise ValueError('Shader tree has no exact native material/group owner: '+owner.name)
    return result


def _restore_values(objects,states,armatures,bones,nodes,node_values,shapes,shape_values,shape_coords):
    for obj in objects:
        state=states[obj.name];obj.rotation_mode=state['_rotation_mode']
        for path,val in state.items():
            if not path.startswith('_'):setattr(obj,path,val)
    for arm in armatures:
        for bone in arm.pose.bones:
            state=bones[arm.name][bone.name];bone.rotation_mode=state['_rotation_mode']
            for path,val in state.items():
                if not path.startswith('_'):setattr(bone,path,val)
    for key,(_,_,socket,_,_) in nodes.items():socket.default_value=node_values[key]
    for name,obj in shapes.items():
        for key in obj.data.shape_keys.key_blocks:
            key.value=shape_values[name].get(key.name,0.)
            if key.name in shape_coords[name]:
                for vertex,co in zip(key.data,shape_coords[name][key.name]):vertex.co=co
    bpy.context.view_layer.update()


def bake_asset(asset_id,asset,output_dir=None,replace=False,canonical_direction=True):
    """Bake one asset into independent clip cohorts. Returns a JSON-safe record.
    Existing action bindings and visible pose are restored; new native actions
    and sampled shape keys persist. Explicit replace only removes previous
    actions owned by this helper for this exact asset ID.
    """
    if not asset.get('pose') or not asset.get('clips'):raise ValueError('Missing pose/clip API for '+asset_id)
    old=[a for a in bpy.data.actions if a.get('source')=='native_actions.py' and a.get('asset_id')==asset_id]
    if old and not replace:raise ValueError('Already baked '+asset_id+'; use replace=True for a deliberate rebuild')
    for action in old:bpy.data.actions.remove(action,do_unlink=True)
    objects=_all_objects(asset);nodes=_node_sockets(objects);shapes=_shape_meshes(objects)
    armatures=[o for o in objects if o.type=='ARMATURE']
    raw_meshes={o.name:o for o in objects if o.type=='MESH' and o.data.shape_keys is None}
    mesh_baseline={name:tuple(tuple(v.co) for v in obj.data.vertices) for name,obj in raw_meshes.items()}
    states={o.name:_object_state(o) for o in objects};bone_states={a.name:{b.name:_bone_state(b) for b in a.pose.bones} for a in armatures}
    node_values={k:_num(v[2].default_value) for k,v in nodes.items()}
    shape_values={n:{k.name:k.value for k in o.data.shape_keys.key_blocks} for n,o in shapes.items()}
    shape_coords={n:{k.name:tuple(tuple(v.co) for v in k.data) for k in o.data.shape_keys.key_blocks if not k.name.startswith(BAKED_KEY_PREFIX)} for n,o in shapes.items()}
    owners=_animation_owners(objects,nodes,shapes);saved_animation=_detach(owners)
    arm_custom={a.name:{k:a[k] for k in a.keys() if k.startswith('current_') or k in ('hand_sockets_current','seat_contact_current','hip_control_current','feet_current')} for a in armatures}
    root=asset['root'];record={'assetId':asset_id,'fps':12,'source':'native_actions.py','static':all(c.get('static',False) for c in asset['clips'].values()),'clips':{},'armatures':[],
      'footprint':_plain(asset.get('footprint')),'projection':asset.get('projection',root.get('projection')),'groundRootObject':root.name,'sockets':_plain(asset.get('sockets',{})),'notes':['Native object, rig, visibility, shape and shader channels; no raster substitutes.','Runtime frames exclude the duplicate loop closure key.','Visual contact and deformation review remains separate from these structural records.']}
    created=[];samples={};node_closures={}
    try:
        if canonical_direction:root.rotation_euler.z=0
        # Sample ALL states with no actions assigned. Thus prior baked channels
        # cannot overwrite procedural pose callbacks during dependency updates.
        for clip,config in asset['clips'].items():
            count=int(config['frames']);fps=int(config.get('fps',12))
            if count<1 or fps!=12:raise ValueError('Invalid12fps clip '+asset_id+'/'+clip)
            frames=[]
            for f in range(count):
                t=f/count if config.get('loop') else f/max(1,count-1)
                asset['pose'](clip,t)
                mesh_changes={}
                for name,obj in raw_meshes.items():
                    coords=tuple(tuple(v.co) for v in obj.data.vertices)
                    if coords!=mesh_baseline[name]:mesh_changes[name]=coords
                frames.append({'objects':{o.name:_object_state(o) for o in objects},'bones':{a.name:{b.name:_bone_state(b) for b in a.pose.bones} for a in armatures},
                  'nodes':{k:_num(v[2].default_value) for k,v in nodes.items()},'shapes':{n:_shape_snapshot(o) for n,o in shapes.items()},'controls':_socket_controls(asset),'mesh_changes':mesh_changes})
            samples[clip]=frames
            if config.get('loop'):
                asset['pose'](clip,1.0)
                node_closures[clip]={k:_num(v[2].default_value) for k,v in nodes.items()}
        flat=[frame for frames in samples.values() for frame in frames]
        reference=flat[0]
        object_channels={o.name:[p for p in reference['objects'][o.name] if not p.startswith('_') and any(_different(reference['objects'][o.name][p],f['objects'][o.name][p]) for f in flat[1:])] for o in objects}
        # A composed plate/knife render flag must also affect the native viewport.
        for name,paths in object_channels.items():
            if 'hide_render' in paths and 'hide_viewport' not in paths:paths.append('hide_viewport')
        dynamic_nodes=[k for k in nodes if any(_different(reference['nodes'][k],f['nodes'][k]) for f in flat[1:])]
        dynamic_shapes=[n for n in shapes if any(_different(reference['shapes'][n],f['shapes'][n]) for f in flat[1:])]
        direct_names=sorted({name for sample in flat for name in sample['mesh_changes']})
        for name in direct_names:
            obj=raw_meshes[name]
            basis=obj.shape_key_add(name='Basis')
            for vertex,co in zip(basis.data,mesh_baseline[name]):vertex.co=co
            live=obj.shape_key_add(name='S33 Procedural source')
            for vertex,co in zip(live.data,mesh_baseline[name]):vertex.co=co
            live.value=1.;shapes[name]=obj;owners.append(obj.data.shape_keys)
            shape_values[name]={'Basis':0.,'S33 Procedural source':1.}
            shape_coords[name]={'Basis':mesh_baseline[name],'S33 Procedural source':mesh_baseline[name]}
            for sample in flat:sample['shapes'][name]=sample['mesh_changes'].get(name,mesh_baseline[name])
            dynamic_shapes.append(name)
        if dynamic_shapes:
            original_pose=asset['pose']
            bridges={name:shapes[name].data.shape_keys.key_blocks['S33 Procedural source'] for name in direct_names}
            def live_geometry_pose(clip,t):
                for name in dynamic_shapes:
                    for key in shapes[name].data.shape_keys.key_blocks:
                        key.value=0. if key.name.startswith(BAKED_KEY_PREFIX) else shape_values[name].get(key.name,key.value)
                original_pose(clip,t)
                for name,key in bridges.items():
                    obj=raw_meshes[name]
                    for dest,vertex in zip(key.data,obj.data.vertices):dest.co=vertex.co
                    key.value=1.
                for name in dynamic_shapes:
                    for key in shapes[name].data.shape_keys.key_blocks:
                        if key.name.startswith(BAKED_KEY_PREFIX):key.value=0.
                bpy.context.view_layer.update()
            asset['pose']=live_geometry_pose
            record['proceduralMeshBridges']=direct_names
        sampled_keys={}
        for name in dynamic_shapes:
            obj=shapes[name];keys=obj.data.shape_keys;sampled_keys[name]={}
            for clip,frames in samples.items():
                sampled_keys[name][clip]=[]
                for i,sample in enumerate(frames):
                    keyname=BAKED_KEY_PREFIX+_safe_name(asset_id)+' '+_safe_name(clip)+' '+str(i).zfill(3)
                    key=keys.key_blocks.get(keyname) or obj.shape_key_add(name=keyname)
                    key.relative_key=keys.key_blocks[0]
                    for vertex,co in zip(key.data,sample['shapes'][name]):vertex.co=co
                    key.value=0.;sampled_keys[name][clip].append(key)
        for arm in armatures:
            record['armatures'].append({'object':arm.name,'data':arm.data.name,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'deform':bool(b.use_deform),'head':list(b.head_local),'tail':list(b.tail_local),'length':b.length,'matrix':_plain(b.matrix_local)} for b in arm.data.bones]})
        for clip,config in asset['clips'].items():
            frames=samples[clip];count=len(frames);loop=bool(config.get('loop'));targets=[];clip_actions=[]
            for obj in objects:
                paths=object_channels[obj.name]
                if not paths and obj not in armatures:continue
                action=_new_action(obj,asset_id,clip,obj.name);created.append(action);clip_actions.append((obj,action))
                for i in range(count+int(loop)):
                    sample=frames[i%count];keyframe=i+1;state=sample['objects'][obj.name]
                    obj.rotation_mode=state['_rotation_mode']
                    for path in paths:
                        value=state['hide_render'] if path=='hide_viewport' and 'hide_render' in paths else state[path]
                        setattr(obj,path,value);obj.keyframe_insert(data_path=path,frame=keyframe,group='Object and visibility')
                    if obj in armatures:
                        for bone in obj.pose.bones:
                            bstate=sample['bones'][obj.name][bone.name];bone.rotation_mode=bstate['_rotation_mode']
                            for path,value in bstate.items():
                                if path.startswith('_'):continue
                                setattr(bone,path,value);bone.keyframe_insert(data_path=path,frame=keyframe,group=bone.name)
                _linear_keys(action);targets.append(_target_record(obj,action))
            by_tree={}
            for key in dynamic_nodes:by_tree.setdefault(nodes[key][0],[]).append(key)
            for tree,keys in by_tree.items():
                action=_new_action(tree,asset_id,clip,tree.name);created.append(action);clip_actions.append((tree,action))
                for i in range(count+int(loop)):
                    sample=frames[i%count]
                    for key in keys:
                        socket=nodes[key][2];socket.default_value=node_closures[clip][key] if loop and i==count else sample['nodes'][key];socket.keyframe_insert(data_path='default_value',frame=i+1,group='Shader phase and material')
                _linear_keys(action);targets.append(_target_record(tree,action))
            for name in dynamic_shapes:
                obj=shapes[name];keys=obj.data.shape_keys
                for key in keys.key_blocks:key.value=0
                baked=sampled_keys[name][clip]
                action=_new_action(keys,asset_id,clip,name+'__geometry');created.append(action);clip_actions.append((keys,action))
                # Key every non-basis value including other clip samples at zero,
                # so assigning a different action cannot retain stale geometry.
                for i in range(count+int(loop)):
                    for key in keys.key_blocks[1:]:
                        key.value=1. if key==baked[i%count] else 0.
                        key.keyframe_insert(data_path='value',frame=i+1,group='Sampled native geometry')
                _linear_keys(action);targets.append(_target_record(keys,action))
            for owner,action in clip_actions:owner.animation_data.action=None
            record['clips'][clip]={'frames':count,'fps':12,'loop':loop,'static':bool(config.get('static',False)),'firstFrame':1,'lastUniqueFrame':count,'closingKeyFrame':count+1 if loop else None,'actions':targets,
              'controlsByFrame':[f['controls'] for f in frames],'geometryOwners':dynamic_shapes,'shaderChannels':dynamic_nodes,'shaderLoopClosure':{k:node_closures[clip][k] for k in dynamic_nodes} if loop else {}}
        root['native_action_record']=json.dumps({'source':'native_actions.py','assetId':asset_id,'clips':{k:[a['action'] for a in v['actions']] for k,v in record['clips'].items()}})
        record['actionCount']=len(created);record['createdAtUnix']=time.time();record['status']='native-actions-baked-needs-visual-review'
        source_root=pathlib.Path(__file__).parent
        record['sourceFiles']={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in ('native_actions.py','character_builders.py','prop_builders.py','world_components.py','food_belt_builders.py','creature_fx_builders.py','character_composition.py','production_library.py','catalog_variants.py') if (source_root/name).exists()}
        if output_dir:
            folder=pathlib.Path(output_dir)/_safe_name(asset_id);folder.mkdir(parents=True,exist_ok=True)
            (folder/'rig-actions.json').write_text(json.dumps(record,indent=2)+'\n')
        return record
    finally:
        for owner in owners:
            if owner.animation_data:owner.animation_data.action=None
        _restore_values(objects,states,armatures,bone_states,nodes,node_values,shapes,shape_values,shape_coords)
        for name in locals().get('direct_names',[]):
            for vertex,co in zip(raw_meshes[name].data.vertices,mesh_baseline[name]):vertex.co=co
            raw_meshes[name].data.update()
        _restore_animation(saved_animation)
        for arm in armatures:
            for key,value in arm_custom[arm.name].items():arm[key]=value


def _resolve_owner(target):
    typ=target['ownerType'];name=target['ownerName']
    if typ=='Object':owner=bpy.data.objects.get(name)
    elif typ=='Key':owner=bpy.data.shape_keys.get(name)
    elif typ in ('ShaderNodeTree','CompositorNodeTree','GeometryNodeTree','NodeTree'):
        material_name=target.get('materialOwnerName')
        group_name=target.get('nodeGroupOwnerName')
        if material_name:
            material=bpy.data.materials.get(material_name)
            if material is None or not material.use_nodes or material.node_tree is None:raise KeyError('Missing exact shader material owner '+material_name)
            owner=material.node_tree
        elif group_name:
            owner=bpy.data.node_groups.get(group_name)
        else:
            # Embedded shader trees commonly ALL have name"Shader Nodetree".
            # A first-match lookup silently animates another belt's material.
            candidates=[m.node_tree for m in bpy.data.materials if m.use_nodes and m.node_tree and m.node_tree.name==name]
            group=bpy.data.node_groups.get(name)
            if group is not None:candidates.append(group)
            unique={tree.as_pointer():tree for tree in candidates}
            if len(unique)>1:raise ValueError('Ambiguous embedded node-tree owner '+name+'; backfill materialOwnerName before native playback')
            owner=next(iter(unique.values()),None)
    else:raise ValueError('Unsupported action owner '+typ)
    if owner is None:raise KeyError('Missing native action owner '+typ+':'+name)
    return owner


def apply_clip(asset,record,clip,frame=1,direction='S',scene=None):
    """Assign every action in one native cohort and evaluate it without pose().
    Can be used for post-bake parity inspection and ordinary native playback.
    Keep the returned registry record beside the .blend for later iteration.
    """
    if clip not in record['clips']:raise KeyError(clip)
    objects=_all_objects(asset);nodes=_node_sockets(objects);shapes=_shape_meshes(objects)
    for owner in _animation_owners(objects,nodes,shapes):
        if owner.animation_data:
            owner.animation_data.action=None
            for track in owner.animation_data.nla_tracks:track.mute=True
    for target in record['clips'][clip]['actions']:
        owner=_resolve_owner(target);action=bpy.data.actions.get(target['action'])
        if action is None:raise KeyError('Missing action '+target['action'])
        _assign(owner,action,target.get('slotIdentifier'))
    asset['root'].rotation_euler.z={'S':0.,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]
    sc=scene or bpy.context.scene;sc.render.fps=12
    sc.frame_start=1;sc.frame_end=record['clips'][clip]['lastUniqueFrame'];sc.frame_set(int(frame))
    bpy.context.view_layer.update()
    return {'assetId':record['assetId'],'clip':clip,'frame':int(frame),'direction':direction,'actions':[t['action'] for t in record['clips'][clip]['actions']]}


def bake_registry(runtime,asset_ids=None,output_dir=None,replace=False):
    """Incremental batch adapter; preserves earlier records and native actions.
    Previously recorded clips whose action IDs remain loaded are reused unless
    replace=True. Records for assets outside this batch are never dropped.
    """
    if getattr(runtime,'job_status',{}).get('state')=='rendering':raise RuntimeError('Wait for active capture before native action bake')
    ids=list(asset_ids or runtime.assets.keys())
    destination=pathlib.Path(output_dir) if output_dir else pathlib.Path(runtime.OUT)/'source'/'native-actions'
    destination.mkdir(parents=True,exist_ok=True);manifest=destination/'library-actions.json'
    previous=json.loads(manifest.read_text()) if manifest.exists() else {}
    records=dict(previous.get('assets',{}))
    for asset_id in ids:
        prior=records.get(asset_id)
        valid=prior and all(bpy.data.actions.get(t['action']) is not None for c in prior.get('clips',{}).values() for t in c.get('actions',[]))
        if valid and not replace:continue
        records[asset_id]=bake_asset(asset_id,runtime.assets[asset_id],destination,replace=replace)
    summary={'version':1,'fps':12,'source':'native_actions.py','assets':records,'createdAtUnix':previous.get('createdAtUnix',time.time()),'updatedAtUnix':time.time()}
    manifest.write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def _scene_nodes(layer_collection):
    yield layer_collection
    for child in layer_collection.children:yield from _scene_nodes(child)


def save_production_library(path,assets,records,production_scene=None,visible_asset=None,allow_unbaked_models=True):
    """Write a NEW scene plus explicitly owned action IDs with libraries.write.
    No save_mainfile, no user scene, no unlinking/deleting user content. Only
    supplied production collections and known S33 camera/light objects are
    linked into a temporary export scene, then that new scene is removed.
    """
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    asset_map=dict(assets);record_map=dict(records.get('assets',records))
    if not asset_map:raise ValueError('No production assets to export')
    for aid,a in asset_map.items():_all_objects(a)
    unbaked=[aid for aid in asset_map if aid not in record_map]
    if unbaked and not allow_unbaked_models:raise ValueError('Missing native action record: '+', '.join(unbaked))
    for aid in unbaked:record_map[aid]={'clips':{},'status':'editable-model-only-actions-not-yet-baked'}
    action_ids=set()
    for aid in asset_map:
        for clip in record_map[aid]['clips'].values():
            for target in clip['actions']:
                action=bpy.data.actions.get(target['action'])
                if action is None or action.get('source')!='native_actions.py' or action.get('asset_id')!=aid:raise ValueError('Unowned or missing action '+target['action'])
                action_ids.add(action)
    scene=bpy.data.scenes.new('S33 Native Asset Library Export')
    window=bpy.context.window;previous_scene=window.scene if window else None
    linked=[];collection_visibility={a['collection']:(a['collection'].hide_render,a['collection'].hide_viewport) for a in asset_map.values()};production_scene=production_scene or bpy.data.scenes.get('Sushi33 Production')
    try:
        if window:
            window.scene=scene
            window.view_layer=scene.view_layers[0]
        for aid,asset in asset_map.items():
            collection=asset['collection'];collection.hide_render=False;collection.hide_viewport=False
            if collection not in list(scene.collection.children):scene.collection.children.link(collection);linked.append(collection.name)
        if production_scene:
            for obj in production_scene.objects:
                if obj.type in ('CAMERA','LIGHT') and obj.name.startswith('S33 '):
                    if obj not in list(scene.objects):scene.collection.objects.link(obj)
            if production_scene.camera and production_scene.camera in list(scene.objects):scene.camera=production_scene.camera
            if production_scene.world and production_scene.world.name.startswith('S33 '):scene.world=production_scene.world
            scene.render.engine=production_scene.render.engine
            scene.render.resolution_x=production_scene.render.resolution_x;scene.render.resolution_y=production_scene.render.resolution_y
            scene.render.resolution_percentage=production_scene.render.resolution_percentage
            scene.render.pixel_aspect_x=production_scene.render.pixel_aspect_x;scene.render.pixel_aspect_y=production_scene.render.pixel_aspect_y
            scene.render.film_transparent=True
            scene.view_settings.view_transform=production_scene.view_settings.view_transform
        scene.render.fps=12;scene.frame_start=1;scene.frame_end=max((c['lastUniqueFrame'] for a in record_map.values() for c in a['clips'].values()),default=1)
        first=visible_asset or next(iter(asset_map));first_collection=asset_map[first]['collection']
        scene.view_layers[0].update()
        if window:bpy.context.view_layer.update()
        tree=scene.view_layers[0].layer_collection
        if tree is None:raise RuntimeError('Export view-layer collection tree is unavailable after scene activation')
        for layer in _scene_nodes(tree):
            if layer.collection in [a['collection'] for a in asset_map.values()]:layer.exclude=layer.collection!=first_collection
        scene['issue']=33;scene['source']='native_actions.py';scene['asset_ids']=json.dumps(list(asset_map));scene['actions_manifest']=json.dumps({aid:{clip:[t['action'] for t in c['actions']] for clip,c in record_map[aid]['clips'].items()} for aid in asset_map})
        scene['usage']='One independent native action cohort per clip. Use library-actions.json / apply_clip to assign all owners including visibility, shader and native geometry. No raster stand-ins.'
        owned_objects={o for a in asset_map.values() for o in a['collection'].all_objects}
        foreign=[o.name for o in scene.objects if o not in owned_objects and not(o.type in ('CAMERA','LIGHT') and o.name.startswith('S33 '))]
        if foreign:raise ValueError('Refusing foreign export objects: '+', '.join(foreign))
        bpy.data.libraries.write(str(path),{scene,*action_ids},fake_user=True,compress=True)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        report={'path':str(path),'sha256':digest,'bytes':path.stat().st_size,'exportScene':scene.name,'assetIds':list(asset_map),'collections':linked,'ownedObjects':len(owned_objects),'independentActions':len(action_ids),'userScenesIncluded':False,'foreignObjects':foreign,'visibleAsset':first,'unbakedAssetIds':unbaked,'animationRecordsPreserved':list(set(asset_map)-set(unbaked))}
        path.with_suffix('.export.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    finally:
        if window and previous_scene:window.scene=previous_scene
        for collection,(render,viewport) in collection_visibility.items():collection.hide_render=render;collection.hide_viewport=viewport
        bpy.data.scenes.remove(scene)


def backfill_belt_shader_owners(assets,records,source_dir=None):
    """Repair existing20 belt action locators using live phase-node ownership.
    No geometry, key values, action frames or material names are changed. Pass
    export/source to update per-ID rig JSON, rig-actions JSON and the incremental
    library-actions manifest; all unrelated records are retained.
    """
    asset_map=dict(assets);record_map=records.get('assets',records);changed=[]
    for aid,asset in asset_map.items():
        if not aid.startswith('belt-') or aid not in record_map:continue
        phase=asset.get('phaseNode')
        if phase is None:raise ValueError('Belt is missing its native phase node: '+aid)
        tree=phase.id_data
        materials=[m for m in bpy.data.materials if m.use_nodes and m.node_tree and m.node_tree.as_pointer()==tree.as_pointer()]
        if len(materials)!=1:raise ValueError('Expected exactly one phase material for '+aid+'; found'+str(len(materials)))
        material=materials[0];record=record_map[aid];count=0
        for clip,recipe in record['clips'].items():
            shader_targets=[t for t in recipe['actions'] if t['ownerType']=='ShaderNodeTree']
            if len(shader_targets)!=1:raise ValueError('Expected one shader action cohort for '+aid+'/'+clip)
            for target in shader_targets:
                action=bpy.data.actions.get(target['action'])
                if action is None or action.get('asset_id')!=aid:raise ValueError('Missing or mismatched belt action '+target['action'])
                target['materialOwnerName']=material.name;target['ownerName']=tree.name
                action['material_owner_name']=material.name
                count+=1
        record['ownershipMetadataRevision']={'source':'native_actions.py','sourceSha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'reason':'Exact material ownership for embedded shader node trees','geometryAndKeysUnchanged':True,'updatedAtUnix':time.time()}
        if source_dir:
            source=pathlib.Path(source_dir)
            for path in (source/aid/'rig.json',source/'native-actions'/aid/'rig-actions.json'):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(record,indent=2)+'\n')
        changed.append({'assetId':aid,'materialOwnerName':material.name,'shaderActions':count})
    if source_dir:
        manifest=pathlib.Path(source_dir)/'native-actions'/'library-actions.json'
        summary=json.loads(manifest.read_text()) if manifest.exists() else {'version':1,'fps':12,'source':'native_actions.py','assets':{}}
        summary.setdefault('assets',{}).update(record_map);summary['updatedAtUnix']=time.time()
        manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(summary,indent=2)+'\n')
    return {'changedBelts':len(changed),'owners':changed,'geometryAndKeysUnchanged':True}
