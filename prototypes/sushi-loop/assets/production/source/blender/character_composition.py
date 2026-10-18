"""Reusable native plate/utensil composition attached to evaluated character hands.
The food meshes come from exactly the same builder as standalone world dishes.
"""
import bpy,json,math
from mathutils import Vector

def add_held_props(character,food_builder,recipe='dish-salmon'):
    meal=food_builder.create_asset(recipe);target=character['collection']
    for obj in list(meal['collection'].objects):
        meal['collection'].objects.unlink(obj);target.objects.link(obj)
    bpy.data.collections.remove(meal['collection'])
    meal['root'].parent=character['root'];meal['root'].name=character['root'].name+'__held_'+recipe
    original=character['pose'];parts=list(meal['parts'].values())
    # A short modeled knife is held only during cooking; no invented station.
    blade_mat=food_builder.M['metal'];handle_mat=food_builder.M['wood_dark']
    utensil=bpy.data.objects.new(character['root'].name+'__utensil',None);target.objects.link(utensil);utensil.parent=character['root']
    for name,loc,size,mat in [('handle',(0,0,0),(.035,.10,.038),handle_mat),('blade',(0,-.105,.005),(.06,.16,.012),blade_mat)]:
        bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=character['root'].name+'__knife_'+name
        for c in list(o.users_collection):c.objects.unlink(o)
        target.objects.link(o);o.parent=utensil;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
        parts.append(o)
    def pose(clip,t):
        original(clip,t)
        hands=json.loads(character['armature']['hand_sockets_current']);left=Vector(hands['L']);right=Vector(hands['R']);center=(left+right)*.5
        holding=clip in ['hold','load','eat','seated_wait','seated-wait']
        for o in meal['parts'].values():o.hide_render=not holding
        meal['root'].location=center+Vector((0,-.025,.018));meal['root'].rotation_euler=(0,0,0)
        utensil.location=right;utensil.rotation_euler=(0,.18*math.sin(t*math.tau),0)
        for o in utensil.children:o.hide_render=clip!='work'
        bpy.context.view_layer.update()
    character['pose']=pose
    character['held_composition']={'recipe':recipe,'foodRoot':meal['root'],'utensilRoot':utensil,'parts':parts,'source':'food_belt_builders.py'}
    character['root']['food_composition']='Reused native '+recipe+' attached to evaluated palm sockets; knife during work. Separate food world sprites also exported.'
    return character

def bake_props(character,actions):
    roots=[character['held_composition']['foodRoot'],character['held_composition']['utensilRoot']]
    result={}
    for clip,recipe in character['clips'].items():
        for root in roots:
            if root.animation_data:root.animation_data.action=None
        for f in range(recipe['frames']+(1 if recipe.get('loop') else 0)):
            character['pose'](clip,(f%recipe['frames'])/recipe['frames'] if recipe.get('loop') else f/max(1,recipe['frames']-1))
            for root in roots:
                for path in ['location','rotation_euler','scale']:root.keyframe_insert(data_path=path,frame=f+1)
        result[clip]=[]
        for root in roots:
            act=root.animation_data.action;act.name=root.name+'__'+clip+'__12fps';act.use_fake_user=True;result[clip].append(act)
    return result
