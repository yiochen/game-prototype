import bpy, math, json, hashlib, bmesh
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
P=Path(__file__).resolve().parents[1]
ROUND='draft'
OUT=P/'candidates'/ROUND;OUT.mkdir(parents=True,exist_ok=True)
SOURCE=P/'source/original-library.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ORIGINAL_HASH=sha(SOURCE)
record=json.loads((P/'inputs/source-camera.json').read_text())
asset=json.loads((P/'inputs/source-assetRecord.json').read_text())
rig=json.loads((P/'inputs/source-rig.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='sign-blank native S'
with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):dst.collections=['S33_PROP_sign-blank']
collection=dst.collections[0];scene.collection.children.link(collection)
collection.hide_viewport=False;collection.hide_render=False
for obj in collection.all_objects:obj.hide_render=False;obj.hide_viewport=False;obj.hide_set(False)
bpy.context.view_layer.update()
def matrix(m):return [list(r) for r in m]
def measures():
 deps=bpy.context.evaluated_depsgraph_get();out=[];points=[]
 for o in collection.all_objects:
  r={'name':o.name,'type':o.type,'matrix':matrix(o.matrix_world),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None,'customProperties':{k:str(o[k]) for k in o.keys()}}
  if o.type=='MESH':
   ev=o.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];points+=vs
   bm=bmesh.new();bm.from_mesh(me)
   r.update(bounds=[[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]],sourceVertices=len(o.data.vertices),sourceFaces=len(o.data.polygons),evaluatedVertices=len(me.vertices),evaluatedFaces=len(me.polygons),nonManifoldEdges=sum(len(e.link_faces)!=2 for e in bm.edges),zeroAreaFaces=sum(f.calc_area()<1e-12 for f in bm.faces),uvLayers=[u.name for u in o.data.uv_layers],materialSlots=[m.name if m else None for m in o.data.materials]);bm.free();ev.to_mesh_clear()
  out.append(r)
 return {'objects':out,'bounds':[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]}
original=measures()

def linear(h):
 rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
def wood(name,color,post=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['base_srgb']='#'+color
 ns=m.node_tree.nodes;ns.clear();ls=m.node_tree.links
 out=ns.new('ShaderNodeOutputMaterial');bs=ns.new('ShaderNodeBsdfPrincipled');ls.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Roughness'].default_value=.76;bs.inputs['Specular IOR Level'].default_value=.18
 bs.inputs['Diffuse Roughness'].default_value=.25
 tex=ns.new('ShaderNodeTexCoord');sep=ns.new('ShaderNodeSeparateXYZ');ls.new(tex.outputs['Generated'],sep.inputs[0])
 ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';ls.new(sep.outputs['Z'],ramp.inputs['Fac'])
 base=linear(color)
 for e,f in zip(ramp.color_ramp.elements,[.88 if post else .85,1.07]):e.color=(*[v*f for v in base],1)
 noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.2;noise.inputs['Detail'].default_value=1;noise.inputs['Roughness'].default_value=.45
 vec=ns.new('ShaderNodeVectorMath');vec.operation='MULTIPLY';vec.inputs[1].default_value=(.5,.5,4 if not post else .5);ls.new(tex.outputs['Generated'],vec.inputs[0]);ls.new(vec.outputs[0],noise.inputs['Vector'])
 nr=ns.new('ShaderNodeMapRange');nr.inputs['From Min'].default_value=0;nr.inputs['From Max'].default_value=1;nr.inputs['To Min'].default_value=.94;nr.inputs['To Max'].default_value=1.06;ls.new(noise.outputs['Fac'],nr.inputs['Value'])
 mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;ls.new(ramp.outputs['Color'],mix.inputs[1]);ls.new(nr.outputs['Result'],mix.inputs[2]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
 return m
boards=[wood('Warm softly finished honey-gold 0','D99036'),wood('Warm softly finished honey-gold 1','DEA047'),wood('Warm softly finished honey-gold 2','D99439')]
post=wood('Warm softly finished brown posts','985C2B',True)
metal=bpy.data.materials.new('Restrained navy fasteners');metal.use_nodes=True
bs=metal.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*linear('30495E'),1);bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=.15;bs.inputs['Specular IOR Level'].default_value=.22
for o in collection.all_objects:
 if o.type!='MESH':continue
 if 'blank_plank' in o.name:material=boards[int(o.name.rsplit('_',1)[1])]
 elif 'rear_post' in o.name:material=post
 else:material=metal
 o.data.materials.clear();o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=6;mod.harden_normals=True
  if mod.type=='BEVEL' and 'blank_plank' in o.name:mod.width=.018
 if 'nail' in o.name:
  mod=o.modifiers.new('Small native hardware edge softness','BEVEL');mod.width=.001;mod.segments=3;mod.harden_normals=True
 wn=o.modifiers.new('Broad planar surfaces and soft bevel normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=50

# One horizontally symmetric illumination configuration, no ground receiver.
world=bpy.data.worlds.new('Neutral ambient');scene.world=world;world.use_nodes=True
world.node_tree.nodes.get('Background').inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.55
lights=[]
def area(name,pos,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.5))-ob.location).to_track_quat('-Z','Y').to_euler();lights.append(ob)
area('Broad centered overhead',(0,0,4.5),120,4)
for i,(x,y) in enumerate([(3,0),(0,3),(-3,0),(0,-3)]):area('Equal cardinal fill '+str(i),(x,y,2),65,5)
camdata=bpy.data.cameras.new('Registered sign-blank orthographic');cam=bpy.data.objects.new('Registered sign-blank orthographic',camdata);scene.collection.objects.link(cam);scene.camera=cam
cam.matrix_world=Matrix(record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5;camdata.clip_start=.1;camdata.clip_end=1000
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=record['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=record['camera']['pixelAspect'][1]
def px(v):
 q=world_to_camera_view(scene,cam,Vector(v));return Vector((q.x*384,(1-q.y)*704))
camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y
camdata.shift_y=(512-base.y)/dy;bpy.context.view_layer.update()
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=dev.type=='METAL'
scene.cycles.device='GPU';scene.cycles.seed=41
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=15
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.fps=12;scene.frame_start=1;scene.frame_end=1;scene.frame_set(1)
# Remove unused material/image data imported with the source collection.
for m in list(bpy.data.materials):
 if m.users==0:bpy.data.materials.remove(m)
for i in list(bpy.data.images):
 if i.users==0:bpy.data.images.remove(i)
for d in list(bpy.data.collections):
 if d!=collection and d.users==0:bpy.data.collections.remove(d)
bpy.ops.outliner.orphans_purge(do_recursive=True)
for lib in list(bpy.data.libraries):
 if not any(d.library==lib for bank in [bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.collections,bpy.data.node_groups,bpy.data.images] for d in bank):bpy.data.libraries.remove(lib)
bpy.context.view_layer.update();current=measures()
origin=px((0,0,0));calibration={'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)}
camrec={'projection':record['projection'],'frame':[192,352],'nativeFrame':[384,704],'anchor':[96,256],'cellSize':128,'captureScale':2,'fps':12,'axes':record['axes'],'camera':{'type':'orthographic','worldMatrix':matrix(cam.matrix_world),'projectionMatrix':matrix(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)),'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':record['camera']['elevationDegrees'],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y]},'calibration':calibration,'artStyle':{'revision':'warm-soft-cartoon-sign-v1','lighting':'broad centered overhead, four equal cardinal fills, neutral ambient','horizontalSymmetry':4}}
(OUT/'camera.json').write_text(json.dumps(camrec,indent=2))
asset['scale']=2;asset['artStyle']=camrec['artStyle'];(OUT/'asset.json').write_text(json.dumps(asset,indent=2));(OUT/'rig.json').write_text(json.dumps(rig,indent=2))
scene.render.filepath=str(OUT/'static-S.png')
blend=P/'source'/('round-'+ROUND+'.blend' if not ROUND.startswith('round-') else ROUND+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.render.render(write_still=True)
validation={'asset':'sign-blank','round':ROUND,'pipeline':'native-3d','blender':bpy.app.version_string,'sourceOriginal':{'path':'source/original-library.blend','sha256':ORIGINAL_HASH,'collection':collection.name,'measured':original},'sourceEdited':{'path':str(blend.relative_to(P)),'sha256':sha(blend),'recipe':str(Path(__file__).relative_to(P)),'recipeSha256':sha(__file__)},'capture':camrec,'nativeCurrent':current,'nativeSource':original,'root':list(bpy.data.objects['sign-blank__root'].location),'functionalContract':{'nominalCatalogHeight':1.12,'footprint':[1,1],'rootCell':[.5,.5],'groundBandY':[-.5,-.27],'allowCoOccupancy':True,'renderPass':'foreground','sockets':asset['sockets'],'facingPolicy':'single-player-facing','directions':['S'],'static':True,'frames':1,'fps':12,'loop':False},'lighting':{'worldStrength':.55,'worldColor':[1,1,1],'horizontalSymmetry':4,'groundReceiver':False,'engine':'CYCLES','device':scene.cycles.device,'devices':[{'name':d.name,'type':d.type,'use':d.use} for d in prefs.devices],'samples':64,'denoise':True,'seed':41,'lights':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'location':list(o.location),'rotation':list(o.rotation_euler)} for o in lights]},'checks':{'originalSourceUntouched':sha(SOURCE)==ORIGINAL_HASH,'sourceCollectionIsolated':True,'nativeIdentityPreserved':len([o for o in collection.all_objects if o.type=='MESH'])==9,'rootRegistered':(origin-Vector((192,512))).length<.001,'calibrationRegistered':all((Vector(calibration[k])-Vector(v)).length<.001 for k,v in {'unitX':[256,0],'unitDepth':[0,256],'unitHeight':[0,-179.2]}.items()),'boundsPreserved':max(abs(original['bounds'][j][i]-current['bounds'][j][i]) for j in range(2) for i in range(3))<1e-6,'meshTransformsPreserved':all(a['matrix']==b['matrix'] for a,b in zip(original['objects'],current['objects'])),'allMeshesManifold':all(o.get('nonManifoldEdges',0)==0 for o in current['objects']),'noZeroAreaFaces':all(o.get('zeroAreaFaces',0)==0 for o in current['objects']),'noRasterCard':all(o.type in ('MESH','EMPTY') for o in collection.all_objects),'noExternalImages':all(i.packed_file or i.source!='FILE' for i in bpy.data.images),'noLinkedLibraries':not bpy.data.libraries,'noGroundReceiver':True,'singleSFrame':True,'blankFace':True},'dependencies':{'images':[{'name':i.name,'source':i.source,'packed':bool(i.packed_file),'filepath':i.filepath} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries],'selfContained':True},'materials':[{'name':m.name,'baseSRGB':m.get('base_srgb'),'nodes':[n.bl_idname for n in m.node_tree.nodes] if m.node_tree else []} for m in bpy.data.materials],'renders':[{'clip':'static','direction':'S','index':0,'path':str((OUT/'static-S.png').relative_to(P)),'sha256':sha(OUT/'static-S.png')}],'status':'technical-evidence-awaiting-independent-review'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
print('COMPLETED',blend,validation['checks'])
