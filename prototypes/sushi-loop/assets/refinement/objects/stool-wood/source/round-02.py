"""Exact native stool refinement recipe. Run against read-only production blend.
/opt/homebrew/bin/blender --background <original.blend> --python source/round-02.py
"""
import bpy, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]
ROUND='round-02'; OUT=BASE/'candidates'/ROUND
OUT.mkdir(parents=True,exist_ok=True)
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(x):return [list(v) for v in x]
sc=bpy.data.scenes['S33 Native Asset Library Export']
bpy.context.window.scene=sc
root=bpy.data.objects['stool_wood__root.001']
parts=list(root.children_recursive)
coll=next(c for c in sc.collection.children if root in list(c.all_objects))
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=False
coll.hide_render=False;coll.hide_viewport=False
for o in [root]+parts:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
root.rotation_euler=(0,0,0);sc.frame_set(1);sc.view_layers[0].update()
def bounds(objects):
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in objects:
        if o.type!='MESH':continue
        ev=o.evaluated_get(dg);me=ev.to_mesh()
        pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    lo=[min(p[i] for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)]
    return {'min':lo,'max':hi,'dimensions':[hi[i]-lo[i]for i in range(3)]}
source_bounds=bounds(parts)
source_transforms={o.name:{'matrix':rows(o.matrix_world),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}for o in [root]+parts}
source_project=Path(bpy.data.filepath);source_sha=sha(source_project)
cam=sc.camera
keep=set([root,cam]+parts)
for o in list(bpy.data.objects):
    if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
    if s!=sc:bpy.data.scenes.remove(s)
for c in list(bpy.data.collections):
    if c!=coll and not c.all_objects:bpy.data.collections.remove(c)
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=False

# Recorded stool camera, not the unrelated character camera saved at library startup.
original_camera=json.loads((BASE/'inputs/source-camera.json').read_text())
sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
cam.matrix_world=Matrix(original_camera['camera']['worldMatrix'])
sc.render.resolution_x=384;sc.render.resolution_y=704;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=original_camera['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
cam.data.shift_x=0;cam.data.shift_y=0;sc.view_layers[0].update()
def px(v):
    p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*704]
b=px((0,0,0));cam.data.shift_y=1;sc.view_layers[0].update();dy=px((0,0,0))[1]-b[1]
cam.data.shift_y=(496-b[1])/dy;sc.view_layers[0].update()
assert abs(px((0,0,0))[1]-496)<.005
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=64
sc.cycles.use_denoising=True;sc.cycles.seed=29
sc.cycles.max_bounces=8;sc.cycles.diffuse_bounces=4;sc.cycles.glossy_bounces=4
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=100
sc.render.fps=12;sc.render.dither_intensity=0;sc.render.use_file_extension=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.use_nodes=False

def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgb(h):return [linear(int(h[i:i+2],16)/255)for i in (0,2,4)]
def material(name,light,dark,roughness,specular,coat,grain=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');p=nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Roughness'].default_value=roughness;p.inputs['Specular IOR Level'].default_value=specular
    p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.35
    p.inputs['IOR'].default_value=1.45
    links.new(p.outputs['BSDF'],out.inputs['Surface'])
    tex=nodes.new('ShaderNodeTexCoord');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(tex.outputs['Generated'],sep.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(*rgb(dark),1)
    ramp.color_ramp.elements[1].position=1;ramp.color_ramp.elements[1].color=(*rgb(light),1)
    links.new(sep.outputs['Z'],ramp.inputs[0]);links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    if grain:
        scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1.4,70,10)
        links.new(tex.outputs['Generated'],scale.inputs[0]);noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.4;noise.inputs['Detail'].default_value=1.0;noise.inputs['Roughness'].default_value=.4
        links.new(scale.outputs[0],noise.inputs['Vector']);mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.04
        links.new(ramp.outputs[0],mix.inputs[1]);links.new(noise.outputs['Fac'],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
    m.diffuse_color=(*rgb(light),1);return m
seatmat=material('Warm soft honey seat','F8BB48','D88A24',.43,.26,.06,True)
legmat=material('Warm soft brown legs','B5722E','8D4C20',.54,.22,.035,False)
rungmat=material('Warm soft stretcher','B77B32','9C5F26',.51,.22,.035,False)
seammat=material('Warm shallow plank groove','BD7D2C','B47729',.64,.15,0,False)
for o in parts:
    o.data.materials.clear()
    o.data.materials.append(seatmat if '__seat.' in o.name else seammat if 'seat_seam' in o.name else legmat if '__leg_' in o.name else rungmat)
    if 'seat_seam' in o.name:continue
    for mod in o.modifiers:
        if mod.type=='BEVEL':
            mod.segments=6;mod.width=.035 if '__seat.' in o.name else .012;mod.harden_normals=True
    for p in o.data.polygons:p.use_smooth=True
    normal=o.modifiers.new('Preserve broad wooden planes','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50

# Shallow genuine channels replace raised painted strips. Each strip remains a
# narrow native floor beneath the channel, with the original line positions.
seat=next(o for o in parts if '__seat.' in o.name)
for o in [o for o in parts if 'seat_seam' in o.name]:
    y=o.location.y
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,y,.652))
    cutter=bpy.context.object;cutter.name='Temporary shallow seam channel';cutter.dimensions=(.593,.010,.012)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bm=seat.modifiers.new('Inset board channel','BOOLEAN');bm.operation='DIFFERENCE';bm.solver='EXACT';bm.object=cutter
    bpy.context.view_layer.objects.active=seat
    bpy.ops.object.modifier_move_to_index(modifier=bm.name,index=0)
    bpy.ops.object.modifier_apply(modifier=bm.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    o.location.z=.6465;o.dimensions=(.590,.009,.001)
    bm=o.modifiers.new('Soft groove floor edge','BEVEL');bm.width=.0004;bm.segments=3
    for p in o.data.polygons:p.use_smooth=False
# Newly cut tiny rim gets a restrained geometric roll.
for poly in seat.data.polygons:poly.material_index=0
while len(seat.data.materials)>1:seat.data.materials.pop(index=len(seat.data.materials)-1)
bm=seat.modifiers.new('Soft inset seam lips','BEVEL');bm.width=.0015;bm.segments=3;bm.affect='EDGES'
bm.limit_method='ANGLE';bm.angle_limit=.65;bm.harden_normals=True

world=bpy.data.worlds.new('Horizontally neutral soft studio');world.use_nodes=True
sc.world=world;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.48
lights=[]
def area(name,loc,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.35))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
area('Centered broad overhead',(0,0,4.5),180,3.5)
for i in range(8):
    a=i*math.tau/8;area('Neutral ring fill %02d'%i,(3*math.cos(a),3*math.sin(a),2),22,3)
sc['s33Lighting']='Warm soft: centered overhead + equal eight-way ring + neutral world; no ground'
sc['startup_asset']='stool-wood';sc['startup_clip']='static';sc['startup_frame']=0
sc['refinement_recipe']='source/round-02.py';sc['source_library_sha256']=source_sha
sc['project_role']='Editable isolated refined stool-wood capture scene'
sc['capture_scale']=2
root['artStyle']='warm-soft-stool-round-02'
root['capture_frame']=json.dumps([192,352]);root['capture_anchor']=json.dumps([96,248]);root['capture_scale']=2
sc.frame_set(1);sc.view_layers[0].update()
current_bounds=bounds(parts)
# Remove unused library resources. No external images or linked libraries.
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'source'/f'{ROUND}.blend'),compress=True)

def camera_record():
    return {'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':2,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'scene':sc.name,'cameraObject':cam.name,'rootObject':root.name,'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i]for i in range(2)],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i]for i in range(2)],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i]for i in range(2)]},'artStyle':{'revision':'warm-soft-stool-round-02','lighting':'Centered broad overhead + equal eight-way ring + neutral world; no ground','horizontalSymmetry':8,'roughness':.43}}
camera=camera_record();write(OUT/'records/camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['captureScale']=2;asset['sourceScale']=2;asset['scene']=sc.name;asset['groundRootObject']=root.name;asset['cameraObject']=cam.name;asset['artStyle']=camera['artStyle'];write(OUT/'records/asset.json',asset)
rig=json.loads((BASE/'inputs/source-rig.json').read_text());rig['scene']=sc.name;rig['cameraObject']=cam.name;rig['captureScale']=2;rig['status']='native-static-four-facing-captured';write(OUT/'records/rig.json',rig)
def topology(o):
    dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh()
    edges={tuple(sorted(e.vertices)):0 for e in me.edges}
    for p in me.polygons:
        for i in range(len(p.vertices)):
            key=tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)])));edges[key]=edges.get(key,0)+1
    out={'object':o.name,'type':o.type,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'evaluatedVertices':len(me.vertices),'evaluatedFaces':len(me.polygons),'boundaryEdges':sum(v==1 for v in edges.values()),'nonmanifoldEdges':sum(v!=2 for v in edges.values()),'degenerateFaces':sum(p.area<1e-12 for p in me.polygons),'materials':[m.name if m else None for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)}for m in o.modifiers]};ev.to_mesh_clear();return out
native=[]
for direction,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
    root.rotation_euler.z=angle;sc.frame_set(1);sc.view_layers[0].update()
    png=OUT/'raw'/f'static-{direction}-0000.png';png.parent.mkdir(exist_ok=True)
    sc.render.filepath=str(png);bpy.ops.render.render(write_still=True,scene=sc.name)
    sockets={k:px(root.matrix_world@Vector(v))for k,v in asset['sockets'].items()}
    rec={'asset':'stool-wood','clip':'static','sourceClip':'idle','direction':direction,'frame':0,'blenderFrame':1,'png':str(png.relative_to(BASE)),'sha256':sha(png),'scene':sc.name,'rootObject':root.name,'rootMatrix':rows(root.matrix_world),'cameraObject':cam.name,'cameraMatrix':rows(cam.matrix_world),'bounds':bounds(parts),'projectedSockets':sockets,'rootPixel':px((0,0,0)),'captureScale':2,'resolution':[384,704]}
    write(png.with_suffix('.capture.json'),rec);native.append(rec)
root.rotation_euler.z=0;sc.view_layers[0].update()
validation={'asset':'stool-wood','round':ROUND,'blender':bpy.app.version_string,'pipeline':'native-3d','sourceIntegrity':{'path':str(source_project),'sha256Before':source_sha,'sha256After':sha(source_project),'unchanged':sha(source_project)==source_sha},'sourceBounds':source_bounds,'currentBounds':current_bounds,'sourceTransforms':source_transforms,'currentRoot':{'name':root.name,'matrix':rows(root.matrix_world),'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale)},'camera':camera,'nativeCaptures':native,'socketNative':asset['sockets'],'topology':[topology(o)for o in parts],'lighting':{'horizontalSymmetry':8,'worldColor':[1,1,1],'worldStrength':.48,'groundMeshes':[],'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)}for o in lights]},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'seed':sc.cycles.seed,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'resolution':[384,704],'compositorEnabled':sc.use_nodes},'dependencies':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images if i.source=='FILE'],'externalRequired':[]},'edits':['Native six-segment seat/support bevels and weighted normals','Native shallow Boolean seam channels with original seam positions','Native warm satin wood shaders with restrained generated-coordinate variation','Horizontally neutral studio lighting; no ground receiver or raster image cards'],'replay':{'project':f'source/{ROUND}.blend','scene':sc.name,'rootObject':root.name,'cameraObject':cam.name,'frame':1,'rotationByDirection':{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2},'fixedResolution':[384,704]}}
write(OUT/'validation-native.json',validation)
write(BASE/'source'/f'{ROUND}-settings.json',{'recipe':f'source/{ROUND}.py','recipeSHA256':sha(__file__),'project':f'source/{ROUND}.blend','projectSHA256':sha(BASE/'source'/f'{ROUND}.blend'),'originalProjectSHA256':source_sha,'camera':camera,'render':validation['render'],'lighting':validation['lighting'],'materials':[{ 'name':m.name,'diffuse':list(m.diffuse_color)}for m in (seatmat,legmat,rungmat,seammat)]})
print('STOOL_ROUND_COMPLETE',OUT)
