"""Private native construction and saved-action replay. No raster assets used."""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

FACING = {'N':180, 'E':90, 'S':0, 'W':-90}
CLIPS = ['shimmer','attract','collect','b-shimmer','b-attract','b-collect','c-shimmer','c-attract','c-collect']
ROOTS = ['salvage_a__root.001','salvage_b__root.001','salvage_c__root.001']

def variant(clip): return 1 if clip.startswith('b-') else 2 if clip.startswith('c-') else 0
def curves(action):
    return [f for l in action.layers for s in l.strips for bag in s.channelbags for f in bag.fcurves]
def mat(name, color, metallic=0, roughness=.55):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=roughness;p.inputs['Specular IOR Level'].default_value=.3
    return m
def finish(obj, parent, material, bevel=.02):
    obj.parent=parent;obj.data.materials.append(material)
    if bevel:
        m=obj.modifiers.new('Soft forged edges','BEVEL');m.width=bevel;m.segments=4;m.affect='EDGES';m.harden_normals=True
    for p in obj.data.polygons:p.use_smooth=True
    n=obj.modifiers.new('Planar weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
    obj['variantIndex']=parent['variantIndex'];return obj
def box(name, loc, size, parent, material, bevel=.02, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc);o=bpy.context.object;o.name=name
    for v in o.data.vertices:
        for i in range(3):v.co[i]*=size[i]
    o.rotation_euler=rotation
    return finish(o,parent,material,bevel)
def bolt(name, center, normal, radius, parent, steel, dark):
    normal=Vector(normal).normalized();q=normal.to_track_quat('Z','Y')
    for suffix,r,d,offset,material,sides in [('seat',radius*1.25,.012,0,dark,24),('head',radius,.036,.018,steel,6)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=d,location=Vector(center)+normal*offset)
        o=bpy.context.object;o.name=name+'__'+suffix;o.rotation_euler=q.to_euler();finish(o,parent,material,.006 if suffix=='head' else .003)
def prism(name, profile, width, parent, material):
    n=len(profile);verts=[(x,y,z) for x in [-width/2,width/2] for y,z in profile]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);return finish(o,parent,material,.022)
def camera_record():
    sc=bpy.context.scene;c=sc.camera
    def px(p):
        v=world_to_camera_view(sc,c,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
    root=px((0,0,0));axes={k:[v[i]-root[i] for i in range(2)] for k,v in [('unitX',px((1,0,0))),('unitDepth',px((0,-1,0))),('unitHeight',px((0,0,1)))]}
    return {'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in c.matrix_world],'projectionMatrix':[list(r) for r in c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(math.atan(1/.7))},'calibration':{'root':root,**axes}}
def setup_camera_lights():
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
    cam=bpy.data.objects.new('Registered 55 degree camera',bpy.data.cameras.new('Registered orthographic'));sc.collection.objects.link(cam);sc.camera=cam
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
    e=math.atan(1/.7);cam.location=(0,-10*math.cos(e),10*math.sin(e));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
    def px():return (1-world_to_camera_view(sc,cam,Vector((0,0,0))).y)*1408
    base=px();cam.data.shift_y=1;bpy.context.view_layer.update();cam.data.shift_y=(992-base)/(px()-base);bpy.context.view_layer.update()
    sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=50;sc.render.dither_intensity=0
    sc.render.fps=12;sc.frame_start=1;sc.frame_end=12;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.world=bpy.data.worlds.new('Neutral soft world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.82,.86,.92,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.24
    for name,pos,energy,size in [('overhead',(0,0,4.5),110,4.0)]+[(f'cardinal{i}',pos,55,4.0) for i,pos in enumerate([(3,0,2.8),(-3,0,2.8),(0,3,2.8),(0,-3,2.8)])]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=(1,.96,.9);o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    if hasattr(sc,'eevee'):sc.eevee.taa_render_samples=32
    sc.render.filter_size=1.5
    sc['recipe']='Private round01: true bevels/weighted normals, clean broad matte steel, symmetric overhead+four equal cardinal broad lights, no floor or external image textures.'
def build():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for a in list(bpy.data.actions):bpy.data.actions.remove(a)
    for m in list(bpy.data.materials):bpy.data.materials.remove(m)
    sc=bpy.context.scene;sc.name='Salvage metal round01 native'
    steel=mat('Soft blue-gray steel',(.17,.27,.35),.22,.5);light=mat('Pale worn steel',(.32,.44,.52),.2,.48);dark=mat('Deep slate seams',(.055,.095,.13),.16,.58);wood=mat('Warm cut wood',(.42,.19,.061),0,.75);grain=mat('Wood join lines',(.22,.078,.019),0,.85);wear=mat('Restrained ochre wear',(.38,.205,.075),.05,.73)
    parents=[]
    for i,name in enumerate(ROOTS):
        root=bpy.data.objects.new(name,None);sc.collection.objects.link(root);root['variantIndex']=i
        p=bpy.data.objects.new(f'salvage_{"abc"[i]}__assembly',None);sc.collection.objects.link(p);p.parent=root;p['variantIndex']=i;parents.append(p)
    p=parents[0]
    box('plate__forged_body',(0,0,.21),(.65,.48,.42),p,steel,.035)
    box('plate__rolled_rim',(0,0,.455),(.72,.57,.09),p,dark,.035)
    box('plate__broad_top',(0,0,.477),(.704,.554,.09),p,light,.033)
    for side in [-1,1]:
        for x in [-.19,.19]:bolt(f'plate__fastener_{side}_{x}',(x,side*.247,.22),(0,side,0),.061,p,light,dark)
    for x,y,angle,length in [(-.17,-.12,-.40,.14),(.17,.13,-.40,.09)]:
        box(f'plate__worn_score_{x}',(x,y,.522),(length,.008,.003),p,wear,.002,(0,0,angle))
    p=parents[1]
    profile=[(-.21,0),(.15,0),(.15,.30),(.07,.60),(-.06,.65),(-.13,.61),(-.03,.32),(-.21,.27)]
    prism('bent__continuous_fold',profile,.46,p,steel)
    bolt('bent__lower_bolt',(0,-.215,.135),(0,-1,0),.054,p,light,dark)
    bolt('bent__upper_bolt',(0,-.0714,.44),(0,-.945,-.326),.054,p,light,dark)
    box('bent__fold_seam',(0,-.127,.284),(.40,.018,.018),p,dark,.007,(math.radians(-20),0,0))
    for x in [-.21,.21]:
        box(f'bent__cut_wear_{x}',(x,.025,.612),(.018,.105,.012),p,wear,.005,(math.radians(-20),0,0))
    p=parents[2]
    box('mixed__wood_block',(-.17,0,.175),(.37,.43,.35),p,wood,.028)
    for side in [-1,1]:
        for z in [.112,.245]:box(f'mixed__plank_seam_{side}_{z}',(-.17,side*.214,z),(.32,.006,.008),p,grain,.003)
    angle=-.20;h=.61;w=.32;z=(h*math.cos(angle)+w*abs(math.sin(angle)))/2
    scrap=box('mixed__leaning_steel',(.155,.016,z),(w,.37,h),p,steel,.03,(0,angle,0))
    # Small cap on the actual upper steel face; same rotation and attached overlap.
    caploc=Vector(scrap.location)+scrap.rotation_euler.to_matrix()@Vector((0,0,h/2-.008))
    box('mixed__steel_cap',caploc,(w*.91,.34,.035),p,light,.012,(0,angle,0))
    for side in [-1,1]:
        box(f'mixed__retaining_strap_{side}',(0,side*.235,.205),(.62,.048,.078),p,dark,.016)
        for x in [-.23,.22]:bolt(f'mixed__strap_bolt_{side}_{x}',(x,side*.263,.205),(0,side,0),.032,p,light,dark)
    setup_camera_lights()
    rig={'assetId':'salvage-metal','fps':12,'static':False,'source':'round01_native.py','groundRootObject':ROOTS[0],'variantRoots':ROOTS,'clips':{},'armatures':[],'footprint':[1,1],'sockets':{},'ports':{}}
    for clip in CLIPS:
        i=variant(clip);p=parents[i];p.animation_data_clear();loop=not clip.endswith('collect')
        for frame in range(1,14 if loop else 25):
            if loop:
                t=(frame-1)%12/12;z=0;s=1;r=(.022 if clip.endswith('shimmer') else .042)*math.sin(2*math.pi*t)
            else:
                t=min(frame-1,11)/11;e=t*t*(3-2*t);z=.95*e;s=1-.935*e;r=.16*math.sin(math.pi*t)
            p.location=(0,0,z);p.scale=(s,s,s);p.rotation_euler=(0,0,r)
            for path in ['location','scale','rotation_euler']:p.keyframe_insert(path,frame=frame)
        action=p.animation_data.action;action.name='SALVAGE_ROUND01__'+clip;action.use_fake_user=True
        for f in curves(action):
            f.extrapolation='CONSTANT'
            for k in f.keyframe_points:k.interpolation='LINEAR'
        rig['clips'][clip]={'frames':12,'fps':12,'loop':loop,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13 if loop else None,'variantIndex':i,'variantRoot':ROOTS[i],'actions':[{'ownerType':'Object','ownerName':p.name,'action':action.name,'slotIdentifier':p.animation_data.action_slot.identifier}], 'motion':'Rigid whole-assembly native motion; rest pivot at registered ground; bounded Z rise and scale for collect.'}
    sc['salvage_round01_rig']=json.dumps(rig);activate('shimmer','S',1);return rig
def activate(clip,direction,frame):
    sc=bpy.context.scene;rig=json.loads(sc['salvage_round01_rig']);i=variant(clip)
    for index,name in enumerate(ROOTS):
        root=bpy.data.objects[name];root.rotation_euler=(0,0,math.radians(FACING[direction]));p=bpy.data.objects[f'salvage_{"abc"[index]}__assembly'];p.animation_data_clear()
        p.location=(0,0,0);p.scale=(1,1,1);p.rotation_euler=(0,0,0)
        for obj in sc.objects:
            if obj.type=='MESH' and obj.get('variantIndex')==index:obj.hide_render=index!=i;obj.hide_viewport=False;obj.hide_set(False)
    entry=rig['clips'][clip];owner=bpy.data.objects[entry['actions'][0]['ownerName']];owner.animation_data_create();owner.animation_data.action=bpy.data.actions[entry['actions'][0]['action']]
    owner.animation_data.action_slot=owner.animation_data.action.slots[0]
    sc.frame_set(frame);bpy.context.view_layer.update();return rig, bpy.data.objects[ROOTS[i]],owner

if __name__=='__main__':
    base=Path(__file__).resolve().parents[1];rig=build();p=base/'source/round-01.blend'
    if p.exists():raise RuntimeError('Refuse replacing saved round')
    bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
    (base/'candidates/round-01/rig.json').write_text(json.dumps(rig,indent=2)+'\n')
    print('ROUND01_NATIVE_SAVED',str(p))
