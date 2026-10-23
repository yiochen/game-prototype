"""Reproduce crate-wood round 02 in Blender 5.2.2. No production writes.
Blender --background --python /absolute/path/to/round-01.py
All sprite pixels are native renders; Pillow is used only by package_round.py for previews/audits.
"""
import bpy, math, json, hashlib, bmesh, time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROUND='round-02'
OUT=BASE/'candidates'/ROUND
OUT.mkdir(parents=True,exist_ok=True)
BLEND=HERE/(ROUND+'.blend')
if BLEND.exists() or any((OUT/(d+'.png')).exists() for d in 'NESW'):
 raise RuntimeError('Immutable round exists; create a new numbered recipe')
SOURCE=HERE/'original-library.blend'
SOURCE_HASH='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE)==SOURCE_HASH
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name='Crate wood warm soft round 02'
with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
 assert 'S33_PROP_crate-wood' in src.collections
 dst.collections=['S33_PROP_crate-wood']
collection=dst.collections[0]
scene.collection.children.link(collection)
collection.hide_render=False;collection.hide_viewport=False
root=bpy.data.objects['crate-wood__root']
root.rotation_euler=(0,0,0)
bpy.context.view_layer.update()

def evaluated_bounds():
 deps=bpy.context.evaluated_depsgraph_get()
 points=[]
 for o in collection.all_objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(deps);me=eo.to_mesh()
  points += [eo.matrix_world@v.co for v in me.vertices]
  eo.to_mesh_clear()
 return [[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]]
original_bounds=evaluated_bounds()
original_parts=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in collection.all_objects]

def linear_hex(h):
 vals=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in vals)+(1,)

def material(name,color,roughness=.42):
 m=bpy.data.materials.new(name);m.use_nodes=True
 nodes=m.node_tree.nodes;nodes.clear();links=m.node_tree.links
 output=nodes.new('ShaderNodeOutputMaterial')
 shader=nodes.new('ShaderNodeBsdfPrincipled')
 shader.inputs['Base Color'].default_value=linear_hex(color)
 shader.inputs['Roughness'].default_value=roughness
 shader.inputs['Specular IOR Level'].default_value=.32
 shader.inputs['Coat Weight'].default_value=.04
 shader.inputs['Coat Roughness'].default_value=.38
 links.new(shader.outputs['BSDF'],output.inputs['Surface'])
 # Broad, extremely quiet timber variation follows model coordinates, not camera.
 coord=nodes.new('ShaderNodeTexCoord')
 mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,1,3)
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.2;noise.inputs['Detail'].default_value=1.3;noise.inputs['Roughness'].default_value=.55
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.89,.86,.83,1);ramp.color_ramp.elements[1].color=(1,1,1,1)
 mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=linear_hex(color)
 links.new(coord.outputs['Generated'],mapping.inputs[0]);links.new(mapping.outputs['Vector'],noise.inputs['Vector']);links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],mix.inputs[2]);links.new(mix.outputs['Color'],shader.inputs['Base Color'])
 m['base_srgb']=color;m['finish']='warm quiet timber, broad low-gloss response'
 return m

bodymat=material('Crate warm brown inset','B06C24',.48)
topmat=material('Crate golden lid','C99235',.4)
rimmat=material('Crate amber perimeter','CA862A',.43)
bracemat=material('Crate golden brace','D7902B',.4)

def finish(o,width):
 o.modifiers.clear()
 b=o.modifiers.new('Soft rounded timber edges','BEVEL');b.width=width;b.segments=5;b.affect='EDGES'
 b.use_clamp_overlap=True;b.harden_normals=True
 for p in o.data.polygons:p.use_smooth=True
 n=o.modifiers.new('Broad flat faces and rounded edges','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
 o.data.materials.clear()

body=bpy.data.objects['crate-wood__crate_body']
# Keep original bottom and side envelope; make room below the thicker, rounded lid planks.
for v in body.data.vertices:
 if v.co.z>0:v.co.z-=.025
body.data.update();finish(body,.032);body.data.materials.append(bodymat)
for o in list(collection.objects):
 if o.type!='MESH':continue
 if '_top_slats' in o.name:
  # Original max Z .915 is preserved. Extra thickness extends into the body.
  for v in o.data.vertices:
   if v.co.z<0:v.co.z-=.037
  o.data.update();finish(o,.019);o.data.materials.append(topmat)
 elif '_diagonal_' in o.name:
  finish(o,.016);o.data.materials.append(bracemat)

# Replace intersecting rail-bar corners by two closed, continuous manifold rings.
# Outer extrema match the measured original rails exactly; the body masks the inner junction.
removed=[]
for o in list(collection.objects):
 if '_rail_' in o.name:
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)

def ring(name,z):
 outer=[(-.489500016,-.441881448),(.489500016,-.441881448),(.489500016,.441881448),(-.489500016,.441881448)]
 inner=[(-.414,-.366),(.414,-.366),(.414,.366),(-.414,.366)]
 verts=[]
 for zz in (z-.045,z+.045):
  verts += [(x,y,zz) for x,y in outer]+[(x,y,zz) for x,y in inner]
 faces=[]
 for i in range(4):
  j=(i+1)%4
  faces += [(i,j,j+8,i+8),(i+4,i+12,j+12,j+4),(i+8,j+8,j+12,i+12),(i+4,j+4,j,i)]
 mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 o=bpy.data.objects.new(name,mesh);collection.objects.link(o);o.parent=root
 finish(o,.016);o.data.materials.append(rimmat)
 o['construction']='Continuous manifold perimeter; no intersecting coplanar corner bars'
 return o
ring('crate-wood__continuous_lower_rim',.135)
ring('crate-wood__continuous_upper_rim',.765)

# Fixed project camera: same world pose, orthographic scale, aspect and root as production.
cam=bpy.data.objects.new('Crate fixed catalog camera',bpy.data.cameras.new('Crate fixed catalog camera'))
scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5
elevation=math.atan(1/.7)
cam.location=(0,-10*math.cos(elevation),10*math.sin(elevation));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=math.sqrt(1+.7*.7);scene.render.pixel_aspect_y=1
scene.render.fps=12
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=15
scene.render.dither_intensity=0
def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*384,(1-p.y)*704))
bpy.context.view_layer.update();base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-base.y
cam.data.shift_y=(496-base.y)/dy;cam.data.shift_x=0;bpy.context.view_layer.update()
origin=pixel((0,0,0))
assert (origin-Vector((192,496))).length<.05

# Horizontally symmetric native illumination. No ground receiver or ground cast shadow.
world=bpy.data.worlds.new('Crate neutral warm world');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.08
def light(name,location,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler()
 return o
light('Crate broad centered overhead',(0,0,4.5),210,3.5)
for i in range(4):
 a=i*math.pi/2;light('Crate equal cardinal fill '+str(i),(3*math.cos(a),3*math.sin(a),1.8),65,4)
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.cycles.transparent_max_bounces=4
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.use_compositing=False
root['refinement_round']=ROUND;root['refinement_pipeline']='native-3d'
root['capture_logical_frame']='[192,352]';root['capture_logical_root']='[96,248]';root['capture_source_scale']=2
scene['reproduction_script']=str(Path(__file__).name);scene['source_sha256']=SOURCE_HASH
for o in collection.all_objects:
 o.hide_render=False;o.hide_set(False)
bpy.context.view_layer.update()
current_bounds=evaluated_bounds()
bound_delta=max(abs(original_bounds[a][i]-current_bounds[a][i]) for a in range(2) for i in range(3))
assert bound_delta<.002, (original_bounds,current_bounds,bound_delta)

topology=[]
for o in collection.all_objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 topology.append({'object':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'bevelWidths':[m.width for m in o.modifiers if m.type=='BEVEL'],'bevelSegments':[m.segments for m in o.modifiers if m.type=='BEVEL']})
 bm.free()
assert all(t['nonManifoldEdges']==0 and t['zeroAreaFaces']==0 for t in topology)
textblock=bpy.data.texts.new(Path(__file__).name);textblock.write(Path(__file__).read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
records={}
for direction,rotation in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=rotation;bpy.context.view_layer.update();scene.frame_set(1)
 scene.render.filepath=str(OUT/(direction+'.png'))
 started=time.monotonic();bpy.ops.render.render(write_still=True)
 records[direction]={'image':direction+'.png','sha256':sha(OUT/(direction+'.png')),'rootRotationZ':rotation,'bounds':evaluated_bounds(),'seconds':time.monotonic()-started}
root.rotation_euler.z=0;bpy.context.view_layer.update()
calibration={'root':list(origin),'unitX':list(pixel((1,0,0))-origin),'unitDepth':list(pixel((0,-1,0))-origin),'unitHeight':list(pixel((0,0,1))-origin)}
validation={'asset':'crate-wood','round':ROUND,'pipeline':'native-3d','blender':bpy.app.version_string,'sourceOriginal':{'path':'source/original-library.blend','sha256':SOURCE_HASH,'collection':'S33_PROP_crate-wood','parts':original_parts},'sourceEdited':{'path':'source/'+BLEND.name,'sha256':sha(BLEND),'reproductionScript':'source/'+Path(__file__).name,'reproductionScriptSha256':sha(Path(__file__))},'checks':{'originalSourceUntouched':sha(SOURCE)==SOURCE_HASH,'onlyCrateCollection':len([c for c in scene.collection.children])==1,'nativeMeshesOnly':all(o.type in ('MESH','EMPTY') for o in collection.all_objects),'allMeshesManifold':all(t['nonManifoldEdges']==0 for t in topology),'noZeroAreaFaces':all(t['zeroAreaFaces']==0 for t in topology),'boundsPreserved':bound_delta<.002,'rootRegistered':(origin-Vector((192,496))).length<.05,'noGroundReceiver':True,'fourNativeRotations':len(records)==4,'noExternalImages':not any(i.source=='FILE' for i in bpy.data.images),'fixedCameraAndMaterialsAcrossViews':True,'horizontalLightingSymmetry':4},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,248],'sourceScale':2,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'worldMatrix':[list(r) for r in cam.matrix_world],'shift':[cam.data.shift_x,cam.data.shift_y],'elevationDegrees':math.degrees(elevation)},'calibration':calibration,'footprint':[1,1],'authoredHeight':.925,'sourceMeshBounds':original_bounds,'candidateMeshBounds':current_bounds,'maximumBoundDelta':bound_delta,'boundsTolerance':.002,'clips':[{'id':'static','sourceClipId':'idle','frames':1,'fps':12,'static':True,'loop':False}],'sockets':{},'ports':{}},'topology':topology,'lighting':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoise':scene.cycles.use_denoising,'worldStrength':.08,'noGround':True,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'location':list(o.location),'rotation':list(o.rotation_euler)} for o in scene.objects if o.type=='LIGHT']},'materials':[{'name':m.name,'base_srgb':m.get('base_srgb'),'proceduralOnly':True} for m in (bodymat,topmat,rimmat,bracemat)],'removedIntersectingRails':removed,'renders':records,'dependencies':{'externalImages':[],'linkedLibraries':[],'selfContained':True},'status':'native-technical-checks-passed-awaiting-independent-visual-review'}
(OUT/'validation-native.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({'blend':str(BLEND),'out':str(OUT),'bounds':current_bounds,'maxBoundDelta':bound_delta,'seconds':{d:r['seconds'] for d,r in records.items()}},indent=2))
