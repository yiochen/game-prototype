"""ImageGen 2D sushi attached to evaluated native character palm sockets.

Sushi is a transparent camera-facing image plane, never reconstructed in 3D.
One static alpha rectangle determines UV registration; no pose is fitted/cropped.
The root cancels character yaw with a native driver, retaining a readable plate
in every direction while the hand attachment follows the actual weighted rig.
A dimensional knife is held during cooking only; this is not a sushi mesh.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

SOURCE=Path(__file__).resolve().parents[1]/'2d/generated'
SPRITE_WIDTH_CELLS=.35
CAMERA_DEPTH_BIAS_CELLS=.60


def _alpha_rectangle(image):
    import numpy as np
    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
    alpha=pixels.reshape((image.size[1],image.size[0],4))[:,:,3]
    rows,columns=np.nonzero(alpha>0)
    if not len(rows):raise ValueError('Held sushi image has no alpha content: '+image.filepath)
    # Native Blender image rows start at bottom. UV rectangle remains exact and
    # is constant for every motion sample and facing.
    return [int(columns.min()),int(rows.min()),int(columns.max())+1,int(rows.max())+1]


def _food_sprite(character,recipe):
    path=SOURCE/(recipe+'.png')
    if not path.exists():raise FileNotFoundError('Required ImageGen held sushi cutout is missing: '+str(path))
    name=character['root'].name+'__held_'+recipe;target=character['collection']
    root=bpy.data.objects.new(name,None);target.objects.link(root);root.parent=character['root']
    image=bpy.data.images.load(str(path),check_existing=True);image.alpha_mode='STRAIGHT'
    if image.packed_file is None:image.pack()
    x0,y0,x1,y1=_alpha_rectangle(image)
    native_scale=float(character['root'].get('uniform_native_scale',1.25))
    width=SPRITE_WIDTH_CELLS/native_scale;height=width*(y1-y0)/(x1-x0)
    # Anchor the lowest plate pixel just above the palms. Up is the fixed camera
    # screen-up axis after the 55-degree plane rotation.
    vertices=[(-width/2,0,0),(width/2,0,0),(width/2,height,0),(-width/2,height,0)]
    mesh=bpy.data.meshes.new(name+'__image_geometry');mesh.from_pydata(vertices,[],[(0,1,2,3)]);mesh.update()
    plane=bpy.data.objects.new(name+'__image_plane',mesh);target.objects.link(plane);plane.parent=root
    uv=mesh.uv_layers.new(name='Fixed ImageGen alpha rectangle')
    w,h=image.size;coords=[(x0/w,y0/h),(x1/w,y0/h),(x1/w,y1/h),(x0/w,y1/h)]
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:uv.data[loop_index].uv=coords[mesh.loops[loop_index].vertex_index]
    plane.rotation_euler.x=math.radians(55)
    driver=plane.driver_add('rotation_euler',2).driver;driver.type='SCRIPTED';driver.expression='-facing'
    variable=driver.variables.new();variable.name='facing';variable.type='SINGLE_PROP'
    variable.targets[0].id=character['root'];variable.targets[0].data_path='rotation_euler[2]'
    # Shift only along the orthographic camera ray. This changes depth ordering
    # without moving the registered plate by a single projected pixel. A 2D
    # display plane has no physical ground footprint; native body/knife do.
    horizontal=math.cos(math.radians(35))*CAMERA_DEPTH_BIAS_CELLS/native_scale
    plane.location.z=math.sin(math.radians(35))*CAMERA_DEPTH_BIAS_CELLS/native_scale
    for axis,expression in [(0,'-sin(facing)*'+repr(horizontal)),(1,'-cos(facing)*'+repr(horizontal))]:
        ray_driver=plane.driver_add('location',axis).driver;ray_driver.type='SCRIPTED';ray_driver.expression=expression
        ray_variable=ray_driver.variables.new();ray_variable.name='facing';ray_variable.type='SINGLE_PROP'
        ray_variable.targets[0].id=character['root'];ray_variable.targets[0].data_path='rotation_euler[2]'
    material=bpy.data.materials.new(name+'__transparent_2D_material');material.use_nodes=True
    material['sprite_source']='ImageGen 2D cutout; preserve texture and alpha'
    nodes=material.node_tree.nodes;nodes.clear();links=material.node_tree.links
    output=nodes.new('ShaderNodeOutputMaterial');texture=nodes.new('ShaderNodeTexImage');texture.image=image;texture.interpolation='Linear';texture.extension='CLIP'
    emission=nodes.new('ShaderNodeEmission');links.new(texture.outputs['Color'],emission.inputs['Color'])
    transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
    links.new(texture.outputs['Alpha'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    if hasattr(material,'surface_render_method'):material.surface_render_method='DITHERED'
    if hasattr(material,'use_transparent_shadow'):material.use_transparent_shadow=False
    plane.data.materials.append(material)
    plane['representation']='2D ImageGen sprite, not modeled sushi';plane['fixed_alpha_rectangle']=json.dumps([x0,y0,x1,y1])
    plane['source_image']=str(path);plane['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    plane['world_width_cells']=SPRITE_WIDTH_CELLS;plane['camera_ray_depth_bias_world_cells']=CAMERA_DEPTH_BIAS_CELLS
    return root,plane,{'path':str(path),'sha256':plane['source_sha256'],'alphaRectangleBottomOrigin':[x0,y0,x1,y1],
        'worldWidthCells':SPRITE_WIDTH_CELLS,'cameraElevationDegrees':35,'cameraRayDepthBiasCells':CAMERA_DEPTH_BIAS_CELLS,'attachmentRevision':3,'facingPolicy':'player-facing, native yaw cancellation driver',
        'registration':'fixed full source alpha rectangle, lowest plate pixel at evaluated palm attachment'}


def add_held_props(character,food_builder,recipe='dish-salmon'):
    target=character['collection'];food_root,plane,evidence=_food_sprite(character,recipe)
    original=character['pose'];parts=[plane]
    # The knife remains a real native prop. It does not introduce 3D sushi.
    utensil=bpy.data.objects.new(character['root'].name+'__utensil',None);target.objects.link(utensil);utensil.parent=character['root']
    for name,loc,size,mat in [('handle',(0,0,0),(.028,.075,.030),food_builder.M['wood_dark']),('blade',(0,-.080,.004),(.046,.12,.010),food_builder.M['metal'])]:
        bpy.ops.mesh.primitive_cube_add(size=1);obj=bpy.context.object;obj.name=character['root'].name+'__knife_'+name
        for collection in list(obj.users_collection):collection.objects.unlink(obj)
        target.objects.link(obj);obj.parent=utensil;obj.location=loc;obj.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);obj.data.materials.append(mat);parts.append(obj)
    def pose(clip,t):
        original(clip,t)
        hands=json.loads(character['armature']['hand_sockets_current']);left=Vector(hands['L']);right=Vector(hands['R']);center=(left+right)*.5
        holding=clip in ['hold','load','eat','seated_wait','seated-wait']
        plane.hide_render=not holding
        food_root.location=center+Vector((0,0,.018));food_root.rotation_euler=(0,0,0)
        utensil.location=right;utensil.rotation_euler=(0,.18*math.sin(t*math.tau),0)
        for obj in utensil.children:obj.hide_render=clip!='work'
        bpy.context.view_layer.update()
    character['pose']=pose
    character['held_composition']={'recipe':recipe,'foodRoot':food_root,'utensilRoot':utensil,'parts':parts,'source':'ImageGen 2D source','image':evidence}
    character['root']['food_composition']='ImageGen '+recipe+' fixed alpha plane attached to evaluated palms; facing-independent image; knife during work.'
    character['root']['held_food_source']=json.dumps(evidence)
    return character


def bake_props(character,actions):
    roots=[character['held_composition']['foodRoot'],character['held_composition']['utensilRoot']];result={}
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


def upgrade_existing(character,force=False):
    """Upgrade an already-created ImageGen composition before native baking.

    This is useful for a live batch that loaded the earlier module while isolated
    image/depth diagnostics were still running. It never rebuilds the character.
    """
    composition=character['held_composition'];food_root=composition['foodRoot']
    evidence=composition.get('image',{})
    if evidence.get('attachmentRevision',1)>=3 and not force:return character
    plane=next(obj for obj in composition['parts'] if obj.get('representation')=='2D ImageGen sprite, not modeled sushi')
    native_scale=float(character['root'].get('uniform_native_scale',1.25))
    current_width=(max(v.co.x for v in plane.data.vertices)-min(v.co.x for v in plane.data.vertices))*native_scale
    if abs(current_width-SPRITE_WIDTH_CELLS)>1e-8:
        for vertex in plane.data.vertices:vertex.co*=SPRITE_WIDTH_CELLS/current_width
    horizontal=math.cos(math.radians(35))*CAMERA_DEPTH_BIAS_CELLS/native_scale
    plane.location.z=math.sin(math.radians(35))*CAMERA_DEPTH_BIAS_CELLS/native_scale
    for axis,expression in [(0,'-sin(facing)*'+repr(horizontal)),(1,'-cos(facing)*'+repr(horizontal))]:
        try:plane.driver_remove('location',axis)
        except (TypeError,RuntimeError):pass
        driver=plane.driver_add('location',axis).driver;driver.type='SCRIPTED';driver.expression=expression
        variable=driver.variables.new();variable.name='facing';variable.type='SINGLE_PROP'
        variable.targets[0].id=character['root'];variable.targets[0].data_path='rotation_euler[2]'
    # Rebind only the 2D plate attachment, retaining the accepted body pose.
    # Reasserting the measured palm midpoint avoids stacking legacy Y offsets
    # when upgrading an already-patched live object. force=True is idempotent.
    original=composition.get('_pose_before_attachment_revision3',character['pose'])
    composition['_pose_before_attachment_revision3']=original
    def pose(clip,t):
        original(clip,t)
        hands=json.loads(character['armature']['hand_sockets_current'])
        center=(Vector(hands['L'])+Vector(hands['R']))*.5
        food_root.location=center+Vector((0,0,.018));food_root.rotation_euler=(0,0,0)
        plane.hide_render=clip not in ['hold','load','eat','seated_wait','seated-wait']
        bpy.context.view_layer.update()
    character['pose']=pose
    evidence.update(worldWidthCells=SPRITE_WIDTH_CELLS,cameraRayDepthBiasCells=CAMERA_DEPTH_BIAS_CELLS,attachmentRevision=3)
    plane['world_width_cells']=SPRITE_WIDTH_CELLS;plane['camera_ray_depth_bias_world_cells']=CAMERA_DEPTH_BIAS_CELLS
    character['root']['held_food_source']=json.dumps(evidence)
    return character
