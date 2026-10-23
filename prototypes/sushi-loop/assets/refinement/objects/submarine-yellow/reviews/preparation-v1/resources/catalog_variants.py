"""Genuine native mesh variants inside existing issue33 catalog entries.
Called by production orchestration after its base motion wrappers are installed.
No rendering, camera changes, MCP calls or publication. Native bake records all
variant visibility and transforms as part of each existing entry's clip cohort.
"""
import bpy
import math
import json
from mathutils import Vector

RECIPES=(('salmon-nigiri','dish-salmon',''),('cucumber-maki','dish-cucumber','cucumber-'),('eel-roll','dish-eel','eel-'))


def _merge(host,child,namespace):
    target=host['collection'];source=child['collection']
    for obj in list(source.objects):source.objects.unlink(obj);target.objects.link(obj)
    bpy.data.collections.remove(source)
    child['root'].parent=host['root']
    host['parts']=dict(host['parts'])
    host['parts'].update({namespace+'__'+name:obj for name,obj in child['parts'].items()})
    host['parts'][namespace+'__root']=child['root']
    return child


def _meshes(root):return [o for o in root.children_recursive if o.type in ('MESH','CURVE','SURFACE','FONT')]


def _visibility(objects,shown):
    for obj in objects:obj.hide_render=not shown;obj.hide_viewport=not shown


def _root_state(root):return (root.location.copy(),root.rotation_euler.copy(),root.scale.copy())


def _restore_root(root,state):root.location=state[0];root.rotation_euler=state[1];root.scale=state[2]


def _variant_clips(host,definitions):
    old=dict(host['clips']);host['clips']=dict(old);variants={}
    for name,prefix in definitions:
        ids=[]
        for source,recipe in old.items():
            ident=prefix+source;ids.append(ident)
            if prefix:host['clips'][ident]=dict(recipe)
        variants[name]={'clips':ids}
    host['variants']=variants;host['root']['variants']=json.dumps(variants)
    host['root']['animation_recipes']=json.dumps(host['clips'])
    return list(old)


def _dispatch(clip,base_clips,definitions):
    for name,prefix in reversed(definitions):
        if prefix and clip.startswith(prefix):
            source=clip[len(prefix):]
            if source in base_clips:return name,source
    if clip in base_clips:return definitions[0][0],clip
    raise KeyError('Unknown native variant clip '+clip)


def augment_blackboard(host,food_builder):
    """Three real recipe assemblies on the same board; default salmon IDs stay."""
    if host.get('recipe_geometry_variants'):return host
    original=host['pose'];legacy=[o for name,o in host['parts'].items() if name.startswith(('token_plate_','token_recipe_'))]
    children={};states={};definitions=[(name,prefix) for name,_,prefix in RECIPES]
    for name,food_id,prefix in RECIPES:
        child=_merge(host,food_builder.create_asset(food_id),'board_'+name)
        child['root'].location=(0,-.148,.625);child['root'].rotation_euler=(math.pi/2,0,0);child['root'].scale*=.55
        states[name]=_root_state(child['root']);children[name]=child
    base_clips=_variant_clips(host,definitions)
    def pose(clip,t):
        selected,source=_dispatch(clip,base_clips,definitions)
        original(source,t)
        _visibility(legacy,False)
        for name,child in children.items():
            child['reset']();_restore_root(child['root'],states[name])
            _visibility(_meshes(child['root']),name==selected)
        root=children[selected]['root']
        if source=='selected':root.scale*=1+.04*math.sin(math.tau*t)
        elif source.replace('_','-')=='recipe-change':root.rotation_euler.z+=.035*math.sin(math.tau*t)*math.sin(math.pi*t)
        bpy.context.view_layer.update()
    host['pose']=pose;host['reset']=lambda:pose(base_clips[0],0.)
    host['recipe_geometry_variants']={'kind':'blackboard','roots':{name:child['root'].name for name,child in children.items()},'legacyTokensHidden':[o.name for o in legacy]}
    host['root']['recipe_geometry_variants']=json.dumps(host['recipe_geometry_variants'])
    pose(base_clips[0],0.)
    return host


def augment_preference_bubble(host,food_builder):
    """Extend an existing attach_food salmon bubble without changing its motion."""
    if host.get('recipe_geometry_variants'):return host
    salmon=host['parts'].get('native_preference_dish')
    if salmon is None:raise ValueError('Install the existing native salmon attach_food wrapper before augment_preference_bubble')
    original=host['pose'];children={};definitions=[(name,prefix) for name,_,prefix in RECIPES]
    for name,food_id,prefix in RECIPES[1:]:children[name]=_merge(host,food_builder.create_asset(food_id),'preference_'+name)
    original_states={name:_root_state(child['root']) for name,child in children.items()}
    base_clips=_variant_clips(host,definitions)
    def pose(clip,t):
        selected,source=_dispatch(clip,base_clips,definitions)
        original(source,t)
        _visibility(_meshes(salmon),selected=='salmon-nigiri')
        for name,child in children.items():
            child['reset']();_restore_root(child['root'],original_states[name])
            child['root'].location=salmon.location.copy();child['root'].rotation_euler=salmon.rotation_euler.copy();child['root'].scale=salmon.scale.copy()
            _visibility(_meshes(child['root']),selected==name)
        bpy.context.view_layer.update()
    host['pose']=pose;host['reset']=lambda:pose(base_clips[0],0.)
    host['recipe_geometry_variants']={'kind':'preference-bubble','roots':{'salmon-nigiri':salmon.name,**{name:child['root'].name for name,child in children.items()}},'motion':'existing appear/idle/fade transform reused exactly'}
    host['root']['recipe_geometry_variants']=json.dumps(host['recipe_geometry_variants'])
    pose(base_clips[0],0.)
    return host


def augment_salvage(host,prop_builder):
    """Three distinct native fragments; a is default, b-/c- prefix extra clips."""
    if host.get('salvage_geometry_variants'):return host
    original=host['pose'];base_meshes=[o for o in host['parts'].values() if o.type in ('MESH','CURVE')]
    children={name:_merge(host,prop_builder.create_asset('salvage_'+name),'salvage_'+name) for name in ('b','c')}
    states={name:_root_state(child['root']) for name,child in children.items()}
    definitions=[('a',''),('b','b-'),('c','c-')];base_clips=_variant_clips(host,definitions)
    mapping={'shimmer':'idle','attract':'attraction','collect':'collection','idle':'idle','attraction':'attraction','collection':'collection'}
    if any(clip not in mapping for clip in base_clips):raise ValueError('Unexpected salvage source clip set')
    def pose(clip,t):
        selected,source=_dispatch(clip,base_clips,definitions)
        original(source,t)
        _visibility(base_meshes,selected=='a')
        for name,child in children.items():
            child['reset']();_restore_root(child['root'],states[name]);child['pose'](mapping[source],t)
            _visibility(_meshes(child['root']),selected==name)
        bpy.context.view_layer.update()
    host['pose']=pose;host['reset']=lambda:pose(base_clips[0],0.)
    host['variants']={name:host['variants'][key] for name,key in [('plate','a'),('bent','b'),('mixed','c')]}
    host['root']['variants']=json.dumps(host['variants'])
    host['salvage_geometry_variants']={'a':'existing plate fragment','b':'angular bolt-studded bent fragment','c':'wood-backed metal cluster','roots':{name:child['root'].name for name,child in children.items()}}
    host['root']['salvage_geometry_variants']=json.dumps(host['salvage_geometry_variants'])
    pose(base_clips[0],0.)
    return host


def augment(host,asset_id,food_builder,prop_builder):
    if asset_id=='chef-blackboard':return augment_blackboard(host,food_builder)
    if asset_id=='bubble-preference':return augment_preference_bubble(host,food_builder)
    if asset_id=='salvage-metal':return augment_salvage(host,prop_builder)
    raise ValueError('No geometry variant helper for '+asset_id)
