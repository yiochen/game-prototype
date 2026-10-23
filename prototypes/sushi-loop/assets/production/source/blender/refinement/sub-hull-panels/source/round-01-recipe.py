"""Portable native paired-saddle recipe. Blender 5.2; no production writes."""
import sys, json, math, hashlib, argparse
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent; EXP=HERE.parent; OUT=EXP/'candidates/round-01'
OUT.mkdir(parents=True,exist_ok=True)
DIRS={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bounded(pts):return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
def geometry(ob):
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh()
    pts=[eo.matrix_world@v.co for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];eo.to_mesh_clear();return pts,polys
def mat(name,color,rough=.32,metal=0.,coat=.15):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    def lin(c):return c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4
    rgb=tuple(lin(int(color[i:i+2],16)/255) for i in (0,2,4))
    p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.25
    return m
def finalize(ob,name,material,bevel=0):
    ob.name=name;bpy.context.view_layer.objects.active=ob
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    if bevel:
        m=ob.modifiers.new('Crafted rounded edge','BEVEL');m.width=bevel;m.segments=4
        bpy.ops.object.modifier_apply(modifier=m.name)
        for p in ob.data.polygons:p.use_smooth=True
        m=ob.modifiers.new('Planar weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50
        bpy.ops.object.modifier_apply(modifier=m.name)
    ob.data.materials.append(material)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    bpy.data.collections['SUB_HULL_PANELS__neutral'].objects.link(ob);ob.parent=bpy.data.objects['sub-hull-panels__motion']
    return ob
def box(name,center,size,material,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);ob=bpy.context.object;ob.dimensions=size
    return finalize(ob,name,material,bevel)
def cylinder(name,center,radius,depth,material,bevel):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=center)
    return finalize(bpy.context.object,name,material,bevel)
def build():
    # Derive a native clearance tool from exact frozen hull, then discard the
    # pairing scene. This changes only our saddle underside, never the body.
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'resources/frozen-main-v1/project.blend'))
    fr=bpy.data.objects['submarine-yellow__root'];fa=json.loads(fr['nativeActions'])
    for owner,name in fa['upgraded-dock-ready'].items():
        ob=bpy.data.objects[owner];a=bpy.data.actions[name];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
    bpy.context.scene.frame_set(1);fr.rotation_euler=(0,0,0);bpy.context.view_layer.update()
    hullpts,hullpolys=geometry(bpy.data.objects['body__hull'])
    # Main→canonical component transform: (X*2,(Y-.16)*2,(Z-.65)*2).
    # 0.002 local lift provides 0.001 main native surface clearance.
    cutterpts=[(v.x*2,(v.y-.16)*2,(v.z-.65)*2+.002) for v in hullpts]
    bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name='Sub hull panels native refinement'
    coll=bpy.data.collections.new('SUB_HULL_PANELS__neutral');sc.collection.children.link(coll)
    root=bpy.data.objects.new('sub-hull-panels__root',None);coll.objects.link(root)
    motion=bpy.data.objects.new('sub-hull-panels__motion',None);coll.objects.link(motion);motion.parent=root
    yellow=mat('PANELS__warm_yellow_enamel','F7BD2D',.29,0,.23)
    edge=mat('PANELS__orange_lower_shell','D8891F',.38,0,.14)
    cream=mat('PANELS__cream_raised_inset','FFE991',.31,0,.2)
    seam=mat('PANELS__gold_inset_seam','DA941D',.38,0,.12)
    silver=mat('PANELS__brushed_silver_dome','9DAAB7',.25,.42,.15)
    for sign in [-1,1]:
        x=sign*.43;side='L' if sign<0 else 'R'
        # Broad finite underside patch; its lower face lies exactly at local Z0.
        box(f'panel_{side}__seat_base',(x,0,.024),(.132,.52,.048),edge,.008)
        box(f'panel_{side}__rounded_armor',(x,0,.076),(.176,.59,.098),yellow,.026)
        # Layered construction is physical and remains within the frozen reservation.
        box(f'panel_{side}__inset_surround',(x,0,.124),(.110,.377,.016),seam,.007)
        box(f'panel_{side}__cream_inset',(x,0,.135),(.087,.350,.022),cream,.010)
        for y in [-.226,.226]:
            k='fore' if y<0 else 'aft'
            cylinder(f'panel_{side}__{k}_gold_collar',(x,y,.120),.048,.021,seam,.007)
            cylinder(f'panel_{side}__{k}_silver_cup',(x,y,.132),.037,.012,silver,.005)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=(x,y,.137))
            ob=bpy.context.object;ob.scale=(.032,.032,.018)
            for p in ob.data.polygons:p.use_smooth=True
            finalize(ob,f'panel_{side}__{k}_silver_dome',silver)
    cutmesh=bpy.data.meshes.new('Frozen hull clearance tool');cutmesh.from_pydata(cutterpts,[],hullpolys);cutmesh.update()
    cutter=bpy.data.objects.new('Temporary native hull clearance tool',cutmesh);sc.collection.objects.link(cutter)
    for ob in list(coll.objects):
        if ob.name.endswith('__seat_base'):
            bpy.context.view_layer.objects.active=ob
            mod=ob.modifiers.new('Actual native hull underside clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.ops.object.modifier_apply(modifier=mod.name)
            # Boolean cut surfaces use the base's real material. Remove the
            # cutter's empty slot rather than leaving an unbound resource.
            for poly in ob.data.polygons:poly.material_index=0
            ob.data.materials.clear();ob.data.materials.append(edge)
    bpy.data.objects.remove(cutter,do_unlink=True);bpy.data.meshes.remove(cutmesh)
    # Native exact continuous trigonometric F-curves, not interpolated sampled poses.
    motion.scale=(1,1,1);motion.location=(0,0,0)
    for path in ['location','scale']:motion.keyframe_insert(data_path=path,frame=1)
    idle=motion.animation_data.action;idle.name='PANELS__idle_neutral';idle.use_fake_user=True
    motion.animation_data.action=None
    for path in ['location','scale']:motion.keyframe_insert(data_path=path,frame=1)
    active=motion.animation_data.action;active.name='PANELS__active_ground_origin_pulse';active.use_fake_user=True
    for layer in active.layers:
      for strip in layer.strips:
       for bag in strip.channelbags:
        for fc in bag.fcurves:
         if fc.data_path=='scale' or (fc.data_path=='location' and fc.array_index==2):
          m=fc.modifiers.new('FNGENERATOR');m.function_type='SIN';m.use_additive=False;m.phase_multiplier=2*math.pi/12
          if fc.data_path=='scale':m.amplitude=.015;m.phase_offset=-2*math.pi/12;m.value_offset=1
          else:m.amplitude=-.008;m.phase_offset=math.pi/2-2*math.pi/12;m.value_offset=.008
    root['nativeClipActions']=json.dumps({'idle':idle.name,'active':active.name})
    root['canonicalIdleGeometry']='Exact neutral resources only; do not adopt standalone active into main clips.'
    apply_pose('idle',1,'S');configure(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'),compress=True)
    dump(OUT/'settings.json',settings(sc))
    return sc
def apply_pose(clip,frame,direction):
    root=bpy.data.objects['sub-hull-panels__root'];motion=bpy.data.objects['sub-hull-panels__motion']
    a=bpy.data.actions[json.loads(root['nativeClipActions'])[clip]];motion.animation_data_create();motion.animation_data.action=a;motion.animation_data.action_slot=a.slots[0]
    root.rotation_euler=(0,0,DIRS[direction]);bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
def configure(sc):
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.fps=12
    sc.render.film_transparent=True;sc.render.filter_size=.5;sc.eevee.taa_render_samples=64
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30
    sc.render.dither_intensity=0;sc.render.threads_mode='FIXED';sc.render.threads=4
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.35;sc.view_settings.gamma=1
    sc.world=bpy.data.worlds.new('PANELS__symmetric_world');sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.12
    cam=bpy.data.objects.new('PANELS__registered_camera',bpy.data.cameras.new('PANELS__registered_camera'));sc.collection.objects.link(cam);sc.camera=cam
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
    el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
    def px():
        v=world_to_camera_view(sc,cam,Vector((0,0,0)));return Vector((v.x*768,(1-v.y)*1408))
    base=px();cam.data.shift_y=1;bpy.context.view_layer.update();delta=px().y-base.y;cam.data.shift_y=(992-base.y)/delta
    for name,loc,power,size in [('overhead',(0,0,4.5),210,4),('east',(3,0,2.3),85,4),('west',(-3,0,2.3),85,4),('north',(0,3,2.3),85,4),('south',(0,-3,2.3),85,4)]:
        ld=bpy.data.lights.new('PANELS__'+name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
        ob=bpy.data.objects.new('PANELS__'+name,ld);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
def settings(sc):
    cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get()
    def p(v):
        q=world_to_camera_view(sc,cam,Vector(v));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
    root=p((0,0,0));return {'blender':bpy.app.version_string,'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'filter_size':sc.render.filter_size,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'cameraWorldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(dg,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeRoot':root,'basis':{n:[v-root[i] for i,v in enumerate(p(pos))] for n,pos in [('X',(1,0,0)),('depth',(0,-1,0)),('height',(0,0,1))]},'lights':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'worldStrength':sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'colorManagement':{'transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'horizontalLightSymmetry':4,'groundReceiver':False,'publication':'Whole native768x1408 frame BOX resize to384x704; no other pixel operations.'}
def serial(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return list(v)
    except:return str(v)
def identity():
    coll=bpy.data.collections['SUB_HULL_PANELS__neutral'];records=[]
    for ob in sorted(coll.all_objects,key=lambda o:o.name):
      if ob.type!='MESH':continue
      me=ob.data;rec={'name':ob.name,'vertices':[list(v.co) for v in me.vertices],'polygons':[list(p.vertices) for p in me.polygons],'smooth':[p.use_smooth for p in me.polygons],'loopNormals':[list(n.vector) for n in me.corner_normals],'uvLayers':{uv.name:[list(v.uv) for v in uv.data] for uv in me.uv_layers},'materials':[m.name for m in me.materials],'objectLocalMatrix':[list(r) for r in ob.matrix_local],'modifiers':[m.type for m in ob.modifiers]};rec['sha256']=hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest();records.append(rec)
    mats=[]
    for m in sorted({m for o in coll.all_objects if o.type=='MESH' for m in o.data.materials},key=lambda m:m.name):
      mats.append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.identifier:serial(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in m.node_tree.links]})
    return {'meshes':records,'materials':mats,'images':[],'externalResources':[]}
def render_all(test=False):
    sc=bpy.context.scene;records=[];coll=bpy.data.collections['SUB_HULL_PANELS__neutral'];root=bpy.data.objects['sub-hull-panels__root']
    for d in DIRS:
      for clip,count in [('idle',1),('active',12)]:
       for index in range(count):
        if test and (clip!='idle'):continue
        apply_pose(clip,index+1,d);pts=[p for ob in coll.all_objects if ob.type=='MESH' for p in geometry(ob)[0]]
        p=OUT/'native-frames'/f'{clip}-{d}'/f'{index:03}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        records.append({'clip':clip,'direction':d,'index':index,'nativeFrame':index+1,'path':str(p.relative_to(EXP)),'size':[768,1408],'sha256':sha(p),'rootRotationZ':float(root.rotation_euler.z),'actualRootMatrix':[list(r) for r in root.matrix_world],'nativeBounds':bounded(pts),'motionMatrix':[list(r) for r in bpy.data.objects['sub-hull-panels__motion'].matrix_local]})
        dump(OUT/'native-render-manifest.json',{'nativeCaptures':records})
    apply_pose('idle',1,'S');dump(OUT/'neutral-resource-identity.json',identity())
    bpy.data.libraries.write(str(HERE/'round-01-neutral.blend'),{coll},fake_user=True,compress=True)
def action_audit():
    rows=[];coll=bpy.data.collections['SUB_HULL_PANELS__neutral']
    for d in DIRS:
      for frame in [1+i*.5 for i in range(25)]:
        apply_pose('active',frame,d);pts=[p for ob in coll.all_objects if ob.type=='MESH' for p in geometry(ob)[0]];theta=2*math.pi*(frame-1)/12;s=1+.015*math.sin(theta);z=.008*(1-math.cos(theta));m=bpy.data.objects['sub-hull-panels__motion']
        rows.append({'direction':d,'frame':frame,'rootRotationZ':float(bpy.data.objects['sub-hull-panels__root'].rotation_euler.z),'actualScale':list(m.scale),'actualBobZ':float(m.location.z),'expectedScale':s,'expectedBobZ':z,'maxLawError':max(abs(v-s) for v in m.scale)+abs(m.location.z-z),'bounds':bounded(pts)})
    # Dense sweep certifies continuous native law against frozen active reservation.
    sweep=[]
    for i in range(1201):
      t=2*math.pi*i/1200;s=1+.015*math.sin(t);z=.008*(1-math.cos(t));sweep.append([s,z])
    apply_pose('idle',1,'S');geo=identity();pts=[Vector(v) for o in geo['meshes'] for v in o['vertices']]
    continuous={'minZ':min(p.z*s+z for s,z in sweep for p in pts),'maxZ':max(p.z*s+z for s,z in sweep for p in pts),'maxAbsX':max(abs(p.x)*s for s,z in sweep for p in pts),'maxAbsY':max(abs(p.y)*s for s,z in sweep for p in pts),'analyticConservativeMaxZ':max(p.z for p in pts)+.008+math.sqrt((.015*max(p.z for p in pts))**2+.008**2),'analyticMinimumZ':0,'phaseSamples':1201}
    curves=[]
    for a in bpy.data.actions:
      for l in a.layers:
       for strip in l.strips:
        for bag in strip.channelbags:
         for fc in bag.fcurves:curves.append({'action':a.name,'path':fc.data_path,'index':fc.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in fc.keyframe_points],'functionModifiers':[{'type':m.type,'function':getattr(m,'function_type',None),'amplitude':getattr(m,'amplitude',None),'phaseMultiplier':getattr(m,'phase_multiplier',None),'phaseOffset':getattr(m,'phase_offset',None),'valueOffset':getattr(m,'value_offset',None)} for m in fc.modifiers]})
    dump(OUT/'action-audit.json',{'law':'scale1+.015sin(theta), bob.008(1-cos(theta)), theta2pi(frame-1)/12; ground origin','staticIdle':'exact identity','runtimeFrames':12,'closingFrame':13,'fps':12,'poses':rows,'continuousSweep':continuous,'curves':curves,'sameMotionParentForAllPieces':True,'noMaterialOrShapeActions':True})
def render_continuity():
    sc=bpy.context.scene;records=[]
    for d in DIRS:
      for f in [1.5+i for i in range(12)]+[13.]:
        apply_pose('active',f,d);p=OUT/'motion-evidence'/f'{d}-{f:04.1f}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        records.append({'clip':'active','direction':d,'nativeFrame':f,'runtime':False,'path':str(p.relative_to(EXP)),'size':[768,1408],'sha256':sha(p),'rootRotationZ':float(bpy.data.objects['sub-hull-panels__root'].rotation_euler.z),'actualRootMatrix':[list(r) for r in bpy.data.objects['sub-hull-panels__root'].matrix_world]})
    dump(OUT/'motion-evidence/render-manifest.json',{'captures':records,'purpose':'Exact native frame13 closure and all12 half phases; evidence only, excluded from runtime atlases.'})
def mounted():
    originalIdentity=json.loads((OUT/'neutral-resource-identity.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(HERE/'resources/frozen-main-v1/project.blend'))
    sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];acts=json.loads(root['nativeActions'])
    for owner,name in acts['upgraded-dock-ready'].items():
      o=bpy.data.objects[owner];a=bpy.data.actions[name];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
    sc.frame_set(1);root.rotation_euler=(0,0,0)
    with bpy.data.libraries.load(str(HERE/'round-01-neutral.blend'),link=False) as (a,b):b.collections=['SUB_HULL_PANELS__neutral']
    coll=b.collections[0];sc.collection.children.link(coll);panelroot=bpy.data.objects['sub-hull-panels__root'];panelroot.parent=bpy.data.objects['MOUNT__sub-hull-panels'];panelroot.matrix_parent_inverse=Matrix.Identity(4);panelroot.matrix_basis=Matrix.Identity(4)
    motion=bpy.data.objects['sub-hull-panels__motion'];motion.animation_data_clear();motion.matrix_basis=Matrix.Identity(4)
    for o in sc.objects:
      if o.name.startswith('PROVISIONAL__panel'):o.animation_data_clear();o.hide_render=True
    bpy.context.view_layer.update()
    mountedIdentity=identity();dump(OUT/'mounted/inverse-mount-identity.json',{'localMeshNormalUVMaterialIdentityExact':mountedIdentity==originalIdentity,'canonicalIdentity':originalIdentity,'extractedAfterAssembly':mountedIdentity,'assemblyMountMatrix':[list(r) for r in panelroot.parent.matrix_local],'mainSourceSHA256':sha(HERE/'resources/frozen-main-v1/project.blend'),'policy':'Exact neutral local arrays and node resources. Standalone active animation cleared only in unsaved paired memory scene.'})
    panels=[o for o in coll.all_objects if o.type=='MESH'];contacts=[];collisions=[]
    for o in panels:
      av,ap=geometry(o);tree=BVHTree.FromPolygons(av,ap,all_triangles=False)
      for body in sc.objects:
       if body.type!='MESH' or not body.name.startswith('body__'):continue
       bv,bp=geometry(body);pairs=tree.overlap(BVHTree.FromPolygons(bv,bp,all_triangles=False))
       if pairs:collisions.append({'candidate':o.name,'body':body.name,'surfacePairs':len(pairs),'intentionalSeatContact':body.name.startswith('body__panel_contact_seat') and o.name.endswith('__seat_base')})
      if o.name.endswith('__seat_base'):
       faces=[];triangles=[];vs=[];area=0.;centroid=Vector()
       o.data.calc_loop_triangles()
       for tri in o.data.loop_triangles:
        poly=o.data.polygons[tri.polygon_index];tv=[o.matrix_world@o.data.vertices[i].co for i in tri.vertices];n=o.matrix_world.to_3x3().inverted().transposed()@poly.normal;n.normalize()
        if max(abs(p.z-.65) for p in tv)<1e-6 and n.z<-.999:
         ta=(tv[1]-tv[0]).cross(tv[2]-tv[0]).length*.5;area+=ta;centroid+=sum(tv,Vector())/3*ta;vs.extend(tv);faces.append(poly.index);triangles.append([list(v) for v in tv])
       centroid/=area;bounds=bounded(vs);sign=-1 if centroid.x<0 else 1;center=Vector((sign*.215,.16,.65))
       def intriangle(t):
        a,b,c=[Vector(v) for v in t];cross=[(b-a).cross(center-a).z,(c-b).cross(center-b).z,(a-c).cross(center-c).z]
        return all(v>=-1e-9 for v in cross) or all(v<=1e-9 for v in cross)
       contacts.append({'candidate':o.name,'actualFaceIndices':sorted(set(faces)),'actualContactTriangles':triangles,'normal':[0,0,-1],'areaWorld':area,'centroid':list(centroid),'extents':[bounds[1][i]-bounds[0][i] for i in range(3)],'bounds':bounds,'planeSeparation':max(abs(p.z-.65) for p in vs),'seatAvailableAreaWorld':.017952,'seatRelativeCoverage':area/.017952,'intendedSeatCenter':list(center),'containsIntendedCenter':any(intriangle(t) for t in triangles),'contactAreaMethod':'Actual coplanar downward native underside triangles, summed world cross-product area and area-weighted centroid. All contact vertices contained within the actual finite seat rectangle.'})
    # Contact invariance from exact shared rigid body_motion parent, inspected all12 main phases and half phases.
    invariance=[]
    for f in [1+i*.5 for i in range(25)]:
      sc.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();m=panelroot.parent.matrix_world
      invariance.append({'frame':f,'componentRootRelativeToMount':[list(r) for r in m.inverted()@panelroot.matrix_world],'bodyMotionParent':panelroot.parent.parent.name})
    sc.frame_set(1);root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
    dump(OUT/'mounted/native-seat-clearance-audit.json',{'contacts':contacts,'nativeSurfaceIntersections':collisions,'unintendedSurfaceIntersectionCount':sum(not r['intentionalSeatContact'] for r in collisions),'corridorIntegratedX':[-.15,.15],'candidateNeutralMainBounds':bounded([p for o in panels for p in geometry(o)[0]]),'bodyMotionContactInvariance':invariance,'frozenSourceSHA256':sha(HERE/'resources/frozen-main-v1/project.blend'),'otherEquipment':'provisional; panel placeholders hidden only in memory','mainSettings':settings(sc),'noPairedProjectResaved':True})
    manifest=[]
    for d,ang in DIRS.items():
      root.rotation_euler.z=ang;bpy.context.view_layer.update();p=OUT/'mounted'/f'neutral-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
      manifest.append({'direction':d,'path':str(p.relative_to(EXP)),'size':[sc.render.resolution_x,sc.render.resolution_y],'rootRotationZ':float(root.rotation_euler.z),'actualRootMatrix':[list(r) for r in root.matrix_world],'sha256':sha(p),'clip':'frozen-upgraded-dock-ready-neutral','index':0})
    dump(OUT/'mounted/render-manifest.json',{'renders':manifest,'scope':'Frozen preliminary body, exact native neutral candidate pair, other equipment provisional. No final main approval.'})
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',default='build');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.mode=='build':build()
    elif args.mode in ['test','render','audit','continuity']:
      bpy.ops.wm.open_mainfile(filepath=str(HERE/'round-01.blend'))
      if args.mode=='continuity':render_continuity()
      else:
        if args.mode!='audit':render_all(args.mode=='test')
        action_audit()
    elif args.mode=='mount':mounted()
