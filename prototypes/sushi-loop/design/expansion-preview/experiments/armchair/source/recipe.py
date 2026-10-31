"""Editable compact abandoned chair, derived from the approved native sofa scene.
Run: /opt/homebrew/bin/blender -b --python source/recipe.py -- --round draft-01 --draft
Only self-contained native mesh/curve/procedural material assets; fixed source camera.
"""
import bpy, math, json, pathlib, argparse, sys, hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent; EXP=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--round',default='draft-01');ap.add_argument('--draft',action='store_true');arg=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=EXP/'candidates'/arg.round;OUT.mkdir(parents=True,exist_ok=True)
SOURCE=EXP/'backups/original.blend';bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
sc=bpy.context.scene;root=bpy.data.objects['garbage-sofa__root'];cam=sc.camera
source_camera={'matrix':[[float(v) for v in r] for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'frame':[sc.render.resolution_x,sc.render.resolution_y]}
source_root=[[float(v) for v in r] for r in root.matrix_world]
# Keep the actual source root and capture rig. Rebuild the authorized whole furniture variant.
for o in list(bpy.data.objects):
    if o!=root and o.type not in {'CAMERA','LIGHT'}:bpy.data.objects.remove(o,do_unlink=True)
root.animation_data_clear();root['variant']='garbage-armchair';root['sourceScale']=2;root['deliveryScope']='four static facings; runtime CSS highlight/removal'
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
COLL=bpy.data.collections.new('Mustard worn armchair native parts');sc.collection.children.link(COLL)
def color(h):
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
def material(name,h,rough=.8,wear=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*color(h),1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.24;bs.inputs['Emission Color'].default_value=(*color(h),1);bs.inputs['Emission Strength'].default_value=.055;l.new(bs.outputs['BSDF'],out.inputs['Surface'])
    if wear:
        tc=n.new('ShaderNodeTexCoord');tc.object=root;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=10;noise.inputs['Detail'].default_value=1.8;noise.inputs['Roughness'].default_value=.65;l.new(tc.outputs['Object'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[0].color=tuple(v*.92 for v in color(h))+(1,);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=tuple(v*1.035 for v in color(h))+(1,);l.new(noise.outputs['Fac'],ramp.inputs[0])
        stain=n.new('ShaderNodeTexNoise');stain.inputs['Scale'].default_value=18;stain.inputs['Detail'].default_value=1.1;stain.inputs['Roughness'].default_value=.6;l.new(tc.outputs['Object'],stain.inputs['Vector']);mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.68;mask.color_ramp.elements[0].color=(0,0,0,1);mask.color_ramp.elements[1].position=.76;mask.color_ramp.elements[1].color=(.4,.4,.4,1);l.new(stain.outputs['Fac'],mask.inputs[0]);mix=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],mix.inputs[0]);l.new(ramp.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=tuple(v*.55 for v in color(h))+(1,);l.new(mix.outputs[0],bs.inputs['Base Color'])
    return m
cloth=material('Faded mustard woven cloth','BF9650',wear=True);edge=material('Raised ochre piping','D1AC66',.85);torn=material('Fresh pale torn cloth edges','E1BF7A',.9);dark=material('Deep warm cavity cloth','5C4023',.97);wood=material('Exposed worn honey timber','9D653A',.75);woodlight=material('Scraped timber grain','BC8951',.85);feetmat=material('Dark short wooden feet','68432C',.85);stuff=material('Ivory cotton stuffing','E9DDBD',.98);thread=material('Dark ochre stitched seams','A17632',.9)
def attach(o,name,mat):
    o.name='armchair__'+name
    for c in list(o.users_collection):c.objects.unlink(o)
    COLL.objects.link(o);wm=o.matrix_world.copy();o.parent=root;o.matrix_world=wm
    if mat:o.data.materials.clear();o.data.materials.append(mat)
    return o
def box(name,loc,dims,mat,bevel=.04,soft=True):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Real upholstered edge radius','BEVEL');mod.width=bevel;mod.segments=5 if soft else 3;bpy.ops.object.modifier_apply(modifier=mod.name)
    if soft:
        mod=o.modifiers.new('Broad cushion volume','SUBSURF');mod.levels=3 if name=='sagged_back_pillow' else 2;mod.render_levels=mod.levels;bpy.ops.object.modifier_apply(modifier=mod.name)
        hx,hy,hz=[v/2 for v in dims]
        for v in o.data.vertices:
            x,y,z=v.co
            if abs(z)>hz*.55:v.co.z+=math.copysign(.018*max(0,1-(x/hx)**2)*max(0,1-(y/hy)**2),z)
            if abs(x)>hx*.55:v.co.x+=math.copysign(.008*max(0,1-(y/hy)**2)*max(0,1-(z/hz)**2),x)
            if abs(y)>hy*.55:v.co.y+=math.copysign(.014*max(0,1-(x/hx)**2)*max(0,1-(z/hz)**2),y)
            if name=='sagged_back_pillow' and y<0:
                # Visible native depressed crescent and gentle lopsided slouch.
                v.co.y+=.13*math.exp(-((x-.055)/.23)**2-((z-.015)/.16)**2)
                v.co.z-=.042*math.exp(-((x-.07)/.22)**2)*max(0,1-(y/hy)**2)
            if name=='sagged_back_pillow' and z>hz*.45:
                v.co.z-=.068*math.exp(-((x-.08)/.24)**2)*max(0,1-(y/hy)**2)
                v.co.z-=.025*(x/hx+.2)*max(0,1-(y/hy)**2)
            if name=='single_sagged_seat' and z>hz*.55:
                v.co.z-=.024*math.exp(-((x+.025)/.21)**2-((y+.02)/.25)**2)
        for poly in o.data.polygons:poly.use_smooth=True
    return attach(o,name,mat)
def tube(name,pts,rad,mat,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=rad;c.bevel_resolution=3;c.use_fill_caps=True;s=c.splines.new('POLY');s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts):p.co=(*v,1)
    s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);COLL.objects.link(o);return attach(o,name,mat)
def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return attach(o,name,mat)
def panel(name,points,mat,thickness=.008):
    me=bpy.data.meshes.new(name);me.from_pydata(points,[],[tuple(range(len(points)))]);me.update();o=bpy.data.objects.new(name,me);COLL.objects.link(o);o=attach(o,name,mat)
    mod=o.modifiers.new('Physical cloth thickness','SOLIDIFY');mod.thickness=thickness;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=o.modifiers.new('Soft torn edge','BEVEL');mod.width=.004;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def prism(name,poly,axis,lo,hi):
    verts=[]
    for d in [lo,hi]:
        for a,b in poly:verts.append((a,d,b) if axis=='Y' else (a,b,d))
    n=len(poly);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);COLL.objects.link(o);return o
def cut(obj,cutter,name):
    bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
def seam(name,obj,center,half,plane,rad=.0032,mat=edge,corner=.045,side=1):
    pts=[]
    for sx,sy,a in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
        for j in range(8):
            t=math.radians(a+j*90/7);u=sx*(half[0]-corner)+corner*math.cos(t);v=sy*(half[1]-corner)+corner*math.sin(t)
            if plane=='XY':p=Vector((center[0]+u,center[1]+v,center[2]));ax=2
            elif plane=='XZ':p=Vector((center[0]+u,center[1],center[2]+v));ax=1
            else:p=Vector((center[0],center[1]+u,center[2]+v));ax=0
            start=p.copy();start[ax]=side*3;d=Vector((0,0,0));d[ax]=-side;bpy.context.view_layer.update();inv=obj.matrix_world.inverted();hit,loc,normal,_=obj.ray_cast(inv@start,inv.to_3x3()@d)
            if hit:p=obj.matrix_world@loc+(obj.matrix_world.to_3x3()@normal)*.001
            pts.append(p)
    return tube(name,pts,rad,mat,True)
# Four actual supports touch z0. No detached floor rubbish in this compact variant.
for x in [-.32,.32]:
    for y in [-.32,.32]:box('short_foot_%s_%s'%(x,y),(x,y,.055),(.12,.14,.11),feetmat,.018,False)
base=box('upholstered_base',(0,0,.195),(.81,.82,.20),cloth,.055)
box('underside_dust_cover',(0,0,.105),(.64,.64,.018),dark,.015,False)
# Low back structure joins the whole chair; one large back pillow defines the silhouette.
shell=box('rear_upholstery_shell',(0,.336,.57),(.84,.23,.79),cloth,.082)
back=box('sagged_back_pillow',(0,.245,.825),(.82,.30,.58),cloth,.105)
seam('back_rear_perimeter',shell,(0,.45,.57),(.355,.33),'XZ',.003,thread,.065,1)
# The pillow's front stays uninterrupted cloth; its broad native sag carries the
# wear cue. A rigid rectangular piping path would bridge that depressed surface.
for x in [-.205,.205]:tube('rear_shallow_seam_'+str(x),[(x,.454,.27),(x,.459,.53),(x,.451,.84)],.0028,thread)
# Bulky asymmetrical arm caps with a real damaged left front.
left=box('ripped_left_arm',(-.365,-.01,.455),(.224,.89,.64),cloth,.086)
right=box('intact_right_arm',(.365,-.01,.455),(.224,.89,.64),cloth,.086)
seam('right_front_arm_piping',right,(.365,-.458,.455),(.092,.267),'XZ',.0031,edge,.075,-1)
# Open cavity breaks the front-left sleeve and its upper rim. No dark decal plane.
arm_poly=[(-.478,.365),(-.478,.81),(-.445,.845),(-.414,.806),(-.388,.843),(-.361,.799),(-.337,.817),(-.325,.771),(-.287,.752),(-.296,.48),(-.323,.454),(-.306,.413),(-.354,.40),(-.390,.365),(-.425,.382),(-.447,.348)]
cut(left,prism('left native ragged cavity cutter',arm_poly,'Y',-.54,-.255),'Actual torn arm opening')
# Native cavity lining and exposed timber follow the cavity depth, behind frayed sleeve.
box('left_arm_dark_cavity',(-.379,-.29,.535),(.153,.025,.313),dark,.015,False)
box('exposed_vertical_wood_slat',(-.404,-.319,.55),(.100,.045,.34),wood,.010,False)
box('exposed_second_wood_slat',(-.344,-.308,.545),(.036,.039,.29),wood,.007,False)
for i,x in enumerate([-.428,-.407,-.387]):tube('exposed_wood_grain_'+str(i),[(x,-.345,.409),(x+.003,-.346,.53),(x-.002,-.343,.67)],.0011,woodlight)
# Thick attached cloth folds, not a thin outlined box. The upper flap lies along the
# actual remaining top shell and curls into the cavity; ragged points vary in depth.
panel('upper_torn_arm_cloth_fold',[(-.466,-.242,.710),(-.447,-.235,.748),(-.419,-.234,.776),(-.386,-.236,.785),(-.354,-.237,.782),(-.325,-.242,.759),(-.307,-.249,.725),(-.322,-.298,.705),(-.349,-.292,.733),(-.367,-.316,.709),(-.391,-.293,.742),(-.417,-.313,.723),(-.437,-.294,.714),(-.455,-.315,.677)],cloth,.014)
tube('upper_torn_arm_pale_fibers',[(-.307,-.249,.725),(-.322,-.298,.705),(-.349,-.292,.733),(-.367,-.316,.709),(-.391,-.293,.742),(-.417,-.313,.723),(-.437,-.294,.714),(-.455,-.315,.677)],.0031,torn)
panel('left_ragged_arm_sleeve',[(-.477,-.402,.349),(-.478,-.375,.625),(-.464,-.315,.698),(-.451,-.335,.664),(-.460,-.376,.608),(-.451,-.405,.566),(-.466,-.412,.520),(-.458,-.429,.472),(-.470,-.443,.430),(-.458,-.45,.38)],cloth,.012)
panel('peeled_lower_arm_fabric',[(-.457,-.445,.365),(-.428,-.468,.406),(-.392,-.473,.424),(-.354,-.469,.432),(-.313,-.454,.411),(-.323,-.437,.369),(-.354,-.433,.358),(-.384,-.449,.339),(-.425,-.448,.318)],cloth,.015)
tube('lower_arm_torn_pale_edge',[(-.457,-.445,.365),(-.428,-.468,.406),(-.392,-.473,.424),(-.354,-.469,.432),(-.313,-.454,.411)],.0035,torn)
for i in range(4):
    x=-.437+i*.033;tube('short_arm_fray_'+str(i),[(x,-.453,.412),(x-.005,-.462,.393)],.002,edge)
# A single compressed seat, not scaled old sofa cushions.
seat=box('single_sagged_seat',(0,-.095,.355),(.586,.689,.223),cloth,.072)
seam('seat_single_perimeter',seat,(0,-.095,.455),(.267,.315),'XY',.0035,edge,.060,1)
# A generous tear remains readable from the phone world camera, with cream stuffing.
seat_poly=[(.012,-.25),(.066,-.209),(.102,-.181),(.149,-.149),(.188,-.104),(.218,-.064),(.213,-.118),(.244,-.154),(.249,-.205),(.218,-.249),(.174,-.266),(.129,-.246),(.082,-.257),(.046,-.241)]
cut(seat,prism('seat native jagged aperture cutter',seat_poly,'Z',.382,.53),'Actual open seat cloth tear')
box('seat_tear_recessed_lining',(.147,-.187,.386),(.229,.185,.012),dark,.025,False)
for i,(loc,scale) in enumerate([((.165,-.171,.475),(.051,.044,.045)),((.212,-.213,.467),(.041,.046,.040)),((.195,-.124,.463),(.039,.033,.037))]):sphere('exposed_cotton_tuft_'+str(i),loc,scale,stuff)
tube('seat_tear_raised_pale_lip',[(.012,-.25,.457),(.066,-.209,.461),(.102,-.181,.465),(.149,-.149,.462),(.188,-.104,.458),(.218,-.064,.450)],.0053,torn)
panel('seat_torn_curled_cloth',[(-.001,-.258,.449),(.042,-.217,.468),(.09,-.193,.472),(.142,-.152,.468),(.189,-.109,.46),(.157,-.152,.480),(.107,-.192,.484),(.053,-.228,.479)],cloth,.008)
# Distinct subtle rear wear provides coherent unseen upholstery without invented accessories.
panel('rear_lower_repair',[(.12,.454,.32),(.258,.454,.333),(.25,.454,.442),(.117,.454,.429)],thread,.004)
for i in range(4):
    x=.13+i*.035;tube('rear_repair_stitch_'+str(i),[(x,.46,.325),(x+.004,.46,.344)],.0023,edge)
# Retain source world, broad symmetric five lights and its exact renderer treatment.
sc.render.resolution_percentage=100;sc.cycles.samples=16 if arg.draft else 32
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.film_transparent=True
sc.frame_set(1);root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
for blocks in [bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.images,bpy.data.cameras,bpy.data.lights,bpy.data.worlds]:
    for d in list(blocks):
        if not d.users:blocks.remove(d)
project=P/(arg.round+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(project))
def rows(m):return [[float(v) for v in r] for r in m]
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def px(v):
    p=world_to_camera_view(sc,cam,Vector(v));return [p.x*896,(1-p.y)*1152]
points={'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1))}
records=[]
for direction,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();allpts=[];parts=[]
    for o in COLL.objects:
        ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];allpts+=ps;parts.append({'name':o.name,'bounds':bounds(ps),'vertices':len(me.vertices),'faces':len(me.polygons)});ev.to_mesh_clear()
    records.append({'direction':direction,'rootMatrix':rows(root.matrix_world),'localBounds':bounds(allpts),'parts':parts})
    if arg.draft:sc.render.resolution_percentage=50
    sc.render.filepath=str(OUT/(direction+'.png'));bpy.ops.render.render(write_still=True)
root.rotation_euler.z=0;sc.render.resolution_percentage=100;bpy.context.view_layer.update()
native={'round':arg.round,'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'sourceCamera':source_camera,'currentCamera':{'matrix':rows(cam.matrix_world),'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'frame':[sc.render.resolution_x,sc.render.resolution_y]},'sourceRootMatrix':source_root,'currentRootMatrix':rows(root.matrix_world),'projectionPoints':points,'geometry':records,'lights':[{'name':o.name,'matrix':rows(o.matrix_world),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'filmTransparent':sc.render.film_transparent},'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]},'notes':'Static scope. Full native model, physical apertures in left arm and seat; no cards, textures or loose external debris.'}
(OUT/'native-measurements.json').write_text(json.dumps(native,indent=2)+'\n')
print('COMPLETE',arg.round,OUT)
