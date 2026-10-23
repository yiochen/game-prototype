"""Issue 33 native creature and world-effect authoring through ROOT Blender MCP.

This module performs no file I/O, camera changes, rendering or scene deletion.
create_asset(id) returns real geometry, an independent ground root, explicit clips,
and deterministic pose/reset/bake_actions callables. One model unit = one tile.
Coordinates X=right, -Y=depth, Z=up. Actor art uses ordinary orthographic camera;
environment/axis effects use square top/front oblique capture.
"""
import bpy
import math
import json
from mathutils import Vector

TAU = math.tau
PALETTE = {
 'blue':'168FD2','blue_dark':'08649D','blue_light':'42B9E7','yellow':'FFD247',
 'yellow_dark':'F7A62D','cream':'FFF0BD','white':'F6FAF4','navy':'17344F',
 'black':'102C43','aqua':'4DDCF0','cyan':'A1F5F6','teal':'1FADBD',
 'pink':'EE7098','red':'E8525D','orange':'F6A232','amber':'FFC744',
 'gold':'F8C139','gold_dark':'CB841F','metal':'819AA8','metal_light':'D7E5E7',
 'reef':'4A7EAE','purple':'7963BC','green':'72C95A'
}


def _linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def material(name, emission=0.0, alpha=1.0):
    key = 'S33_CFX_' + name + ('_emit' if emission else '')
    result = bpy.data.materials.get(key)
    if result:
        return result
    rgb = tuple(_linear(int(PALETTE.get(name, name).lstrip('#')[i:i+2], 16) / 255) for i in (0,2,4))
    result = bpy.data.materials.new(key)
    result.diffuse_color = (*rgb, alpha)
    result.use_nodes = True
    shader = next((n for n in result.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if shader is None:
        shader = result.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output = next((n for n in result.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if output is None:
            output = result.node_tree.nodes.new('ShaderNodeOutputMaterial')
        result.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    shader.inputs['Base Color'].default_value = (*rgb, alpha)
    shader.inputs['Roughness'].default_value = .8
    if 'Metallic' in shader.inputs:
        shader.inputs['Metallic'].default_value = .0
    if 'Alpha' in shader.inputs:
        shader.inputs['Alpha'].default_value = alpha
    if 'Specular IOR Level' in shader.inputs:
        shader.inputs['Specular IOR Level'].default_value = .22
    emission_input = shader.inputs.get('Emission Color') or shader.inputs.get('Emission')
    if emission_input is not None:
        emission_input.default_value = (*rgb, 1)
    if 'Emission Strength' in shader.inputs:
        shader.inputs['Emission Strength'].default_value = emission
    return result


def _clip(frames=12, loop=True, static=False):
    return {'frames':frames, 'fps':12, 'loop':loop, 'static':static}


class Builder:
    def __init__(self, asset_id):
        self.id = asset_id
        self.collection = bpy.data.collections.new('S33_CFX_' + asset_id)
        bpy.context.scene.collection.children.link(self.collection)
        self.root = bpy.data.objects.new(asset_id + '__ground_root', None)
        self.collection.objects.link(self.root)
        self.root.empty_display_type = 'PLAIN_AXES'
        self.root.empty_display_size = .2
        self.parts = {}
        self.sockets = {}
        self.motion = {}
        self.vertex_motion = {}
        self.footprint = [1,1]
        self.height = 1.0
        self.projection = 'square-top-front-oblique'
        self.notes = []
        self.rig = None
        self.frame_size = [192,320]
        self.frame_root = [96,248]

    def add(self, obj, name, color=None):
        obj.name = self.id + '__' + name
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        self.collection.objects.link(obj)
        obj.parent = self.root
        if color:
            obj.data.materials.append(material(color))
        self.parts[name] = obj
        return obj

    def mesh(self, name, verts, faces, color='aqua'):
        data = bpy.data.meshes.new(self.id + '__' + name + '_mesh')
        data.from_pydata(verts, [], faces)
        data.update()
        obj = bpy.data.objects.new(self.id + '__' + name, data)
        self.collection.objects.link(obj)
        obj.parent = self.root
        obj.data.materials.append(material(color))
        self.parts[name] = obj
        return obj

    def ico(self, name, loc, scale, color='aqua', subdivisions=1):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=loc)
        obj = self.add(bpy.context.object, name, color)
        obj.scale = scale
        return obj

    def box(self, name, loc, scale, color='aqua', bevel=.01):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        obj = self.add(bpy.context.object, name, color)
        obj.dimensions = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            modifier = obj.modifiers.new('Angular edge bevel', 'BEVEL')
            modifier.width = bevel
            modifier.segments = 1
        return obj

    def cylinder(self, name, loc, radius, depth, color='aqua', vertices=10, rotation=(0,0,0)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
        obj = self.add(bpy.context.object, name, color)
        obj.rotation_euler = rotation
        return obj

    def beam(self, name, a, c, width, color='aqua'):
        a, c = Vector(a), Vector(c)
        obj = self.box(name, (a+c)/2, (width,width,(c-a).length), color, .005)
        obj.rotation_euler = (c-a).to_track_quat('Z','Y').to_euler()
        return obj

    def tube(self, name, points, radius=.025, color='aqua', sides=6):
        """Real continuous low-poly tube with an animatable native shape key."""
        def vertices(samples):
            result=[]
            for index,p in enumerate(samples):
                p=Vector(p)
                tangent=Vector(samples[min(index+1,len(samples)-1)])-Vector(samples[max(index-1,0)])
                if tangent.length < 1e-8:
                    tangent=Vector((0,1,0))
                tangent.normalize()
                cross=tangent.cross(Vector((0,0,1)))
                if cross.length < 1e-6:
                    cross=tangent.cross(Vector((0,1,0)))
                cross.normalize(); up=cross.cross(tangent).normalized()
                for side in range(sides):
                    angle=side*TAU/sides
                    result.append(tuple(p+radius*(math.cos(angle)*cross+math.sin(angle)*up)))
            return result
        faces=[]
        for ring in range(len(points)-1):
            for side in range(sides):
                faces.append((ring*sides+side,ring*sides+(side+1)%sides,(ring+1)*sides+(side+1)%sides,(ring+1)*sides+side))
        faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+i for i in range(sides))])
        obj=self.mesh(name,vertices(points),faces,color)
        obj.shape_key_add(name='Basis')
        live=obj.shape_key_add(name='Procedural deformation')
        live.value=1.0
        def update(samples):
            if len(samples) != len(points):
                raise ValueError('Tube animation preserves section count')
            for target,position in zip(live.data,vertices(samples)):
                target.co=position
        self.vertex_motion[name]=(obj,live,update)
        return obj,update

    def finish(self, clips, pose_function=None):
        baseline={name:(obj.location.copy(),obj.rotation_euler.copy(),obj.scale.copy(),obj.hide_render)
                  for name,obj in self.parts.items()}
        def reset():
            for name,obj in self.parts.items():
                loc,rot,scale,hidden=baseline[name]
                obj.location=loc;obj.rotation_euler=rot;obj.scale=scale;obj.hide_render=hidden
            if self.rig:
                self.rig.location=(0,0,0)
                self.rig.rotation_euler=(0,0,0)
                for bone in self.rig.pose.bones:
                    bone.rotation_mode='XYZ';bone.rotation_euler=(0,0,0)
        def pose(clip='idle',t=0.0):
            reset()
            config=clips.get(clip,clips[next(iter(clips))])
            t=float(t)%1.0 if config.get('loop') else min(1.,max(0.,float(t)))
            if pose_function:
                pose_function(clip,t)
            elif clip in self.motion:
                self.motion[clip](t)
            elif 'idle' in self.motion:
                self.motion['idle'](t)
            bpy.context.view_layer.update()
        def bake_actions():
            """Bake transforms, rig bones and live geometry into editable native actions.

            Dynamic geometry is sampled into individual shape keys, not substituted
            by a rendered image. No camera or global scene frame changes are needed.
            """
            actions=[]
            targets=list(self.parts.values())
            if self.rig and self.rig not in targets:
                targets.append(self.rig)
            for cid,config in clips.items():
                for target in targets:
                    target.animation_data_create()
                    target.animation_data.action=bpy.data.actions.new('S33_'+self.id+'_'+cid+'_'+target.name.split('__')[-1])
                    actions.append(target.animation_data.action.name)
                shape_targets=[]
                for name,(target,live,updater) in self.vertex_motion.items():
                    if not target.data.shape_keys:
                        continue
                    target.data.shape_keys.animation_data_create()
                    target.data.shape_keys.animation_data.action=bpy.data.actions.new('S33_'+self.id+'_'+cid+'_'+name+'_mesh')
                    actions.append(target.data.shape_keys.animation_data.action.name)
                    shape_targets.append((target,live))
                count=config['frames']
                for index in range(count+int(bool(config.get('loop')))):
                    t=index/count if config.get('loop') else index/max(1,count-1)
                    pose(cid,t)
                    frame=index+1
                    for target in targets:
                        for path in ('location','rotation_euler','scale'):
                            target.keyframe_insert(data_path=path,frame=frame)
                    if self.rig:
                        for bone in self.rig.pose.bones:
                            bone.keyframe_insert(data_path='rotation_euler',frame=frame,group=bone.name)
                    for target,live in shape_targets:
                        live.value=0.0
                        live.keyframe_insert(data_path='value',frame=frame)
                        key=target.shape_key_add(name=cid+'_'+str(index).zfill(2))
                        for dest,src in zip(key.data,live.data):
                            dest.co=src.co
                        key.value=1.;key.keyframe_insert(data_path='value',frame=frame)
                        key.value=0.
                        key.keyframe_insert(data_path='value',frame=frame-1)
                        key.keyframe_insert(data_path='value',frame=frame+1)
                for target in targets:
                    if target.animation_data:
                        target.animation_data.action=None
                for target,live in shape_targets:
                    target.data.shape_keys.animation_data.action=None
                    live.value=1.0
                    for key in target.data.shape_keys.key_blocks:
                        if key.name not in ['Basis','Procedural deformation']:
                            key.value=0
                reset()
            pose(next(iter(clips)),0)
            return actions
        self.root['asset_id']=self.id
        self.root['ground_root']='[0,0,0]'
        self.root['footprint_cells']=json.dumps(self.footprint)
        self.root['visual_height']=self.height
        self.root['sockets']=json.dumps(self.sockets)
        self.root['animation_recipes']=json.dumps(clips)
        self.root['projection']=self.projection
        self.root['source']='creature_fx_builders.py'
        self.root['notes']=json.dumps(self.notes)
        result={'root':self.root,'collection':self.collection,'parts':self.parts,
                'footprint':self.footprint,'height':self.height,'directions':['N','E','S','W'],
                'sockets':self.sockets,'clips':clips,'pose':pose,'reset':reset,
                'bake_actions':bake_actions,'projection':self.projection,
                'frameSize':self.frame_size,'frameRoot':self.frame_root,'notes':self.notes}
        if self.rig:
            result['rig']=self.rig
        return result


def build_creature(builder,eel=True):
    """Single continuous faceted body, weighted cross-sections and real armature."""
    b=builder
    b.projection='character-orthographic'
    b.height=.9 if eel else .84
    b.footprint=[1,2] if eel else [1,1]
    if eel:
        b.frame_size=[256,384];b.frame_root=[128,300]
    y_head=.52 if eel else .43
    y_tail=-1.0 if eel else -.58
    center_z=.44
    bone_count=7 if eel else 5
    arm_data=bpy.data.armatures.new(b.id+'__spine_armature')
    arm=bpy.data.objects.new(b.id+'__armature',arm_data)
    b.collection.objects.link(arm);arm.parent=b.root;b.rig=arm
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True);bpy.context.view_layer.objects.active=arm
    bpy.ops.object.mode_set(mode='EDIT')
    for index in range(bone_count):
        bone=arm_data.edit_bones.new('spine_'+str(index))
        bone.head=(0,y_head+(y_tail-y_head)*index/bone_count,center_z)
        bone.tail=(0,y_head+(y_tail-y_head)*(index+1)/bone_count,center_z)
        if index:
            bone.parent=arm_data.edit_bones['spine_'+str(index-1)]
            bone.use_connect=True
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.show_in_front=True
    sections=29 if eel else 19;sides=10
    verts=[];faces=[];station=[]
    for ring in range(sections):
        q=ring/(sections-1)
        y=y_tail+(y_head-y_tail)*q
        if eel:
            width=.035+.18*q**.55
            height=.035+.16*q**.5
        else:
            width=.035+.25*math.sin(q*math.pi)**.75
            height=.035+.30*math.sin(q*math.pi)**.75
        if not eel and q>.88:
            width*=1.12;height*=1.1
        for side in range(sides):
            a=side*TAU/sides
            verts.append((width*math.cos(a),y,center_z+height*math.sin(a)))
            station.append(q)
    for ring in range(sections-1):
        for side in range(sides):
            faces.append((ring*sides+side,ring*sides+(side+1)%sides,(ring+1)*sides+(side+1)%sides,(ring+1)*sides+side))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple((sections-1)*sides+i for i in range(sides))])
    body=b.mesh('continuous_body',verts,faces,'blue')
    body.data.materials.append(material('blue_dark'));body.data.materials.append(material('cream' if eel else 'blue_light'))
    for polygon in body.data.polygons:
        center=polygon.center
        if center.z<center_z-.025:polygon.material_index=2
        elif center.z>center_z+.11:polygon.material_index=1
    def weight(obj,positions=None,force_head=False):
        groups=[obj.vertex_groups.new(name='spine_'+str(i)) for i in range(bone_count)]
        for vertex in obj.data.vertices:
            q=(vertex.co.y-y_tail)/(y_head-y_tail)
            distance=max(0.,min(bone_count-.0001,(1-q)*bone_count-.5))
            lo=int(distance);hi=min(bone_count-1,lo+1);frac=distance-lo
            if hi==lo:
                frac=0.0
            if force_head:
                lo=hi=0;frac=0
            groups[lo].add([vertex.index],1-frac,'REPLACE')
            if hi!=lo and frac:
                groups[hi].add([vertex.index],frac,'REPLACE')
        modifier=obj.modifiers.new('Continuous weighted spine','ARMATURE');modifier.object=arm
        obj.parent=arm
    weight(body)
    # Thin connected dorsal ribbon shares spine weights; it bends with body sections.
    fin_verts=[];fin_faces=[]
    for ring in range(sections):
        q=ring/(sections-1);y=y_tail+(y_head-y_tail)*q
        top=center_z+(.035+.16*q**.5 if eel else .035+.30*math.sin(q*math.pi*.93)**.65)
        crest=(.17 if eel else .20)*math.sin(q*math.pi)**1.2
        fin_verts.extend([(-.009,y,top),(.009,y,top),(0,y,top+crest)])
    for ring in range(sections-1):
        for side in range(3):
            fin_faces.append((ring*3+side,ring*3+(side+1)%3,(ring+1)*3+(side+1)%3,(ring+1)*3+side))
    dorsal=b.mesh('continuous_dorsal_fin',fin_verts,fin_faces,'yellow' if eel else 'blue_dark');weight(dorsal)
    # Sculpted tail paddle and paired side fins are complete real wedges, not icons.
    if eel:
        # Slender curved continuation of the tail, with a narrow vertical yellow
        # ribbon rather than a broad triangular fish paddle. Complete connected
        # cross-sections keep the fin dimensional in all four native views.
        tail_vertices=[];tail_faces=[]
        stations=[(0.,.045,.035,.045),(.018,-.075,.035,.085),(.067,-.18,.026,.065),(.125,-.27,.009,.022)]
        for x,dy,width,rise in stations:
            tail_vertices.extend([(x-width,y_tail+dy,center_z),(x,y_tail+dy,center_z+rise),(x+width,y_tail+dy,center_z),(x,y_tail+dy,center_z-rise*.55)])
        for ring in range(len(stations)-1):
            for side in range(4):tail_faces.append((ring*4+side,ring*4+(side+1)%4,(ring+1)*4+(side+1)%4,(ring+1)*4+side))
        tail_faces.extend([(3,2,1,0),(12,13,14,15)])
        tail=b.mesh('tail_fin',tail_vertices,tail_faces,'yellow');weight(tail)
    else:
        tail_width=.29
        tail=b.mesh('tail_fin',[(-tail_width,y_tail-.22,center_z+.18),(tail_width,y_tail-.22,center_z+.18),(0,y_tail+.08,center_z),(0,y_tail-.25,center_z-.17),(0,y_tail-.20,center_z+.05)],[(0,1,4),(1,2,4),(2,0,4),(0,2,3),(2,1,3),(1,0,3)],'blue_dark');weight(tail)
    for sign in (-1,1):
        fin_points=([(sign*.15,.13,center_z),(sign*.285,.02,center_z-.025),(sign*.24,-.13,center_z-.07),(sign*.145,-.045,center_z-.05)] if eel else [(sign*.16,.13,center_z),(sign*.42,-.02,center_z-.04),(sign*.28,-.24,center_z-.12),(sign*.13,-.03,center_z-.06)])
        fin=b.mesh('side_fin_'+str(sign),fin_points,[(0,1,2),(0,2,3),(0,3,1),(1,3,2)],'yellow' if eel else 'blue_dark');weight(fin)
        eye=b.ico('eye_white_'+str(sign),(sign*.145,y_head-.045,center_z+.150),(.065,.065,.065),'white',2);weight(eye,force_head=True)
        # Pupils sit toward the crown, with only a modest forward/lateral offset.
        # They remain visible from the elevated ordinary actor camera rather than
        # disappearing onto the hidden front of a giant white eyeball.
        pupil=b.ico('eye_pupil_'+str(sign),(sign*.155,y_head-.023,center_z+.193),(.037,.037,.037),'navy',2);weight(pupil,force_head=True)
        shine=b.ico('eye_glint_'+str(sign),(sign*.160,y_head-.017,center_z+.221),(.011,.011,.011),'white',1);weight(shine,force_head=True)
    mouth=b.beam('mouth',(-.07,y_head+.043,center_z-.055),(.07,y_head+.043,center_z-.055),.025,'navy');weight(mouth,force_head=True)
    # Canonical authored front is S=-Y. The inner orientation is independent
    # of the capture root so a renderer can rotate root for N/E/S/W inspection.
    facing=bpy.data.objects.new(b.id+'__canonical_S_facing',None)
    b.collection.objects.link(facing);facing.parent=b.root
    facing.rotation_euler.z=math.pi
    arm.parent=facing
    b.sockets={'hook':[0,-.16,center_z+.12],'cable':[0,-.16,center_z+.12],'nose':[0,-(y_head+.08),center_z]}
    b.root['canonical_front']='S=-Y'
    b.root['inner_orientation_degrees']=180
    clips={name:_clip(24,True) for name in ['normal','swim','aim','restless','pursuit','weave','dash','pause']}
    clips.update({name:_clip(12,False) for name in ['hook','caught','escape']})
    def pose(clip,t):
        amplitude={'normal':.10,'swim':.20,'aim':.12,'restless':.32,'hook':.37,'pursuit':.25,'caught':.52,'escape':.34,'weave':.30,'dash':.18,'pause':.09}.get(clip,.18)
        cycles={'normal':1,'aim':1,'restless':2,'hook':3,'pursuit':2,'caught':1,'escape':2,'dash':2}.get(clip,1)
        pulse=math.sin(t*TAU)
        if clip in ['hook','caught','escape']:
            amplitude*=.35+.65*math.sin(math.pi*t)
        for index,bone in enumerate(arm.pose.bones):
            wave=math.sin(t*TAU*cycles-index*.78)
            bone.rotation_euler.z=amplitude*wave*(.35+.65*index/(bone_count-1))
            bone.rotation_euler.x=.035*math.sin(t*TAU-index*.42)
        arm.location.z=.025*pulse
        if clip=='aim':arm.rotation_euler.x=.14+.04*pulse
        elif clip=='restless':arm.rotation_euler.y=.11*math.sin(t*TAU*2)
        elif clip=='hook':arm.rotation_euler.x=-.12*math.sin(math.pi*t);arm.rotation_euler.y=.22*math.sin(t*TAU*3)
        elif clip=='caught':
            arm.rotation_euler.x=-.23*math.sin(math.pi*t)
            for index,bone in enumerate(arm.pose.bones):bone.rotation_euler.z+=.30*math.sin(math.pi*t)*index/(bone_count-1)
        elif clip=='escape':arm.rotation_euler.z=.35*math.sin(math.pi*t);arm.location.z=.12*math.sin(math.pi*t)
        elif clip=='weave':arm.rotation_euler.z=.18*math.sin(t*TAU)
        elif clip=='dash':arm.rotation_euler.z=.15*math.sin(t*TAU)*abs(math.sin(t*TAU))
        elif clip=='pause':arm.rotation_euler.x=.04*math.sin(t*TAU)
    b.notes += ['Continuous faceted body and dorsal ribbon with blended section weights; actual seven/five-bone chain.',
                'Ground root never moves. Canonical front S=-Y uses a constant inner orientation; root remains free for capture facings. Socket coordinates include that orientation.',
                'Approved blue/yellow eel or single generic blue fish; no additional species.',
                'Native rig actions can be baked with bake_actions(); duplicate closing key omitted from sprite export.']
    return b.finish(clips,pose)


def build_bubble(b,emotion='preference'):
    b.height=1.85;b.projection='character-orthographic'
    body=b.ico('bubble',(0,0,1.42),(.39,.26,.36),'cream',2)
    b.mesh('bubble_tail',[(-.12,-.02,1.18),(.11,-.02,1.18),(-.10,-.02,.96),(-.07,.05,1.16)],[(0,1,2),(0,3,1),(0,2,3),(1,3,2)],'cream')
    if emotion=='preference':
        # Intentionally an empty socket frame, not a substitute finished food model.
        b.cylinder('dish_attachment_plate',(0,-.263,1.43),.205,.022,'white',12,(math.pi/2,0,0))
        b.sockets['dishIcon']=[0,-.286,1.43]
        for index in range(12):
            a=index*TAU/12
            obj=b.box('timer_segment_'+str(index),(.315*math.cos(a),-.145,1.42+.286*math.sin(a)),(.035,.032,.06),'pink',.005)
            obj.rotation_euler.y=-a
        b.notes.append('Dish attachment plate is a socket awaiting separately modeled dish geometry; timer segments can be manually hidden for review, not a gameplay timer.')
    elif emotion=='happy':
        for sign in (-1,1):
            b.tube('happy_eye_'+str(sign),[(sign*.15+.065*math.cos(math.pi*i/5),-.252,1.49+.045*math.sin(math.pi*i/5)) for i in range(6)],.018,'navy')
        b.tube('smile',[(.14*math.cos(math.pi+math.pi*i/8),-.272,1.39+.105*math.sin(math.pi+math.pi*i/8)) for i in range(9)],.022,'navy')
        for sign in (-1,1):b.ico('cheek_'+str(sign),(sign*.23,-.20,1.36),(.06,.018,.04),'pink',1)
    elif emotion=='puzzled':
        b.tube('question_curve',[(.11*math.cos(-.15+math.pi*1.5*i/12),-.265,1.50+.12*math.sin(-.15+math.pi*1.5*i/12)) for i in range(13)],.028,'blue_dark')
        b.beam('question_stem',(-.02,-.265,1.40),(-.02,-.265,1.34),.045,'blue_dark')
        b.ico('question_dot',(-.02,-.265,1.26),(.033,.025,.033),'blue_dark',1)
    else:
        b.box('panic_stem',(0,-.267,1.51),(.06,.045,.22),'red',.012)
        b.ico('panic_dot',(0,-.267,1.29),(.038,.026,.038),'red',1)
    clips={'appear':_clip(12,False),'idle':_clip(24,True),'fade':_clip(12,False)}
    if emotion=='happy':clips['happy-transition']=_clip(12,False)
    def pose(clip,t):
        scale=1+.025*math.sin(t*TAU)
        if clip=='appear':scale=max(.025,1-(1-t)**3)+.08*math.sin(t*math.pi*2)*(1-t)
        elif clip=='fade':scale=max(.025,1-t*t)
        elif clip=='happy-transition':scale=1+.13*math.sin(t*math.pi)
        for part in b.parts.values():
            center=Vector((0,0,1.42))
            part.location=center+(part.location-center)*scale
            part.scale*=scale
            part.location.z += .025*math.sin(t*TAU)
        if emotion=='panic':
            for part in b.parts.values():part.location.x+=.018*math.sin(t*TAU*3)
    b.sockets['customerBubble']=[0,0,1.42]
    b.notes.append('Native dimensional world bubble, transparent sprite capture. Shared customer attachment; four inspection views.')
    return b.finish(clips,pose)


def build_coin(b):
    b.height=1.12
    coin=b.cylinder('coin_disc',(0,0,.66),.22,.075,'gold',12,(math.pi/2,0,0))
    b.cylinder('coin_inset',(0,-.042,.66),.17,.012,'yellow',12,(math.pi/2,0,0))
    b.box('coin_mark',(0,-.054,.66),(.045,.012,.20),'gold_dark',.005)
    for x,z in [(-.11,.86),(.16,.96),(.31,.70)]:
        b.beam('spark_x_'+str(x),(x-.045,-.02,z),(x+.045,-.02,z),.019,'yellow')
        b.beam('spark_z_'+str(x),(x,-.02,z-.045),(x,-.02,z+.045),.019,'yellow')
    def pose(clip,t):
        for name,obj in b.parts.items():
            obj.location.z+=.42*t
            obj.scale*=max(.025,math.sin(math.pi*t)**.45)
            if name.startswith('coin'):obj.rotation_euler.z+=t*.7
    b.notes.append('Small sale coin pop has no amount label and no added reward mechanics.')
    return b.finish({'pop':_clip(12,False)},pose)


def build_harpoon(b):
    b.height=.55
    b.cylinder('shaft',(0,0,.3),.035,.75,'metal',8,(math.pi/2,0,0))
    b.mesh('point',[(0,.64,.30),(-.12,.35,.30),(.12,.35,.30),(0,.36,.39),(0,.36,.21)],[(0,1,3),(0,3,2),(0,2,4),(0,4,1),(1,4,2,3)],'metal_light')
    b.box('collar',(0,-.23,.3),(.10,.17,.10),'navy',.012)
    b.beam('barb_left',(-.12,.35,.30),(-.06,.50,.30),.025,'metal')
    b.beam('barb_right',(.12,.35,.30),(.06,.50,.30),.025,'metal')
    b.sockets={'tailCable':[0,-.40,.30],'hookTip':[0,.64,.30]}
    def pose(clip,t):
        for obj in b.parts.values():
            if clip=='launch':obj.location.z+=.025*math.sin(math.pi*t);obj.location.y+=.20*math.sin(math.pi*t)
            elif clip=='flight':obj.location.z+=.015*math.sin(t*TAU);obj.rotation_euler.y+=.02*math.sin(t*TAU)
            else:obj.rotation_euler.z+=.055*math.sin(t*TAU*2)*(1-t)
    b.notes.append('Separate projectile, explicit harpoon/cable sockets; movement here is only a local inspection gesture.')
    return b.finish({'launch':_clip(12,False),'flight':_clip(12,True),'hook':_clip(12,False)},pose)


def build_cable(b):
    b.footprint=[1,2];b.height=.7
    b.frame_size=[256,384];b.frame_root=[128,300]
    count=25
    def cable_points(t=0.,taut=False,fray=False,half=0):
        result=[]
        for index in range(count):
            q=index/(count-1)
            x=(.025 if taut else .18)*math.sin(math.pi*q)+.025*math.sin(t*TAU-q*TAU)*math.sin(math.pi*q)
            z=.38-(.015 if taut else .13)*math.sin(math.pi*q)
            y=(q-.5)*1.65
            if half:
                y=(q*.47-.5)*1.65 if half<0 else (.03+q*.47)*1.65
                x+=half*.12*math.sin(math.pi*t)
            result.append((x,y,z))
        return result
    cable,update=b.tube('main_cable',cable_points(),.024,'navy')
    left,left_update=b.tube('broken_left',cable_points(half=-1),.024,'navy')
    right,right_update=b.tube('broken_right',cable_points(half=1),.024,'navy')
    left.hide_render=right.hide_render=True
    for index in range(5):
        angle=index*TAU/5
        b.beam('fray_'+str(index),(0,0,.34),(.15*math.cos(angle),.12*math.sin(angle),.34+.09*math.sin(angle)),.014,'orange')
    b.sockets={'ship':[0,-.825,.38],'creature':[0,.825,.38]}
    def pose(clip,t):
        cable.hide_render=clip=='break'
        left.hide_render=right.hide_render=clip!='break'
        update(cable_points(t,taut=clip in ['taut','fraying']))
        left_update(cable_points(t,half=-1));right_update(cable_points(t,half=1))
        for name,obj in b.parts.items():
            if name.startswith('fray_'):
                obj.hide_render=clip not in ['fraying','break']
                obj.scale*=.5+.5*abs(math.sin(t*TAU*2+int(name.split('_')[-1])))
                if clip=='break':obj.location.z+=.1*t;obj.scale*=1-t*.7
    b.notes += ['True continuous six-sided tube sections with native shape-key deformation.',
                'Normal/taut/fraying/break states have explicit fixed endpoint sockets; target composition may span cable between actors.',
                'Break is a one-shot separated cable, not a HUD cue.']
    return b.finish({'normal':_clip(24,True),'taut':_clip(12,True),'fraying':_clip(12,True),'break':_clip(12,False)},pose)


def build_flow(b,kind='current'):
    b.height=.42;b.footprint=[1,2] if kind in ['follow','boost'] else [2,1]
    if kind in ['follow','boost']:
        b.frame_size=[256,384];b.frame_root=[128,300]
    if kind=='follow':
        for index in range(7):
            y=(index-3)*.26
            b.box('strip_'+str(index),(0,y,.08),(.26,.16,.014),'teal',.0)
            b.box('strip_glint_'+str(index),(0,y,.095),(.05,.13,.008),'aqua',.0)
        b.notes.append('Faint open-ended vertical following strip at creature X; no countdown/return arrow. Render with low review opacity metadata.')
    elif kind=='boost':
        for index in range(7):
            q=index/6
            b.ico('wake_'+str(index),(.13*math.sin(index*1.7),-.1-q*1.18,.22),(.11*(1-q*.65),.16*(1-q*.55),.10*(1-q*.65)),'aqua' if index%2 else 'cyan',1)
        for sign in (-1,1):
            b.tube('wake_rail_'+str(sign),[(sign*(.18+.12*i/8),-.2-i*.14,.15+.03*math.sin(i)) for i in range(9)],.02,'blue_light')
    else:
        # Three dimensional arrow-chevron current marks, generated from one family.
        for index in range(3):
            x=(index-1)*.48
            b.mesh('arrow_'+str(index),[(x-.22,-.13,.14),(x+.05,-.13,.14),(x+.05,-.25,.14),(x+.27,0,.14),(x+.05,.25,.14),(x+.05,.13,.14),(x-.22,.13,.14),(x-.22,-.13,.18),(x+.27,0,.18)],[(0,1,2,3,4,5,6),(7,8,3,2,1,0),(6,5,4,3,8,7)],'aqua' if kind=='current' else 'cyan')
        b.notes.append('Axis effect rotates actual geometry for four inspection orientations; flow denotes accepted lateral current only.')
    def pose(clip,t):
        for index,(name,obj) in enumerate(b.parts.items()):
            phase=t*TAU-index*.55
            if kind=='follow':
                obj.scale.x*=.84+.16*math.sin(phase)
                obj.location.z+=.009*math.sin(phase)
            elif kind=='boost':
                obj.scale*=.72+.28*(.5+.5*math.sin(phase))
                obj.location.x+=.025*math.sin(phase)
            else:
                obj.location.x+=.10*math.sin(phase)
                obj.scale*=.9+.10*math.sin(phase)
    clip='boost' if kind=='boost' else 'flow'
    if kind=='attack':
        base_pose=pose
        def attack_pose(clip,t):
            base_pose(clip,t)
            envelope=.3+.7*t if clip=='windup' else 1 if clip=='active' else max(.03,1-t)
            for obj in b.parts.values():
                obj.location*=envelope
                obj.scale*=envelope
        return b.finish({'windup':_clip(12,False),'active':_clip(24,True),'recovery':_clip(12,False)},attack_pose)
    return b.finish({clip:_clip(24,True)},pose)


def build_fragments(b):
    b.height=.9
    for index in range(9):
        a=index*2.399963
        r=.15+.12*(index%3)
        obj=b.ico('fragment_'+str(index),(r*math.cos(a),r*math.sin(a),.2+.08*(index%4)),(.11+.025*(index%3),.09,.12),'reef' if index%2 else 'purple',1)
        obj.rotation_euler=(index*.2,index*.3,index*.5)
    def pose(clip,t):
        for index,obj in enumerate(b.parts.values()):
            a=index*2.399963
            spread=.05+.15*math.sin(t*math.pi) if clip=='windup' else .15+.45*t if clip=='active' else .6+.15*t
            obj.location.x+=spread*math.cos(a);obj.location.y+=spread*math.sin(a)
            obj.location.z+=.13*math.sin(t*math.pi)*(1+index%3)
            obj.rotation_euler.x+=t*(index%3+1)*.5
            obj.rotation_euler.y+=t*.8
            if clip=='recovery':obj.scale*=max(.025,1-t*.9)
    b.notes.append('Accepted reef-breaking fragment presentation, with no damage/scheduling logic.')
    return b.finish({name:_clip(12,False) for name in ['windup','active','recovery']},pose)


def build_swirl(b):
    b.height=.75
    for layer in range(3):
        points=[]
        for index in range(29):
            q=index/28;a=q*TAU*1.3+layer*.5;r=.12+.37*q
            points.append((r*math.cos(a),r*math.sin(a),.16+layer*.16+.035*math.sin(a)))
        b.tube('swirl_ring_'+str(layer),points,.035,'cyan' if layer==2 else 'blue_light')
    b.ico('swirl_core',(0,0,.2),(.13,.13,.09),'white',1)
    def pose(clip,t):
        envelope=.4+.6*t if clip=='windup' else 1.0 if clip=='active' else max(.05,1-t*.85)
        for index,obj in enumerate(b.parts.values()):
            obj.rotation_euler.z+=TAU*t*(1+index*.15)
            obj.scale*=envelope*(.95+.05*math.sin(t*TAU))
    return b.finish({'windup':_clip(12,False),'active':_clip(24,True),'recovery':_clip(12,False)},pose)


def build_warning(b,symbol=False):
    b.height=.42
    if symbol:
        verts=[(-.04,.35,.20),(-.23,-.03,.20),(-.04,-.03,.20),(-.14,-.36,.20),(.23,.09,.20),(.04,.09,.20)]
        bolt=b.mesh('lightning_symbol',verts,[(0,1,2,3,4,5)],'amber')
        solid=bolt.modifiers.new('Lightning thickness','SOLIDIFY');solid.thickness=.045
    else:
        b.footprint=[3,1];b.frame_size=[448,384];b.frame_root=[224,300]
        b.box('warning_base',(0,0,.10),(2.9,.65,.04),'amber',.015)
        # Real connected diagonal prism bars; all stripes end at the same edge.
        for index in range(10):
            x=-1.3+index*.285
            points=[(x-.12,-.31,.135),(x+.035,-.31,.135),(x+.24,.31,.135),(x+.085,.31,.135)]
            stripe=b.mesh('warning_hatch_'+str(index),points,[(0,1,2,3)],'navy')
            solid=stripe.modifiers.new('Hatch thickness','SOLIDIFY');solid.thickness=.006
        for y in (-.335,.335):b.box('warning_border_'+str(y),(0,y,.13),(2.94,.035,.055),'yellow',.008)
        b.notes.append('Amber diagonal hatch strip distinct from faint following zone; no text/countdown/damage mechanic.')
    def pose(clip,t):
        a=.92+.08*math.sin(t*TAU*2)
        envelope=.2+.8*t if clip=='windup' else 1 if clip=='active' else max(.04,1-t)
        for obj in b.parts.values():
            obj.scale.z*=a;obj.scale.y*=envelope;obj.location.y*=envelope;obj.location.z+=.012*math.sin(t*TAU)
    return b.finish({'windup':_clip(12,False),'active':_clip(12,True),'recovery':_clip(12,False)},pose)


def build_discharge(b):
    b.height=.9
    for index in range(7):
        a=index*TAU/7
        points=[]
        for node in range(8):
            q=node/7;r=.12+.53*q
            bend=.045*math.sin(node*2.7+index)
            points.append((r*math.cos(a)+bend*math.sin(a),r*math.sin(a)+bend*math.cos(a),.38+.10*math.sin(node*1.7+index)))
        b.tube('electric_arc_'+str(index),points,.019,'cyan')
    b.ico('discharge_core',(0,0,.38),(.13,.13,.13),'white',1)
    def pose(clip,t):
        envelope=.25+.75*t if clip=='windup' else 1.0 if clip=='active' else max(.04,1-t*.95)
        for index,(name,obj) in enumerate(b.parts.items()):
            obj.scale*=envelope*(.82+.18*math.sin(t*TAU*3+index))
            obj.rotation_euler.z+=.07*math.sin(t*TAU*2+index)
            if name.startswith('electric_arc_'):
                obj.location.z+=.022*math.sin(t*TAU*3+index)
    b.notes.append('Native faceted electrical arcs; short world effect, no full-screen catch cinematic or attack timer.')
    return b.finish({'windup':_clip(12,False),'active':_clip(12,True),'recovery':_clip(12,False)},pose)


SUPPORTED_IDS=[
 'creature-eel','creature-fish','bubble-preference','bubble-happy','bubble-puzzled',
 'bubble-panic','coin-pop','harpoon-projectile','harpoon-cable','route-current',
 'boost-trail','following-strip','attack-reef-fragments','attack-swirl',
 'attack-lateral-current','eel-warning-strip','eel-lightning-symbol','eel-discharge'
]


def canonical_s(result, angle):
    """Orient authored source geometry, never the capture-controlled ground root."""
    root=result['root']
    inner=bpy.data.objects.new(root['asset_id']+'__canonical_S_facing',None)
    result['collection'].objects.link(inner)
    inner.parent=root;inner.rotation_euler.z=angle
    for child in list(root.children):
        if child != inner:
            child.parent=inner
    c,s=math.cos(angle),math.sin(angle)
    for name,point in result['sockets'].items():
        x,y,z=point
        result['sockets'][name]=[c*x-s*y,s*x+c*y,z]
    root['sockets']=json.dumps(result['sockets'])
    root['canonical_front']='S=-Y'
    root['inner_orientation_degrees']=math.degrees(angle)
    return result


def create_asset(asset_id):
    if asset_id not in SUPPORTED_IDS:
        raise ValueError('Unknown creature/worldFX asset: '+str(asset_id))
    b=Builder(asset_id)
    if asset_id in ['creature-eel','creature-fish']:
        return build_creature(b,asset_id=='creature-eel')
    if asset_id.startswith('bubble-'):
        return build_bubble(b,asset_id.split('-',1)[1])
    if asset_id=='coin-pop':return build_coin(b)
    if asset_id=='harpoon-projectile':return canonical_s(build_harpoon(b),math.pi)
    if asset_id=='harpoon-cable':return canonical_s(build_cable(b),math.pi)
    if asset_id in ['route-current','attack-lateral-current']:
        return canonical_s(build_flow(b,'current' if asset_id=='route-current' else 'attack'),-math.pi/2)
    if asset_id=='boost-trail':return canonical_s(build_flow(b,'boost'),math.pi)
    if asset_id=='following-strip':return build_flow(b,'follow')
    if asset_id=='attack-reef-fragments':return build_fragments(b)
    if asset_id=='attack-swirl':return build_swirl(b)
    if asset_id=='eel-warning-strip':return build_warning(b,False)
    if asset_id=='eel-lightning-symbol':return build_warning(b,True)
    if asset_id=='eel-discharge':return build_discharge(b)
